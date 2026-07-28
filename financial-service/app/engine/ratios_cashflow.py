from typing import Dict, Optional

class CashFlowEngine:
    """
    Pilier 5 : Ratios de Cash Flow et Flux de Trésorerie.
    Conforme CGNC / Bank Al-Maghrib / Moody's.
    """

    @staticmethod
    def calculate_all(cfo: float, free_cash_flow: float,
                      total_dettes: float, total_actif: float) -> Dict[str, Optional[float]]:

        # 1. CFO / Total Debt (Couverture de la dette par les flux opérationnels)
        cfo_to_debt = (cfo / total_dettes) if total_dettes > 0 else None

        # 2. CFO / Total Assets (Capacité de l'actif à générer du cash réel)
        cfo_to_assets = (cfo / total_actif) if total_actif > 0 else None

        # 3. Free Cash Flow / Total Debt (Ratio de désendettement net)
        fcf_to_debt = (free_cash_flow / total_dettes) if total_dettes > 0 else None

        return {
            "cfo_to_total_debt": round(cfo_to_debt, 4) if cfo_to_debt is not None else None,
            "cfo_to_total_assets": round(cfo_to_assets, 4) if cfo_to_assets is not None else None,
            "free_cash_flow_to_total_debt": round(fcf_to_debt, 4) if fcf_to_debt is not None else None
        }