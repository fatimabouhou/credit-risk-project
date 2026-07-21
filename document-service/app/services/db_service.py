import os
import logging
from typing import Dict, Any, Optional
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DatabaseService")


class DatabaseService:
    """
    Gestionnaire de connexion et de stockage MongoDB.
    """

    def __init__(
            self,
            uri: Optional[str] = None,
            db_name: Optional[str] = None
    ):
        # Récupère l'URL Docker ou bascule sur localhost par défaut
        self.uri = uri or os.getenv("MONGO_URI", "mongodb://admin:adminpassword@localhost:27017/")
        self.db_name = db_name or os.getenv("MONGO_DB_NAME", "credit_risk_db")

        try:
            self.client = MongoClient(self.uri, serverSelectionTimeoutMS=3000)
            # Test de connexion (ping)
            self.client.admin.command('ping')
            self.db = self.client[self.db_name]
            self.collection = self.db["client_audits"]
            logger.info("✅ Connexion réussie à MongoDB !")
        except ConnectionFailure as e:
            logger.error(f"❌ Impossible de se connecter à MongoDB : {e}")
            self.client = None

    def save_client_audit(self, audit_data: Dict[str, Any]) -> Optional[str]:
        """
        Sauvegarde ou met à jour le JSON maître du client.
        """
        if self.client is None:
            logger.error("Connexion BDD non disponible. Sauvegarde annulée.")
            return None

        client_id = audit_data.get("client_id", "inconnu")

        try:
            # upsert=True : Crée le document s'il n'existe pas, ou le met à jour s'il existe déjà
            self.collection.update_one(
                {"client_id": client_id},
                {"$set": audit_data},
                upsert=True
            )
            logger.info(f"💾 Dossier client '{client_id}' sauvegardé dans MongoDB avec succès !")
            return client_id
        except Exception as e:
            logger.error(f"Erreur de sauvegarde MongoDB : {e}")
            return None

    def get_client_audit(self, client_id: str) -> Optional[Dict[str, Any]]:
        """
        Récupère le JSON maître d'un client.
        """
        if self.client is None:
            return None
        return self.collection.find_one({"client_id": client_id}, {"_id": 0})