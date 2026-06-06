from app.services.atomiser import split_sentences
from app.services.parsers import clean_text


def test_reflow_joins_mid_sentence_linebreaks():
    raw = (
        "Transit time is the amount of time required for a message to travel from one\n"
        "device to another.\n"
        "Response time is the elapsed time between an inquiry and a response."
    )
    cleaned = clean_text(raw)
    # The mid-sentence wrap is healed, so the sentence is whole.
    assert "from one device to another." in cleaned
    # And sentence splitting now yields complete sentences (none cut mid-clause).
    sents = split_sentences(cleaned)
    assert any(s.endswith("to another.") for s in sents)
    assert all(len(s.split()) >= 4 for s in sents)


def test_reflow_keeps_paragraph_breaks():
    raw = "First paragraph ends here.\n\nSecond paragraph starts here."
    cleaned = clean_text(raw)
    assert "\n\n" in cleaned


def test_mends_hyphenated_linebreak():
    assert "photosynthesis" in clean_text("photo-\nsynthesis happens in plants.")
