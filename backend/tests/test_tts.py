from app.services import tts


def test_each_format_has_a_distinct_voice_profile():
    rates = {f: tts.get_voice_profile(f).browser_rate for f in
             ("adhd_gamified", "dyslexia_audio", "asd_structured", "blended")}
    # Dyslexia must be the slowest; ADHD the fastest.
    assert rates["dyslexia_audio"] < rates["asd_structured"]
    assert rates["adhd_gamified"] == max(rates.values())


def test_profile_payload_shape():
    payload = tts.profile_payload("dyslexia_audio")
    assert payload["engine"] in ("coqui", "browser")
    assert 0.5 <= payload["browser_rate"] <= 1.5
    assert payload["style"]


def test_unknown_format_falls_back_to_default():
    assert tts.get_voice_profile("nonsense").format == tts.DEFAULT_PROFILE.format


def test_coqui_speed_derives_from_wpm():
    p = tts.get_voice_profile("adhd_gamified")
    assert p.coqui_speed > 1.0  # 185 wpm is faster than the 150 wpm base
