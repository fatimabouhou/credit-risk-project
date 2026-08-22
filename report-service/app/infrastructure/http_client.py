"""
Client HTTP vers document-service (extraction) et agentic-service
(analyse + décision) — report-service ne recalcule rien, il récupère tel
quel ce que ces 2 services ont déjà produit (voir services/report_generator.py
pour la mise en page).

agentic-service expose déjà analyse ET décision fusionnées dans une seule
réponse (POST /analyze/{client_id}, voir agentic-service/app/api/routes.py,
analyze_client) : un seul appel suffit pour les 2, pas besoin d'un 3ème
endpoint séparé pour la décision.
"""

import os

import httpx

DOCUMENT_SERVICE_URL = os.environ.get("DOCUMENT_SERVICE_URL", "http://localhost:8000")
AGENTIC_SERVICE_URL = os.environ.get("AGENTIC_SERVICE_URL", "http://localhost:8002")

# L'agent d'analyse (agentic-service) peut tourner plusieurs dizaines de
# secondes (boucle ReAct + appels LLM) — timeout large et distinct de
# celui, court, utilisé pour l'extraction (simple lecture MongoDB déjà
# faite, pas de nouvelle extraction déclenchée ici).
_EXTRACTION_TIMEOUT = 15.0
_ANALYSIS_TIMEOUT = 180.0


async def fetch_extraction(client_id: str) -> dict:
    """
    GET document-service/client/{client_id} : dossier déjà extrait et
    sauvegardé. Suppose que POST document-service/analyze/{client_id} a
    déjà tourné en amont (sinon 404, voir document-service/app/main.py).
    """
    async with httpx.AsyncClient(timeout=_EXTRACTION_TIMEOUT) as client:
        response = await client.get(f"{DOCUMENT_SERVICE_URL}/client/{client_id}")
        response.raise_for_status()
        return response.json()


# Lecture du diagnostic déjà calculé : simple SELECT Postgres, sans agent.
_CACHE_TIMEOUT = 10.0


async def fetch_analysis(client_id: str) -> dict:
    """
    Récupère l'analyse + décision du client.

    D'ABORD en lecture du dernier résultat enregistré
    (GET /analysis/{client_id}), et seulement à défaut en relançant les
    agents (POST /analyze/{client_id}).

    Sans cette lecture préalable, générer un rapport relançait les deux
    agents LLM à chaque fois — y compris immédiatement après une analyse
    affichée à l'écran, dont le résultat était donc jeté. C'était l'essentiel
    du temps d'attente du rapport, pour un diagnostic déjà disponible.
    """
    async with httpx.AsyncClient(timeout=_CACHE_TIMEOUT) as client:
        try:
            response = await client.get(f"{AGENTIC_SERVICE_URL}/api/v1/agentic/analysis/{client_id}")
            if response.status_code == 200:
                return response.json()
        except httpx.RequestError:
            # Service momentanément injoignable : on retente via l'analyse
            # complète ci-dessous, qui remontera l'erreur si elle persiste.
            pass

    async with httpx.AsyncClient(timeout=_ANALYSIS_TIMEOUT) as client:
        response = await client.post(f"{AGENTIC_SERVICE_URL}/api/v1/agentic/analyze/{client_id}")
        response.raise_for_status()
        return response.json()
