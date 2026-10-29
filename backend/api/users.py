"""
User Management & Administrative RBAC API Routes.

Implements:
- GET   /api/users            — Admin-only user list with search, filtering, and pagination
- GET   /api/users/{id}       — User detail (Admin or self)
- PATCH /api/users/{id}       — Admin user detail update
- PATCH /api/users/{id}/role  — Privileged role change with self-protection & session revocation
- DELETE /api/users/{id}      — Admin user deletion with self-deletion protection
- GET   /api/admin/system-settings — System configuration overview
- PATCH /api/admin/system-settings — System configuration update
"""

import math
import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Request, Query, status
from sqlalchemy.orm import Session as DbSession
from sqlalchemy import or_

from core.dependencies import get_db, get_current_user
from core.authorization import require_admin, require_role
from models.user import User, UserRole
from models.session import Session as SessionModel
from models.auth_tokens import PasswordResetToken, EmailVerificationToken
from schemas.user import (
    UserResponse,
    AdminUserUpdate,
    RoleUpdateRequest,
    UserPaginationResponse,
    MessageResponse,
    SystemSettingsSchema,
)
from services.session_service import revoke_all_user_sessions
from services.audit_service import log_security_event

logger = logging.getLogger(__name__)
router = APIRouter(tags=["User Management & Administration"])

# In-memory institutional system settings cache
_SYSTEM_SETTINGS = {
    "app_name": "PlagiarismAI",
    "environment": "production",
    "max_upload_size_mb": 25,
    "allowed_file_types": [".pdf", ".docx", ".doc", ".txt", ".png", ".jpg", ".jpeg"],
    "session_idle_timeout_seconds": 1800,
    "session_max_age_seconds": 86400,
    "registration_open": True,
    "maintenance_mode": False,
}


# ── 1. List Users (Admin Only) ─────────────────────────────────
@router.get("/api/users", response_model=UserPaginationResponse)
def list_users(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    role: Optional[str] = Query(None, description="Filter by role (student, teacher, hod, admin)"),
    q: Optional[str] = Query(None, description="Search term across name, email, enrollment_no"),
    current_user: User = Depends(require_admin),
    db: DbSession = Depends(get_db),
):
    """
    Paginated user directory restricted strictly to Administrators.
    Server-side filtering prevents unauthorized enumeration or data exposure.
    """
    query = db.query(User)

    if role:
        clean_role = role.strip().lower()
        query = query.filter(User.role == clean_role)

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


# ── 2. Get User Detail (Admin or Self) ─────────────────────────
@router.get("/api/users/{user_id}", response_model=UserResponse)
def get_user_detail(
    user_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """
    Retrieve user profile by ID.
    Enforces object-level authorization: users can only inspect their own account
    unless they hold the Administrator role.
    """
    role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)

    if role_val != "admin" and current_user.id != user_id:
        log_security_event(
            event_type="OBJECT_ACCESS_DENIED",
            user_id=current_user.id,
            email=current_user.email,
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent"),
            status="BLOCKED",
            detail=f"User {current_user.id} attempted to view User #{user_id} profile without admin privileges.",
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You do not have permission to view this user profile.",
        )

    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    return target_user


# ── 3. Update User (Admin Only) ────────────────────────────────
@router.patch("/api/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    payload: AdminUserUpdate,
    request: Request,
    current_user: User = Depends(require_admin),
    db: DbSession = Depends(get_db),
):
    """
    Administrative user update endpoint.
    Strictly whitelisted fields: name, phone, section, branch, department, is_verified.
    """
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid fields provided for update.",
        )

    if "email" in update_data and update_data["email"]:
        clean_email = normalize_email(str(update_data["email"]))
        existing = db.query(User).filter(User.email == clean_email, User.id != user_id).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email already exists.",
            )
        target_user.email = clean_email
        del update_data["email"]

    for field, value in update_data.items():
        if hasattr(target_user, field):
            setattr(target_user, field, value)

    db.commit()
    db.refresh(target_user)

    log_security_event(
        event_type="ADMIN_ACTION",
        user_id=current_user.id,
        email=current_user.email,
        ip_address=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent"),
        detail=f"Admin updated User #{target_user.id} fields: {list(update_data.keys())}",
    )
    return target_user


# ── 4. Change User Role (Admin Only with Protections) ──────────
@router.patch("/api/users/{user_id}/role", response_model=UserResponse)
def change_user_role(
    user_id: int,
    payload: RoleUpdateRequest,
    request: Request,
    current_user: User = Depends(require_admin),
    db: DbSession = Depends(get_db),
):
    """
    Privileged role transition endpoint:
    - Restricted exclusively to Administrators.
    - Prevents self-modification: An admin cannot modify their own role.
    - Validates target role.
    - Automatically revokes ALL active sessions of the target user to ensure
      instantaneous permission change across all devices.
    """
    # 1. Self-protection guard
    if current_user.id == user_id:
        log_security_event(
            event_type="PRIVILEGE_ESCALATION_ATTEMPT",
            user_id=current_user.id,
            email=current_user.email,
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent"),
            status="BLOCKED",
            detail="Admin attempted to modify their own role.",
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Self-role modification is prohibited. Another administrator must perform this action.",
        )

    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target user not found.",
        )

    old_role = target_user.role.value if hasattr(target_user.role, "value") else str(target_user.role)
    new_role = payload.role.strip().lower()

    if old_role == new_role:
        return target_user

    # 2. Update role
    target_user.role = UserRole(new_role)
    db.commit()
    db.refresh(target_user)

    # 3. Immediately revoke all active sessions for target user
    revoked_count = revoke_all_user_sessions(db, target_user.id)

    log_security_event(
        event_type="ROLE_CHANGE",
        user_id=current_user.id,
        email=current_user.email,
        ip_address=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent"),
        detail=f"Admin changed User #{target_user.id} ({target_user.email}) role: {old_role} -> {new_role}. Revoked {revoked_count} active sessions.",
    )

    return target_user


# ── 5. Delete User (Admin Only with Protections) ───────────────
@router.delete("/api/users/{user_id}", response_model=MessageResponse)
def delete_user(
    user_id: int,
    request: Request,
    current_user: User = Depends(require_admin),
    db: DbSession = Depends(get_db),
):
    """
    Administrative user deletion:
    - Prevents self-deletion.
    - Cascades removal of sessions and tokens.
    """
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own administrative account.",
        )

    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    target_email = target_user.email

    # Cascade remove sessions and auth tokens
    db.query(SessionModel).filter(SessionModel.user_id == user_id).delete()
    db.query(PasswordResetToken).filter(PasswordResetToken.user_id == user_id).delete()
    db.query(EmailVerificationToken).filter(EmailVerificationToken.user_id == user_id).delete()

    db.delete(target_user)
    db.commit()

    log_security_event(
        event_type="ADMIN_ACTION",
        user_id=current_user.id,
        email=current_user.email,
        ip_address=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent"),
        detail=f"Admin deleted User #{user_id} ({target_email}).",
    )

    return MessageResponse(message=f"User #{user_id} ({target_email}) successfully deleted.")


# ── 6. System Settings Management (Admin Only) ─────────────────
@router.get("/api/admin/system-settings", response_model=SystemSettingsSchema)
def get_system_settings(
    current_user: User = Depends(require_admin),
):
    """Retrieve current system security and operational parameters (Admin only)."""
    return SystemSettingsSchema(**_SYSTEM_SETTINGS)


@router.patch("/api/admin/system-settings", response_model=SystemSettingsSchema)
def update_system_settings(
    payload: SystemSettingsSchema,
    request: Request,
    current_user: User = Depends(require_admin),
):
    """Update institutional settings (Admin only)."""
    global _SYSTEM_SETTINGS
    _SYSTEM_SETTINGS.update(payload.model_dump())

    log_security_event(
        event_type="ADMIN_ACTION",
        user_id=current_user.id,
        email=current_user.email,
        ip_address=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent"),
        detail=f"Admin updated system settings: {payload.model_dump()}",
    )
    return SystemSettingsSchema(**_SYSTEM_SETTINGS)
