from typing import Dict, Optional

class DSCREngine:
    """
    Pilier 6 : Debt Service Coverage Ratio (DSCR).
    Conforme aux normes IFC et pratiques bancaires (Bank Al-Maghrib).
    """

    @staticmethod
    def calculate_dscr(ebitda: float = 0.0,
                       annuite_emprunts: float = 0.0,
                       cfo: Optional[float] = None) -> Dict[str, Optional[float]]:
        """
        Calcule le ratio de couverture du service de la dette.
        - Si 'cfo' est transmis à la place d'ebitda, on l'utilise intelligemment.
        """
        # Utilise CFO si fourni et valide, sinon EBITDA
        flux_disponible = cfo if (cfo is not None and cfo > 0) else ebitda

        if annuite_emprunts <= 0:
            return {
                "dscr": None,
                "is_dscr_acceptable": None
            }

        dscr = flux_disponible / annuite_emprunts
        is_acceptable = dscr >= 1.25

        return {
            "dscr": round(dscr, 2),
            "is_dscr_acceptable": is_acceptable
        }