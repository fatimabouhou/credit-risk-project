import os
import json
import logging
import re
import pdfplumber
from typing import Dict, Any, List

# -------------------------------------------------------------
# CONFIGURATION DES LOGS
# -------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("ComplianceExtractor")

class ComplianceExtractor:
    """
    Extracteur spécialisé pour les documents de conformité (Attestations DGI, CNSS).
    Vérifie la régularité fiscale et sociale de l'entreprise.
    """

    def __init__(self):
        self.supported_files = ["attestation_dgi", "attestation_cnss"]

    def extract_attestation(self, pdf_path: str, doc_source: str) -> Dict[str, Any]:
        """Extrait l'ICE et le statut de conformité d'une attestation."""
        data = {
            "source": doc_source,
            "ice": None,
            "is_compliant": False,
            "statut_texte": "Inconnu"
        }

        try:
            with pdfplumber.open(pdf_path) as pdf:
                text = pdf.pages[0].extract_text()

                if text:
                    # 1. Extraction de l'ICE (15 chiffres consécutifs)
                    ice_match = re.search(r'([0-9]{15})', text)
                    if ice_match:
                        data["ice"] = ice_match.group(1)

                    # 2. Vérification sémantique de la régularité
                    text_lower = text.lower()
                    mots_cles_positifs = ["en règle", "régulière", "à jour", "n'a pas de dette", "régularité"]

                    if any(mot in text_lower for mot in mots_cles_positifs):
                        data["is_compliant"] = True
                        data["statut_texte"] = "En règle"
                    else:
                        data["is_compliant"] = False
                        data["statut_texte"] = "Non conforme / Anomalie détectée"

        except Exception as e:
            logger.error(f"Erreur d'extraction de l'attestation {doc_source} ({os.path.basename(pdf_path)}): {e}")

        return data

    def process_folder(self, folder_path: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Parcourt le dossier et analyse toutes les attestations de conformité.
        """
        result = {"attestations_legales": []}

        if not os.path.exists(folder_path):
            logger.warning(f"Le dossier spécifié n'existe pas : {folder_path}")
            return result

        for filename in os.listdir(folder_path):
            filepath = os.path.join(folder_path, filename)

            if not os.path.isfile(filepath):
                continue

            # Routage vers la même logique mais en taggant la source (DGI ou CNSS)
            if "dgi" in filename.lower():
                logger.info(f"Analyse fiscale en cours : {filename}")
                result["attestations_legales"].append(self.extract_attestation(filepath, "DGI"))
            elif "cnss" in filename.lower():
                logger.info(f"Analyse sociale en cours : {filename}")
                result["attestations_legales"].append(self.extract_attestation(filepath, "CNSS"))

        return result


# -------------------------------------------------------------
# BLOC DE TEST D'EXÉCUTION
# -------------------------------------------------------------
if __name__ == "__main__":

    # Chemin vers ton dossier de conformité
    chemin_test = r"C:\Users\pc\Desktop\credit-risk-platform\document-service\simulators\data\02_conformite"

    logger.info(f"Lancement du module d'extraction sur : {chemin_test}")

    if os.path.exists(chemin_test):
        extracteur = ComplianceExtractor()
        donnees_extraites = extracteur.process_folder(chemin_test)

        print("\n" + "="*60)
        print("✅ EXTRACTION DE CONFORMITÉ RÉUSSIE - SORTIE JSON")
        print("="*60)
        print(json.dumps(donnees_extraites, indent=4, ensure_ascii=False))
        print("="*60 + "\n")
    else:
        logger.error("Dossier introuvable. Vérifiez que le chemin est correct.")