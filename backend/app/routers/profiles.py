"""Cognitive profile endpoints: onboarding quiz, read, educator override, history."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import CognitiveProfile, CognitiveProfileSnapshot, User
from app.schemas import (
    ProfileSnapshotOut,
    ProfileUpdateRequest,
    ProfileWeightsOut,
    QuizQuestionOut,
    QuizSubmission,
)
from app.services.quiz_engine import QUIZ_QUESTIONS, compute_profile_from_quiz

router = APIRouter(prefix="/profiles", tags=["profiles"])


def _ensure_access(actor: User, student_id: str, db: Session) -> User:
    """Students may only touch their own profile; educators/admins may touch
    students within their institution."""
    student = db.get(User, student_id)
    if student is None or student.role != "student":
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Student not found")
    if actor.role == "student" and actor.id != student_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Cannot access another student's profile")
    if actor.role == "educator" and actor.institution_id != student.institution_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Student is outside your institution")
    return student


def _get_or_create_profile(db: Session, student_id: str) -> CognitiveProfile:
    profile = db.scalar(select(CognitiveProfile).where(CognitiveProfile.student_id == student_id))
    if profile is None:
        profile = CognitiveProfile(student_id=student_id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


@router.get("/quiz", response_model=list[QuizQuestionOut])
def get_quiz() -> list[QuizQuestionOut]:
    return [QuizQuestionOut(id=q.id, text=q.text) for q in QUIZ_QUESTIONS]


@router.post("/{student_id}/quiz", response_model=ProfileWeightsOut)
def submit_quiz(
    student_id: str,
    body: QuizSubmission,
    actor: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CognitiveProfile:
    _ensure_access(actor, student_id, db)
    weights = compute_profile_from_quiz(body.answers)
    profile = _get_or_create_profile(db, student_id)

    _snapshot(db, profile, reason="pre_quiz_recalibration")
    profile.adhd_weight = float(weights["adhd_weight"])
    profile.dyslexia_weight = float(weights["dyslexia_weight"])
    profile.asd_weight = float(weights["asd_weight"])
    profile.profile_version += 1
    profile.calibration_source = "onboarding"
    profile.last_calibrated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(profile)
    return profile


@router.get("/{student_id}", response_model=ProfileWeightsOut)
def get_profile(
    student_id: str,
    actor: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CognitiveProfile:
    _ensure_access(actor, student_id, db)
    return _get_or_create_profile(db, student_id)


@router.put("/{student_id}", response_model=ProfileWeightsOut)
def update_profile(
    student_id: str,
    body: ProfileUpdateRequest,
    actor: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CognitiveProfile:
    if actor.role not in ("educator", "admin"):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only educators may override profiles")
    _ensure_access(actor, student_id, db)
    profile = _get_or_create_profile(db, student_id)

    _snapshot(db, profile, reason=body.snapshot_reason or "educator_override")
    profile.adhd_weight = body.adhd_weight
    profile.dyslexia_weight = body.dyslexia_weight
    profile.asd_weight = body.asd_weight
    profile.profile_version += 1
    profile.calibration_source = body.calibration_source
    profile.last_calibrated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(profile)
    return profile


@router.get("/{student_id}/history", response_model=list[ProfileSnapshotOut])
def profile_history(
    student_id: str,
    actor: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[CognitiveProfileSnapshot]:
    _ensure_access(actor, student_id, db)
    profile = _get_or_create_profile(db, student_id)
    return list(
        db.scalars(
            select(CognitiveProfileSnapshot)
            .where(CognitiveProfileSnapshot.profile_id == profile.id)
            .order_by(CognitiveProfileSnapshot.created_at.desc())
        ).all()
    )


def _snapshot(db: Session, profile: CognitiveProfile, reason: str) -> None:
    db.add(
        CognitiveProfileSnapshot(
            profile_id=profile.id,
            adhd_weight=profile.adhd_weight,
            dyslexia_weight=profile.dyslexia_weight,
            asd_weight=profile.asd_weight,
            profile_version=profile.profile_version,
            snapshot_reason=reason,
        )
    )
