import os
import sys
import logging
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any

# -------------------------------------------------------------
# GESTION DU PYTHONPATH
# -------------------------------------------------------------
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

# Import de notre orchestrateur
from services.document_processor import DocumentProcessor

# -------------------------------------------------------------
# INITIALISATION FASTAPI & LOGS
# -------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DocumentServiceAPI")

app = FastAPI(
    title="Document Processing Microservice",
    description="Microservice d'extraction de PDF financiers et d'audit pour le risque crédit",
    version="1.0.0"
)

# Instanciation unique de l'orchestrateur au démarrage du service
processor = DocumentProcessor()


# -------------------------------------------------------------
# ROUTES DE L'API
# -------------------------------------------------------------

@app.get("/")
def read_root():
    """Route de santé pour vérifier que le service fonctionne."""
    return {
        "status": "online",
        "service": "Document Processing Microservice",
        "version": "1.0.0"
    }


@app.post("/analyze/{client_id}")
def analyze_client_folder(client_id: str) -> Dict[str, Any]:
    """
    Route principale :
    1. Reçoit un ID client (ex: 'data').
    2. Localise son dossier de documents dans simulators/.
    3. Extrait toutes les informations des PDF.
    4. Enregistre automatiquement le JSON résultant dans MongoDB.
    """
    logger.info(f"Requête d'analyse reçue pour le client : {client_id}")

    # Construction du chemin dynamique vers le dossier du client
    BASE_DIR = os.path.dirname(CURRENT_DIR)
    folder_path = os.path.join(BASE_DIR, "simulators", client_id)

    # Vérification de l'existence du dossier
    if not os.path.exists(folder_path):
        logger.error(f"Dossier client introuvable : {folder_path}")
        raise HTTPException(
            status_code=404,
            detail=f"Dossier client '{client_id}' introuvable sur le serveur."
        )

    try:
        # Lancement de l'extraction + Sauvegarde MongoDB automatique
        audit_result = processor.process_client_folder(root_folder=folder_path, save_to_db=True)

        return {
            "status": "success",
            "message": f"Dossier client '{client_id}' analysé et sauvegardé dans MongoDB !",
            "data": audit_result
        }

    except Exception as e:
        logger.error(f"Erreur lors de l'analyse du client {client_id} : {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur interne lors du traitement : {str(e)}"
        )