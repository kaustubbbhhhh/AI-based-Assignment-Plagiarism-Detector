"""
Pydantic schemas for Subject API requests and responses.
"""

from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime


class SubjectCreate(BaseModel):
    subject_code: str
    subject_name: str
    branch: str
    semester: int

    @field_validator("subject_code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        clean = v.strip()
        if len(clean) < 2:
            raise ValueError("Subject code must be at least 2 characters.")
        return clean

    @field_validator("subject_name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        clean = v.strip()
        if len(clean) < 2:
            raise ValueError("Subject name must be at least 2 characters.")
        return clean

    @field_validator("branch")
    @classmethod
    def validate_branch(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("Branch is required.")
        return clean

    @field_validator("semester")
    @classmethod
    def validate_semester(cls, v: int) -> int:
        if v < 1 or v > 12:
            raise ValueError("Semester must be between 1 and 12.")
        return v


class SubjectUpdate(BaseModel):
    subject_code: Optional[str] = None
    subject_name: Optional[str] = None
    branch: Optional[str] = None
    semester: Optional[int] = None
    status: Optional[str] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            clean = v.strip().lower()
            if clean not in ("active", "inactive"):
                raise ValueError("Status must be 'active' or 'inactive'.")
            return clean
        return v

    class Config:
        extra = "forbid"


class SubjectResponse(BaseModel):
    id: int
    subject_code: str
    subject_name: str
    branch: str
    semester: int
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SubjectListResponse(BaseModel):
    items: List[SubjectResponse]
    total: int
