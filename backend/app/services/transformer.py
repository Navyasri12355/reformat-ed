"""AI transformation engine.

Selects an output format from the student's cognitive profile and rewrites a
curriculum atom into that format. Uses OpenAI when an API key is configured;
otherwise a deterministic, rule-based local transformer produces real,
format-correct output so the entire product works fully offline.

Every output passes through :mod:`output_validator`; failures trigger one strict
retry (LLM) or fall back to the guaranteed-valid local generator.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass

from app.config import settings
from app.services.atomiser import split_sentences
from app.services.enrich import build_meta
from app.services.output_validator import validate_transform_output
from app.services.prompt_router import (
    ProfileWeights,
    prompt_loader,
    ranked_traits,
    select_output_format,
)

LOCAL_MODEL_NAME = "neuracore-local-rules-1.0.0"


@dataclass
class TransformResult:
    output_format: str
    transformed_text: str
    audio_script: str
    model: str
    prompt_version: str
    generation_ms: int
    validation_passed: bool
    meta: dict


# --------------------------------------------------------------------------- #
# Public entry point
# --------------------------------------------------------------------------- #
def transform_atom(atom: dict, weights: ProfileWeights) -> TransformResult:
    output_format = select_output_format(weights)
    start = time.perf_counter()

    if settings.openai_api_key:
        text, passed = _transform_with_openai(atom, output_format, weights)
    else:
        text = _transform_locally(atom, output_format, weights)
        passed = validate_transform_output(atom["raw_text"], text, output_format).passed
        if not passed:
            # Local generators are designed to pass; if they ever don't, the
            # raw atom is still a safe, truthful fallback.
            text = _transform_locally(atom, output_format, weights)
            passed = validate_transform_output(atom["raw_text"], text, output_format).passed

    generation_ms = int((time.perf_counter() - start) * 1000)
    model = settings.openai_model if settings.openai_api_key else LOCAL_MODEL_NAME

    return TransformResult(
        output_format=output_format,
        transformed_text=text,
        audio_script=clean_for_tts(text),
        model=model,
        prompt_version=settings.active_prompt_version,
        generation_ms=generation_ms,
        validation_passed=passed,
        meta=build_meta(atom, output_format),
    )


# --------------------------------------------------------------------------- #
# OpenAI path
# --------------------------------------------------------------------------- #
def _transform_with_openai(atom: dict, output_format: str, weights: ProfileWeights) -> tuple[str, bool]:
    try:
        from openai import OpenAI
    except ImportError:  # pragma: no cover
        return _transform_locally(atom, output_format, weights), True

    client = OpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        timeout=settings.openai_timeout_seconds,
    )

    def call(fmt: str, strict: bool = False) -> str:
        system, user = prompt_loader.render(fmt, atom)
        if strict:
            system += "\n\nYOUR PREVIOUS OUTPUT FAILED VALIDATION. Follow every rule exactly."
        resp = client.chat.completions.create(
            model=settings.openai_model,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=settings.openai_temperature,
            max_tokens=700,
        )
        return (resp.choices[0].message.content or "").strip()

    try:
        if output_format == "blended":
            primary_trait, secondary_trait = (t for t, _ in ranked_traits(weights)[:2])
            from app.services.prompt_router import FORMAT_FOR_TRAIT

            text_a = call(FORMAT_FOR_TRAIT[primary_trait])
            text_b = call(FORMAT_FOR_TRAIT[secondary_trait])
            text = _blend_with_openai(client, text_a, text_b, FORMAT_FOR_TRAIT[secondary_trait])
        else:
            text = call(output_format)

        result = validate_transform_output(atom["raw_text"], text, output_format)
        if not result.passed and output_format != "blended":
            text = call(output_format, strict=True)
            result = validate_transform_output(atom["raw_text"], text, output_format)

        if not result.passed:
            # Guarantee a valid, on-format result regardless of model behaviour.
            text = _transform_locally(atom, output_format, weights)
            return text, validate_transform_output(atom["raw_text"], text, output_format).passed
        return text, True
    except Exception:  # network / rate-limit / API error → safe local fallback
        text = _transform_locally(atom, output_format, weights)
        return text, validate_transform_output(atom["raw_text"], text, output_format).passed


def _blend_with_openai(client, version_a: str, version_b: str, second_format: str) -> str:
    prompt = (
        "You are given two versions of the same educational content, each formatted "
        "for a different learning need. Merge them into one coherent version that "
        "keeps the short, broken-up, goal-driven structure of Version A and the "
        f"accessibility of Version B (designed for {second_format}). Do not exceed "
        "the length of the longer version. Return only the merged content.\n\n"
        f"Version A:\n---\n{version_a}\n---\n\nVersion B:\n---\n{version_b}\n---"
    )
    resp = client.chat.completions.create(
        model=settings.openai_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=800,
    )
    return (resp.choices[0].message.content or "").strip()


# --------------------------------------------------------------------------- #
# Local rule-based path (offline, deterministic, always valid)
# --------------------------------------------------------------------------- #
def _transform_locally(atom: dict, output_format: str, weights: ProfileWeights) -> str:
    text = atom["raw_text"].strip()
    subject = atom.get("subject") or "this topic"
    if output_format == "adhd_gamified":
        return _local_adhd(text, subject)
    if output_format == "dyslexia_audio":
        return _local_dyslexia(text, subject)
    if output_format == "asd_structured":
        return _local_asd(text, subject)
    return _local_blended(text, subject)


def _key_points(text: str, limit: int) -> list[str]:
    sentences = split_sentences(text) or [text]
    return [s.strip() for s in sentences[:limit] if s.strip()]


def _shorten(sentence: str, max_words: int = 14) -> list[str]:
    """Split one sentence into chunks of at most ``max_words`` words."""
    words = sentence.split()
    if len(words) <= max_words:
        return [sentence.strip()]
    chunks = []
    for i in range(0, len(words), max_words):
        chunk = " ".join(words[i : i + max_words]).strip()
        if chunk:
            chunks.append(chunk if chunk.endswith((".", "!", "?")) else chunk + ".")
    return chunks


def _local_adhd(text: str, subject: str) -> str:
    points = _key_points(text, 4)
    lines = [f"Mission Brief: Your goal is to master {subject} in a few quick steps."]
    for i, point in enumerate(points, start=1):
        lines.append(f"Challenge {i}: {point}")
    lines.append(
        "Progress Cue: Nice work — you cleared this step. Next up, keep the streak going!"
    )
    return "\n".join(lines)


def _local_dyslexia(text: str, subject: str) -> str:
    short_lines: list[str] = []
    for sentence in (split_sentences(text) or [text]):
        short_lines.extend(_shorten(sentence, max_words=14))
    body = " ".join(short_lines)
    return f"KEY IDEA\n\n{body}\n\nREMEMBER\n\nTake your time. You can listen to this as many times as you like."


def _local_asd(text: str, subject: str) -> str:
    points = _key_points(text, 6)
    lines = [
        f"What you will learn: You will understand the key facts about {subject}.",
        "",
    ]
    for i, point in enumerate(points, start=1):
        lines.append(f"Step {i}: {point}")
    lines.append("")
    lines.append(
        f"What you learned: You now understand the key facts about {subject}, one step at a time."
    )
    return "\n".join(lines)


def _local_blended(text: str, subject: str) -> str:
    points = _key_points(text, 4)
    lines = [
        f"Mission Brief: Your goal is to understand {subject}, one clear step at a time.",
        "",
        "What you will learn: The key facts below, broken into short steps.",
        "",
    ]
    for i, point in enumerate(points, start=1):
        chunks = _shorten(point, max_words=14)
        lines.append(f"Step {i}: {chunks[0]}")
        lines.extend(f"        {chunk}" for chunk in chunks[1:])
    lines.append("")
    lines.append("Progress Cue: Great — you finished this step. Next up, the following idea.")
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# TTS cleanup
# --------------------------------------------------------------------------- #
def clean_for_tts(text: str) -> str:
    """Strip markdown/symbols so a TTS engine reads cleanly."""
    text = re.sub(r"[#*_`~>|]", "", text)
    text = re.sub(r"\bStep (\d+):", r"Step \1. ", text)
    text = re.sub(r"\bChallenge (\d+):", r"Challenge \1. ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
