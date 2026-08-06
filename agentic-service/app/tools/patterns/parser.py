"""
Parseur des fichiers Markdown de data/patterns/ (base de connaissances
de patterns combinant plusieurs ratios) vers des objets Pattern.

Format attendu par section (délimitée par "## ID — Titre" ... "---") :
    **Catégorie :** ...
    **Objectif :** ...
    **Conditions obligatoires (required) :**
    - Ratio : verdict[ ou verdict2]
    **Conditions renforçant la confiance (optional) :**
    - ...
    **Niveau de confiance :** ...
    **Diagnostic :**
    paragraphe
    **Hypothèses possibles :**
    - ...
    **Actions d'investigation :**
    - ...
    **Niveau de risque :** ...
    **Priorité :** ...
    **Références :** ...

Extraction générique (pas un regex par champ) : on repère tous les
marqueurs "**Label :**" et on découpe le texte entre marqueurs
consécutifs, pour rester robuste à l'ordre exact des champs plutôt que
de le supposer figé.
"""

import re
from pathlib import Path

from tools.patterns.models import Condition, Pattern

_HEADER_RE = re.compile(r"^##\s+(\S+)\s+—\s+(.+?)\s*$", re.MULTILINE)
_FIELD_MARKER_RE = re.compile(r"\*\*([^*]+?)\s*:\*\*[ \t]*(.*)")


def _split_field_blocks(body: str) -> dict[str, str]:
    """
    Repère chaque marqueur "**Label :**" dans `body` et associe à chaque
    label tout le texte jusqu'au marqueur suivant (ou la fin du bloc).
    Le texte inline après le marqueur (même ligne) est inclus.
    """
    matches = list(_FIELD_MARKER_RE.finditer(body))
    fields: dict[str, str] = {}
    for i, m in enumerate(matches):
        label = m.group(1).strip()
        inline = m.group(2).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        block = body[start:end].strip()
        content = (inline + "\n" + block).strip() if inline else block
        fields[label] = content
    return fields


def _parse_bullet_list(text: str) -> list[str]:
    items = [line.strip().lstrip("-").strip() for line in text.splitlines() if line.strip().startswith("-")]
    if len(items) == 1 and items[0].lower() in ("aucune", "aucun"):
        return []
    return items


def _parse_condition_line(line: str) -> Condition | None:
    """
    "Current Ratio : dans_la_norme" -> Condition(["Current Ratio"], ["dans_la_norme"], ...)
    "Quick Ratio : dans_la_norme ou au_dessus_norme" -> 2 verdicts acceptés.
    "DSO ou DIO : au_dessus_norme" -> 2 ratios acceptés (l'un ou l'autre).
    Une ligne sans " : " n'est pas une condition ratio/verdict mais une
    méta-condition qualitative (ex. "Constat observé sur plusieurs
    exercices consécutifs") — conservée telle quelle, ratios/verdicts vides.
    """
    line = line.strip()
    if not line:
        return None
    if " : " not in line:
        return Condition(ratios=[], verdicts=[], raw_text=line)

    left, right = line.split(" : ", 1)
    # Une parenthèse de renvoi ("voir 04_activite_patterns.md") ne fait pas
    # partie du verdict : on la retire du côté droit avant de découper sur " ou ".
    right = re.sub(r"\s*\([^)]*\)\s*$", "", right).strip()
    ratios = [r.strip() for r in left.split(" ou ")]
    verdicts = [v.strip() for v in right.split(" ou ")]
    return Condition(ratios=ratios, verdicts=verdicts, raw_text=line)


def _parse_conditions(text: str) -> list[Condition]:
    conditions = []
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("-"):
            continue
        line = line.lstrip("-").strip()
        if line.lower() in ("aucune", "aucun"):
            continue
        cond = _parse_condition_line(line)
        if cond:
            conditions.append(cond)
    return conditions


def _parse_pattern_block(header_id: str, header_titre: str, body: str, source_file: str) -> Pattern:
    fields = _split_field_blocks(body)
    return Pattern(
        id=header_id,
        titre=header_titre,
        categorie=fields.get("Catégorie", ""),
        objectif=fields.get("Objectif", ""),
        required=_parse_conditions(fields.get("Conditions obligatoires (required)", "")),
        optional=_parse_conditions(fields.get("Conditions renforçant la confiance (optional)", "")),
        niveau_confiance=fields.get("Niveau de confiance", ""),
        diagnostic=fields.get("Diagnostic", ""),
        hypotheses=_parse_bullet_list(fields.get("Hypothèses possibles", "")),
        actions=_parse_bullet_list(fields.get("Actions d'investigation", "")),
        niveau_risque=fields.get("Niveau de risque", ""),
        priorite=fields.get("Priorité", ""),
        references=[r.strip() for r in fields.get("Références", "").split(",") if r.strip()],
        source_file=source_file,
    )


def parse_pattern_file(path: Path) -> list[Pattern]:
    text = path.read_text(encoding="utf-8")
    headers = list(_HEADER_RE.finditer(text))
    patterns = []
    for i, header in enumerate(headers):
        pattern_id = header.group(1)
        titre = header.group(2)
        start = header.end()
        end = headers[i + 1].start() if i + 1 < len(headers) else len(text)
        body = text[start:end]
        body = re.sub(r"\n-{3,}\s*$", "", body)  # sépare le "---" de fin de bloc
        patterns.append(_parse_pattern_block(pattern_id, titre, body, path.name))
    return patterns


def parse_pattern_directory(directory: Path) -> list[Pattern]:
    patterns = []
    for path in sorted(directory.glob("*.md")):
        if path.name.startswith("00_"):
            continue  # note méthodologique, pas des patterns
        patterns.extend(parse_pattern_file(path))
    return patterns


if __name__ == "__main__":
    import sys

    sys.stdout.reconfigure(encoding="utf-8")

    directory = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/patterns")
    all_patterns = parse_pattern_directory(directory)
    print(f"{len(all_patterns)} patterns parsés depuis {directory}\n")
    for p in all_patterns:
        req = "; ".join(c.raw_text for c in p.required)
        print(f"[{p.id}] {p.titre}")
        print(f"  required: {req}")
    print(f"\nTotal : {len(all_patterns)}")
