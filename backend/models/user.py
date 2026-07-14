"""
User SQLAlchemy model.
Roles: student, teacher, hod
"""

from sqlalchemy import Column, Integer, String, DateTime, Enum as SAEnum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from core.database import Base
import enum


class UserRole(str, enum.Enum):
    student = "student"
    teacher = "teacher"
    hod = "hod"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(SAEnum(UserRole), nullable=False, default=UserRole.student)
    phone = Column(String(15), nullable=True)

    # ── Student-specific fields ───────────────────────────────
    enrollment_no = Column(String(30), unique=True, nullable=True, index=True)
    father_phone = Column(String(15), nullable=True)
    mother_phone = Column(String(15), nullable=True)
    session = Column(String(20), nullable=True)              # e.g. 2024-2028

    # ── Teacher-specific fields ───────────────────────────────
    teacher_id = Column(String(30), unique=True, nullable=True, index=True)
    subjects_sections = Column(JSON, nullable=True)          # [{"subject": "DBMS", "section": "CSE-A"}, ...]

    # ── HOD-specific fields ───────────────────────────────────
    hod_id = Column(String(30), unique=True, nullable=True, index=True)
    department = Column(String(50), nullable=True)

    # ── Shared fields ─────────────────────────────────────────
    section = Column(String(20), nullable=True)              # e.g. CSE-A, IT-B
    branch = Column(String(50), nullable=True)               # e.g. CSE, IT, ECE
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    submissions = relationship("Submission", back_populates="student", lazy="dynamic")

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"
