"""
Persistance de l'état de l'agent — checkpointing LangGraph via PostgreSQL.

À ne pas confondre avec les deux autres modules de db/ :
- database_service.py persiste la connaissance RAG (Chroma) ;
- ce module persiste l'état du GRAPHE lui-même (graph/state.py) : l'
  historique de messages et tool_error_count de chaque run, indexé par
  thread_id (voir graph/workflow.py). Sans checkpointer, chaque appel à
  l'agent repartait de zéro — c'est ce que ce module corrige.

PostgreSQL tourne dans son propre conteneur Docker (voir docker-compose.yml,
service "postgres"), même logique que Chroma : ce module n'est qu'un
client vers ce serveur.
"""

import os

from dotenv import load_dotenv
from langgraph.checkpoint.postgres import PostgresSaver

load_dotenv()

POSTGRES_CHECKPOINT_URI = os.environ.get(
    "POSTGRES_CHECKPOINT_URI",
    "postgresql://agentic:agentic_checkpoint_pwd@localhost:5432/agentic_checkpoints",
)


def get_postgres_checkpointer():
    """
    Retourne le context manager PostgresSaver (à utiliser avec `with` —
    il gère l'ouverture/fermeture du pool de connexions). L'appelant doit
    appeler `.setup()` une fois entré dans le `with` pour créer les
    tables de checkpoint si elles n'existent pas encore (idempotent, sûr
    à rappeler à chaque démarrage).
    """
    return PostgresSaver.from_conn_string(POSTGRES_CHECKPOINT_URI)
