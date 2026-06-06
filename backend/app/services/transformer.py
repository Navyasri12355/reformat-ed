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
from string import punctuation

from app import logging_config as log
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
            passed = validate_transform_output(
                atom["raw_text"], text, output_format
            ).passed

    text = finalize_transform_text(text, atom["raw_text"], output_format)
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
def _transform_with_openai(
    atom: dict, output_format: str, weights: ProfileWeights
) -> tuple[str, bool]:
    try:
        from openai import OpenAI
    except ImportError:  # pragma: no cover
        log.warning("openai_not_installed", hint="pip install openai")
        return _transform_locally(atom, output_format, weights), True

    client = OpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        timeout=settings.openai_timeout_seconds,
    )

    def call(fmt: str, strict: bool = False) -> str:
        system, user = prompt_loader.render(fmt, atom)
        if strict:
            system += (
                "\n\nYOUR PREVIOUS OUTPUT FAILED VALIDATION. Follow every rule exactly."
            )
        resp = client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=settings.openai_temperature,
            max_tokens=2048,
        )
        return (resp.choices[0].message.content or "").strip()

    try:
        if output_format == "blended":
            primary_trait, secondary_trait = (t for t, _ in ranked_traits(weights)[:2])
            from app.services.prompt_router import FORMAT_FOR_TRAIT

            text_a = call(FORMAT_FOR_TRAIT[primary_trait])
            text_b = call(FORMAT_FOR_TRAIT[secondary_trait])
            text = _blend_with_openai(
                client, text_a, text_b, FORMAT_FOR_TRAIT[secondary_trait]
            )
        else:
            text = call(output_format)

        result = validate_transform_output(atom["raw_text"], text, output_format)
        if not result.passed and output_format != "blended":
            text = call(output_format, strict=True)
            result = validate_transform_output(atom["raw_text"], text, output_format)

        if not result.passed:
            # Guarantee a valid, on-format result regardless of model behaviour.
            text = _transform_locally(atom, output_format, weights)
            return text, validate_transform_output(
                atom["raw_text"], text, output_format
            ).passed
        return text, True
    except Exception as exc:  # network / rate-limit / API error → safe local fallback
        log.error(
            "openai_transform_failed", error=str(exc), model=settings.openai_model
        )
        text = _transform_locally(atom, output_format, weights)
        return text, validate_transform_output(
            atom["raw_text"], text, output_format
        ).passed


def _blend_with_openai(
    client, version_a: str, version_b: str, second_format: str
) -> str:
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
        max_tokens=2048,
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


_MAX_POINTS = 5
_ADHD_POINTS = 3
_ASD_POINTS = 4
_BLENDED_POINTS = 4
_DYSLEXIA_SENTENCES = 3


def _sentences(text: str) -> list[str]:
    """All non-empty sentences of an atom — never truncated, never broken."""
    out = [
        normalise_sentence(s) for s in (split_sentences(text) or [text]) if s.strip()
    ]
    return out or [normalise_sentence(text.strip())]


def normalise_sentence(sentence: str) -> str:
    sentence = re.sub(r"\s+", " ", sentence or "").strip()
    if not sentence:
        return sentence
    if sentence[-1] not in ".!?":
        sentence = sentence.rstrip(punctuation + " ") + "."
    return sentence


def _readable(sentence: str, max_words: int = 22) -> str:
    """Keep a sentence whole. If it is very long, soften it by turning clause
    boundaries (commas/semicolons) into sentence stops — WITHOUT cutting words
    or fabricating breaks mid-clause."""
    if len(sentence.split()) <= max_words:
        return sentence
    softened = re.sub(r"\s*[;:]\s+", ". ", sentence)
    softened = re.sub(
        r",\s+(?=(and|but|which|where|while|so|because)\b)", ". ", softened
    )
    return softened


def _focus_points(text: str, limit: int) -> list[str]:
    points = _sentences(text)
    cleaned = [re.sub(r"\s+", " ", p).strip() for p in points if p.strip()]
    return cleaned[:limit] or cleaned[:1]


def _plain_rephrase(sentence: str) -> str:
    sentence = _readable(sentence, max_words=16)
    sentence = re.sub(
        r"\bprovides important information about\b", "shows", sentence, flags=re.I
    )
    sentence = re.sub(r"\bis a collection of\b", "includes", sentence, flags=re.I)
    sentence = re.sub(r"\bwith a wide range of\b", "with many", sentence, flags=re.I)
    sentence = re.sub(
        r"\bphysiochemical\b", "physical and chemical", sentence, flags=re.I
    )
    return normalise_sentence(sentence)


def _local_adhd(text: str, subject: str) -> str:
    points = [_plain_rephrase(p) for p in _focus_points(text, _ADHD_POINTS)]
    lines = [f"Mission Brief: Learn the main idea of {subject} in 3 quick moves."]
    for i, point in enumerate(points, start=1):
        lines.append(f"Challenge {i}: {point}")
    lines.append(
        "Progress Cue: Good job. You finished the important part of this section."
    )
    return "\n".join(lines)


def _local_dyslexia(text: str, subject: str) -> str:
    points = [_plain_rephrase(p) for p in _focus_points(text, _DYSLEXIA_SENTENCES)]
    body = "\n".join(points)
    return (
        "KEY IDEA\n\n"
        f"{body}\n\n"
        "REMEMBER\n\n"
        "Take your time. Listen again if you need to."
    )


def _local_asd(text: str, subject: str) -> str:
    points = [_plain_rephrase(p) for p in _focus_points(text, _ASD_POINTS)]
    lines = [
        f"What you will learn: You will learn the key facts about {subject} in a fixed order.",
        "",
    ]
    for i, point in enumerate(points, start=1):
        lines.append(f"Step {i}: {point}")
    lines.append("")
    lines.append(
        f"What you learned: You reviewed {len(points)} key facts about {subject}."
    )
    return "\n".join(lines)


def _local_blended(text: str, subject: str) -> str:
    points = [_plain_rephrase(p) for p in _focus_points(text, _BLENDED_POINTS)]
    lines = [
        f"Mission Brief: Learn the main ideas of {subject} in short, clear steps.",
        "",
        "What you will learn: The most important ideas only.",
        "",
    ]
    for i, point in enumerate(points, start=1):
        lines.append(f"Step {i}: {point}")
    lines.append("")
    lines.append(
        "Progress Cue: You finished this short section. Move on when you are ready."
    )
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# TTS cleanup
# --------------------------------------------------------------------------- #
def strip_markdown(text: str) -> str:
    """Remove markdown formatting that LLMs add (so it never shows as literal
    `**`, `#`, backticks, list bullets) while keeping the words and line breaks."""
    if not text:
        return text
    # Bold/italic markers: **x**, __x__, *x*, _x_  → x
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"__(.+?)__", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    text = re.sub(r"(?<!\w)_(.+?)_(?!\w)", r"\1", text)
    text = re.sub(r"`{1,3}([^`]*)`{1,3}", r"\1", text)
    # Leading heading hashes and list bullets at line starts.
    text = re.sub(r"(?m)^\s{0,3}#{1,6}\s*", "", text)
    text = re.sub(r"(?m)^\s*[-*+]\s+", "", text)
    # Any stray remaining bold/italic asterisks/underscores.
    text = text.replace("**", "").replace("__", "")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def finalize_transform_text(text: str, original_text: str, output_format: str) -> str:
    text = strip_markdown(text)
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    cleaned: list[str] = []
    for line in lines:
        if not line:
            if cleaned and cleaned[-1] != "":
                cleaned.append("")
            continue
        header_match = re.match(
            r"^((?:Mission Brief|Progress Cue|What you will learn|What you learned|Key Idea|Remember)):\s*(.*)$",
            line,
            re.I,
        )
        step_match = re.match(
            r"^((?:Step|Challenge)\s*\d+)\s*[:.)-]?\s*(.*)$", line, re.I
        )
        if header_match:
            label, body = header_match.groups()
            body = normalise_sentence(body) if body else ""
            cleaned.append(f"{label}: {body}".strip())
        elif step_match:
            label, body = step_match.groups()
            body = normalise_sentence(body) if body else ""
            cleaned.append(f"{label}: {body}".strip())
        else:
            cleaned.append(normalise_sentence(line))
    final = "\n".join(cleaned).strip()
    return (
        final
        if final
        else _transform_locally(
            {"raw_text": original_text, "subject": "this topic"},
            output_format,
            ProfileWeights(0.0, 0.0, 0.0),
        )
    )


def clean_for_tts(text: str) -> str:
    """Strip markdown/symbols so a TTS engine reads cleanly."""
    text = re.sub(r"[#*_`~>|]", "", text)
    text = re.sub(r"\bStep (\d+):", r"Step \1. ", text)
    text = re.sub(r"\bChallenge (\d+):", r"Challenge \1. ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
