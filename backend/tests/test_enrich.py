from app.services.enrich import build_meta, build_poll, detect_idioms, extract_keywords

ATOM = {
    "raw_text": (
        "Photosynthesis is how green plants make food. It happens inside chloroplasts, "
        "which contain chlorophyll. For a plant this is a piece of cake."
    ),
    "subject": "biology",
    "grade_level": "middle",
    "bloom_level": "understand",
}


def test_dyslexia_meta_has_keywords():
    meta = build_meta(ATOM, "dyslexia_audio")
    assert meta["keywords"]
    assert "photosynthesis" in meta["keywords"]
    assert meta["illustration"] == "leaf"
    assert meta["diagram"].startswith("flowchart")


def test_adhd_meta_has_goal_anchor_poll():
    meta = build_meta(ATOM, "adhd_gamified")
    assert meta["goal"]
    assert meta["anchor"] == "🌿"
    assert meta["illustration"] == "leaf"
    poll = meta["poll"]
    assert len(poll["options"]) == 3
    assert 0 <= poll["answer"] < 3
    # Cloze: the question shows a blank, and the answer is a word from the atom.
    assert poll["q"].startswith("Fill in the blank")
    assert "______" in poll["q"]
    assert poll["options"][poll["answer"]].lower() in ATOM["raw_text"].lower()
    # The blanked word must not still be visible in the question.
    assert poll["options"][poll["answer"]].lower() not in poll["q"].lower().replace("fill in the blank", "")


def test_asd_meta_has_schedule_idioms_rubric_example():
    meta = build_meta(ATOM, "asd_structured")
    assert meta["schedule"] == ["Schedule", "Content", "Summary", "Quiz"]
    assert any(i["phrase"] == "a piece of cake" for i in meta["idioms"])
    assert meta["real_world"]
    assert len(meta["rubric"]) >= 2


def test_poll_is_deterministic():
    a = build_poll(ATOM["raw_text"], extract_keywords(ATOM["raw_text"], "biology"), "biology")
    b = build_poll(ATOM["raw_text"], extract_keywords(ATOM["raw_text"], "biology"), "biology")
    assert a == b


def test_idiom_detection_literal_meaning():
    idioms = detect_idioms("This is a piece of cake to understand.")
    assert idioms == [{"phrase": "a piece of cake", "literal": "very easy"}]
