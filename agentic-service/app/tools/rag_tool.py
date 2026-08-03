"""
Outil RAG 1 — connaissances d'analyse financière.

Rôle : étant donné une question en langage naturel, retrouve les passages
les plus pertinents des fiches de normes sectorielles (benchmarks, normes
comptables — voir app/data/docs/) déjà chunkées, embeddées et indexées
dans Chroma (ingestion/pipeline.py, db/database_service.py).

Utilisé par le Financial Analysis Agent (et par benchmark_tool.py) pour
aller chercher la norme sectorielle à laquelle comparer un ratio calculé.

Fonction volontairement simple (pas encore décorée en tool LangChain/
LangGraph) : graph/ n'existe pas encore. Le jour où l'agent est construit,
ajouter le décorateur @tool autour de rag_search est un changement
mécanique, pas une réécriture.
"""

from db.database_service import query_similar
from ingestion.embedder import embed_chunks
from ingestion.models import Chunk


def rag_search(question: str, top_k: int = 3) -> list[dict]:
    """
    Retourne les top_k chunks les plus pertinents pour `question`.

    Chaque résultat : chunk_id, source_file, section_title, text (le
    passage complet, en-tête de contexte inclus) et distance (cosinus,
    plus petit = plus proche).
    """
    query_chunk = Chunk(
        chunk_id="query",
        source_file="query",
        doc_title="query",
        section_title="query",
        text=question,
        char_count=len(question),
        token_count=0,
        is_simulated=False,
        nature=None,
    )
    query_embedding = embed_chunks([query_chunk])[0].embedding
    result = query_similar(query_embedding, top_k=top_k)

    if not result["ids"][0]:
        return []

    return [
        {
            "chunk_id": chunk_id,
            "source_file": meta["source_file"],
            "section_title": meta["section_title"],
            "text": doc,
            "distance": distance,
        }
        for chunk_id, meta, doc, distance in zip(
            result["ids"][0],
            result["metadatas"][0],
            result["documents"][0],
            result["distances"][0],
        )
    ]


if __name__ == "__main__":
    import sys

    sys.stdout.reconfigure(encoding="utf-8")

    q = sys.argv[1] if len(sys.argv) > 1 else "Niveau de levier financier acceptable pour le secteur BTP"
    for r in rag_search(q):
        print(f"[{r['chunk_id']}] (distance={r['distance']:.4f})")
        print(r["text"][:200].replace("\n", " "))
        print()
