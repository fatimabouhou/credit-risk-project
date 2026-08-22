"""
PHASE 4 — Persistance (vector store)

Rôle de ce module :
    Stocker les EmbeddedChunk (sortie de la phase 3 / embedder.py) dans
    Chroma, et permettre de retrouver les chunks les plus proches d'un
    vecteur de requête (recherche par similarité, pour tools/rag_tool.py).

Chroma tourne dans son propre conteneur Docker (voir docker-compose.yml,
service "chroma") — ce module n'est qu'un client HTTP vers ce serveur, il
n'embarque jamais de Chroma "local" en mémoire du process agentic-service.
Host/port sont configurables par variables d'environnement pour fonctionner
aussi bien en local (poetry run, hors Docker) qu'en conteneur (où le host
devient le nom du service Docker : "chroma").
"""

import os

import chromadb
from chromadb.api import ClientAPI

from ingestion.models import EmbeddedChunk

CHROMA_HOST = os.environ.get("CHROMA_HOST", "localhost")
CHROMA_PORT = int(os.environ.get("CHROMA_PORT", "8010"))

# Une collection par modèle d'embedding : des vecteurs produits par des
# modèles différents ne sont pas comparables entre eux, donc pas question
# de les mélanger dans la même collection Chroma.
COLLECTION_NAME = "fiches_financieres__bge_m3"

_client: ClientAPI | None = None
_collection = None


def get_client() -> ClientAPI:
    """Client HTTP vers le serveur Chroma (lazy, mis en cache)."""
    global _client
    if _client is None:
        _client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
    return _client


def get_collection():
    """
    Récupère (ou crée) la collection Chroma dédiée à ce modèle d'embedding.
    Mise en cache comme `get_client()` : avant ce cache, chaque `rag_search`
    (voir tools/rag_tool.py) déclenchait un aller-retour HTTP `get_or_create_
    collection` EN PLUS de la recherche elle-même — un run d'analyse complet
    (~35 recherches RAG, voir benchmark_tool.py/context_builder.py) doublait
    ainsi son trafic Chroma pour rien, la collection ne changeant jamais
    entre deux appels au sein du même process.
    """
    global _collection
    if _collection is None:
        _collection = get_client().get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def persist_embedded_chunks(embedded_chunks: list[EmbeddedChunk]) -> None:
    """
    Upsert les chunks embeddés dans Chroma : un chunk_id déjà présent est
    remplacé (idempotent — relancer le pipeline sur les mêmes docs ne crée
    pas de doublons).
    """
    if not embedded_chunks:
        return

    collection = get_collection()
    collection.upsert(
        ids=[ec.chunk.chunk_id for ec in embedded_chunks],
        embeddings=[ec.embedding for ec in embedded_chunks],
        documents=[ec.chunk.text for ec in embedded_chunks],
        metadatas=[
            {
                "source_file": ec.chunk.source_file,
                "doc_title": ec.chunk.doc_title,
                "section_title": ec.chunk.section_title,
                "is_simulated": ec.chunk.is_simulated,
                "nature": ec.chunk.nature or "",
                "embedding_model": ec.embedding_model,
            }
            for ec in embedded_chunks
        ],
    )


def query_similar(
    query_embedding: list[float], top_k: int = 5, contains: str | None = None
) -> chromadb.QueryResult:
    """
    Retourne les top_k chunks les plus proches (cosinus) d'un vecteur de
    requête.

    `contains` (optionnel) : recherche hybride — restreint D'ABORD aux
    chunks dont le TEXTE contient exactement cette sous-chaîne (via
    `where_document`, filtre exact sur le contenu, pas une comparaison de
    vecteurs), puis classe ce sous-ensemble par similarité. Utilisé pour
    ne jamais confondre deux ratios voisins dans la même fiche (ex.
    current_ratio / quick_ratio) : la similarité seule ne suffisait pas à
    les distinguer de façon fiable (voir tools/benchmark_tool.py).
    """
    collection = get_collection()
    where_document = {"$contains": contains} if contains else None
    return collection.query(
        query_embeddings=[query_embedding], n_results=top_k, where_document=where_document
    )


if __name__ == "__main__":
    import sys
    from pathlib import Path

    sys.stdout.reconfigure(encoding="utf-8")

    from ingestion.pipeline import run_ingestion_pipeline

    docs_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/docs")
    embedded_chunks = run_ingestion_pipeline(docs_path, show_progress_bar=True)
    persist_embedded_chunks(embedded_chunks)

    print(
        f"{len(embedded_chunks)} chunks persistés dans la collection "
        f"'{COLLECTION_NAME}' ({CHROMA_HOST}:{CHROMA_PORT})."
    )
