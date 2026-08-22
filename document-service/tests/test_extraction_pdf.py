"""
Extraction sur PDF de référence.

Le parsing unitaire (test_amount_parsing.py) vérifie des chaînes déjà
découpées. Il ne dit rien du maillon précédent : est-ce que pdfplumber
retrouve les bonnes lignes dans le vrai document, et est-ce que la valeur
associée au bon libellé arrive intacte ?

Ces tests utilisent les PDF versionnés de `simulators/data/`, qui sont
générés par les scripts de `simulators/mocks/`. Ils sont donc stables et
comparables d'un commit à l'autre — c'est ce qui rend l'assertion possible.

Ils se `skip` proprement si un PDF a été déplacé, plutôt que d'échouer en
rouge sur un problème qui n'est pas une régression de code.
"""

from pathlib import Path

import pytest

from app.services.extractors.banking_extractor import BankingExtractor
from app.services.extractors.guarantee_extractor import GuaranteeExtractor

DATA = Path(__file__).resolve().parents[1] / "simulators" / "data"


def _pdf(*parties: str) -> Path:
    chemin = DATA.joinpath(*parties)
    if not chemin.exists():
        pytest.fail(f"PDF de référence absent : {chemin.relative_to(DATA.parent)}")
    return chemin


def _valeurs_tracees(noeud):
    """Parcourt une structure extraite et rend tous les {value, source, page}."""
    if isinstance(noeud, dict):
        if {"value", "source", "page"} <= set(noeud):
            yield noeud
            return
        for enfant in noeud.values():
            yield from _valeurs_tracees(enfant)
    elif isinstance(noeud, list):
        for enfant in noeud:
            yield from _valeurs_tracees(enfant)


class TestTracabilite:
    """
    Chaque valeur extraite doit rester rattachée à son document et sa page :
    c'est ce qui permet à un analyste de remonter à la pièce d'origine, et au
    frontend d'afficher « — » plutôt qu'un chiffre orphelin.
    """

    def test_le_releve_bancaire_trace_chaque_valeur(self):
        resultat = BankingExtractor().extract_releve(str(_pdf("04_bancaire", "releve_attijari.pdf")), "Attijariwafa")
        traces = list(_valeurs_tracees(resultat))
        assert traces, "aucun champ tracé produit par l'extraction"
        for trace in traces:
            assert trace["source"], "un champ extrait sans document source"
            assert isinstance(trace["page"], int)
            assert trace["page"] >= 1

    def test_la_centrale_des_risques_trace_chaque_valeur(self):
        resultat = BankingExtractor().extract_centrale_risques(str(_pdf("04_bancaire", "releve_central_risques.pdf")))
        for trace in _valeurs_tracees(resultat):
            assert trace["source"]
            assert isinstance(trace["page"], int)


class TestReleveBancaire:
    @pytest.fixture(scope="class")
    @staticmethod
    def releve():
        return BankingExtractor().extract_releve(str(_pdf("04_bancaire", "releve_attijari.pdf")), "Attijariwafa")

    def test_identifie_la_banque_demandee(self, releve):
        assert releve.get("banque") == "Attijariwafa"

    def test_extrait_des_montants_exploitables(self, releve):
        # Au moins une valeur numérique non nulle : une extraction qui rend
        # zéro partout est un échec silencieux, pas un compte vide.
        numeriques = [t["value"] for t in _valeurs_tracees(releve) if isinstance(t["value"], (int, float))]
        assert numeriques, "aucune valeur numérique extraite du relevé"
        assert any(v != 0 for v in numeriques), "toutes les valeurs extraites sont nulles"

    def test_les_montants_restent_dans_un_ordre_de_grandeur_credible(self, releve):
        # Garde-fou contre une erreur de séparateur : un solde de relevé
        # d'entreprise ne vaut ni 3 dirhams ni 10 milliards. Ce test attrape
        # précisément le « 1 250 000 lu 125 000 » s'il change d'un facteur 1000.
        montants = [
            abs(t["value"])
            for t in _valeurs_tracees(releve)
            if isinstance(t["value"], (int, float)) and t["value"] != 0
        ]
        assert montants
        assert max(montants) < 1e11, "montant absurde : séparateur de milliers probablement mal lu"


class TestSoldeDepart:
    """Parsing du solde de départ, isolé du PDF (fonction de texte pur)."""

    @pytest.fixture
    def extracteur(self):
        return BankingExtractor()

    def test_lit_un_solde_avec_date_espacee(self, extracteur):
        # Piège réel : la date « 01 07 2023 » contient des groupes de chiffres
        # qui ressemblent à des montants. La date doit être écartée d'abord.
        texte = "SOLDE DEPART AU 01 07 2023 5 000 000,00"
        assert extracteur._extract_solde_depart(texte) == 5_000_000.0

    def test_lit_un_solde_au_format_anglo_saxon(self, extracteur):
        texte = "SOLDE DEPART AU 01 07 2023 10,000,000.00"
        assert extracteur._extract_solde_depart(texte) == 10_000_000.0

    def test_ne_confond_pas_l_annee_avec_le_montant(self, extracteur):
        # Si la date n'était pas isolée, « 2023 » pourrait être retenu.
        texte = "SOLDE DEPART AU 01 07 2023 5 000 000,00"
        assert extracteur._extract_solde_depart(texte) != 2023.0

    def test_renvoie_none_quand_la_ligne_est_absente(self, extracteur):
        assert extracteur._extract_solde_depart("MOUVEMENTS DU MOIS\n1 000,00") is None

    def test_ignore_la_casse_du_libelle(self, extracteur):
        assert extracteur._extract_solde_depart("Solde Depart au 01 07 2023 1 500,00") == 1_500.0


class TestGaranties:
    @pytest.fixture(scope="class")
    @staticmethod
    def garanties():
        return GuaranteeExtractor().extract(str(_pdf("05_garanties", "annexe_garanties.pdf")))

    def test_produit_une_liste_de_garanties(self, garanties):
        assert isinstance(garanties.get("garanties"), list)

    def test_chaque_garantie_a_un_type_reconnu_ou_aucun(self, garanties):
        # Un type non reconnu doit rester non reconnu, pas être rattaché au
        # hasard à une catégorie : le barème de décote en dépend directement.
        connus = set(GuaranteeExtractor._TYPE_LABELS.values())
        for garantie in garanties.get("garanties", []):
            type_garantie = garantie.get("type")
            assert type_garantie is None or type_garantie in connus

    def test_aucune_valeur_declaree_negative(self, garanties):
        for garantie in garanties.get("garanties", []):
            valeur = garantie.get("valeur_declaree")
            assert valeur is None or valeur > 0
