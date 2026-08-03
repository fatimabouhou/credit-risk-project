"""
Script d'inspection : affiche le texte nettoyé complet de chaque document
et le contenu complet de chaque chunk (pas de troncature).
"""
import sys
from pathlib import Path

from ingestion.parser import parse_directory
from ingestion.chunker import chunk_documents

docs_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/docs")

documents = parse_directory(docs_path)

print("=" * 100)
print("TEXTE NETTOYÉ COMPLET (sortie phase 1)")
print("=" * 100)
for doc in documents:
    print(f"\n{'#' * 80}\n# {doc.source_file}\n{'#' * 80}\n")
    print(doc.clean_text)
    print(f"\n[char_count = {doc.char_count}]\n")

chunks = chunk_documents(documents)

print("\n\n" + "=" * 100)
print("CHUNKS COMPLETS (sortie phase 2)")
print("=" * 100)
for c in chunks:
    print(f"\n{'-' * 80}")
    print(f"chunk_id      : {c.chunk_id}")
    print(f"section_title : {c.section_title}")
    print(f"char_count    : {c.char_count}")
    print(f"is_simulated  : {c.is_simulated}")
    print("-" * 80)
    print(c.text)

print(f"\n\nTotal : {len(chunks)} chunks pour {len(documents)} documents.")