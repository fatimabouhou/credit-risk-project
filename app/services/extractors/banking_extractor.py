import os
import json
import logging
import re
import pdfplumber
from typing import Dict, Any, List, Optional

# -------------------------------------------------------------
# CONFIGURATION DES LOGS
# -------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("BankingExtractor")

class BankingExtractor:
    """
    Extracteur bancaire spécialisé pour l'analyse de risque de crédit.
    Fournit une traçabilité complète (value, source, page) et le détail par engagement.
    """

    def clean_amount(self, text_value: str) -> float:
        """Nettoie une chaîne comptable (ex: '47,645,000.00' -> 47645000.0)."""
        if not text_value:
            return 0.0
        cleaned = re.sub(r'[^\d,\.-]', '', text_value)
        if ',' in cleaned and '.' in cleaned:
            cleaned = cleaned.replace(',', '')
        elif ',' in cleaned and '.' not in cleaned:
            parts = cleaned.split(',')
            if len(parts[-1]) == 3:
                cleaned = cleaned.replace(',', '')
            else:
                cleaned = cleaned.replace(',', '.')
        try:
            return float(cleaned)
        except ValueError:
            return 0.0

    def _make_entry(self, value: Any, source: str, page: int) -> Dict[str, Any]:
        """Format standard de traçabilité pour tous les extracteurs."""
        return {"value": value, "source": source, "page": page}

    def extract_centrale_risques(self, pdf_path: str) -> Dict[str, Any]:
        """Analyse le relevé consolidé de Bank Al-Maghrib."""
        filename = os.path.basename(pdf_path)
        data = {
            "ice": self._make_entry(None, filename, 1),
            "total_autorisation": self._make_entry(0.0, filename, 1),
            "total_encours_utilise": self._make_entry(0.0, filename, 1),
            "taux_utilisation": self._make_entry(0.0, filename, 1),
            "incidents": {
                "incidents_definis": self._make_entry(False, filename, 1),
                "statut_incidents": self._make_entry("Aucun incident déclaré", filename, 1),
                "nombre_incidents": self._make_entry(0, filename, 1)
            }
        }
        try:
            with pdfplumber.open(pdf_path) as pdf:
                page = pdf.pages[0]
                full_text = page.extract_text() or ""

                # 1. Extraction ICE
                ice_match = re.search(r'\(ICE\)\s*[\:\-]?\s*(\d{15})', full_text, re.IGNORECASE)
                if ice_match:
                    data["ice"] = self._make_entry(ice_match.group(1), filename, 1)

                # 2. Gestion des Incidents
                if "néant" in full_text.lower() or "aucun incident" in full_text.lower():
                    data["incidents"]["incidents_definis"] = self._make_entry(False, filename, 1)
                    data["incidents"]["statut_incidents"] = self._make_entry("NÉANT (Aucun incident)", filename, 1)
                else:
                    data["incidents"]["incidents_definis"] = self._make_entry(True, filename, 1)
                    data["incidents"]["statut_incidents"] = self._make_entry("Incidents détectés", filename, 1)

                # 3. Engagements & Ratios
                for line in full_text.split('\n'):
                    if "TOTAL DES ENGAGEMENTS" in line.upper():
                        amounts = re.findall(r'\d{1,3}(?:,\d{3})+', line)
                        if len(amounts) >= 2:
                            aut = self.clean_amount(amounts[0])
                            enc = self.clean_amount(amounts[1])
                            data["total_autorisation"] = self._make_entry(aut, filename, 1)
                            data["total_encours_utilise"] = self._make_entry(enc, filename, 1)

                            taux = round((enc / aut) * 100, 2) if aut > 0 else 0.0
                            data["taux_utilisation"] = self._make_entry(taux, filename, 1)

        except Exception as e:
            logger.error(f"Erreur Centrale des Risques ({filename}): {e}")

        return data

    def extract_releve(self, pdf_path: str, banque_name: str) -> Dict[str, Any]:
        """Extrait les soldes, flux et comportements d'un relevé bancaire."""
        filename = os.path.basename(pdf_path)
        data = {
            "banque": banque_name,
            "solde_fin_periode": self._make_entry(None, filename, 1),
            "total_crediteur": self._make_entry(0.0, filename, 1),
            "total_debiteur": self._make_entry(0.0, filename, 1),
            "comportement": {
                "nombre_rejets": self._make_entry(0, filename, 1),
                "decouvert_max_detecte": self._make_entry(0.0, filename, 1)
            }
        }
        try:
            with pdfplumber.open(pdf_path) as pdf:
                full_text = ""
                has_explicit_totals = False

                for page_idx, page in enumerate(pdf.pages, start=1):
                    page_text = page.extract_text() or ""
                    full_text += page_text + "\n"

                    for line in page_text.split('\n'):
                        line_upper = line.upper()

                        if "SOLDE FINAL AU" in line_upper or "NOUVEAU SOLDE AU" in line_upper:
                            amounts = re.findall(r'\d{1,3}(?:[,\s\.]\d{3})*(?:\.\d{2})?', line)
                            if amounts:
                                data["solde_fin_periode"] = self._make_entry(self.clean_amount(amounts[-1]), filename, page_idx)

                        elif "TOTAL DES MOUVEMENTS" in line_upper or "TOTAL MOUVEMENTS" in line_upper:
                            amounts = re.findall(r'\d{1,3}(?:[,\s\.]\d{3})*(?:\.\d{2})?', line)
                            if len(amounts) >= 2:
                                data["total_debiteur"] = self._make_entry(self.clean_amount(amounts[0]), filename, page_idx)
                                data["total_crediteur"] = self._make_entry(self.clean_amount(amounts[1]), filename, page_idx)
                                has_explicit_totals = True

                # Calcul dynamique des colonnes si pas de sous-total explicite
                if not has_explicit_totals:
                    tot_deb = 0.0
                    tot_cred = 0.0
                    for page_idx, page in enumerate(pdf.pages, start=1):
                        tables = page.extract_tables()
                        for table in tables:
                            for row in table:
                                if len(row) >= 6:
                                    deb = self.clean_amount(row[-3]) if len(row) > 3 and row[-3] else 0.0
                                    cred = self.clean_amount(row[-1]) if row[-1] else 0.0
                                    tot_deb += deb
                                    tot_cred += cred
                    data["total_debiteur"] = self._make_entry(tot_deb, filename, 1)
                    data["total_crediteur"] = self._make_entry(tot_cred, filename, 1)

        except Exception as e:
            logger.error(f"Erreur Relevé {banque_name}: {e}")

        return data

    def extract_amortissement(self, pdf_path: str) -> Dict[str, Any]:
        """Extrait le détail de chaque crédit et les synthèses de la dette."""
        filename = os.path.basename(pdf_path)
        data = {
            "credits_detailles": [],
            "mensualite_totale": self._make_entry(0.0, filename, 1),
            "capital_restant_total": self._make_entry(0.0, filename, 1)
        }
        try:
            with pdfplumber.open(pdf_path) as pdf:
                full_text = pdf.pages[0].extract_text() or ""

                # Découpage par bloc de crédit
                blocks = re.split(r'(CREDIT\s+[A-Z\s\-]+)', full_text)
                tot_mensualite = 0.0
                tot_encours = 0.0

                # Parcours des paires (Titre crédit, Contenu)
                for i in range(1, len(blocks), 2):
                    title = blocks[i].strip()
                    content = blocks[i+1] if i+1 < len(blocks) else ""

                    mensualite_match = re.search(r'Mensualité:\s*([\d,]+)\s*DH', content, re.IGNORECASE)
                    encours_match = re.search(r'Capital restant[^\:]*:\s*([\d,]+)\s*DH', content, re.IGNORECASE)

                    m_val = self.clean_amount(mensualite_match.group(1)) if mensualite_match else 0.0
                    e_val = self.clean_amount(encours_match.group(1)) if encours_match else 0.0

                    tot_mensualite += m_val
                    tot_encours += e_val

                    data["credits_detailles"].append({
                        "intitule": title,
                        "mensualite": self._make_entry(m_val, filename, 1),
                        "capital_restant": self._make_entry(e_val, filename, 1)
                    })

                data["mensualite_totale"] = self._make_entry(tot_mensualite, filename, 1)
                data["capital_restant_total"] = self._make_entry(tot_encours, filename, 1)

        except Exception as e:
            logger.error(f"Erreur Amortissement: {e}")

        return data

    def process_folder(self, folder_path: str) -> Dict[str, Any]:
        result = {
            "comptes_bancaires": [],
            "dette_existante": {},
            "centrale_risques": {}
        }

        if not os.path.exists(folder_path):
            logger.warning(f"Le dossier spécifié n'existe pas : {folder_path}")
            return result

        for filename in os.listdir(folder_path):
            filepath = os.path.join(folder_path, filename)
            if not os.path.isfile(filepath):
                continue

            file_lower = filename.lower()

            if "releve" in file_lower and "risque" not in file_lower:
                banque = "Attijariwafa Bank" if "attijari" in file_lower else "CIH Bank" if "cih" in file_lower else "Autre Banque"
                logger.info(f"Traitement relevé bancaire ({banque}) : {filename}")
                result["comptes_bancaires"].append(self.extract_releve(filepath, banque))

            elif "amortissement" in file_lower or "echeancier" in file_lower:
                logger.info(f"Traitement tableau d'amortissement : {filename}")
                result["dette_existante"] = self.extract_amortissement(filepath)

            elif "risque" in file_lower or "central" in file_lower:
                logger.info(f"Traitement Centrale des Risques (BAM) : {filename}")
                result["centrale_risques"] = self.extract_centrale_risques(filepath)

        return result


if __name__ == "__main__":
    chemin_test = r"C:\Users\pc\Desktop\credit-risk-platform\document-service\simulators\data\04_bancaire"

    if os.path.exists(chemin_test):
        extracteur = BankingExtractor()
        donnees_extraites = extracteur.process_folder(chemin_test)

        print("\n" + "="*60)
        print("✅ EXTRACTION BANCAIRE FINALE (TRACÉE & DÉTAILLÉE)")
        print("="*60)
        print(json.dumps(donnees_extraites, indent=4, ensure_ascii=False))
        print("="*60 + "\n")