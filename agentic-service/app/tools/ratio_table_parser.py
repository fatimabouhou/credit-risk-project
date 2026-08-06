"""
Extraction déterministe des bornes numériques (min/max) depuis les tables
Markdown des fiches de normes RAG, pour calculer un verdict exact côté
Python plutôt que de laisser le LLM comparer deux nombres lui-même.

Pourquoi : le LLM (llama-3.3-70b via Groq, temperature=0) confondait de
façon intermittente "Moyenne" avec la borne basse de la fourchette (ex.
debt_to_equity=1,09 comparé à [Min=0,40, Moyenne=0,90] au lieu de
[Min=0,40, Max acceptable=1,50], fausse anomalie) — un problème
d'interprétation du texte RAG, pas de récupération (le hybrid search de
benchmark_tool.py retrouve déjà la bonne table à chaque fois).

Important : ce module ne duplique AUCUNE valeur numérique. Il parse, à
chaque appel, le texte déjà récupéré du RAG (les fiches Markdown restent
l'unique source de vérité) — si une fiche change, le verdict suit sans
rien à resynchroniser ailleurs. Ce qui est codé en dur ici, c'est
uniquement la FORME de chaque table (quelles colonnes existent et leur
rôle), jamais ses valeurs.

Portée : la seule fiche encore non couverte est `working_capital_frf`
(montant absolu en MAD, pas un ratio — un seuil chiffré y serait
mathématiquement faux puisqu'il dépend de la taille exacte de
l'entreprise ; le signal existe déjà, normalisé, sous
net_current_liabilities_to_assets). Pour ce cas-là uniquement,
parse_verdict() renvoie None et l'agent est instruit (voir planner.py) à
se reporter à ce ratio jumeau plutôt qu'à interpréter un montant brut.
"""

import re

RATIO_TABLE_SHAPES = {
    "liquidite.quick_ratio": {"shape": "band"},
    "liquidite.current_ratio": {"shape": "band"},
    "rentabilite.marge_operationnelle": {"shape": "band"},
    "rentabilite.roa_return_on_assets": {"shape": "band"},
    "rentabilite.roe_return_on_equity": {"shape": "band"},
    "rentabilite.marge_nette": {"shape": "band"},
    "rentabilite.ebitda_margin": {"shape": "band"},
    "activite.asset_turnover": {"shape": "band"},
    "solvabilite.debt_to_equity_leverage": {"shape": "band_ceiling_alert"},
    "solvabilite.liabilities_to_assets": {"shape": "band_ceiling_alert"},
    "solvabilite.autonomie_financiere": {"shape": "floor_alert"},
    "activite.dso_days": {"shape": "range_cell", "cell_index": 1},
    "activite.dpo_days": {"shape": "range_cell", "cell_index": 2},
    "activite.dio_days": {"shape": "range_cell", "cell_index": 3},
    # Tables à zones qualitatives universelles (pas de segmentation
    # secteur/taille : le seuil est le même pour tout le monde).
    "liquidite.cash_ratio": {
        "shape": "zone_table",
        "ratio_col": None,
        "range_col": 1,
        "zone_labels": ["seuil_alerte_bas", "zone_confortable", "zone_a_interroger_haut"],
    },
    "solvabilite.net_current_liabilities_to_assets": {
        "shape": "zone_table",
        "ratio_col": 0,
        "range_col": 1,
        "zone_labels": ["favorable", "neutre", "besoin_significatif"],
    },
    "solvabilite.retained_earnings_to_current_liabilities": {
        "shape": "zone_table",
        "ratio_col": 0,
        "range_col": 1,
        "zone_labels": ["coussin_faible", "niveau_courant", "coussin_confortable"],
    },
}

# Ratios dont la table de zones n'est pas segmentée par secteur/taille —
# parse_verdict() ne doit pas exiger de segment_code pour ceux-là.
_UNSEGMENTED_SHAPES = {"zone_table"}

_NUMBER_RE = re.compile(r"[<>]?\s*(-?\d+(?:[.,]\d+)?)\s*(%)?")
_RANGE_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*à\s*(\d+(?:[.,]\d+)?)")
_LT_RE = re.compile(r"<\s*(\d+(?:[.,]\d+)?)")
_GT_RE = re.compile(r">\s*(\d+(?:[.,]\d+)?)")


def _parse_number(text: str) -> float | None:
    """"0,60" -> 0.60 ; "5%" -> 0.05 ; "> 2,00" -> 2.0 (le signe est ignoré, l'appelant gère le sens)."""
    match = _NUMBER_RE.search(text.strip())
    if not match:
        return None
    value = float(match.group(1).replace(",", "."))
    if match.group(2):
        value /= 100
    return value


def _parse_range_cell(cell: str) -> tuple[float, float | None] | None:
    m = _RANGE_RE.search(cell)
    if m:
        return float(m.group(1).replace(",", ".")), float(m.group(2).replace(",", "."))
    m = _LT_RE.search(cell)
    if m:
        return 0.0, float(m.group(1).replace(",", "."))
    m = _GT_RE.search(cell)
    if m:
        return float(m.group(1).replace(",", ".")), None
    return None


def _split_row(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


_SEPARATOR_ROW_RE = re.compile(r"^[\s|:\-]+$")


def _find_table(table_text: str) -> tuple[list[str], list[list[str]]] | None:
    """
    Retourne (headers, [rows...]) pour le premier tableau Markdown pipe
    trouvé, ou None.

    Le parser d'ingestion (ingestion/parser.py) retire la ligne de
    séparation Markdown ("|---|---|...") avant chunking : le texte
    stocké dans Chroma enchaîne directement l'en-tête puis les lignes de
    données, sans séparateur. On la retire ici seulement si elle est
    malgré tout présente (robustesse), jamais en supposant sa position.
    """
    lines = [line for line in table_text.splitlines() if line.strip().startswith("|")]
    if len(lines) < 2:
        return None
    headers = _split_row(lines[0])
    data_lines = lines[1:]
    if data_lines and _SEPARATOR_ROW_RE.match(data_lines[0]):
        data_lines = data_lines[1:]
    rows = [_split_row(line) for line in data_lines if line.strip()]
    return headers, rows


def _find_segment_row(rows: list[list[str]], segment_code: str) -> list[str] | None:
    code = segment_code.strip().upper()
    for row in rows:
        if not row:
            continue
        label = row[0].strip().upper()
        if label == code or f"({code})" in label:
            return row
    return None


def _col_index(headers: list[str], *keywords: str) -> int | None:
    for i, header in enumerate(headers):
        header_low = header.lower()
        if all(k.lower() in header_low for k in keywords):
            return i
    return None


_ZONE_NUMBER = r"-?\d+(?:[.,]\d+)?%?"
_ZONE_RANGE_RE = re.compile(rf"({_ZONE_NUMBER})\s*à\s*({_ZONE_NUMBER})")
_ZONE_LT_RE = re.compile(rf"<\s*({_ZONE_NUMBER})")
_ZONE_GT_RE = re.compile(rf">\s*({_ZONE_NUMBER})")


def _parse_zone_bounds(cell: str) -> tuple[float | None, float | None] | None:
    """
    Comme _parse_range_cell, mais pour les tables de zones qualitatives
    (cash_ratio, net_current_liabilities_to_assets, retained_earnings_
    to_current_liabilities) : ces ratios peuvent être négatifs (ex.
    "< 0" pour net_current_liabilities_to_assets), donc le plancher
    implicite d'un "< X" est -infini ici (None), pas 0 comme pour les
    fourchettes de délais en jours où une valeur négative n'a pas de sens.
    """
    m = _ZONE_RANGE_RE.search(cell)
    if m:
        return _parse_number(m.group(1)), _parse_number(m.group(2))
    m = _ZONE_LT_RE.search(cell)
    if m:
        return None, _parse_number(m.group(1))
    m = _ZONE_GT_RE.search(cell)
    if m:
        return _parse_number(m.group(1)), None
    return None


def _parse_zone_table(
    ratio_name: str,
    ratio_value: float,
    rows: list[list[str]],
    ratio_col: int | None,
    range_col: int,
    zone_labels: list[str],
) -> dict | None:
    if ratio_col is not None:
        bare_name = ratio_name.rsplit(".", 1)[-1]
        rows = [r for r in rows if ratio_col < len(r) and r[ratio_col].strip() == bare_name]

    for label, row in zip(zone_labels, rows):
        if range_col >= len(row):
            continue
        bounds = _parse_zone_bounds(row[range_col])
        if bounds is None:
            continue
        lo, hi = bounds
        if (lo is None or ratio_value >= lo) and (hi is None or ratio_value <= hi):
            return {"min": lo, "max": hi, "seuil_alerte": None, "zone_confortable": None, "verdict": label}

    return {
        "min": None,
        "max": None,
        "seuil_alerte": None,
        "zone_confortable": None,
        "verdict": "zone_intermediaire_non_definie",
    }


def parse_verdict(
    ratio_name: str, ratio_value: float, table_text: str, segment_code: str | None
) -> dict | None:
    """
    Calcule un verdict exact pour `ratio_name` à partir du texte brut
    déjà récupéré du RAG (`table_text`). Retourne None si ce ratio n'est
    pas couvert (voir RATIO_TABLE_SHAPES) ou si le texte n'a pas pu être
    parsé avec confiance — un None plutôt qu'un résultat incertain.
    `segment_code` (secteur ou taille) est requis pour les tables
    segmentées, pas pour les tables de zones universelles (cash_ratio...
    voir _UNSEGMENTED_SHAPES).
    """
    shape_info = RATIO_TABLE_SHAPES.get(ratio_name)
    if shape_info is None:
        return None
    shape = shape_info["shape"]
    if shape not in _UNSEGMENTED_SHAPES and not segment_code:
        return None

    parsed = _find_table(table_text)
    if parsed is None:
        return None
    headers, rows = parsed

    if shape == "zone_table":
        return _parse_zone_table(
            ratio_name,
            ratio_value,
            rows,
            shape_info["ratio_col"],
            shape_info["range_col"],
            shape_info["zone_labels"],
        )

    row = _find_segment_row(rows, segment_code)
    if row is None:
        return None

    if shape == "range_cell":
        cell_index = shape_info["cell_index"]
        if cell_index >= len(row):
            return None
        bounds = _parse_range_cell(row[cell_index])
        if bounds is None:
            return None
        return _build_verdict(ratio_value, bounds[0], bounds[1])

    if shape == "band":
        min_i = _col_index(headers, "min")
        max_i = _col_index(headers, "max")
        if min_i is None or max_i is None or min_i >= len(row) or max_i >= len(row):
            return None
        min_b = _parse_number(row[min_i])
        max_b = _parse_number(row[max_i])
        if min_b is None or max_b is None:
            return None
        return _build_verdict(ratio_value, min_b, max_b)

    if shape == "band_ceiling_alert":
        min_i = _col_index(headers, "min")
        max_i = _col_index(headers, "max")
        alert_i = _col_index(headers, "seuil", "alerte")
        if min_i is None or max_i is None or min_i >= len(row) or max_i >= len(row):
            return None
        min_b = _parse_number(row[min_i])
        max_b = _parse_number(row[max_i])
        if min_b is None or max_b is None:
            return None
        alert_b = _parse_number(row[alert_i]) if alert_i is not None and alert_i < len(row) else None
        return _build_verdict(ratio_value, min_b, max_b, seuil_alerte=alert_b, seuil_type="plafond")

    if shape == "floor_alert":
        min_i = _col_index(headers, "min")
        alert_i = _col_index(headers, "seuil", "alerte")
        comfort_i = _col_index(headers, "zone", "confortable")
        if min_i is None or min_i >= len(row):
            return None
        min_b = _parse_number(row[min_i])
        if min_b is None:
            return None
        alert_b = _parse_number(row[alert_i]) if alert_i is not None and alert_i < len(row) else None
        comfort_b = (
            _parse_number(row[comfort_i]) if comfort_i is not None and comfort_i < len(row) else None
        )
        return _build_verdict(
            ratio_value,
            min_b,
            None,
            seuil_alerte=alert_b,
            seuil_type="plancher",
            zone_confortable=comfort_b,
        )

    return None


def _build_verdict(
    value: float,
    min_b: float | None,
    max_b: float | None,
    seuil_alerte: float | None = None,
    seuil_type: str | None = None,
    zone_confortable: float | None = None,
) -> dict:
    if seuil_type == "plancher":
        if seuil_alerte is not None and value < seuil_alerte:
            verdict = "en_dessous_seuil_alerte"
        elif min_b is not None and value < min_b:
            verdict = "en_dessous_norme"
        elif zone_confortable is not None and value >= zone_confortable:
            verdict = "zone_confortable"
        else:
            verdict = "dans_la_norme"
    else:
        if seuil_type == "plafond" and seuil_alerte is not None and value > seuil_alerte:
            verdict = "au_dela_seuil_alerte"
        elif max_b is not None and value > max_b:
            verdict = "au_dessus_norme"
        elif min_b is not None and value < min_b:
            verdict = "en_dessous_norme"
        else:
            verdict = "dans_la_norme"

    return {
        "min": min_b,
        "max": max_b,
        "seuil_alerte": seuil_alerte,
        "zone_confortable": zone_confortable,
        "verdict": verdict,
    }
