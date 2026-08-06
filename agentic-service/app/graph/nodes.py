"""
Outils exposés au Financial Analysis Agent, et les nœuds qui les exécutent.

Chaque outil enveloppe une fonction déjà construite et testée dans
tools/ — ce module ne contient aucune nouvelle logique métier, seulement
la déclaration LangChain (@tool, avec une docstring qui sert directement
de description à l'outil pour le LLM) qui les rend appelables par le
planner (voir planner.py).
"""

import json

from langchain_core.messages import ToolMessage
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode

from tools.benchmark_tool import check_client_ratios
from tools.client_profile_tool import get_client_profile
from tools.financial_report_tool import get_financial_report
from tools.patterns.pattern_tool import check_client_patterns
from tools.rag_tool import rag_search
from tools.secteur_classifier import try_classify_secteur
from tools.trend_tool import get_trend_analysis
from tools.validation_tool import get_validation_report


@tool
def outil_profil_client(client_id: str) -> str:
    """
    Récupère l'identité et le secteur d'activité réel du client (texte
    libre, ex. "Commerce de matériaux de construction") déjà extraits de
    son dossier par document-service. À appeler avant
    outil_benchmark_sectoriel : c'est la SEULE source du secteur réel du
    client — jamais à deviner.

    "secteur_code_suggere" (optionnel) : si présent (ex. "COM"), c'est un
    cas non ambigu déjà résolu de façon déterministe (préfixe "Commerce
    de"/"Négoce de"/"Distribution de"/"Import-export de" — achète et
    revend X, quel que soit X) — utilise-le DIRECTEMENT, sans appeler
    outil_recherche_normes ni réinterpréter toi-même le texte libre
    (l'exemple "Commerce de matériaux de construction" a déjà été mal
    classé en BTP par erreur malgré l'exemple explicite du prompt système
    — ce champ existe pour éliminer ce risque). S'il est absent (null),
    rapproche le texte libre d'un des 6 codes de
    00_segmentation_reference.md via outil_recherche_normes, comme
    d'habitude. Pour le détail bancaire ou les alertes de cohérence, voir
    outil_validation_dossier (outil séparé, optionnel).
    """
    try:
        profile = get_client_profile(client_id)
    except Exception as e:
        return f"Erreur : impossible de récupérer le profil du client '{client_id}' ({e})."

    # Extrait volontairement restreint : le profil complet (comportement
    # bancaire détaillé, historique financier brut) fait ~6000 caractères
    # et n'apporte rien à la démarche standard (secteur + comparaison de
    # ratios) — il est renvoyé en entier par outil_validation_dossier et
    # outil_tendances si besoin. Chaque tour de la boucle ReAct renvoie
    # l'historique complet au LLM : un payload inutilement gros ici se
    # paie à chaque tour, pas une seule fois (voir l'incident du
    # 2026-08-04 : quota Groq épuisé par des payloads non filtrés).
    admin = profile.get("profil_administratif", {}).get("fiche_renseignements", {})
    secteur_libre = admin.get("secteur")
    slim = {
        "client_id": client_id,
        "raison_sociale": admin.get("raison_sociale"),
        "secteur": secteur_libre,
        "secteur_code_suggere": try_classify_secteur(secteur_libre),
        "nombre_alertes_coherence": len(profile.get("alertes_coherence", [])),
    }
    return json.dumps(slim, ensure_ascii=False)


@tool
def outil_recherche_normes(question: str) -> str:
    """
    Cherche dans les fiches de normes sectorielles (RAG) la réponse à une
    question sur les seuils/repères financiers attendus — pour un ratio,
    un secteur, une taille d'entreprise, ou la règle de classement
    sectoriel elle-même (00_segmentation_reference.md).
    Exemple : "quel current_ratio est normal pour une PME du BTP ?"
    """
    try:
        results = rag_search(question, top_k=3)
    except Exception as e:
        return f"Erreur : recherche RAG impossible ({e})."
    if not results:
        return "Aucun passage pertinent trouvé dans le RAG."
    return "\n\n---\n\n".join(
        f"[{r['source_file']} — {r['section_title']}]\n{r['text']}" for r in results
    )


@tool
def outil_rapport_financier(client_id: str) -> str:
    """
    Récupère les ratios financiers déjà calculés d'un client auprès de
    financial-service (liquidité, rentabilité, solvabilité, activité,
    DSCR, score de défaillance Altman) — à comparer ensuite aux normes
    RAG via outil_benchmark_sectoriel. Pour l'évolution sur 3 exercices,
    voir outil_tendances (outil séparé, optionnel) plutôt que de la
    redemander ici.

    "altman_score" ("model"/"score"/"zone"/"formula_used", zone =
    "safe"/"grey"/"distress") est un score global déjà calculé — NE LE
    MENTIONNE PAS toi-même dans ta conclusion, il est ajouté
    automatiquement après coup par du code séparé (voir point 6 du
    prompt système). outil_patterns_croises vérifie déjà sa cohérence
    avec le reste de l'analyse (voir "coherence_altman").
    """
    try:
        report = get_financial_report(client_id)
    except Exception as e:
        return f"Erreur : impossible de récupérer le rapport pour le client '{client_id}' ({e})."

    # analyse_tendances_3ans exclu : redondant avec outil_tendances (même
    # source, même contenu) — inutile de le dupliquer si l'agent appelle
    # les deux. donnees_brutes_applaties exclu : gros volume (3 ans de
    # données ligne à ligne), non exploité par le benchmark. En revanche
    # couverture_dette_dscr est gardé : quasi gratuit en taille (~40
    # caractères) et directement pertinent pour un agent de risque crédit
    # (is_dscr_acceptable est un signal réel, ex. False sur le client
    # test) — retiré par erreur dans une première passe trop agressive.
    # altman_score gardé pour la même raison que couverture_dette_dscr :
    # quasi gratuit en taille (~60 caractères), et c'est un score de
    # défaillance global déjà calculé par financial-service (voir
    # ScoringEngine) — pas à recalculer ni réinterpréter, juste à citer.
    slim = {
        "client_id": client_id,
        "statut_evaluation": report.get("statut_evaluation"),
        "annee_reference": report.get("annee_reference"),
        "ratios_financiers_n": report.get("ratios_financiers_n"),
        "couverture_dette_dscr": report.get("couverture_dette_dscr"),
        "altman_score": report.get("altman_score"),
    }
    return json.dumps(slim, ensure_ascii=False)


@tool
def outil_benchmark_sectoriel(client_id: str, secteur: str, taille: str | None = None) -> str:
    """
    Compare chaque ratio calculé du client à la norme sectorielle
    correspondante du RAG. `secteur` doit être un des 6 codes de
    00_segmentation_reference.md (BTP, IND, COM, SRV, HOT, TRA) — à
    déterminer via outil_recherche_normes si besoin avant d'appeler cet
    outil.

    `taille` (optionnel, "TPE", "PME" ou "GE") : LAISSE ABSENT dans le cas
    normal — la taille de l'entreprise (nécessaire pour current_ratio,
    roe_return_on_equity, autonomie_financiere) est calculée
    automatiquement à partir du chiffre d'affaires et du total actif du
    dossier, tu n'as rien à faire. Ne renseigne ce paramètre QUE si la
    question posée à l'agent précise une taille différente explicitement
    — ne la devine JAMAIS toi-même à partir du secteur, du capital social
    ou de toute autre donnée indirecte.

    Réponse structurée : "taille" (celle utilisée pour les comparaisons),
    "taille_source" ("calculée automatiquement..." ou "fournie par
    l'utilisateur"), "taille_ecart" (si le chiffre d'affaires et le total
    actif pointent vers des tailles différentes — à mentionner dans la
    conclusion, ce peut être un signal utile en soi, ex. foncière/
    holding), "references" (texte brut, mais SEULEMENT pour les ratios
    SANS champ "verdict" — le budget de tokens/minute Groq est serré,
    inutile de renvoyer le texte intégral d'une table déjà résumée en
    verdict), "comparisons" (un "reference_id" par ratio, et "verdict"
    quand il a été calculé), "anomalies_detectees" (déjà filtré en
    Python : uniquement les ratios dont le verdict N'EST PAS sain, avec
    "severite" = "elevee" ou "a_surveiller" — voir plus bas) et
    "comparisons_indisponibles" (ratios qu'il n'a pas été possible de
    comparer, avec la raison — n'arrive que si même le calcul automatique
    de la taille échoue ; à signaler dans la conclusion, jamais à ignorer
    silencieusement). Les combinaisons de ratios qui se contredisent ou
    s'expliquent mutuellement (ex. trésorerie confortable mais
    recouvrement dégradé) sont détectées par outil_patterns_croises, pas
    ici — voir cet outil pour la partie "risques" de ta conclusion.

    IMPORTANT — pour la section "Risques" de ta conclusion, ne cite QUE
    des ratios présents dans "anomalies_detectees", jamais un ratio que tu
    aurais toi-même jugé anormal en relisant "comparisons" : c'est cette
    relecture manuelle qui a déjà produit des contradictions (ex. citer
    "debt_to_equity élevé" comme risque alors que son verdict dans
    "comparisons" est "dans_la_norme" juste au-dessus, ou citer
    working_capital_frf comme risque alors qu'il n'a jamais de verdict).
    "anomalies_detectees" est déjà le bon filtre, ne le recalcule pas.

    IMPORTANT : quand une entrée de "comparisons" contient un champ
    "verdict", il a déjà été calculé en Python à partir du texte RAG —
    NE LE RECALCULE PAS toi-même à partir du texte de "references",
    contente-toi de le reprendre tel quel dans ta conclusion (reformule
    en français, mais ne compare jamais à nouveau la valeur à une borne
    lue dans le texte). Deux familles de verdicts possibles :
    - Ratios à fourchette (min/max) : "dans_la_norme", "au_dessus_norme",
      "en_dessous_norme", "au_dela_seuil_alerte", "en_dessous_seuil_alerte",
      "zone_confortable".
    - Ratios à zones qualitatives universelles, sans segmentation secteur/
      taille (cash_ratio, net_current_liabilities_to_assets,
      retained_earnings_to_current_liabilities) : verdict = le nom de la
      zone (ex. "zone_confortable", "besoin_significatif", "coussin_
      faible") — reformule simplement en français, ce n'est ni bon ni
      mauvais par défaut, lis le texte RAG associé pour la nuance.

    Seul `liquidite.working_capital_frf` n'a jamais de champ "verdict" (et
    n'en aura jamais) : c'est un montant absolu en MAD, pas un ratio — un
    seuil chiffré y serait mathématiquement faux car il dépend de la
    taille exacte de l'entreprise. Le même signal existe déjà, normalisé,
    sous solvabilite.net_current_liabilities_to_assets (rapporté au total
    actif) — reporte-toi à CE ratio pour interpréter le besoin de
    financement court terme, ne commente jamais working_capital_frf comme
    "dans" ou "hors norme" à partir de sa seule valeur brute.
    """
    try:
        result = check_client_ratios(client_id, secteur, taille)
    except Exception as e:
        return f"Erreur lors du benchmark : {e}"
    return json.dumps(result, ensure_ascii=False)


@tool
def outil_patterns_croises(client_id: str, secteur: str, taille: str | None = None) -> str:
    """
    Détecte, parmi 49 combinaisons de ratios documentées, lesquelles
    s'appliquent réellement au client (ex. trésorerie confortable +
    recouvrement dégradé, ROE porté par le levier). Complète
    outil_benchmark_sectoriel (qui compare CHAQUE ratio séparément) en
    regardant comment PLUSIEURS se combinent. Calculé en Python à partir
    des verdicts déjà connus — n'invente jamais une combinaison non
    listée ici, n'en ignore aucune renvoyée. Aucun résultat = normal.

    Réponse : "patterns_declenches", chacun avec "diagnostic" (à
    reprendre fidèlement) et "hypotheses" (plusieurs lectures possibles —
    n'en retiens JAMAIS une seule comme certaine). Un id "GLOB.xxx" donne
    une vue d'ensemble à privilégier pour le diagnostic global de ta
    conclusion. "coherence_altman" (présent seulement s'il y a une
    divergence entre le score Altman et la synthèse par patterns) N'EST
    PAS à mentionner toi-même : il est ajouté automatiquement à ta
    réponse par du code séparé, après coup.
    """
    try:
        result = check_client_patterns(client_id, secteur, taille)
    except Exception as e:
        return f"Erreur lors de la détection de patterns : {e}"
    return json.dumps(result, ensure_ascii=False)


@tool
def outil_tendances(client_id: str) -> str:
    """
    Retourne l'évolution sur 3 exercices (N, N-1, N-2) des indicateurs
    clés du client (chiffre d'affaires, EBITDA, résultat net, dettes,
    fonds propres) — valeurs, variations en % et tendance récente.
    OPTIONNEL, à n'appeler que si un ratio semble limite ou si la
    conclusion bénéficierait de savoir si la situation se dégrade ou
    s'améliore dans le temps ; pas nécessaire pour une analyse standard.
    """
    try:
        result = get_trend_analysis(client_id)
    except Exception as e:
        return f"Erreur : impossible de récupérer les tendances du client '{client_id}' ({e})."
    return json.dumps(result, ensure_ascii=False)


@tool
def outil_validation_dossier(client_id: str) -> str:
    """
    Retourne les alertes de cohérence croisée (ex. incidents de paiement
    détectés à la Centrale des Risques BAM) et le statut de conformité
    réglementaire (DGI/CNSS) du dossier client. OPTIONNEL, à appeler si
    tu veux vérifier la fiabilité du dossier avant d'interpréter ses
    ratios ; pas nécessaire pour une analyse standard sans signal
    d'alerte particulier.
    """
    try:
        result = get_validation_report(client_id)
    except Exception as e:
        return f"Erreur : impossible de récupérer la validation du client '{client_id}' ({e})."
    return json.dumps(result, ensure_ascii=False)


TOOLS = [
    outil_profil_client,
    outil_recherche_normes,
    outil_rapport_financier,
    outil_benchmark_sectoriel,
    outil_patterns_croises,
    outil_tendances,
    outil_validation_dossier,
]

_tool_node = ToolNode(TOOLS)


def tools_node(state: dict) -> dict:
    """
    Exécute les outils demandés (via ToolNode) puis compte, parmi les
    résultats obtenus à CE tour seulement, ceux qui sont des erreurs (nos
    outils attrapent leurs exceptions et renvoient une chaîne "Erreur : ..."
    plutôt que de lever — voir les docstrings ci-dessus) pour incrémenter
    tool_error_count. C'est ce compteur que workflow.py utilise pour couper
    court après plusieurs échecs plutôt que de laisser le LLM tourner sur
    des données manquantes.
    """
    result = _tool_node.invoke(state)
    new_errors = sum(
        1
        for m in result["messages"]
        if isinstance(m, ToolMessage) and str(m.content).startswith("Erreur")
    )
    return {
        "messages": result["messages"],
        "tool_error_count": state.get("tool_error_count", 0) + new_errors,
    }
