"""
Modèles de données partagés entre les phases du pipeline d'ingestion.
"""

from dataclasses import dataclass


@dataclass
class RawDocument:
    """Sortie de la phase 1 (parser.py) : un document .md extrait + nettoyé."""

    source_file: str
    title: str
    nature: str | None
    is_simulated: bool
    clean_text: str

    @property
    def char_count(self) -> int:
        return len(self.clean_text)

@dataclass
class Chunk:
    """Sortie de la phase 2 (chunker.py) : un chunk prêt pour l'embedding."""

    chunk_id: str
    source_file: str
    doc_title: str
    section_title: str
    text: str
    char_count: int
    token_count: int
    is_simulated: bool
    nature: str | None


@dataclass
class EmbeddedChunk:
    """Sortie de la phase 3 (embedder.py) : un chunk + son vecteur d'embedding."""

    chunk: Chunk
    embedding: list[float]
    embedding_model: str