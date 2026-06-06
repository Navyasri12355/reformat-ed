"""Task dispatch abstraction.

``task_backend="inline"`` (default) runs long jobs in a background thread pool —
the API returns a task id immediately and the work completes asynchronously with
no Redis/Celery required. ``task_backend="celery"`` dispatches to Celery workers
(see :mod:`app.workers`). Either way callers use the same two functions.
"""

from __future__ import annotations

import uuid
from concurrent.futures import ThreadPoolExecutor

from app import logging_config as log
from app.config import settings
from app.services.ingestion import ingest_document
from app.services.transform_batch import transform_document_for_student

_executor = ThreadPoolExecutor(max_workers=8, thread_name_prefix="neuracore-task")


def _submit_inline(fn, *args) -> str:
    task_id = uuid.uuid4().hex

    def _wrapped():
        try:
            fn(*args)
        except Exception as exc:  # noqa: BLE001 - logged; status persisted in DB
            log.error("task_failed", task_id=task_id, fn=fn.__name__, error=str(exc))

    _executor.submit(_wrapped)
    return task_id


def run_ingestion(document_id: str) -> str:
    if settings.task_backend == "celery":
        from app.workers.tasks import ingest_document_task

        return ingest_document_task.delay(document_id).id
    return _submit_inline(ingest_document, document_id)


def run_transform(document_id: str, student_id: str, force_auto_approve: bool = False) -> str:
    if settings.task_backend == "celery":
        from app.workers.tasks import transform_document_task

        return transform_document_task.delay(document_id, student_id, force_auto_approve).id
    return _submit_inline(
        transform_document_for_student, document_id, student_id, force_auto_approve
    )
