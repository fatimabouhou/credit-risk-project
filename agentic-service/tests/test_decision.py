"""
compute_risk_score : calcul déterministe de la décision de crédit.

C'est la seule partie du service qui ne passe PAS par un LLM — donc la seule
qui puisse être verrouillée par des tests. Les seuils vérifiés ici sont ceux
que l'interface affiche sur le cadran d'indice de risque : les faire diverger
casserait la lecture du dossier côté frontend.
"""

import pytest

from graph.decision import (
    _SEUIL_ACCORD_MAX,
    _SEUIL_SURVEILLANCE_MAX,
    _is_tendance_degradee,
    compute_risk_score,
)


def _points_de(resultat, fragment):
    """Points de la première contribution dont le label contient `fragment`."""
    for contribution in resultat["contributions"]:
        if fragment in contribution["label"]:
            return contribution["points"]
    return None


class TestDossierVierge:
    def test_un_diagnostic_vide_donne_un_accord_a_zero(self):
        resultat = compute_risk_score({})
        assert resultat == {"decision": "accord", "score": 0, "contributions": []}

    def test_des_listes_nulles_sont_traitees_comme_vides(self):
        resultat = compute_risk_score(
            {"patterns": None, "anomalies": None, "altman_score": None, "dscr": None, "garanties": None}
        )
        assert resultat["score"] == 0


class TestPatterns:
    def test_un_pattern_eleve_pese_trois_points(self):
        resultat = compute_risk_score({"patterns": [{"id": "ACT.001", "niveau_risque": "élevé"}]})
        assert resultat["score"] == 3
        assert _points_de(resultat, "ACT.001") == 3

    def test_un_pattern_modere_pese_un_point(self):
        resultat = compute_risk_score({"patterns": [{"id": "ACT.004", "niveau_risque": "modéré"}]})
        assert resultat["score"] == 1

    def test_un_niveau_inconnu_ne_pese_rien(self):
        # Pas de points par défaut : un niveau non reconnu n'est pas un risque
        # supposé, il est ignoré plutôt qu'estimé.
        resultat = compute_risk_score({"patterns": [{"id": "X.001", "niveau_risque": "faible"}]})
        assert resultat["contributions"] == []

    def test_les_patterns_se_cumulent(self):
        resultat = compute_risk_score(
            {
                "patterns": [
                    {"id": "A.001", "niveau_risque": "élevé"},
                    {"id": "B.001", "niveau_risque": "modéré"},
                ]
            }
        )
        assert resultat["score"] == 4

    def test_le_label_cite_l_identifiant_du_pattern(self):
        # La décision doit rester auditable : chaque point porte son origine.
        resultat = compute_risk_score({"patterns": [{"id": "CROSS.LIQ.001", "niveau_risque": "élevé"}]})
        assert "CROSS.LIQ.001" in resultat["contributions"][0]["label"]


class TestAnomalies:
    def test_une_anomalie_grave_pese_deux_points(self):
        resultat = compute_risk_score(
            {"anomalies": [{"ratio_name": "liquidite.quick_ratio", "severite": "elevee"}]}
        )
        assert resultat["score"] == 2

    def test_une_anomalie_non_grave_ne_pese_rien(self):
        resultat = compute_risk_score(
            {"anomalies": [{"ratio_name": "liquidite.quick_ratio", "severite": "moderee"}]}
        )
        assert resultat["contributions"] == []

    def test_une_anomalie_deja_couverte_par_un_pattern_n_est_pas_recomptee(self):
        """
        Le double comptage est le piège central de ce calcul : une anomalie et
        le pattern qui en dérive décrivent le même problème sous-jacent.
        """
        from tools.patterns.pattern_tool import ratios_couverts

        couverts = ratios_couverts(["ACT.001"])
        if not couverts:
            pytest.skip("le pattern ACT.001 ne couvre aucun ratio dans ce référentiel")
        ratio = next(iter(couverts))

        resultat = compute_risk_score(
            {
                "patterns": [{"id": "ACT.001", "niveau_risque": "élevé"}],
                "anomalies": [{"ratio_name": ratio, "severite": "elevee"}],
            }
        )
        # Seul le pattern compte : 3 points, pas 3 + 2.
        assert resultat["score"] == 3
        assert len(resultat["contributions"]) == 1

    def test_une_anomalie_hors_perimetre_du_pattern_reste_comptee(self):
        resultat = compute_risk_score(
            {
                "patterns": [{"id": "ACT.001", "niveau_risque": "élevé"}],
                "anomalies": [{"ratio_name": "ratio.inexistant.pour.ce.pattern", "severite": "elevee"}],
            }
        )
        assert resultat["score"] == 5


class TestAltman:
    @pytest.mark.parametrize("zone,points", [("distress", 4), ("grey", 2)])
    def test_les_zones_a_risque_sont_penalisees(self, zone, points):
        resultat = compute_risk_score({"altman_score": {"zone": zone}})
        assert resultat["score"] == points

    @pytest.mark.parametrize("zone", ["safe", None, "inconnue"])
    def test_les_autres_zones_ne_pesent_rien(self, zone):
        resultat = compute_risk_score({"altman_score": {"zone": zone}})
        assert resultat["contributions"] == []


class TestDscr:
    def test_un_dscr_insuffisant_pese_trois_points(self):
        resultat = compute_risk_score({"dscr": {"is_dscr_acceptable": False}})
        assert resultat["score"] == 3

    def test_un_dscr_non_evaluable_pese_cinq_points(self):
        # Plus lourd qu'un DSCR insuffisant : un dossier qu'on ne peut pas
        # évaluer est plus gênant qu'un dossier évalué et jugé faible.
        resultat = compute_risk_score({"dscr": {"nouveau_credit_evaluable": False}})
        assert resultat["score"] == 5

    def test_un_dscr_insuffisant_prime_sur_le_non_evaluable(self):
        resultat = compute_risk_score(
            {"dscr": {"is_dscr_acceptable": False, "nouveau_credit_evaluable": False}}
        )
        assert resultat["score"] == 3
        assert len(resultat["contributions"]) == 1

    def test_un_dscr_acceptable_ne_pese_rien(self):
        resultat = compute_risk_score({"dscr": {"is_dscr_acceptable": True, "nouveau_credit_evaluable": True}})
        assert resultat["contributions"] == []


class TestGaranties:
    def test_une_couverture_insuffisante_pese_deux_points(self):
        resultat = compute_risk_score({"garanties": {"evaluable": True, "couverture_pct": 76.0}})
        assert resultat["score"] == 2

    def test_une_couverture_suffisante_ne_pese_rien(self):
        resultat = compute_risk_score({"garanties": {"evaluable": True, "couverture_pct": 120.0}})
        assert resultat["contributions"] == []

    def test_des_garanties_non_evaluables_ne_penalisent_pas(self):
        # Sans montant de crédit, l'absence de couverture n'est pas un signal.
        resultat = compute_risk_score({"garanties": {"evaluable": False, "couverture_pct": None}})
        assert resultat["contributions"] == []


class TestTendances:
    def test_un_seul_indicateur_en_baisse_ne_suffit_pas(self):
        # Les cinq indicateurs sont corrélés : un seul mouvement ne fait pas
        # une dégradation globale.
        assert _is_tendance_degradee({"chiffre_affaires": {"tendance_recente": "Baisse"}}) is False

    def test_deux_indicateurs_mauvais_declenchent_la_degradation(self):
        assert _is_tendance_degradee(
            {
                "chiffre_affaires": {"tendance_recente": "Baisse"},
                "ebitda": {"tendance_recente": "Baisse"},
            }
        ) is True

    def test_la_direction_mauvaise_depend_de_l_indicateur(self):
        # Une hausse est mauvaise pour les dettes, bonne pour le reste.
        assert _is_tendance_degradee(
            {
                "total_dettes": {"tendance_recente": "Hausse"},
                "fonds_propres": {"tendance_recente": "Baisse"},
            }
        ) is True
        assert _is_tendance_degradee(
            {
                "total_dettes": {"tendance_recente": "Baisse"},
                "chiffre_affaires": {"tendance_recente": "Hausse"},
            }
        ) is False

    @pytest.mark.parametrize("tendances", [None, {}])
    def test_absence_de_tendances_n_est_pas_une_degradation(self, tendances):
        assert _is_tendance_degradee(tendances) is False

    def test_une_tendance_degradee_pese_deux_points(self):
        resultat = compute_risk_score(
            {
                "tendances": {
                    "chiffre_affaires": {"tendance_recente": "Baisse"},
                    "ebitda": {"tendance_recente": "Baisse"},
                }
            }
        )
        assert resultat["score"] == 2


class TestConformiteEtIncidents:
    def test_une_attestation_non_conforme_pese_cinq_points(self):
        resultat = compute_risk_score(
            {"conformite_reglementaire": {"attestations_legales": [{"source": "DGI", "is_compliant": False}]}}
        )
        assert resultat["score"] == 5
        assert "DGI" in resultat["contributions"][0]["label"]

    def test_plusieurs_non_conformites_donnent_une_seule_contribution(self):
        resultat = compute_risk_score(
            {
                "conformite_reglementaire": {
                    "attestations_legales": [
                        {"source": "DGI", "is_compliant": False},
                        {"source": "CNSS", "is_compliant": False},
                    ]
                }
            }
        )
        assert resultat["score"] == 5
        assert "DGI, CNSS" in resultat["contributions"][0]["label"]

    def test_des_attestations_conformes_ne_pesent_rien(self):
        resultat = compute_risk_score(
            {"conformite_reglementaire": {"attestations_legales": [{"source": "DGI", "is_compliant": True}]}}
        )
        assert resultat["contributions"] == []

    def test_un_incident_de_paiement_pese_cinq_points(self):
        resultat = compute_risk_score({"alertes_coherence": ["Incident BAM détecté"]})
        assert resultat["score"] == 5

    def test_une_liste_d_alertes_vide_ne_pese_rien(self):
        resultat = compute_risk_score({"alertes_coherence": []})
        assert resultat["contributions"] == []


class TestSeuilsDeDecision:
    """
    Bornes inclusives : accord <= 3, surveillance <= 7, refus au-delà.
    Le cadran du frontend est gradué sur ces deux valeurs.
    """

    def _score_exact(self, points):
        # Un pattern modéré vaut 1 point : le répéter donne le score voulu.
        patterns = [{"id": f"P.{i:03d}", "niveau_risque": "modéré"} for i in range(points)]
        return compute_risk_score({"patterns": patterns})

    @pytest.mark.parametrize("points", [0, 1, 2, 3])
    def test_accord_jusqu_au_seuil_inclus(self, points):
        resultat = self._score_exact(points)
        assert resultat["score"] == points
        assert resultat["decision"] == "accord"

    @pytest.mark.parametrize("points", [4, 5, 6, 7])
    def test_surveillance_entre_les_deux_seuils(self, points):
        assert self._score_exact(points)["decision"] == "a_surveiller"

    @pytest.mark.parametrize("points", [8, 12, 30])
    def test_refus_au_dela_du_second_seuil(self, points):
        assert self._score_exact(points)["decision"] == "refus"

    def test_les_seuils_exposes_gardent_les_valeurs_attendues(self):
        # Le frontend duplique ces bornes pour graduer son cadran : les
        # changer ici sans le prévenir décalerait la lecture du dossier.
        assert _SEUIL_ACCORD_MAX == 3
        assert _SEUIL_SURVEILLANCE_MAX == 7


class TestTracabilite:
    def test_le_score_est_la_somme_exacte_des_contributions(self):
        resultat = compute_risk_score(
            {
                "patterns": [{"id": "A.001", "niveau_risque": "élevé"}],
                "altman_score": {"zone": "grey"},
                "dscr": {"is_dscr_acceptable": False},
            }
        )
        assert resultat["score"] == sum(c["points"] for c in resultat["contributions"])
        assert resultat["score"] == 8
        assert resultat["decision"] == "refus"

    def test_chaque_contribution_porte_un_label_et_des_points(self):
        resultat = compute_risk_score({"altman_score": {"zone": "distress"}})
        for contribution in resultat["contributions"]:
            assert contribution["label"]
            assert isinstance(contribution["points"], int)
