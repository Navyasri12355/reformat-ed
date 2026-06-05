"""Educator analytics — per-student, per-atom engagement for a document."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.auth import require_educator
from app.database import get_db
from app.models import (
    CurriculumAtom,
    SessionEvent,
    SourceDocument,
    TransformedAtom,
    User,
    StudentFeedback,
)
from app.schemas import AtomAnalyticsRow, FeedbackOut

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/{document_id}", response_model=list[AtomAnalyticsRow])
def document_analytics(
    document_id: str,
    educator: User = Depends(require_educator),
    db: Session = Depends(get_db),
) -> list[AtomAnalyticsRow]:
    doc = db.get(SourceDocument, document_id)
    if doc is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
    if educator.role != "admin" and doc.uploaded_by != educator.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not your document")

    completions = func.sum(case((SessionEvent.event_type == "atom_complete", 1), else_=0))
    retries = func.sum(case((SessionEvent.event_type == "atom_retry", 1), else_=0))
    exits = func.sum(case((SessionEvent.event_type == "exit_mid_atom", 1), else_=0))
    avg_time = func.avg(
        case((SessionEvent.event_type == "atom_complete", SessionEvent.time_on_atom_ms))
    )

    rows = db.execute(
        select(
            SessionEvent.student_id,
            User.display_name,
            SessionEvent.atom_id,
            CurriculumAtom.sequence_index,
            TransformedAtom.output_format,
            completions.label("completions"),
            retries.label("retries"),
            exits.label("exits"),
            avg_time.label("avg_time_ms"),
        )
        .join(User, User.id == SessionEvent.student_id)
        .join(CurriculumAtom, CurriculumAtom.id == SessionEvent.atom_id)
        .join(TransformedAtom, TransformedAtom.id == SessionEvent.transformed_atom_id, isouter=True)
        .where(CurriculumAtom.document_id == document_id)
        .group_by(
            SessionEvent.student_id,
            User.display_name,
            SessionEvent.atom_id,
            CurriculumAtom.sequence_index,
            TransformedAtom.output_format,
        )
        .order_by(CurriculumAtom.sequence_index, User.display_name)
    ).all()

    return [
        AtomAnalyticsRow(
            student_id=r.student_id,
            student_name=r.display_name,
            atom_id=r.atom_id,
            sequence_index=r.sequence_index,
            output_format=r.output_format,
            completions=int(r.completions or 0),
            retries=int(r.retries or 0),
            exits=int(r.exits or 0),
            avg_time_ms=float(r.avg_time_ms) if r.avg_time_ms is not None else None,
        )
        for r in rows
    ]


@router.get("/{document_id}/feedback", response_model=list[FeedbackOut])
def get_document_feedback(
    document_id: str,
    educator: User = Depends(require_educator),
    db: Session = Depends(get_db),
) -> list[FeedbackOut]:
    doc = db.get(SourceDocument, document_id)
    if doc is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
    if educator.role != "admin" and doc.uploaded_by != educator.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not your document")

    feedbacks = db.execute(
        select(
            StudentFeedback.id,
            User.display_name.label("student_name"),
            CurriculumAtom.sequence_index,
            StudentFeedback.message,
            StudentFeedback.created_at,
        )
        .join(User, User.id == StudentFeedback.student_id)
        .join(TransformedAtom, TransformedAtom.id == StudentFeedback.transformed_atom_id)
        .join(CurriculumAtom, CurriculumAtom.id == TransformedAtom.atom_id)
        .where(CurriculumAtom.document_id == document_id)
        .order_by(StudentFeedback.created_at.desc())
    ).all()

    return [
        FeedbackOut(
            id=f.id,
            student_name=f.student_name,
            sequence_index=f.sequence_index,
            message=f.message,
            created_at=f.created_at,
        )
        for f in feedbacks
    ]
