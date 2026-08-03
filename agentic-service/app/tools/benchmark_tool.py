"""
Outil de benchmarking — rapproche les ratios calculés d'un client des
normes sectorielles du RAG 1, pour que l'agent puisse juger s'il y a une
anomalie.

Ce module ne décide PAS lui-même si un ratio est anormal : coder un seuil
numérique en dur ici reviendrait à réinventer une règle rigide sur un texte
non structuré (tableau Markdown) — fragile, et contraire à l'esprit du RAG
(laisser le LLM lire la norme et raisonner sur l'écart). Il rassemble,
pour chaque ratio, la valeur mesurée + le passage RAG le plus pertinent
décrivant la norme sectorielle — prêt à être interprété par l'agent (dans
graph/, une fois construit).

Limite connue : le secteur du client (`profil_administratif.
fiche_renseignements.secteur` dans client_audits, ex. "Commerce de
matériaux de construction") est du texte libre extrait par
document-service, pas un des codes sectoriels utilisés par le RAG (BTP,
IND, COM, SRV, HOT, TRA — voir 00_segmentation_reference.md, qui
n'existe pas encore dans data/docs/). Ce module prend `secteur` en
paramètre plutôt que de tenter de le déduire automatiquement : la
normalisation texte-libre -> code sectoriel reste à faire.
"""

from tools.financial_report_tool import get_financial_report
from tools.rag_tool import rag_search

# Catégories de ratios couvertes par une fiche de normes sectorielles
# (data/docs/) — cash_flow et dscr n'ont pas de fiche associée, donc pas
# de benchmark RAG possible pour ces ratios-là (voir ratios_financiers_n
# dans le rapport financial-service).
BENCHMARKED_CATEGORIES = ["liquidite", "rentabilite", "activite", "solvabilite"]


def get_benchmark_context(ratio_name: str, ratio_value: float, secteur: str) -> dict:
    """
    Rassemble, pour un ratio, la valeur mesurée et le passage RAG le plus
    pertinent décrivant la norme sectorielle correspondante.
    """
    question = f"Valeurs de référence sectorielles pour {ratio_name} dans le secteur {secteur}"
    matches = rag_search(question, top_k=1)
    best = matches[0] if matches else None

    return {
        "ratio_name": ratio_name,
        "ratio_value": ratio_value,
        "secteur": secteur,
        "norme_reference": best["text"] if best else None,
        "source": best["source_file"] if best else None,
    }


def check_client_ratios(client_id: str, secteur: str) -> dict:
    """
    Pour un client donné, rassemble le contexte de benchmark (valeur
    mesurée + norme RAG) pour chaque ratio couvert par une fiche
    sectorielle.

    Les champs `None` dans le rapport financier (ex. activite.dpo_days
    quand la donnée source manque) sont écartés du benchmarking et listés
    à part plutôt que silencieusement ignorés — cohérent avec la fiche
    04_activite.md, qui documente déjà ces trous connus.
    """
    report = get_financial_report(client_id)
    ratios = report["ratios_financiers_n"]

    comparisons = []
    champs_manquants = []

    for category in BENCHMARKED_CATEGORIES:
        for ratio_key, value in ratios.get(category, {}).items():
            full_name = f"{category}.{ratio_key}"
            if value is None:
                champs_manquants.append(full_name)
                continue
            comparisons.append(get_benchmark_context(full_name, value, secteur))

    return {
        "client_id": client_id,
        "secteur": secteur,
        "comparisons": comparisons,
        "champs_manquants": champs_manquants,
    }


if __name__ == "__main__":
    import json
    import sys

    sys.stdout.reconfigure(encoding="utf-8")

    client_id = sys.argv[1] if len(sys.argv) > 1 else "data"
    secteur = sys.argv[2] if len(sys.argv) > 2 else "Commerce"

    result = check_client_ratios(client_id, secteur)
    print(json.dumps(result, ensure_ascii=False, indent=2))
