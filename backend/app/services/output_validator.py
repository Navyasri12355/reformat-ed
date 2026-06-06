"""Quality gate for LLM (or local) transform output.

Deliberately lenient: it only rejects output that is genuinely unusable — a model
refusal, near-empty text, or implausibly long hallucinated padding. It does NOT
reject content for "expanding" the original or for missing exact structure
markers, because accessibility reframing legitimately rewrites and lengthens
text. (Over-strict checks here were causing good reframed output to be thrown
away in favour of the raw, unreframed fallback.)
"""

from __future__ import annotations

from dataclasses import dataclass, field

FORBIDDEN_PHRASES = (
    "as an ai",
    "i cannot",
    "i'm unable",
    "i am unable",
    "i can't help",
    "original curriculum content",
    "rewrite this content following",
    "here is the rewritten",  # meta-preamble leak
)

MIN_WORDS = 12
# Only flag truly runaway output (hallucinated padding), with a generous floor
# so short atoms can still be reframed into fuller explanations.
RUNAWAY_MULTIPLIER = 8
RUNAWAY_FLOOR_WORDS = 400


@dataclass
class ValidationResult:
    passed: bool
    issues: list[str] = field(default_factory=list)


def validate_transform_output(original: str, transformed: str, output_format: str) -> ValidationResult:
    issues: list[str] = []
    transformed = (transformed or "").strip()
    transformed_words = len(transformed.split())
    original_words = len(original.split())

    if transformed_words < MIN_WORDS:
        issues.append(f"Output is too short (< {MIN_WORDS} words)")

    lower = transformed.lower()
    for phrase in FORBIDDEN_PHRASES:
        if phrase in lower:
            issues.append(f"Output contains a refusal/meta phrase: '{phrase}'")

    if original_words and transformed_words > max(original_words * RUNAWAY_MULTIPLIER, RUNAWAY_FLOOR_WORDS):
        issues.append(f"Output is implausibly long ({transformed_words} words)")

    return ValidationResult(passed=not issues, issues=issues)
