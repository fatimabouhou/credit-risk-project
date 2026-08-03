"""
État partagé du graphe agentique.

Un seul champ : `messages`, l'historique complet de la conversation entre
l'agent et ses outils (question initiale, décisions d'appel d'outil,
résultats, conclusion finale). C'est cet historique — pas un ensemble de
champs séparés à synchroniser — que le LLM relit à chaque tour pour
décider de la suite (voir planner.py) : c'est le mécanisme même qui rend
la boucle "agentique" plutôt qu'un pipeline à état fixe.
"""

from typing import Annotated, TypedDict

from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
