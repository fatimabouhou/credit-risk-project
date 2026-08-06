from ingestion.parser import clean_text, detect_simulated, extract_nature, extract_title


def test_extract_title_finds_first_h1():
    text = "# Fiche méthodologique — Ratios de liquidité\n\nContenu."
    assert extract_title(text) == "Fiche méthodologique — Ratios de liquidité"


def test_extract_title_returns_empty_when_absent():
    assert extract_title("Pas de titre ici.") == ""


def test_extract_nature_parses_blockquote():
    text = (
        "# Titre\n\n"
        "> **Nature de ce document.** Fiche de normes sectorielles [SIMULÉ] "
        "destinée au RAG 1.\n\n"
        "## Section suivante\n"
    )
    nature = extract_nature(text)
    assert nature is not None
    assert "Fiche de normes sectorielles" in nature


def test_extract_nature_none_when_absent():
    assert extract_nature("# Titre\n\nPas de note ici.\n\n## Section\n") is None


def test_detect_simulated_true_and_false():
    assert detect_simulated("Valeur [SIMULÉ] fictive.") is True
    assert detect_simulated("Valeur réelle.") is False


def test_clean_text_removes_horizontal_rules_and_extra_blank_lines():
    raw = "Titre\n\n---\n\nParagraphe.\n\n\n\n\nAutre paragraphe.   \n"
    cleaned = clean_text(raw)
    assert "---" not in cleaned
    assert "\n\n\n" not in cleaned
    assert not cleaned.endswith(" ")
