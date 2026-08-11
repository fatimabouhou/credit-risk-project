"""
Point d'entrée FastAPI de report-service.

Assemble le rapport de crédit final (PDF) à partir de 2 sources déjà
produites ailleurs — document-service (extraction) et agentic-service
(analyse + décision) — sans appeler de LLM lui-même : le texte en
langage naturel ("conclusion", "justification") existe déjà, ce service
se contente de le mettre en page dans un template fixe (voir
services/report_generator.py).
"""

import logging
import os
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Même trick que document-service/app/main.py : la commande de lancement
# (voir Dockerfile) est "uvicorn app.main:app" depuis /app, donc /app est
# sur sys.path mais pas /app/app — sans cet insert, "from api import
# routes" (et les imports flat similaires plus bas dans le service)
# échoueraient à l'exécution dans le conteneur.
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from api import routes as report_routes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ReportServiceAPI")

app = FastAPI(
    title="Report Service API",
    description="Génération du rapport de crédit final (PDF)",
    version="1.0.0",
)

# Même besoin que document-service/agentic-service : le frontend (dev
# server Vite) appelle cette API directement depuis le navigateur.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(report_routes.router, prefix="/api/v1/report", tags=["Rapport"])


@app.get("/health", tags=["System"])
def health_check():
    """Vérifie que le service est en ligne."""
    return {"status": "online", "service": "report-service"}
