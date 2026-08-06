"""
Construit le contexte nécessaire au moteur de patterns (engine.py) à
partir des données déjà calculées par benchmark_tool.py, sans dupliquer
de logique de calcul : ce module ne fait qu'assembler et ajouter un
complément qui n'existe pas encore ailleurs (le signe de
working_capital_frf), pour un client déjà évalué par check_client_ratios().
"""

from tools.benchmark_tool import check_client_ratios
from tools.financial_report_tool import get_financial_report

# En dessous de ce seuil (en proportion du total actif), le fonds de
# roulement est considéré "proche de zéro" plutôt que franchement positif
# ou négatif — seuil de plausibilité pour l'exercice, pas une norme
# officielle (aucune fiche ne documente de seuil chiffré pour ce cas,
# volontairement : working_capital_frf est un montant absolu, voir
# benchmark_tool.py).
_WORKING_CAPITAL_NEUTRAL_THRESHOLD = 0.01


def _classify_working_capital_sign(working_capital_frf: float, total_actif: float | None) -> str:
    """"positif" / "négatif" / "proche_de_zero" — un simple signe, jamais un jugement de norme."""
    if total_actif and total_actif > 0:
        ratio = working_capital_frf / total_actif
        if abs(ratio) <= _WORKING_CAPITAL_NEUTRAL_THRESHOLD:
            return "proche_de_zero"
    return "positif" if working_capital_frf > 0 else "négatif"


def build_pattern_context(
    client_id: str, secteur: str, taille: str | None = None, trends: dict | None = None
) -> dict:
    """
    Rassemble tout ce dont le moteur de patterns (engine.py) a besoin :
    - verdicts : {nom_interne_du_ratio: verdict} pour tous les ratios déjà
      couverts par check_client_ratios() (dont désormais "solvabilite.
      liabilities_to_assets", qui a sa propre table de normes — voir
      03_solvabilite.md § 5), plus "liquidite.working_capital_frf" (signe
      uniquement, voir _classify_working_capital_sign).
    - valeurs : {nom_interne_du_ratio: valeur brute} — utilisé pour les
      conditions "négatif" des patterns, qui vérifient le signe réel de
      la valeur plutôt qu'un verdict de norme.
    - trends : tendances (ex. "chiffre_affaires": "Hausse"/"Baisse"/
      "Stable") si fournies par l'appelant (outil_tendances) — sinon
      absentes, et les conditions qui en dépendent restent non évaluables
      (voir vocabulary.py, RATIO_NAME_MAP "TREND:...").
    """
    result = check_client_ratios(client_id, secteur, taille)

    verdicts: dict[str, str] = {}
    valeurs: dict[str, float] = {}
    for comparison in result["comparisons"]:
        if comparison.get("verdict"):
            verdicts[comparison["ratio_name"]] = comparison["verdict"]["verdict"]
        valeurs[comparison["ratio_name"]] = comparison["ratio_value"]

    report = get_financial_report(client_id)
    working_capital_frf = report.get("ratios_financiers_n", {}).get("liquidite", {}).get(
        "working_capital_frf"
    )
    if working_capital_frf is not None:
        annee = str(report.get("annee_reference"))
        total_actif = report.get("donnees_brutes_applaties", {}).get(annee, {}).get("total_actif")
        verdicts["liquidite.working_capital_frf"] = _classify_working_capital_sign(
            working_capital_frf, total_actif
        )
        valeurs["liquidite.working_capital_frf"] = working_capital_frf

    return {
        "client_id": client_id,
        "secteur": result["secteur"],
        "taille": result["taille"],
        "verdicts": verdicts,
        "valeurs": valeurs,
        "trends": trends or {},
        "benchmark_result": result,
        "altman_score": report.get("altman_score"),
    }
