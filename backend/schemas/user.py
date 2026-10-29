"""
Pydantic schemas for User API requests and responses.
All sensitive authentication state (passwords, hashes, internal tokens) are strictly excluded from response schemas.
"""

from pydantic import BaseModel, EmailStr, field_validator, model_validator
from typing import Optional, List
from datetime import datetime
import re


# ── Subject-Section mapping for teachers ──────────────────────
class SubjectSection(BaseModel):
    subject: str
    section: str
    branch: Optional[str] = None


# ── Request Schemas ───────────────────────────────────────────

class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str
    confirm_password: Optional[str] = None
    role: str = "student"          # student | teacher | hod
    phone: Optional[str] = None

    # Student fields
    enrollment_no: Optional[str] = None
    father_phone: Optional[str] = None
    mother_phone: Optional[str] = None
    section: Optional[str] = None
    branch: Optional[str] = None
    session: Optional[str] = None

    # Teacher fields
    teacher_id: Optional[str] = None
    subjects_sections: Optional[List[SubjectSection]] = None

    # HOD fields
    hod_id: Optional[str] = None
    department: Optional[str] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        clean = v.strip()
        if len(clean) < 2:
            raise ValueError("Name must be at least 2 characters long.")
        return clean

    @field_validator("password")
    @classmethod
    def validate_password_policy(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        if len(v) > 128:
            raise ValueError("Password cannot exceed 128 characters.")
        if not re.search(r"[A-Za-z]", v) or not re.search(r"\d", v):
            raise ValueError("Password must contain both letters and numbers.")
        return v

    @model_validator(mode="after")
    def check_password_match(self):
        if self.confirm_password is not None and self.password != self.confirm_password:
            raise ValueError("Passwords do not match.")
        return self


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str
    otp_code: Optional[str] = None

    @field_validator("new_password")
    @classmethod
    def validate_new_password_policy(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        if len(v) > 128:
            raise ValueError("Password cannot exceed 128 characters.")
        if not re.search(r"[A-Za-z]", v) or not re.search(r"\d", v):
            raise ValueError("Password must contain both letters and numbers.")
        return v


class ValidateResetTokenResponse(BaseModel):
    is_valid: bool
    requires_otp: bool = False
    message: str = "Reset token is valid."



class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("New password must be at least 8 characters long.")
        if len(v) > 128:
            raise ValueError("New password cannot exceed 128 characters.")
        if not re.search(r"[A-Za-z]", v) or not re.search(r"\d", v):
            raise ValueError("New password must contain both letters and numbers.")
        return v


class VerifyEmailRequest(BaseModel):
    token: str


class ResendVerificationRequest(BaseModel):
    email: EmailStr


# ── Response Schemas ──────────────────────────────────────────

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str
    phone: Optional[str] = None
    is_verified: bool = True
    must_change_password: bool = False
    enrollment_no: Optional[str] = None
    father_phone: Optional[str] = None
    mother_phone: Optional[str] = None
    teacher_id: Optional[str] = None
    hod_id: Optional[str] = None
    section: Optional[str] = None
    branch: Optional[str] = None
    department: Optional[str] = None
    session: Optional[str] = None
    semester: Optional[int] = None
    subjects_sections: Optional[list] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AdminCreateUser(BaseModel):
    """Schema for admin-initiated user creation. No password field — the backend
    assigns the configured DEFAULT_USER_PASSWORD automatically."""
    name: str
    email: EmailStr
    role: str  # student | teacher | hod
    phone: Optional[str] = None

    # Student fields
    enrollment_no: Optional[str] = None
    branch: Optional[str] = None
    section: Optional[str] = None
    session: Optional[str] = None
    semester: Optional[int] = None

    # Teacher fields
    teacher_id: Optional[str] = None
    subjects_sections: Optional[List["SubjectSection"]] = None

    # HOD fields
    hod_id: Optional[str] = None
    department: Optional[str] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        clean = v.strip()
        if len(clean) < 2:
            raise ValueError("Name must be at least 2 characters long.")
        return clean

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        clean = v.strip().lower()
        if clean not in ("student", "teacher", "hod"):
            raise ValueError("Admin can only create student, teacher, or hod accounts.")
        return clean

    class Config:
        extra = "forbid"


class AdminCreateStudent(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    enrollment_no: Optional[str] = None
    branch: Optional[str] = None
    semester: Optional[int] = None
    section: Optional[str] = None
    session: Optional[str] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        clean = v.strip()
        if len(clean) < 2:
            raise ValueError("Name must be at least 2 characters long.")
        return clean

    class Config:
        extra = "forbid"


class AdminCreateTeacher(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    teacher_id: Optional[str] = None
    branch: Optional[str] = None
    subjects_sections: Optional[List["SubjectSection"]] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        clean = v.strip()
        if len(clean) < 2:
            raise ValueError("Name must be at least 2 characters long.")
        return clean

    class Config:
        extra = "forbid"


class AdminCreateHOD(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    hod_id: Optional[str] = None
    department: Optional[str] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        clean = v.strip()
        if len(clean) < 2:
            raise ValueError("Name must be at least 2 characters long.")
        return clean

    class Config:
        extra = "forbid"


class UserStatusUpdate(BaseModel):
    is_verified: bool

    class Config:
        extra = "forbid"


class AuthResponse(BaseModel):
    message: str = "Authentication successful"
    user: UserResponse


class MessageResponse(BaseModel):
    message: str


class ForgotPasswordResponse(BaseModel):
    message: str
    reset_link: Optional[str] = None


# ── Profile & Authorization Management Schemas ───────────────

class UserProfileUpdate(BaseModel):
    """
    Whitelisted fields for user self-profile updates.
    Prevents Mass-Assignment: role, id, email, is_verified, enrollment_no, etc.
    cannot be modified through this schema.
    """
    name: Optional[str] = None
    phone: Optional[str] = None
    father_phone: Optional[str] = None
    mother_phone: Optional[str] = None

    class Config:
        extra = "forbid"  # Explicitly reject unexpected/manipulated fields like 'role' or 'isAdmin'


class AdminUserUpdate(BaseModel):
    """
    Administrative update schema for managing existing user records.
    """
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    section: Optional[str] = None
    branch: Optional[str] = None
    department: Optional[str] = None
    semester: Optional[int] = None
    session: Optional[str] = None
    enrollment_no: Optional[str] = None
    teacher_id: Optional[str] = None
    hod_id: Optional[str] = None
    is_verified: Optional[bool] = None

    class Config:
        extra = "forbid"


class RoleUpdateRequest(BaseModel):
    """
    Schema for administrative role changes.
    """
    role: str

    @field_validator("role")
    @classmethod
    def validate_target_role(cls, v: str) -> str:
        clean = v.strip().lower()
        allowed = {"student", "teacher", "hod", "admin"}
        if clean not in allowed:
            raise ValueError(f"Invalid role '{v}'. Allowed roles: {', '.join(allowed)}")
        return clean


class UserPaginationResponse(BaseModel):
    items: List[UserResponse]
    total: int
    page: int
    limit: int
    total_pages: int


class SystemSettingsSchema(BaseModel):
    app_name: str = "PlagiarismAI"
    environment: str = "production"
    max_upload_size_mb: int = 25
    allowed_file_types: List[str] = [".pdf", ".docx", ".doc", ".txt", ".png", ".jpg", ".jpeg"]
    session_idle_timeout_seconds: int = 1800
    session_max_age_seconds: int = 86400
    registration_open: bool = True
    maintenance_mode: bool = False
