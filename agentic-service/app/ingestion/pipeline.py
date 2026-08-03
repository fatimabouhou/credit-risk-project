"""
Orchestrateur du pipeline d'ingestion RAG.

Enchaîne les 3 phases sur un dossier de fiches .md :
    1. parser.py   — extraction + nettoyage -> RawDocument
    2. chunker.py  — découpage token-aware   -> Chunk
    3. embedder.py — embedding (BAAI/bge-m3) -> EmbeddedChunk

La persistance des vecteurs (vector store) n'est volontairement pas gérée
ici : c'est le rôle de db/database_service.py (phase 4, à venir).
"""

from pathlib import Path

from ingestion.chunker import chunk_documents
from ingestion.embedder import embed_chunks
from ingestion.models import EmbeddedChunk
from ingestion.parser import parse_directory


def run_ingestion_pipeline(
    docs_dir: Path,
    max_tokens: int = 480,
    show_progress_bar: bool = False,
) -> list[EmbeddedChunk]:
    """Exécute les 3 phases du pipeline sur tous les .md de `docs_dir`."""
    documents = parse_directory(docs_dir)
    chunks = chunk_documents(documents, max_tokens=max_tokens)
    return embed_chunks(chunks, show_progress_bar=show_progress_bar)


if __name__ == "__main__":
    import sys

    # Force l'UTF-8 en sortie : la console Windows par défaut (cp1252)
    # affiche mal les caractères accentués du français sinon.
    sys.stdout.reconfigure(encoding="utf-8")

    docs_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/docs")
    embedded_chunks = run_ingestion_pipeline(docs_path, show_progress_bar=True)

    by_file: dict[str, int] = {}
    for ec in embedded_chunks:
        by_file[ec.chunk.source_file] = by_file.get(ec.chunk.source_file, 0) + 1

    print(f"\nPipeline terminé : {len(embedded_chunks)} chunks embeddés.")
    for source_file, count in by_file.items():
        print(f"  - {source_file} : {count} chunks")
