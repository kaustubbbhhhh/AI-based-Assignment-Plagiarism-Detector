"""
Pydantic schemas for User API requests and responses.
"""

from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


# ── Subject-Section mapping for teachers ──────────────────────
class SubjectSection(BaseModel):
    subject: str
    section: str


# ── Request Schemas ───────────────────────────────────────────

class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str
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


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class ForgotPasswordResponse(BaseModel):
    message: str
    reset_link: Optional[str] = None



# ── Response Schemas ──────────────────────────────────────────

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str
    phone: Optional[str] = None
    enrollment_no: Optional[str] = None
    teacher_id: Optional[str] = None
    hod_id: Optional[str] = None
    section: Optional[str] = None
    branch: Optional[str] = None
    department: Optional[str] = None
    session: Optional[str] = None
    subjects_sections: Optional[list] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
