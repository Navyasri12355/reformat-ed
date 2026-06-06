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


# Questions adapted from the screening instruments used by thruday.com's
# self-assessments: the WHO ASRS v1.1 (ADHD), a DSM-5 based autism screen (ASD),
# and a dyslexia checklist. Answered on a frequency scale (never → always).
QUIZ_QUESTIONS: list[QuizQuestion] = [
    # --- ADHD (ASRS: inattention, hyperactivity, impulsivity) ---
    QuizQuestion(
        "q1",
        "How often do you have trouble wrapping up the final details of a project once the challenging parts are done?",
        adhd_loading=0.85, dyslexia_loading=0.10, asd_loading=0.05,
    ),
    QuizQuestion(
        "q2",
        "How often do you have difficulty getting things in order when you have to do a task that requires organisation?",
        adhd_loading=0.85, dyslexia_loading=0.05, asd_loading=0.10,
    ),
    QuizQuestion(
        "q3",
        "How often do you feel restless, fidgety, or overly active, as if driven by a motor?",
        adhd_loading=0.85, dyslexia_loading=0.05, asd_loading=0.10,
    ),
    QuizQuestion(
        "q4",
        "How often are you distracted by activity or noise around you?",
        adhd_loading=0.90, dyslexia_loading=0.05, asd_loading=0.05,
    ),
    # --- Dyslexia (reading, writing, memory) ---
    QuizQuestion(
        "q5",
        "How often do you find yourself re-reading sentences several times to understand them?",
        adhd_loading=0.10, dyslexia_loading=0.85, asd_loading=0.05,
    ),
    QuizQuestion(
        "q6",
        "How often do you confuse or mix up similar-looking words or letters when reading or writing?",
        adhd_loading=0.05, dyslexia_loading=0.90, asd_loading=0.05,
    ),
    QuizQuestion(
        "q7",
        "How often do you make spelling mistakes, even with words you know well?",
        adhd_loading=0.05, dyslexia_loading=0.90, asd_loading=0.05,
    ),
    QuizQuestion(
        "q8",
        "How often does reading aloud, or reading for a long time, feel slow and tiring?",
        adhd_loading=0.10, dyslexia_loading=0.85, asd_loading=0.05,
    ),
    # --- Autism / ASD (social, patterns, sensory) ---
    QuizQuestion(
        "q9",
        "How often do you feel overwhelmed or drained in social situations?",
        adhd_loading=0.10, dyslexia_loading=0.05, asd_loading=0.85,
    ),
    QuizQuestion(
        "q10",
        "How often do you keep to the same routines and feel upset when plans change unexpectedly?",
        adhd_loading=0.05, dyslexia_loading=0.05, asd_loading=0.90,
    ),
    QuizQuestion(
        "q11",
        "How often do you have intense interests that take up most of your time and focus?",
        adhd_loading=0.15, dyslexia_loading=0.05, asd_loading=0.75,
    ),
    QuizQuestion(
        "q12",
        "How often are you very sensitive to sounds, lights, textures, or other sensory input?",
        adhd_loading=0.05, dyslexia_loading=0.05, asd_loading=0.85,
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
