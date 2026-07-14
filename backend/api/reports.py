"""
Report API routes.
GET /api/report/{submission_id} — Fetch the full analysis report.
GET /api/reports/section/{section} — Fetch all reports for a section (teacher/hod).
GET /api/reports/batch — Fetch all reports across sections (hod).
"""

import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from core.dependencies import get_db, get_current_user
from models.user import User
from models.submission import Submission
from models.report import Report
from schemas.report import ReportResponse, ReportSummary

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["Reports"])


@router.get("/report/{submission_id}", response_model=ReportResponse)
def get_report(
    submission_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Fetch the full analysis report for a specific submission."""

    report = db.query(Report).filter(Report.submission_id == submission_id).first()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report for submission #{submission_id} not found. It may still be processing.",
        )
    return report


def _build_summary(report: Report, submission: Submission, student: User) -> ReportSummary:
    """Helper to build a ReportSummary from DB objects."""
    return ReportSummary(
        submission_id=submission.id,
        subject=submission.subject,
        filename=submission.filename,
        student_name=student.name,
        section=student.section,
        ai_score=report.ai_score,
        plagiarism_score=report.plagiarism_score,
        label=report.label.value,
        submitted_at=submission.created_at,
    )


@router.get("/reports/section/{section}", response_model=List[ReportSummary])
def get_reports_by_section(
    section: str,
    subject: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Fetch all completed reports for students in a specific section.
    Optionally filter by subject as well.
    Used by teachers & HOD for dashboard views.
    """

    # Only teachers and HOD can view section reports
    if current_user.role.value not in ("teacher", "hod"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers and HOD can access section reports.",
        )

    query = (
        db.query(Report, Submission, User)
        .join(Submission, Report.submission_id == Submission.id)
        .join(User, Submission.student_id == User.id)
        .filter(User.section.ilike(f"%{section}%"))
    )

    # ── Subject filter (fixes the loophole) ───────────────────
    if subject:
        query = query.filter(Submission.subject == subject)

    results = query.all()

    return [_build_summary(r, s, u) for r, s, u in results]


@router.get("/reports/batch", response_model=List[ReportSummary])
def get_batch_reports(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Fetch ALL completed reports across all sections.
    Used by HOD for batch-level overview.
    """

    if current_user.role.value != "hod":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only HOD can access batch reports.",
        )

    results = (
        db.query(Report, Submission, User)
        .join(Submission, Report.submission_id == Submission.id)
        .join(User, Submission.student_id == User.id)
        .all()
    )

    return [_build_summary(r, s, u) for r, s, u in results]
