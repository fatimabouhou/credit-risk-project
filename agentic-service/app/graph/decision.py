"""
2ème agent : décision de crédit.

Rôle : à partir du diagnostic DÉJÀ produit par le premier agent (secteur,
taille, anomalies, patterns croisés, score Altman, conclusion), rendre une
décision de crédit synthétique (accord/refus/à surveiller) + justification.

Volontairement PAS un 2ème passage dans le graphe LangGraph de planner.py :
un appel LLM indépendant, avec un contexte neuf et compact (juste le
diagnostic déjà condensé, jamais l'historique complet de l'agent 1 —
outils bruts, chunks RAG...). Sinon le coût en tokens de ce 2ème agent
grossirait avec la taille de l'exploration du premier, alors qu'il n'a
besoin que du résultat.

Provider différent de l'agent 1 (OpenRouter au lieu de Groq) : les deux
agents ont des quotas totalement indépendants, un run de l'agent 1 ne
peut jamais empêcher l'agent 2 de tourner (et inversement).
"""

import json
import os

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

load_dotenv()

OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "openai/gpt-oss-20b:free")

DECISION_SYSTEM_PROMPT = """Tu es l'agent de décision de crédit d'une plateforme de risque de crédit.

Tu reçois un diagnostic déjà produit par l'agent d'analyse financière : secteur, taille,
anomalies détectées, combinaisons de ratios significatives ("patterns"), score de
défaillance Altman, et la conclusion déjà rédigée. C'est un dossier déjà analysé, pas des
données brutes à recalculer.

Ta mission : rendre une décision de crédit synthétique à partir de CE diagnostic, rien
d'autre.

Règles strictes :
- Ne recalcule JAMAIS un ratio, un score ou un verdict : ils sont déjà corrects dans le
  diagnostic reçu, contente-toi de les utiliser.
- N'invente aucun fait absent de ce diagnostic (pas de garanties, de comportement bancaire
  ou d'historique non mentionnés).
- "decision" : EXACTEMENT une valeur parmi "accord", "refus", "a_surveiller".
- "justification" : 2 à 4 phrases qui citent explicitement les signaux (patterns, anomalies,
  altman_score) qui pèsent le plus dans ta décision — jamais une reformulation générique du
  diagnostic déjà donné.

Réponds STRICTEMENT en JSON, sans texte autour, sans balise markdown :
{"decision": "accord|refus|a_surveiller", "justification": "..."}
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
    conclusion) — jamais les tool_calls bruts ni les passages RAG.

    Retourne {"decision", "justification"} ou, si le modèle n'a pas
    répondu en JSON valide (arrive avec des modèles gratuits moins
    fiables sur le function-calling/format strict), {"decision": None,
    "justification": <texte brut>, "erreur_parsing": True} plutôt que de
    lever une exception qui ferait échouer toute la réponse de l'API.
    """
    messages = [
        SystemMessage(content=DECISION_SYSTEM_PROMPT),
        HumanMessage(content=json.dumps(diagnostic, ensure_ascii=False)),
    ]
    response = get_decision_llm().invoke(messages)
    raw = response.content.strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    try:
        parsed = json.loads(raw)
        return {"decision": parsed.get("decision"), "justification": parsed.get("justification")}
    except (json.JSONDecodeError, TypeError):
        return {"decision": None, "justification": raw, "erreur_parsing": True}


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
        "conclusion": "La liquidité du client est confortable... [conclusion complète]",
    }

    print(json.dumps(decide_credit(exemple_diagnostic), ensure_ascii=False, indent=2))
