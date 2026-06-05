"""Transformation endpoints: request a batch, fetch a student's content, and the
educator review queue + approve/reject workflow."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth import get_current_user, require_educator
from app.database import get_db
from app.models import (
    CognitiveProfile,
    CurriculumAtom,
    SourceDocument,
    TransformedAtom,
    User,
)
from app.schemas import (
    ReviewDecision,
    ReviewQueueItem,
    ReviewQueueResponse,
    StudentContentResponse,
    TransformBatchResponse,
    TransformedAtomOut,
    TransformRequest,
)
from app.services.transformer import clean_for_tts
from app.tasks import run_transform

router = APIRouter(prefix="/transforms", tags=["transforms"])


@router.post("", response_model=TransformBatchResponse, status_code=status.HTTP_202_ACCEPTED)
def request_transform(
    body: TransformRequest,
    actor: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TransformBatchResponse:
    # Resolve the target student.
    if actor.role == "student":
        student_id = actor.id
    else:
        if not body.student_id:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "student_id required for educators")
        student_id = body.student_id

    doc = db.get(SourceDocument, body.document_id)
    if doc is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
    if doc.parse_status != "complete":
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Document is not ready (parse_status={doc.parse_status})",
        )

    profile = db.scalar(select(CognitiveProfile).where(CognitiveProfile.student_id == student_id))
    if profile is None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Student has no cognitive profile yet — complete the onboarding quiz first",
        )

    atom_count = db.scalar(
        select(func.count()).select_from(CurriculumAtom).where(
            CurriculumAtom.document_id == body.document_id
        )
    ) or 0

    task_id = run_transform(body.document_id, student_id)
    auto_approve = bool(doc.institution and doc.institution.auto_approve_transforms)

    return TransformBatchResponse(
        transform_batch_id=uuid.uuid4().hex,
        document_id=body.document_id,
        student_id=student_id,
        atom_count=atom_count,
        task_ids=[task_id],
        review_required=not auto_approve,
    )


@router.get("", response_model=StudentContentResponse)
def get_student_content(
    document_id: str = Query(...),
    student_id: str | None = Query(None),
    actor: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StudentContentResponse:
    target = student_id or (actor.id if actor.role == "student" else None)
    if target is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "student_id required")
    if actor.role == "student" and target != actor.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Cannot view another student's content")

    profile = db.scalar(select(CognitiveProfile).where(CognitiveProfile.student_id == target))
    profile_snapshot = {
        "adhd_weight": float(profile.adhd_weight) if profile else 0.0,
        "dyslexia_weight": float(profile.dyslexia_weight) if profile else 0.0,
        "asd_weight": float(profile.asd_weight) if profile else 0.0,
    }

    rows = db.execute(
        select(TransformedAtom, CurriculumAtom.sequence_index)
        .join(CurriculumAtom, CurriculumAtom.id == TransformedAtom.atom_id)
        .where(
            CurriculumAtom.document_id == document_id,
            TransformedAtom.student_id == target,
        )
        .order_by(CurriculumAtom.sequence_index)
    ).all()

    # Students only ever receive approved/auto-approved content (enforced here,
    # at the delivery layer). Educators viewing a student see everything.
    visible_statuses = {"approved", "auto_approved"}
    atoms: list[TransformedAtomOut] = []
    for ta, seq in rows:
        if actor.role == "student" and ta.review_status not in visible_statuses:
            continue
        atoms.append(
            TransformedAtomOut(
                id=ta.id,
                atom_id=ta.atom_id,
                sequence_index=seq,
                output_format=ta.output_format,
                transformed_text=ta.transformed_text,
                audio_script=ta.audio_script,
                meta=ta.meta,
                review_status=ta.review_status,
            )
        )

    return StudentContentResponse(
        document_id=document_id,
        student_id=target,
        profile_snapshot=profile_snapshot,
        atoms=atoms,
    )


@router.get("/review-queue", response_model=ReviewQueueResponse)
def review_queue(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    educator: User = Depends(require_educator),
    db: Session = Depends(get_db),
) -> ReviewQueueResponse:
    base = (
        select(TransformedAtom, CurriculumAtom, SourceDocument)
        .join(CurriculumAtom, CurriculumAtom.id == TransformedAtom.atom_id)
        .join(SourceDocument, SourceDocument.id == CurriculumAtom.document_id)
        .where(TransformedAtom.review_status == "pending")
    )
    if educator.role != "admin":
        base = base.where(SourceDocument.uploaded_by == educator.id)

    total = db.scalar(select(func.count()).select_from(base.subquery())) or 0
    rows = db.execute(
        base.order_by(TransformedAtom.created_at.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    items = [
        ReviewQueueItem(
            transformed_atom_id=ta.id,
            atom_id=ca.id,
            output_format=ta.output_format,
            review_status=ta.review_status,
            atom_preview=ca.raw_text[:200],
            transform_preview=ta.transformed_text[:200],
            file_name=sd.file_name,
            created_at=ta.created_at,
        )
        for ta, ca, sd in rows
    ]
    return ReviewQueueResponse(items=items, total=total, page=page)


@router.post("/{transformed_atom_id}/review")
def review_transform(
    transformed_atom_id: str,
    decision: ReviewDecision,
    educator: User = Depends(require_educator),
    db: Session = Depends(get_db),
) -> dict:
    ta = db.get(TransformedAtom, transformed_atom_id)
    if ta is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Transformed atom not found")

    # Verify the educator owns the source document (or is admin).
    doc = ta.atom.document
    if educator.role != "admin" and doc.uploaded_by != educator.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not your document")

    if decision.action == "approve":
        ta.review_status = "approved"
        if decision.edited_text:
            ta.transformed_text = decision.edited_text
            ta.audio_script = clean_for_tts(decision.edited_text)
    else:
        ta.review_status = "rejected"
        ta.rejection_note = decision.rejection_note

    ta.reviewed_by = educator.id
    ta.reviewed_at = datetime.now(timezone.utc)
    db.commit()
    return {"transformed_atom_id": ta.id, "review_status": ta.review_status}
