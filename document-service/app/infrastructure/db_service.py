import os
import logging
from typing import Dict, Any, Optional
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure

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

        # MongoClient est lazy (aucune connexion réseau ici) et se reconnecte
        # tout seul : on ne le remplace JAMAIS par None sur un échec.
        # DatabaseService est instancié à l'import (main.py, via
        # DocumentProcessor), donc avant que MongoDB soit prêt au démarrage de
        # la stack Docker — l'ancien code condamnait alors la connexion
        # définitivement, et toute sauvegarde/lecture échouait silencieusement
        # jusqu'à un redémarrage manuel tombant au bon moment.
        self.client = MongoClient(self.uri, serverSelectionTimeoutMS=3000)
        self.db = self.client[self.db_name]
        self.collection = self.db["client_audits"]

        self._connected = False
        self._ensure_connected()

    def _ensure_connected(self) -> bool:
        """Vérifie (et retente) la connexion, sans jamais la condamner."""
        if self._connected:
            return True
        try:
            self.client.admin.command("ping")
            self._connected = True
            logger.info("✅ Connexion réussie à MongoDB !")
            return True
        except (ConnectionFailure, OperationFailure) as e:
            logger.error(f"❌ MongoDB injoignable (sera retenté au prochain appel) : {e}")
            return False

    def save_client_audit(self, audit_data: Dict[str, Any]) -> Optional[str]:
        """
        Sauvegarde ou met à jour le JSON maître du client.
        """
        if not self._ensure_connected():
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
        except (ConnectionFailure, OperationFailure) as e:
            self._connected = False
            logger.error(f"Erreur de sauvegarde MongoDB : {e}")
            return None
        except Exception as e:
            logger.error(f"Erreur de sauvegarde MongoDB : {e}")
            return None

    def get_client_audit(self, client_id: str) -> Optional[Dict[str, Any]]:
        """
        Récupère le JSON maître d'un client.
        """
        if not self._ensure_connected():
            logger.error("Connexion BDD non disponible pour la lecture.")
            return None
        try:
            return self.collection.find_one({"client_id": client_id}, {"_id": 0})
        except (ConnectionFailure, OperationFailure) as e:
            self._connected = False
            logger.error(f"Erreur de lecture MongoDB : {e}")
            return None