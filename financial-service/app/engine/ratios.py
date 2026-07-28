from typing import Dict, Any

from .ratios_liquidity import LiquidityEngine
from .ratios_profitability import ProfitabilityEngine
from .ratios_activity import ActivityEngine
from .ratios_cashflow import CashFlowEngine
from .ratios_solvency import SolvencyEngine
from .dscr import DSCREngine


class RatiosHub:
    """
    Le Hub Central qui orchestre le calcul de tous les ratios financiers.
    Il pré-prépare les données manquantes (fallbacks) puis appelle les sous-modules.
    """

    @classmethod
    def calculate_all_ratios(cls, data: Dict[str, float]) -> Dict[str, Any]:
        """
        Prend un dictionnaire plat de données financières et retourne
        un rapport structuré classé par catégories.
        """

        # -------------------------------------------------------------
        # 0. HARMONISATION ET PRÉ-CALCUL DES AGRÉGATS FINANCIERS
        # -------------------------------------------------------------
        stocks = data.get("stocks", 0.0)
        creances = data.get("creances_clients", 0.0)
        treso_actif = data.get("tresorerie_actif", 0.0)
        dettes_ct = data.get("dettes_court_terme", 0.0)
        dettes_lt = data.get("dettes_financement", 0.0)

        # 🔹 Actif circulant = Stocks + Créances + Trésorerie Actif (si non fourni explicitement)
        actif_circulant = data.get("actif_circulant") or (stocks + creances + treso_actif)

        # 🔹 Passif circulant = Dettes à court terme (si non fourni explicitement)
        passif_circulant = data.get("passif_circulant") or dettes_ct

        # 🔹 Dettes totales = Dettes LT + Dettes CT
        dettes_totales = data.get("total_dettes") or data.get("dettes_totales") or (dettes_lt + dettes_ct)

        # 🔹 EBITDA = EBITDA explicite OR Résultat d'exploitation OR EBIT
        ebitda = data.get("ebitda") or data.get("resultat_exploitation") or data.get("ebit", 0.0)

        # 🔹 CFO (Flux de Trésorerie Opérationnel) = CFO explicite OR EBITDA
        cfo = data.get("cfo") or ebitda

        # -------------------------------------------------------------
        # 1. CALCULS DES RATIOS VIA LES MOTEURS SPÉCIFIQUES
        # -------------------------------------------------------------

        # 1. Liquidité
        liquidite = LiquidityEngine.calculate_all(
            actif_circulant=actif_circulant,
            passif_circulant=passif_circulant,
            tresorerie_actif=treso_actif,
            stocks=stocks
        )

        # 2. Rentabilité
        rentabilite = ProfitabilityEngine.calculate_all(
            chiffre_affaires=data.get("chiffre_affaires", 0.0),
            resultat_net=data.get("resultat_net", 0.0),
            resultat_exploitation=data.get("resultat_exploitation", 0.0),
            ebitda=ebitda,
            capitaux_propres=data.get("capitaux_propres", 0.0),
            total_actif=data.get("total_actif", 0.0)
        )

        # 3. Activité (Cycle d'exploitation)
        activite = ActivityEngine.calculate_all(
            chiffre_affaires=data.get("chiffre_affaires", 0.0),
            total_actif=data.get("total_actif", 0.0),
            creances_clients=creances,
            dettes_fournisseurs=data.get("dettes_fournisseurs", 0.0),
            achats_consommes=data.get("achats_consommes", 0.0)
        )

        # 4. Cash Flow
        cash_flow = CashFlowEngine.calculate_all(
            cfo=cfo,
            free_cash_flow=data.get("free_cash_flow", 0.0),
            total_dettes=dettes_totales,
            total_actif=data.get("total_actif", 0.0)
        )

        # 5. Solvabilité (Endettement)
        solvabilite = SolvencyEngine.calculate_all(
            total_actif=data.get("total_actif", 0.0),
            capitaux_propres=data.get("capitaux_propres", 0.0),
            dettes_totales=dettes_totales,
            passif_circulant=passif_circulant,
            tresorerie_actif=treso_actif,
            report_a_nouveau=data.get("report_a_nouveau", 0.0)
        )

        # 6. DSCR (Service de la dette)
        dscr_result = DSCREngine.calculate_dscr(
            ebitda=ebitda,
            annuite_emprunts=data.get("annuite_emprunts", 0.0)
        )

        # -------------------------------------------------------------
        # 2. ASSEMBLAGE FINAL
        # -------------------------------------------------------------
        return {
            "liquidite": liquidite,
            "rentabilite": rentabilite,
            "activite": activite,
            "cash_flow": cash_flow,
            "solvabilite": solvabilite,
            "dscr": dscr_result
        }