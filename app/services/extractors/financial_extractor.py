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
logger = logging.getLogger("FinancialExtractor")

# Champs financiers extraits, dans l'ordre où ils apparaissent typiquement
FIELDS = [
    "chiffre_affaires",
    "resultat_exploitation",
    "resultat_financier",
    "resultat_net",
    "total_actif",
    "immobilisations",
    "capitaux_propres",
    "dettes_financement",
    "dettes_court_terme",
    "tresorerie_actif",
    "tresorerie_passif",
    "creances_clients",
    "stocks",
]

# Mapping des en-têtes "Tableau : ..." bruts vers des libellés courts et stables.
# Utilisé pour que le champ "source" soit homogène même si la mise en forme du
# PDF varie légèrement d'un exercice à l'autre.
SOURCE_ALIASES = [
    (r'bilan\s*\(actif\)', "Bilan Actif"),
    (r'bilan\s*\(passif\)', "Bilan Passif"),
    (r'compte de produits et charges', "CPC"),
    (r'detail des postes du c\.?p\.?c', "CPC (détail des postes)"),
    (r'etat des soldes de gestion', "ESG"),
    (r'tableau de financement', "Tableau de financement"),
    (r'etat detaille des stocks', "État détaillé des stocks"),
    (r'tableau des immobilisations', "Tableau des immobilisations"),
    (r'tableau des amortissements', "Tableau des amortissements"),
    (r'tableau des provisions', "Tableau des provisions"),
]


class FinancialExtractor:
    def __init__(self, debug: bool = False):
        self.supported_files = ["bilan", "cpc", "liasse"]
        self.debug = debug
        # Regex pour les montants (ex: 19 974 254,32 ou -3 145 776,06)
        self.amount_pattern = re.compile(r'-?\d{1,3}(?:[ \xa0]\d{3})*(?:[,\.]\d{2})?')
        # Regex pour détecter les en-têtes de section "Tableau : XXX"
        self.table_header_pattern = re.compile(r'^tableau\s*:\s*(.+)$')

    def clean_amount(self, text_value: str) -> float:
        """Nettoie et convertit en float."""
        if not text_value:
            return 0.0
        cleaned = text_value.replace(' ', '').replace('\xa0', '').replace(',', '.')
        try:
            return float(cleaned)
        except ValueError:
            return 0.0

    def get_valid_amounts(self, line: str) -> List[float]:
        """Extrait les montants d'une ligne en ignorant les notes de bas de page (1, 2, 3...)."""
        raw_amounts = self.amount_pattern.findall(line)
        valid_amounts = []
        for raw in raw_amounts:
            val = self.clean_amount(raw)
            # On ignore les petits chiffres isolés qui sont des renvois du PDF
            if val not in [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0]:
                valid_amounts.append(val)
        return valid_amounts

    @staticmethod
    def pick_total_exercice(amounts: List[float]) -> float:
        """
        Choisit la colonne représentant le TOTAL de l'exercice en cours,
        qu'il s'agisse d'une ligne de Bilan (Brut/Amort/Net/Net N-1) ou
        d'une ligne de CPC (Propre/Concernant antérieurs/Total N/Total N-1).

        - 4 colonnes -> avant-dernière = Total exercice N
        - 3 colonnes -> avant-dernière = Total exercice N
          (cas où la colonne "concernant exercices antérieurs" est nulle
          et donc absente du texte)
        - 1 ou 2 colonnes -> première = valeur de l'exercice N
        """
        if not amounts:
            return 0.0
        if len(amounts) >= 3:
            return amounts[-2]
        return amounts[0]

    def _normalize_source(self, raw_title: str) -> str:
        """Convertit un en-tête brut 'Tableau : XXX' en libellé court et stable."""
        raw_lower = raw_title.lower().strip()
        for pattern, alias in SOURCE_ALIASES:
            if re.search(pattern, raw_lower):
                return alias
        # Repli : on garde le titre brut, nettoyé et raccourci
        return raw_title.strip().title()[:60]

    def _make_entry(self, value: float, source: Optional[str], page: int) -> Dict[str, Any]:
        """Construit l'objet tracé {value, source, page} pour une valeur trouvée."""
        return {"value": value, "source": source or "Inconnu", "page": page}

    def extract_financial_data(self, pdf_path: str, annee: str) -> Dict[str, Any]:
        data: Dict[str, Any] = {"annee": int(annee) if annee.isdigit() else annee}
        for field in FIELDS:
            data[field] = None

        try:
            with pdfplumber.open(pdf_path) as pdf:
                current_source: Optional[str] = None
                # Fallback pour "Stocks (F)" : sa ligne suit toujours la ligne
                # "TOTAL (A+B+C+D+E)" (immobilisations) dans le Bilan Actif,
                # mais son libellé utilise souvent un glyphe spécial (flèche/
                # crochet) non fiable en matching texte.
                stocks_pending = False

                for page_num, page in enumerate(pdf.pages, start=1):
                    extracted = page.extract_text()
                    if not extracted:
                        continue

                    for line in extracted.split('\n'):
                        line_stripped = line.strip()
                        line_lower = line_stripped.lower()

                        # Détection d'un en-tête de section -> met à jour la source courante
                        header_match = self.table_header_pattern.match(line_lower)
                        if header_match:
                            current_source = self._normalize_source(line_stripped.split(':', 1)[1])
                            continue

                        amounts = self.get_valid_amounts(line_stripped)

                        # Rubriques légitimement vides (aucun montant sur la ligne)
                        # mais dont on veut quand même distinguer "confirmé à 0"
                        # de "jamais trouvé" (null).
                        if not amounts:
                            if "dettes de financement (c)" in line_lower and data["dettes_financement"] is None:
                                data["dettes_financement"] = self._make_entry(0.0, current_source, page_num)
                            elif re.search(r'tr[ée]sorerie\W{0,3}passif', line_lower) and data["tresorerie_passif"] is None:
                                data["tresorerie_passif"] = self._make_entry(0.0, current_source, page_num)
                            continue

                        val_net = self.pick_total_exercice(amounts)

                        if self.debug:
                            logger.debug(
                                f"[{annee}] p.{page_num} [{current_source}] LINE: {line_stripped!r} "
                                f"-> amounts={amounts} val_net={val_net}"
                            )

                        if stocks_pending:
                            stocks_pending = False
                            if data["stocks"] is None:
                                data["stocks"] = self._make_entry(val_net, current_source, page_num)
                            continue

                        # --- CPC ---
                        if "ventes de biens et services" in line_lower and data["chiffre_affaires"] is None:
                            data["chiffre_affaires"] = self._make_entry(val_net, current_source, page_num)
                        elif "résultat d'exploitation" in line_lower or "resultat d'exploitation" in line_lower:
                            if data["resultat_exploitation"] is None:
                                data["resultat_exploitation"] = self._make_entry(val_net, current_source, page_num)
                        elif "résultat financier" in line_lower or "resultat financier" in line_lower:
                            if data["resultat_financier"] is None:
                                data["resultat_financier"] = self._make_entry(val_net, current_source, page_num)
                        elif "résultat net de l'exercice" in line_lower or "resultat net de l'exercice" in line_lower:
                            if data["resultat_net"] is None:
                                data["resultat_net"] = self._make_entry(val_net, current_source, page_num)

                        # --- BILAN ---
                        elif "total general i+ii+iii" in line_lower or "total général i+ii+iii" in line_lower:
                            if data["total_actif"] is None or val_net > data["total_actif"]["value"]:
                                data["total_actif"] = self._make_entry(val_net, current_source, page_num)
                        elif "total des capitaux propres (a)" in line_lower:
                            if data["capitaux_propres"] is None:
                                data["capitaux_propres"] = self._make_entry(val_net, current_source, page_num)
                        elif re.search(r'total\s*i?\s*\(a\+b\+c\+d\+e\)', line_lower) and data["immobilisations"] is None:
                            data["immobilisations"] = self._make_entry(val_net, current_source, page_num)
                            stocks_pending = True

                        # --- ENDETTEMENT & BFR ---
                        elif "dettes de financement (c)" in line_lower:
                            if data["dettes_financement"] is None:
                                data["dettes_financement"] = self._make_entry(val_net, current_source, page_num)
                        elif "dettes du passif circulant (f)" in line_lower:
                            if data["dettes_court_terme"] is None:
                                data["dettes_court_terme"] = self._make_entry(val_net, current_source, page_num)
                        elif "trésorerie-actif" in line_lower or "tresorerie-actif" in line_lower:
                            if data["tresorerie_actif"] is None:
                                data["tresorerie_actif"] = self._make_entry(val_net, current_source, page_num)
                        elif re.search(r'tr[ée]sorerie\W{0,3}passif', line_lower):
                            if data["tresorerie_passif"] is None:
                                data["tresorerie_passif"] = self._make_entry(val_net, current_source, page_num)
                        elif "clients et comptes rattachés" in line_lower and data["creances_clients"] is None:
                            data["creances_clients"] = self._make_entry(val_net, current_source, page_num)
                        elif re.match(r'^stocks\W{0,3}f\b', line_lower):
                            if data["stocks"] is None:
                                data["stocks"] = self._make_entry(val_net, current_source, page_num)

        except Exception as e:
            logger.error(f"Erreur d'extraction du bilan {annee} : {e}")

        return data

    def process_folder(self, folder_path: str) -> Dict[str, List[Dict[str, Any]]]:
        result = {"historique_financier": []}
        if not os.path.exists(folder_path):
            return result

        for filename in os.listdir(folder_path):
            filepath = os.path.join(folder_path, filename)
            if not os.path.isfile(filepath):
                continue

            if "bilan" in filename.lower():
                year_match = re.search(r'(20\d{2})', filename)
                annee = year_match.group(1) if year_match else "Inconnue"

                logger.info(f"Analyse financière en cours : Exercice {annee}")
                bilan_data = self.extract_financial_data(filepath, annee)
                result["historique_financier"].append(bilan_data)

        result["historique_financier"] = sorted(result["historique_financier"], key=lambda x: str(x["annee"]))
        return result


if __name__ == "__main__":
    chemin_test = r"C:\Users\pc\Desktop\credit-risk-platform\document-service\simulators\data\03_financier"
    if os.path.exists(chemin_test):
        donnees_extraites = FinancialExtractor(debug=False).process_folder(chemin_test)
        print("\n" + "=" * 60)
        print("✅ EXTRACTION AVEC TRAÇABILITÉ (value/source/page)")
        print("=" * 60)
        print(json.dumps(donnees_extraites, indent=4, ensure_ascii=False))
        print("=" * 60 + "\n")