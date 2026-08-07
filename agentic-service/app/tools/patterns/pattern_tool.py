"""
Point d'entrée public du moteur de patterns pour l'agent (voir
graph/nodes.py) — assemble contexte + moteur de matching, et ne renvoie
que les patterns effectivement déclenchés, dans un format compact prêt à
être relayé par le LLM sans relecture ni recalcul de sa part.

Les patterns sont parsés une seule fois au chargement du module (fichiers
Markdown statiques, jamais modifiés à l'exécution) plutôt qu'à chaque
appel — évite de reparser 6 fichiers à chaque tour de la boucle ReAct.
"""

from pathlib import Path

from tools.patterns.context_builder import build_pattern_context
from tools.patterns.engine import evaluate_all_patterns
from tools.patterns.parser import parse_pattern_directory
from tools.patterns.vocabulary import RATIO_NAME_MAP

_PATTERNS_DIR = Path(__file__).resolve().parents[2] / "data" / "patterns"
_ALL_PATTERNS = parse_pattern_directory(_PATTERNS_DIR)

# Un pattern peut citer jusqu'à 4 hypothèses dans le Markdown ; n'en
# garder qu'une seule dans la réponse à l'agent (les "actions
# d'investigation" ne sont pas renvoyées du tout) — le budget de
# tokens/minute Groq est serré (voir l'incident documenté dans
# benchmark_tool.py) et une hypothèse suffit à illustrer le diagnostic
# sans reproduire la fiche en entier ; le prompt système rappelle déjà
# de ne jamais la traiter comme la seule lecture possible.
_MAX_ITEMS_PER_LIST = 1

# GLOB.001 = "profil globalement sain", GLOB.003 = "profil à risque
# élevé" (voir data/patterns/06_patterns_globaux.md) — les deux extrêmes
# de la synthèse par patterns, comparés à la zone Altman pour détecter
# une divergence de lecture entre les deux approches (score statistique
# global vs combinaisons de ratios).
_GLOB_SAIN_IDS = {"GLOB.001"}
_GLOB_RISQUE_IDS = {"GLOB.003"}


def _check_altman_coherence(altman_score: dict | None, fired: list) -> dict | None:
    """
    Compare, en Python et sans appel LLM, la zone du score Altman à la
    synthèse GLOB issue des patterns — même principe que la détection
    d'incohérences déjà appliquée aux ratios individuels (voir
    benchmark_tool.py, historique). Retourne None si rien à signaler
    (pas de contradiction, ou pas de score Altman disponible) : ne pas
    ajouter de bruit quand les deux lectures convergent.
    """
    if not altman_score or not altman_score.get("zone"):
        return None
    zone = altman_score["zone"]
    fired_glob_ids = {r.pattern.id for r in fired if r.pattern.id.startswith("GLOB.")}

    if zone == "safe" and (fired_glob_ids & _GLOB_RISQUE_IDS):
        divergence = "risque élevé détecté par les patterns malgré une zone Altman 'safe'"
    elif zone == "distress" and (fired_glob_ids & _GLOB_SAIN_IDS):
        divergence = "aucun risque significatif détecté par les patterns malgré une zone Altman 'distress'"
    else:
        return None

    return {
        "altman_zone": zone,
        "divergence": divergence,
    }


def ratios_couverts(pattern_ids: list[str]) -> set[str]:
    """
    Noms de ratios INTERNES (ex. "liquidite.current_ratio", même
    vocabulaire que "ratio_name" dans anomalies_detectees, voir
    benchmark_tool.py) couverts par les conditions "required" des
    patterns donnés (identifiants comme dans "patterns_declenches",
    fusions "X / Y" gérées).

    Utilisé par graph/decision.py pour ne pas compter deux fois le même
    signal sous-jacent dans compute_risk_score : une anomalie et le
    pattern qui en dérive tous les deux, séparément, alors qu'ils
    décrivent le même problème (voir planner.py point 6d, même règle
    déjà appliquée à la conclusion texte, appliquée ici au score).
    """
    by_id = {p.id: p for p in _ALL_PATTERNS}
    covered: set[str] = set()
    for pattern_id in pattern_ids:
        for single_id in pattern_id.split(" / "):
            pattern = by_id.get(single_id.strip())
            if not pattern:
                continue
            for condition in pattern.required:
                for display_name in condition.ratios:
                    internal_name = RATIO_NAME_MAP.get(display_name)
                    if internal_name and not internal_name.startswith("TREND:"):
                        covered.add(internal_name)
    return covered


def check_client_patterns(
    client_id: str, secteur: str, taille: str | None = None, trends: dict | None = None
) -> dict:
    """
    Évalue les 49 patterns (data/patterns/) contre les ratios déjà
    calculés du client, et renvoie uniquement ceux qui se sont
    effectivement déclenchés (jamais un pattern non concluant ou
    indisponible faute de données — pas de bruit pour l'agent).
    """
    ctx = build_pattern_context(client_id, secteur, taille, trends)
    results = evaluate_all_patterns(_ALL_PATTERNS, ctx)

    fired = [r for r in results if r.declenche]
    # Les plus sévères / les plus fiables en premier, pour que l'agent les
    # traite en priorité même s'il ne cite pas tout.
    ordre_risque = {"élevé": 0, "modéré": 1, "faible": 2}
    fired.sort(key=lambda r: ordre_risque.get(r.pattern.niveau_risque, 1))

    # Certains patterns sont des doublons assumés, déclenchés par
    # exactement les mêmes conditions mais reformulés pour être
    # accessibles depuis deux tables (voir data/patterns/
    # 00_notes_methodologiques.md § 3, ex. RENT.008 / CROSS.RENT.001 —
    # texte différent, conditions requises identiques). Les envoyer deux
    # fois au LLM gonflerait le budget de tokens/minute pour une
    # information redondante : on ne garde que la première occurrence
    # (l'ordre des fichiers 01-06 place la version univariée avant son
    # doublon croisé), en citant les deux identifiants pour ne rien
    # perdre de la traçabilité. Le doublon est détecté par la SIGNATURE
    # des conditions requises, pas par le texte du diagnostic (les deux
    # versions sont reformulées différemment, jamais mot pour mot identiques).
    deduped: dict[tuple, dict] = {}
    for r in fired:
        key = tuple(sorted((tuple(c.ratios), tuple(c.verdicts)) for c in r.pattern.required))
        if key in deduped:
            deduped[key]["id"] += f" / {r.pattern.id}"
            continue
        deduped[key] = {
            "id": r.pattern.id,
            "titre": r.pattern.titre,
            "niveau_risque": r.pattern.niveau_risque,
            "priorite": r.pattern.priorite,
            "confiance": r.confiance_ajustee,
            "diagnostic": r.pattern.diagnostic,
            "hypotheses": r.pattern.hypotheses[:_MAX_ITEMS_PER_LIST],
        }

    response = {
        "client_id": client_id,
        "secteur": ctx["secteur"],
        "taille": ctx["taille"],
        "patterns_declenches": list(deduped.values()),
    }
    coherence = _check_altman_coherence(ctx.get("altman_score"), fired)
    if coherence:
        response["coherence_altman"] = coherence
    return response


if __name__ == "__main__":
    import json
    import sys

    sys.stdout.reconfigure(encoding="utf-8")

    client_id = sys.argv[1] if len(sys.argv) > 1 else "data"
    secteur = sys.argv[2] if len(sys.argv) > 2 else "COM"
    taille = sys.argv[3] if len(sys.argv) > 3 else None

    result = check_client_patterns(client_id, secteur, taille)
    print(json.dumps(result, ensure_ascii=False, indent=2))
