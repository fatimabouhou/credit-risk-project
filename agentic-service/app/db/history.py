"""
Historique des analyses passées d'un client — consultation des runs déjà
persistés par le checkpointer Postgres (voir checkpointer.py, graph/workflow.py).

Chaque run de l'agent crée un thread_id unique ("{client_id}:{run_id}")
pour rester isolé des autres analyses du même client. Ce module retrouve
tous les thread_id d'un client donné et récupère la conclusion de chaque
run, pour pouvoir consulter l'historique sans interroger Postgres à la main.

La liste des threads d'un client n'est PAS quelque chose que l'API native
du checkpointer LangGraph sait faire (list() lit un thread précis, pas
plusieurs) — d'où la requête SQL directe sur la table checkpoints, avant
de repasser par le checkpointer pour lire le contenu de chaque thread.
"""

import psycopg
from langchain_core.messages import AIMessage

from db.checkpointer import POSTGRES_CHECKPOINT_URI, get_postgres_checkpointer


def list_analysis_history(client_id: str) -> list[dict]:
    """
    Retourne, pour chaque run passé de ce client, le thread_id et la
    conclusion finale de l'agent (le dernier message IA sans appel
    d'outil) — trié du plus récent au plus ancien.
    """
    with psycopg.connect(POSTGRES_CHECKPOINT_URI, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT DISTINCT thread_id FROM checkpoints WHERE thread_id LIKE %s",
                (f"{client_id}:%",),
            )
            thread_ids = [row[0] for row in cur.fetchall()]

    history = []
    with get_postgres_checkpointer() as checkpointer:
        checkpointer.setup()
        for thread_id in thread_ids:
            config = {"configurable": {"thread_id": thread_id}}
            checkpoint_tuple = checkpointer.get_tuple(config)
            if checkpoint_tuple is None:
                continue

            messages = checkpoint_tuple.checkpoint.get("channel_values", {}).get("messages", [])
            conclusion = None
            for m in reversed(messages):
                if isinstance(m, AIMessage) and not m.tool_calls:
                    conclusion = m.content
                    break

            history.append(
                {
                    "thread_id": thread_id,
                    "timestamp": checkpoint_tuple.checkpoint.get("ts"),
                    "conclusion": conclusion,
                }
            )

    history.sort(key=lambda h: h["timestamp"] or "", reverse=True)
    return history


if __name__ == "__main__":
    import json
    import sys

    sys.stdout.reconfigure(encoding="utf-8")

    client_id = sys.argv[1] if len(sys.argv) > 1 else "data"
    for entry in list_analysis_history(client_id):
        print(json.dumps(entry, ensure_ascii=False, indent=2, default=str))
