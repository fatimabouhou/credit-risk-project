import os
import sys
import json
import logging
from typing import Dict, Any

# -------------------------------------------------------------
# GESTION DYNAMIQUE DU PYTHONPATH
# -------------------------------------------------------------
# Ce fichier est dans app/services/ -> on remonte d'un niveau pour arriver à app/
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))   # app/services
APP_DIR = os.path.dirname(CURRENT_DIR)                      # app/
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

# Importation des 4 extracteurs spécialisés (depuis app/services/extractors/)
from services.extractors.administrative_extractor import AdministrativeExtractor
from services.extractors.compliance_extractor import ComplianceExtractor
from services.extractors.financial_extractor import FinancialExtractor
from services.extractors.banking_extractor import BankingExtractor
from services.extractors.guarantee_extractor import GuaranteeExtractor

# Importation du service BDD MongoDB (depuis app/infrastructure/)
from infrastructure.db_service import DatabaseService

# -------------------------------------------------------------
# CONFIGURATION DES LOGS
# -------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("DocumentProcessor")

# Écart relatif (trésorerie déclarée au bilan vs solde bancaire observé sur
# les relevés) au-delà duquel on signale une alerte de cohérence — 25% pour
# ne réagir qu'à un vrai décalage, pas au bruit normal entre la date de
# clôture du bilan et la période couverte par le(s) relevé(s).
TRESORERIE_ECART_ALERTE_PCT = 0.25


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
        self.guarantee_extractor = GuaranteeExtractor()

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
            "04_bancaire": os.path.join(root_folder, "04_bancaire"),
            "05_garanties": os.path.join(root_folder, "05_garanties")
        }

        # Structure du JSON maître unifié
        global_data = {
            "client_id": os.path.basename(root_folder),
            "profil_administratif": {},
            "conformite_reglementaire": {},
            "historique_financier": {},
            "comportement_bancaire": {},
            "garanties": {},
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

        # 5. Extraction des garanties proposées
        if os.path.exists(paths["05_garanties"]):
            global_data["garanties"] = self.guarantee_extractor.process_folder(paths["05_garanties"])

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

        self._check_coherence_tresorerie(data)

    def _check_coherence_tresorerie(self, data: Dict[str, Any]):
        """
        Compare le solde bancaire réellement observé sur les relevés (somme de
        "solde_fin_periode" de chaque compte, comptes_bancaires vient de
        BankingExtractor) à la trésorerie-actif déclarée au bilan de l'exercice
        le plus récent — signale un écart significatif plutôt que de laisser
        les deux sources diverger silencieusement.

        Ne modifie jamais les ratios ni la trésorerie utilisée par
        financial-service (qui ne lit que historique_financier) : ce contrôle
        n'ajoute qu'une alerte informative dans alertes_coherence, déjà lue
        par outil_validation_dossier côté agentic-service pour nuancer la
        confiance à accorder aux ratios plutôt qu'un nouveau chiffre à
        interpréter.

        Silencieux (aucune alerte) si l'une des deux sources manque : un
        dossier sans relevé bancaire, ou sans bilan exploitable, ne permet
        aucune comparaison fiable.
        """
        comptes = data.get("comportement_bancaire", {}).get("comptes_bancaires", [])
        soldes = [
            c["solde_fin_periode"]["value"]
            for c in comptes
            if c.get("solde_fin_periode", {}).get("value") is not None
        ]
        if not soldes:
            return
        solde_bancaire_total = sum(soldes)

        historique = data.get("historique_financier", {}).get("historique_financier", [])
        if not historique:
            return
        dernier_exercice = historique[-1]
        tresorerie = dernier_exercice.get("tresorerie_actif")
        if tresorerie is None or tresorerie.get("value") is None:
            return
        tresorerie_declaree = tresorerie["value"]

        base = max(abs(solde_bancaire_total), abs(tresorerie_declaree))
        if base == 0:
            return
        ecart_pct = abs(solde_bancaire_total - tresorerie_declaree) / base

        if ecart_pct > TRESORERIE_ECART_ALERTE_PCT:
            data["alertes_coherence"].append(
                "⚠️ ALERTE : Trésorerie déclarée au bilan "
                f"({tresorerie_declaree:,.0f} MAD) incohérente avec le solde observé sur "
                f"les relevés bancaires ({solde_bancaire_total:,.0f} MAD) — écart de "
                f"{ecart_pct:.0%}."
            )


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