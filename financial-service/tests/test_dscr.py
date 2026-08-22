"""
DSCREngine : couverture du service de la dette.

Le DSCR arbitre l'octroi (seuil 1.25) et son annuité alimente le score de
décision côté agentic-service — une erreur ici se propage jusqu'au verdict
de crédit, d'où des cas explicites sur chaque branche.
"""

import pytest

from app.engine.dscr import DSCREngine


class TestFluxRetenu:
    """Le CFO prime sur l'EBITDA, mais seulement s'il est réellement exploitable."""

    def test_utilise_le_cfo_quand_il_est_positif(self):
        result = DSCREngine.calculate_dscr(ebitda=1_000_000, annuite_emprunts=500_000, cfo=800_000)
        assert result["dscr_existant"] == pytest.approx(1.6)

    def test_retombe_sur_ebitda_quand_le_cfo_est_absent(self):
        result = DSCREngine.calculate_dscr(ebitda=1_000_000, annuite_emprunts=500_000, cfo=None)
        assert result["dscr_existant"] == pytest.approx(2.0)

    def test_retombe_sur_ebitda_quand_le_cfo_est_negatif(self):
        # Un CFO négatif n'est pas un flux disponible : le retenir donnerait
        # un DSCR négatif, plus trompeur que le proxy EBITDA.
        result = DSCREngine.calculate_dscr(ebitda=1_000_000, annuite_emprunts=500_000, cfo=-200_000)
        assert result["dscr_existant"] == pytest.approx(2.0)

    def test_retombe_sur_ebitda_quand_le_cfo_est_nul(self):
        result = DSCREngine.calculate_dscr(ebitda=1_000_000, annuite_emprunts=500_000, cfo=0)
        assert result["dscr_existant"] == pytest.approx(2.0)


class TestDscrExistant:
    def test_reste_none_sans_annuite_existante(self):
        # Aucune dette en cours : le ratio n'a pas de dénominateur, il ne vaut
        # pas zéro. Renvoyer 0 laisserait croire à une couverture nulle.
        result = DSCREngine.calculate_dscr(ebitda=1_000_000, annuite_emprunts=0)
        assert result["dscr_existant"] is None

    def test_est_arrondi_a_deux_decimales(self):
        result = DSCREngine.calculate_dscr(ebitda=1_000_000, annuite_emprunts=300_000)
        assert result["dscr_existant"] == 3.33


class TestNouveauCreditNonEvaluable:
    """Sans montant ni durée exploitables, rien n'est estimé : tout reste None."""

    @pytest.mark.parametrize(
        "montant,duree",
        [
            (None, 60),
            (2_500_000, None),
            (0, 60),
            (2_500_000, 0),
            (-1, 60),
            (2_500_000, -12),
        ],
    )
    def test_marque_le_nouveau_credit_non_evaluable(self, montant, duree):
        result = DSCREngine.calculate_dscr(
            ebitda=1_000_000,
            annuite_emprunts=400_000,
            montant_nouveau_credit=montant,
            duree_nouveau_credit_mois=duree,
        )
        assert result["nouveau_credit_evaluable"] is False
        assert result["dscr_apres_nouveau_credit"] is None
        assert result["annuite_nouveau_credit"] is None
        assert result["is_dscr_apres_nouveau_credit_acceptable"] is None

    def test_conserve_le_dscr_existant_malgre_le_nouveau_credit_non_evaluable(self):
        result = DSCREngine.calculate_dscr(ebitda=1_000_000, annuite_emprunts=400_000)
        assert result["dscr"] == result["dscr_existant"] == 2.5


class TestNouveauCreditEvaluable:
    def test_calcule_l_annuite_par_amortissement_constant_a_taux_nul(self):
        # Taux 0 : l'annuité est la simple division du capital par la durée.
        result = DSCREngine.calculate_dscr(
            ebitda=1_000_000,
            annuite_emprunts=0,
            montant_nouveau_credit=1_200_000,
            duree_nouveau_credit_mois=60,
            taux_annuel_nouveau_credit=0,
        )
        assert result["annuite_nouveau_credit"] == pytest.approx(240_000, abs=0.01)

    def test_applique_la_formule_de_mensualite_a_taux_positif(self):
        # 2 500 000 sur 60 mois à 6 % : mensualité ~48 332 MAD, soit ~580 K/an.
        result = DSCREngine.calculate_dscr(
            ebitda=5_000_000,
            annuite_emprunts=0,
            montant_nouveau_credit=2_500_000,
            duree_nouveau_credit_mois=60,
            taux_annuel_nouveau_credit=0.06,
        )
        assert result["annuite_nouveau_credit"] == pytest.approx(579_984, rel=1e-3)

    def test_le_taux_alourdit_l_annuite(self):
        sans_interet = DSCREngine.calculate_dscr(
            ebitda=5_000_000, annuite_emprunts=0,
            montant_nouveau_credit=2_500_000, duree_nouveau_credit_mois=60,
            taux_annuel_nouveau_credit=0,
        )
        avec_interet = DSCREngine.calculate_dscr(
            ebitda=5_000_000, annuite_emprunts=0,
            montant_nouveau_credit=2_500_000, duree_nouveau_credit_mois=60,
            taux_annuel_nouveau_credit=0.06,
        )
        assert avec_interet["annuite_nouveau_credit"] > sans_interet["annuite_nouveau_credit"]

    def test_cumule_l_annuite_existante_et_la_nouvelle(self):
        result = DSCREngine.calculate_dscr(
            ebitda=1_000_000,
            annuite_emprunts=200_000,
            montant_nouveau_credit=1_200_000,
            duree_nouveau_credit_mois=60,
            taux_annuel_nouveau_credit=0,
        )
        # 1 000 000 / (200 000 + 240 000) = 2.27
        assert result["dscr_apres_nouveau_credit"] == pytest.approx(2.27, abs=0.01)

    def test_le_dscr_apres_credit_est_toujours_inferieur_a_l_existant(self):
        result = DSCREngine.calculate_dscr(
            ebitda=1_000_000,
            annuite_emprunts=200_000,
            montant_nouveau_credit=1_200_000,
            duree_nouveau_credit_mois=60,
            taux_annuel_nouveau_credit=0.06,
        )
        assert result["dscr_apres_nouveau_credit"] < result["dscr_existant"]

    def test_le_champ_dscr_expose_la_valeur_apres_nouveau_credit(self):
        # C'est la valeur qui doit primer une fois un crédit demandé : le
        # dossier se juge sur la situation post-financement.
        result = DSCREngine.calculate_dscr(
            ebitda=1_000_000, annuite_emprunts=200_000,
            montant_nouveau_credit=1_200_000, duree_nouveau_credit_mois=60,
            taux_annuel_nouveau_credit=0,
        )
        assert result["dscr"] == result["dscr_apres_nouveau_credit"]
        assert result["nouveau_credit_evaluable"] is True


class TestSeuilAcceptabilite:
    """Seuil bancaire de 1.25, borne incluse."""

    def test_accepte_exactement_au_seuil(self):
        # 1 250 000 / 1 000 000 = 1.25 pile.
        result = DSCREngine.calculate_dscr(
            ebitda=1_250_000,
            annuite_emprunts=0,
            montant_nouveau_credit=5_000_000,
            duree_nouveau_credit_mois=60,
            taux_annuel_nouveau_credit=0,
        )
        assert result["dscr_apres_nouveau_credit"] == pytest.approx(1.25)
        assert result["is_dscr_apres_nouveau_credit_acceptable"] is True

    def test_refuse_juste_sous_le_seuil(self):
        result = DSCREngine.calculate_dscr(
            ebitda=1_200_000,
            annuite_emprunts=0,
            montant_nouveau_credit=5_000_000,
            duree_nouveau_credit_mois=60,
            taux_annuel_nouveau_credit=0,
        )
        assert result["is_dscr_apres_nouveau_credit_acceptable"] is False

    def test_les_deux_drapeaux_d_acceptabilite_concordent(self):
        result = DSCREngine.calculate_dscr(
            ebitda=3_000_000, annuite_emprunts=100_000,
            montant_nouveau_credit=1_200_000, duree_nouveau_credit_mois=60,
            taux_annuel_nouveau_credit=0,
        )
        assert result["is_dscr_acceptable"] == result["is_dscr_apres_nouveau_credit_acceptable"]
