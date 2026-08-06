"""
Pre-classification deterministe du secteur pour les cas non ambigus
(prefixes "Commerce/Negoce/Distribution/Import-export de X"), deja
documentes en langage naturel dans graph/planner.py mais pas toujours
appliques de facon fiable par le LLM (ex. "Commerce de materiaux de
construction" parfois classe a tort en BTP a cause du mot
"construction", malgre l'exemple explicite dans le prompt).

Ne couvre QUE ce cas non ambigu : la regle est purement lexicale
("achete et revend X" = commerce, quel que soit X) et ne depend d'aucune
valeur chiffree. Les distinctions plus fines (BTP vs vente de materiaux,
IND vs SRV, etc.) restent laissees au LLM + RAG : une vraie tache de
classification semantique qu'une regex ne peut pas couvrir correctement
sans devenir aussi peu fiable que ce qu'elle remplace.
"""

import re

_COMMERCE_PREFIX_RE = re.compile(
    r"^\s*(commerce|n[eé]goce|distribution|import[\s-]?export|vente en gros|grossiste)\s+(de|d'|en)\b",
    re.IGNORECASE,
)


def try_classify_secteur(secteur_libre: str | None) -> str | None:
    """
    Retourne "COM" si `secteur_libre` correspond sans ambiguïté à un
    schéma "Commerce/Négoce/Distribution/Import-export de X" (achète et
    revend X) — sinon None, laissant la classification au LLM (cas plus
    nuancés, ex. BTP vs vente de matériaux de construction).
    """
    if not secteur_libre:
        return None
    if _COMMERCE_PREFIX_RE.match(secteur_libre.strip()):
        return "COM"
    return None
