"""
Admin Management API Routes.

Implements:
- POST   /api/admin/users                   — Create user with default password
- GET    /api/admin/users                    — List users with search/filter/pagination
- POST   /api/admin/users/{id}/reset-password — Reset user password to default
- GET    /api/admin/subjects                 — List subjects (with optional filters)
- POST   /api/admin/subjects                 — Create subject
- PUT    /api/admin/subjects/{id}            — Update subject
- DELETE /api/admin/subjects/{id}            — Deactivate (soft-delete) subject
- GET    /api/subjects                       — Public: fetch active subjects by branch+semester

All admin endpoints are protected by require_admin RBAC.
"""

import math
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Query, status
from sqlalchemy.orm import Session as DbSession
from sqlalchemy import or_

from core.dependencies import get_db, get_current_user
from core.authorization import require_admin
from core.config import get_settings
from core.security import hash_password, normalize_email, validate_password_strength
from models.user import User, UserRole
from models.subject import Subject, SubjectStatus
from schemas.user import (
    UserResponse,
    UserPaginationResponse,
    AdminCreateUser,
    AdminCreateStudent,
    AdminCreateTeacher,
    AdminCreateHOD,
    UserStatusUpdate,
    MessageResponse,
    SubjectSection,
)
from schemas.subject import (
    SubjectCreate,
    SubjectUpdate,
    SubjectResponse,
    SubjectListResponse,
)
from services.audit_service import log_security_event
from services.session_service import revoke_all_user_sessions

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(tags=["Admin Management"])


# ═══════════════════════════════════════════════════════════════
#  USER MANAGEMENT
# ═══════════════════════════════════════════════════════════════

# ── Create User (Admin Only) ──────────────────────────────────
@router.post("/api/admin/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def admin_create_user(
    payload: AdminCreateUser,
    request: Request,
    current_user: User = Depends(require_admin),
    db: DbSession = Depends(get_db),
):
    """
    Admin creates a new user (student, teacher, or hod).
    Password is automatically set to the configured DEFAULT_USER_PASSWORD.
    User will be required to change password on first login.
    """
    client_ip = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent")

    clean_email = normalize_email(str(payload.email))

    # Check duplicate email
    existing = db.query(User).filter(User.email == clean_email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    # Check unique institutional identifiers
    if payload.role == "student" and payload.enrollment_no:
        if db.query(User).filter(User.enrollment_no == payload.enrollment_no.strip()).first():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This enrollment number is already registered.")

    if payload.role == "teacher" and payload.teacher_id:
        if db.query(User).filter(User.teacher_id == payload.teacher_id.strip()).first():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This Teacher ID is already registered.")

    if payload.role == "hod" and payload.hod_id:
        if db.query(User).filter(User.hod_id == payload.hod_id.strip()).first():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This HOD ID is already registered.")

    # Validate default password meets policy
    default_pwd = settings.DEFAULT_USER_PASSWORD
    is_valid_pwd, pwd_error = validate_password_strength(default_pwd)
    if not is_valid_pwd:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Server configuration error: DEFAULT_USER_PASSWORD does not meet password policy: {pwd_error}",
        )

    # Build subjects_sections JSON if teacher
    ss_data = None
    if payload.subjects_sections:
        ss_data = [
            {"subject": s.subject, "section": s.section, **({  "branch": s.branch} if s.branch else {})}
            for s in payload.subjects_sections
        ]

    role = UserRole(payload.role)

    user = User(
        name=payload.name.strip(),
        email=clean_email,
        hashed_password=hash_password(default_pwd),
        role=role,
        phone=payload.phone.strip() if payload.phone else None,
        is_verified=True,
        must_change_password=True,
        section=payload.section.strip() if payload.section else None,
        branch=payload.branch.strip() if payload.branch else None,
        enrollment_no=payload.enrollment_no.strip() if payload.enrollment_no else None,
        session=payload.session.strip() if payload.session else None,
        semester=payload.semester,
        teacher_id=payload.teacher_id.strip() if payload.teacher_id else None,
        subjects_sections=ss_data,
        hod_id=payload.hod_id.strip() if payload.hod_id else None,
        department=payload.department.strip() if payload.department else None,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    log_security_event(
        event_type="ADMIN_USER_CREATED",
        user_id=current_user.id,
        email=current_user.email,
        ip_address=client_ip,
        user_agent=ua,
        detail=f"Admin created user #{user.id} ({user.email}) with role '{user.role.value}'. Default password assigned.",
    )

    return user


# ── List Users (Admin Only) ──────────────────────────────────
@router.get("/api/admin/users", response_model=UserPaginationResponse)
def admin_list_users(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    role: Optional[str] = Query(None),
    branch: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    current_user: User = Depends(require_admin),
    db: DbSession = Depends(get_db),
):
    """Paginated user directory with search, role, and branch filters."""
    query = db.query(User)

    if role:
        query = query.filter(User.role == role.strip().lower())

    if branch:
        query = query.filter(User.branch == branch.strip())

    if q:
        term = f"%{q.strip().lower()}%"
        query = query.filter(
            or_(
                User.name.ilike(term),
                User.email.ilike(term),
                User.enrollment_no.ilike(term),
                User.teacher_id.ilike(term),
                User.hod_id.ilike(term),
            )
        )

    total = query.count()
    offset = (page - 1) * limit
    users = query.order_by(User.id.desc()).offset(offset).limit(limit).all()
    total_pages = math.ceil(total / limit) if total > 0 else 1

    return UserPaginationResponse(
        items=[UserResponse.model_validate(u) for u in users],
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
    )


# ── Student Management (Admin Only) ───────────────────────────
@router.get("/api/admin/users/students", response_model=UserPaginationResponse)
def admin_list_students(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    branch: Optional[str] = Query(None),
    semester: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    current_user: User = Depends(require_admin),
    db: DbSession = Depends(get_db),
):
    """List student accounts with role enforcement, search, and academic filters."""
    query = db.query(User).filter(User.role == UserRole.student)

    if branch and branch.strip():
        query = query.filter(User.branch == branch.strip())

    if semester is not None:
        query = query.filter(User.semester == semester)

    if status and status.strip():
        st = status.strip().lower()
        if st in ("active", "verified", "1", "true"):
            query = query.filter(User.is_verified == True)
        elif st in ("inactive", "deactivated", "0", "false"):
            query = query.filter(User.is_verified == False)

    if q and q.strip():
        term = f"%{q.strip().lower()}%"
        query = query.filter(
            or_(
                User.name.ilike(term),
                User.email.ilike(term),
                User.enrollment_no.ilike(term),
            )
        )

    total = query.count()
    offset = (page - 1) * limit
    users = query.order_by(User.id.desc()).offset(offset).limit(limit).all()
    total_pages = math.ceil(total / limit) if total > 0 else 1

    return UserPaginationResponse(
        items=[UserResponse.model_validate(u) for u in users],
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
    )


@router.post("/api/admin/users/students", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def admin_create_student(
    payload: AdminCreateStudent,
    request: Request,
    current_user: User = Depends(require_admin),
    db: DbSession = Depends(get_db),
):
    """Create a new student account."""
    client_ip = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent")

    clean_email = normalize_email(str(payload.email))
    existing = db.query(User).filter(User.email == clean_email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"An account with email '{clean_email}' already exists.",
        )

    default_pwd = settings.DEFAULT_USER_PASSWORD
    pwd_valid, pwd_error = validate_password_strength(default_pwd)
    if not pwd_valid:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Server configuration error: DEFAULT_USER_PASSWORD does not meet password policy: {pwd_error}",
        )

    user = User(
        name=payload.name.strip(),
        email=clean_email,
        hashed_password=hash_password(default_pwd),
        role=UserRole.student,
        phone=payload.phone.strip() if payload.phone else None,
        is_verified=True,
        must_change_password=True,
        enrollment_no=payload.enrollment_no.strip() if payload.enrollment_no else None,
        branch=payload.branch.strip() if payload.branch else None,
        semester=payload.semester,
        section=payload.section.strip() if payload.section else None,
        session=payload.session.strip() if payload.session else None,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    log_security_event(
        event_type="ADMIN_USER_CREATED",
        user_id=current_user.id,
        email=current_user.email,
        ip_address=client_ip,
        user_agent=ua,
        detail=f"Admin created student #{user.id} ({user.email}).",
    )
    return user


# ── Teacher Management (Admin Only) ───────────────────────────
@router.get("/api/admin/users/teachers", response_model=UserPaginationResponse)
def admin_list_teachers(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    branch: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    current_user: User = Depends(require_admin),
    db: DbSession = Depends(get_db),
):
    """List teacher accounts with role enforcement, search, and department filters."""
    query = db.query(User).filter(User.role == UserRole.teacher)

    if branch and branch.strip():
        query = query.filter(User.branch == branch.strip())

    if status and status.strip():
        st = status.strip().lower()
        if st in ("active", "verified", "1", "true"):
            query = query.filter(User.is_verified == True)
        elif st in ("inactive", "deactivated", "0", "false"):
            query = query.filter(User.is_verified == False)

    if q and q.strip():
        term = f"%{q.strip().lower()}%"
        query = query.filter(
            or_(
                User.name.ilike(term),
                User.email.ilike(term),
                User.teacher_id.ilike(term),
            )
        )

    total = query.count()
    offset = (page - 1) * limit
    users = query.order_by(User.id.desc()).offset(offset).limit(limit).all()
    total_pages = math.ceil(total / limit) if total > 0 else 1

    return UserPaginationResponse(
        items=[UserResponse.model_validate(u) for u in users],
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
    )


@router.post("/api/admin/users/teachers", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def admin_create_teacher(
    payload: AdminCreateTeacher,
    request: Request,
    current_user: User = Depends(require_admin),
    db: DbSession = Depends(get_db),
):
    """Create a new teacher account."""
    client_ip = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent")

    clean_email = normalize_email(str(payload.email))
    existing = db.query(User).filter(User.email == clean_email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"An account with email '{clean_email}' already exists.",
        )

    default_pwd = settings.DEFAULT_USER_PASSWORD
    pwd_valid, pwd_error = validate_password_strength(default_pwd)
    if not pwd_valid:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Server configuration error: DEFAULT_USER_PASSWORD does not meet password policy: {pwd_error}",
        )

    ss_data = None
    if payload.subjects_sections:
        ss_data = [
            {"subject": s.subject, "section": s.section, **({"branch": s.branch} if s.branch else {})}
            for s in payload.subjects_sections
        ]

    user = User(
        name=payload.name.strip(),
        email=clean_email,
        hashed_password=hash_password(default_pwd),
        role=UserRole.teacher,
        phone=payload.phone.strip() if payload.phone else None,
        is_verified=True,
        must_change_password=True,
        teacher_id=payload.teacher_id.strip() if payload.teacher_id else None,
        branch=payload.branch.strip() if payload.branch else None,
        subjects_sections=ss_data,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    log_security_event(
        event_type="ADMIN_USER_CREATED",
        user_id=current_user.id,
        email=current_user.email,
        ip_address=client_ip,
        user_agent=ua,
        detail=f"Admin created teacher #{user.id} ({user.email}).",
    )
    return user


# ── HOD Management (Admin Only) ───────────────────────────────
@router.get("/api/admin/users/hods", response_model=UserPaginationResponse)
def admin_list_hods(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    department: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    current_user: User = Depends(require_admin),
    db: DbSession = Depends(get_db),
):
    """List HOD accounts with role enforcement, search, and department filters."""
    query = db.query(User).filter(User.role == UserRole.hod)

    if department and department.strip():
        query = query.filter(or_(User.department == department.strip(), User.branch == department.strip()))

    if status and status.strip():
        st = status.strip().lower()
        if st in ("active", "verified", "1", "true"):
            query = query.filter(User.is_verified == True)
        elif st in ("inactive", "deactivated", "0", "false"):
            query = query.filter(User.is_verified == False)

    if q and q.strip():
        term = f"%{q.strip().lower()}%"
        query = query.filter(
            or_(
                User.name.ilike(term),
                User.email.ilike(term),
                User.hod_id.ilike(term),
            )
        )

    total = query.count()
    offset = (page - 1) * limit
    users = query.order_by(User.id.desc()).offset(offset).limit(limit).all()
    total_pages = math.ceil(total / limit) if total > 0 else 1

    return UserPaginationResponse(
        items=[UserResponse.model_validate(u) for u in users],
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
    )


@router.post("/api/admin/users/hods", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def admin_create_hod(
    payload: AdminCreateHOD,
    request: Request,
    current_user: User = Depends(require_admin),
    db: DbSession = Depends(get_db),
):
    """Create a new HOD account."""
    client_ip = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent")

    clean_email = normalize_email(str(payload.email))
    existing = db.query(User).filter(User.email == clean_email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"An account with email '{clean_email}' already exists.",
        )

    default_pwd = settings.DEFAULT_USER_PASSWORD
    pwd_valid, pwd_error = validate_password_strength(default_pwd)
    if not pwd_valid:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Server configuration error: DEFAULT_USER_PASSWORD does not meet password policy: {pwd_error}",
        )

    user = User(
        name=payload.name.strip(),
        email=clean_email,
        hashed_password=hash_password(default_pwd),
        role=UserRole.hod,
        phone=payload.phone.strip() if payload.phone else None,
        is_verified=True,
        must_change_password=True,
        hod_id=payload.hod_id.strip() if payload.hod_id else None,
        department=payload.department.strip() if payload.department else None,
        branch=payload.department.strip() if payload.department else None,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    log_security_event(
        event_type="ADMIN_USER_CREATED",
        user_id=current_user.id,
        email=current_user.email,
        ip_address=client_ip,
        user_agent=ua,
        detail=f"Admin created HOD #{user.id} ({user.email}).",
    )
    return user


# ── Toggle User Active/Inactive Status (Admin Only) ───────────
@router.patch("/api/admin/users/{user_id}/status", response_model=UserResponse)
def admin_toggle_user_status(
    user_id: int,
    payload: UserStatusUpdate,
    request: Request,
    current_user: User = Depends(require_admin),
    db: DbSession = Depends(get_db),
):
    """
    Activate or deactivate user account.
    - Cannot deactivate own admin account.
    - If deactivated, revokes all active sessions immediately.
    """
    client_ip = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent")

    if user_id == current_user.id and not payload.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own administrative account.",
        )

    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    target_user.is_verified = payload.is_verified
    db.commit()
    db.refresh(target_user)

    if not payload.is_verified:
        revoked_count = revoke_all_user_sessions(db, target_user.id)
        action_desc = f"deactivated (revoked {revoked_count} sessions)"
    else:
        action_desc = "activated"

    log_security_event(
        event_type="ADMIN_USER_STATUS_CHANGED",
        user_id=current_user.id,
        email=current_user.email,
        ip_address=client_ip,
        user_agent=ua,
        detail=f"Admin {action_desc} user #{target_user.id} ({target_user.email}).",
    )

    return target_user


# ── Reset User Password (Admin Only) ─────────────────────────
@router.post("/api/admin/users/{user_id}/reset-password", response_model=MessageResponse)
def admin_reset_password(
    user_id: int,
    request: Request,
    current_user: User = Depends(require_admin),
    db: DbSession = Depends(get_db),
):
    """
    Reset a user's password to the configured default password.
    Sets must_change_password flag so user must change on next login.
    """
    client_ip = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent")

    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    # Prevent resetting own password through this endpoint
    if target_user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot reset your own password through admin reset. Use the Change Password feature.",
        )

    default_pwd = settings.DEFAULT_USER_PASSWORD
    target_user.hashed_password = hash_password(default_pwd)
    target_user.must_change_password = True
    db.commit()

    log_security_event(
        event_type="ADMIN_PASSWORD_RESET",
        user_id=current_user.id,
        email=current_user.email,
        ip_address=client_ip,
        user_agent=ua,
        detail=f"Admin reset password for user #{target_user.id} ({target_user.email}). Force-change flag set.",
    )

    return MessageResponse(
        message=f"Password for {target_user.name} ({target_user.email}) has been reset to the default password. They will be required to change it on next login."
    )


# ═══════════════════════════════════════════════════════════════
#  SUBJECT MANAGEMENT
# ═══════════════════════════════════════════════════════════════

# ── List Subjects (Admin Only) ────────────────────────────────
@router.get("/api/admin/subjects", response_model=SubjectListResponse)
def admin_list_subjects(
    branch: Optional[str] = Query(None),
    semester: Optional[int] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: User = Depends(require_admin),
    db: DbSession = Depends(get_db),
):
    """List all subjects with optional filters. Admin can see inactive subjects too."""
    query = db.query(Subject)

    if branch:
        query = query.filter(Subject.branch == branch.strip())
    if semester is not None:
        query = query.filter(Subject.semester == semester)
    if status_filter:
        query = query.filter(Subject.status == status_filter.strip().lower())

    subjects = query.order_by(Subject.branch, Subject.semester, Subject.subject_code).all()

    return SubjectListResponse(
        items=[SubjectResponse.model_validate(s) for s in subjects],
        total=len(subjects),
    )


# ── Create Subject (Admin Only) ──────────────────────────────
@router.post("/api/admin/subjects", response_model=SubjectResponse, status_code=status.HTTP_201_CREATED)
def admin_create_subject(
    payload: SubjectCreate,
    request: Request,
    current_user: User = Depends(require_admin),
    db: DbSession = Depends(get_db),
):
    """Create a new subject. Enforces unique (code, branch, semester) constraint."""
    client_ip = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent")

    # Check for duplicate
    existing = db.query(Subject).filter(
        Subject.subject_code == payload.subject_code.strip(),
        Subject.branch == payload.branch.strip(),
        Subject.semester == payload.semester,
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Subject '{payload.subject_code}' already exists for {payload.branch} Semester {payload.semester}.",
        )

    subject = Subject(
        subject_code=payload.subject_code.strip(),
        subject_name=payload.subject_name.strip(),
        branch=payload.branch.strip(),
        semester=payload.semester,
        status=SubjectStatus.active,
    )
    db.add(subject)
    db.commit()
    db.refresh(subject)

    log_security_event(
        event_type="ADMIN_SUBJECT_CREATED",
        user_id=current_user.id,
        email=current_user.email,
        ip_address=client_ip,
        user_agent=ua,
        detail=f"Admin created subject '{subject.subject_code} - {subject.subject_name}' for {subject.branch} Sem {subject.semester}.",
    )

    return subject


# ── Update Subject (Admin Only) ──────────────────────────────
@router.put("/api/admin/subjects/{subject_id}", response_model=SubjectResponse)
def admin_update_subject(
    subject_id: int,
    payload: SubjectUpdate,
    request: Request,
    current_user: User = Depends(require_admin),
    db: DbSession = Depends(get_db),
):
    """Update an existing subject's details."""
    client_ip = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent")

    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found.")

    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields provided for update.")

    # If changing code/branch/semester, check uniqueness
    new_code = update_data.get("subject_code", subject.subject_code).strip()
    new_branch = update_data.get("branch", subject.branch).strip()
    new_semester = update_data.get("semester", subject.semester)

    if (new_code != subject.subject_code or new_branch != subject.branch or new_semester != subject.semester):
        conflict = db.query(Subject).filter(
            Subject.subject_code == new_code,
            Subject.branch == new_branch,
            Subject.semester == new_semester,
            Subject.id != subject_id,
        ).first()
        if conflict:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Subject '{new_code}' already exists for {new_branch} Semester {new_semester}.",
            )

    for field, value in update_data.items():
        if hasattr(subject, field):
            setattr(subject, field, value.strip() if isinstance(value, str) else value)

    db.commit()
    db.refresh(subject)

    log_security_event(
        event_type="ADMIN_SUBJECT_UPDATED",
        user_id=current_user.id,
        email=current_user.email,
        ip_address=client_ip,
        user_agent=ua,
        detail=f"Admin updated subject #{subject.id} ({subject.subject_code}). Fields: {list(update_data.keys())}",
    )

    return subject


# ── Delete / Deactivate Subject (Admin Only) ─────────────────
@router.delete("/api/admin/subjects/{subject_id}", response_model=MessageResponse)
def admin_delete_subject(
    subject_id: int,
    request: Request,
    current_user: User = Depends(require_admin),
    db: DbSession = Depends(get_db),
):
    """Soft-delete a subject by setting status to 'inactive'."""
    client_ip = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent")

    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found.")

    subject.status = SubjectStatus.inactive
    db.commit()

    log_security_event(
        event_type="ADMIN_SUBJECT_DEACTIVATED",
        user_id=current_user.id,
        email=current_user.email,
        ip_address=client_ip,
        user_agent=ua,
        detail=f"Admin deactivated subject #{subject.id} ({subject.subject_code} - {subject.subject_name}).",
    )

    return MessageResponse(message=f"Subject '{subject.subject_code} — {subject.subject_name}' has been deactivated.")


# ═══════════════════════════════════════════════════════════════
#  PUBLIC SUBJECT API (for Teacher dropdown)
# ═══════════════════════════════════════════════════════════════

@router.get("/api/subjects", response_model=SubjectListResponse)
def get_subjects(
    branch: Optional[str] = Query(None),
    semester: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """
    Fetch active subjects, optionally filtered by branch and semester.
    Available to any authenticated user (teachers use this to populate dropdowns).
    """
    query = db.query(Subject).filter(Subject.status == SubjectStatus.active)

    if branch:
        query = query.filter(Subject.branch == branch.strip())
    if semester is not None:
        query = query.filter(Subject.semester == semester)

    subjects = query.order_by(Subject.subject_code).all()

    return SubjectListResponse(
        items=[SubjectResponse.model_validate(s) for s in subjects],
        total=len(subjects),
    )
