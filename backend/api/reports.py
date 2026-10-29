"""
Report API routes.
GET /api/report/{submission_id} — Fetch the full analysis report.
GET /api/reports/section/{section} — Fetch all reports for a section (teacher/hod/admin).
GET /api/reports/batch — Fetch all reports across sections (hod/admin).
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from core.dependencies import get_db, get_current_user
from core.authorization import check_submission_access, check_teacher_section_access
from models.user import User
from models.submission import Submission
from models.report import Report
from schemas.report import ReportResponse, ReportSummary
from services.audit_service import log_security_event

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["Reports"])


@router.get("/report/{submission_id}", response_model=ReportResponse)
def get_report(
    submission_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Fetch the full analysis report for a specific submission.
    Enforces object-level authorization:
    - Student: can only access their own report.
    - Teacher: can only access reports for assigned courses & sections.
    - HOD & Admin: full departmental / institutional access.
    """

    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Submission #{submission_id} not found.",
        )

    # Object-level authorization check
    check_submission_access(current_user, submission, action="read", db=db, request=request)

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
    subject: Optional[str] = None,
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Fetch all completed reports for students in a specific section.
    Optionally filter by subject as well.
    Used by teachers, HOD, and Admin for dashboard views.
    Enforces scope-based authorization for teachers.
    """

    role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)

    # Only teachers, HOD, and Admin can view section reports
    if role_val not in ("teacher", "hod", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers, HOD, and administrators can access section reports.",
        )

    # If teacher, verify that they are actually assigned to this section (and subject if provided)
    if role_val == "teacher":
        if not check_teacher_section_access(current_user, section=section, subject=subject):
            client_ip = request.client.host if request and request.client else "unknown"
            ua = request.headers.get("user-agent") if request else "unknown"
            log_security_event(
                event_type="OBJECT_ACCESS_DENIED",
                user_id=current_user.id,
                email=current_user.email,
                ip_address=client_ip,
                user_agent=ua,
                status="BLOCKED",
                detail=f"Teacher {current_user.id} attempted to view unassigned section '{section}' (subject: {subject})",
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: You are not assigned to teach section '{section}'.",
            )

    query = (
        db.query(Report, Submission, User)
        .join(Submission, Report.submission_id == Submission.id)
        .join(User, Submission.student_id == User.id)
        .filter(User.section.ilike(f"%{section}%"))
    )

    if subject:
        query = query.filter(Submission.subject == subject)

    results = query.all()

    return [_build_summary(r, s, u) for r, s, u in results]


@router.get("/reports/batch", response_model=List[ReportSummary])
def get_batch_reports(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Fetch ALL completed reports across all sections.
    Restricted to HOD and Admin.
    """
    role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)

    if role_val not in ("hod", "admin"):
        client_ip = request.client.host if request and request.client else "unknown"
        ua = request.headers.get("user-agent") if request else "unknown"
        log_security_event(
            event_type="PRIVILEGE_ESCALATION_ATTEMPT",
            user_id=current_user.id,
            email=current_user.email,
            ip_address=client_ip,
            user_agent=ua,
            status="BLOCKED",
            detail=f"User with role '{role_val}' attempted to access batch reports (requires HOD or Admin)",
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Only HOD and Admin can access batch reports.",
        )

    results = (
        db.query(Report, Submission, User)
        .join(Submission, Report.submission_id == Submission.id)
        .join(User, Submission.student_id == User.id)
        .all()
    )

    return [_build_summary(r, s, u) for r, s, u in results]
