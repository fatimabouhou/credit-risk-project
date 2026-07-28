from typing import Dict, Any, Optional, List
import logging

from .ratios import RatiosHub
from .trends import TrendsEngine
from .dscr import DSCREngine

logger = logging.getLogger("EvaluatorService")


class FinancialEvaluator:
    """
    Chef d'orchestre global de l'analyse financière.
    Prend le document MongoDB imbriqué et coordonne l'extraction, les ratios,
    les tendances et la viabilité de la dette.
    """

    @staticmethod
    def extract_flat_year_data(mongo_document: Dict[str, Any], year: int) -> Dict[str, float]:
        """
        Extracteur / Adapter : Convertit le bloc 'historique_financier' d'une année spécifique
        du format MongoDB imbriqué ({'value': X}) en un dictionnaire plat (float).
        """
        flat_data = {}
        historique_list = mongo_document.get("historique_financier", {}).get("historique_financier", [])

        # Recherche du bloc correspondant à l'année (ex: 2023)
        year_block = next((item for item in historique_list if item.get("annee") == year), None)

        if not year_block:
            logger.warning(f"Aucune donnée financière trouvée pour l'année {year}")
            return flat_data

        # On parcourt chaque poste et on extrait uniquement la clé 'value'
        for key, content in year_block.items():
            if isinstance(content, dict) and "value" in content:
                try:
                    flat_data[key] = float(content["value"])
                except (ValueError, TypeError):
                    flat_data[key] = 0.0
            elif isinstance(content, (int, float)) and key != "annee":
                flat_data[key] = float(content)

        return flat_data

    @classmethod
    def _enrich_year_data(cls, data: Dict[str, float]) -> Dict[str, float]:
        """
        Enrichit les dictionnaires d'années avec les fallbacks nécessaires
        afin qu'aucun indicateur vital ne manque (ebitda, total_dettes, fonds_propres).
        """
        if not data:
            return data

        # 1. Fallback EBITDA
        if "ebitda" not in data or data.get("ebitda") == 0:
            data["ebitda"] = data.get("resultat_exploitation") or data.get("ebit", 0.0)

        # 2. Total Dettes (LT + CT)
        if "total_dettes" not in data or data.get("total_dettes") == 0:
            dettes_lt = data.get("dettes_financement", 0.0)
            dettes_ct = data.get("dettes_court_terme", 0.0)
            data["total_dettes"] = dettes_lt + dettes_ct

        # 3. Fonds Propres / Capitaux Propres
        if "fonds_propres" not in data or data.get("fonds_propres") == 0:
            data["fonds_propres"] = data.get("capitaux_propres", 0.0)

        return data

    @classmethod
    def evaluate_full_dossier(cls, mongo_document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Point d'entrée principal : prend tout le document MongoDB et génère le rapport complet.
        """
        client_id = mongo_document.get("client_id", "Inconnu")
        logger.info(f"⚡ Début de l'évaluation financière pour le dossier client : {client_id}")

        # 1. Extraction et aplatissement des 3 années
        data_2023 = cls.extract_flat_year_data(mongo_document, 2023)
        data_2022 = cls.extract_flat_year_data(mongo_document, 2022)
        data_2021 = cls.extract_flat_year_data(mongo_document, 2021)

        # 2. Enrichissement des données pour harmoniser les noms de variables
        data_2023 = cls._enrich_year_data(data_2023)
        data_2022 = cls._enrich_year_data(data_2022)
        data_2021 = cls._enrich_year_data(data_2021)

        # 3. Récupération de l'annuité pour le calcul du DSCR
        dette_info = mongo_document.get("comportement_bancaire", {}).get("dette_existante", {})
        mensualite_totale_annuelle = dette_info.get("mensualite_totale", {}).get("value", 0.0) * 12

        # Injecte l'annuité dans les données 2023 pour le RatiosHub
        data_2023["annuite_emprunts"] = mensualite_totale_annuelle

        # 4. Calcul des Ratios sur l'année la plus récente (N = 2023)
        ratios_2023 = RatiosHub.calculate_all_ratios(data_2023)

        # 5. Analyse des Tendances Historiques sur 3 ans (N, N-1, N-2)
        tendances = TrendsEngine.analyze_trends(
            data_n=data_2023,
            data_n_1=data_2022,
            data_n_2=data_2021
        )

        # 6. Calcul de la Capacité de Remboursement (DSCR)
        ebitda_2023 = data_2023.get("ebitda", 0.0)
        dscr_analysis = DSCREngine.calculate_dscr(
            ebitda=ebitda_2023,
            annuite_emprunts=mensualite_totale_annuelle
        )

        # 7. Assemblage final
        evaluation_report = {
            "client_id": client_id,
            "statut_evaluation": "SUCCÈS",
            "annee_reference": 2023,
            "ratios_financiers_n": ratios_2023,
            "analyse_tendances_3ans": tendances,
            "couverture_dette_dscr": dscr_analysis,
            "donnees_brutes_applaties": {
                "2023": data_2023,
                "2022": data_2022,
                "2021": data_2021
            }
        }

        logger.info(f"✅ Évaluation financière terminée pour '{client_id}' !")
        return evaluation_report