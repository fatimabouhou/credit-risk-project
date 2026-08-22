import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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

# Le tableau de bord React (Vite) interroge directement l'API financière.
app.add_middleware(
    CORSMiddleware,
    # Vite may select 5174 when another local dev server owns 5173.
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_methods=["*"],
    allow_headers=["*"],
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
        # On réutilise l'instance de api/routes.py (celle qui sert réellement
        # les requêtes) au lieu d'en créer une seconde : la version précédente
        # instanciait ici un DatabaseService jetable, qui loggait "✅ Connexion
        # réussie" alors que l'instance des routes, créée plus tôt à l'import
        # (avant que MongoDB soit prêt), était définitivement hors service —
        # les logs affichaient donc une connexion OK pendant que toutes les
        # requêtes répondaient 404 "client introuvable".
        from app.api.routes import db_service

        if db_service.db is not None:
            collections = db_service.db.list_collection_names()
            if "financial_evaluations" not in collections:
                db_service.db.create_collection("financial_evaluations")
                logger.info("📁 Collection 'financial_evaluations' et BDD créées avec succès !")
            else:
                logger.info("ℹ️ La collection 'financial_evaluations' existe déjà dans MongoDB.")

            # Index unique : sans lui, l'upsert de save_evaluation_report()
            # n'est PAS atomique — deux évaluations concurrentes du même
            # client (cas réel : document-service notifie financial-service en
            # tâche de fond pendant que le frontend appelle /evaluate lui-même)
            # ne trouvent ni l'une ni l'autre de document existant et insèrent
            # chacune le leur. Constaté le 2026-08-17 : 2 documents 'ABSH'
            # créés à la même seconde, l'un avec le score Altman calculé,
            # l'autre avec des null — find_one() pouvant renvoyer le mauvais.
            db_service.eval_collection.create_index("client_id", unique=True)
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
