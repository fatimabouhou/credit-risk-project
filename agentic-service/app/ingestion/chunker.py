"""
PHASE 2 — Chunking (version token-aware)

Rôle de ce module :
    Découper un RawDocument (issu de la phase 1 / parser.py) en chunks
    exploitables par la phase 3 (embedding), en mesurant la taille de
    chaque chunk en VRAIS TOKENS du modèle d'embedding utilisé
    (BAAI/bge-m3), pas en caractères.

    Pourquoi les tokens et pas les caractères :
    - C'est le nombre de tokens qui détermine si un chunk dépasse la
      limite d'entrée du modèle d'embedding, pas le nombre de caractères.
    - Le ratio caractères/tokens varie selon la langue, les accents, les
      symboles (%, |, chiffres) — un comptage par caractères est donc un
      proxy imprécis qui peut soit tronquer silencieusement un chunk trop
      long, soit sous-découper inutilement un chunk en réalité correct.

    Stratégie de découpage (cascade, structure-aware) :
    1. Une section de niveau 2 ("## Titre") = un chunk de base.
    2. Si une section dépasse MAX_TOKENS : re-découpage en blocs atomiques
       (un tableau Markdown = un bloc jamais coupé ; un paragraphe = un
       bloc re-découpable).
    3. Si un paragraphe dépasse encore MAX_TOKENS : re-découpage par
       phrase, puis par mot en dernier recours.
    4. Les sections trop courtes (< MIN_TOKENS) sont fusionnées avec la
       suivante.

Ce module ne fait PAS d'embedding (voir embedder.py, phase 3) — il importe
seulement le tokenizer du modèle pour COMPTER les tokens, sans charger le
modèle d'embedding lui-même (plus léger, plus rapide).
"""

import re
from pathlib import Path

from transformers import AutoTokenizer

from ingestion.models import RawDocument, Chunk

# --- Modèle d'embedding cible ---
# BAAI/bge-m3 : gratuit, open-source, multilingue (bon en français),
# fenêtre de contexte de 8192 tokens. Voir embedder.py pour le chargement
# du modèle complet ; ici on ne charge que le tokenizer (léger).
EMBEDDING_MODEL_NAME = "BAAI/bge-m3"

_tokenizer = None


def get_tokenizer():
    """Charge le tokenizer une seule fois (lazy loading, mis en cache)."""
    global _tokenizer
    if _tokenizer is None:
        _tokenizer = AutoTokenizer.from_pretrained(EMBEDDING_MODEL_NAME)
    return _tokenizer


def count_tokens(text: str) -> int:
    """Nombre réel de tokens que produirait le modèle d'embedding pour ce texte."""
    tok = get_tokenizer()
    return len(tok.encode(text, add_special_tokens=False))


SECTION_RE = re.compile(r"^##\s+(.+)$", re.MULTILINE)
SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")

# Bruit syntaxique Markdown sans valeur sémantique : la ligne de séparation
# d'un tableau ("|---|---|---|", éventuellement avec ":" pour l'alignement)
# et les marqueurs **gras** / `code` — le texte qu'ils encadrent est gardé,
# seuls les caractères de balisage disparaissent.
TABLE_SEPARATOR_RE = re.compile(r"^\|(?:\s*:?-{2,}:?\s*\|)+[ \t]*\n?", re.MULTILINE)
BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
INLINE_CODE_RE = re.compile(r"`([^`\n]+)`")

# MAX_TOKENS reste volontairement bien en dessous de la limite du modèle
# (8192) : un chunk plus petit et focalisé donne de meilleurs embeddings
# pour la recherche par similarité qu'un chunk proche de la limite max.
MAX_TOKENS = 480
MIN_TOKENS = 40


def clean_for_embedding(text: str) -> str:
    """
    Retire le bruit Markdown purement décoratif avant tout comptage de
    tokens / découpage — pour que token_count, char_count et le texte
    finalement embeddé correspondent tous à la même version "propre" :
    - la ligne de séparation des tableaux ("|---|---|---|") : jamais du
      contenu, juste de la mise en page ;
    - les marqueurs **gras** et `code` : le texte encadré reste, seul le
      balisage disparaît.
    Ne touche ni aux titres (#, ##) ni aux lignes de données des tableaux
    (toujours des blocs "|...|", donc toujours détectées comme atomiques
    par _iter_atomic_blocks).
    """
    text = TABLE_SEPARATOR_RE.sub("", text)
    text = BOLD_RE.sub(r"\1", text)
    text = INLINE_CODE_RE.sub(r"\1", text)
    return text


def split_into_sections(clean_text: str) -> list[tuple[str, str]]:
    """
    Découpe le texte nettoyé en sections de niveau 2 (## Titre).
    Retourne une liste de (titre_section, contenu_section).
    """
    matches = list(SECTION_RE.finditer(clean_text))
    if not matches:
        return [("Introduction", clean_text.strip())]

    sections = []
    intro = clean_text[: matches[0].start()].strip()
    if intro:
        sections.append(("Introduction", intro))

    for i, m in enumerate(matches):
        title = m.group(1).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(clean_text)
        content = clean_text[start:end].strip()
        sections.append((title, content))

    return sections


def _is_table_line(line: str) -> bool:
    return line.strip().startswith("|")


def _iter_atomic_blocks(content: str) -> list[tuple[str, str]]:
    """
    Découpe un contenu en blocs atomiques :
    - un tableau Markdown (lignes "|...|" consécutives) = un bloc de type "table"
    - un paragraphe (séparé par une ligne vide) = un bloc de type "text"

    Un bloc "table" ne sera jamais redécoupé plus loin.
    Un bloc "text" pourra l'être si besoin (par phrase, puis par mot).
    """
    lines = content.split("\n")
    blocks: list[tuple[str, str]] = []
    current: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]

        if _is_table_line(line):
            if current:
                blocks.append(("text", "\n".join(current).strip()))
                current = []
            table_lines = []
            while i < len(lines) and _is_table_line(lines[i]):
                table_lines.append(lines[i])
                i += 1
            blocks.append(("table", "\n".join(table_lines)))
            continue

        if line.strip() == "":
            if current:
                blocks.append(("text", "\n".join(current).strip()))
                current = []
            i += 1
            continue

        current.append(line)
        i += 1

    if current:
        blocks.append(("text", "\n".join(current).strip()))

    return [b for b in blocks if b[1]]


def _split_by_words(text: str, max_tokens: int) -> list[str]:
    """Dernier recours : redécoupe un texte mot par mot pour respecter max_tokens."""
    words = text.split(" ")
    out: list[str] = []
    current: list[str] = []
    for w in words:
        candidate = " ".join(current + [w])
        if not current or count_tokens(candidate) <= max_tokens:
            current.append(w)
        else:
            out.append(" ".join(current))
            current = [w]
    if current:
        out.append(" ".join(current))
    return out


def _split_text_block(text: str, max_tokens: int) -> list[str]:
    """
    Redécoupe un bloc de texte (non-tableau) trop long :
    d'abord par phrase, puis par mot si une phrase seule dépasse encore.
    """
    if count_tokens(text) <= max_tokens:
        return [text]

    sentences = SENTENCE_SPLIT_RE.split(text)
    out: list[str] = []
    current = ""
    for sent in sentences:
        candidate = f"{current} {sent}".strip() if current else sent
        if count_tokens(candidate) <= max_tokens:
            current = candidate
        else:
            if current:
                out.append(current)
            if count_tokens(sent) > max_tokens:
                out.extend(_split_by_words(sent, max_tokens))
                current = ""
            else:
                current = sent
    if current:
        out.append(current)
    return out


def split_long_section(content: str, max_tokens: int = MAX_TOKENS) -> list[str]:
    """
    Redécoupe une section trop longue en respectant la hiérarchie :
    tableau (atomique, jamais coupé) > paragraphe > phrase > mot.
    """
    blocks = _iter_atomic_blocks(content)
    result: list[str] = []
    current_parts: list[str] = []
    current_tokens = 0

    for kind, block_text in blocks:
        if kind == "table":
            block_tokens = count_tokens(block_text)
            if current_tokens + block_tokens > max_tokens and current_parts:
                result.append("\n\n".join(current_parts))
                current_parts, current_tokens = [], 0
            current_parts.append(block_text)
            current_tokens += block_tokens
            continue

        block_tokens = count_tokens(block_text)
        sub_parts = (
            [block_text]
            if block_tokens <= max_tokens
            else _split_text_block(block_text, max_tokens)
        )
        for part in sub_parts:
            part_tokens = count_tokens(part)
            if current_tokens + part_tokens > max_tokens and current_parts:
                result.append("\n\n".join(current_parts))
                current_parts, current_tokens = [], 0
            current_parts.append(part)
            current_tokens += part_tokens

    if current_parts:
        result.append("\n\n".join(current_parts))

    return result


def build_chunk_text(doc_title: str, section_title: str, content: str) -> str:
    """Injecte un en-tête de contexte dans chaque chunk (voir explication précédente)."""
    header = f"[Fiche : {doc_title} — Section : {section_title}]"
    return f"{header}\n\n{content}"


def chunk_document(doc: RawDocument, max_tokens: int = MAX_TOKENS) -> list[Chunk]:
    """
    Découpe un RawDocument en chunks, en mesurant tout en tokens réels
    (tokenizer bge-m3) plutôt qu'en caractères.
    """
    sections = split_into_sections(clean_for_embedding(doc.clean_text))

    merged: list[tuple[str, str]] = []
    pending_title, pending_content = None, ""
    for title, content in sections:
        if pending_title is None:
            pending_title, pending_content = title, content
        elif count_tokens(pending_content) < MIN_TOKENS:
            pending_content = f"{pending_content}\n\n## {title}\n{content}"
            pending_title = f"{pending_title} + {title}"
        else:
            merged.append((pending_title, pending_content))
            pending_title, pending_content = title, content
    if pending_title is not None:
        merged.append((pending_title, pending_content))

    chunks: list[Chunk] = []
    chunk_index = 0
    for section_title, content in merged:
        blocks = (
            [content]
            if count_tokens(content) <= max_tokens
            else split_long_section(content, max_tokens)
        )
        for block in blocks:
            text = build_chunk_text(doc.title, section_title, block)
            chunks.append(
                Chunk(
                    chunk_id=f"{doc.source_file}::{chunk_index}",
                    source_file=doc.source_file,
                    doc_title=doc.title,
                    section_title=section_title,
                    text=text,
                    char_count=len(text),
                    token_count=count_tokens(text),
                    is_simulated=doc.is_simulated,
                    nature=doc.nature,
                )
            )
            chunk_index += 1

    return chunks


def chunk_documents(docs: list[RawDocument], max_tokens: int = MAX_TOKENS) -> list[Chunk]:
    """Applique chunk_document à une liste de RawDocument (sortie de la phase 1)."""
    all_chunks: list[Chunk] = []
    for doc in docs:
        all_chunks.extend(chunk_document(doc, max_tokens=max_tokens))
    return all_chunks


if __name__ == "__main__":
    import sys
    from ingestion.parser import parse_directory

    sys.stdout.reconfigure(encoding="utf-8")

    docs_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/docs")
    documents = parse_directory(docs_path)
    chunks = chunk_documents(documents)

    for c in chunks:
        print(f"--- {c.chunk_id} ({c.token_count} tokens, {c.char_count} car.) ---")
        print(c.text[:200].replace("\n", " "))
        print("...\n")

    print(f"Total : {len(chunks)} chunks pour {len(documents)} documents.")