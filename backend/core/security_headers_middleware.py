"""
Security Headers Middleware.

Injects HTTP security headers onto every API response:
- X-Content-Type-Options: nosniff
- X-Frame-Options: DENY
- Referrer-Policy: strict-origin-when-cross-origin
- Permissions-Policy: geolocation=(), camera=(), microphone=()
- Strict-Transport-Security (HSTS) when operating in secure production mode
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from core.config import get_settings

settings = get_settings()


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response: Response = await call_next(request)
        
        # Prevent MIME-sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        
        # Referrer policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Restrict dangerous browser features
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"

        # HTTP Strict Transport Security (HSTS)
        if settings.COOKIE_SECURE:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        return response
