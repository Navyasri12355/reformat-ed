"""Ingestion orchestration: parse a stored document into curriculum atoms.

This is the synchronous worker body. It is invoked either inline (background
thread) or from a Celery task — both call :func:`ingest_document`.
"""

from __future__ import annotations

from sqlalchemy import delete, select

from app.config import settings
from app.database import session_scope
from app.models import CurriculumAtom, SessionEvent, SourceDocument, TransformedAtom
from app.services import parsers, storage
from app.services.atomiser import CurriculumAtomiser


def ingest_document(document_id: str) -> dict:
    """Parse → atomise → persist atoms. Updates parse_status throughout."""
    with session_scope() as db:
        doc = db.get(SourceDocument, document_id)
        if doc is None:
            raise ValueError(f"Document {document_id} not found")
        doc.parse_status = "processing"
        db.commit()

        try:
            data = storage.get(doc.storage_key)
            pages = parsers.parse(data, doc.file_type)
            doc.page_count = len(pages)

            atomiser = CurriculumAtomiser()
            candidates = atomiser.atomise(pages)[: settings.max_atoms_per_document]

            for cand in candidates:
                db.add(
                    CurriculumAtom(
                        document_id=document_id,
                        sequence_index=cand.sequence_index,
                        raw_text=cand.raw_text,
                        subject=doc.subject_override or cand.subject,
                        grade_level=doc.grade_override or cand.grade_level,
                        bloom_level=cand.bloom_level,
                        estimated_reading_minutes=cand.estimated_reading_minutes,
                    )
                )

            doc.parse_status = "complete"
            doc.parse_error = None
            db.commit()
            return {"document_id": document_id, "atom_count": len(candidates)}

        except Exception as exc:  # noqa: BLE001 - record failure, surface to API
            db.rollback()
            doc = db.get(SourceDocument, document_id)
            if doc is not None:
                doc.parse_status = "failed"
                doc.parse_error = str(exc)[:1000]
                db.commit()
            raise


def reprocess_document(document_id: str) -> dict:
    """Re-extract a document with the current atomiser, WITHOUT re-uploading.

    Parses the stored file first; only if that yields fresh atoms does it replace
    the old ones (and the rows that depend on them — transforms and behavioural
    events) in FK-safe order. If the file is missing or unparseable, it raises
    and leaves all existing data untouched (non-destructive on failure).
    """
    with session_scope() as db:
        doc = db.get(SourceDocument, document_id)
        if doc is None:
            raise ValueError(f"Document {document_id} not found")
        storage_key, file_type = doc.storage_key, doc.file_type
        subject_override, grade_override = doc.subject_override, doc.grade_override

    # Parse BEFORE touching the database, so a failure never destroys content.
    data = storage.get(storage_key)
    pages = parsers.parse(data, file_type)
    candidates = CurriculumAtomiser().atomise(pages)[: settings.max_atoms_per_document]
    if not candidates:
        return {"document_id": document_id, "atom_count": 0, "reprocessed": False}

    with session_scope() as db:
        atom_ids = list(
            db.scalars(select(CurriculumAtom.id).where(CurriculumAtom.document_id == document_id))
        )
        if atom_ids:
            db.execute(delete(SessionEvent).where(SessionEvent.atom_id.in_(atom_ids)))
            db.execute(delete(TransformedAtom).where(TransformedAtom.atom_id.in_(atom_ids)))
            db.execute(delete(CurriculumAtom).where(CurriculumAtom.document_id == document_id))

        doc = db.get(SourceDocument, document_id)
        doc.page_count = len(pages)
        for cand in candidates:
            db.add(
                CurriculumAtom(
                    document_id=document_id,
                    sequence_index=cand.sequence_index,
                    raw_text=cand.raw_text,
                    subject=subject_override or cand.subject,
                    grade_level=grade_override or cand.grade_level,
                    bloom_level=cand.bloom_level,
                    estimated_reading_minutes=cand.estimated_reading_minutes,
                )
            )
        doc.parse_status = "complete"
        doc.parse_error = None
        db.commit()

    return {"document_id": document_id, "atom_count": len(candidates), "reprocessed": True}
