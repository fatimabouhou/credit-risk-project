"""
Assemble le graphe agentique : boucle ReAct (Reason + Act).

    agent (LLM décide) --tool_calls--> tools (exécution) --> agent (relit, redécide)
      |                                    |
      |                                    +--trop d'erreurs--> échec (FIN)
      +--pas de tool_calls (conclusion)--------------------------------> FIN

Ce n'est pas une séquence figée : le nombre de tours et l'ordre des
outils appelés ne sont pas codés en dur ici, ils dépendent uniquement de
ce que le LLM décide à chaque passage par `agent` (voir planner.py).
`tools_condition` (fourni par LangGraph) route vers `tools` si le dernier
message contient des tool_calls, vers FIN sinon.

La branche "échec" existe pour un cas réel rencontré en dev : si
financial-service ou document-service est injoignable, rien n'empêchait
le LLM de boucler indéfiniment sur le même outil en échec, ou pire, de
conclure quand même en inventant des valeurs. Au-delà de MAX_TOOL_ERRORS
échecs d'outils, le graphe coupe court vers une conclusion d'échec
déterministe (pas un appel LLM de plus) plutôt que de laisser dériver.
"""

from langgraph.graph import END, StateGraph
from langgraph.prebuilt import tools_condition

from langchain_core.messages import AIMessage

from .nodes import tools_node
from .planner import agent_node
from .state import AgentState

MAX_TOOL_ERRORS = 2


def route_after_tools(state: AgentState) -> str:
    if state.get("tool_error_count", 0) >= MAX_TOOL_ERRORS:
        return "echec"
    return "agent"


def echec_node(state: AgentState) -> dict:
    """Conclusion d'échec déterministe — pas d'appel LLM, pour ne pas risquer une conclusion inventée sur des données manquantes."""
    return {
        "messages": [
            AIMessage(
                content=(
                    f"Analyse interrompue : {state.get('tool_error_count', 0)} outils ont "
                    "échoué (financial-service et/ou document-service injoignable, ou "
                    "client introuvable). Impossible de produire une conclusion fiable "
                    "sans ces données — vérifier la disponibilité des services en amont "
                    "puis relancer l'analyse."
                )
            )
        ]
    }


def build_workflow(checkpointer=None):
    """
    checkpointer=None (par défaut) : le graphe reste sans mémoire, comme
    avant — utile pour des tests unitaires isolés. Passer un checkpointer
    (voir db/checkpointer.py) active la persistance de l'état par
    thread_id : deux invoke() avec le même thread_id continuent la même
    conversation au lieu de repartir de zéro.
    """
    graph = StateGraph(AgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tools_node)
    graph.add_node("echec", echec_node)

    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", tools_condition, {"tools": "tools", END: END})
    graph.add_conditional_edges("tools", route_after_tools, {"agent": "agent", "echec": "echec"})
    graph.add_edge("echec", END)

    return graph.compile(checkpointer=checkpointer)


if __name__ == "__main__":
    import sys
    import uuid

    from langchain_core.messages import HumanMessage

    from db.checkpointer import get_postgres_checkpointer

    sys.stdout.reconfigure(encoding="utf-8")

    client_id = sys.argv[2] if len(sys.argv) > 2 else "data"
    question = (
        sys.argv[1]
        if len(sys.argv) > 1
        else f"Analyse le dossier du client '{client_id}' : détermine son secteur, "
        "compare ses ratios à la norme, et signale toute anomalie."
    )

    # thread_id = client_id + un identifiant de run unique : chaque analyse reste
    # isolée (contexte borné, pas d'accumulation entre deux analyses indépendantes
    # du même client — voir l'incident réel du 2026-08-03, rate limit Groq dépassé
    # après deux runs sous le même thread_id "data"), tout en gardant le lien avec
    # le client (préfixe interrogeable en base pour retrouver son historique).
    thread_id = f"{client_id}:{uuid.uuid4().hex[:8]}"

    with get_postgres_checkpointer() as checkpointer:
        checkpointer.setup()
        app = build_workflow(checkpointer=checkpointer)
        final_state = app.invoke(
            {"messages": [HumanMessage(content=question)], "tool_error_count": 0},
            config={"recursion_limit": 25, "configurable": {"thread_id": thread_id}},
        )

    print("=" * 100)
    print("TRACE DE L'AGENT")
    print("=" * 100)
    for m in final_state["messages"]:
        kind = getattr(m, "type", "?")
        if kind == "human":
            print(f"\n[QUESTION] {m.content}")
        elif kind == "ai" and getattr(m, "tool_calls", None):
            for c in m.tool_calls:
                print(f"\n[AGENT decide d'appeler] {c['name']}({c['args']})")
        elif kind == "tool":
            preview = str(m.content)[:300]
            print(f"\n[OUTIL -> {getattr(m, 'name', '?')}] {preview}...")
        elif kind == "ai":
            print(f"\n[AGENT - CONCLUSION]\n{m.content}")

    print("\n" + "=" * 100)
