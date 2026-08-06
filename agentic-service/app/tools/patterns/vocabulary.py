"""
Pont de vocabulaire entre les patterns (data/patterns/, écrits avec des
noms de ratios "affichés" et un jeu de verdicts pensé indépendamment) et
le système de verdicts réel (tools/ratio_table_parser.py,
tools/benchmark_tool.py).

Rien n'est dupliqué en valeur ici — uniquement des correspondances de
NOMS entre deux vocabulaires, construites en comparant chaque pattern
existant (data/patterns/) au système de verdicts déjà en place et vérifié
(voir tools/benchmark_tool.py, tools/ratio_table_parser.py).
"""

# Nom affiché dans les patterns -> nom interne ("categorie.ratio_key") du
# système existant, tel que produit par check_client_ratios(). Un
# marqueur spécial :
#   - None : ratio non calculé par financial-service (Marge brute,
#     Interest Coverage) -> toute condition qui le cite est non évaluable.
#   - "TREND:<indicateur>" : donnée de tendance (outil_tendances), non
#     disponible dans check_client_ratios() — évaluable seulement si les
#     tendances ont été fournies en entrée du moteur de patterns.
# "Working Capital" pointe directement vers "liquidite.working_capital_frf"
# : ce ratio n'a pas de verdict de norme (montant absolu, voir
# benchmark_tool.py) mais context_builder.py y calcule et y range un signe
# (positif/négatif/proche_de_zero) dans le même dictionnaire "verdicts" —
# aucun traitement spécial requis côté moteur de matching.
RATIO_NAME_MAP: dict[str, str | None] = {
    "Current Ratio": "liquidite.current_ratio",
    "Quick Ratio": "liquidite.quick_ratio",
    "Cash Ratio": "liquidite.cash_ratio",
    "Working Capital": "liquidite.working_capital_frf",
    "Marge nette": "rentabilite.marge_nette",
    "Marge opérationnelle": "rentabilite.marge_operationnelle",
    "Marge brute": None,
    "ROA": "rentabilite.roa_return_on_assets",
    "ROE": "rentabilite.roe_return_on_equity",
    "Asset Turnover": "activite.asset_turnover",
    "DSO": "activite.dso_days",
    "DIO": "activite.dio_days",
    "DPO": "activite.dpo_days",
    "Debt Ratio": "solvabilite.liabilities_to_assets",
    "Debt-to-Equity": "solvabilite.debt_to_equity_leverage",
    "Equity Ratio": "solvabilite.autonomie_financiere",
    "Interest Coverage": None,
    "Chiffre d'affaires": "TREND:chiffre_affaires",
}

# Verdicts du vocabulaire "patterns" qui n'existent pas tels quels dans le
# vocabulaire réel du ratio concerné, et leur équivalent le plus proche.
# Clé : (nom_interne_du_ratio, verdict_pattern) -> verdict_reel.
# Construit en comparant les 49 patterns au jeu de verdicts effectivement
# produit par ratio_table_parser.py pour chaque ratio (voir
# RATIO_TABLE_SHAPES) — pas une règle générique, une correspondance
# ratio par ratio car les formes de table diffèrent (cash_ratio a de
# vraies zones nommées, DSO/DIO/DPO n'ont qu'un band Min/Max sans zone).
VERDICT_ALIASES: dict[tuple[str, str], str] = {
    ("liquidite.cash_ratio", "zone_a_interroger_bas"): "seuil_alerte_bas",
    ("activite.dio_days", "zone_a_interroger_bas"): "en_dessous_norme",
    ("activite.dio_days", "zone_a_interroger_haut"): "au_dessus_norme",
    ("activite.dpo_days", "zone_a_interroger_haut"): "au_dessus_norme",
    ("activite.dpo_days", "zone_a_interroger_bas"): "en_dessous_norme",
    ("activite.dso_days", "zone_a_interroger_haut"): "au_dessus_norme",
    ("activite.dso_days", "zone_a_interroger_bas"): "en_dessous_norme",
    ("solvabilite.liabilities_to_assets", "zone_a_interroger_haut"): "au_dela_seuil_alerte",
}


def resolve_verdict(internal_ratio: str, pattern_verdict: str) -> str:
    """Traduit un verdict écrit dans un pattern vers le vocabulaire réel du ratio."""
    return VERDICT_ALIASES.get((internal_ratio, pattern_verdict), pattern_verdict)


# Conditions qualitatives non calculables avec les données actuelles
# (historique multi-exercices, contexte sectoriel qualitatif...) —
# repérées par une sous-chaîne dans le texte brut de la condition
# (Condition.raw_text). Toujours en position "optional" dans les
# patterns existants : ignorées (ni satisfaites ni bloquantes), jamais
# en position "required" à ce jour.
NON_EVALUABLE_MARKERS = (
    "plusieurs exercices",
    "secteur d'activité connu pour",
    "les patterns modérés concernent des dimensions distinctes",
)


def is_non_evaluable(raw_text: str) -> bool:
    lowered = raw_text.lower()
    return any(marker in lowered for marker in NON_EVALUABLE_MARKERS)
