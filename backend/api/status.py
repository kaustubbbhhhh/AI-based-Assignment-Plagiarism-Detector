"""
Status Polling API.
GET /api/status/{submission_id} — Check processing status.
Works in both sync mode (no Redis) and async mode (Celery).
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from core.dependencies import get_db, get_current_user
from models.user import User
from models.submission import Submission
from models.report import Report
from schemas.submission import SubmissionStatusResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["Status"])


@router.get("/status/{submission_id}", response_model=SubmissionStatusResponse)
def get_submission_status(
    submission_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Poll the current processing status of a submission.
    If completed, includes the final scores in the response.
    """

    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Submission #{submission_id} not found.",
        )

    # ── Build base response ───────────────────────────────────
    response = SubmissionStatusResponse(
        submission_id=submission.id,
        status=submission.status.value,
    )

    # ── Check Celery task state for progress info ─────────────
    if submission.celery_task_id and submission.celery_task_id != "sync_mode":
        try:
            from celery.result import AsyncResult
            from tasks.celery_app import celery_app
            task_result = AsyncResult(submission.celery_task_id, app=celery_app)
            if task_result.state == "PROGRESS" and task_result.info:
                response.progress = task_result.info.get("progress", "Processing...")
            elif task_result.state == "PENDING":
                response.progress = "Waiting in queue..."
            elif task_result.state == "STARTED":
                response.progress = "Task started..."
        except Exception:
            # Redis not available — skip Celery status check
            pass

    # ── If completed, attach scores ───────────────────────────
    if submission.status.value == "completed":
        report = db.query(Report).filter(Report.submission_id == submission_id).first()
        if report:
            response.ai_score = report.ai_score
            response.plagiarism_score = report.plagiarism_score
            response.label = report.label.value
            response.progress = "Completed"

    elif submission.status.value == "failed":
        response.progress = "Processing failed"

    elif submission.status.value == "processing":
        response.progress = response.progress or "Analyzing content..."

    elif submission.status.value == "pending":
        response.progress = "Waiting in queue..."

    return response
