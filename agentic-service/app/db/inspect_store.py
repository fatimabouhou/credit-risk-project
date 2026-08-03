"""
Utilitaire de consultation du vector store Chroma.

Liste tout ce qui est réellement stocké dans la collection (pas un
recalcul local) : ids, métadonnées, aperçu du texte, dimension des
vecteurs — pour vérifier ce qui a été persisté par database_service.py.

Usage (depuis app/) :
    python -m db.inspect_store
"""

import sys

from db.database_service import COLLECTION_NAME, get_collection


def inspect() -> None:
    sys.stdout.reconfigure(encoding="utf-8")

    collection = get_collection()
    total = collection.count()
    print(f"Collection : {COLLECTION_NAME}")
    print(f"Total      : {total} chunks\n")

    if total == 0:
        print("(vide — lance `python -m db.database_service` pour y mettre des chunks)")
        return

    result = collection.get(include=["metadatas", "documents", "embeddings"])

    by_file: dict[str, list[int]] = {}
    for i, meta in enumerate(result["metadatas"]):
        by_file.setdefault(meta["source_file"], []).append(i)

    for source_file in sorted(by_file):
        indices = by_file[source_file]
        print(f"{'=' * 70}")
        print(f"{source_file}  ({len(indices)} chunks)")
        print(f"{'=' * 70}")
        for i in indices:
            chunk_id = result["ids"][i]
            meta = result["metadatas"][i]
            doc = result["documents"][i]
            emb = result["embeddings"][i]
            preview = doc.replace("\n", " ")[:140]

            print(f"\n[{chunk_id}]")
            print(f"  section    : {meta['section_title']}")
            print(f"  simulé     : {meta['is_simulated']}")
            print(f"  embedding  : dim={len(emb)}, modèle={meta['embedding_model']}")
            print(f"  texte      : {preview}...")
        print()


if __name__ == "__main__":
    inspect()
