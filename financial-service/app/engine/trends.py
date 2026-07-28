from typing import Dict, Any, Optional

class TrendsEngine:
    """
    Pilier 8 : Analyse des tendances (N, N-1, N-2).
    Calcule les variations historiques pour détecter la trajectoire financière de l'entreprise.
    """

    @staticmethod
    def calculate_variation(current_value: float, previous_value: float) -> Optional[float]:
        """
        Calcule le taux de variation en pourcentage entre deux périodes.
        """
        if previous_value == 0:
            return None

        variation = ((current_value - previous_value) / abs(previous_value)) * 100
        return round(variation, 2)

    @staticmethod
    def get_trend_label(variation: Optional[float]) -> str:
        """
        Traduit le pourcentage en un mot clair pour l'Agent IA.
        """
        if variation is None:
            return "Non calculable"

        if variation > 5.0:
            return "Hausse"
        elif variation < -5.0:
            return "Baisse"
        else:
            return "Stagnation"

    @classmethod
    def analyze_trends(cls, data_n: Dict[str, float], data_n_1: Dict[str, float], data_n_2: Dict[str, float]) -> Dict[str, Any]:
        """
        Croise les données sur 3 ans pour générer le rapport complet des tendances.
        Prend en entrée les 3 dictionnaires d'années générés par MongoDB.
        """
        trends_report = {}

        # Liste des indicateurs vitaux
        key_indicators = [
            'chiffre_affaires',
            'ebitda',
            'resultat_net',
            'total_dettes',
            'fonds_propres'
        ]

        for indicator in key_indicators:
            # Récupération sécurisée
            val_n = data_n.get(indicator, 0.0)
            val_n_1 = data_n_1.get(indicator, 0.0)
            val_n_2 = data_n_2.get(indicator, 0.0)

            # Calculs
            var_n_vs_n1 = cls.calculate_variation(val_n, val_n_1)
            var_n1_vs_n2 = cls.calculate_variation(val_n_1, val_n_2)

            trends_report[indicator] = {
                "valeurs": {
                    "N": round(val_n, 2),
                    "N-1": round(val_n_1, 2),
                    "N-2": round(val_n_2, 2)
                },
                "variations": {
                    "N_vs_N-1_pct": var_n_vs_n1,
                    "N-1_vs_N-2_pct": var_n1_vs_n2
                },
                "tendance_recente": cls.get_trend_label(var_n_vs_n1)
            }

        return trends_report