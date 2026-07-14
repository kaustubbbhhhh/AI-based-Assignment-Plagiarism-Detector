"""
Pydantic schemas for Submission API requests and responses.
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# ── Request Schemas ───────────────────────────────────────────

class SubmissionCreate(BaseModel):
    """Metadata sent alongside the file upload."""
    subject: str
    student_name: Optional[str] = None


# ── Response Schemas ──────────────────────────────────────────

class SubmissionResponse(BaseModel):
    id: int
    student_id: int
    subject: str
    filename: str
    status: str
    celery_task_id: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SubmissionStatusResponse(BaseModel):
    submission_id: int
    status: str
    progress: Optional[str] = None       # e.g. "Extracting text...", "Running AI detection..."
    ai_score: Optional[float] = None     # filled once completed
    plagiarism_score: Optional[float] = None
    label: Optional[str] = None

    class Config:
        from_attributes = True


class SubmitResponse(BaseModel):
    """Immediate response after file upload."""
    message: str
    submission_id: int
    celery_task_id: str
