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


async def fetch_analysis(client_id: str) -> dict:
    """
    POST agentic-service/api/v1/agentic/analyze/{client_id} : lance
    l'agent 1 (analyse) puis l'agent 2 (décision) et renvoie les deux
    fusionnés.
    """
    async with httpx.AsyncClient(timeout=_ANALYSIS_TIMEOUT) as client:
        response = await client.post(f"{AGENTIC_SERVICE_URL}/api/v1/agentic/analyze/{client_id}")
        response.raise_for_status()
        return response.json()
