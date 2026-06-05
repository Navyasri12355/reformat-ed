"""Onboarding quiz → cognitive profile.

Each question loads onto the three trait dimensions (ADHD, dyslexia, ASD) with
weights inspired by validated screening instruments (SNAP-IV, the Adult Dyslexia
Checklist and AQ-10). Answers are Likert-scaled and scores are normalised per
trait into [0, 1]. The traits are independent — they are not forced to sum to 1.
"""

from __future__ import annotations

from dataclasses import dataclass

ANSWER_WEIGHT: dict[str, float] = {
    "never": 0.0,
    "sometimes": 0.33,
    "often": 0.67,
    "always": 1.0,
}


@dataclass(frozen=True)
class QuizQuestion:
    id: str
    text: str
    adhd_loading: float
    dyslexia_loading: float
    asd_loading: float


QUIZ_QUESTIONS: list[QuizQuestion] = [
    QuizQuestion(
        "q1",
        "I find it hard to stay focused on a task without it changing or having a reward.",
        adhd_loading=0.85, dyslexia_loading=0.05, asd_loading=0.10,
    ),
    QuizQuestion(
        "q2",
        "I prefer listening to information rather than reading it.",
        adhd_loading=0.15, dyslexia_loading=0.80, asd_loading=0.05,
    ),
    QuizQuestion(
        "q3",
        "I like knowing exactly what will happen next before I start a new task.",
        adhd_loading=0.05, dyslexia_loading=0.05, asd_loading=0.90,
    ),
    QuizQuestion(
        "q4",
        "Reading long paragraphs feels tiring, or the words seem to move around.",
        adhd_loading=0.10, dyslexia_loading=0.85, asd_loading=0.05,
    ),
    QuizQuestion(
        "q5",
        "I often start tasks enthusiastically but struggle to finish them.",
        adhd_loading=0.80, dyslexia_loading=0.10, asd_loading=0.10,
    ),
    QuizQuestion(
        "q6",
        "Unexpected changes to a plan or routine really bother me.",
        adhd_loading=0.05, dyslexia_loading=0.05, asd_loading=0.90,
    ),
    QuizQuestion(
        "q7",
        "I find it easier to learn through games or interactive challenges.",
        adhd_loading=0.75, dyslexia_loading=0.15, asd_loading=0.10,
    ),
    QuizQuestion(
        "q8",
        "I sometimes mix up the order of letters when spelling words.",
        adhd_loading=0.05, dyslexia_loading=0.90, asd_loading=0.05,
    ),
    QuizQuestion(
        "q9",
        "I work best when instructions are broken into very clear numbered steps.",
        adhd_loading=0.20, dyslexia_loading=0.10, asd_loading=0.70,
    ),
    QuizQuestion(
        "q10",
        "I get easily distracted by other things happening around me.",
        adhd_loading=0.90, dyslexia_loading=0.05, asd_loading=0.05,
    ),
]

_BY_ID = {q.id: q for q in QUIZ_QUESTIONS}


def compute_profile_from_quiz(answers: dict[str, str]) -> dict[str, float | str]:
    """Map quiz answers to normalised trait weights.

    ``answers`` maps question id → Likert answer ("never"/"sometimes"/"often"/
    "always"). Unknown question ids and answers are ignored gracefully.
    """
    adhd_score = dyslexia_score = asd_score = 0.0

    for qid, answer in answers.items():
        question = _BY_ID.get(qid)
        if question is None or answer not in ANSWER_WEIGHT:
            continue
        weight = ANSWER_WEIGHT[answer]
        adhd_score += weight * question.adhd_loading
        dyslexia_score += weight * question.dyslexia_loading
        asd_score += weight * question.asd_loading

    adhd_max = sum(q.adhd_loading for q in QUIZ_QUESTIONS)
    dyslexia_max = sum(q.dyslexia_loading for q in QUIZ_QUESTIONS)
    asd_max = sum(q.asd_loading for q in QUIZ_QUESTIONS)

    def normalise(score: float, denom: float) -> float:
        if denom <= 0:
            return 0.0
        return round(min(1.0, max(0.0, score / denom)), 3)

    return {
        "adhd_weight": normalise(adhd_score, adhd_max),
        "dyslexia_weight": normalise(dyslexia_score, dyslexia_max),
        "asd_weight": normalise(asd_score, asd_max),
        "calibration_source": "onboarding",
    }
