import os
import json
import logging
import pdfplumber
from typing import Dict, Any

# -------------------------------------------------------------
# CONFIGURATION DES LOGS
# -------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("AdministrativeExtractor")

class AdministrativeExtractor:
    """
    Extracteur spécialisé pour les documents administratifs (Demande de crédit, Fiche de renseignements).
    """

    def __init__(self):
        self.supported_files = ["demande_credit", "fiche_renseignements"]

    def extract_demande(self, pdf_path: str) -> Dict[str, Any]:
        """Extrait les données clés d'une demande de crédit via le texte brut."""
        data = {"montant_demande": None, "duree": None, "objet": None, "apport": None}
        try:
            with pdfplumber.open(pdf_path) as pdf:
                text = pdf.pages[0].extract_text()
                if text:
                    # On lit le document ligne par ligne
                    for line in text.split('\n'):
                        line_lower = line.lower()

                        # Si on trouve le mot clé, on coupe la phrase au niveau du ":" et on prend la suite
                        if "montant demandé" in line_lower:
                            data["montant_demande"] = line.split(":")[-1].strip()
                        elif "durée du crédit" in line_lower:
                            data["duree"] = line.split(":")[-1].strip()
                        elif "objet du financement" in line_lower:
                            data["objet"] = line.split(":")[-1].strip()
                        elif "apport personnel" in line_lower:
                            data["apport"] = line.split(":")[-1].strip()
        except Exception as e:
            logger.error(f"Erreur d'extraction de la Demande ({os.path.basename(pdf_path)}): {e}")
        return data

    def extract_fiche(self, pdf_path: str) -> Dict[str, Any]:
        """Extrait les données réelles présentes dans la fiche de renseignements."""
        data = {"raison_sociale": None, "capital_social": None, "secteur": None, "creation": None}
        try:
            with pdfplumber.open(pdf_path) as pdf:
                text = pdf.pages[0].extract_text()
                if text:
                    for line in text.split('\n'):
                        line_lower = line.lower()

                        if "raison sociale" in line_lower:
                            data["raison_sociale"] = line.split(":")[-1].strip()
                        elif "capital social" in line_lower:
                            data["capital_social"] = line.split(":")[-1].strip()
                        elif "activité" in line_lower:
                            data["secteur"] = line.split(":")[-1].strip()
                        elif "date de création" in line_lower:
                            data["creation"] = line.split(":")[-1].strip()
        except Exception as e:
            logger.error(f"Erreur d'extraction de la Fiche ({os.path.basename(pdf_path)}): {e}")
        return data

    def process_folder(self, folder_path: str) -> Dict[str, Any]:
        """
        Parcourt un dossier spécifié et extrait les données de tous
        les documents administratifs reconnus.
        """
        result = {}

        if not os.path.exists(folder_path):
            logger.warning(f"Le dossier spécifié n'existe pas : {folder_path}")
            return result

        for filename in os.listdir(folder_path):
            filepath = os.path.join(folder_path, filename)

            if not os.path.isfile(filepath):
                continue

            if "demande" in filename.lower():
                logger.info(f"Traitement en cours : {filename}")
                result["demande_credit"] = self.extract_demande(filepath)
            elif "fiche" in filename.lower():
                logger.info(f"Traitement en cours : {filename}")
                result["fiche_renseignements"] = self.extract_fiche(filepath)

        return result


# -------------------------------------------------------------
# BLOC DE TEST D'EXÉCUTION
# -------------------------------------------------------------
if __name__ == "__main__":

    chemin_test = r"C:\Users\pc\Desktop\credit-risk-platform\document-service\simulators\data\01_administratif"

    logger.info(f"Lancement du module d'extraction sur : {chemin_test}")

    if os.path.exists(chemin_test):
        extracteur = AdministrativeExtractor()
        donnees_extraites = extracteur.process_folder(chemin_test)

        print("\n" + "="*60)
        print("✅ EXTRACTION RÉUSSIE - SORTIE JSON")
        print("="*60)
        print(json.dumps(donnees_extraites, indent=4, ensure_ascii=False))
        print("="*60 + "\n")
    else:
        logger.error("Dossier introuvable. Vérifiez que le chemin est correct.")