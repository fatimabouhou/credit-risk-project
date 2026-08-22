from typing import Dict, Optional

class DSCREngine:
    """
    Pilier 6 : Debt Service Coverage Ratio (DSCR).
    Conforme aux normes IFC et pratiques bancaires (Bank Al-Maghrib).
    """

    @staticmethod
    def calculate_dscr(ebitda: float = 0.0,
                       annuite_emprunts: float = 0.0,
                       cfo: Optional[float] = None,
                       montant_nouveau_credit: Optional[float] = None,
                       duree_nouveau_credit_mois: Optional[int] = None,
                       taux_annuel_nouveau_credit: float = 0.06) -> Dict[str, Optional[float]]:
        """
        Calcule le ratio de couverture du service de la dette.
        - Si 'cfo' est transmis à la place d'ebitda, on l'utilise intelligemment.
        """
        # Utilise le CFO lorsqu'il est disponible, sinon l'EBITDA comme proxy
        # explicite. Le DSCR post-financement ajoute le service du nouveau prêt.
        flux_disponible = cfo if (cfo is not None and cfo > 0) else ebitda

        dscr_existant = None
        if annuite_emprunts > 0:
            dscr_existant = round(flux_disponible / annuite_emprunts, 2)

        nouveau_credit_valide = (
            montant_nouveau_credit is not None
            and montant_nouveau_credit > 0
            and duree_nouveau_credit_mois is not None
            and duree_nouveau_credit_mois > 0
            and taux_annuel_nouveau_credit >= 0
        )

        if not nouveau_credit_valide:
            return {
                "dscr": dscr_existant,
                "dscr_existant": dscr_existant,
                "dscr_apres_nouveau_credit": None,
                "annuite_nouveau_credit": None,
                "is_dscr_acceptable": None,
                "is_dscr_apres_nouveau_credit_acceptable": None,
                "nouveau_credit_evaluable": False,
            }

        taux_mensuel = taux_annuel_nouveau_credit / 12
        if taux_mensuel == 0:
            mensualite_nouveau_credit = montant_nouveau_credit / duree_nouveau_credit_mois
        else:
            mensualite_nouveau_credit = montant_nouveau_credit * (
                taux_mensuel * (1 + taux_mensuel) ** duree_nouveau_credit_mois
                / ((1 + taux_mensuel) ** duree_nouveau_credit_mois - 1)
            )

        annuite_totale = annuite_emprunts + mensualite_nouveau_credit * 12
        dscr_apres_nouveau_credit = flux_disponible / annuite_totale
        is_acceptable = dscr_apres_nouveau_credit >= 1.25

        return {
            "dscr": round(dscr_apres_nouveau_credit, 2),
            "dscr_existant": dscr_existant,
            "dscr_apres_nouveau_credit": round(dscr_apres_nouveau_credit, 2),
            "annuite_nouveau_credit": round(mensualite_nouveau_credit * 12, 2),
            "is_dscr_acceptable": is_acceptable,
            "is_dscr_apres_nouveau_credit_acceptable": is_acceptable,
            "nouveau_credit_evaluable": True,
        }
