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
    ocr_score: Optional[float] = 100.0
    ocr_status: Optional[str] = "Accepted"
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
    assignment_title: Optional[str] = "Assignment 1"
    filename: str
    student_name: str
    section: Optional[str] = None
    ai_score: float
    plagiarism_score: float
    ocr_score: Optional[float] = 100.0
    label: str
    is_locked: Optional[bool] = False
    submitted_at: datetime

    class Config:
        from_attributes = True
