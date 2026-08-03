"""
PHASE 1 — Extraction + Nettoyage

Rôle de ce module :
    Lire un fichier .md source, en extraire les métadonnées de tête
    (titre, note "Nature de ce document"), et produire un texte Markdown
    nettoyé, prêt à être découpé en chunks (phase 2).

Ce module ne fait PAS de chunking et ne fait PAS d'embedding.
Il ne fait que lire + nettoyer + structurer minimalement.
"""

import re
from pathlib import Path

from ingestion.models import RawDocument


# --- Regex compilées une seule fois (perf + lisibilité) ---

TITLE_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)
NATURE_RE = re.compile(
    r"> \*\*Nature de ce document\.\*\*\s*(.*?)(?=\n\n)",
    re.DOTALL,
)
SIMULE_RE = re.compile(r"\[SIMUL[ÉE]\]")

# Lignes qu'on ne veut jamais garder dans le texte "propre" utilisé pour le chunking :
# séparateurs horizontaux Markdown ("---") isolés, espaces multiples inutiles.
HR_LINE_RE = re.compile(r"^-{3,}\s*$", re.MULTILINE)
MULTI_BLANK_LINES_RE = re.compile(r"\n{3,}")
TRAILING_SPACES_RE = re.compile(r"[ \t]+$", re.MULTILINE)


def extract_title(text: str) -> str:
    """Retourne le premier titre '# ...' du document, ou une chaîne vide si absent."""
    match = TITLE_RE.search(text)
    return match.group(1).strip() if match else ""


def extract_nature(text: str) -> str | None:
    """
    Retourne le contenu de la note '> **Nature de ce document.** ...'
    (le blockquote explicatif en tête de chaque fiche). None si absent.
    """
    match = NATURE_RE.search(text)
    if not match:
        return None
    # Le blockquote Markdown préfixe chaque ligne par "> " -> on l'enlève.
    raw = match.group(1)
    lines = [line.lstrip("> ").strip() for line in raw.splitlines()]
    return " ".join(line for line in lines if line)


def detect_simulated(text: str) -> bool:
    """True si le document contient au moins une mention '[SIMULÉ]' ou '[SIMULE]'."""
    return bool(SIMULE_RE.search(text))


def clean_text(text: str) -> str:
    """
    Nettoyage conservateur du Markdown :
    - supprime les lignes de séparation horizontale isolées ("---")
    - supprime les espaces/tabs en fin de ligne
    - réduit les suites de 3+ lignes vides à une seule ligne vide
    - trim début/fin de document

    Important : on NE touche PAS à la structure des titres (#, ##) ni aux
    tableaux Markdown (| ... |) -> ils sont indispensables aux phases 2 et 3.
    """
    text = HR_LINE_RE.sub("", text)
    text = TRAILING_SPACES_RE.sub("", text)
    text = MULTI_BLANK_LINES_RE.sub("\n\n", text)
    return text.strip()


def parse_file(path: Path) -> RawDocument:
    """
    Extrait + nettoie un seul fichier .md et retourne un RawDocument prêt
    pour la phase 2 (chunking).
    """
    raw = path.read_text(encoding="utf-8")

    return RawDocument(
        source_file=path.name,
        title=extract_title(raw),
        nature=extract_nature(raw),
        is_simulated=detect_simulated(raw),
        clean_text=clean_text(raw),
    )


def parse_directory(docs_dir: Path, pattern: str = "*.md") -> list[RawDocument]:
    """
    Parse tous les fichiers .md d'un dossier (ex: data/docs/).
    Retourne la liste des RawDocument, triée par nom de fichier pour un ordre stable.
    """
    files = sorted(docs_dir.glob(pattern))
    if not files:
        raise FileNotFoundError(f"Aucun fichier '{pattern}' trouvé dans {docs_dir}")
    return [parse_file(f) for f in files]


if __name__ == "__main__":
    # Test manuel rapide : exécuter `python -m ingestion.parser` depuis app/
    # pour valider la phase 1 sur les fichiers réels avant de passer à la phase 2.
    import sys

    sys.stdout.reconfigure(encoding="utf-8")

    docs_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/docs")
    documents = parse_directory(docs_path)

    for doc in documents:
        print(f"--- {doc.source_file} ---")
        print(f"Titre       : {doc.title}")
        print(f"Nature      : {doc.nature[:100] if doc.nature else None}...")
        print(f"Simulé      : {doc.is_simulated}")
        print(f"Char count  : {doc.char_count}")
        print()