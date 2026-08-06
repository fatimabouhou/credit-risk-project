from typing import Any, Dict, Optional


class ScoringEngine:
    """
    Pilier 7 : Modèle statistique de défaillance Altman Z-Score.

    Ce module calcule UNIQUEMENT le score et la zone (Safe/Grey/Distress) —
    aucune interprétation métier (pas de "risque faible", pas de
    recommandation de crédit) : ce raisonnement est le rôle de
    l'agentic-service, en aval, pas de financial-service.

    Sélection automatique entre les 3 formules officielles selon le
    profil de l'entreprise :
        - Z (1968)  : cotée ET manufacturière (nécessite market_value_equity)
        - Z' (1983) : privée ET manufacturière
        - Z'' (1995) : tous les autres cas (commerce, services, BTP,
          transport, ou "manufacturière" inconnue) — c'est la formule la
          plus générale, utilisée par défaut si `is_manufacturier` n'est
          pas fourni (aucune donnée structurée de secteur/activité
          n'existe aujourd'hui dans le dossier client pour le déterminer
          de façon fiable — voir `is_manufacturier` ci-dessous).
    """

    @staticmethod
    def calculate_altman_z_score(
        working_capital: float,
        total_assets: float,
        retained_earnings: float,
        ebit: float,
        book_value_equity: float,
        total_liabilities: float,
        sales: float,
        is_listed: bool = False,
        is_manufacturier: Optional[bool] = None,
        market_value_equity: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        `is_listed` / `is_manufacturier` : renseignés par l'utilisateur via
        l'interface (aucune des deux données n'est extraite automatiquement
        du dossier aujourd'hui) — `is_manufacturier=None` (non renseigné)
        est traité comme non-manufacturière, pas comme une hypothèse
        risquée : c'est la formule Z'' qui couvre déjà explicitement
        commerce/services/BTP/transport, donc le cas par défaut le plus
        sûr en l'absence d'information.
        `market_value_equity` : capitalisation boursière, uniquement
        pertinente si `is_listed=True` — sans donnée boursière disponible,
        la formule Z (1968) ne peut jamais s'appliquer, quel que soit
        `is_listed` (retombe sur Z' ou Z'').
        """
        if total_assets <= 0 or total_liabilities <= 0:
            return {"model": None, "score": None, "zone": None, "formula_used": None}

        x1 = working_capital / total_assets
        x2 = retained_earnings / total_assets
        x3 = ebit / total_assets
        x5 = sales / total_assets

        # Le choix se fait d'abord sur "manufacturière" (détermine la famille de
        # formule), puis sur "cotée avec donnée boursière disponible" à
        # l'intérieur de cette famille — pas un simple if/elif/else à plat sur
        # les deux critères : une entreprise cotée ET manufacturière mais sans
        # market_value_equity disponible (cas réel aujourd'hui : cette donnée
        # n'existe nulle part dans le système) doit retomber sur Z' (toujours
        # manufacturière, juste avec la valeur comptable), pas sur Z'' qui est
        # pensée pour les entreprises NON manufacturières — un mauvais choix de
        # famille serait pire qu'une simple substitution de X4.
        if is_manufacturier and is_listed and market_value_equity is not None:
            x4 = market_value_equity / total_liabilities
            score = 1.2 * x1 + 1.4 * x2 + 3.3 * x3 + 0.6 * x4 + 1.0 * x5
            model, formula_used = "Z", "Altman Z (1968)"
            distress_max, safe_min = 1.81, 2.99
        elif is_manufacturier:
            x4 = book_value_equity / total_liabilities
            score = 0.717 * x1 + 0.847 * x2 + 3.107 * x3 + 0.420 * x4 + 0.998 * x5
            model, formula_used = "Z'", "Altman Z' (1983)"
            distress_max, safe_min = 1.23, 2.90
        else:
            x4 = book_value_equity / total_liabilities
            score = 6.56 * x1 + 3.26 * x2 + 6.72 * x3 + 1.05 * x4
            model, formula_used = "Z''", "Altman Z'' (1995)"
            distress_max, safe_min = 1.10, 2.60

        score = round(score, 2)
        if score < distress_max:
            zone = "distress"
        elif score < safe_min:
            zone = "grey"
        else:
            zone = "safe"

        return {
            "model": model,
            "score": score,
            "zone": zone,
            "formula_used": formula_used,
        }
