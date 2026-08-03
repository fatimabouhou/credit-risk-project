"""
PHASE 3 — Embedding

Rôle de ce module :
    Transformer chaque Chunk (issu de la phase 2 / chunker.py) en vecteur
    numérique exploitable pour la recherche par similarité (RAG).

Modèle utilisé : BAAI/bge-m3
    - Gratuit, open-source (licence MIT), pas d'appel API payant.
    - Multilingue, très bon en français (langue des fiches de ce projet).
    - Fenêtre de contexte 8192 tokens : couvre largement MAX_TOKENS=480
      utilisé par chunker.py, donc aucun chunk n'est tronqué à l'embedding.
    - Classé parmi les meilleurs modèles d'embedding open-source multilingues
      (MTEB), niveau de qualité proche de modèles propriétaires payants.

Outil : sentence-transformers
    - Wrapper standard, maintenu, au-dessus de `transformers` : gère le
      pooling, la normalisation et le batching en quelques lignes, avec
      détection automatique du GPU (CUDA) si disponible, sinon CPU.
    - bge-m3 sait aussi produire des représentations creuses (lexicales) et
      multi-vecteurs (ColBERT) via la librairie officielle FlagEmbedding,
      pour une recherche hybride dense+sparse. Non implémenté ici (RAG dense
      simple suffit pour ce corpus) mais c'est l'évolution naturelle si la
      qualité de recherche doit être poussée plus loin — voir rag_tool.py.

Ce module ne fait PAS de chunking (voir chunker.py, phase 2) et ne
persiste PAS les vecteurs (voir db/database_service.py) — il calcule
seulement les embeddings.
"""

from sentence_transformers import SentenceTransformer

from ingestion.models import Chunk, EmbeddedChunk

# Même modèle que le tokenizer utilisé en phase 2 (chunker.py) : la taille
# des chunks a été mesurée avec le tokenizer de ce modèle exact.
EMBEDDING_MODEL_NAME = "BAAI/bge-m3"

_model: SentenceTransformer | None = None


def get_model() -> SentenceTransformer:
    """Charge le modèle d'embedding une seule fois (lazy loading, mis en cache)."""
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return _model


def embed_chunks(
    chunks: list[Chunk],
    batch_size: int = 16,
    show_progress_bar: bool = False,
) -> list[EmbeddedChunk]:
    """
    Calcule un embedding dense pour chaque chunk.

    Les vecteurs sont normalisés (norme L2 = 1) pour que la similarité
    cosinus se réduise à un simple produit scalaire côté recherche
    (compatible avec la quasi-totalité des vector stores).
    """
    if not chunks:
        return []

    model = get_model()
    texts = [c.text for c in chunks]
    vectors = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=show_progress_bar,
        normalize_embeddings=True,
        convert_to_numpy=True,
    )

    return [
        EmbeddedChunk(
            chunk=chunk,
            embedding=vector.tolist(),
            embedding_model=EMBEDDING_MODEL_NAME,
        )
        for chunk, vector in zip(chunks, vectors)
    ]


if __name__ == "__main__":
    import sys
    from pathlib import Path

    from ingestion.chunker import chunk_documents
    from ingestion.parser import parse_directory

    sys.stdout.reconfigure(encoding="utf-8")

    docs_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/docs")
    documents = parse_directory(docs_path)
    chunks = chunk_documents(documents)
    embedded = embed_chunks(chunks, show_progress_bar=True)

    for ec in embedded:
        print(f"--- {ec.chunk.chunk_id} (dim={len(ec.embedding)}) ---")
        print(ec.chunk.text[:200].replace("\n", " "))
        print("...\n")

    print(f"Total : {len(embedded)} chunks embeddés avec {EMBEDDING_MODEL_NAME}.")
