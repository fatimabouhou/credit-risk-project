from typing import Dict, Any, Optional, List
import logging
import os
import re

from .ratios import RatiosHub
from .trends import TrendsEngine
from .dscr import DSCREngine
from .scoring import ScoringEngine
from .guarantees import assess_guarantees

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

        # 4. Fonds de roulement (Working Capital) = Actif circulant - Passif circulant,
        # même logique de repli que RatiosHub.calculate_all_ratios (dupliquée ici
        # plutôt que réutilisée : ce module ne dépend pas de RatiosHub, et cette
        # valeur est nécessaire avant l'appel à RatiosHub, pour le score Altman).
        if "working_capital" not in data:
            stocks = data.get("stocks", 0.0)
            creances = data.get("creances_clients", 0.0)
            treso_actif = data.get("tresorerie_actif", 0.0)
            actif_circulant = data.get("actif_circulant") or (stocks + creances + treso_actif)
            passif_circulant = data.get("passif_circulant") or data.get("dettes_court_terme", 0.0)
            data["working_capital"] = actif_circulant - passif_circulant

        return data

    @staticmethod
    def _parse_positive_number(value: Any) -> Optional[float]:
        """Parse un montant extrait d'un PDF sans confondre texte invalide et zéro."""
        if isinstance(value, (int, float)):
            return float(value) if value > 0 else None
        if not isinstance(value, str):
            return None
        normalized = value.replace("\u202f", "").replace(" ", "")
        normalized = re.sub(r"[^0-9,.-]", "", normalized)
        if not normalized:
            return None
        if "," in normalized and "." in normalized:
            normalized = normalized.replace(".", "").replace(",", ".")
        else:
            normalized = normalized.replace(",", ".")
        try:
            parsed = float(normalized)
        except ValueError:
            return None
        return parsed if parsed > 0 else None

    @staticmethod
    def _parse_duration_months(value: Any) -> Optional[int]:
        if not isinstance(value, str):
            parsed = FinancialEvaluator._parse_positive_number(value)
            return int(parsed) if parsed is not None else None
        match = re.search(r"(\d+(?:[,.]\d+)?)\s*(an|ans|année|années|mois)?", value.lower())
        if not match:
            return None
        number = float(match.group(1).replace(",", "."))
        unit = match.group(2) or "mois"
        months = number * 12 if unit in {"an", "ans", "année", "années"} else number
        return int(months) if months > 0 and months.is_integer() else None

    @classmethod
    def _extract_new_credit_terms(cls, mongo_document: Dict[str, Any]) -> tuple[Optional[float], Optional[int]]:
        demande = mongo_document.get("profil_administratif", {}).get("demande_credit", {})
        montant = cls._parse_positive_number(demande.get("montant_demande"))
        return montant, cls._parse_duration_months(demande.get("duree"))

    @staticmethod
    def _annees_disponibles(mongo_document: Dict[str, Any]) -> List[int]:
        """
        Années réellement présentes dans historique_financier, triées de la
        plus récente à la plus ancienne — plutôt que de supposer 2023/2022/2021
        en dur : un dossier avec un seul exercice (ex. 2024 seul) n'a alors
        aucune donnée sous "2023", et extract_flat_year_data renvoyait un
        dict vide en silence (ratios/Altman/DSCR à 0 sans erreur explicite).
        """
        historique_list = mongo_document.get("historique_financier", {}).get("historique_financier", [])
        annees = {
            item.get("annee") for item in historique_list if isinstance(item.get("annee"), int)
        }
        return sorted(annees, reverse=True)

    @classmethod
    def evaluate_full_dossier(
        cls,
        mongo_document: Dict[str, Any],
        is_listed: bool = False,
        is_manufacturier: Optional[bool] = None,
        market_value_equity: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Point d'entrée principal : prend tout le document MongoDB et génère le rapport complet.

        `is_listed` / `is_manufacturier` / `market_value_equity` : voir
        ScoringEngine.calculate_altman_z_score — aucune de ces données
        n'existe dans le dossier client aujourd'hui, destinées à être
        saisies par l'utilisateur via une future interface (voir
        app/api/routes.py). Sans elles, le score Altman utilise
        systématiquement la formule Z'' (1995), la plus générale.
        """
        client_id = mongo_document.get("client_id", "Inconnu")
        logger.info(f"⚡ Début de l'évaluation financière pour le dossier client : {client_id}")

        # 1. Détermine N / N-1 / N-2 depuis les années réellement présentes dans
        # le dossier (pas 2023/2022/2021 en dur) — un dossier à 1 seul exercice
        # n'a alors que N, N-1/N-2 restent des dicts vides (déjà géré par
        # TrendsEngine.analyze_trends, qui retombe sur 0.0 par indicateur).
        annees = cls._annees_disponibles(mongo_document)
        if not annees:
            logger.warning(f"Aucun exercice trouvé dans historique_financier pour '{client_id}'")
            return {
                "client_id": client_id,
                "statut_evaluation": "ECHEC",
                "erreur": "Aucune donnée financière (historique_financier) trouvée dans le dossier.",
            }
        annee_n, annee_n_1, annee_n_2 = (annees + [None, None])[:3]

        # 2. Extraction, aplatissement et enrichissement de chaque année disponible
        data_n = cls._enrich_year_data(cls.extract_flat_year_data(mongo_document, annee_n))
        data_n_1 = cls._enrich_year_data(cls.extract_flat_year_data(mongo_document, annee_n_1)) if annee_n_1 else {}
        data_n_2 = cls._enrich_year_data(cls.extract_flat_year_data(mongo_document, annee_n_2)) if annee_n_2 else {}

        # 3. Récupération de l'annuité pour le calcul du DSCR
        dette_info = mongo_document.get("comportement_bancaire", {}).get("dette_existante", {})
        mensualite_totale_annuelle = dette_info.get("mensualite_totale", {}).get("value", 0.0) * 12
        montant_nouveau_credit, duree_nouveau_credit_mois = cls._extract_new_credit_terms(mongo_document)
        taux_nouveau_credit = float(os.environ.get("DEFAULT_NEW_CREDIT_ANNUAL_RATE", "0.06"))

        # Injecte l'annuité dans les données N pour le RatiosHub
        data_n["annuite_emprunts"] = mensualite_totale_annuelle

        # 4. Calcul des Ratios sur l'année la plus récente (N)
        ratios_n = RatiosHub.calculate_all_ratios(data_n)

        # 5. Analyse des Tendances Historiques sur les exercices disponibles (N, N-1, N-2)
        tendances = TrendsEngine.analyze_trends(
            data_n=data_n,
            data_n_1=data_n_1,
            data_n_2=data_n_2
        )

        # 6. Calcul de la Capacité de Remboursement (DSCR)
        ebitda_n = data_n.get("ebitda", 0.0)
        dscr_analysis = DSCREngine.calculate_dscr(
            ebitda=ebitda_n,
            annuite_emprunts=mensualite_totale_annuelle,
            montant_nouveau_credit=montant_nouveau_credit,
            duree_nouveau_credit_mois=duree_nouveau_credit_mois,
            taux_annuel_nouveau_credit=taux_nouveau_credit,
        )
        dscr_analysis["montant_nouveau_credit"] = montant_nouveau_credit
        dscr_analysis["duree_nouveau_credit_mois"] = duree_nouveau_credit_mois
        dscr_analysis["taux_annuel_nouveau_credit"] = taux_nouveau_credit
        garanties = mongo_document.get("garanties", {}).get("garanties", [])
        garanties_analysis = assess_guarantees(garanties, montant_nouveau_credit)

        # 7. Score de défaillance Altman Z
        # (dettes_totales / total_dettes garanti non-nul par _enrich_year_data)
        altman_score = ScoringEngine.calculate_altman_z_score(
            working_capital=data_n.get("working_capital", 0.0),
            total_assets=data_n.get("total_actif", 0.0),
            retained_earnings=data_n.get("report_a_nouveau", 0.0),
            ebit=data_n.get("resultat_exploitation", 0.0),
            book_value_equity=data_n.get("capitaux_propres", 0.0),
            total_liabilities=data_n.get("total_dettes", 0.0),
            sales=data_n.get("chiffre_affaires", 0.0),
            is_listed=is_listed,
            is_manufacturier=is_manufacturier,
            market_value_equity=market_value_equity,
        )

        # 8. Assemblage final
        donnees_brutes_applaties = {str(annee_n): data_n}
        if annee_n_1:
            donnees_brutes_applaties[str(annee_n_1)] = data_n_1
        if annee_n_2:
            donnees_brutes_applaties[str(annee_n_2)] = data_n_2

        evaluation_report = {
            "client_id": client_id,
            "statut_evaluation": "SUCCÈS",
            "annee_reference": annee_n,
            "ratios_financiers_n": ratios_n,
            "analyse_tendances_3ans": tendances,
            "couverture_dette_dscr": dscr_analysis,
            "analyse_garanties": garanties_analysis,
            "altman_score": altman_score,
            "donnees_brutes_applaties": donnees_brutes_applaties,
        }

        logger.info(f"✅ Évaluation financière terminée pour '{client_id}' !")
        return evaluation_report