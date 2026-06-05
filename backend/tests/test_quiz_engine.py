from app.services.quiz_engine import QUIZ_QUESTIONS, compute_profile_from_quiz


def test_all_never_yields_zero_weights():
    answers = {q.id: "never" for q in QUIZ_QUESTIONS}
    profile = compute_profile_from_quiz(answers)
    assert profile["adhd_weight"] == 0.0
    assert profile["dyslexia_weight"] == 0.0
    assert profile["asd_weight"] == 0.0


def test_adhd_dominant_answers():
    answers = {q.id: "never" for q in QUIZ_QUESTIONS}
    # ADHD-loaded questions answered "always"
    for qid in ("q1", "q5", "q7", "q10"):
        answers[qid] = "always"
    profile = compute_profile_from_quiz(answers)
    assert profile["adhd_weight"] > profile["dyslexia_weight"]
    assert profile["adhd_weight"] > profile["asd_weight"]


def test_weights_are_bounded():
    answers = {q.id: "always" for q in QUIZ_QUESTIONS}
    profile = compute_profile_from_quiz(answers)
    for key in ("adhd_weight", "dyslexia_weight", "asd_weight"):
        assert 0.0 <= profile[key] <= 1.0


def test_unknown_answers_ignored():
    profile = compute_profile_from_quiz({"q1": "banana", "nope": "always"})
    assert profile["adhd_weight"] == 0.0


def test_calibration_source_is_onboarding():
    assert compute_profile_from_quiz({})["calibration_source"] == "onboarding"
