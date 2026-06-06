"""Batch transformation: rewrite every atom of a document for one student.

"Prepare for me" (re)generates content. The first time a document is prepared
in this server run it is re-extracted with the current atomiser (so previously
uploaded lessons pick up parser/atomiser improvements without re-uploading), and
each atom's transform is regenerated in place — so clicking Prepare again is a
genuine "re-generate" rather than a no-op.
"""

from __future__ import annotations

from sqlalchemy import select

from app import logging_config as log
from app.config import settings
from app.database import session_scope
from app.models import CognitiveProfile, CurriculumAtom, SourceDocument, TransformedAtom
from app.services.ingestion import reprocess_document
from app.services.prompt_router import ProfileWeights
from app.services.transformer import transform_atom

# Documents already re-extracted with the latest atomiser during this run.
_reprocessed: set[str] = set()


def transform_document_for_student(
    document_id: str, student_id: str, force_auto_approve: bool = False
) -> dict:
    # Refresh the document's atoms with the current atomiser the first time it is
    # prepared this run, so older uploads improve without a manual re-upload.
    if document_id not in _reprocessed:
        try:
            reprocess_document(document_id)
        except Exception as exc:  # noqa: BLE001 - non-fatal; fall back to existing atoms
            log.error("reprocess_failed", document_id=document_id, error=str(exc))
        _reprocessed.add(document_id)

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
        status = "auto_approved" if auto_approve else "pending"

        atoms = db.scalars(
            select(CurriculumAtom)
            .where(CurriculumAtom.document_id == document_id)
            .order_by(CurriculumAtom.sequence_index)
        ).all()

        processed = 0
        for atom in atoms:
            result = transform_atom(
                {
                    "raw_text": atom.raw_text,
                    "subject": atom.subject,
                    "grade_level": atom.grade_level,
                    "bloom_level": atom.bloom_level,
                },
                weights,
            )

            existing = db.scalar(
                select(TransformedAtom).where(
                    TransformedAtom.atom_id == atom.id,
                    TransformedAtom.student_id == student_id,
                )
            )
            if existing is not None:
                # Regenerate in place (keeps any session-event references intact).
                existing.adhd_weight = profile.adhd_weight
                existing.dyslexia_weight = profile.dyslexia_weight
                existing.asd_weight = profile.asd_weight
                existing.output_format = result.output_format
                existing.transformed_text = result.transformed_text
                existing.audio_script = result.audio_script
                existing.meta = result.meta
                existing.review_status = status
                existing.reviewed_by = None
                existing.reviewed_at = None
                existing.rejection_note = None
                existing.llm_model = result.model
                existing.prompt_version = result.prompt_version
                existing.generation_ms = result.generation_ms
                existing.validation_passed = result.validation_passed
            else:
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
                        review_status=status,
                        llm_model=result.model,
                        prompt_version=result.prompt_version,
                        generation_ms=result.generation_ms,
                        validation_passed=result.validation_passed,
                    )
                )
            # Commit per atom so the student can begin the first segment while
            # the rest are still generating (responsive on long documents).
            db.commit()
            processed += 1

        return {"document_id": document_id, "student_id": student_id, "created": processed}
