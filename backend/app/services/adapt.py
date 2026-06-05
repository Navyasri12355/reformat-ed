"""Adaptive feedback loop.

Reads append-only behavioural signals and nudges a student's trait weights
toward whichever format they engage with best. The numerical core is a pure
function (easy to unit-test); the DB wrapper applies it and snapshots history.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from statistics import mean

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import CognitiveProfile, CognitiveProfileSnapshot, SessionEvent, TransformedAtom

LEARNING_RATE = 0.15  # conservative — weights shift slowly
MIN_EVENTS = 10  # below this, not enough signal to recalibrate
MIN_EVENTS_PER_FORMAT = 3
MIN_DELTA = 0.02  # ignore negligible changes

FORMAT_TO_TRAIT = {
    "adhd_gamified": "adhd_weight",
    "dyslexia_audio": "dyslexia_weight",
    "asd_structured": "asd_weight",
}


@dataclass
class SignalEvent:
    event_type: str
    time_on_atom_ms: int | None
    retry_count: int | None
    output_format: str


def event_engagement_score(event: SignalEvent) -> float:
    """Normalised engagement score in [0, 1] for a single event.

    High = the student engaged well with this format; low = they struggled.
    """
    score = 0.5  # neutral baseline

    if event.event_type == "atom_complete":
        score += 0.3
        if event.retry_count == 0:
            score += 0.1
        if event.time_on_atom_ms and event.time_on_atom_ms > 15_000:
            score += 0.1
    elif event.event_type == "atom_skip":
        score -= 0.3
    elif event.event_type == "exit_mid_atom":
        score -= 0.2
    elif event.event_type == "atom_retry":
        score -= 0.1
    elif event.event_type == "audio_play" and event.output_format == "dyslexia_audio":
        score += 0.15

    return max(0.0, min(1.0, score))


def recalibrate_weights(
    events: list[SignalEvent], current_weights: dict[str, float]
) -> dict[str, float] | None:
    """Pure recalibration. Returns new weights, or None if no meaningful change.

    ``current_weights`` keys: adhd_weight, dyslexia_weight, asd_weight.
    """
    if len(events) < MIN_EVENTS:
        return None

    per_format: dict[str, list[float]] = {fmt: [] for fmt in FORMAT_TO_TRAIT}
    for event in events:
        if event.output_format in per_format:
            per_format[event.output_format].append(event_engagement_score(event))

    format_avg = {
        fmt: mean(scores)
        for fmt, scores in per_format.items()
        if len(scores) >= MIN_EVENTS_PER_FORMAT
    }
    if not format_avg:
        return None

    total = sum(format_avg.values())
    if total <= 0:
        return None

    new_weights = dict(current_weights)
    for fmt, avg_score in format_avg.items():
        trait = FORMAT_TO_TRAIT[fmt]
        signal = avg_score / total
        blended = (1 - LEARNING_RATE) * current_weights[trait] + LEARNING_RATE * signal
        new_weights[trait] = round(max(0.0, min(1.0, blended)), 3)

    delta = max(abs(new_weights[k] - current_weights[k]) for k in current_weights)
    if delta < MIN_DELTA:
        return None
    return new_weights


def recalibrate_profile(db: Session, student_id: str, window_days: int = 30) -> bool:
    """Apply recalibration for one student. Returns True if the profile changed."""
    profile = db.scalar(select(CognitiveProfile).where(CognitiveProfile.student_id == student_id))
    if profile is None:
        return False

    since = datetime.now(timezone.utc) - timedelta(days=window_days)
    rows = db.execute(
        select(
            SessionEvent.event_type,
            SessionEvent.time_on_atom_ms,
            SessionEvent.retry_count,
            TransformedAtom.output_format,
        )
        .join(TransformedAtom, TransformedAtom.id == SessionEvent.transformed_atom_id)
        .where(
            SessionEvent.student_id == student_id,
            SessionEvent.recorded_at >= since,
            SessionEvent.transformed_atom_id.is_not(None),
        )
    ).all()

    events = [
        SignalEvent(
            event_type=r.event_type,
            time_on_atom_ms=r.time_on_atom_ms,
            retry_count=r.retry_count,
            output_format=r.output_format,
        )
        for r in rows
    ]

    current = {
        "adhd_weight": float(profile.adhd_weight),
        "dyslexia_weight": float(profile.dyslexia_weight),
        "asd_weight": float(profile.asd_weight),
    }
    new_weights = recalibrate_weights(events, current)
    if new_weights is None:
        return False

    # Snapshot the current state before mutating (append-only history).
    db.add(
        CognitiveProfileSnapshot(
            profile_id=profile.id,
            adhd_weight=profile.adhd_weight,
            dyslexia_weight=profile.dyslexia_weight,
            asd_weight=profile.asd_weight,
            profile_version=profile.profile_version,
            snapshot_reason="pre_auto_recalibration",
        )
    )

    profile.adhd_weight = new_weights["adhd_weight"]
    profile.dyslexia_weight = new_weights["dyslexia_weight"]
    profile.asd_weight = new_weights["asd_weight"]
    profile.profile_version += 1
    profile.last_calibrated_at = datetime.now(timezone.utc)
    profile.calibration_source = "auto"
    db.commit()
    return True
