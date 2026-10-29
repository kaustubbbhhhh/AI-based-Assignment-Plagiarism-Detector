"""
Centralized Backend-Enforced Authorization Architecture (RBAC & ABAC).

Provides:
- Formal permission definitions and role-permission matrix.
- Reusable FastAPI dependencies: require_permission, require_role, require_admin.
- Object-level authorization helpers (ABAC/Ownership):
    * check_submission_access (student ownership, faculty subject-section scope, admin/hod oversight)
    * check_report_access
    * check_user_access
- Structured security logging for all authorization failures.
"""

import logging
from typing import List, Optional, Callable, Set
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session as DbSession

from core.dependencies import get_db, get_current_user
from models.user import User, UserRole
from models.submission import Submission
from services.audit_service import log_security_event

logger = logging.getLogger(__name__)


# ── 1. Permission Definitions ─────────────────────────────────

class Permission:
    # Submissions / Assignments
    ASSIGNMENT_CREATE = "assignment:create"
    ASSIGNMENT_READ_OWN = "assignment:read:own"
    ASSIGNMENT_READ_ASSIGNED = "assignment:read:assigned"
    ASSIGNMENT_READ_ALL = "assignment:read:all"
    ASSIGNMENT_DELETE_OWN = "assignment:delete:own"
    ASSIGNMENT_LOCK_OWN = "assignment:lock:own"
    ASSIGNMENT_LOCK_ASSIGNED = "assignment:lock:assigned"
    ASSIGNMENT_LOCK_ALL = "assignment:lock:all"
    ASSIGNMENT_DOWNLOAD_OWN = "assignment:download:own"
    ASSIGNMENT_DOWNLOAD_ASSIGNED = "assignment:download:assigned"
    ASSIGNMENT_DOWNLOAD_ALL = "assignment:download:all"

    # Plagiarism Reports
    REPORT_READ_OWN = "report:read:own"
    REPORT_READ_ASSIGNED = "report:read:assigned"
    REPORT_READ_ALL = "report:read:all"

    # Analytics
    ANALYTICS_READ_ASSIGNED = "analytics:read:assigned"
    ANALYTICS_READ_ALL = "analytics:read:all"

    # User Management
    USER_READ_OWN = "user:read:own"
    USER_READ_ALL = "user:read:all"
    USER_UPDATE_OWN = "user:update:own"
    USER_UPDATE_ALL = "user:update:all"
    USER_DELETE = "user:delete"
    ROLE_CHANGE = "role:change"

    # System Settings
    SYSTEM_SETTINGS = "system:settings"


# ── 2. Role-Permission Matrix ─────────────────────────────────

ROLE_PERMISSIONS: dict[str, Set[str]] = {
    UserRole.student.value: {
        Permission.ASSIGNMENT_CREATE,
        Permission.ASSIGNMENT_READ_OWN,
        Permission.ASSIGNMENT_DELETE_OWN,
        Permission.ASSIGNMENT_LOCK_OWN,
        Permission.ASSIGNMENT_DOWNLOAD_OWN,
        Permission.REPORT_READ_OWN,
        Permission.USER_READ_OWN,
        Permission.USER_UPDATE_OWN,
    },
    UserRole.teacher.value: {
        Permission.ASSIGNMENT_READ_ASSIGNED,
        Permission.ASSIGNMENT_DOWNLOAD_ASSIGNED,
        Permission.ASSIGNMENT_LOCK_ASSIGNED,
        Permission.REPORT_READ_ASSIGNED,
        Permission.ANALYTICS_READ_ASSIGNED,
        Permission.USER_READ_OWN,
        Permission.USER_UPDATE_OWN,
    },
    UserRole.hod.value: {
        Permission.ASSIGNMENT_READ_ALL,
        Permission.ASSIGNMENT_DOWNLOAD_ALL,
        Permission.ASSIGNMENT_LOCK_ALL,
        Permission.REPORT_READ_ALL,
        Permission.ANALYTICS_READ_ALL,
        Permission.USER_READ_OWN,
        Permission.USER_UPDATE_OWN,
    },
    UserRole.admin.value: {
        # Admin holds all permissions wildcard
        "*"
    },
}


def user_has_permission(user: User, permission: str) -> bool:
    """Check whether a user's role grants a specific permission."""
    if not user or not user.role:
        return False
    role_val = user.role.value if hasattr(user.role, "value") else str(user.role)
    perms = ROLE_PERMISSIONS.get(role_val, set())
    if "*" in perms or permission in perms:
        return True
    return False


# ── 3. FastAPI Authorization Dependencies ─────────────────────

def require_role(*allowed_roles: str) -> Callable:
    """
    Dependency that verifies the authenticated user possesses one of the allowed roles.
    Never trusts client-provided role headers or payloads.
    """
    def role_checker(
        request: Request,
        current_user: User = Depends(get_current_user),
    ) -> User:
        user_role = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
        if user_role not in allowed_roles:
            log_security_event(
                event_type="PRIVILEGE_ESCALATION_ATTEMPT",
                user_id=current_user.id,
                email=current_user.email,
                ip_address=request.client.host if request.client else "unknown",
                user_agent=request.headers.get("user-agent"),
                status="BLOCKED",
                detail=f"Role '{user_role}' attempted access to endpoint requiring {allowed_roles} on {request.method} {request.url.path}",
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden: You do not have permission to access this resource.",
            )
        return current_user

    return role_checker


def require_permission(*required_permissions: str) -> Callable:
    """
    Dependency verifying that the user has at least one of the specified permissions.
    """
    def permission_checker(
        request: Request,
        current_user: User = Depends(get_current_user),
    ) -> User:
        user_role = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
        perms = ROLE_PERMISSIONS.get(user_role, set())
        has_any = ("*" in perms) or any(p in perms for p in required_permissions)

        if not has_any:
            log_security_event(
                event_type="AUTHORIZATION_DENIED",
                user_id=current_user.id,
                email=current_user.email,
                ip_address=request.client.host if request.client else "unknown",
                user_agent=request.headers.get("user-agent"),
                status="BLOCKED",
                detail=f"User missing required permissions {required_permissions} on {request.method} {request.url.path}",
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden: You do not possess the required permissions.",
            )
        return current_user

    return permission_checker


require_admin = require_role("admin")
require_faculty_or_admin = require_role("teacher", "hod", "admin")
require_hod_or_admin = require_role("hod", "admin")


# ── 4. Object-Level Access Control (ABAC & Ownership) ─────────

def check_submission_access(
    user: User,
    submission: Submission,
    action: str,
    db: DbSession,
    request: Optional[Request] = None,
) -> bool:
    """
    Enforce fine-grained, object-level authorization on a Submission resource.
    
    Rules:
    - Admin: Full access to any submission for any action.
    - HOD: Full departmental read/download/lock access to any submission.
    - Student: Strict ownership isolation — student_id must equal user.id.
    - Teacher: Assigned scope isolation — teacher can only access submissions
      belonging to courses/subjects and sections they are assigned to teach.
      Teachers cannot delete submissions.
    """
    role_val = user.role.value if hasattr(user.role, "value") else str(user.role)

    # 1. Admin has global access
    if role_val == "admin":
        return True

    # 2. HOD has department-wide oversight (cannot delete student submissions)
    if role_val == "hod":
        if action == "delete":
            _deny_object_access(user, "submission", submission.id, action, "HOD cannot delete student submissions", request)
        return True

    # 3. Student: strict resource ownership
    if role_val == "student":
        if submission.student_id != user.id:
            _deny_object_access(
                user, "submission", submission.id, action,
                f"Student {user.id} attempted access to Submission {submission.id} owned by student {submission.student_id}",
                request,
            )
        return True

    # 4. Teacher: course & section scope verification
    if role_val == "teacher":
        if action == "delete":
            _deny_object_access(user, "submission", submission.id, action, "Teachers cannot delete student submissions", request)

        # Check teacher assigned subjects and sections
        teacher_mappings = user.subjects_sections or []
        if not teacher_mappings:
            _deny_object_access(user, "submission", submission.id, action, "Teacher has no assigned subjects", request)

        # Get student details for section verification
        student = db.query(User).filter(User.id == submission.student_id).first()
        student_section = (student.section or "").strip().lower() if student else ""

        is_assigned = False
        sub_subject = (submission.subject or "").strip().lower()

        for mapping in teacher_mappings:
            mapped_subj = (mapping.get("subject") or "").strip().lower()
            mapped_sect = (mapping.get("section") or "").strip().lower()

            # Subject match
            if mapped_subj == sub_subject or mapped_subj in sub_subject or sub_subject in mapped_subj:
                # If a section was specified in teacher config, verify student section
                if mapped_sect:
                    if mapped_sect in student_section or student_section in mapped_sect:
                        is_assigned = True
                        break
                else:
                    is_assigned = True
                    break

        if not is_assigned:
            _deny_object_access(
                user, "submission", submission.id, action,
                f"Teacher {user.id} is not assigned to subject '{submission.subject}' / section '{student_section}'",
                request,
            )
        return True

    # Default deny for any unknown roles
    _deny_object_access(user, "submission", submission.id, action, f"Unknown role '{role_val}'", request)
    return False


def check_report_access(
    user: User,
    submission: Submission,
    db: DbSession,
    request: Optional[Request] = None,
) -> bool:
    """Check whether user is authorized to read the report for a submission."""
    return check_submission_access(user, submission, action="read", db=db, request=request)


def check_teacher_section_access(user: User, section: str, subject: Optional[str] = None) -> bool:
    """
    Verify if a teacher is authorized to access section reports.
    Admins and HODs always have access.
    """
    role_val = user.role.value if hasattr(user.role, "value") else str(user.role)
    if role_val in ("admin", "hod"):
        return True

    if role_val != "teacher":
        return False

    teacher_mappings = user.subjects_sections or []
    req_section = (section or "").strip().lower()
    req_subject = (subject or "").strip().lower() if subject else None

    for m in teacher_mappings:
        m_sect = (m.get("section") or "").strip().lower()
        m_subj = (m.get("subject") or "").strip().lower()

        section_match = (m_sect in req_section or req_section in m_sect)
        if req_subject:
            subject_match = (m_subj in req_subject or req_subject in m_subj)
            if section_match and subject_match:
                return True
        else:
            if section_match:
                return True

    return False


def _deny_object_access(
    user: User,
    resource_type: str,
    resource_id: int,
    action: str,
    reason: str,
    request: Optional[Request] = None,
):
    """Log security audit event and raise 403 Forbidden."""
    client_ip = request.client.host if request and request.client else "unknown"
    ua = request.headers.get("user-agent") if request else "unknown"

    log_security_event(
        event_type="OBJECT_ACCESS_DENIED",
        user_id=user.id,
        email=user.email,
        ip_address=client_ip,
        user_agent=ua,
        status="BLOCKED",
        detail=f"Denied {action} on {resource_type} #{resource_id}: {reason}",
    )
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access forbidden: You do not have permission to access this resource.",
    )
