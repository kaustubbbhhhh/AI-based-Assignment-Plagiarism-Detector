"""
Celery application instance configured with Redis broker and backend.
"""

import logging
from celery import Celery
from core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

celery_app = Celery(
    "plagiarism_detector",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["tasks.process_submission"],
)

# ── Celery Configuration ──────────────────────────────────────
celery_app.conf.update(
    task_always_eager=settings.CELERY_TASK_ALWAYS_EAGER,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,                    # re-queue if worker crashes
    worker_prefetch_multiplier=1,           # one task at a time per worker
    result_expires=3600,                    # results expire after 1 hour
)

if settings.CELERY_TASK_ALWAYS_EAGER:
    logger.warning("Celery is running in eager mode (synchronous task execution).")
else:
    logger.info("Celery is running in async queue mode.")
