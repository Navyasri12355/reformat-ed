from app.services.adapt import SignalEvent, event_engagement_score, recalibrate_weights


def _events(fmt: str, event_type: str, n: int, time_ms: int = 20000, retry: int = 0):
    return [SignalEvent(event_type, time_ms, retry, fmt) for _ in range(n)]


def test_engagement_score_bounds():
    high = event_engagement_score(SignalEvent("atom_complete", 20000, 0, "adhd_gamified"))
    low = event_engagement_score(SignalEvent("atom_skip", None, None, "adhd_gamified"))
    assert 0.0 <= low < high <= 1.0


def test_insufficient_data_returns_none():
    events = _events("adhd_gamified", "atom_complete", 3)
    assert recalibrate_weights(events, {"adhd_weight": 0.3, "dyslexia_weight": 0.3, "asd_weight": 0.3}) is None


def test_strong_dyslexia_engagement_raises_weight():
    # Lots of successful dyslexia engagement, poor adhd engagement.
    events = _events("dyslexia_audio", "atom_complete", 12) + _events("adhd_gamified", "atom_skip", 6)
    current = {"adhd_weight": 0.4, "dyslexia_weight": 0.2, "asd_weight": 0.1}
    new = recalibrate_weights(events, current)
    assert new is not None
    assert new["dyslexia_weight"] > current["dyslexia_weight"]


def test_weights_stay_bounded():
    events = _events("asd_structured", "atom_complete", 30)
    current = {"adhd_weight": 0.0, "dyslexia_weight": 0.0, "asd_weight": 0.99}
    new = recalibrate_weights(events, current)
    if new is not None:
        for v in new.values():
            assert 0.0 <= v <= 1.0
