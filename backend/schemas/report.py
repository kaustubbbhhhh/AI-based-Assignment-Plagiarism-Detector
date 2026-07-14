"""
Pydantic schemas for Report API responses.
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ReportResponse(BaseModel):
    id: int
    submission_id: int
    ai_score: float
    plagiarism_score: float
    label: str
    processed_text: Optional[str] = None
    word_count: Optional[int] = None
    sentence_count: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ReportSummary(BaseModel):
    """Lightweight report for listing/dashboard views."""
    submission_id: int
    subject: str
    filename: str
    student_name: str
    section: Optional[str] = None
    ai_score: float
    plagiarism_score: float
    label: str
    submitted_at: datetime
