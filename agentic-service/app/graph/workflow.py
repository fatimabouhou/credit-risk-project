"""
Assemble le graphe agentique : boucle ReAct (Reason + Act).

    agent (LLM décide) --tool_calls--> tools (exécution) --> agent (relit, redécide)
      |
      +--pas de tool_calls (conclusion)--> FIN

Ce n'est pas une séquence figée : le nombre de tours et l'ordre des
outils appelés ne sont pas codés en dur ici, ils dépendent uniquement de
ce que le LLM décide à chaque passage par `agent` (voir planner.py).
`tools_condition` (fourni par LangGraph) route vers `tools` si le dernier
message contient des tool_calls, vers FIN sinon.
"""

from langgraph.graph import END, StateGraph
from langgraph.prebuilt import tools_condition

from .nodes import tools_node
from .planner import agent_node
from .state import AgentState


def build_workflow():
    graph = StateGraph(AgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tools_node)

    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", tools_condition, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")

    return graph.compile()


if __name__ == "__main__":
    import sys

    from langchain_core.messages import HumanMessage

    sys.stdout.reconfigure(encoding="utf-8")

    question = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "Analyse le dossier du client 'data' : détermine son secteur, "
        "compare ses ratios à la norme, et signale toute anomalie."
    )

    app = build_workflow()
    final_state = app.invoke(
        {"messages": [HumanMessage(content=question)]},
        config={"recursion_limit": 25},
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
