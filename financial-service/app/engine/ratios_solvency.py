from typing import Dict, Optional

class SolvencyEngine:
    """
    Pilier 2 : Ratios de Solvabilité (Capacité à rembourser les dettes à long terme).
    Conforme strictement au référentiel CGNC / Bank Al-Maghrib / Moody's.
    """

    @staticmethod
    def calculate_all(total_actif: float, capitaux_propres: float,
                      dettes_totales: float, passif_circulant: float,
                      tresorerie_actif: float, report_a_nouveau: float = 0.0) -> Dict[str, Optional[float]]:

        if total_actif <= 0:
            return {
                "liabilities_to_assets": None,
                "net_current_liabilities_to_assets": None,
                "debt_to_equity_leverage": None,
                "retained_earnings_to_current_liabilities": None,
                "autonomie_financiere": None
            }

        # 1. Liabilities / Assets (Debt Ratio - Endettement global)
        liabilities_to_assets = dettes_totales / total_actif

        # 2. (Current Liabilities - Cash) / Assets (Poids du passif court terme net)
        net_current_liabilities_to_assets = (passif_circulant - tresorerie_actif) / total_actif

        # 3. Debt to Equity / Leverage (Levier financier)
        debt_to_equity = (dettes_totales / capitaux_propres) if capitaux_propres > 0 else None

        # 4. Retained Earnings / Current Liabilities (Réserves / Passif circulant)
        retained_earnings_ratio = (report_a_nouveau / passif_circulant) if passif_circulant > 0 else None

        # 5. Autonomie Financière (Capitaux propres / Total Actif)
        autonomie_financiere = capitaux_propres / total_actif

        return {
            "liabilities_to_assets": round(liabilities_to_assets, 4),
            "net_current_liabilities_to_assets": round(net_current_liabilities_to_assets, 4),
            "debt_to_equity_leverage": round(debt_to_equity, 2) if debt_to_equity is not None else None,
            "retained_earnings_to_current_liabilities": round(retained_earnings_ratio, 4) if retained_earnings_ratio is not None else None,
            "autonomie_financiere": round(autonomie_financiere, 4)
        }