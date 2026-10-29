"""
Rate Limiting & Brute-Force Protection Service.

Implements a thread-safe sliding window rate limiter to protect
authentication endpoints from brute-force and credential-stuffing attacks.
"""

import time
import threading
from typing import Dict, List, Tuple, Optional
from fastapi import Request, HTTPException, status
from services.audit_service import log_security_event

# Lock for in-memory tracker synchronization
_rate_limit_lock = threading.Lock()
# Storage format: { "action:key": [timestamp1, timestamp2, ...] }
_rate_limits: Dict[str, List[float]] = {}

# Default policies: (max_requests, window_seconds)
RATE_LIMIT_POLICIES = {
    "login": (10, 300),              # 10 attempts per 5 minutes per IP
    "login_account": (5, 300),       # 5 failed attempts per 5 minutes per account
    "register": (15, 3600),          # 15 registrations per hour per IP
    "forgot_password": (5, 900),     # 5 reset requests per 15 minutes per IP
    "reset_password": (5, 900),      # 5 reset attempts per 15 minutes per IP
    "resend_verification": (3, 900), # 3 resends per 15 minutes per IP
}


def is_rate_limited(action: str, key: str, max_requests: int, window_seconds: int) -> Tuple[bool, int]:
    """
    Check if a key is rate limited for a given action using sliding window.
    Returns (is_limited, retry_after_seconds).
    """
    composite_key = f"{action}:{key}"
    now = time.time()
    cutoff = now - window_seconds

    with _rate_limit_lock:
        timestamps = _rate_limits.get(composite_key, [])
        # Discard expired timestamps
        timestamps = [ts for ts in timestamps if ts > cutoff]
        
        if len(timestamps) >= max_requests:
            retry_after = int(timestamps[0] + window_seconds - now) + 1
            _rate_limits[composite_key] = timestamps
            return True, max(1, retry_after)

        timestamps.append(now)
        _rate_limits[composite_key] = timestamps
        return False, 0


def get_client_ip(request: Request) -> str:
    """Extract client IP, taking X-Forwarded-For into account if behind trusted proxy."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def enforce_rate_limit(
    request: Request,
    action: str,
    identifier: Optional[str] = None,
    custom_policy: Optional[Tuple[int, int]] = None
):
    """
    Dependency helper to enforce rate limiting on endpoints.
    Raises 429 Too Many Requests if threshold is exceeded.
    """
    policy = custom_policy or RATE_LIMIT_POLICIES.get(action, (20, 60))
    max_requests, window_seconds = policy

    client_ip = get_client_ip(request)
    target_key = f"{client_ip}:{identifier.strip().lower()}" if identifier else client_ip

    limited, retry_after = is_rate_limited(action, target_key, max_requests, window_seconds)
    if limited:
        log_security_event(
            event_type="RATE_LIMIT_EXCEEDED",
            ip_address=client_ip,
            user_agent=request.headers.get("user-agent"),
            status="BLOCKED",
            detail=f"Action '{action}' throttled. Retry after {retry_after}s.",
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many requests. Please try again in {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)},
        )


def enforce_forgot_password_rate_limits(request: Request, email: Optional[str] = None):
    """
    Enforce dual-dimension rate limiting:
    1. Per IP: throttles requests from a given IP address.
    2. Per Account/Email: throttles requests targeting a specific email (normalized).
    """
    from core.config import get_settings
    settings = get_settings()
    window = settings.PASSWORD_RESET_RATE_LIMIT_WINDOW
    ip_limit = settings.PASSWORD_RESET_RATE_LIMIT_IP
    email_limit = settings.PASSWORD_RESET_RATE_LIMIT_EMAIL

    # 1. IP check
    enforce_rate_limit(request, action="forgot_password", custom_policy=(ip_limit, window))

    # 2. Email check (if provided)
    if email:
        clean_email = email.strip().lower()
        enforce_rate_limit(
            request,
            action="forgot_password_email",
            identifier=clean_email,
            custom_policy=(email_limit, window)
        )


def enforce_reset_password_rate_limits(request: Request, token_prefix: Optional[str] = None):
    """
    Enforce dual-dimension rate limiting for password reset attempts:
    1. Per IP limit
    2. Per Token attempt limit (protects against token brute-force)
    """
    from core.config import get_settings
    settings = get_settings()
    window = settings.PASSWORD_RESET_RATE_LIMIT_WINDOW
    ip_limit = settings.PASSWORD_RESET_RATE_LIMIT_IP

    # 1. IP limit
    enforce_rate_limit(request, action="reset_password", custom_policy=(ip_limit, window))

    # 2. Token attempt limit
    if token_prefix:
        enforce_rate_limit(
            request,
            action="reset_password_token",
            identifier=token_prefix,
            custom_policy=(ip_limit, window)
        )



def reset_rate_limit_for_key(action: str, key: str):
    """Reset rate limiter after a successful security action (e.g. successful login)."""
    composite_key = f"{action}:{key}"
    with _rate_limit_lock:
        if composite_key in _rate_limits:
            del _rate_limits[composite_key]


def clear_all_rate_limits():
    """Clear all rate limit state (used in test suites)."""
    with _rate_limit_lock:
        _rate_limits.clear()

