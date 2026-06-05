import pytest

from app.services.prompt_router import ProfileWeights, prompt_loader, select_output_format


@pytest.mark.parametrize(
    "adhd,dyslexia,asd,expected",
    [
        (0.9, 0.1, 0.0, "adhd_gamified"),
        (0.1, 0.8, 0.1, "dyslexia_audio"),
        (0.0, 0.1, 0.9, "asd_structured"),
        (0.6, 0.5, 0.1, "blended"),  # dominant & second within threshold
        (0.1, 0.1, 0.1, "asd_structured"),  # all low → safe default
        (0.6, 0.0, 0.59, "blended"),  # ADHD & ASD near-equal
    ],
)
def test_format_selection(adhd, dyslexia, asd, expected):
    assert select_output_format(ProfileWeights(adhd, dyslexia, asd)) == expected


def test_prompt_templates_load_and_render():
    for fmt in ("adhd_gamified", "dyslexia_audio", "asd_structured"):
        system, user = prompt_loader.render(
            fmt,
            {"raw_text": "Cells are the basic unit of life.", "subject": "biology"},
        )
        assert system.strip()
        assert "Cells are the basic unit of life." in user
