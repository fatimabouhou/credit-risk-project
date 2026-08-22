"""
assess_guarantees : couverture indicative après décote.

Le résultat n'a aucune valeur juridique — ces tests vérifient surtout qu'une
garantie non exploitable ne se transforme jamais silencieusement en zéro,
ce qui gonflerait artificiellement la couverture affichée au chargé de risque.
"""

import pytest

from app.engine.guarantees import HAIRCUTS, assess_guarantees


class TestDecotes:
    @pytest.mark.parametrize(
        "type_garantie,attendu",
        [("hypotheque", 0.70), ("nantissement", 0.50), ("caution", 0.00)],
    )
    def test_applique_la_decote_du_bareme(self, type_garantie, attendu):
        result = assess_guarantees(
            [{"type": type_garantie, "valeur_declaree": 1_000_000}],
            montant_nouveau_credit=1_000_000,
        )
        assert result["garanties"][0]["decote"] == attendu
        assert result["garanties"][0]["valeur_retenue_indicative"] == pytest.approx(1_000_000 * attendu)

    def test_un_type_inconnu_ne_retient_aucune_valeur(self):
        # Décote 0 par défaut : mieux vaut sous-estimer la couverture que
        # créditer une sûreté dont on ignore le régime.
        result = assess_guarantees(
            [{"type": "gage_sur_stock", "valeur_declaree": 1_000_000}],
            montant_nouveau_credit=1_000_000,
        )
        assert result["garanties"][0]["decote"] == 0.0
        assert result["garanties"][0]["valeur_retenue_indicative"] == 0.0
        assert result["couverture_pct"] == 0.0

    def test_le_bareme_couvre_les_trois_types_attendus(self):
        assert set(HAIRCUTS) == {"hypotheque", "nantissement", "caution"}


class TestValeurDeclareeInexploitable:
    @pytest.mark.parametrize("valeur", [None, "1 000 000", "", {}])
    def test_laisse_la_valeur_retenue_a_none(self, valeur):
        # None, pas 0 : une valeur illisible n'est pas une garantie sans valeur.
        result = assess_guarantees(
            [{"type": "hypotheque", "valeur_declaree": valeur}],
            montant_nouveau_credit=1_000_000,
        )
        assert result["garanties"][0]["valeur_retenue_indicative"] is None

    def test_n_alimente_pas_le_total_retenu(self):
        result = assess_guarantees(
            [
                {"type": "hypotheque", "valeur_declaree": None},
                {"type": "hypotheque", "valeur_declaree": 1_000_000},
            ],
            montant_nouveau_credit=1_000_000,
        )
        assert result["valeur_retenue_indicative"] == pytest.approx(700_000)


class TestCouverture:
    def test_somme_les_garanties_apres_decote(self):
        result = assess_guarantees(
            [
                {"type": "hypotheque", "valeur_declaree": 2_000_000},   # 1 400 000
                {"type": "nantissement", "valeur_declaree": 1_000_000},  # 500 000
                {"type": "caution", "valeur_declaree": 5_000_000},       # 0
            ],
            montant_nouveau_credit=2_500_000,
        )
        assert result["valeur_retenue_indicative"] == pytest.approx(1_900_000)
        assert result["couverture_pct"] == pytest.approx(76.0)
        assert result["evaluable"] is True
        assert result["statut"] == "a_verifier"

    def test_peut_depasser_cent_pour_cent(self):
        # Pas de plafonnement : une sur-couverture est une information utile.
        result = assess_guarantees(
            [{"type": "hypotheque", "valeur_declaree": 10_000_000}],
            montant_nouveau_credit=1_000_000,
        )
        assert result["couverture_pct"] == pytest.approx(700.0)

    def test_preserve_les_champs_d_origine_de_chaque_garantie(self):
        result = assess_guarantees(
            [{"type": "hypotheque", "valeur_declaree": 1_000_000, "reference": "TF 12/345"}],
            montant_nouveau_credit=1_000_000,
        )
        assert result["garanties"][0]["reference"] == "TF 12/345"


class TestMontantCreditManquant:
    @pytest.mark.parametrize("montant", [None, 0, -1])
    def test_marque_le_dossier_non_evaluable(self, montant):
        result = assess_guarantees(
            [{"type": "hypotheque", "valeur_declaree": 1_000_000}],
            montant_nouveau_credit=montant,
        )
        assert result["evaluable"] is False
        assert result["couverture_pct"] is None
        assert result["statut"] == "montant_credit_manquant"

    def test_expose_quand_meme_la_valeur_retenue(self):
        # Le calcul des sûretés reste utile même sans montant demandé.
        result = assess_guarantees(
            [{"type": "hypotheque", "valeur_declaree": 1_000_000}],
            montant_nouveau_credit=None,
        )
        assert result["valeur_retenue_indicative"] == pytest.approx(700_000)


class TestAucuneGarantie:
    @pytest.mark.parametrize("garanties", [None, []])
    def test_donne_une_couverture_nulle_mais_evaluable(self, garanties):
        result = assess_guarantees(garanties, montant_nouveau_credit=1_000_000)
        assert result["garanties"] == []
        assert result["valeur_retenue_indicative"] == 0.0
        assert result["evaluable"] is True
        assert result["couverture_pct"] == 0.0
