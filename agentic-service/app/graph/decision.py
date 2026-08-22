"""
2ème agent : décision de crédit.

Rôle : à partir du diagnostic DÉJÀ produit par le premier agent (secteur,
taille, anomalies, patterns croisés, score Altman, DSCR, tendances,
conformité réglementaire DGI/CNSS, alertes Centrale des Risques BAM), rendre
une décision de crédit synthétique (accord/refus/à surveiller).

La décision elle-même (compute_risk_score) est calculée en Python, PAS par
le LLM : un premier essai laissant le LLM juger librement à partir du
diagnostic donnait une décision non reproductible (deux dossiers similaires
pouvaient être tranchés différemment) et non auditable. Même symptôme, une
fois de plus, que les verdicts de ratios et la citation Altman ailleurs
dans ce service — tout ce qui doit être fiable est sorti du LLM.

Le score est construit à partir des signaux DÉJÀ INTERPRÉTÉS par l'agent 1
(patterns, anomalies, zone Altman, DSCR, tendances), jamais des ratios
bruts : trois ratios de liquidité faibles (current/quick/cash ratio) ne
comptent qu'une fois, via le pattern de liquidité qui les regroupe déjà —
pondérer chaque ratio séparément aurait sur-compté un seul problème sous
plusieurs angles corrélés.

Le LLM garde un rôle : rédiger la justification en langage naturel à partir
du score déjà tranché et des signaux qui l'ont produit — c'est ce qu'il
fait bien (synthèse), pas décider (ce qu'il fait de façon peu fiable).

Volontairement PAS un 2ème passage dans le graphe LangGraph de planner.py :
un appel LLM indépendant, avec un contexte neuf et compact (juste le
diagnostic déjà condensé, jamais l'historique complet de l'agent 1 —
outils bruts, chunks RAG...) — le coût en tokens de ce 2ème agent reste
indépendant de la taille de l'exploration du premier.

Provider différent de l'agent 1 (OpenRouter au lieu de Groq) : les deux
agents ont des quotas totalement indépendants, un run de l'agent 1 ne
peut jamais empêcher l'agent 2 de tourner (et inversement).
"""

import json
import os

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from tools.patterns.pattern_tool import ratios_couverts

load_dotenv()

OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "openai/gpt-oss-20b:free")

# Poids par catégorie de signal DÉJÀ INTERPRÉTÉ, jamais par ratio individuel
# (voir docstring du module) — validés avec l'utilisateur avant implémentation.
_POINTS_PATTERN_ELEVE = 3
_POINTS_PATTERN_MODERE = 1
_POINTS_ANOMALIE_GRAVE = 2
_POINTS_ALTMAN_DISTRESS = 4
_POINTS_ALTMAN_GREY = 2
_POINTS_DSCR_INSUFFISANT = 3
_POINTS_DSCR_NON_EVALUABLE = 5
_POINTS_GARANTIE_COUVERTURE_INSUFFISANTE = 2
_POINTS_TENDANCE_DEGRADEE = 2
_POINTS_NON_CONFORMITE = 5
_POINTS_INCIDENT_BAM = 5

# 3 exercices par indicateur (voir trend_tool.py) : direction "mauvaise"
# par indicateur (pas la même pour tous — total_dettes en hausse est
# mauvais, contrairement à chiffre_affaires/ebitda/fonds_propres/
# resultat_net). Seuil >= 2 indicateurs mauvais avant de compter la
# tendance comme dégradée : ces 5 indicateurs sont eux-mêmes corrélés
# (ex. resultat_net et ebitda bougent souvent ensemble), un seul en
# baisse isolée ne suffit pas à parler de dégradation globale.
_TENDANCE_DIRECTION_MAUVAISE = {
    "chiffre_affaires": "Baisse",
    "ebitda": "Baisse",
    "resultat_net": "Baisse",
    "total_dettes": "Hausse",
    "fonds_propres": "Baisse",
}
_TENDANCE_SEUIL_DEGRADEE = 2

_SEUIL_ACCORD_MAX = 3
_SEUIL_SURVEILLANCE_MAX = 7


def _is_tendance_degradee(tendances: dict | None) -> bool:
    if not tendances:
        return False
    nb_mauvaises = sum(
        1
        for indicateur, direction_mauvaise in _TENDANCE_DIRECTION_MAUVAISE.items()
        if tendances.get(indicateur, {}).get("tendance_recente") == direction_mauvaise
    )
    return nb_mauvaises >= _TENDANCE_SEUIL_DEGRADEE


def compute_risk_score(diagnostic: dict) -> dict:
    """
    Calcule la décision de façon déterministe et auditable : chaque
    contribution est tracée (label + points), pas juste un total opaque.
    """
    contributions = []

    for pattern in diagnostic.get("patterns") or []:
        niveau = pattern.get("niveau_risque")
        if niveau == "élevé":
            contributions.append(
                {"label": f"Pattern {pattern.get('id')} (risque élevé)", "points": _POINTS_PATTERN_ELEVE}
            )
        elif niveau == "modéré":
            contributions.append(
                {"label": f"Pattern {pattern.get('id')} (risque modéré)", "points": _POINTS_PATTERN_MODERE}
            )

    patterns = diagnostic.get("patterns") or []
    ratios_deja_couverts = ratios_couverts([p.get("id") for p in patterns if p.get("id")])

    for anomalie in diagnostic.get("anomalies") or []:
        if anomalie.get("ratio_name") in ratios_deja_couverts:
            continue  # déjà compté via le pattern qui en dérive (voir ratios_couverts)
        if anomalie.get("severite") == "elevee":
            contributions.append(
                {"label": f"Anomalie grave : {anomalie.get('ratio_name')}", "points": _POINTS_ANOMALIE_GRAVE}
            )

    altman_score = diagnostic.get("altman_score") or {}
    zone = altman_score.get("zone")
    if zone == "distress":
        contributions.append({"label": "Score Altman en zone 'distress'", "points": _POINTS_ALTMAN_DISTRESS})
    elif zone == "grey":
        contributions.append({"label": "Score Altman en zone 'grey'", "points": _POINTS_ALTMAN_GREY})

    dscr = diagnostic.get("dscr") or {}
    if dscr.get("is_dscr_acceptable") is False:
        contributions.append({"label": "DSCR insuffisant", "points": _POINTS_DSCR_INSUFFISANT})
    elif dscr.get("nouveau_credit_evaluable") is False:
        contributions.append(
            {"label": "DSCR après nouveau crédit non évaluable (montant ou durée manquant)", "points": _POINTS_DSCR_NON_EVALUABLE}
        )

    garanties = diagnostic.get("garanties") or {}
    if garanties.get("evaluable") is True and garanties.get("couverture_pct", 0) < 100:
        contributions.append(
            {"label": "Couverture indicative des garanties inférieure à 100 %", "points": _POINTS_GARANTIE_COUVERTURE_INSUFFISANTE}
        )

    if _is_tendance_degradee(diagnostic.get("tendances")):
        contributions.append({"label": "Tendance dégradée sur plusieurs indicateurs", "points": _POINTS_TENDANCE_DEGRADEE})

    conformite = diagnostic.get("conformite_reglementaire") or {}
    attestations = conformite.get("attestations_legales") or []
    non_conformes = [a for a in attestations if a.get("is_compliant") is False]
    if non_conformes:
        sources = ", ".join(a.get("source", "?") for a in non_conformes)
        contributions.append(
            {"label": f"Non-conformité réglementaire ({sources})", "points": _POINTS_NON_CONFORMITE}
        )

    if diagnostic.get("alertes_coherence"):
        contributions.append(
            {"label": "Incident de paiement détecté (Centrale des Risques BAM)", "points": _POINTS_INCIDENT_BAM}
        )

    score = sum(c["points"] for c in contributions)
    if score <= _SEUIL_ACCORD_MAX:
        decision = "accord"
    elif score <= _SEUIL_SURVEILLANCE_MAX:
        decision = "a_surveiller"
    else:
        decision = "refus"

    return {"decision": decision, "score": score, "contributions": contributions}


JUSTIFICATION_SYSTEM_PROMPT = """Tu es l'agent de décision de crédit d'une plateforme de risque de crédit.

La décision ("decision") et le détail des points qui l'ont produite ("contributions") sont
déjà calculés — PAS par toi, par une grille de points déterministe appliquée aux signaux
déjà détectés par l'agent d'analyse (patterns, anomalies, score Altman, DSCR, tendances).

Ta seule tâche : rédiger une justification de 2 à 4 phrases, factuelle, style rapport
bancaire, qui explique cette décision à partir de "contributions" (les signaux qui ont
réellement compté) et du "diagnostic" fourni (contexte : secteur, taille, conclusion déjà
rédigée par l'agent d'analyse).

Règles strictes :
- Ne remets JAMAIS en cause la décision reçue, ne la recalcule jamais toi-même.
- N'invente aucun fait absent de "contributions"/"diagnostic".
- Cite les signaux qui pèsent le plus (triés par points dans "contributions"), pas
  nécessairement tous s'il y en a beaucoup.

Réponds STRICTEMENT en JSON, sans texte autour, sans balise markdown :
{"justification": "..."}
"""

_llm = None


def get_decision_llm():
    global _llm
    if _llm is None:
        _llm = ChatOpenAI(
            model=OPENROUTER_MODEL,
            temperature=0,
            api_key=os.environ["OPENROUTER_API_KEY"],
            base_url="https://openrouter.ai/api/v1",
        )
    return _llm


def decide_credit(diagnostic: dict) -> dict:
    """
    `diagnostic` : le sous-ensemble déjà condensé du résultat de l'agent 1
    (secteur, taille, anomalies, patterns, altman_score, coherence_altman,
    dscr, tendances, conclusion) — jamais les tool_calls bruts ni les
    passages RAG.

    Retourne {"decision", "score", "contributions", "justification"}. Si le
    LLM ne répond pas en JSON valide (arrive avec des modèles gratuits
    moins fiables sur le format strict), "justification" retombe sur une
    phrase générée à partir de "contributions" directement — la décision
    elle-même reste fiable dans tous les cas, elle ne dépend jamais de
    cette étape.
    """
    resultat = compute_risk_score(diagnostic)

    messages = [
        SystemMessage(content=JUSTIFICATION_SYSTEM_PROMPT),
        HumanMessage(
            content=json.dumps(
                {"decision": resultat["decision"], "contributions": resultat["contributions"], "diagnostic": diagnostic},
                ensure_ascii=False,
            )
        ),
    ]

    try:
        response = get_decision_llm().invoke(messages)
        raw = response.content.strip()
        if raw.startswith("```"):
            raw = raw.strip("`")
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()
        justification = json.loads(raw)["justification"]
    except Exception:
        if resultat["contributions"]:
            signaux = ", ".join(c["label"] for c in resultat["contributions"])
            justification = f"Décision '{resultat['decision']}' (score {resultat['score']}) fondée sur : {signaux}."
        else:
            justification = f"Décision '{resultat['decision']}' (score {resultat['score']}) : aucun signal de risque détecté."

    return {**resultat, "justification": justification}


if __name__ == "__main__":
    import sys

    sys.stdout.reconfigure(encoding="utf-8")

    exemple_diagnostic = {
        "secteur": "COM",
        "taille": "PME",
        "anomalies": [],
        "patterns": [
            {
                "id": "GLOB.004",
                "titre": "Fragilité concentrée sur une seule dimension",
                "niveau_risque": "modéré",
                "diagnostic": "Le risque identifié semble concentré sur une seule dimension "
                "de l'analyse financière, les autres composantes restant globalement "
                "satisfaisantes.",
            },
            {
                "id": "ACT.001",
                "titre": "Difficulté de recouvrement des créances",
                "niveau_risque": "élevé",
                "diagnostic": "Un délai moyen de recouvrement des créances supérieur aux "
                "références peut accroître les besoins en fonds de roulement.",
            },
        ],
        "altman_score": {"model": "Z''", "score": 3.73, "zone": "safe", "formula_used": "Altman Z'' (1995)"},
        "coherence_altman": None,
        "dscr": {"dscr": 1.17, "is_dscr_acceptable": False},
        "tendances": None,
        "conclusion": "La liquidité du client est confortable... [conclusion complète]",
    }

    print(json.dumps(decide_credit(exemple_diagnostic), ensure_ascii=False, indent=2))
