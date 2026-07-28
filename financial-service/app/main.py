import logging
from fastapi import FastAPI
from app.api.routes import router as evaluation_router

# Configuration des logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("FinancialServiceAPI")

# Initialisation de l'application FastAPI
app = FastAPI(
    title="Financial Service API",
    description="Microservice chargé de l'analyse financière, du calcul des ratios et du scoring.",
    version="1.0.0"
)


# -------------------------------------------------------------
# 🔥 INITIALISATION AUTOMATIQUE DE LA BDD AU DÉMARRAGE
# -------------------------------------------------------------
@app.on_event("startup")
async def initialize_database():
    """
    Force la création de la BDD 'credit_risk_db' et de la collection
    'financial_evaluations' dès le démarrage du conteneur Docker.
    """
    try:
        # Import basé sur ton arborescence : app.db.database_service
        from app.db.database_service import DatabaseService

        # Connexion à la BDD
        db_service = DatabaseService()

        if db_service.db is not None:
            collections = db_service.db.list_collection_names()
            if "financial_evaluations" not in collections:
                db_service.db.create_collection("financial_evaluations")
                logger.info("📁 Collection 'financial_evaluations' et BDD créées avec succès !")
            else:
                logger.info("ℹ️ La collection 'financial_evaluations' existe déjà dans MongoDB.")
    except Exception as e:
        logger.warning(f"⚠️ Impossible d'initialiser la BDD au démarrage : {str(e)}")


# Inclusion des routes
app.include_router(evaluation_router, prefix="/api/v1/financial", tags=["Evaluation"])


# Route de santé (Health Check) pour Docker / API Gateway
@app.get("/health", tags=["System"])
def health_check():
    """
    Vérifie que le service est en ligne.
    """
    return {
        "status": "online",
        "service": "financial-service"
    }