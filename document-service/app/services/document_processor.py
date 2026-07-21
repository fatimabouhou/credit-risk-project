import os
import sys
import json
import logging
from typing import Dict, Any

# -------------------------------------------------------------
# GESTION DYNAMIQUE DU PYTHONPATH
# -------------------------------------------------------------
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

# Importation des 4 extracteurs spécialisés
from extractors.administrative_extractor import AdministrativeExtractor
from extractors.compliance_extractor import ComplianceExtractor
from extractors.financial_extractor import FinancialExtractor
from extractors.banking_extractor import BankingExtractor

# Importation du service BDD MongoDB
from db_service import DatabaseService

# -------------------------------------------------------------
# CONFIGURATION DES LOGS
# -------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("DocumentProcessor")


class DocumentProcessor:
    """
    Orchestrateur central du service documentaire.
    Parcourt l'ensemble des sous-dossiers d'un client, agrège les données
    et enregistre le résultat dans MongoDB.
    """

    def __init__(self):
        logger.info("Initialisation des moteurs d'extraction et de la BDD...")
        self.admin_extractor = AdministrativeExtractor()
        self.compliance_extractor = ComplianceExtractor()
        self.financial_extractor = FinancialExtractor()
        self.banking_extractor = BankingExtractor()

        # Initialisation du service MongoDB
        self.db_service = DatabaseService()

    def process_client_folder(self, root_folder: str, save_to_db: bool = True) -> Dict[str, Any]:
        """
        Analyse l'intégralité du dossier client, agrège les données et sauvegarde en BDD.
        """
        logger.info(f"=== DÉBUT D'ANALYSE DU DOSSIER : {os.path.basename(root_folder)} ===")

        paths = {
            "01_administratif": os.path.join(root_folder, "01_administratif"),
            "02_conformite": os.path.join(root_folder, "02_conformite"),
            "03_financier": os.path.join(root_folder, "03_financier"),
            "04_bancaire": os.path.join(root_folder, "04_bancaire")
        }

        # Structure du JSON maître unifié
        global_data = {
            "client_id": os.path.basename(root_folder),
            "profil_administratif": {},
            "conformite_reglementaire": {},
            "historique_financier": {},
            "comportement_bancaire": {},
            "alertes_coherence": []
        }

        # 1. Extraction Administratif
        if os.path.exists(paths["01_administratif"]):
            logger.info("--> Exécution de AdministrativeExtractor...")
            global_data["profil_administratif"] = self.admin_extractor.process_folder(paths["01_administratif"])

        # 2. Extraction Conformité (DGI / CNSS)
        if os.path.exists(paths["02_conformite"]):
            logger.info("--> Exécution de ComplianceExtractor...")
            global_data["conformite_reglementaire"] = self.compliance_extractor.process_folder(paths["02_conformite"])

        # 3. Extraction Financière (Liasse Fiscale)
        if os.path.exists(paths["03_financier"]):
            logger.info("--> Exécution de FinancialExtractor...")
            global_data["historique_financier"] = self.financial_extractor.process_folder(paths["03_financier"])

        # 4. Extraction Bancaire (Relevés, Amortissements, BAM)
        if os.path.exists(paths["04_bancaire"]):
            logger.info("--> Exécution de BankingExtractor...")
            global_data["comportement_bancaire"] = self.banking_extractor.process_folder(paths["04_bancaire"])

        # 5. Contrôles de cohérence croisés (Cross-Checking)
        self._check_coherence(global_data)

        # 6. Sauvegarde du dictionnaire extrait dans MongoDB
        if save_to_db:
            self.db_service.save_client_audit(global_data)

        logger.info("=== FIN DE L'ANALYSE GLOBALE ===")
        return global_data

    def _check_coherence(self, data: Dict[str, Any]):
        """
        Vérifie la cohérence croisée des informations extraites.
        """
        bancaire = data.get("comportement_bancaire", {})
        centrale = bancaire.get("centrale_risques", {})
        incidents = centrale.get("incidents", {}).get("incidents_definis", {}).get("value")

        if incidents:
            data["alertes_coherence"].append("⚠️ ALERTE : Présence d'incidents de paiement à la Centrale des Risques BAM.")


# -------------------------------------------------------------
# BLOC DE TEST
# -------------------------------------------------------------
if __name__ == "__main__":
    # Détection intelligente et adaptative du dossier simulators/data
    # document_processor.py est dans app/services/ -> remonte de 2 niveaux vers la racine du microservice
    CURRENT_FILE_DIR = os.path.dirname(os.path.abspath(__file__))
    BASE_DIR = os.path.dirname(os.path.dirname(CURRENT_FILE_DIR))

    dossier_client_racine = os.path.join(BASE_DIR, "simulators", "data")

    # Fallback de sécurité si l'arborescence varie
    if not os.path.exists(dossier_client_racine):
        dossier_client_racine = os.path.join(os.path.dirname(CURRENT_FILE_DIR), "simulators", "data")

    if os.path.exists(dossier_client_racine):
        orchestrator = DocumentProcessor()
        json_maitre = orchestrator.process_client_folder(dossier_client_racine)

        print("\n" + "="*80)
        print("🚀 JSON MAÎTRE UNIFIÉ - EXTRAIT ET ENREGISTRÉ DANS MONGODB")
        print("="*80)
        print(json.dumps(json_maitre, indent=4, ensure_ascii=False))
        print("="*80 + "\n")
    else:
        logger.error(f"Dossier racine introuvable : {dossier_client_racine}")