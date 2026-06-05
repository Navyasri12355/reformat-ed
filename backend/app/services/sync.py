from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import CognitiveProfile, TransformedAtom, CurriculumAtom
from app.services.prompt_router import ProfileWeights, select_output_format
from app.tasks import run_transform


def sync_student_transforms(db: Session, student_id: str):
    profile = db.scalar(select(CognitiveProfile).where(CognitiveProfile.student_id == student_id))
    if not profile:
        return

    profile_weights = ProfileWeights(
        adhd=float(profile.adhd_weight),
        dyslexia=float(profile.dyslexia_weight),
        asd=float(profile.asd_weight),
    )
    new_format = select_output_format(profile_weights)

    # Find all TransformedAtoms for this student that don't match the new format
    outdated = db.scalars(
        select(TransformedAtom)
        .join(CurriculumAtom, CurriculumAtom.id == TransformedAtom.atom_id)
        .where(
            TransformedAtom.student_id == student_id,
            TransformedAtom.output_format != new_format,
        )
    ).all()

    if not outdated:
        return

    # Find the document IDs for the outdated transforms
    doc_ids = set()
    for ta in outdated:
        doc_ids.add(ta.atom.document_id)
        db.delete(ta)

    db.commit()  # commit deletes before running async tasks

    # Re-trigger transform for these documents
    for doc_id in doc_ids:
        run_transform(doc_id, student_id)
