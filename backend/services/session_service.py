"""
Server-side Session Management Service.

Handles:
- Cryptographically secure session token generation
- SHA-256 token hashing for database storage
- Idle timeout & absolute timeout validation
- Session rotation (fixation defense)
- Single-session and all-sessions revocation
"""

import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from sqlalchemy.orm import Session as DbSession
from models.session import Session as SessionModel
from core.config import get_settings
from services.audit_service import log_security_event

settings = get_settings()


def hash_token(raw_token: str) -> str:
    """Compute SHA-256 hash of a raw token for secure database storage/lookup."""
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def create_session(
    db: DbSession,
    user_id: int,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> Tuple[SessionModel, str]:
    """
    Create a new server-side authenticated session.
    Returns (SessionModel_instance, raw_session_token).
    Only the raw_session_token is returned to the client in the HttpOnly cookie.
    The database only ever stores the SHA-256 hash.
    """
    raw_token = secrets.token_urlsafe(32)
    token_hash = hash_token(raw_token)

    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(seconds=settings.SESSION_MAX_AGE)

    session = SessionModel(
        session_token_hash=token_hash,
        user_id=user_id,
        created_at=now,
        expires_at=expires_at,
        last_activity_at=now,
        ip_address=ip_address,
        user_agent=user_agent[:490] if user_agent else None,
        is_revoked=False,
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    log_security_event(
        event_type="SESSION_CREATED",
        user_id=user_id,
        ip_address=ip_address,
        user_agent=user_agent,
        detail=f"Session ID {session.id} created.",
    )

    return session, raw_token


def validate_session(
    db: DbSession,
    raw_token: str,
) -> Tuple[Optional[SessionModel], Optional[str]]:
    """
    Validate a raw session token against the database.
    Checks:
      1. Token existence and active status (!is_revoked)
      2. Absolute expiration (now > expires_at)
      3. Idle inactivity timeout (now - last_activity_at > SESSION_IDLE_TIMEOUT)
    Updates last_activity_at on successful verification.

    Returns (session, None) on success, or (None, failure_reason) on failure.
    """
    if not raw_token:
        return None, "Missing session token"

    token_hash = hash_token(raw_token)
    session = (
        db.query(SessionModel)
        .filter(
            SessionModel.session_token_hash == token_hash,
            SessionModel.is_revoked == False,
        )
        .first()
    )

    if not session:
        return None, "Invalid or revoked session"

    now = datetime.now(timezone.utc)

    # Ensure timezone awareness for comparisons
    session_expires = session.expires_at
    if session_expires.tzinfo is None:
        session_expires = session_expires.replace(tzinfo=timezone.utc)

    session_last_activity = session.last_activity_at
    if session_last_activity.tzinfo is None:
        session_last_activity = session_last_activity.replace(tzinfo=timezone.utc)

    # 1. Check absolute expiration
    if now > session_expires:
        session.is_revoked = True
        db.commit()
        log_security_event(
            event_type="SESSION_EXPIRED",
            user_id=session.user_id,
            ip_address=session.ip_address,
            detail="Session exceeded maximum lifetime (SESSION_MAX_AGE).",
        )
        return None, "Session has expired"

    # 2. Check idle inactivity timeout
    idle_duration = (now - session_last_activity).total_seconds()
    if idle_duration > settings.SESSION_IDLE_TIMEOUT:
        session.is_revoked = True
        db.commit()
        log_security_event(
            event_type="SESSION_IDLE_TIMEOUT",
            user_id=session.user_id,
            ip_address=session.ip_address,
            detail=f"Session timed out after {int(idle_duration)}s idle.",
        )
        return None, "Session expired due to inactivity"

    # 3. Session is valid -> refresh last_activity_at
    session.last_activity_at = now
    db.commit()
    return session, None


def revoke_session(db: DbSession, raw_token: str) -> bool:
    """Revoke a single session by its raw token."""
    if not raw_token:
        return False

    token_hash = hash_token(raw_token)
    session = (
        db.query(SessionModel)
        .filter(SessionModel.session_token_hash == token_hash)
        .first()
    )
    if session and not session.is_revoked:
        session.is_revoked = True
        db.commit()
        log_security_event(
            event_type="SESSION_REVOKED",
            user_id=session.user_id,
            ip_address=session.ip_address,
            detail=f"Session {session.id} revoked.",
        )
        return True
    return False


def revoke_all_user_sessions(db: DbSession, user_id: int) -> int:
    """
    Revoke all active sessions belonging to a specific user.
    Used for 'Logout all devices' and after password reset/change.
    """
    count = (
        db.query(SessionModel)
        .filter(
            SessionModel.user_id == user_id,
            SessionModel.is_revoked == False,
        )
        .update({SessionModel.is_revoked: True}, synchronize_session="fetch")
    )
    db.commit()
    log_security_event(
        event_type="LOGOUT_ALL",
        user_id=user_id,
        detail=f"Revoked {count} active sessions for user {user_id}.",
    )
    return count


def rotate_session(
    db: DbSession,
    old_raw_token: Optional[str],
    user_id: int,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> Tuple[SessionModel, str]:
    """
    Rotate session on authentication boundaries to prevent session fixation.
    Revokes the old session if present, and creates a fresh authenticated session.
    """
    if old_raw_token:
        revoke_session(db, old_raw_token)
    return create_session(db, user_id, ip_address, user_agent)
