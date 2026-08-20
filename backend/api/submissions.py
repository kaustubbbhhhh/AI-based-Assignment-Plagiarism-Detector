"""
Submission API routes.
POST /api/submit — Upload assignment file + metadata, queue processing.
GET  /api/submissions/my — Fetch all submissions for the logged-in student.
POST /api/submissions/{id}/lock — Lock and finalize the assignment submission.
DELETE /api/submissions/{id} — Discard an unlocked assignment submission.
GET  /api/download/{id} — Download submitted file.
"""

import os
import uuid
import secrets
from datetime import datetime
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from core.dependencies import get_db, get_current_user
from core.config import get_settings
from models.user import User
from models.submission import Submission, SubmissionStatus
from models.report import Report
from schemas.submission import SubmitResponse, LockSubmissionResponse, StudentSubmissionItem
from fastapi.responses import FileResponse

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter(prefix="/api", tags=["Submissions"])


@router.post("/submit", response_model=SubmitResponse, status_code=status.HTTP_202_ACCEPTED)
def submit_assignment(
    subject: str = Form(...),
    assignment_title: Optional[str] = Form("Assignment 1"),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Accept an assignment file upload (PDF, DOCX, TXT, PNG, JPG, JPEG) and queue processing.
    """

    # ── Validate file type (first-class JPG, PNG, DOCX, PDF, TXT) ──
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
    clean_title = (assignment_title or "Assignment 1").strip()
    submission = Submission(
        student_id=current_user.id,
        subject=subject.strip(),
        assignment_title=clean_title,
        filename=file.filename,
        filepath=filepath,
        status=SubmissionStatus.pending,
        is_locked=False,
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)

    # ── Process asynchronously (Redis + Celery) or fallback ───
    from tasks.process_submission import process_submission_task, process_submission_sync
    celery_task_id = "sync_mode"
    try:
        task = process_submission_task.delay(submission.id)
        logger.info(f"Submission #{submission.id} queued as task {task.id}.")
        celery_task_id = task.id
        submission.celery_task_id = celery_task_id
        db.commit()
    except Exception as e:
        logger.warning(f"Async Celery queue unavailable ({e}). Running synchronously...")
        try:
            submission.celery_task_id = "sync_mode"
            db.commit()
            process_submission_sync(submission.id)
        except Exception as sync_err:
            logger.error(f"Synchronous processing failed: {sync_err}")
            submission.status = SubmissionStatus.failed
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Analysis failed: {str(sync_err)}"
            )

    return SubmitResponse(
        message="Assignment uploaded and queued for forensic OCR & Plagiarism analysis.",
        submission_id=submission.id,
        assignment_title=submission.assignment_title,
        celery_task_id=celery_task_id,
    )


@router.get("/submissions/my", response_model=List[StudentSubmissionItem])
def get_my_submissions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Fetch all past submissions made by the currently logged-in student.
    """
    submissions = (
        db.query(Submission)
        .filter(Submission.student_id == current_user.id)
        .order_by(Submission.created_at.desc())
        .all()
    )

    results = []
    for s in submissions:
        report = db.query(Report).filter(Report.submission_id == s.id).first()
        results.append(StudentSubmissionItem(
            id=s.id,
            subject=s.subject,
            assignment_title=s.assignment_title or "Assignment 1",
            filename=s.filename,
            status=s.status.value,
            is_locked=bool(s.is_locked),
            locked_at=s.locked_at,
            verification_token=s.verification_token,
            created_at=s.created_at,
            ocr_score=report.ocr_score if report else None,
            ocr_status=report.ocr_status if report else None,
            ai_score=report.ai_score if report else None,
            plagiarism_score=report.plagiarism_score if report else None,
            label=report.label.value if report else None,
            word_count=report.word_count if report else None,
        ))

    return results


@router.post("/submissions/{submission_id}/lock", response_model=LockSubmissionResponse)
def lock_submission(
    submission_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Finalize and permanently lock an assignment submission.
    Generates an official verification receipt token and timestamp.
    """
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found"
        )

    if submission.student_id != current_user.id and current_user.role.value not in ("teacher", "hod"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to lock this submission"
        )

    if submission.status == SubmissionStatus.failed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot lock a failed submission. Please re-upload your document."
        )

    # Generate official cryptographic receipt verification token
    token_suffix = secrets.token_hex(4).upper()
    now = datetime.utcnow()
    verification_token = f"PLAG-SEC-{submission.id:04d}-{now.strftime('%Y%m%d')}-{token_suffix}"

    submission.is_locked = True
    submission.locked_at = now
    submission.verification_token = verification_token
    db.commit()
    db.refresh(submission)

    report = db.query(Report).filter(Report.submission_id == submission_id).first()

    return LockSubmissionResponse(
        message="Assignment officially locked and finalized in the institutional registry.",
        submission_id=submission.id,
        assignment_title=submission.assignment_title or "Assignment 1",
        subject=submission.subject,
        filename=submission.filename,
        is_locked=True,
        locked_at=submission.locked_at,
        verification_token=verification_token,
        ocr_score=report.ocr_score if report else 100.0,
        ai_score=report.ai_score if report else 0.0,
        plagiarism_score=report.plagiarism_score if report else 0.0,
    )


@router.delete("/submissions/{submission_id}")
def delete_submission(
    submission_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Discard an unlocked draft/review submission before final lock.
    """
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found"
        )

    if submission.student_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this submission"
        )

    if submission.is_locked:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot discard a finalized, locked submission."
        )

    # Clean up associated report
    report = db.query(Report).filter(Report.submission_id == submission_id).first()
    if report:
        db.delete(report)

    # Remove file from disk if exists
    if os.path.exists(submission.filepath):
        try:
            os.remove(submission.filepath)
        except Exception:
            pass

    db.delete(submission)
    db.commit()

    return {"message": "Draft submission discarded successfully."}


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
