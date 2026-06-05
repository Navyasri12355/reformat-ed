"""Learning-session lifecycle and append-only behavioural signal ingest."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth import get_current_user, require_student
from app.database import get_db
from app.models import CurriculumAtom, LearningSession, SessionEvent, SourceDocument, User
from app.schemas import SessionEventRequest, SessionOut, SessionStartRequest
from app.services.adapt import recalibrate_profile

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", response_model=SessionOut, status_code=status.HTTP_201_CREATED)
def start_session(
    body: SessionStartRequest,
    student: User = Depends(require_student),
    db: Session = Depends(get_db),
) -> LearningSession:
    if db.get(SourceDocument, body.document_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
    total_atoms = db.scalar(
        select(func.count()).select_from(CurriculumAtom).where(
            CurriculumAtom.document_id == body.document_id
        )
    ) or 0
    session = LearningSession(
        student_id=student.id,
        document_id=body.document_id,
        total_atoms=total_atoms,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.post("/{session_id}/events", status_code=status.HTTP_204_NO_CONTENT)
def record_event(
    session_id: str,
    body: SessionEventRequest,
    student: User = Depends(require_student),
    db: Session = Depends(get_db),
) -> Response:
    session = db.get(LearningSession, session_id)
    if session is None or session.student_id != student.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Session not found")

    db.add(
        SessionEvent(
            session_id=session_id,
            student_id=student.id,
            atom_id=body.atom_id,
            transformed_atom_id=body.transformed_atom_id,
            event_type=body.event_type,
            time_on_atom_ms=body.time_on_atom_ms,
            retry_count=body.retry_count,
            payload=body.payload or None,
        )
    )
    if body.event_type == "atom_complete":
        session.atoms_completed += 1
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{session_id}/end", response_model=SessionOut)
def end_session(
    session_id: str,
    student: User = Depends(require_student),
    db: Session = Depends(get_db),
) -> LearningSession:
    session = db.get(LearningSession, session_id)
    if session is None or session.student_id != student.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Session not found")
    session.ended_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(session)
    return session


@router.post("/recalibrate")
def trigger_recalibration(
    student: User = Depends(require_student),
    db: Session = Depends(get_db),
) -> dict:
    """On-demand recalibration for the current student (the same logic the weekly
    scheduled job runs for everyone)."""
    changed = recalibrate_profile(db, student.id)
    return {"recalibrated": changed}
