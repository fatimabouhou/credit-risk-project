"""
Outil de benchmarking — rapproche les ratios calculés d'un client des
normes sectorielles du RAG 1, pour que l'agent puisse juger s'il y a une
anomalie.

Pour chaque ratio, ce module rassemble la valeur mesurée + le passage RAG
le plus pertinent décrivant la norme sectorielle (recherche hybride, voir
plus bas), et, quand la table a une forme reconnue (RATIO_TABLE_SHAPES
dans ratio_table_parser.py), calcule aussi un verdict exact en Python à
partir de ce texte. Les fiches Markdown restent l'unique source de
vérité — aucune valeur numérique n'est dupliquée en dur, seule la FORME
de chaque table (quelles colonnes existent) est codée en dur. Seul
`liquidite.working_capital_frf` reste sans verdict calculable : montant
absolu en MAD, un seuil chiffré y serait faux (dépend de la taille
exacte de l'entreprise) — le même signal existe déjà normalisé sous
`solvabilite.net_current_liabilities_to_assets`.

Limite connue : le secteur du client (`profil_administratif.
fiche_renseignements.secteur` dans client_audits, ex. "Commerce de
matériaux de construction") est du texte libre extrait par
document-service, pas un des codes sectoriels utilisés par le RAG (BTP,
IND, COM, SRV, HOT, TRA — voir 00_segmentation_reference.md). Ce module
prend `secteur` en paramètre plutôt que de tenter de le déduire
automatiquement : la normalisation texte-libre -> code sectoriel reste à
faire.

Cas particulier — normes segmentées par taille (TAILLE_SEGMENTEE) : trois
normes (current_ratio en 01_liquidite.md § 4, roe_return_on_equity en
02_rentabilite.md § 5, autonomie_financiere en 03_solvabilite.md § 4)
sont classées par taille (TPE/PME/GE), pas par secteur. La taille est
calculée automatiquement (voir taille_classifier.py) à partir du chiffre
d'affaires et du total actif de l'exercice de référence — disponibles
dans financial-service (donnees_brutes_applaties) même si exclus du
payload allégé envoyé au LLM — selon la règle documentée dans
00_segmentation_reference.md § 3 (CA prioritaire, écart CA/actif signalé
plutôt que corrigé). `taille` reste un paramètre optionnel pour un
override manuel explicite ; JAMAIS deviné (deviner produisait de fausses
anomalies — ex. un current_ratio correct pour une PME/GE signalé à tort
comme "au-dessus de la norme TPE"). Si même le calcul automatique échoue
(CA absent du dossier), la comparaison est marquée indisponible plutôt
que hasardeuse.

Verdict calculé côté Python (voir ratio_table_parser.py) : le LLM
confondait de façon intermittente "Moyenne" avec la borne basse de la
fourchette (ex. debt_to_equity=1,09 comparé à [Min=0,40, Moyenne=0,90]
au lieu de [Min=0,40, Max=1,50], fausse anomalie). Pour les ratios dont
la table a une forme reconnue (RATIO_TABLE_SHAPES), le module parse le
texte RAG déjà récupéré et calcule min/max/verdict directement — le LLM
n'a plus qu'à le lire, jamais à recomparer deux nombres. Les fiches
restent l'unique source de vérité : rien n'est dupliqué, seule la FORME
de chaque table (quelles colonnes existent) est codée en dur, jamais ses
valeurs. Couvre aussi bien les tables à fourchette secteur/taille que les
tables à zones qualitatives universelles (cash_ratio,
net_current_liabilities_to_assets, retained_earnings_to_current_
liabilities — voir shape "zone_table"). Seul working_capital_frf
(montant absolu, pas de norme chiffrée possible) reste en lecture
qualitative par le LLM, comme avant.

Détection d'incohérences entre ratios : gérée depuis tools/patterns/
(outil_patterns_croises, voir graph/nodes.py), pas ici. Une première
version vivait dans ce module (_detect_incoherences, ex. trésorerie vs
recouvrement) mais faisait doublon avec les patterns CROSS.* — deux
sources concurrentes pour le même signal, l'agent retombant sur la plus
simple des deux (celle-ci) au lieu d'exploiter la plus riche (hypothèses
multiples, actions d'investigation). Retirée pour ne laisser qu'une
seule source de vérité.
"""

import time

from tools.financial_report_tool import get_financial_report
from tools.rag_tool import rag_search
from tools.ratio_table_parser import parse_verdict
from tools.taille_classifier import classify_taille_code

# outil_patterns_croises (graph/nodes.py) a besoin du même résultat que
# outil_benchmark_sectoriel (mêmes secteur/taille, appelés à quelques
# secondes d'intervalle dans le même run — voir planner.py, "appelle
# ensuite outil_patterns_croises (mêmes secteur/taille qu'à l'étape 4)")
# mais le recalculait entièrement (~17 requêtes RAG, une par ratio,
# refaites deux fois par analyse). TTL court (pas un cache permanent) :
# assez long pour couvrir cet écart au sein d'un même run, assez court
# pour ne jamais servir un résultat périmé entre deux analyses séparées
# du même client (ex. après un ré-upload de son dossier).
_RATIOS_CACHE_TTL_SECONDS = 30
_ratios_cache: dict[tuple[str, str, str | None], tuple[float, dict]] = {}

# Catégories de ratios couvertes par une fiche de normes sectorielles
# (data/docs/) — cash_flow et dscr n'ont pas de fiche associée, donc pas
# de benchmark RAG possible pour ces ratios-là (voir ratios_financiers_n
# dans le rapport financial-service).
BENCHMARKED_CATEGORIES = ["liquidite", "rentabilite", "activite", "solvabilite"]

# Ratios exclus du benchmarking individuel : ce ne sont pas des trous de
# données mais des ratios sans norme propre à eux, par construction.
# Aucun ratio n'y figure actuellement : `liabilities_to_assets` avait été
# exclu ici en tant que "redondant" avec `autonomie_financiere` (censés
# sommer à 1), mais des tests contre de vraies données ont montré que ce
# n'est pas fiable en pratique — l'écart de périmètre entre `total_dettes`
# (dettes financières uniquement) et le reste du passif (fournisseurs,
# provisions...) fait que la somme observée s'écarte souvent de 1 (voir
# 03_solvabilite.md § 1). `liabilities_to_assets` a donc sa propre table
# de normes (03_solvabilite.md § 5) comme tout autre ratio, au lieu
# d'être dérivé de `autonomie_financiere`.
REDUNDANT_RATIOS: dict[str, str] = {}

# Verdicts jugés sains (aucune anomalie) — tout le reste (au_dessus_norme,
# en_dessous_norme, au_dela_seuil_alerte, en_dessous_seuil_alerte,
# seuil_alerte_bas, zone_a_interroger_haut, besoin_significatif,
# coussin_faible...) compte comme une anomalie à lister dans
# "anomalies_detectees". zone_intermediaire_non_definie est neutre (zone
# non couverte par la fiche, ni bonne ni mauvaise) donc traité comme sain.
_HEALTHY_VERDICTS = {
    "dans_la_norme",
    "zone_confortable",
    "favorable",
    "niveau_courant",
    "coussin_confortable",
    "zone_intermediaire_non_definie",
}
_SEVERE_VERDICTS = {"au_dela_seuil_alerte", "en_dessous_seuil_alerte", "besoin_significatif"}

# Ratios de pure rentabilité où dépasser le Max habituel n'est pas un
# signal de risque crédit (contrairement à un excès de liquidité — voir
# 01_liquidite.md § 5, "un cash ratio très élevé n'est pas toujours
# positif" — ou à un levier trop élevé) : "au_dessus_norme" y est traité
# comme sain, "en_dessous_norme" reste une anomalie (faible rentabilité).
_HIGH_IS_GOOD_RATIOS = {
    "rentabilite.roa_return_on_assets",
    "rentabilite.roe_return_on_equity",
    "rentabilite.marge_nette",
    "rentabilite.marge_operationnelle",
    "rentabilite.ebitda_margin",
}


def _is_anomaly(ratio_name: str, verdict_slug: str) -> bool:
    if verdict_slug in _HEALTHY_VERDICTS:
        return False
    if verdict_slug == "au_dessus_norme" and ratio_name in _HIGH_IS_GOOD_RATIOS:
        return False
    return True

# Ratios dont la norme RAG est segmentée par taille (TPE/PME/GE) plutôt
# que par secteur — voir la limite documentée en tête de module.
TAILLE_SEGMENTED_RATIOS = {
    "liquidite.current_ratio",
    "rentabilite.roe_return_on_equity",
    "solvabilite.autonomie_financiere",
}


def get_benchmark_context(
    ratio_name: str, ratio_value: float, secteur: str, taille: str | None = None
) -> dict:
    """
    Rassemble, pour un ratio, la valeur mesurée et le passage RAG le plus
    pertinent décrivant la norme sectorielle correspondante.

    Recherche hybride : les fiches (data/docs/) portent désormais un tag
    dédié à côté de chaque table ("RATIO_BENCHMARK_TAG: liquidite.
    quick_ratio" — sans backticks : le parser les nettoie avant chunking,
    voir plus bas). On filtre D'ABORD sur ce tag exact (pas juste le nom
    du ratio seul : la table "Périmètre" de chaque fiche liste tous ses
    identifiants aussi, un filtre sur le nom nu aurait matché cette table
    générique en plus de la bonne section) avant de
    classer par similarité — élimine la confusion entre ratios voisins
    (ex. current_ratio / quick_ratio, même document, vocabulaire proche)
    sans dépendre uniquement de la similarité sémantique. Si aucun chunk
    ne porte ce tag (ratio non couvert), on retombe sur une recherche par
    similarité seule plutôt que de ne rien retourner.

    Si `ratio_name` fait partie de TAILLE_SEGMENTED_RATIOS et que `taille`
    n'est pas fourni, aucune recherche n'est faite : la table a bien 3
    tranches (TPE/PME/GE) dans le même chunk, donc la retrouver ne suffit
    pas à savoir laquelle appliquer — sans la taille, mieux vaut ne rien
    retourner que forcer un rapprochement au hasard (voir la limite
    documentée en tête de module). `indisponible` porte alors la raison.
    """
    if ratio_name in TAILLE_SEGMENTED_RATIOS and not taille:
        return {
            "ratio_name": ratio_name,
            "ratio_value": ratio_value,
            "secteur": secteur,
            "chunk_id": None,
            "norme_reference": None,
            "source": None,
            "indisponible": (
                "norme segmentée par taille (TPE/PME/GE), taille de l'entreprise non fournie"
            ),
        }

    question = f"Valeurs de référence sectorielles pour {ratio_name} dans le secteur {secteur}"
    # Le parser (ingestion/parser.py) nettoie les backticks Markdown avant
    # chunking : le tag stocké dans Chroma est donc "RATIO_BENCHMARK_TAG:
    # liquidite.current_ratio", sans backticks autour du nom du ratio.
    tag = f"RATIO_BENCHMARK_TAG: {ratio_name}"
    matches = rag_search(question, top_k=1, contains=tag)
    if not matches:
        matches = rag_search(question, top_k=1)
    best = matches[0] if matches else None

    verdict = None
    if best:
        segment_code = taille if ratio_name in TAILLE_SEGMENTED_RATIOS else secteur
        verdict = parse_verdict(ratio_name, ratio_value, best["text"], segment_code)

    return {
        "ratio_name": ratio_name,
        "ratio_value": ratio_value,
        "secteur": secteur,
        "taille": taille,
        "chunk_id": best["chunk_id"] if best else None,
        "norme_reference": best["text"] if best else None,
        "source": best["source_file"] if best else None,
        "verdict": verdict,
    }


def _auto_classify_taille(report: dict) -> tuple[str | None, str, str | None]:
    """
    Calcule automatiquement la taille depuis le chiffre d'affaires et le
    total actif de l'exercice de référence (report["annee_reference"]),
    disponibles dans donnees_brutes_applaties (financial-service) même si
    exclus du payload allégé envoyé au LLM — voir taille_classifier.py.
    Retourne (taille_code ou None, source lisible, écart CA/actif ou None).
    """
    annee = str(report.get("annee_reference"))
    donnees = report.get("donnees_brutes_applaties", {}).get(annee, {})
    chiffre_affaires = donnees.get("chiffre_affaires")
    total_actif = donnees.get("total_actif")
    if chiffre_affaires is None:
        return None, "indéterminée (chiffre d'affaires indisponible dans le dossier)", None

    result = classify_taille_code(chiffre_affaires, total_actif)
    if result["taille_code"] is None:
        return None, "indéterminée (table de segmentation introuvable dans le RAG)", None
    return result["taille_code"], "calculée automatiquement (chiffre d'affaires / total actif)", result[
        "ecart"
    ]


def check_client_ratios(client_id: str, secteur: str, taille: str | None = None) -> dict:
    """
    Enveloppe mise en cache de `_check_client_ratios_impl` (voir
    `_RATIOS_CACHE_TTL_SECONDS` ci-dessus) — même signature, mêmes
    garanties, juste évite de refaire le calcul (et les ~17 requêtes RAG
    qu'il déclenche) quand `outil_patterns_croises` le rappelle avec les
    mêmes arguments juste après `outil_benchmark_sectoriel`.
    """
    key = (client_id, secteur, taille)
    cached = _ratios_cache.get(key)
    if cached is not None:
        cached_at, result = cached
        if time.monotonic() - cached_at < _RATIOS_CACHE_TTL_SECONDS:
            return result

    result = _check_client_ratios_impl(client_id, secteur, taille)
    _ratios_cache[key] = (time.monotonic(), result)
    return result


def _check_client_ratios_impl(client_id: str, secteur: str, taille: str | None = None) -> dict:
    """
    Pour un client donné, rassemble le contexte de benchmark (valeur
    mesurée + norme RAG) pour chaque ratio couvert par une fiche
    sectorielle.

    Plusieurs ratios citent souvent le même passage RAG (ex. tous les
    ratios de solvabilité renvoient vers la même table sectorielle du
    levier) : le texte de chaque passage n'est donc inclus qu'une seule
    fois, dans `references` (clé = chunk_id), et chaque comparaison n'y
    fait plus que référence. Sans ça, un run complet (16 ratios) pouvait
    répéter le même passage RAG jusqu'à 5-6 fois et dépasser la limite de
    tokens/minute de l'API Groq gratuite — la donnée est identique, seule
    la duplication de texte est retirée.

    Les champs `None` dans le rapport financier (ex. activite.dpo_days
    quand la donnée source manque) sont écartés du benchmarking et listés
    à part plutôt que silencieusement ignorés — cohérent avec la fiche
    04_activite.md, qui documente déjà ces trous connus.

    `taille` (optionnel, TPE/PME/GE) : override manuel, à ne transmettre
    que si la question posée à l'agent la précise explicitement. Si non
    fourni, la taille est calculée automatiquement depuis le chiffre
    d'affaires / total actif du dossier (voir _auto_classify_taille) —
    plus fiable qu'une saisie manuelle et sans intervention utilisateur.
    Si même ce calcul échoue (CA absent du dossier), les ratios segmentés
    par taille sont écartés de `comparisons` et listés dans
    `comparisons_indisponibles` avec la raison, plutôt que rapprochés
    d'une tranche choisie au hasard.
    """
    report = get_financial_report(client_id)
    ratios = report["ratios_financiers_n"]

    taille_source = "fournie par l'utilisateur"
    taille_ecart = None
    if not taille:
        taille, taille_source, taille_ecart = _auto_classify_taille(report)

    comparisons = []
    comparisons_indisponibles = []
    references = {}
    champs_manquants = []

    for category in BENCHMARKED_CATEGORIES:
        for ratio_key, value in ratios.get(category, {}).items():
            full_name = f"{category}.{ratio_key}"
            if value is None:
                champs_manquants.append(full_name)
                continue
            if full_name in REDUNDANT_RATIOS:
                comparisons_indisponibles.append(
                    {
                        "ratio_name": full_name,
                        "ratio_value": value,
                        "raison": REDUNDANT_RATIOS[full_name],
                    }
                )
                continue

            ctx = get_benchmark_context(full_name, value, secteur, taille)
            if ctx.get("indisponible"):
                comparisons_indisponibles.append(
                    {
                        "ratio_name": full_name,
                        "ratio_value": value,
                        "raison": ctx["indisponible"],
                    }
                )
                continue

            chunk_id = ctx["chunk_id"]
            has_verdict = bool(ctx.get("verdict"))
            # Le texte complet du passage RAG n'est envoyé que pour les ratios SANS
            # verdict pré-calculé (aujourd'hui : working_capital_frf uniquement) — pour
            # les autres, l'agent a l'instruction explicite de ne jamais relire la table
            # pour recalculer, donc renvoyer son texte intégral (~10 tables par run) ne
            # ferait que gonfler le budget de tokens/minute de Groq pour rien.
            if chunk_id and not has_verdict and chunk_id not in references:
                references[chunk_id] = {"source": ctx["source"], "text": ctx["norme_reference"]}

            comparison = {
                "ratio_name": full_name,
                "ratio_value": value,
                "reference_id": chunk_id,
            }
            if full_name in TAILLE_SEGMENTED_RATIOS:
                comparison["taille"] = taille
            if has_verdict:
                # Ne garde que les clés renseignées : la plupart des tables n'ont ni
                # seuil d'alerte ni zone confortable (ex. quick_ratio n'a que Min/
                # Moyenne/Max) — inutile d'envoyer null au LLM pour chacune des ~16
                # comparaisons, ça pèse aussi sur ce même budget.
                comparison["verdict"] = {
                    k: v for k, v in ctx["verdict"].items() if v is not None
                }
            comparisons.append(comparison)

    # Calculé en Python plutôt que laissé à l'agent : lui faire relire "comparisons"
    # pour en déduire quels ratios sont anormaux a produit des contradictions (ex.
    # "risques" citant un ratio marqué dans_la_norme juste au-dessus, ou
    # working_capital_frf — qui n'a pourtant aucun verdict) — même symptôme que la
    # confusion Moyenne/borne que le calcul déterministe des verdicts a déjà réglée.
    anomalies_detectees = [
        {
            "ratio_name": c["ratio_name"],
            "ratio_value": c["ratio_value"],
            "verdict": c["verdict"]["verdict"],
            "severite": "elevee" if c["verdict"]["verdict"] in _SEVERE_VERDICTS else "a_surveiller",
        }
        for c in comparisons
        if c.get("verdict") and _is_anomaly(c["ratio_name"], c["verdict"]["verdict"])
    ]

    return {
        "client_id": client_id,
        "secteur": secteur,
        "taille": taille,
        "taille_source": taille_source,
        "taille_ecart": taille_ecart,
        "references": references,
        "comparisons": comparisons,
        "anomalies_detectees": anomalies_detectees,
        "comparisons_indisponibles": comparisons_indisponibles,
        "champs_manquants": champs_manquants,
    }


if __name__ == "__main__":
    import json
    import sys

    sys.stdout.reconfigure(encoding="utf-8")

    client_id = sys.argv[1] if len(sys.argv) > 1 else "data"
    secteur = sys.argv[2] if len(sys.argv) > 2 else "Commerce"
    taille = sys.argv[3] if len(sys.argv) > 3 else None

    result = check_client_ratios(client_id, secteur, taille)
    print(json.dumps(result, ensure_ascii=False, indent=2))
