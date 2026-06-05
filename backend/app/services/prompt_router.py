"""Format selection + prompt template loading.

The router decides which output format a student's profile maps to, and loads
the matching versioned YAML prompt template from disk (cached in-process).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from app.config import settings

BLENDED_THRESHOLD = 0.15  # second trait within this of dominant → blended
LOW_WEIGHT_FLOOR = 0.2  # all weights below this → safe structured default

FORMAT_FOR_TRAIT = {
    "adhd": "adhd_gamified",
    "dyslexia": "dyslexia_audio",
    "asd": "asd_structured",
}


@dataclass(frozen=True)
class ProfileWeights:
    adhd: float
    dyslexia: float
    asd: float

    def as_trait_map(self) -> dict[str, float]:
        return {"adhd": self.adhd, "dyslexia": self.dyslexia, "asd": self.asd}


def ranked_traits(profile: ProfileWeights) -> list[tuple[str, float]]:
    return sorted(profile.as_trait_map().items(), key=lambda kv: kv[1], reverse=True)


def select_output_format(profile: ProfileWeights) -> str:
    ranked = ranked_traits(profile)
    (dominant_trait, dominant_weight), (_second_trait, second_weight) = ranked[0], ranked[1]

    # Profile barely expresses any trait → predictable structured layout is the
    # safest, least-stimulating default.
    if dominant_weight < LOW_WEIGHT_FLOOR:
        return "asd_structured"

    # Two traits close together → blend both supports.
    if dominant_weight - second_weight <= BLENDED_THRESHOLD:
        return "blended"

    return FORMAT_FOR_TRAIT[dominant_trait]


class PromptLoader:
    """Loads and caches versioned prompt templates from the prompts directory."""

    def __init__(self, base_dir: str | None = None):
        self._base = Path(base_dir or settings.prompts_dir)
        self._cache: dict[str, dict] = {}

    def load(self, format_name: str, version: str | None = None) -> dict:
        version = version or settings.active_prompt_version
        key = f"{version}/{format_name}"
        if key not in self._cache:
            path = self._base / version / f"{format_name}.yaml"
            if not path.exists():
                raise FileNotFoundError(f"Prompt template not found: {path}")
            with path.open(encoding="utf-8") as fh:
                self._cache[key] = yaml.safe_load(fh)
        return self._cache[key]

    def render(self, format_name: str, atom: dict, version: str | None = None) -> tuple[str, str]:
        """Return (system_prompt, user_prompt) for the given atom."""
        template = self.load(format_name, version)
        user_prompt = template["user"].format(
            raw_text=atom["raw_text"],
            subject=atom.get("subject") or "general",
            grade_level=atom.get("grade_level") or "unknown",
            bloom_level=atom.get("bloom_level") or "understand",
        )
        return template["system"], user_prompt


prompt_loader = PromptLoader()
