from ingestion.chunker import MAX_TOKENS, chunk_document, clean_for_embedding, split_into_sections
from ingestion.models import RawDocument


def test_clean_for_embedding_removes_table_separator_row():
    text = "| Champ | Valeur |\n|---|---|\n| a | 1 |\n"
    cleaned = clean_for_embedding(text)
    assert "|---|---|" not in cleaned
    assert "| Champ | Valeur |" in cleaned
    assert "| a | 1 |" in cleaned


def test_clean_for_embedding_strips_bold_and_code_markers_but_keeps_text():
    text = "Le **ratio important** et `liquidite.current_ratio` sont clés."
    cleaned = clean_for_embedding(text)
    assert "**" not in cleaned
    assert "`" not in cleaned
    assert "ratio important" in cleaned
    assert "liquidite.current_ratio" in cleaned


def test_split_into_sections_splits_on_h2_titles():
    text = "Intro texte.\n\n## Première section\nContenu 1.\n\n## Deuxième section\nContenu 2.\n"
    sections = split_into_sections(text)
    titles = [t for t, _ in sections]
    assert "Première section" in titles
    assert "Deuxième section" in titles


def test_split_into_sections_no_h2_returns_single_introduction_section():
    sections = split_into_sections("Juste du texte, sans sous-titre.")
    assert len(sections) == 1
    assert sections[0][0] == "Introduction"


def _make_doc(clean_text: str) -> RawDocument:
    return RawDocument(
        source_file="test.md",
        title="Fiche de test",
        nature="Fiche de test.",
        is_simulated=False,
        clean_text=clean_text,
    )


def test_chunk_document_respects_max_tokens_for_normal_content():
    text = (
        "# Fiche de test\n\n"
        "> **Nature de ce document.** Fiche de test.\n\n"
        "## 1. Petite section\n\n"
        "| Champ | Formule | Mesure |\n|---|---|---|\n"
        "| a | b / c | d |\n| e | f / g | h |\n\n"
        "Un paragraphe de texte normal pour compléter la section.\n"
    )
    chunks = chunk_document(_make_doc(text))
    assert len(chunks) >= 1
    for c in chunks:
        assert c.token_count <= MAX_TOKENS


def test_chunk_document_never_splits_a_table_even_if_it_exceeds_max_tokens():
    # Un tableau volontairement bien plus gros que MAX_TOKENS (480) pour
    # vérifier l'invariant : un tableau reste un bloc atomique, jamais
    # fragmenté ligne par ligne, même quand il dépasse la limite à lui seul.
    rows = "\n".join(f"| Ligne {i} | Valeur {i} | Détail explicatif {i} |" for i in range(120))
    text = (
        "# Fiche de test\n\n"
        "> **Nature de ce document.** Fiche de test.\n\n"
        "## 1. Grande section\n\n"
        f"| Colonne A | Colonne B | Colonne C |\n|---|---|---|\n{rows}\n"
    )
    chunks = chunk_document(_make_doc(text))
    table_chunks = [c for c in chunks if "Ligne 0 " in c.text]
    assert len(table_chunks) == 1
    assert "Ligne 119" in table_chunks[0].text
