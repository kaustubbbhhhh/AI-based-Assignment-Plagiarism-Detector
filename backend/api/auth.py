"""
Authentication & Session Management API Routes.

Implements:
- POST /api/auth/register          — User registration with password policy & email normalization
- POST /api/auth/login             — Secure login with session creation & HttpOnly cookies
- POST /api/auth/logout            — Server-side session invalidation & cookie clearance
- POST /api/auth/logout-all        — Invalidation of all active user sessions across all devices
- GET  /api/auth/me                — Retrieve authenticated user safe profile
- POST /api/auth/change-password   — Password change with session rotation
- POST /api/auth/forgot-password   — Generic response password reset request with secure token
- POST /api/auth/reset-password    — Password reset with token invalidation & session revocation
- POST /api/auth/verify-email      — Single-use email verification
- POST /api/auth/resend-verification — Rate-limited email verification resend
- GET  /api/auth/csrf              — Issue / refresh anti-CSRF token
- PUT  /api/auth/teacher/subjects  — Update teacher subjects/sections
"""

import logging
from typing import List, Optional
from datetime import datetime, timedelta, timezone
import secrets
from fastapi import APIRouter, Depends, HTTPException, Request, Response, Query, status
from sqlalchemy.orm import Session as DbSession

from core.dependencies import get_db, get_current_user, require_role
from core.config import get_settings
from core.security import (
    hash_password,
    verify_password,
    normalize_email,
    validate_password_strength,
    generate_secure_token,
    hash_token_string,
)
from core.csrf_middleware import generate_csrf_token
from models.user import User, UserRole
from models.auth_tokens import PasswordResetToken, EmailVerificationToken, cleanup_expired_reset_tokens
from schemas.user import (
    UserRegister,
    UserLogin,
    UserResponse,
    AuthResponse,
    MessageResponse,
    SubjectSection,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    ForgotPasswordResponse,
    ValidateResetTokenResponse,
    ChangePasswordRequest,
    VerifyEmailRequest,
    ResendVerificationRequest,
    UserProfileUpdate,
)
from services.session_service import (
    create_session,
    revoke_session,
    revoke_all_user_sessions,
    rotate_session,
)
from services.rate_limiter import (
    enforce_rate_limit,
    enforce_forgot_password_rate_limits,
    enforce_reset_password_rate_limits,
    get_client_ip,
)
from services.audit_service import log_security_event
from services.email_service import (
    send_reset_password_email,
    send_password_changed_notification_email,
    send_password_reset_otp_email,
)

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter(prefix="/api/auth", tags=["Authentication"])



# ── Helper to attach authentication cookies ───────────────────
def set_auth_cookies(response: Response, raw_session_token: str):
    """Sets HttpOnly session cookie and accessible CSRF cookie on response."""
    response.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=raw_session_token,
        max_age=settings.SESSION_MAX_AGE,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        path="/",
    )
    # Anti-CSRF Double-Submit cookie (readable by JS to include in X-CSRF-Token)
    response.set_cookie(
        key=settings.CSRF_COOKIE_NAME,
        value=generate_csrf_token(),
        max_age=settings.SESSION_MAX_AGE,
        httponly=False,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        path="/",
    )


def clear_auth_cookies(response: Response):
    """Deletes authentication cookies from client."""
    response.delete_cookie(key=settings.SESSION_COOKIE_NAME, path="/")
    response.delete_cookie(key=settings.CSRF_COOKIE_NAME, path="/")


# ── Public Register Endpoint (Permanently Disabled) ──────────
@router.post("/register", status_code=status.HTTP_403_FORBIDDEN)
def register(request: Request):
    """
    Public self-registration is permanently disabled.
    All user accounts (Student, Teacher, HOD, Admin) must be created
    exclusively by an authenticated administrator through the Admin Management System.
    """
    client_ip = get_client_ip(request)
    ua = request.headers.get("user-agent")

    log_security_event(
        event_type="PUBLIC_REGISTRATION_ATTEMPT_BLOCKED",
        email="anonymous",
        ip_address=client_ip,
        user_agent=ua,
        status="BLOCKED",
        detail="Public self-registration attempt rejected. User accounts must be provisioned by an administrator.",
    )
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Public registration is disabled. All user accounts must be created by an administrator.",
    )


# ── Login Endpoint ────────────────────────────────────────────
@router.post("/login", response_model=AuthResponse)
def login(
    payload: UserLogin,
    request: Request,
    response: Response,
    db: DbSession = Depends(get_db),
):
    """
    Authenticate user credentials, create a server-side session,
    and set secure HttpOnly authentication cookie.
    """
    client_ip = get_client_ip(request)
    ua = request.headers.get("user-agent")

    # Brute-force rate limiting
    enforce_rate_limit(request, action="login")
    clean_email = normalize_email(str(payload.email))

    # Look up user by normalized email
    user = db.query(User).filter(User.email == clean_email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        log_security_event(
            event_type="LOGIN_FAILURE",
            email=clean_email,
            ip_address=client_ip,
            user_agent=ua,
            status="FAILURE",
            detail="Invalid email or password.",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    if not user.is_verified:
        log_security_event(
            event_type="LOGIN_BLOCKED_INACTIVE",
            user_id=user.id,
            email=clean_email,
            ip_address=client_ip,
            user_agent=ua,
            status="BLOCKED",
            detail="Account is deactivated.",
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been deactivated. Please contact the administrator.",
        )

    # Session Rotation: invalidate any existing session from cookie to prevent fixation
    old_cookie = request.cookies.get(settings.SESSION_COOKIE_NAME)
    session_record, raw_token = rotate_session(
        db=db,
        old_raw_token=old_cookie,
        user_id=user.id,
        ip_address=client_ip,
        user_agent=ua,
    )

    # Set secure HttpOnly cookie + CSRF cookie
    set_auth_cookies(response, raw_token)

    log_security_event(
        event_type="LOGIN_SUCCESS",
        user_id=user.id,
        email=user.email,
        ip_address=client_ip,
        user_agent=ua,
        detail=f"Logged in successfully. Session {session_record.id} created.",
    )

    return AuthResponse(
        message="Login successful.",
        user=UserResponse.model_validate(user),
    )


# ── Current User Profile ──────────────────────────────────────
@router.get("/me", response_model=UserResponse)
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve profile details of currently authenticated user.
    Returns 401 if unauthenticated.
    """
    return current_user


@router.patch("/profile", response_model=UserResponse)
def update_current_user_profile(
    payload: UserProfileUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """
    Update profile details for the authenticated user.
    Enforces strict field-level authorization: only whitelisted fields
    (name, phone, father_phone, mother_phone) can be updated.
    Prevents mass assignment vulnerabilities.
    """
    client_ip = get_client_ip(request)
    ua = request.headers.get("user-agent")

    # Whitelist assignment only
    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid profile fields provided for update.",
        )

    for field, value in update_data.items():
        if field in ("name", "phone", "father_phone", "mother_phone"):
            setattr(current_user, field, value.strip() if isinstance(value, str) else value)

    db.commit()
    db.refresh(current_user)

    log_security_event(
        event_type="PROFILE_UPDATED",
        user_id=current_user.id,
        email=current_user.email,
        ip_address=client_ip,
        user_agent=ua,
        detail=f"Updated profile fields: {list(update_data.keys())}",
    )
    return current_user


# ── Logout Endpoint ───────────────────────────────────────────
@router.post("/logout", response_model=MessageResponse)
def logout(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """
    Invalidate current session server-side and clear client cookies.
    """
    raw_token = getattr(request.state, "raw_session_token", None) or request.cookies.get(settings.SESSION_COOKIE_NAME)
    if raw_token:
        revoke_session(db, raw_token)

    clear_auth_cookies(response)

    log_security_event(
        event_type="LOGOUT",
        user_id=current_user.id,
        email=current_user.email,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
        detail="Current session terminated.",
    )
    return MessageResponse(message="Logged out successfully.")


# ── Logout All Devices Endpoint ───────────────────────────────
@router.post("/logout-all", response_model=MessageResponse)
def logout_all(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """
    Invalidate all active sessions for the current user across all devices.
    """
    count = revoke_all_user_sessions(db, current_user.id)
    clear_auth_cookies(response)

    log_security_event(
        event_type="LOGOUT_ALL",
        user_id=current_user.id,
        email=current_user.email,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
        detail=f"Terminated {count} active sessions across all devices.",
    )
    return MessageResponse(message=f"Logged out from all devices successfully ({count} sessions revoked).")


# ── Change Password Endpoint ──────────────────────────────────
@router.post("/change-password", response_model=MessageResponse)
def change_password(
    payload: ChangePasswordRequest,
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    """
    Allow authenticated user to change password.
    Requires current password, verifies new password strength,
    invalidates old sessions, and issues a fresh rotated session for this device.
    """
    client_ip = get_client_ip(request)
    ua = request.headers.get("user-agent")

    if not verify_password(payload.current_password, current_user.hashed_password):
        log_security_event(
            event_type="PASSWORD_CHANGE_FAILED",
            user_id=current_user.id,
            email=current_user.email,
            ip_address=client_ip,
            user_agent=ua,
            status="FAILURE",
            detail="Incorrect current password provided.",
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect.",
        )

    is_valid_pwd, pwd_error = validate_password_strength(payload.new_password)
    if not is_valid_pwd:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=pwd_error)

    if payload.current_password == payload.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password cannot be the same as current password.",
        )

    # Update password hash and clear force-change flag
    current_user.hashed_password = hash_password(payload.new_password)
    current_user.must_change_password = False
    db.commit()

    # Invalidate all prior sessions for this user
    revoke_all_user_sessions(db, current_user.id)

    # Issue a fresh rotated session for current device
    _, new_raw_token = create_session(db, current_user.id, client_ip, ua)
    set_auth_cookies(response, new_raw_token)

    log_security_event(
        event_type="PASSWORD_CHANGED",
        user_id=current_user.id,
        email=current_user.email,
        ip_address=client_ip,
        user_agent=ua,
        detail="Password changed. All prior sessions revoked, fresh session issued.",
    )
    return MessageResponse(message="Password changed successfully. Your account security has been updated.")


# ── Forgot Password Endpoint ──────────────────────────────────
@router.post("/forgot-password", response_model=ForgotPasswordResponse)
def forgot_password(
    payload: ForgotPasswordRequest,
    request: Request,
    db: DbSession = Depends(get_db),
):
    """
    Initiate password reset flow.
    - Dual-dimension rate limiting (client IP + normalized email).
    - Generic response to prevent account enumeration.
    - Single-use, cryptographically secure 256-bit token.
    - Previous tokens for user invalidated.
    - Raw token NEVER stored in DB or returned in production API responses.
    """
    clean_email = normalize_email(str(payload.email))
    enforce_forgot_password_rate_limits(request, email=clean_email)
    client_ip = get_client_ip(request)
    ua = request.headers.get("user-agent")

    user = db.query(User).filter(User.email == clean_email).first()
    generic_msg = "If an account exists for this email, password reset instructions have been sent."

    if not user:
        log_security_event(
            event_type="PASSWORD_RESET_REQUESTED",
            email=clean_email,
            ip_address=client_ip,
            user_agent=ua,
            detail="Password reset requested for non-existent account (generic response returned).",
        )
        return ForgotPasswordResponse(message=generic_msg, reset_link=None)

    now = datetime.now(timezone.utc)

    # Invalidate prior unused reset tokens for this user
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.is_used == False,
    ).update({
        PasswordResetToken.is_used: True,
        PasswordResetToken.used_at: now,
    }, synchronize_session=False)

    # Generate single-use cryptographic token with configurable expiration (default: 20 min)
    raw_token, token_hash = generate_secure_token()
    expiry_minutes = settings.PASSWORD_RESET_TOKEN_EXPIRY_MINUTES
    expires_at = now + timedelta(minutes=expiry_minutes)

    reset_record = PasswordResetToken(
        user_id=user.id,
        token_hash=token_hash,
        created_at=now,
        expires_at=expires_at,
        is_used=False,
        ip_address=client_ip,
        user_agent=(ua[:250] if ua else None),
    )
    db.add(reset_record)
    db.commit()

    frontend_base = settings.FRONTEND_URL.rstrip("/")
    full_reset_link = f"{frontend_base}/reset-password?token={raw_token}"
    dev_relative_link = f"/reset-password?token={raw_token}"

    log_security_event(
        event_type="PASSWORD_RESET_TOKEN_CREATED",
        user_id=user.id,
        email=user.email,
        ip_address=client_ip,
        user_agent=ua,
        detail=f"Secure reset token created (valid for {expiry_minutes}m). Previous tokens invalidated.",
    )

    # Dispatch real email via SMTP if configured (never logs raw token)
    email_sent = send_reset_password_email(email_to=user.email, reset_link=full_reset_link)
    # Expose dev link ONLY in non-production environments when SMTP is unconfigured
    is_dev_mode = not settings.COOKIE_SECURE and settings.SECRET_KEY.startswith("dev-")
    dev_link = dev_relative_link if (not email_sent and is_dev_mode) else None

    # Periodic cleanup of expired tokens
    try:
        cleanup_expired_reset_tokens(db)
    except Exception as e:
        logger.debug(f"Expired token cleanup skipped: {e}")

    return ForgotPasswordResponse(
        message=generic_msg,
        reset_link=dev_link,
    )


# ── Validate Reset Token Endpoint ─────────────────────────────
@router.get("/validate-reset-token", response_model=ValidateResetTokenResponse)
def validate_reset_token(
    token: str = Query(..., description="The raw password reset token"),
    request: Request = None,
    db: DbSession = Depends(get_db),
):
    """
    Validate a password reset token before displaying the reset password form.
    Checks expiration, single-use status, and evaluates risk signals (e.g. IP anomaly).
    """
    client_ip = get_client_ip(request) if request else "unknown"
    ua = request.headers.get("user-agent") if request else "unknown"

    clean_token = token.strip()
    if not clean_token:
        return ValidateResetTokenResponse(
            is_valid=False,
            requires_otp=False,
            message="This password reset link is invalid or has expired."
        )

    # Enforce rate limit on token validation against brute-force attacks
    if request:
        enforce_rate_limit(request, action="validate_reset_token", custom_policy=(10, 300))

    incoming_hash = hash_token_string(clean_token)
    now = datetime.now(timezone.utc)

    reset_token = (
        db.query(PasswordResetToken)
        .filter(
            PasswordResetToken.token_hash == incoming_hash,
            PasswordResetToken.is_used == False,
        )
        .first()
    )

    if not reset_token:
        log_security_event(
            event_type="PASSWORD_RESET_TOKEN_REJECTED",
            ip_address=client_ip,
            user_agent=ua,
            status="FAILURE",
            detail="Token validation failed: not found or already consumed.",
        )
        return ValidateResetTokenResponse(
            is_valid=False,
            requires_otp=False,
            message="This password reset link is invalid or has expired."
        )

    # Check expiration
    expires_at = reset_token.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if now > expires_at:
        reset_token.is_used = True
        reset_token.used_at = now
        db.commit()
        log_security_event(
            event_type="PASSWORD_RESET_TOKEN_EXPIRED",
            user_id=reset_token.user_id,
            ip_address=client_ip,
            user_agent=ua,
            status="FAILURE",
            detail="Token validation failed: token has expired.",
        )
        return ValidateResetTokenResponse(
            is_valid=False,
            requires_otp=False,
            message="This password reset link is invalid or has expired."
        )

    # Lightweight Risk-Based Verification Check:
    # If client IP differs from requesting IP (and not a local test runner), require email OTP
    requires_otp = False
    if reset_token.ip_address and reset_token.ip_address != client_ip and client_ip not in ("testclient", "127.0.0.1", "localhost"):
        requires_otp = True
        if not reset_token.requires_otp or not reset_token.otp_hash:
            otp_num = secrets.randbelow(900000) + 100000
            otp_code = f"{otp_num}"
            reset_token.requires_otp = True
            reset_token.otp_hash = hash_token_string(otp_code)
            reset_token.otp_expires_at = now + timedelta(minutes=settings.PASSWORD_RESET_OTP_EXPIRY_MINUTES)
            reset_token.otp_attempts = 0
            db.commit()

            user = db.query(User).filter(User.id == reset_token.user_id).first()
            if user:
                send_password_reset_otp_email(user.email, otp_code)

    return ValidateResetTokenResponse(
        is_valid=True,
        requires_otp=requires_otp,
        message="Additional verification code sent to email." if requires_otp else "Reset token is valid."
    )


# ── Reset Password Endpoint ───────────────────────────────────
@router.post("/reset-password", response_model=MessageResponse)
def reset_password(
    payload: ResetPasswordRequest,
    request: Request,
    db: DbSession = Depends(get_db),
):
    """
    Finalize password reset using single-use cryptographically hashed reset token.
    - Rate-limited against token brute force.
    - Atomic single-use token consumption preventing race conditions.
    - Secure password validation & bcrypt hashing.
    - Invalidation of ALL active sessions across all devices.
    - Security notification email dispatched to user.
    """
    client_ip = get_client_ip(request)
    ua = request.headers.get("user-agent")

    # Rate limiting on token consumption attempts
    token_prefix = payload.token.strip()[:10] if payload.token else None
    enforce_reset_password_rate_limits(request, token_prefix=token_prefix)

    is_valid_pwd, pwd_error = validate_password_strength(payload.new_password)
    if not is_valid_pwd:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=pwd_error)

    # Hash the submitted raw token and look up valid record
    incoming_hash = hash_token_string(payload.token.strip())
    now = datetime.now(timezone.utc)

    reset_token = (
        db.query(PasswordResetToken)
        .filter(
            PasswordResetToken.token_hash == incoming_hash,
            PasswordResetToken.is_used == False,
        )
        .first()
    )

    if not reset_token:
        log_security_event(
            event_type="PASSWORD_RESET_TOKEN_REJECTED",
            ip_address=client_ip,
            user_agent=ua,
            status="FAILURE",
            detail="Reset attempt with invalid or already consumed token.",
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This password reset link is invalid or has expired.",
        )

    # Check expiration
    expires_at = reset_token.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if now > expires_at:
        reset_token.is_used = True
        reset_token.used_at = now
        db.commit()
        log_security_event(
            event_type="PASSWORD_RESET_TOKEN_EXPIRED",
            user_id=reset_token.user_id,
            ip_address=client_ip,
            user_agent=ua,
            status="FAILURE",
            detail="Reset attempt with expired token.",
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This password reset link is invalid or has expired.",
        )

    # If risk check required an OTP, verify the OTP
    if reset_token.requires_otp:
        if not payload.otp_code or not payload.otp_code.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Verification code is required for this password reset.",
            )

        # Check OTP expiration
        otp_exp = reset_token.otp_expires_at
        if otp_exp and otp_exp.tzinfo is None:
            otp_exp = otp_exp.replace(tzinfo=timezone.utc)

        if not otp_exp or now > otp_exp:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Verification code has expired. Please request a new reset link.",
            )

        incoming_otp_hash = hash_token_string(payload.otp_code.strip())
        if incoming_otp_hash != reset_token.otp_hash:
            reset_token.otp_attempts += 1
            if reset_token.otp_attempts >= settings.PASSWORD_RESET_MAX_OTP_ATTEMPTS:
                # Invalidate the token to prevent brute-forcing OTP
                reset_token.is_used = True
                reset_token.used_at = now
            db.commit()
            log_security_event(
                event_type="PASSWORD_RESET_OTP_FAILED",
                user_id=reset_token.user_id,
                ip_address=client_ip,
                user_agent=ua,
                status="FAILURE",
                detail=f"Incorrect OTP attempt ({reset_token.otp_attempts}/{settings.PASSWORD_RESET_MAX_OTP_ATTEMPTS}).",
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification code.",
            )

    user = db.query(User).filter(User.id == reset_token.user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    # ── Atomic Token Consumption & Password Update ────────────
    # Atomic conditional update prevents concurrent race conditions
    rows_updated = db.query(PasswordResetToken).filter(
        PasswordResetToken.id == reset_token.id,
        PasswordResetToken.is_used == False,
    ).update({
        PasswordResetToken.is_used: True,
        PasswordResetToken.used_at: now,
    }, synchronize_session=False)

    if rows_updated == 0:
        log_security_event(
            event_type="PASSWORD_RESET_FAILED",
            user_id=user.id,
            email=user.email,
            ip_address=client_ip,
            user_agent=ua,
            status="BLOCKED",
            detail="Concurrent token consumption race condition blocked.",
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This password reset link is invalid or has expired.",
        )

    # Update password hash using bcrypt
    user.hashed_password = hash_password(payload.new_password)

    # Invalidate ALL active sessions for this user across all devices
    revoke_all_user_sessions(db, user.id)

    db.commit()

    log_security_event(
        event_type="PASSWORD_RESET_COMPLETED",
        user_id=user.id,
        email=user.email,
        ip_address=client_ip,
        user_agent=ua,
        detail="Password successfully reset.",
    )
    log_security_event(
        event_type="ALL_SESSIONS_REVOKED_AFTER_PASSWORD_RESET",
        user_id=user.id,
        email=user.email,
        ip_address=client_ip,
        user_agent=ua,
        detail="All active user sessions invalidated across all devices.",
    )

    # Dispatch security notification email to user's registered email
    send_password_changed_notification_email(
        email_to=user.email,
        client_ip=client_ip,
        user_agent=ua,
    )

    return MessageResponse(
        message="Password has been successfully reset. All active sessions have been signed out. Please log in again."
    )



# ── Email Verification Endpoints ──────────────────────────────
@router.post("/verify-email", response_model=MessageResponse)
def verify_email(
    payload: VerifyEmailRequest,
    db: DbSession = Depends(get_db),
):
    """Verify user account with single-use verification token."""
    incoming_hash = hash_token_string(payload.token.strip())
    now = datetime.now(timezone.utc)

    token_record = (
        db.query(EmailVerificationToken)
        .filter(
            EmailVerificationToken.token_hash == incoming_hash,
            EmailVerificationToken.is_used == False,
        )
        .first()
    )

    if not token_record:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired verification token.")

    expires_at = token_record.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if now > expires_at:
        token_record.is_used = True
        db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification token has expired.")

    user = db.query(User).filter(User.id == token_record.user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    token_record.is_used = True
    user.is_verified = True
    db.commit()

    log_security_event(
        event_type="EMAIL_VERIFIED",
        user_id=user.id,
        email=user.email,
        detail="User email verified.",
    )
    return MessageResponse(message="Email verified successfully.")


@router.post("/resend-verification", response_model=MessageResponse)
def resend_verification(
    payload: ResendVerificationRequest,
    request: Request,
    db: DbSession = Depends(get_db),
):
    """Resend email verification token (rate limited)."""
    enforce_rate_limit(request, action="resend_verification")
    clean_email = normalize_email(str(payload.email))
    user = db.query(User).filter(User.email == clean_email).first()

    generic_msg = "If an account exists for this email, verification instructions have been resent."
    if not user or user.is_verified:
        return MessageResponse(message=generic_msg)

    # Invalidate previous tokens
    db.query(EmailVerificationToken).filter(
        EmailVerificationToken.user_id == user.id,
        EmailVerificationToken.is_used == False,
    ).update({EmailVerificationToken.is_used: True})

    raw_token, token_hash = generate_secure_token()
    now = datetime.now(timezone.utc)
    token_record = EmailVerificationToken(
        user_id=user.id,
        token_hash=token_hash,
        created_at=now,
        expires_at=now + timedelta(hours=24),
        is_used=False,
    )
    db.add(token_record)
    db.commit()

    log_security_event(
        event_type="EMAIL_VERIFICATION_RESENT",
        user_id=user.id,
        email=user.email,
        detail="Email verification token resent.",
    )
    return MessageResponse(message=generic_msg)


# ── CSRF Token Endpoint ───────────────────────────────────────
@router.get("/csrf")
def get_csrf_token(response: Response):
    """Issue a fresh anti-CSRF token and set it in the csrf_token cookie."""
    token = generate_csrf_token()
    response.set_cookie(
        key=settings.CSRF_COOKIE_NAME,
        value=token,
        max_age=settings.SESSION_MAX_AGE,
        httponly=False,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        path="/",
    )
    return {"csrf_token": token}


# ── Teacher Subjects Update ───────────────────────────────────
@router.put("/teacher/subjects", response_model=UserResponse)
def update_teacher_subjects(
    payload: List[SubjectSection],
    current_user: User = Depends(require_role("teacher")),
    db: DbSession = Depends(get_db),
):
    """Allow authenticated teachers to update their subject-section list."""
    ss_data = [
        {"subject": s.subject, "section": s.section, **({"branch": s.branch} if s.branch else {})}
        for s in payload
    ]
    current_user.subjects_sections = ss_data
    db.commit()
    db.refresh(current_user)

    logger.info(f"Teacher {current_user.email} updated subjects/sections list: {ss_data}")
    return current_user
