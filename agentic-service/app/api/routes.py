"""
Routes HTTP du Financial Analysis Agent.

Le checkpointer Postgres (voir db/checkpointer.py) est ouvert une seule
fois au démarrage du service (main.py, lifespan) et injecté ici via la
variable de module `checkpointer` — pas rouvert à chaque requête (coût
de connexion évité), même pattern que db_service instancié une seule
fois au niveau module dans financial-service/document-service.
"""

import json
import logging
import uuid

from fastapi import APIRouter, HTTPException, status
from langchain_core.messages import HumanMessage, ToolMessage

from db.history import list_analysis_history
from graph.decision import decide_credit
from graph.workflow import MAX_TOOL_ERRORS, build_workflow

logger = logging.getLogger("AgenticAPI")
router = APIRouter()

# Injecté par main.py (lifespan) au démarrage du service.
checkpointer = None


def _extract_benchmark(messages: list) -> dict | None:
    """
    Retrouve le dernier résultat de outil_benchmark_sectoriel dans
    l'historique de messages et le renvoie déjà structuré (secteur,
    taille, ratios avec verdict).

    Pourquoi ne pas demander au LLM de reformuler ça en JSON structuré
    lui-même : ce serait un nouveau maillon non fiable ajouté après coup
    (mêmes symptômes qu'avant le calcul déterministe des verdicts) — les
    données structurées existent déjà, calculées et vérifiées, dans la
    réponse de l'outil ; ce helper les récupère telles quelles plutôt que
    de les faire retraverser le LLM. Retourne None si l'outil n'a pas été
    appelé (ex. secteur non déterminable, voir planner.py).
    """
    for message in reversed(messages):
        if isinstance(message, ToolMessage) and message.name == "outil_benchmark_sectoriel":
            try:
                data = json.loads(message.content)
            except (json.JSONDecodeError, TypeError):
                return None
            if "comparisons" not in data:
                return None  # message d'erreur texte, pas un résultat structuré
            return {
                "secteur": data.get("secteur"),
                "taille": data.get("taille"),
                "taille_source": data.get("taille_source"),
                "taille_ecart": data.get("taille_ecart"),
                "ratios": data.get("comparisons", []),
                "anomalies": data.get("anomalies_detectees", []),
                "ratios_non_comparables": data.get("comparisons_indisponibles", []),
                "champs_manquants": data.get("champs_manquants", []),
            }
    return None


def _extract_patterns(messages: list) -> dict:
    """
    Même principe que _extract_benchmark, pour outil_patterns_croises :
    les combinaisons de ratios réellement déclenchées (diagnostic,
    hypothèses) — le signal le plus riche pour la partie "risques" de la
    conclusion (voir planner.py) — et "coherence_altman" (présent
    seulement en cas de divergence entre le score Altman et la synthèse
    par patterns, voir tools/patterns/pattern_tool.py). Listes/champs
    vides si l'outil n'a pas été appelé ou n'a rien déclenché (état
    normal, pas une erreur).
    """
    for message in reversed(messages):
        if isinstance(message, ToolMessage) and message.name == "outil_patterns_croises":
            try:
                data = json.loads(message.content)
            except (json.JSONDecodeError, TypeError):
                return {"patterns": [], "coherence_altman": None}
            return {
                "patterns": data.get("patterns_declenches", []),
                "coherence_altman": data.get("coherence_altman"),
            }
    return {"patterns": [], "coherence_altman": None}


def _extract_altman_score(messages: list) -> dict | None:
    """
    Retrouve le dernier résultat de outil_rapport_financier et en extrait
    "altman_score" (déjà calculé par financial-service, voir
    ScoringEngine) — même principe que _extract_benchmark : donnée
    structurée existante, pas reformulée par le LLM.
    """
    for message in reversed(messages):
        if isinstance(message, ToolMessage) and message.name == "outil_rapport_financier":
            try:
                data = json.loads(message.content)
            except (json.JSONDecodeError, TypeError):
                return None
            return data.get("altman_score")
    return None


def _extract_dscr(messages: list) -> dict | None:
    """
    "couverture_dette_dscr" ("dscr"/"is_dscr_acceptable") fait partie du
    payload de outil_rapport_financier, TOUJOURS appelé (pas optionnel
    comme outil_tendances/outil_validation_dossier) — donc disponible dès
    que l'analyse a pu aller au bout.
    """
    for message in reversed(messages):
        if isinstance(message, ToolMessage) and message.name == "outil_rapport_financier":
            try:
                data = json.loads(message.content)
            except (json.JSONDecodeError, TypeError):
                return None
            return data.get("couverture_dette_dscr")
    return None


def _extract_tendances(messages: list) -> dict | None:
    """
    "tendances" (outil_tendances) : OPTIONNEL, l'agent 1 ne l'appelle que
    s'il juge que la trajectoire sur 3 exercices apporte quelque chose à
    CE dossier. None si jamais appelé — pas une erreur, juste un signal
    absent (compute_risk_score le traite comme neutre, voir decision.py).
    """
    for message in reversed(messages):
        if isinstance(message, ToolMessage) and message.name == "outil_tendances":
            try:
                data = json.loads(message.content)
            except (json.JSONDecodeError, TypeError):
                return None
            return data.get("tendances")
    return None


def _extract_validation(messages: list) -> dict | None:
    """
    "alertes_coherence" (ex. incident de paiement détecté à la Centrale
    des Risques BAM) et "conformite_reglementaire" (attestations DGI/
    CNSS) — outil_validation_dossier, OPTIONNEL comme outil_tendances :
    None si jamais appelé (l'agent 1 ne le juge pertinent que s'il a un
    doute sur la fiabilité du dossier).
    """
    for message in reversed(messages):
        if isinstance(message, ToolMessage) and message.name == "outil_validation_dossier":
            try:
                data = json.loads(message.content)
            except (json.JSONDecodeError, TypeError):
                return None
            return {
                "alertes_coherence": data.get("alertes_coherence", []),
                "conformite_reglementaire": data.get("conformite_reglementaire", {}),
            }
    return None


_ALTMAN_ZONE_INTERPRETATION = {
    "safe": "un risque de défaillance faible selon ce modèle",
    "grey": "une zone d'incertitude selon ce modèle",
    "distress": "un risque de défaillance élevé selon ce modèle",
}


def _inject_altman_sentence(conclusion: str, altman_score: dict | None, coherence_altman: dict | None) -> str:
    """
    Ajoute la citation du score Altman à la conclusion par du code, pas
    par le LLM : un test réel (client "data" simulé en zone "distress")
    a montré que le LLM omet ce chiffre malgré une instruction explicite
    "OBLIGATOIRE" dans le prompt système — même symptôme, une fois de
    plus, que les verdicts de ratios avant leur passage en Python (voir
    ratio_table_parser.py). altman_score non calculé/non null uniquement
    : sinon la conclusion reste inchangée.

    Placement : "safe"/"grey" ouvre le 1er paragraphe (dimensions
    saines) ; "distress" ouvre le 2e (risques) — même règle que
    planner.py appliquait auparavant au LLM. "coherence_altman" (divergence
    entre le score et les patterns) est toujours ajouté au paragraphe 2,
    juste après la phrase Altman si elle y est déjà, sinon en tête.
    """
    zone = (altman_score or {}).get("zone")
    if not altman_score or zone not in _ALTMAN_ZONE_INTERPRETATION:
        return conclusion

    altman_sentence = (
        f"Le score de défaillance Altman ({altman_score['model']}, {altman_score['formula_used']}) "
        f"s'établit à {altman_score['score']}, ce qui place l'entreprise en zone '{zone}' "
        f"et suggère {_ALTMAN_ZONE_INTERPRETATION[zone]}."
    )
    coherence_sentence = None
    if coherence_altman and coherence_altman.get("divergence"):
        coherence_sentence = (
            f"Cette lecture contraste toutefois avec l'analyse par patterns : "
            f"{coherence_altman['divergence']}."
        )

    paragraphs = conclusion.split("\n\n")
    target_index = 0 if zone in ("safe", "grey") else 1

    if target_index == 1 and len(paragraphs) < 2:
        paragraphs.append(altman_sentence)
    else:
        paragraphs[target_index] = f"{altman_sentence} {paragraphs[target_index]}"

    if coherence_sentence:
        coherence_index = 1 if len(paragraphs) > 1 else 0
        paragraphs[coherence_index] = f"{paragraphs[coherence_index]} {coherence_sentence}"

    return "\n\n".join(paragraphs)


@router.post("/analyze/{client_id}", status_code=status.HTTP_200_OK)
def analyze_client(client_id: str, taille: str | None = None):
    """
    Lance le Financial Analysis Agent sur un client : récupère son
    rapport financier et son profil réel, détermine son secteur, compare
    ses ratios aux normes RAG, et signale les anomalies détectées.

    `taille` (optionnel, "TPE"/"PME"/"GE") : la taille de l'entreprise est
    normalement calculée automatiquement (chiffre d'affaires / total
    actif du dossier, voir tools/taille_classifier.py) — inutile de le
    renseigner dans le cas normal. Ce paramètre permet un override manuel
    explicite (ex. future interface où l'utilisateur corrige un calcul
    qu'il juge faux) ; il n'est utilisé que si fourni.

    Chaque appel crée un thread_id unique (client_id + identifiant de
    run) : deux analyses du même client restent isolées l'une de l'autre
    plutôt que de partager (et faire grossir sans limite) le même
    historique de conversation — voir graph/workflow.py.

    Réponse : "conclusion" (diagnostic global en 3-5 phrases — l'agent est
    instruit à NE PAS y répéter les listes déjà ci-dessous, voir
    planner.py) accompagné des données structurées déjà calculées par
    outil_benchmark_sectoriel ("secteur", "taille", "ratios" avec verdict
    par ratio, "anomalies" (déjà filtrées, avec "severite"),
    "ratios_non_comparables", "champs_manquants") et par
    outil_patterns_croises ("patterns" : combinaisons de ratios
    réellement déclenchées, avec diagnostic et hypothèses), ainsi que
    "altman_score" (calculé par financial-service, voir
    engine/scoring.py) et "coherence_altman" (présent uniquement en cas
    de divergence entre le score Altman et la synthèse par patterns,
    voir tools/patterns/pattern_tool.py) — un futur frontend construit un
    tableau directement depuis ces champs sans reparser "conclusion".

    "decision" ("decision": "accord"/"refus"/"a_surveiller", "justification") :
    rendue par un 2ème agent indépendant (voir graph/decision.py) à partir du
    diagnostic ci-dessus, jamais à partir des données brutes. Provider et
    quota séparés de l'agent d'analyse — une panne de ce 2ème agent
    n'invalide jamais le reste de la réponse ("decision": None +
    "erreur" dans ce cas).
    """
    if checkpointer is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service pas encore prêt (checkpointer non initialisé).",
        )

    question = (
        f"Analyse le dossier du client '{client_id}' : détermine son secteur, "
        "compare ses ratios à la norme, et signale toute anomalie."
    )
    if taille:
        question += f" Taille de l'entreprise (fournie par l'utilisateur) : {taille}."
    thread_id = f"{client_id}:{uuid.uuid4().hex[:8]}"

    logger.info(f"📩 Analyse demandée pour le client '{client_id}' (thread {thread_id})")

    try:
        app_graph = build_workflow(checkpointer=checkpointer)
        final_state = app_graph.invoke(
            {"messages": [HumanMessage(content=question)], "tool_error_count": 0},
            config={"recursion_limit": 25, "configurable": {"thread_id": thread_id}},
        )
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'analyse du client '{client_id}' : {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur interne lors de l'analyse : {e}",
        )

    conclusion = final_state["messages"][-1].content
    benchmark = _extract_benchmark(final_state["messages"])
    patterns = _extract_patterns(final_state["messages"])
    altman_score = _extract_altman_score(final_state["messages"])
    dscr = _extract_dscr(final_state["messages"])
    tendances = _extract_tendances(final_state["messages"])
    validation = _extract_validation(final_state["messages"])
    conclusion = _inject_altman_sentence(conclusion, altman_score, patterns["coherence_altman"])

    secteur = benchmark["secteur"] if benchmark else None
    taille = benchmark["taille"] if benchmark else None
    anomalies = benchmark["anomalies"] if benchmark else []
    tool_error_count = final_state.get("tool_error_count", 0)

    if tool_error_count >= MAX_TOOL_ERRORS:
        # L'agent 1 a échoué à collecter les données (voir echec_node,
        # workflow.py) : compute_risk_score() sur un diagnostic vide
        # renverrait "accord" (score 0, aucun signal) — un faux négatif
        # dangereux qui confondrait "aucune donnée" avec "aucun risque".
        # L'agent 2 ne doit même pas être appelé dans ce cas.
        decision = {
            "decision": None,
            "justification": None,
            "erreur": "Analyse interrompue : données insuffisantes pour évaluer le risque de crédit.",
        }
    else:
        try:
            decision = decide_credit(
                {
                    "dscr": dscr,
                    "tendances": tendances,
                    "alertes_coherence": validation["alertes_coherence"] if validation else [],
                    "conformite_reglementaire": validation["conformite_reglementaire"] if validation else {},
                    "secteur": secteur,
                    "taille": taille,
                    "anomalies": anomalies,
                    "patterns": patterns["patterns"],
                    "altman_score": altman_score,
                    "coherence_altman": patterns["coherence_altman"],
                    "conclusion": conclusion,
                }
            )
        except Exception as e:
            # Le 2ème agent (OpenRouter, quota/provider séparé de l'agent 1) reste
            # optionnel pour la réponse : une panne ne doit pas invalider le
            # diagnostic déjà produit par l'agent 1, qui est le plus coûteux à
            # obtenir (voir graph/decision.py).
            logger.error(f"❌ Erreur lors de la décision de crédit du client '{client_id}' : {e}")
            decision = {"decision": None, "justification": None, "erreur": str(e)}

    return {
        "client_id": client_id,
        "thread_id": thread_id,
        "tool_error_count": tool_error_count,
        "secteur": secteur,
        "taille": taille,
        "taille_source": benchmark["taille_source"] if benchmark else None,
        "taille_ecart": benchmark["taille_ecart"] if benchmark else None,
        "ratios": benchmark["ratios"] if benchmark else [],
        "anomalies": anomalies,
        "patterns": patterns["patterns"],
        "altman_score": altman_score,
        "coherence_altman": patterns["coherence_altman"],
        "dscr": dscr,
        "tendances": tendances,
        "conformite_reglementaire": validation["conformite_reglementaire"] if validation else {},
        "alertes_coherence": validation["alertes_coherence"] if validation else [],
        "ratios_non_comparables": benchmark["ratios_non_comparables"] if benchmark else [],
        "champs_manquants": benchmark["champs_manquants"] if benchmark else [],
        "conclusion": conclusion,
        "decision": decision,
    }


@router.post("/decision/test", status_code=status.HTTP_200_OK)
def test_decision_agent(diagnostic: dict):
    """
    Fait tourner UNIQUEMENT l'agent 2 (decide_credit, voir graph/decision.py)
    sur un diagnostic fourni directement dans le body — sans passer par
    l'agent 1 (donc sans appel Groq, sans consommer son quota). Pensé pour
    tester la grille de points et le style de justification indépendamment
    d'une analyse complète.

    Body attendu (tous les champs optionnels, absents = neutres) :
    {
      "patterns": [{"id": "...", "niveau_risque": "élevé|modéré|faible"}],
      "anomalies": [{"ratio_name": "...", "severite": "elevee|a_surveiller"}],
      "altman_score": {"zone": "safe|grey|distress"},
      "dscr": {"is_dscr_acceptable": true|false},
      "tendances": {"resultat_net": {"tendance_recente": "Hausse|Baisse"}, ...},
      "conformite_reglementaire": {"attestations_legales": [{"source": "...", "is_compliant": true|false}]},
      "alertes_coherence": ["..."],
      "secteur": "...", "taille": "...", "conclusion": "..."
    }
    """
    try:
        return decide_credit(diagnostic)
    except Exception as e:
        logger.error(f"❌ Erreur lors du test de l'agent de décision : {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur interne lors du test de l'agent de décision : {e}",
        )


@router.get("/history/{client_id}", status_code=status.HTTP_200_OK)
def get_client_history(client_id: str):
    """
    Liste les analyses passées d'un client (une entrée par run, plus
    récent en premier) — thread_id et conclusion de chaque run déjà
    persisté par le checkpointer (voir db/history.py).
    """
    try:
        history = list_analysis_history(client_id)
    except Exception as e:
        logger.error(f"❌ Erreur lors de la lecture de l'historique du client '{client_id}' : {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur interne lors de la lecture de l'historique : {e}",
        )

    return {"client_id": client_id, "analyses": history}
