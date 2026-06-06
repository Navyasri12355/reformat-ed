"""Celery task wrappers around the synchronous service bodies."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.database import session_scope
from app.models import SessionEvent
from app.services.adapt import recalibrate_profile
from app.services.ingestion import ingest_document
from app.services.transform_batch import transform_document_for_student
from app.workers.celery_app import celery_app


@celery_app.task(bind=True, max_retries=3, default_retry_delay=10)
def ingest_document_task(self, document_id: str) -> dict:
    try:
        return ingest_document(document_id)
    except Exception as exc:  # noqa: BLE001
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def transform_document_task(self, document_id: str, student_id: str, force_auto_approve: bool = False) -> dict:
    try:
        return transform_document_for_student(document_id, student_id, force_auto_approve)
    except Exception as exc:  # noqa: BLE001
        raise self.retry(exc=exc)


@celery_app.task
def recalibrate_all_profiles() -> dict:
    """Weekly Beat job: recalibrate every student with recent signal data."""
    since = datetime.now(timezone.utc) - timedelta(days=7)
    with session_scope() as db:
        student_ids = db.scalars(
            select(SessionEvent.student_id)
            .where(SessionEvent.recorded_at >= since)
            .distinct()
        ).all()
    changed = 0
    for student_id in student_ids:
        with session_scope() as db:
            if recalibrate_profile(db, student_id):
                changed += 1
    return {"students_considered": len(student_ids), "students_changed": changed}
