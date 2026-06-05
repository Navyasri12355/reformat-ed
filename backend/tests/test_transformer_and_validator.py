from app.services.output_validator import validate_transform_output
from app.services.prompt_router import ProfileWeights
from app.services.transformer import transform_atom

SAMPLE = {
    "raw_text": (
        "Photosynthesis is the process by which green plants use sunlight to make "
        "food from carbon dioxide and water. It happens in the chloroplasts. The "
        "process releases oxygen as a by-product, which animals need to breathe."
    ),
    "subject": "biology",
    "grade_level": "middle",
    "bloom_level": "understand",
}


def test_local_adhd_output_is_valid():
    result = transform_atom(SAMPLE, ProfileWeights(adhd=0.9, dyslexia=0.0, asd=0.0))
    assert result.output_format == "adhd_gamified"
    assert result.validation_passed
    assert "mission" in result.transformed_text.lower()


def test_local_dyslexia_output_is_valid():
    result = transform_atom(SAMPLE, ProfileWeights(adhd=0.0, dyslexia=0.9, asd=0.0))
    assert result.output_format == "dyslexia_audio"
    assert result.validation_passed


def test_local_asd_output_is_valid():
    result = transform_atom(SAMPLE, ProfileWeights(adhd=0.0, dyslexia=0.0, asd=0.9))
    assert result.output_format == "asd_structured"
    assert result.validation_passed
    assert "step 1" in result.transformed_text.lower()


def test_local_blended_output_is_valid():
    result = transform_atom(SAMPLE, ProfileWeights(adhd=0.6, dyslexia=0.0, asd=0.55))
    assert result.output_format == "blended"
    assert result.validation_passed


def test_validator_flags_refusal():
    result = validate_transform_output(SAMPLE["raw_text"], "As an AI I cannot help.", "asd_structured")
    assert not result.passed


def test_audio_script_has_no_markdown():
    result = transform_atom(SAMPLE, ProfileWeights(adhd=0.0, dyslexia=0.9, asd=0.0))
    assert "#" not in result.audio_script
    assert "*" not in result.audio_script
