from typing import Dict, Optional

class LiquidityEngine:
    """
    Pilier 1 : Ratios de Liquidité (Capacité à honorer les engagements à court terme).
    Conforme CGNC / Bank Al-Maghrib.
    """

    @staticmethod
    def calculate_all(actif_circulant: float, passif_circulant: float,
                      tresorerie_actif: float, stocks: float = 0.0) -> Dict[str, Optional[float]]:

        if passif_circulant <= 0:
            return {
                "current_ratio": None,
                "quick_ratio": None,
                "cash_ratio": None,
                "working_capital_frf": None
            }

        # 1. Current Ratio (Liquidité générale)
        current_ratio = actif_circulant / passif_circulant

        # 2. Quick Ratio (Liquidité réduite)
        quick_ratio = (actif_circulant - stocks) / passif_circulant

        # 3. Cash Ratio (Liquidité immédiate)
        cash_ratio = tresorerie_actif / passif_circulant

        # 4. Working Capital / FRF (Fonds de Roulement Fonctionnel)
        frf = actif_circulant - passif_circulant

        return {
            "current_ratio": round(current_ratio, 2),
            "quick_ratio": round(quick_ratio, 2),
            "cash_ratio": round(cash_ratio, 2),
            "working_capital_frf": round(frf, 2)
        }