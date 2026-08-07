import os
import sys
import logging
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
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

# Import du messager HTTP
from infrastructure.http_client import notify_financial_service

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

# Le frontend (React, dev server Vite) appelle cette API directement
# depuis le navigateur (déclenchement de l'extraction d'un dossier) —
# voir agentic-service/app/main.py pour le même besoin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instanciation unique de l'orchestrateur au démarrage du service
processor = DocumentProcessor()


# -------------------------------------------------------------
# 🔥 NOUVEAU : INITIALISATION AUTOMATIQUE DE LA BDD AU DÉMARRAGE
# -------------------------------------------------------------
@app.on_event("startup")
async def initialize_database():
    """
    Force la création de la BDD 'credit_risk_db' et de la collection
    'client_audits' dès que le microservice démarre dans Docker.
    """
    try:
        # On accède au client MongoDB via l'instance du processor (db_service,
        # pas "repository" — attribut inexistant qui faisait échouer
        # silencieusement cette initialisation, avalé par l'except ci-dessous)
        db = processor.db_service.db

        # Vérification et création explicite de la collection
        collections = db.list_collection_names()
        if "client_audits" not in collections:
            db.create_collection("client_audits")
            logger.info("📁 Collection 'client_audits' et BDD créées avec succès dans MongoDB !")
        else:
            logger.info("ℹ️ La collection 'client_audits' existe déjà dans MongoDB.")
    except Exception as e:
        logger.warning(f"⚠️ Impossible d'initialiser la BDD au démarrage : {str(e)}")


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


@app.get("/client/{client_id}")
def get_client_audit(client_id: str) -> Dict[str, Any]:
    """
    Récupère le dossier client déjà extrait et sauvegardé (profil
    administratif, conformité, historique financier, comportement
    bancaire) sans relancer l'extraction. Utilisé par agentic-service
    pour lire le profil du client (secteur déclaré, raison sociale...).
    """
    audit = processor.db_service.get_client_audit(client_id)
    if not audit:
        raise HTTPException(
            status_code=404,
            detail=f"Aucune donnée trouvée pour le client '{client_id}'. Le POST /analyze/{{client_id}} a-t-il déjà été exécuté ?"
        )
    return audit


@app.post("/analyze/{client_id}")
def analyze_client_folder(client_id: str, background_tasks: BackgroundTasks) -> Dict[str, Any]:
    """
    Route principale :
    1. Reçoit un ID client (ex: 'data').
    2. Localise son dossier de documents dans simulators/.
    3. Extrait toutes les informations des PDF.
    4. Enregistre automatiquement le JSON résultant dans MongoDB.
    5. Notifie le financial-service en arrière-plan.
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

        # Notification asynchrone du financial-service
        background_tasks.add_task(notify_financial_service, client_id)

        return {
            "status": "success",
            "message": f"Dossier client '{client_id}' analysé et sauvegardé. Évaluation financière déclenchée en arrière-plan.",
            "data": audit_result
        }

    except Exception as e:
        logger.error(f"Erreur lors de l'analyse du client {client_id} : {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur interne lors du traitement : {str(e)}"
        )