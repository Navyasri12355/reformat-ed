"""Quality gate for LLM (or local) transform output.

Catches refusals, hallucinated padding, empty output and format-rule violations
before content is ever stored or shown to a student.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

FORBIDDEN_PHRASES = (
    "as an ai",
    "i cannot",
    "i'm unable",
    "i am unable",
    "original curriculum content",
    "rewrite this content",
)


@dataclass
class ValidationResult:
    passed: bool
    issues: list[str] = field(default_factory=list)


def validate_transform_output(original: str, transformed: str, output_format: str) -> ValidationResult:
    issues: list[str] = []
    original_words = len(original.split())
    transformed_words = len(transformed.split())

    if transformed_words < 20:
        issues.append("Output is too short (< 20 words)")

    if original_words and transformed_words > original_words * 3:
        issues.append(
            f"Output too long ({transformed_words} words vs {original_words} original)"
        )

    lower = transformed.lower()
    for phrase in FORBIDDEN_PHRASES:
        if phrase in lower:
            issues.append(f"Output contains forbidden phrase: '{phrase}'")

    if output_format in ("adhd_gamified", "blended"):
        if "mission" not in lower and "goal" not in lower:
            issues.append("ADHD format missing mission/goal framing")

    if output_format in ("asd_structured", "blended"):
        if not re.search(r"(step\s*\d|what you will learn|what you learned)", lower):
            issues.append("ASD format missing required structure markers")

    if output_format in ("dyslexia_audio", "blended"):
        sentences = [s for s in re.split(r"[.!?]+", transformed) if s.strip()]
        long_sentences = [s for s in sentences if len(s.split()) > 20]
        if len(long_sentences) > 2:
            issues.append(f"Dyslexia format has {len(long_sentences)} sentences over 20 words")

    return ValidationResult(passed=not issues, issues=issues)
