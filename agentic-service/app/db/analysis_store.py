"""
Dernier résultat d'analyse complet, par client.

POURQUOI CE MODULE
------------------
Le checkpointer Postgres conserve déjà les messages de chaque run, mais pas
la réponse assemblée que renvoie `analyze_client` : celle-ci agrège les
extractions faites sur les messages (benchmark, patterns, Altman, DSCR,
garanties, tendances, validation) ET la décision, produite par un second
appel LLM. La reconstruire depuis les messages coûterait un nouvel appel à
l'agent 2.

Conséquence directe avant ce module : report-service relançait un
`POST /analyze` complet — deux agents, boucle ReAct, appels LLM — à chaque
génération de rapport, y compris juste après une analyse affichée à l'écran.
Le rapport mettait donc plusieurs dizaines de secondes à sortir pour
recalculer un résultat déjà disponible.

Le payload est stocké tel quel en JSONB : ce qui est relu est exactement ce
qui a été renvoyé au client, sans reconstruction ni dérive possible.
"""

import json
import logging

import psycopg

from db.checkpointer import _uri_requise

logger = logging.getLogger("AnalysisStore")

# Une seule ligne par client : seul le dernier résultat est réutilisable,
# l'historique des runs restant du ressort du checkpointer (voir history.py).
_SCHEMA = """
CREATE TABLE IF NOT EXISTS analysis_results (
    client_id  TEXT PRIMARY KEY,
    thread_id  TEXT,
    payload    JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
)
"""


def _ensure_table(cur) -> None:
    cur.execute(_SCHEMA)


def save_analysis(client_id: str, payload: dict) -> None:
    """
    Enregistre (ou remplace) le dernier résultat complet d'un client.

    Volontairement non bloquant pour l'appelant : une panne d'écriture ne
    doit jamais faire échouer une analyse déjà calculée — le rapport
    retombera simplement sur un recalcul, comme avant.
    """
    try:
        with psycopg.connect(_uri_requise(), autocommit=True) as conn:
            with conn.cursor() as cur:
                _ensure_table(cur)
                cur.execute(
                    """
                    INSERT INTO analysis_results (client_id, thread_id, payload, created_at)
                    VALUES (%s, %s, %s, now())
                    ON CONFLICT (client_id) DO UPDATE
                        SET thread_id = EXCLUDED.thread_id,
                            payload = EXCLUDED.payload,
                            created_at = now()
                    """,
                    (client_id, payload.get("thread_id"), json.dumps(payload, ensure_ascii=False)),
                )
    except Exception as e:
        logger.warning(f"⚠️ Résultat d'analyse du client '{client_id}' non mis en cache : {e}")


def get_latest_analysis(client_id: str) -> dict | None:
    """Dernier résultat complet du client, ou None si aucun run enregistré."""
    try:
        with psycopg.connect(_uri_requise(), autocommit=True) as conn:
            with conn.cursor() as cur:
                _ensure_table(cur)
                cur.execute(
                    "SELECT payload FROM analysis_results WHERE client_id = %s",
                    (client_id,),
                )
                row = cur.fetchone()
    except Exception as e:
        logger.warning(f"⚠️ Lecture du cache d'analyse impossible pour '{client_id}' : {e}")
        return None

    if row is None:
        return None
    # psycopg rend le JSONB déjà désérialisé ; on couvre les deux cas.
    return row[0] if isinstance(row[0], dict) else json.loads(row[0])
