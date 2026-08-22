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

        # MongoClient est lazy (aucune connexion réseau ici) et se reconnecte
        # tout seul quand le serveur revient — on ne le remplace donc JAMAIS
        # par None sur un échec, contrairement à la version précédente.
        #
        # Pourquoi c'est important : cette classe est instanciée au niveau
        # module dans api/routes.py, donc à l'IMPORT, avant même le startup
        # FastAPI. Au démarrage de la stack Docker, MongoDB n'est pas encore
        # prêt à cet instant (depends_on n'attend que le démarrage du
        # conteneur, pas que mongod accepte les connexions) : l'ancien code
        # mettait alors self.client = None DÉFINITIVEMENT, et toutes les
        # requêtes suivantes échouaient en "Connexion BDD indisponible" ->
        # 404 "client introuvable", jusqu'à un redémarrage manuel tombant
        # au bon moment. Ici la connexion est simplement retentée au premier
        # usage suivant (voir _ensure_connected).
        self.client = MongoClient(self.uri, serverSelectionTimeoutMS=3000)
        self.db = self.client[self.db_name]

        # Collection 1 : Source des données extraites (document-service)
        self.raw_collection = self.db["client_audits"]

        # Collection 2 : Destination des analyses financières (financial-service)
        self.eval_collection = self.db["financial_evaluations"]

        self._connected = False
        self._ensure_connected()

    def _ensure_connected(self) -> bool:
        """
        Vérifie (et retente) la connexion, sans jamais la condamner
        définitivement. Le ping n'est refait que tant que la connexion n'est
        pas établie : une fois connecté, on laisse pymongo gérer lui-même les
        reconnexions plutôt que de payer un aller-retour réseau par requête.
        """
        if self._connected:
            return True
        try:
            self.db.command("ping")
            self._connected = True
            logger.info("✅ Connexion réussie de Financial-Service à MongoDB !")
            return True
        except (ConnectionFailure, OperationFailure) as e:
            logger.error(f"❌ MongoDB injoignable (sera retenté au prochain appel) : {e}")
            return False

    def get_client_audit(self, client_id: str) -> Optional[Dict[str, Any]]:
        if not self._ensure_connected():
            logger.error("Connexion BDD indisponible pour la lecture.")
            return None

        try:
            document = self.raw_collection.find_one({"client_id": client_id}, {"_id": 0})
        except (ConnectionFailure, OperationFailure) as e:
            # Connexion perdue en cours de route (MongoDB redémarré...) :
            # on repasse en "non connecté" pour que l'appel suivant repinge.
            self._connected = False
            logger.error(f"❌ Erreur de lecture MongoDB : {e}")
            return None

        if not document:
            logger.warning(f"⚠️ Aucun document trouvé pour client_id='{client_id}' dans client_audits")
        return document

    def save_evaluation_report(self, client_id: str, report: Dict[str, Any]) -> bool:
        if not self._ensure_connected():
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
        except (ConnectionFailure, OperationFailure) as e:
            self._connected = False
            logger.error(f"❌ Erreur lors de la sauvegarde du rapport : {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Erreur lors de la sauvegarde du rapport : {e}")
            return False