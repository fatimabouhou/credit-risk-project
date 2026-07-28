import os
import logging
from typing import Dict, Any, Optional
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("FinancialDBService")


class DatabaseService:
    """
    Gestionnaire BDD pour financial-service.
    Gère la lecture des données brutes et la sauvegarde des évaluations.
    """

    def __init__(self, uri: Optional[str] = None, db_name: Optional[str] = None):
        self.uri = uri or os.getenv("MONGO_URI", "mongodb://localhost:27017/")
        self.db_name = db_name or os.getenv("MONGO_DB_NAME", "credit_risk_db")

        try:
            self.client = MongoClient(self.uri, serverSelectionTimeoutMS=3000)
            self.db = self.client[self.db_name]

            # 💡 FIX : On teste le ping sur la BDD de l'application (self.db) au lieu de self.client.admin
            self.db.command('ping')

            # Collection 1 : Source des données extraites (document-service)
            self.raw_collection = self.db["client_audits"]

            # Collection 2 : Destination des analyses financières (financial-service)
            self.eval_collection = self.db["financial_evaluations"]

            logger.info("✅ Connexion réussie de Financial-Service à MongoDB !")
        except (ConnectionFailure, OperationFailure) as e:
            logger.error(f"❌ Erreur de connexion/authentification MongoDB : {e}")
            self.client = None

    def get_client_audit(self, client_id: str) -> Optional[Dict[str, Any]]:
        if self.client is None:
            logger.error("Connexion BDD indisponible pour la lecture.")
            return None

        document = self.raw_collection.find_one({"client_id": client_id}, {"_id": 0})
        if not document:
            logger.warning(f"⚠️ Aucun document trouvé pour client_id='{client_id}' dans client_audits")
        return document

    def save_evaluation_report(self, client_id: str, report: Dict[str, Any]) -> bool:
        if self.client is None:
            logger.error("Connexion BDD indisponible pour la sauvegarde.")
            return False

        try:
            self.eval_collection.update_one(
                {"client_id": client_id},
                {"$set": report},
                upsert=True
            )
            logger.info(f"💾 Rapport financier sauvegardé avec succès pour le client '{client_id}' !")
            return True
        except Exception as e:
            logger.error(f"❌ Erreur lors de la sauvegarde du rapport : {e}")
            return False