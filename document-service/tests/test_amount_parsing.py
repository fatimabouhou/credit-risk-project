"""
Parsing des montants — l'entrée de toute la chaîne.

Une erreur ici est la plus dangereuse du système : elle est silencieuse
(aucune exception), plausible (le résultat reste un nombre crédible) et se
propage jusqu'au DSCR, au score Altman et à la décision de crédit. Un
« 1 250 000 » lu « 125 000 » ne se voit nulle part en aval.

Trois extracteurs implémentent leur propre parsing, avec des conventions
DIFFÉRENTES. Ces tests documentent le comportement réel de chacun, y compris
là où il diverge — voir TestDivergenceEntreExtracteurs en fin de fichier.
"""

import pytest

from app.services.extractors.banking_extractor import BankingExtractor
from app.services.extractors.financial_extractor import FinancialExtractor
from app.services.extractors.guarantee_extractor import GuaranteeExtractor


@pytest.fixture
def bancaire():
    return BankingExtractor()


@pytest.fixture
def financier():
    return FinancialExtractor()


class TestBankingCleanAmount:
    """
    Format anglo-saxon des relevés : virgule = millier, point = décimale.
    L'ambiguïté d'une virgule SEULE est tranchée par la longueur du dernier
    groupe — c'est la règle la plus risquée du fichier.
    """

    def test_lit_un_montant_anglo_saxon_complet(self, bancaire):
        assert bancaire.clean_amount("47,645,000.00") == 47_645_000.0

    def test_lit_un_montant_francais_a_virgule_decimale(self, bancaire):
        assert bancaire.clean_amount("5 000 000,00") == 5_000_000.0

    @pytest.mark.parametrize(
        "texte,attendu",
        [
            ("1,250", 1_250.0),        # dernier groupe de 3 -> séparateur de milliers
            ("1,250,000", 1_250_000.0),
            ("1,25", 1.25),            # dernier groupe de 2 -> séparateur décimal
            ("1,5", 1.5),
        ],
    )
    def test_tranche_l_ambiguite_de_la_virgule_seule(self, bancaire, texte, attendu):
        assert bancaire.clean_amount(texte) == attendu

    def test_ecarte_le_symbole_monetaire_et_les_espaces(self, bancaire):
        assert bancaire.clean_amount("  2 500 000.00 MAD  ") == 2_500_000.0

    def test_conserve_le_signe_negatif(self, bancaire):
        # Un découvert perdu en valeur absolue rendrait un compte sain.
        assert bancaire.clean_amount("-150,000.00") == -150_000.0

    @pytest.mark.parametrize("texte", ["", None])
    def test_renvoie_zero_sur_une_entree_vide(self, bancaire, texte):
        assert bancaire.clean_amount(texte) == 0.0

    def test_renvoie_zero_sur_un_texte_illisible(self, bancaire):
        # Repli silencieux à 0.0 : c'est le comportement actuel, et c'est
        # précisément pourquoi un test le fige — un changement vers None
        # casserait les appelants qui somment ces valeurs.
        assert bancaire.clean_amount("néant") == 0.0

    def test_un_montant_sans_separateur_est_lu_tel_quel(self, bancaire):
        assert bancaire.clean_amount("1250000") == 1_250_000.0


class TestFinancialCleanAmount:
    """
    Convention des bilans : espace = millier, virgule = décimale.
    Volontairement plus stricte que celle du relevé bancaire.
    """

    def test_lit_un_montant_a_espaces_et_virgule(self, financier):
        assert financier.clean_amount("55 600 000,00") == 55_600_000.0

    def test_lit_l_espace_insecable_des_pdf(self, financier):
        # pdfplumber renvoie souvent \xa0 : le rater ferait tomber le montant à 0.
        assert financier.clean_amount("55\xa0600\xa0000,00") == 55_600_000.0

    def test_renvoie_zero_sur_un_format_anglo_saxon(self, financier):
        # "47,645,000.00" -> "47.645.000.00" -> float() échoue -> 0.0.
        # Ce n'est PAS un bug de ce parseur (les bilans marocains n'utilisent
        # pas ce format), mais la limite est réelle : documentée ici pour
        # qu'un changement de gabarit de bilan soit détecté par ce test.
        assert financier.clean_amount("47,645,000.00") == 0.0

    @pytest.mark.parametrize("texte", ["", None, "N/A"])
    def test_renvoie_zero_sur_une_entree_inexploitable(self, financier, texte):
        assert financier.clean_amount(texte) == 0.0


class TestGetValidAmounts:
    def test_extrait_les_montants_d_une_ligne(self, financier):
        montants = financier.get_valid_amounts("Total actif 55 600 000,00 48 200 000,00")
        assert montants == [55_600_000.0, 48_200_000.0]

    def test_ecarte_les_renvois_de_notes_de_bas_de_page(self, financier):
        montants = financier.get_valid_amounts("Immobilisations 3 1 200 000,00")
        assert 3.0 not in montants
        assert 1_200_000.0 in montants

    @pytest.mark.parametrize("renvoi", [1, 2, 3, 4, 5, 6, 7, 8, 9])
    def test_ecarte_chaque_chiffre_isole_de_1_a_9(self, financier, renvoi):
        assert financier.get_valid_amounts(f"Poste {renvoi}") == []

    @pytest.mark.parametrize("ligne", ["Frais divers 5", "Frais divers 5,00"])
    def test_limite_connue_un_montant_reel_inferieur_a_dix_est_perdu(self, financier, ligne):
        # Effet de bord assumé du filtre anti-renvois : le filtre compare la
        # VALEUR, pas la forme, donc « 5,00 » écrit comme un vrai montant est
        # écarté au même titre qu'un renvoi « 5 ». Sans enjeu sur des bilans
        # en millions, mais la limite est réelle et doit rester explicite.
        assert financier.get_valid_amounts(ligne) == []

    def test_un_montant_a_deux_chiffres_passe_le_filtre(self, financier):
        # La borne est bien à 9 : 12,00 n'est pas confondu avec un renvoi.
        assert financier.get_valid_amounts("Frais 12,00") == [12.0]

    def test_renvoie_une_liste_vide_sur_une_ligne_sans_chiffre(self, financier):
        assert financier.get_valid_amounts("TOTAL GENERAL") == []


class TestPickTotalExercice:
    """
    Choix de la COLONNE du bilan. Se tromper de colonne donne un montant
    parfaitement plausible mais faux : c'est le pire scénario possible ici.
    """

    def test_quatre_colonnes_prend_l_avant_derniere(self):
        # Bilan : Brut / Amortissements / Net N / Net N-1 -> on veut Net N.
        assert FinancialExtractor.pick_total_exercice([1000.0, 200.0, 800.0, 750.0]) == 800.0

    def test_trois_colonnes_prend_l_avant_derniere(self):
        # CPC avec la colonne « exercices antérieurs » absente car nulle.
        assert FinancialExtractor.pick_total_exercice([500.0, 800.0, 750.0]) == 800.0

    def test_deux_colonnes_prend_la_premiere(self):
        # N et N-1 : l'exercice courant est en tête.
        assert FinancialExtractor.pick_total_exercice([800.0, 750.0]) == 800.0

    def test_une_colonne_prend_la_seule_valeur(self):
        assert FinancialExtractor.pick_total_exercice([800.0]) == 800.0

    def test_aucune_colonne_donne_zero(self):
        assert FinancialExtractor.pick_total_exercice([]) == 0.0

    def test_ne_prend_jamais_la_colonne_n_moins_1(self):
        # Régression la plus coûteuse : afficher l'exercice précédent à la
        # place du courant. La dernière colonne est toujours N-1.
        for colonnes in ([1000.0, 200.0, 800.0, 750.0], [500.0, 800.0, 750.0]):
            assert FinancialExtractor.pick_total_exercice(colonnes) != colonnes[-1]


class TestNormalizeSource:
    @pytest.mark.parametrize(
        "titre,alias",
        [
            ("Tableau : BILAN (ACTIF)", "Bilan Actif"),
            ("BILAN (PASSIF) au 31/12/2023", "Bilan Passif"),
            ("COMPTE DE PRODUITS ET CHARGES", "CPC"),
            ("ETAT DES SOLDES DE GESTION", "ESG"),
            ("TABLEAU DE FINANCEMENT", "Tableau de financement"),
        ],
    )
    def test_ramene_un_en_tete_brut_a_un_libelle_stable(self, financier, titre, alias):
        assert financier._normalize_source(titre) == alias

    def test_conserve_un_titre_inconnu_en_repli(self, financier):
        assert financier._normalize_source("tableau exotique") == "Tableau Exotique"

    def test_tronque_un_titre_tres_long(self, financier):
        assert len(financier._normalize_source("x" * 200)) == 60


class TestGuaranteeParseAmount:
    """Convention européenne : point = millier, virgule = décimale."""

    @pytest.mark.parametrize(
        "texte,attendu",
        [
            ("2 000 000,00", 2_000_000.0),
            ("2.000.000,00", 2_000_000.0),
            ("2 000 000,00", 2_000_000.0),  # espace fine insécable
            ("1500", 1500.0),
        ],
    )
    def test_lit_les_formats_attendus(self, texte, attendu):
        assert GuaranteeExtractor._parse_amount(texte) == attendu

    @pytest.mark.parametrize("texte", ["", "néant", "-"])
    def test_renvoie_none_sur_un_texte_illisible(self, texte):
        # None et non 0.0 : une garantie illisible ne doit pas se transformer
        # en garantie de valeur nulle (voir assess_guarantees côté financial).
        assert GuaranteeExtractor._parse_amount(texte) is None

    @pytest.mark.parametrize("texte", ["0", "0,00", "-5000"])
    def test_refuse_les_montants_nuls_ou_negatifs(self, texte):
        assert GuaranteeExtractor._parse_amount(texte) is None


class TestGuaranteeNormalize:
    @pytest.mark.parametrize(
        "texte,attendu",
        [
            ("Hypothèque", "hypotheque"),
            ("NANTISSEMENT", "nantissement"),
            ("Caution Solidaire", "caution solidaire"),
            ("Créance", "creance"),
        ],
    )
    def test_retire_les_accents_et_passe_en_minuscules(self, texte, attendu):
        assert GuaranteeExtractor._normalize(texte) == attendu


class TestDivergenceEntreExtracteurs:
    """
    Constat, pas une prescription : les trois parseurs ne lisent PAS le même
    format de la même façon. C'est cohérent avec les documents que chacun
    traite, mais si un jour un montant transite d'un extracteur à l'autre,
    ces tests montrent où ça casse.
    """

    def test_le_format_anglo_saxon_ne_passe_que_par_l_extracteur_bancaire(self, bancaire, financier):
        assert bancaire.clean_amount("47,645,000.00") == 47_645_000.0
        assert financier.clean_amount("47,645,000.00") == 0.0

    def test_le_point_de_millier_ne_passe_que_par_l_extracteur_garanties(self, bancaire):
        assert GuaranteeExtractor._parse_amount("2.000.000,00") == 2_000_000.0
        # Le parseur bancaire y voit un montant anglo-saxon décimal.
        assert bancaire.clean_amount("2.000.000,00") != 2_000_000.0

    def test_les_trois_s_accordent_sur_le_format_a_espaces(self, bancaire, financier):
        texte = "5 000 000,00"
        assert bancaire.clean_amount(texte) == 5_000_000.0
        assert financier.clean_amount(texte) == 5_000_000.0
        assert GuaranteeExtractor._parse_amount(texte) == 5_000_000.0
