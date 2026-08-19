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
    Identité et secteur réel du client (texte libre, ex. "Commerce de
    matériaux de construction") — SEULE source du secteur, jamais à
    deviner. À appeler avant outil_benchmark_sectoriel.

    "secteur_code_suggere" (optionnel) : si présent (ex. "COM"), cas déjà
    résolu de façon déterministe (préfixe "Commerce/Négoce/Distribution/
    Import-export de X") — utilise-le DIRECTEMENT, sans réinterpréter le
    texte ni appeler outil_recherche_normes (élimine un risque de mauvais
    classement déjà rencontré : "Commerce de matériaux de construction"
    classé à tort en BTP). Sinon, rapproche le texte libre d'un des 6
    codes de 00_segmentation_reference.md via outil_recherche_normes.
    Détail bancaire / alertes de cohérence : voir outil_validation_dossier
    (optionnel).
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
    Ratios financiers déjà calculés d'un client (liquidité, rentabilité,
    solvabilité, activité, DSCR, score Altman) — à comparer ensuite via
    outil_benchmark_sectoriel. Évolution sur 3 exercices : outil_tendances
    (optionnel), pas ici.

    "altman_score" (zone = "safe"/"grey"/"distress") est déjà calculé —
    NE LE MENTIONNE JAMAIS toi-même, ajouté automatiquement après coup
    (outil_patterns_croises vérifie déjà sa cohérence via
    "coherence_altman").
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
    Compare chaque ratio du client à la norme sectorielle du RAG.
    `secteur` doit être un des 6 codes (BTP, IND, COM, SRV, HOT, TRA — voir
    00_segmentation_reference.md, via outil_recherche_normes si besoin).

    `taille` (optionnel, "TPE"/"PME"/"GE") : LAISSE ABSENT dans le cas
    normal — calculée automatiquement depuis le chiffre d'affaires et le
    total actif du dossier. Ne le renseigne QUE si la question précise une
    taille explicite — jamais devinée depuis le secteur, le capital ou
    toute autre donnée indirecte (une tranche devinée a déjà produit de
    fausses anomalies).

    Réponse : "taille" (utilisée), "taille_ecart" (si le chiffre
    d'affaires et le total actif pointent vers des tailles différentes —
    à mentionner en conclusion, signal potentiellement utile, ex.
    foncière/holding), "references" (texte RAG brut, SEULEMENT pour les
    ratios SANS "verdict"), "comparisons" (verdict par ratio quand
    calculé), "anomalies_detectees" (déjà filtré : verdicts non sains,
    avec "severite" = "elevee"/"a_surveiller"), "comparisons_indisponibles"
    (ratios non comparables + raison, à signaler jamais ignorer). Les
    combinaisons de ratios qui se contredisent ou s'expliquent
    mutuellement sont détectées par outil_patterns_croises, pas ici.

    IMPORTANT — pour "Risques", cite UNIQUEMENT "anomalies_detectees",
    jamais un ratio relu toi-même dans "comparisons" : cette relecture
    manuelle a déjà produit des contradictions (ex. citer un ratio
    "dans_la_norme" comme risque, ou working_capital_frf qui n'a jamais de
    verdict). "anomalies_detectees" est déjà le bon filtre.

    IMPORTANT : un champ "verdict" est déjà calculé en Python à partir du
    texte RAG — NE LE RECALCULE JAMAIS depuis "references", reprends-le
    tel quel (reformule en français, mais ne recompare jamais la valeur à
    une borne lue dans le texte — erreur fréquente : comparer à "Moyenne"
    au lieu du couple min/max). Deux familles : fourchette
    ("dans_la_norme", "au_dessus_norme", "en_dessous_norme",
    "au_dela_seuil_alerte", "en_dessous_seuil_alerte", "zone_confortable")
    et zone qualitative universelle (cash_ratio,
    net_current_liabilities_to_assets,
    retained_earnings_to_current_liabilities — le nom de zone EST le
    verdict, ni bon ni mauvais par défaut, lis le texte RAG pour la
    nuance).

    `liquidite.working_capital_frf` n'a JAMAIS de verdict (montant absolu
    en MAD, un seuil chiffré y serait faux selon la taille de
    l'entreprise) — ne le qualifie jamais de "dans"/"hors norme" ; utilise
    solvabilite.net_current_liabilities_to_assets (même signal, normalisé)
    pour interpréter le besoin de financement court terme.
    """
    try:
        result = check_client_ratios(client_id, secteur, taille)
    except Exception as e:
        return f"Erreur lors du benchmark : {e}"
    return json.dumps(result, ensure_ascii=False)


@tool
def outil_patterns_croises(client_id: str, secteur: str, taille: str | None = None) -> str:
    """
    Détecte, parmi 49 combinaisons documentées, celles qui s'appliquent
    réellement au client (ex. trésorerie confortable + recouvrement
    dégradé). Complète outil_benchmark_sectoriel (ratio par ratio) en
    regardant comment PLUSIEURS se combinent. Calculé en Python — n'invente
    jamais une combinaison non listée, n'en ignore aucune renvoyée. Aucun
    résultat = normal.

    Réponse : "patterns_declenches", chacun avec "diagnostic" (à reprendre
    fidèlement) et "hypotheses" (JAMAIS une seule retenue comme certaine).
    Un id "GLOB.xxx" = vue d'ensemble à privilégier pour le diagnostic
    global. "coherence_altman" (si divergence entre score Altman et
    synthèse patterns) N'EST PAS à mentionner toi-même — ajouté
    automatiquement après coup.
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

# Champs à retirer de la VUE envoyée au LLM (jamais de l'état persisté, voir
# build_llm_view ci-dessous) pour chaque outil. "comparisons" de
# outil_benchmark_sectoriel (16-18 entrées, ~600-900 tokens à lui seul) est
# le cas qui a motivé cette liste : la docstring de l'outil instruit déjà le
# LLM de ne jamais s'en servir pour sa conclusion — seul "anomalies_detectees"
# (déjà filtré) doit l'être — ce champ est donc mort pour l'agent dès qu'il
# est produit, mais restait renvoyé et réexpédié en entier à CHAQUE tour
# suivant jusqu'à la fin du run (aucune purge de l'historique, voir state.py).
# "taille_source" (bookkeeping "calculée automatiquement" / "fournie par
# l'utilisateur") : jamais mentionné par le prompt système, seul
# "taille_ecart" (gardé) doit l'être — sert uniquement à _extract_benchmark
# (api/routes.py) pour la réponse HTTP, lue depuis l'état persisté, jamais
# depuis ce que voit le LLM.
#
# "references" (texte RAG brut) et "chunk_id"/"reference_id" à l'intérieur
# de "comparisons" ne sont volontairement PAS dans cette liste :
# "references" reste le seul moyen pour le LLM d'interpréter
# working_capital_frf (aucun verdict pré-calculé pour ce ratio, voir
# benchmark_tool.py) et doit donc rester lisible à CHAQUE tour, y compris
# celui où il rédige sa conclusion finale — un champ utile une seule fois
# n'est pas forcément inutile aux tours suivants, contrairement à
# "comparisons" que le LLM n'a jamais le droit d'utiliser.
_LLM_VIEW_DROP_FIELDS = {
    "outil_benchmark_sectoriel": ["comparisons", "taille_source"],
}


def build_llm_view(messages: list) -> list:
    """
    Construit la liste de messages réellement envoyée au LLM à chaque tour
    (voir planner.py, agent_node) — allégée des champs de _LLM_VIEW_DROP_FIELDS.

    Ne touche JAMAIS aux messages d'origine ni à l'état persisté par
    LangGraph : routes.py relit l'historique complet après coup pour
    construire la réponse HTTP (ex. "comparisons" alimente directement le
    tableau de ratios du frontend, voir api/routes.py:_extract_benchmark) —
    seule la copie envoyée à Groq est réduite, jamais ce qui est stocké.
    """
    compacted = []
    for message in messages:
        drop_fields = _LLM_VIEW_DROP_FIELDS.get(getattr(message, "name", None))
        if not (isinstance(message, ToolMessage) and drop_fields):
            compacted.append(message)
            continue
        try:
            data = json.loads(message.content)
        except (json.JSONDecodeError, TypeError):
            compacted.append(message)
            continue
        for field in drop_fields:
            data.pop(field, None)
        compacted.append(
            ToolMessage(
                content=json.dumps(data, ensure_ascii=False),
                tool_call_id=message.tool_call_id,
                name=message.name,
            )
        )
    return compacted


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
