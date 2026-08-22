import importlib


def test_rag_search_embeds_query_and_forwards_filter(monkeypatch):
    rag = importlib.import_module("tools.rag_tool")
    rag._rag_search_cached.cache_clear()
    captured = {}

    class Embedded:
        embedding = [0.1, 0.2]

    def fake_embed(chunks):
        captured["question"] = chunks[0].text
        return [Embedded()]

    def fake_query(embedding, top_k, contains):
        captured.update(embedding=embedding, top_k=top_k, contains=contains)
        return {"ids": [["chunk-1"]], "metadatas": [[{"source_file": "normes.md", "section_title": "DSCR"}]], "documents": [["DSCR > 1,25"]], "distances": [[0.12]]}

    monkeypatch.setattr(rag, "embed_chunks", fake_embed)
    monkeypatch.setattr(rag, "query_similar", fake_query)
    result = rag.rag_search("norme DSCR", top_k=2, contains="dscr")

    assert result == [{"chunk_id": "chunk-1", "source_file": "normes.md", "section_title": "DSCR", "text": "DSCR > 1,25", "distance": 0.12}]
    assert captured == {"question": "norme DSCR", "embedding": [0.1, 0.2], "top_k": 2, "contains": "dscr"}


def test_rag_search_returns_empty_when_vector_store_has_no_match(monkeypatch):
    rag = importlib.import_module("tools.rag_tool")
    rag._rag_search_cached.cache_clear()

    class Embedded:
        embedding = [0.1]

    monkeypatch.setattr(rag, "embed_chunks", lambda chunks: [Embedded()])
    monkeypatch.setattr(rag, "query_similar", lambda embedding, top_k, contains: {"ids": [[]], "metadatas": [[]], "documents": [[]], "distances": [[]]})

    assert rag.rag_search("question sans resultat") == []