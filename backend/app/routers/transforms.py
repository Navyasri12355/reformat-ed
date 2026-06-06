"""Transformation endpoints: request a batch, fetch a student's content, and the
educator review queue + approve/reject workflow."""

from __future__ import annotations

import uuid
import re
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
    StudentFeedback,
)
from app.schemas import (
    ReviewDecision,
    ReviewQueueItem,
    ReviewQueueResponse,
    StudentContentResponse,
    TransformBatchResponse,
    TransformedAtomOut,
    TransformRequest,
    SupportRequest,
    SupportResponse,
    FeedbackCreate,
)
from app.config import settings
from app.services.transformer import clean_for_tts
from app.services.atomiser import split_sentences

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

    # A student preparing their OWN material is self-study — no educator review
    # gate. Educator-initiated transforms still go through the review queue.
    self_study = actor.role == "student" and student_id == actor.id
    task_id = run_transform(body.document_id, student_id, force_auto_approve=self_study)
    auto_approve = (
        self_study
        or settings.auto_approve_all
        or bool(doc.institution and doc.institution.auto_approve_transforms)
    )

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


def clean_support_response(text: str) -> str:
    if not text:
        return ""

    cleaned = text.strip()
    # Remove a few common templating prefixes but avoid stripping full
    # sentences. Only remove short lead-ins.
    cleaned = re.sub(r'^(Tutor[:\-]\s*)', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'^(Here is an even simpler summary of this section[:\-]?\s*)', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'^(Here is a simpler summary[:\-]?\s*)', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'^(To understand[:\-]?\s*)', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'^(The main idea is[:\-]?\s*)', '', cleaned, flags=re.IGNORECASE)
    # Remove templated bullet labels that LLMs sometimes emit, e.g. '• Concept:'
    cleaned = re.sub(r'(?m)^[\s\u2022\*\-]*\s*(Concept|Detail|Action|Note)\s*[:\-]\s*', '', cleaned, flags=re.IGNORECASE)
    # Strip stray leading bullet characters
    cleaned = re.sub(r'(?m)^\s*[\u2022\*\-]+\s*', '', cleaned)
    return cleaned.strip()


def strip_support_text(text: str) -> str:
    text = text or ""
    text = re.sub(r'(?mi)^(KEY IDEA|REMEMBER|MISSION BRIEF|PROGRESS CUE|WHAT YOU WILL LEARN|WHAT YOU LEARNED|GOAL)\s*[:\-]?\s*', '', text)
    text = re.sub(r'(?m)^\s*[-*\u2022]+\s*', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def is_generic_support(text: str) -> bool:
    if not text or len(text.strip()) < 10:
        return True
    text = text.strip()
    if re.search(r'^(here is|to understand|the main idea is|concept|detail|action|note)\b', text, flags=re.IGNORECASE):
        return True
    if re.search(r'\b(key fact|main idea|important point|important idea)\b', text, flags=re.IGNORECASE) and len(text.split()) < 15:
        return True
    return False


def get_support_source_text(ta: TransformedAtom) -> str:
    source = ""
    if getattr(ta, 'atom', None) is not None and getattr(ta.atom, 'raw_text', None):
        source = ta.atom.raw_text
    if not source:
        source = ta.transformed_text or ""
    return strip_support_text(source)


def generate_support_response(ta: TransformedAtom, question: str | None, db: Session) -> str:
    output_format = ta.output_format

    if settings.openai_api_key:
        try:
            from openai import OpenAI
            client = OpenAI(
                api_key=settings.openai_api_key,
                base_url=settings.openai_base_url,
                timeout=settings.openai_timeout_seconds,
            )

            source_text = get_support_source_text(ta)
            transformed_text = strip_support_text(ta.transformed_text or "")

            if question:
                system_prompt = (
                    f"You are a supportive, friendly neurodivergent-friendly tutor for a student. "
                    f"The student's preferred format is {output_format} (ASD/ADHD/dyslexia). "
                    f"Answer the student's question about the topic in a way that matches this learning style: "
                    f"- For asd_structured: literal, clear, structured, step-by-step, no idioms/metaphors. "
                    f"- For adhd_gamified: short, punchy, engaging, action-oriented, highlighting key points. "
                    f"- For dyslexia_audio: short sentences (max 15 words), simple vocabulary, easy to read/listen. "
                    f"- For blended: balanced, short steps, clear goal. "
                    f"Keep the answer concise (under 120 words). "
                    f"Do not preface the answer with reasoning, introspection, or phrases like 'To understand' or 'Here is'."
                )
                user_prompt = (
                    f"Use the original material and the student-facing rewritten text to answer the question. "
                    f"If the rewritten text contains headings like KEY IDEA or REMEMBER, ignore those labels and focus on the actual content.\n\n"
                    f"Original source text:\n---\n{source_text}\n---\n\n"
                    f"Student-facing text:\n---\n{transformed_text}\n---\n\n"
                    f"Student's question:\n\"{question}\"\n\n"
                    f"Answer the question directly, accurately, and in the requested style."
                )
            else:
                system_prompt = (
                    f"You are a supportive, friendly neurodivergent-friendly tutor. "
                    f"Explain the following original material in an even simpler, more accessible way. "
                    f"Ignore headings like KEY IDEA or REMEMBER and summarize the core meaning. "
                    f"Do not include meta commentary, model reasoning, or phrases like 'To understand' or 'Here is'. "
                    f"Keep the response direct, short, and easy to read. "
                    f"Tailor the explanation format to the student's preferred format: {output_format}.\n"
                    f"- For asd_structured: literal, structured, step-by-step. "
                    f"- For adhd_gamified: brief challenges, active second-person voice. "
                    f"- For dyslexia_audio: short paragraphs, short sentences (max 15 words), plain vocabulary. "
                    f"Keep it very brief (under 150 words)."
                )
                user_prompt = (
                    f"Original source text:\n---\n{source_text}\n---"
                )

            resp = client.chat.completions.create(
                model=settings.openai_model,
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
                temperature=0.4,
                max_tokens=300,
            )
            answer = clean_support_response(resp.choices[0].message.content or "")
            if not answer or is_generic_support(answer):
                raise ValueError("OpenAI returned a generic or placeholder support response")
            return answer
        except Exception:
            pass

    # Deterministic local fallback — produce a short, factual summary from the
    # original source text rather than the rewritten presentation text.
    def short_summary(text: str, max_sentences: int = 2) -> str:
        sents = split_sentences(text) or [text]
        out = " ".join([s.strip() for s in sents[:max_sentences]])
        return out.strip()

    fallback_text = get_support_source_text(ta)
    if question:
        answer = short_summary(fallback_text, max_sentences=2)
        return clean_support_response(
            f"{answer}\n\nIf you'd like more detail, ask a follow-up question."
        )
    else:
        summary = short_summary(fallback_text, max_sentences=2)
        return clean_support_response(
            f"{summary}\n\nAction: Take a moment to review this idea, or listen to the audio readout."
        )


@router.post("/{transformed_atom_id}/support", response_model=SupportResponse)
def get_tutor_support(
    transformed_atom_id: str,
    body: SupportRequest,
    actor: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SupportResponse:
    ta = db.get(TransformedAtom, transformed_atom_id)
    if ta is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Transformed atom not found")

    response_text = generate_support_response(ta, body.question, db)
    return SupportResponse(response=response_text)


@router.post("/{transformed_atom_id}/feedback", status_code=status.HTTP_201_CREATED)
def submit_student_feedback(
    transformed_atom_id: str,
    body: FeedbackCreate,
    actor: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    ta = db.get(TransformedAtom, transformed_atom_id)
    if ta is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Transformed atom not found")

    feedback = StudentFeedback(
        transformed_atom_id=ta.id,
        student_id=actor.id,
        message=body.message.strip(),
    )
    db.add(feedback)
    db.commit()
    return {"status": "success", "feedback_id": feedback.id}
