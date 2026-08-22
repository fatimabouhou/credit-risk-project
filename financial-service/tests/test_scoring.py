"""
ScoringEngine : Altman Z-Score.

Le point sensible n'est pas l'arithmétique mais le CHOIX de formule : la
famille se décide sur "manufacturière", et seulement ensuite sur "cotée avec
capitalisation disponible". Un mauvais choix de famille change les seuils de
zone, donc le verdict.
"""

import pytest

from app.engine.scoring import ScoringEngine


def _base(**overrides):
    params = {
        "working_capital": 300_000,
        "total_assets": 1_000_000,
        "retained_earnings": 200_000,
        "ebit": 150_000,
        "book_value_equity": 400_000,
        "total_liabilities": 600_000,
        "sales": 900_000,
    }
    params.update(overrides)
    return params


class TestDonneesInsuffisantes:
    @pytest.mark.parametrize("total_assets,total_liabilities", [(0, 600_000), (-1, 600_000), (1_000_000, 0), (1_000_000, -1)])
    def test_renvoie_un_resultat_vide_sans_denominateur_exploitable(self, total_assets, total_liabilities):
        # Aucun score inventé : les quatre champs restent None.
        result = ScoringEngine.calculate_altman_z_score(
            **_base(total_assets=total_assets, total_liabilities=total_liabilities)
        )
        assert result == {"model": None, "score": None, "zone": None, "formula_used": None}


class TestChoixDeFormule:
    def test_non_manufacturiere_utilise_z_double_prime(self):
        result = ScoringEngine.calculate_altman_z_score(**_base(is_manufacturier=False))
        assert result["model"] == "Z''"
        assert result["formula_used"] == "Altman Z'' (1995)"

    def test_manufacturier_non_renseigne_est_traite_comme_non_manufacturiere(self):
        # None n'est pas une hypothèse risquée : Z'' couvre déjà explicitement
        # commerce / services / BTP / transport, c'est le défaut le plus sûr.
        implicite = ScoringEngine.calculate_altman_z_score(**_base())
        explicite = ScoringEngine.calculate_altman_z_score(**_base(is_manufacturier=False))
        assert implicite == explicite

    def test_manufacturiere_privee_utilise_z_prime(self):
        result = ScoringEngine.calculate_altman_z_score(**_base(is_manufacturier=True))
        assert result["model"] == "Z'"
        assert result["formula_used"] == "Altman Z' (1983)"

    def test_manufacturiere_cotee_avec_capitalisation_utilise_z_1968(self):
        result = ScoringEngine.calculate_altman_z_score(
            **_base(is_manufacturier=True, is_listed=True, market_value_equity=2_000_000)
        )
        assert result["model"] == "Z"
        assert result["formula_used"] == "Altman Z (1968)"

    def test_manufacturiere_cotee_sans_capitalisation_retombe_sur_z_prime(self):
        # Pas sur Z'' : rester dans la bonne famille (manufacturière) et
        # substituer la valeur comptable est moins faux que changer de famille.
        result = ScoringEngine.calculate_altman_z_score(
            **_base(is_manufacturier=True, is_listed=True, market_value_equity=None)
        )
        assert result["model"] == "Z'"

    def test_cotee_non_manufacturiere_reste_sur_z_double_prime(self):
        result = ScoringEngine.calculate_altman_z_score(
            **_base(is_manufacturier=False, is_listed=True, market_value_equity=2_000_000)
        )
        assert result["model"] == "Z''"


class TestCalculZDoublePrime:
    def test_applique_les_coefficients_de_1995(self):
        # x1=.3 x2=.2 x3=.15 x4=400k/600k ; sales n'entre PAS dans Z''.
        result = ScoringEngine.calculate_altman_z_score(**_base())
        attendu = 6.56 * 0.3 + 3.26 * 0.2 + 6.72 * 0.15 + 1.05 * (400_000 / 600_000)
        assert result["score"] == pytest.approx(round(attendu, 2))

    def test_ignore_le_chiffre_d_affaires(self):
        # Z'' n'a pas de terme X5 : changer les ventes ne doit rien changer.
        sans = ScoringEngine.calculate_altman_z_score(**_base(sales=0))
        avec = ScoringEngine.calculate_altman_z_score(**_base(sales=50_000_000))
        assert sans["score"] == avec["score"]

    def test_le_chiffre_d_affaires_compte_pour_z_prime(self):
        sans = ScoringEngine.calculate_altman_z_score(**_base(is_manufacturier=True, sales=0))
        avec = ScoringEngine.calculate_altman_z_score(**_base(is_manufacturier=True, sales=900_000))
        assert avec["score"] > sans["score"]


class TestZones:
    """Bornes Z'' : distress < 1.10 <= grey < 2.60 <= safe."""

    def _score_z2(self, working_capital):
        return ScoringEngine.calculate_altman_z_score(
            working_capital=working_capital,
            total_assets=1_000_000,
            retained_earnings=0,
            ebit=0,
            book_value_equity=0,
            total_liabilities=1_000_000,
            sales=0,
        )

    def test_zone_distress_sous_la_borne_basse(self):
        assert self._score_z2(100_000)["zone"] == "distress"   # 0.66

    def test_zone_grey_entre_les_deux_bornes(self):
        assert self._score_z2(250_000)["zone"] == "grey"       # 1.64

    def test_zone_safe_au_dessus_de_la_borne_haute(self):
        assert self._score_z2(500_000)["zone"] == "safe"       # 3.28

    def test_la_borne_safe_est_inclusive(self):
        # 6.56 * x1 = 2.60 exactement pour x1 = 0.396341...
        result = self._score_z2(396_341)
        assert result["score"] == 2.60
        assert result["zone"] == "safe"

    def test_un_score_negatif_reste_en_distress(self):
        assert self._score_z2(-500_000)["zone"] == "distress"


class TestFormatDeSortie:
    def test_arrondit_le_score_a_deux_decimales(self):
        result = ScoringEngine.calculate_altman_z_score(**_base())
        assert result["score"] == round(result["score"], 2)

    def test_expose_les_quatre_champs_attendus(self):
        result = ScoringEngine.calculate_altman_z_score(**_base())
        assert set(result) == {"model", "score", "zone", "formula_used"}
