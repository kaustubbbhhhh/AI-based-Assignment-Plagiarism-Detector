"""
Security utilities for password hashing, email normalization, password policy,
and cryptographic token generation.
"""

import re
import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from jose import JWTError, jwt
import bcrypt
from core.config import get_settings

settings = get_settings()


# ── Email Normalization ───────────────────────────────────────

def normalize_email(email: str) -> str:
    """
    Normalize email address before lookup or storage.
    Trims leading/trailing whitespace and converts to lowercase.
    """
    if not email:
        return ""
    return email.strip().lower()


# ── Password Policy & Hashing ─────────────────────────────────

def validate_password_strength(password: str) -> Tuple[bool, str]:
    """
    Validate that a password adheres to security policy.
    - Minimum length 8 characters
    - Maximum length 128 characters
    - Must contain at least one letter and one number
    """
    if not password:
        return False, "Password cannot be empty."
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if len(password) > 128:
        return False, "Password cannot exceed 128 characters."
    if not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
        return False, "Password must contain both letters and numbers."
    return True, ""


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt with cost factor 12."""
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against its bcrypt hash in constant time."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except Exception:
        return False


# ── Cryptographic Random Tokens ───────────────────────────────

def generate_secure_token() -> Tuple[str, str]:
    """
    Generate a cryptographically secure random token and its SHA-256 hash.
    Returns (raw_token, token_hash).
    """
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    return raw_token, token_hash


def hash_token_string(token: str) -> str:
    """Compute SHA-256 hash of a token string."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


# ── Legacy JWT Tokens (kept for fallback & testing) ───────────

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    """Decode a JWT token. Returns the payload dict or None if invalid/expired."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None
