"""Celery application + Beat schedule.

Only used when ``TASK_BACKEND=celery``. Requires ``celery`` and ``redis`` to be
installed (see the commented extras in requirements.txt). The default inline
backend needs none of this.
"""

from __future__ import annotations

from celery import Celery
from celery.schedules import crontab

from app.config import settings

celery_app = Celery(
    "neuracore",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_default_queue="default",
    task_routes={
        "app.workers.tasks.ingest_document_task": {"queue": "ingestion"},
        "app.workers.tasks.transform_document_task": {"queue": "transform"},
        "app.workers.tasks.recalibrate_all_profiles": {"queue": "adapt"},
    },
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

celery_app.conf.beat_schedule = {
    "recalibrate-all-profiles-weekly": {
        "task": "app.workers.tasks.recalibrate_all_profiles",
        "schedule": crontab(hour=2, minute=0, day_of_week=0),  # Sundays 02:00
    }
}
