"""
Routes HTTP de report-service.

Un seul flux : récupérer extraction (document-service) et analyse+décision
(agentic-service) déjà produits ailleurs, puis générer le PDF final (voir
services/report_generator.py). Ce service n'effectue aucun calcul ni
aucune décision — il assemble et met en page ce qui existe déjà.
"""

import asyncio
import logging

import httpx
from fastapi import APIRouter, HTTPException, Response, status

from infrastructure.http_client import fetch_analysis, fetch_extraction
from services.report_generator import render_html, render_pdf

logger = logging.getLogger("ReportAPI")
router = APIRouter()


async def _gather(client_id: str) -> tuple[dict, dict]:
    """
    Va chercher les 2 sources requises. Chaque échec est distingué par sa
    cause (donnée absente vs service injoignable) plutôt que remonté comme
    une 500 générique — utile pour diagnostiquer rapidement lequel des 2
    services en amont bloque la génération du rapport.
    """
    extraction_task, analysis_task = await asyncio.gather(
        fetch_extraction(client_id),
        fetch_analysis(client_id),
        return_exceptions=True,
    )

    try:
        if isinstance(extraction_task, BaseException):
            raise extraction_task
        extraction = extraction_task
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Extraction introuvable pour le client '{client_id}' "
                f"(document-service : {e.response.status_code}). "
                "Le POST document-service/analyze/{client_id} a-t-il déjà été exécuté ?"
            ),
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"document-service injoignable : {e}",
        )

    try:
        if isinstance(analysis_task, BaseException):
            raise analysis_task
        analysis = analysis_task
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Échec de l'analyse pour le client '{client_id}' (agentic-service : {e.response.status_code}).",
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"agentic-service injoignable : {e}",
        )

    return extraction, analysis


@router.post("/{client_id}", status_code=status.HTTP_200_OK)
async def generate_report(client_id: str):
    """
    Génère le rapport de crédit final (PDF) pour un client : extraction
    (document-service) + analyse et décision (agentic-service), mis en
    page dans un template fixe (voir services/report_generator.py).
    """
    extraction, analysis = await _gather(client_id)

    try:
        pdf_bytes = render_pdf(client_id, extraction, analysis)
    except Exception as e:
        logger.error(f"❌ Erreur lors de la génération du PDF pour '{client_id}' : {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur interne lors de la génération du rapport : {e}",
        )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="rapport_{client_id}.pdf"'},
    )


@router.get("/{client_id}/preview", status_code=status.HTTP_200_OK)
async def preview_report(client_id: str):
    """
    Même contenu que POST /{client_id}, mais renvoie le HTML brut (pas de
    conversion PDF) — pensé pour visualiser/ajuster rapidement le
    template dans un navigateur pendant le développement, sans repasser
    par WeasyPrint à chaque itération.
    """
    extraction, analysis = await _gather(client_id)
    html_content = render_html(client_id, extraction, analysis)
    return Response(content=html_content, media_type="text/html")
