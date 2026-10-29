"""
CSRF Protection Middleware & Utilities.

Implements the Double Submit Cookie pattern:
1. Browser receives a readable `csrf_token` cookie (SameSite=Lax).
2. Frontend reads this cookie and includes it in the `X-CSRF-Token` request header.
3. Middleware verifies that state-changing requests (POST, PUT, PATCH, DELETE) with
   an active session cookie contain a matching `X-CSRF-Token` header.
4. Non-browser Bearer-authenticated API calls and safe methods (GET, HEAD, OPTIONS) are exempt.
"""

import hmac
import secrets
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from core.config import get_settings
from services.audit_service import log_security_event

settings = get_settings()

SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
EXEMPT_PATHS = {
    "/api/auth/login",
    "/api/auth/register",
    "/register",
    "/signup",
    "/api/auth/forgot-password",
    "/api/auth/reset-password",
    "/api/auth/verify-email",
    "/api/auth/resend-verification",
    "/api/health",
    "/docs",
    "/openapi.json",
    "/redoc",
}


def generate_csrf_token() -> str:
    """Generate a cryptographically random anti-CSRF token."""
    return secrets.token_urlsafe(32)


class CSRFMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        # If method is safe, proceed and ensure a CSRF cookie is present if missing
        if request.method in SAFE_METHODS:
            response = await call_next(request)
            if settings.CSRF_COOKIE_NAME not in request.cookies:
                token = generate_csrf_token()
                response.set_cookie(
                    key=settings.CSRF_COOKIE_NAME,
                    value=token,
                    max_age=settings.SESSION_MAX_AGE,
                    httponly=False,  # Accessible to client-side JS to put into X-CSRF-Token header
                    secure=settings.COOKIE_SECURE,
                    samesite=settings.COOKIE_SAMESITE,
                    path="/",
                )
            return response

        # Check if request path is exempt
        if request.url.path in EXEMPT_PATHS:
            response = await call_next(request)
            # Ensure fresh CSRF cookie is set on onboarding/login responses
            if settings.CSRF_COOKIE_NAME not in request.cookies:
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
            return response

        # If request is authenticated via Bearer token (non-browser API client), exempt from CSRF
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            return await call_next(request)

        # If session cookie is present, enforce CSRF validation
        session_cookie = request.cookies.get(settings.SESSION_COOKIE_NAME)
        if session_cookie:
            csrf_cookie = request.cookies.get(settings.CSRF_COOKIE_NAME)
            csrf_header = request.headers.get("X-CSRF-Token") or request.headers.get("x-csrf-token")

            if not csrf_cookie or not csrf_header or not hmac.compare_digest(csrf_cookie, csrf_header):
                log_security_event(
                    event_type="CSRF_VALIDATION_FAILED",
                    ip_address=request.client.host if request.client else "unknown",
                    user_agent=request.headers.get("user-agent"),
                    status="BLOCKED",
                    detail=f"CSRF token mismatch on {request.method} {request.url.path}",
                )
                return JSONResponse(
                    status_code=403,
                    content={"detail": "CSRF validation failed. Missing or invalid X-CSRF-Token header."},
                )

        response = await call_next(request)
        return response
