"""
FastAPI dependency injection providers.
- get_db: yields a SQLAlchemy session per request
- get_current_user / require_auth: extracts and validates session cookie (or Bearer fallback)
- require_role(*roles): enforces role-based authorization boundaries
"""

import logging
from typing import Optional, Callable
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session as DbSession
from core.database import SessionLocal
from core.config import get_settings
from core.security import decode_access_token
from services.session_service import validate_session
from services.audit_service import log_security_event
from models.user import User
from models.session import Session as SessionModel

logger = logging.getLogger(__name__)
settings = get_settings()


def get_db():
    """Yield a database session and close it after request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    request: Request,
    db: DbSession = Depends(get_db),
) -> User:
    """
    Authenticate user via HttpOnly session cookie (primary) or Bearer token (fallback).
    Validates session state, idle timeout, and absolute expiration.
    Attaches user and session to request.state.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    raw_token: Optional[str] = None
    auth_method = "cookie"

    # 1. Cookie-first session extraction
    session_cookie = request.cookies.get(settings.SESSION_COOKIE_NAME)
    if session_cookie:
        raw_token = session_cookie
    else:
        # 2. Programmatic API fallback: Authorization header
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            raw_token = auth_header[7:].strip()
            auth_method = "bearer"

    if not raw_token:
        raise credentials_exception

    # 3. Validate against server-side sessions table
    session_record, failure_reason = validate_session(db, raw_token)

    if session_record:
        user = db.query(User).filter(User.id == session_record.user_id).first()
        if not user:
            raise credentials_exception

        # Attach to request state for downstream handlers
        request.state.user = user
        request.state.session = session_record
        request.state.raw_session_token = raw_token
        return user

    # 4. Fallback for legacy JWT tokens if auth_method was bearer
    if auth_method == "bearer":
        payload = decode_access_token(raw_token)
        if payload and "sub" in payload:
            user = db.query(User).filter(User.id == int(payload["sub"])).first()
            if user:
                request.state.user = user
                request.state.session = None
                request.state.raw_session_token = None
                return user

    # If session invalid or expired, log unauthorized attempt
    log_security_event(
        event_type="UNAUTHORIZED_ACCESS_ATTEMPT",
        ip_address=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent"),
        status="FAILURE",
        detail=f"Authentication failed: {failure_reason or 'Invalid session credential'}",
    )
    raise credentials_exception


# Alias for explicit naming
require_auth = get_current_user


# Re-export authorization helpers from centralized authorization module
from core.authorization import (
    require_role,
    require_permission,
    require_admin,
    require_faculty_or_admin,
    require_hod_or_admin,
    check_submission_access,
    check_report_access,
    check_teacher_section_access,
)
