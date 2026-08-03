"""
Outils exposés au Financial Analysis Agent, et le nœud qui les exécute.

Chaque outil enveloppe une fonction déjà construite et testée dans
tools/ — ce module ne contient aucune nouvelle logique métier, seulement
la déclaration LangChain (@tool, avec une docstring qui sert directement
de description à l'outil pour le LLM) qui les rend appelables par le
planner (voir planner.py).
"""

import json

from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode

from tools.benchmark_tool import check_client_ratios
from tools.client_profile_tool import get_client_profile
from tools.financial_report_tool import get_financial_report
from tools.rag_tool import rag_search


@tool
def outil_profil_client(client_id: str) -> str:
    """
    Récupère les données déclaratives réelles du client (raison sociale,
    secteur d'activité en texte libre, comportement bancaire) déjà
    extraites de son dossier par document-service. À appeler avant
    outil_benchmark_sectoriel : c'est la SEULE source du secteur réel du
    client — jamais à deviner. Le secteur retourné est en texte libre
    (ex. "Commerce de matériaux de construction") : le rapprocher d'un
    des 6 codes de 00_segmentation_reference.md via outil_recherche_normes.
    """
    try:
        profile = get_client_profile(client_id)
    except Exception as e:
        return f"Erreur : impossible de récupérer le profil du client '{client_id}' ({e})."
    return json.dumps(profile, ensure_ascii=False)


@tool
def outil_recherche_normes(question: str) -> str:
    """
    Cherche dans les fiches de normes sectorielles (RAG) la réponse à une
    question sur les seuils/repères financiers attendus — pour un ratio,
    un secteur, une taille d'entreprise, ou la règle de classement
    sectoriel elle-même (00_segmentation_reference.md).
    Exemple : "quel current_ratio est normal pour une PME du BTP ?"
    """
    results = rag_search(question, top_k=3)
    if not results:
        return "Aucun passage pertinent trouvé dans le RAG."
    return "\n\n---\n\n".join(
        f"[{r['source_file']} — {r['section_title']}]\n{r['text']}" for r in results
    )


@tool
def outil_rapport_financier(client_id: str) -> str:
    """
    Récupère le rapport financier déjà calculé d'un client auprès de
    financial-service : ratios (liquidité, rentabilité, solvabilité,
    activité), tendances sur 3 exercices (N, N-1, N-2), DSCR.
    """
    try:
        report = get_financial_report(client_id)
    except Exception as e:
        return f"Erreur : impossible de récupérer le rapport pour le client '{client_id}' ({e})."
    return json.dumps(report, ensure_ascii=False)


@tool
def outil_benchmark_sectoriel(client_id: str, secteur: str) -> str:
    """
    Compare chaque ratio calculé du client à la norme sectorielle
    correspondante du RAG (une comparaison par ratio, valeur mesurée +
    passage RAG le plus proche). `secteur` doit être un des 6 codes de
    00_segmentation_reference.md (BTP, IND, COM, SRV, HOT, TRA) — à
    déterminer via outil_recherche_normes si besoin avant d'appeler cet
    outil. Ne juge PAS lui-même de l'anomalie : c'est à l'agent
    d'interpréter l'écart entre la valeur et la norme retournée.
    """
    try:
        result = check_client_ratios(client_id, secteur)
    except Exception as e:
        return f"Erreur lors du benchmark : {e}"
    return json.dumps(result, ensure_ascii=False)


TOOLS = [outil_profil_client, outil_recherche_normes, outil_rapport_financier, outil_benchmark_sectoriel]

tools_node = ToolNode(TOOLS)
