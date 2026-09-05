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


def _normalize(value: str) -> str:
    return (value or "").strip().lower()


def _teacher_can_access_section_subject(current_user: User, section: str, subject: str = None) -> bool:
    mappings = current_user.subjects_sections or []
    if not mappings:
        return False
    target_section = _normalize(section)
    target_subject = _normalize(subject) if subject else None
    for entry in mappings:
        mapped_section = _normalize(entry.get("section"))
        mapped_subject = _normalize(entry.get("subject"))
        if mapped_section == target_section and (target_subject is None or mapped_subject == target_subject):
            return True
    return False


@router.get("/report/{submission_id}", response_model=ReportResponse)
def get_report(
    submission_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Fetch the full analysis report for a specific submission."""
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Submission #{submission_id} not found.",
        )

    if current_user.role.value == "student" and submission.student_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this report.",
        )
    if current_user.role.value == "teacher":
        student = db.query(User).filter(User.id == submission.student_id).first()
        if not student or not _teacher_can_access_section_subject(current_user, student.section, submission.subject):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Teacher is not assigned to this submission's section/subject.",
            )

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
        assignment_title=submission.assignment_title or "Assignment 1",
        filename=submission.filename,
        student_name=student.name,
        section=student.section,
        ai_score=report.ai_score,
        plagiarism_score=report.plagiarism_score,
        ocr_score=report.ocr_score if report.ocr_score is not None else 100.0,
        label=report.label.value,
        is_locked=bool(submission.is_locked),
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
    if current_user.role.value == "teacher":
        if not _teacher_can_access_section_subject(current_user, section, subject):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Teacher is not assigned to this section/subject.",
            )

    query = (
        db.query(Report, Submission, User)
        .join(Submission, Report.submission_id == Submission.id)
        .join(User, Submission.student_id == User.id)
        .filter(User.section == section)
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
