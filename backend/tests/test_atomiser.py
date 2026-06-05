from app.services.atomiser import CurriculumAtomiser


def test_atoms_within_word_bounds():
    atomiser = CurriculumAtomiser(target_words_per_atom=150, max_words_per_atom=250, min_words_per_atom=40)
    long_text = ". ".join("This is a simple educational sentence about cells" for _ in range(80)) + "."
    atoms = atomiser.atomise([{"page_num": 1, "text": long_text}])
    assert atoms, "expected at least one atom"
    for atom in atoms[:-1]:  # last atom may be short (trailing content)
        assert len(atom.raw_text.split()) <= 250


def test_no_content_dropped_for_short_input():
    atomiser = CurriculumAtomiser()
    atoms = atomiser.atomise([{"page_num": 1, "text": "Photosynthesis converts light into energy."}])
    assert len(atoms) == 1
    assert "Photosynthesis" in atoms[0].raw_text


def test_bloom_classification_remember():
    atomiser = CurriculumAtomiser()
    atoms = atomiser.atomise(
        [{"page_num": 1, "text": "Students will define photosynthesis and list its stages."}]
    )
    assert atoms[0].bloom_level == "remember"


def test_subject_classification_biology():
    atomiser = CurriculumAtomiser()
    atoms = atomiser.atomise(
        [{"page_num": 1, "text": "The cell contains DNA and proteins essential to the organism."}]
    )
    assert atoms[0].subject == "biology"


def test_empty_pages_produce_no_atoms():
    atomiser = CurriculumAtomiser()
    assert atomiser.atomise([{"page_num": 1, "text": "   "}]) == []
