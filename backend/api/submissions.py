"""
Submission API routes.
POST /api/submit — Upload assignment file + metadata, process synchronously, return result.
"""

import os
import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from core.dependencies import get_db, get_current_user
from core.config import get_settings
from models.user import User
from models.submission import Submission, SubmissionStatus
from schemas.submission import SubmitResponse
from fastapi.responses import FileResponse

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter(prefix="/api", tags=["Submissions"])


@router.post("/submit", response_model=SubmitResponse, status_code=status.HTTP_202_ACCEPTED)
def submit_assignment(
    subject: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Accept an assignment file upload and process it.
    In sync mode (no Redis), processes immediately and returns.
    """

    # ── Validate file type ────────────────────────────────────
    allowed_extensions = {".pdf", ".docx", ".doc", ".txt", ".png", ".jpg", ".jpeg"}
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {ext}. Allowed: {', '.join(allowed_extensions)}",
        )

    # ── Save file to disk ─────────────────────────────────────
    upload_dir = os.path.join(settings.UPLOAD_DIR)
    os.makedirs(upload_dir, exist_ok=True)

    # Generate unique filename to prevent collisions
    unique_name = f"{uuid.uuid4().hex}_{file.filename}"
    filepath = os.path.join(upload_dir, unique_name)

    try:
        with open(filepath, "wb") as buffer:
            content = file.file.read()
            buffer.write(content)
        logger.info(f"File saved: {filepath} ({len(content)} bytes)")
    except Exception as e:
        logger.error(f"File save failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save uploaded file.",
        )

    # ── Create DB record ──────────────────────────────────────
    submission = Submission(
        student_id=current_user.id,
        subject=subject,
        filename=file.filename,
        filepath=filepath,
        status=SubmissionStatus.pending,
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)

    # ── Process asynchronously (Redis + Celery) ───────────────
    from tasks.process_submission import process_submission_task
    try:
        task = process_submission_task.delay(submission.id)
        logger.info(f"Submission #{submission.id} queued as task {task.id}.")
        celery_task_id = task.id
    except Exception as e:
        logger.error(f"Async processing failed to queue for #{submission.id}: {e}")
        submission.status = SubmissionStatus.failed
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to queue the submission for processing. Ensure Redis and Celery are running."
        )

    return SubmitResponse(
        message="Assignment submitted and queued for analysis.",
        submission_id=submission.id,
        celery_task_id=celery_task_id,
    )


@router.get("/download/{submission_id}")
def download_submission(
    submission_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Download the original submitted file.
    Only teachers, HODs, or the student who submitted it can download it.
    """
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found"
        )
        
    if current_user.role.value not in ("teacher", "hod") and submission.student_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to download this file"
        )
        
    if not os.path.exists(submission.filepath):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File missing from disk"
        )
        
    return FileResponse(submission.filepath, filename=submission.filename)
