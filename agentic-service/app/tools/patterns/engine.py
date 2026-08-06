"""
Moteur de matching déterministe des patterns (data/patterns/) contre le
contexte d'un client (voir context_builder.py).

Deux étages, comme documenté dans data/patterns/06_patterns_globaux.md :
    1. Patterns de catégorie et croisés (fichiers 01-05, + GLOB.006 qui
       utilise en réalité des conditions ratio/verdict ordinaires malgré
       sa place dans le fichier 06) : évalués via evaluate_condition, qui
       compare chaque condition ratio/verdict au contexte réel du client.
    2. Patterns globaux GLOB.001-005 (fichier 06) : leurs conditions ne
       portent pas sur des ratios mais sur le RÉSULTAT de l'étage 1 (ex.
       "au moins deux patterns de niveau élevé déclenchés dans des
       catégories différentes") — nécessairement évalués après coup,
       avec une logique dédiée par pattern plutôt qu'un parseur générique
       (seulement 5 patterns concernés, texte libre non structuré).

Aucun de ces deux étages n'appelle le LLM : le matching est entièrement
déterministe, comme les verdicts de ratios (ratio_table_parser.py) et la
détection d'incohérences (benchmark_tool.py) dont il reprend le principe.
"""

from tools.patterns.models import Condition, MatchResult, Pattern
from tools.patterns.vocabulary import RATIO_NAME_MAP, is_non_evaluable, resolve_verdict

# Regroupement des catégories pour les méta-conditions GLOB (§ 2) : les 4
# catégories univariées (préfixe d'identifiant) plus un groupe "croisé"
# pour tout le reste (CROSS.*), cohérent avec la distinction que fait
# GLOB.001 lui-même entre patterns de catégorie et patterns croisés.
_CATEGORY_PREFIXES = {"LIQ": "liquidité", "RENT": "rentabilité", "SOLV": "solvabilité", "ACT": "activité"}


def _category_group(pattern_id: str) -> str:
    prefix = pattern_id.split(".", 1)[0]
    return _CATEGORY_PREFIXES.get(prefix, "croisé")


def evaluate_condition(condition: Condition, ctx: dict) -> str:
    """
    Retourne "true" / "false" / "unavailable" (jamais un bool seul : il
    faut distinguer "évalué, ne correspond pas" de "aucune donnée pour en
    juger", les deux ayant un traitement différent au niveau du pattern —
    voir evaluate_pattern).
    """
    if is_non_evaluable(condition.raw_text) or not condition.ratios or not condition.verdicts:
        return "unavailable"

    any_data_available = False
    for ratio_display in condition.ratios:
        internal = RATIO_NAME_MAP.get(ratio_display)
        if internal is None:
            continue  # ratio non calculé par financial-service (Marge brute, Interest Coverage)

        if internal.startswith("TREND:"):
            indicateur = internal.split(":", 1)[1]
            tendance = ctx["trends"].get(indicateur)
            if tendance is None:
                continue
            any_data_available = True
            if "en_croissance" in condition.verdicts and tendance == "Hausse":
                return "true"
            continue

        for verdict_voulu in condition.verdicts:
            # "négatif" joue deux rôles selon le ratio : un verdict déjà
            # calculé tel quel pour Working Capital (signe, voir
            # context_builder.py), ou un signe brut à vérifier pour les
            # ratios à verdict de norme classique (Marge nette, ROA...) où
            # une valeur négative ne produit jamais littéralement le
            # verdict "négatif" (juste "en_dessous_norme"). On essaie
            # d'abord le verdict déjà calculé ; on ne retombe sur le signe
            # brut que si "négatif" est demandé et n'a pas déjà matché.
            verdict_reel = ctx["verdicts"].get(internal)
            if verdict_reel is not None:
                any_data_available = True
                if verdict_reel == resolve_verdict(internal, verdict_voulu):
                    return "true"

            if verdict_voulu == "négatif":
                valeur = ctx["valeurs"].get(internal)
                if valeur is not None:
                    any_data_available = True
                    if valeur < 0:
                        return "true"

    return "false" if any_data_available else "unavailable"


def evaluate_pattern(pattern: Pattern, ctx: dict) -> MatchResult:
    """Évaluation générique par conditions ratio/verdict — étage 1 (et GLOB.006)."""
    if not pattern.required:
        return MatchResult(pattern=pattern, declenche=False)

    required_results = [(c, evaluate_condition(c, ctx)) for c in pattern.required]

    if any(r == "unavailable" for _, r in required_results):
        manquantes = [c.raw_text for c, r in required_results if r == "unavailable"]
        return MatchResult(
            pattern=pattern,
            declenche=False,
            indisponible_pour_donnees_manquantes=True,
            raison_indisponibilite="Données non disponibles pour : " + " ; ".join(manquantes),
        )

    declenche = all(r == "true" for _, r in required_results)
    optional_satisfaites = (
        [c for c in pattern.optional if evaluate_condition(c, ctx) == "true"] if declenche else []
    )

    return MatchResult(
        pattern=pattern,
        declenche=declenche,
        required_satisfaites=[c for c, r in required_results if r == "true"],
        required_manquantes=[c for c, r in required_results if r == "false"],
        optional_satisfaites=optional_satisfaites,
        confiance_ajustee=pattern.niveau_confiance,
    )


def evaluate_stage1(patterns: list[Pattern], ctx: dict) -> list[MatchResult]:
    """Tous les patterns sauf GLOB.001-005 (méta-conditions, voir evaluate_stage2)."""
    stage1_ids_a_exclure = {"GLOB.001", "GLOB.002", "GLOB.003", "GLOB.004", "GLOB.005"}
    return [evaluate_pattern(p, ctx) for p in patterns if p.id not in stage1_ids_a_exclure]


def _glob001(pattern: Pattern, fired: list[MatchResult]) -> MatchResult:
    aucun_eleve = not any(r.pattern.niveau_risque == "élevé" for r in fired)
    if not fired:
        return MatchResult(pattern=pattern, declenche=aucun_eleve, confiance_ajustee=pattern.niveau_confiance)
    majorite_faible = sum(1 for r in fired if r.pattern.niveau_risque == "faible") > len(fired) / 2
    return MatchResult(
        pattern=pattern, declenche=aucun_eleve and majorite_faible, confiance_ajustee=pattern.niveau_confiance
    )


def _glob002(pattern: Pattern, fired: list[MatchResult]) -> MatchResult:
    aucun_eleve = not any(r.pattern.niveau_risque == "élevé" for r in fired)
    categories_modere = {_category_group(r.pattern.id) for r in fired if r.pattern.niveau_risque == "modéré"}
    declenche = aucun_eleve and len(categories_modere) >= 2
    return MatchResult(pattern=pattern, declenche=declenche, confiance_ajustee=pattern.niveau_confiance)


def _glob003(pattern: Pattern, fired: list[MatchResult]) -> MatchResult:
    categories_eleve = {_category_group(r.pattern.id) for r in fired if r.pattern.niveau_risque == "élevé"}
    declenche = len(categories_eleve) >= 2
    confiance = pattern.niveau_confiance
    if declenche and any(r.pattern.id == "CROSS.GLOB.001" for r in fired):
        confiance = "élevé (renforcée par CROSS.GLOB.001)"
    return MatchResult(pattern=pattern, declenche=declenche, confiance_ajustee=confiance)


def _glob004(pattern: Pattern, fired: list[MatchResult]) -> MatchResult:
    eleves = [r for r in fired if r.pattern.niveau_risque == "élevé"]
    declenche = len(eleves) == 1
    return MatchResult(pattern=pattern, declenche=declenche, confiance_ajustee=pattern.niveau_confiance)


def _glob005(pattern: Pattern, ctx: dict) -> MatchResult:
    # Seul GLOB restant à dépendre directement du contexte (donnée de
    # tendance) plutôt que du seul résultat de l'étage 1 — traité comme
    # un pattern ordinaire à conditions ratio/verdict.
    return evaluate_pattern(pattern, ctx)


def evaluate_stage2(patterns: list[Pattern], stage1_results: list[MatchResult], ctx: dict) -> list[MatchResult]:
    """GLOB.001-005 : méta-conditions sur le résultat de l'étage 1 (comptage par risque/catégorie)."""
    fired = [r for r in stage1_results if r.declenche]
    by_id = {p.id: p for p in patterns if p.id.startswith("GLOB.")}

    results = []
    if "GLOB.001" in by_id:
        results.append(_glob001(by_id["GLOB.001"], fired))
    if "GLOB.002" in by_id:
        results.append(_glob002(by_id["GLOB.002"], fired))
    if "GLOB.003" in by_id:
        results.append(_glob003(by_id["GLOB.003"], fired))
    if "GLOB.004" in by_id:
        results.append(_glob004(by_id["GLOB.004"], fired))
    if "GLOB.005" in by_id:
        results.append(_glob005(by_id["GLOB.005"], ctx))
    return results


def evaluate_all_patterns(patterns: list[Pattern], ctx: dict) -> list[MatchResult]:
    """Point d'entrée unique : étage 1 puis étage 2, résultat combiné."""
    stage1 = evaluate_stage1(patterns, ctx)
    stage2 = evaluate_stage2(patterns, stage1, ctx)
    return stage1 + stage2
