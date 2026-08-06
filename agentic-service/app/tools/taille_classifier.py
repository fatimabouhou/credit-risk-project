"""
Classe automatiquement la taille d'une entreprise (TPE/PME/GE) a partir de
son chiffre d'affaires et de son total actif, selon la regle de
00_segmentation_reference.md section 3 - evite d'attendre une saisie
manuelle (voir tools/benchmark_tool.py) quand ces deux chiffres sont deja
connus via financial-service (donnees_brutes_applaties, exclu du payload
allege envoye au LLM mais accessible cote Python).

Comme ratio_table_parser.py, les seuils ne sont pas dupliques en dur ici :
la table est retrouvee et parsee en direct depuis le texte RAG a chaque
appel (fiche = unique source de verite). Seule la FORME de la table
(colonnes Code, Taille, CA, Total actif) est connue de ce module.
"""

import re

from tools.rag_tool import rag_search
from tools.ratio_table_parser import _find_table

SEGMENTATION_TAG = "RATIO_BENCHMARK_TAG: segmentation.taille"

_AMOUNT = r"\d[\d\s]*(?:[.,]\d+)?"
_RANGE_RE = re.compile(rf"({_AMOUNT})\s*à\s*({_AMOUNT})")
_LT_RE = re.compile(rf"<\s*({_AMOUNT})")
_GT_RE = re.compile(rf">\s*({_AMOUNT})")


def _to_float(text: str) -> float:
    digits_only = re.sub(r"\s", "", text.strip())
    return float(digits_only.replace(",", "."))


def _parse_amount_range(cell: str) -> tuple[float, float | None] | None:
    """"< 10 000 000 MAD" -> (0, 10000000) ; "10 000 000 a 175 000 000 MAD" -> (10000000, 175000000)."""
    m = _RANGE_RE.search(cell)
    if m:
        return _to_float(m.group(1)), _to_float(m.group(2))
    m = _LT_RE.search(cell)
    if m:
        return 0.0, _to_float(m.group(1))
    m = _GT_RE.search(cell)
    if m:
        return _to_float(m.group(1)), None
    return None


def _bucket_containing(rows: list[list[str]], cell_index: int, value: float) -> str | None:
    for row in rows:
        if cell_index >= len(row):
            continue
        bounds = _parse_amount_range(row[cell_index])
        if bounds is None:
            continue
        lo, hi = bounds
        if lo <= value and (hi is None or value <= hi):
            return row[0].strip()
    return None


def classify_taille_code(chiffre_affaires: float, total_actif: float | None = None) -> dict:
    """
    Retourne {"taille_code": "TPE"|"PME"|"GE"|None, "ecart": str|None}.

    Le CA est le critere prioritaire (regle documentee dans la fiche) :
    si le total actif pointe vers une taille differente, ce n'est pas
    corrige mais signale dans "ecart" - un ecart peut lui-meme etre un
    signal utile (ex. fonciere/holding, actif tres superieur au CA).
    """
    matches = rag_search(
        "Table de classification de la taille d'entreprise par chiffre d'affaires et total actif",
        top_k=1,
        contains=SEGMENTATION_TAG,
    )
    if not matches:
        return {"taille_code": None, "ecart": None}

    parsed = _find_table(matches[0]["text"])
    if parsed is None:
        return {"taille_code": None, "ecart": None}
    _headers, rows = parsed

    # Colonnes de la table : Code | Taille | Chiffre d'affaires annuel | Total actif | Effectif
    ca_code = _bucket_containing(rows, 2, chiffre_affaires)
    if ca_code is None:
        return {"taille_code": None, "ecart": None}

    ecart = None
    if total_actif is not None:
        actif_code = _bucket_containing(rows, 3, total_actif)
        if actif_code and actif_code != ca_code:
            ecart = (
                f"le total actif ({total_actif:,.0f} MAD) pointerait vers {actif_code} alors "
                f"que le chiffre d'affaires ({chiffre_affaires:,.0f} MAD) pointe vers {ca_code} "
                "- taille retenue selon le CA (critere prioritaire), ecart a noter"
            )

    return {"taille_code": ca_code, "ecart": ecart}


if __name__ == "__main__":
    import json
    import sys

    sys.stdout.reconfigure(encoding="utf-8")

    ca = float(sys.argv[1]) if len(sys.argv) > 1 else 55555047.91
    actif = float(sys.argv[2]) if len(sys.argv) > 2 else None
    print(json.dumps(classify_taille_code(ca, actif), ensure_ascii=False, indent=2))
