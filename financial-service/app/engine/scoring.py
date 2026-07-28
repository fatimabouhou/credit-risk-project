from typing import Dict, Any

class ScoringEngine:
    """
    Pilier 7 : Modèles statistiques de défaillance (Altman Z-Score) et Grille de Notation.
    Conforme aux standards académiques (adapté PME).
    """

    @staticmethod
    def calculate_altman_z_score(working_capital: float, total_assets: float,
                                 retained_earnings: float, ebit: float,
                                 equity: float, total_liabilities: float,
                                 sales: float) -> Dict[str, Any]:
        """
        Calcul de l'Altman Z-Score pour PME / entreprises non cotées :
        Z = 0.717*X1 + 0.847*X2 + 3.107*X3 + 0.420*X4 + 0.998*X5
        """
        if total_assets <= 0 or total_liabilities <= 0:
            return {
                "z_score": None,
                "zone": "Inconnu",
                "risk_level": "Indéterminé",
                "suggested_rating": "N/A"
            }

        # X1: Liquidité (Fonds de roulement / Total actif)
        x1 = working_capital / total_assets
        # X2: Rentabilité cumulée (Réserves / Total actif)
        x2 = retained_earnings / total_assets
        # X3: Rentabilité économique (EBIT / Total actif)
        x3 = ebit / total_assets
        # X4: Structure financière (Capitaux propres / Total des dettes)
        # TODO (V2) : Pour les entreprises cotées en bourse, X4 utilisera la Capitalisation Boursière au lieu des Capitaux Propres comptables.
        x4 = equity / total_liabilities
        # X5: Taux de rotation de l'actif (Chiffre d'affaires / Total actif)
        x5 = sales / total_assets

        # =====================================================================
        # TODO (V2) - INTÉGRATION MULTI-PROFILS VIA INTERFACE UTILISATEUR
        # À l'avenir, ajouter les paramètres `is_listed` et `is_industrial` ici
        # pour conditionner le calcul selon 3 scénarios :
        #
        # 1. SI is_listed == True (Cotée en bourse) :
        #    z_score = 1.2*x1 + 1.4*x2 + 3.3*x3 + 0.6*x4 + 1.0*x5
        #    (Avec de nouveaux seuils de zones)
        #
        # 2. SI is_industrial == False (Services / Non-industriel) :
        #    z_score = 6.56*x1 + 3.26*x2 + 6.72*x3 + 1.05*x4
        #    (Attention : la variable X5 est volontairement exclue de ce calcul)
        # =====================================================================

        # Calcul actuel par défaut : Z'-Score (PME Industrielles)
        z_score = round(0.717 * x1 + 0.847 * x2 + 3.107 * x3 + 0.420 * x4 + 0.998 * x5, 2)

        # Interprétation des zones d'Altman Z-Score pour PME
        # TODO (V2) : Ces seuils (2.9 et 1.23) devront devenir dynamiques selon le modèle choisi ci-dessus.
        if z_score > 2.9:
            zone = "Verte"
            risk_level = "Très Faible (Entreprise Saine)"
            rating = "A"
        elif 1.23 <= z_score <= 2.9:
            zone = "Grise"
            risk_level = "Modéré (Vigilance requise)"
            rating = "C"
        else:
            zone = "Rouge"
            risk_level = "Élevé (Risque de défaillance)"
            rating = "E"

        return {
            "z_score": z_score,
            "zone": zone,
            "risk_level": risk_level,
            "suggested_rating": rating
        }