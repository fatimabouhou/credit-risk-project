"""
Point d'entrée FastAPI de agentic-service.

Ouvre la connexion Postgres (checkpointing de l'agent) une seule fois au
démarrage (lifespan), plutôt qu'à chaque requête — voir api/routes.py.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import routes as agentic_routes
from db.checkpointer import get_postgres_checkpointer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AgenticServiceAPI")


@asynccontextmanager
async def lifespan(app: FastAPI):
    with get_postgres_checkpointer() as checkpointer:
        checkpointer.setup()
        agentic_routes.checkpointer = checkpointer
        logger.info("✅ Checkpointer Postgres prêt.")
        yield
        agentic_routes.checkpointer = None


app = FastAPI(
    title="Agentic Service API",
    description="Microservice agentique d'analyse financière (RAG + agent autonome)",
    version="1.0.0",
    lifespan=lifespan,
)


# Le frontend (React, dev server Vite) appelle cette API directement
# depuis le navigateur — sans ça, chaque requête serait bloquée par la
# same-origin policy avant même d'atteindre les routes ci-dessous.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agentic_routes.router, prefix="/api/v1/agentic", tags=["Analyse"])


@app.get("/health", tags=["System"])
def health_check():
    """Vérifie que le service est en ligne."""
    return {"status": "online", "service": "agentic-service"}
