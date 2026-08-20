"""
Pydantic schemas for Submission API requests and responses.
"""

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# ── Request Schemas ───────────────────────────────────────────

class SubmissionCreate(BaseModel):
    """Metadata sent alongside the file upload."""
    subject: str
    assignment_title: Optional[str] = "Assignment 1"
    student_name: Optional[str] = None


# ── Response Schemas ──────────────────────────────────────────

class SubmissionResponse(BaseModel):
    id: int
    student_id: int
    subject: str
    assignment_title: Optional[str] = "Assignment 1"
    filename: str
    status: str
    is_locked: bool = False
    locked_at: Optional[datetime] = None
    verification_token: Optional[str] = None
    celery_task_id: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SubmissionStatusResponse(BaseModel):
    submission_id: int
    assignment_title: Optional[str] = "Assignment 1"
    subject: Optional[str] = None
    filename: Optional[str] = None
    status: str
    progress: Optional[str] = None       # e.g. "Extracting text...", "Running AI detection..."
    stage: Optional[str] = None          # e.g. "ingest", "ocr", "quality", "ai", "plagiarism", "completed"
    current_step: Optional[int] = 1
    total_steps: Optional[int] = 7
    ai_score: Optional[float] = None     # filled once completed
    plagiarism_score: Optional[float] = None
    ocr_score: Optional[float] = None    # 0-100% OCR confidence/legibility
    ocr_status: Optional[str] = None    # "Accepted - High Legibility", "Accepted - Digital Verification"
    label: Optional[str] = None
    word_count: Optional[int] = None
    sentence_count: Optional[int] = None
    processed_text_preview: Optional[str] = None
    is_locked: bool = False
    locked_at: Optional[datetime] = None
    verification_token: Optional[str] = None

    class Config:
        from_attributes = True


class SubmitResponse(BaseModel):
    """Immediate response after file upload."""
    message: str
    submission_id: int
    assignment_title: Optional[str] = "Assignment 1"
    celery_task_id: str


class LockSubmissionResponse(BaseModel):
    """Response returned when a student locks their submission."""
    message: str
    submission_id: int
    assignment_title: str
    subject: str
    filename: str
    is_locked: bool
    locked_at: datetime
    verification_token: str
    ocr_score: Optional[float] = None
    ai_score: Optional[float] = None
    plagiarism_score: Optional[float] = None


class StudentSubmissionItem(BaseModel):
    """Item for student submission history listing."""
    id: int
    subject: str
    assignment_title: str
    filename: str
    status: str
    is_locked: bool
    locked_at: Optional[datetime] = None
    verification_token: Optional[str] = None
    created_at: datetime
    ocr_score: Optional[float] = None
    ocr_status: Optional[str] = None
    ai_score: Optional[float] = None
    plagiarism_score: Optional[float] = None
    label: Optional[str] = None
    word_count: Optional[int] = None

    class Config:
        from_attributes = True
