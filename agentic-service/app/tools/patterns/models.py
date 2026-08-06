"""
Structures de données pour la base de connaissances des patterns
(data/patterns/) — combinaisons de plusieurs ratios pour déduire des
relations, en complément des verdicts unitaires de benchmark_tool.py.
"""

from dataclasses import dataclass, field


@dataclass
class Condition:
    """
    Une condition élémentaire d'un pattern, ex. "Current Ratio :
    dans_la_norme" ou "DSO ou DIO : au_dessus_norme".

    `ratios` : un ou plusieurs noms de ratios AFFICHÉS (ex. "Current
    Ratio"), séparés par " ou " dans le Markdown — la condition est
    satisfaite si AU MOINS UN de ces ratios correspond.
    `verdicts` : un ou plusieurs verdicts acceptés, séparés par " ou ".
    `raw_text` : le texte brut de la condition, conservé pour les cas non
    évaluables (méta-conditions qualitatives, ex. "Constat observé sur
    plusieurs exercices consécutifs") — voir vocabulary.py pour la
    détection de ces cas.
    """

    ratios: list[str]
    verdicts: list[str]
    raw_text: str


@dataclass
class Pattern:
    id: str
    titre: str
    categorie: str
    objectif: str
    required: list[Condition]
    optional: list[Condition]
    niveau_confiance: str
    diagnostic: str
    hypotheses: list[str]
    actions: list[str]
    niveau_risque: str
    priorite: str
    references: list[str]
    source_file: str


@dataclass
class MatchResult:
    """Résultat de l'évaluation d'un pattern contre les données d'un client."""

    pattern: Pattern
    declenche: bool
    required_satisfaites: list[Condition] = field(default_factory=list)
    required_manquantes: list[Condition] = field(default_factory=list)
    optional_satisfaites: list[Condition] = field(default_factory=list)
    confiance_ajustee: str = ""
    indisponible_pour_donnees_manquantes: bool = False
    raison_indisponibilite: str | None = None
