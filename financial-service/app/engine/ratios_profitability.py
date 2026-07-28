from typing import Dict, Optional

class ProfitabilityEngine:
    """
    Pilier 3 : Ratios de Rentabilité (Performance opérationnelle et création de valeur).
    Conforme CGNC / Bank Al-Maghrib / Moody's.
    """

    @staticmethod
    def calculate_all(chiffre_affaires: float, resultat_net: float,
                      resultat_exploitation: float, ebitda: float,
                      capitaux_propres: float, total_actif: float) -> Dict[str, Optional[float]]:

        marge_nette = (resultat_net / chiffre_affaires) if chiffre_affaires > 0 else None
        marge_operationnelle = (resultat_exploitation / chiffre_affaires) if chiffre_affaires > 0 else None
        marge_ebitda = (ebitda / chiffre_affaires) if chiffre_affaires > 0 else None
        roe = (resultat_net / capitaux_propres) if capitaux_propres > 0 else None
        roa = (resultat_net / total_actif) if total_actif > 0 else None

        return {
            "roa_return_on_assets": round(roa, 4) if roa is not None else None,
            "roe_return_on_equity": round(roe, 4) if roe is not None else None,
            "marge_nette": round(marge_nette, 4) if marge_nette is not None else None,
            "marge_operationnelle": round(marge_operationnelle, 4) if marge_operationnelle is not None else None,
            "ebitda_margin": round(marge_ebitda, 4) if marge_ebitda is not None else None
        }