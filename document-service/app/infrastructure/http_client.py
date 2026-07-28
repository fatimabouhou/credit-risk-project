import httpx
import logging
import os

logger = logging.getLogger("DocumentHTTPClient")

# L'URL de base dépend de ton réseau Docker.
# Si tu testes en local sans Docker, ce sera http://localhost:8001
FINANCIAL_SERVICE_URL = os.getenv("FINANCIAL_SERVICE_URL", "http://localhost:8001")

async def notify_financial_service(client_id: str) -> bool:
    """
    Envoie une requête POST au financial-service pour déclencher l'analyse.
    """
    endpoint = f"{FINANCIAL_SERVICE_URL}/api/v1/financial/evaluate/{client_id}"

    logger.info(f"🚀 Notification du financial-service pour le client : {client_id}")

    try:
        # On utilise un client asynchrone pour ne pas bloquer document-service
        async with httpx.AsyncClient() as client:
            response = await client.post(endpoint, timeout=15.0)

            # Vérifie si le code HTTP est 200/2xx
            response.raise_for_status()

            logger.info(f"✅ financial-service a bien reçu la demande pour {client_id}")
            return True

    except httpx.RequestError as exc:
        logger.error(f"❌ Impossible de joindre le financial-service : {exc}")
        return False
    except httpx.HTTPStatusError as exc:
        logger.error(f"❌ Le financial-service a renvoyé une erreur {exc.response.status_code}: {exc}")
        return False