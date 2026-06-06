"""Batch transformation: rewrite every atom of a document for one student.

Invoked inline (background thread) or from a Celery task. Idempotent per
(atom, student): existing transforms for the pair are skipped so re-running is
safe.
"""

from __future__ import annotations

from sqlalchemy import select

from app.config import settings
from app.database import session_scope
from app.models import CognitiveProfile, CurriculumAtom, SourceDocument, TransformedAtom, User
from app.services.prompt_router import ProfileWeights
from app.services.transformer import transform_atom


def transform_document_for_student(
    document_id: str, student_id: str, force_auto_approve: bool = False
) -> dict:
    with session_scope() as db:
        doc = db.get(SourceDocument, document_id)
        if doc is None:
            raise ValueError(f"Document {document_id} not found")

        profile = db.scalar(
            select(CognitiveProfile).where(CognitiveProfile.student_id == student_id)
        )
        if profile is None:
            raise ValueError(f"Student {student_id} has no cognitive profile")

        weights = ProfileWeights(
            adhd=float(profile.adhd_weight),
            dyslexia=float(profile.dyslexia_weight),
            asd=float(profile.asd_weight),
        )

        auto_approve = settings.auto_approve_all or force_auto_approve
        if not auto_approve and doc.institution_id:
            inst = doc.institution
            auto_approve = bool(inst and inst.auto_approve_transforms)

        atoms = db.scalars(
            select(CurriculumAtom)
            .where(CurriculumAtom.document_id == document_id)
            .order_by(CurriculumAtom.sequence_index)
        ).all()

        created = 0
        for atom in atoms:
            existing = db.scalar(
                select(TransformedAtom).where(
                    TransformedAtom.atom_id == atom.id,
                    TransformedAtom.student_id == student_id,
                )
            )
            if existing is not None:
                continue

            result = transform_atom(
                {
                    "raw_text": atom.raw_text,
                    "subject": atom.subject,
                    "grade_level": atom.grade_level,
                    "bloom_level": atom.bloom_level,
                },
                weights,
            )

            db.add(
                TransformedAtom(
                    atom_id=atom.id,
                    student_id=student_id,
                    adhd_weight=profile.adhd_weight,
                    dyslexia_weight=profile.dyslexia_weight,
                    asd_weight=profile.asd_weight,
                    output_format=result.output_format,
                    transformed_text=result.transformed_text,
                    audio_script=result.audio_script,
                    meta=result.meta,
                    review_status="auto_approved" if auto_approve else "pending",
                    llm_model=result.model,
                    prompt_version=result.prompt_version,
                    generation_ms=result.generation_ms,
                    validation_passed=result.validation_passed,
                )
            )
            # Commit per atom so the student can begin the first segment while
            # the rest are still generating (responsive on long documents).
            db.commit()
            created += 1

        return {"document_id": document_id, "student_id": student_id, "created": created}
