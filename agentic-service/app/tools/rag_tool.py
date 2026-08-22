"""
Outil RAG 1 — connaissances d'analyse financière.

Rôle : étant donné une question en langage naturel, retrouve les passages
les plus pertinents des fiches de normes sectorielles (benchmarks, normes
comptables — voir app/data/docs/) déjà chunkées, embeddées et indexées
dans Chroma (ingestion/pipeline.py, db/database_service.py).

Utilisé par le Financial Analysis Agent (et par benchmark_tool.py) pour
aller chercher la norme sectorielle à laquelle comparer un ratio calculé.

Pas décorée en @tool LangChain : appelée en interne par outil_recherche_normes
et benchmark_tool.py, jamais directement par le LLM. @traceable (langsmith)
sert uniquement à faire apparaître cet appel comme un span "Retriever" dans
LangSmith, nesté sous le tool LangChain qui l'appelle.
"""

from functools import lru_cache

from langsmith import traceable

from db.database_service import query_similar
from ingestion.embedder import embed_chunks
from ingestion.models import Chunk

# Cache des recherches, sur toute la durée de vie du process.
#
# Pourquoi c'est sûr : le corpus indexé dans Chroma (fiches de normes
# sectorielles) est STATIQUE à l'exécution — il ne change qu'en relançant
# manuellement le pipeline d'ingestion (ingestion/pipeline.py), ce qui
# implique de toute façon un redémarrage du service. Une même question
# renvoie donc toujours le même résultat.
#
# Pourquoi ça vaut le coup : benchmark_tool.py construit sa question à
# partir du seul couple (ratio_name, secteur) — jamais du client ni de ses
# valeurs. Les ~17 recherches d'un run (une par ratio) sont donc RIGOUREUSEMENT
# identiques d'une analyse à l'autre pour un même secteur, et étaient
# pourtant intégralement refaites à chaque fois. Chaque appel coûtait deux
# fois cher : l'embedding de la question par bge-m3 (CPU) PUIS l'aller-retour
# HTTP vers Chroma. Le cache supprime les deux.
_SEARCH_CACHE_MAXSIZE = 512


@lru_cache(maxsize=_SEARCH_CACHE_MAXSIZE)
def _rag_search_cached(question: str, top_k: int, contains: str | None) -> tuple[dict, ...]:
    """Implémentation réelle, mémoïsée. Retourne un tuple (immuable) plutôt
    qu'une liste, pour qu'un appelant ne puisse pas altérer l'entrée en cache
    partagée par tous les appels suivants."""
    return tuple(_rag_search_uncached(question, top_k, contains))


@traceable(name="Retriever (ChromaDB)", run_type="retriever")
def rag_search(question: str, top_k: int = 3, contains: str | None = None) -> list[dict]:
    """Voir _rag_search_uncached pour le détail. Passe par le cache, et
    recopie chaque résultat : les appelants manipulent ainsi leurs propres
    dicts, sans risque de corrompre le cache."""
    return [dict(r) for r in _rag_search_cached(question, top_k, contains)]


def _rag_search_uncached(question: str, top_k: int = 3, contains: str | None = None) -> list[dict]:
    """
    Retourne les top_k chunks les plus pertinents pour `question`.

    `contains` (optionnel) : recherche hybride — restreint la recherche
    aux chunks dont le texte contient exactement cette sous-chaîne (ex.
    l'identifiant d'un ratio entre backticks, "liquidite.quick_ratio"),
    avant de classer par similarité. À utiliser quand on cherche la norme
    d'un ratio précis et identifiable par nom exact, pour ne jamais
    confondre deux ratios voisins dans la même fiche (voir
    tools/benchmark_tool.py). Sans `contains`, comportement inchangé
    (similarité seule) — utile pour une question vraiment libre.

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
    result = query_similar(query_embedding, top_k=top_k, contains=contains)

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
