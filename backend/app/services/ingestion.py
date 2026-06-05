"""Ingestion orchestration: parse a stored document into curriculum atoms.

This is the synchronous worker body. It is invoked either inline (background
thread) or from a Celery task — both call :func:`ingest_document`.
"""

from __future__ import annotations

from app.config import settings
from app.database import session_scope
from app.models import CurriculumAtom, SourceDocument
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
