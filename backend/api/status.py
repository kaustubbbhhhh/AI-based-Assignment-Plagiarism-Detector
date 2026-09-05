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


def _normalize(value: str) -> str:
    return (value or "").strip().lower()


def _teacher_can_access_submission(current_user: User, section: str, subject: str) -> bool:
    mappings = current_user.subjects_sections or []
    if not mappings:
        return False
    target_section = _normalize(section)
    target_subject = _normalize(subject)
    for entry in mappings:
        if _normalize(entry.get("section")) == target_section and _normalize(entry.get("subject")) == target_subject:
            return True
    return False


@router.get("/status/{submission_id}", response_model=SubmissionStatusResponse)
def get_submission_status(
    submission_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Poll the current processing status of a submission.
    Includes OCR score, AI score, Plagiarism score, metadata, and lock state.
    """

    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Submission #{submission_id} not found.",
        )
    if current_user.role.value == "student" and submission.student_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this submission status.",
        )
    if current_user.role.value == "teacher":
        student = db.query(User).filter(User.id == submission.student_id).first()
        if not student or not _teacher_can_access_submission(current_user, student.section, submission.subject):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Teacher is not assigned to this submission's section/subject.",
            )

    # ── Build base response ───────────────────────────────────
    response = SubmissionStatusResponse(
        submission_id=submission.id,
        assignment_title=submission.assignment_title or "Assignment 1",
        subject=submission.subject,
        filename=submission.filename,
        status=submission.status.value,
        is_locked=bool(submission.is_locked),
        locked_at=submission.locked_at,
        verification_token=submission.verification_token,
        current_step=1,
        total_steps=7,
    )

    # ── Check Celery task state for progress info ─────────────
    if submission.celery_task_id and submission.celery_task_id != "sync_mode":
        try:
            from celery.result import AsyncResult
            from tasks.celery_app import celery_app
            task_result = AsyncResult(submission.celery_task_id, app=celery_app)
            if task_result.state == "PROGRESS" and task_result.info:
                info = task_result.info
                response.progress = info.get("progress", "Processing...")
                response.stage = info.get("stage", "processing")
                response.current_step = info.get("current_step", 2)
                response.total_steps = info.get("total_steps", 7)
            elif task_result.state == "PENDING":
                response.progress = "Waiting in task queue..."
                response.stage = "queued"
                response.current_step = 1
            elif task_result.state == "STARTED":
                response.progress = "Task started by worker..."
                response.stage = "started"
                response.current_step = 1
        except Exception:
            # Redis not available — skip Celery status check
            pass

    # ── If completed, attach scores & extracted text ──────────
    if submission.status.value == "completed":
        report = db.query(Report).filter(Report.submission_id == submission_id).first()
        if report:
            response.ai_score = report.ai_score
            response.plagiarism_score = report.plagiarism_score
            response.ocr_score = report.ocr_score if report.ocr_score is not None else 100.0
            response.ocr_status = report.ocr_status or "Accepted"
            response.label = report.label.value
            response.word_count = report.word_count
            response.sentence_count = report.sentence_count
            response.processed_text_preview = (report.processed_text[:400] + "...") if report.processed_text else ""
            response.progress = "Analysis Completed & Verified"
            response.stage = "completed"
            response.current_step = 7
            response.total_steps = 7

    elif submission.status.value == "failed":
        response.progress = "Processing failed. Document could not be processed."
        response.stage = "failed"

    elif submission.status.value == "processing":
        response.progress = response.progress or "Analyzing content..."
        response.stage = response.stage or "processing"

    elif submission.status.value == "pending":
        response.progress = "Waiting in queue..."
        response.stage = "pending"

    return response
