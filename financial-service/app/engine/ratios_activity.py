from typing import Dict, Optional

class ActivityEngine:
    """
    Pilier 4 : Ratios d'Activité et du Cycle d'Exploitation.
    Conforme CGNC / Bank Al-Maghrib / IFC.
    """

    @staticmethod
    def calculate_all(chiffre_affaires: float, total_actif: float,
                      creances_clients: float, dettes_fournisseurs: float,
                      achats_consommes: float) -> Dict[str, Optional[float]]:

        # 1. Asset Turnover (Rotation du Total Actif)
        asset_turnover = (chiffre_affaires / total_actif) if total_actif > 0 else None

        # 2. DSO (Days Sales Outstanding - Délai moyen de paiement clients)
        dso = (creances_clients / chiffre_affaires * 360) if chiffre_affaires > 0 else None

        # 3. DPO (Days Payables Outstanding - Délai moyen de règlement fournisseurs)
        dpo = (dettes_fournisseurs / achats_consommes * 360) if achats_consommes > 0 else None

        # 4. Cycle d'exploitation simplifié (DSO - DPO)
        cycle_exploitation = (dso - dpo) if (dso is not None and dpo is not None) else None

        return {
            "asset_turnover": round(asset_turnover, 2) if asset_turnover is not None else None,
            "dso_days": round(dso, 1) if dso is not None else None,
            "dpo_days": round(dpo, 1) if dpo is not None else None,
            "cycle_exploitation_days": round(cycle_exploitation, 1) if cycle_exploitation is not None else None
        }