"""
Outil de tendances — évolution des indicateurs clés sur 3 exercices.

financial-service calcule déjà cette analyse (`analyse_tendances_3ans`
dans le rapport complet, voir financial_report_tool.py) : chiffre
d'affaires, EBITDA, résultat net, dettes, fonds propres, avec variations
en % et une étiquette "Hausse"/"Baisse" par indicateur. Ce module
n'ajoute AUCUN calcul — il extrait juste cette section précise du
rapport, pour donner à l'agent un accès direct et focalisé à la
trajectoire du client sans qu'il ait à la retrouver dans le gros JSON
retourné par outil_rapport_financier (qui contient aussi les ratios,
le DSCR, les données brutes par exercice...).

Utile en complément de benchmark_tool.py : un ratio peut être "dans la
norme" à l'instant N tout en faisant partie d'une trajectoire qui se
dégrade depuis 2 exercices — deux angles différents, pas redondants.
"""

from tools.financial_report_tool import get_financial_report


def get_trend_analysis(client_id: str) -> dict:
    """
    Retourne l'évolution sur 3 exercices (N, N-1, N-2) des indicateurs
    clés du client : valeurs, variations en % d'un exercice à l'autre, et
    tendance récente ("Hausse"/"Baisse") par indicateur.
    """
    report = get_financial_report(client_id)
    return {
        "client_id": client_id,
        "annee_reference": report.get("annee_reference"),
        "tendances": report.get("analyse_tendances_3ans", {}),
    }


if __name__ == "__main__":
    import json
    import sys

    sys.stdout.reconfigure(encoding="utf-8")

    client_id = sys.argv[1] if len(sys.argv) > 1 else "data"
    print(json.dumps(get_trend_analysis(client_id), ensure_ascii=False, indent=2))
