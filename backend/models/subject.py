"""
Subject SQLAlchemy model.

Represents academic subjects mapped to Branch + Semester.
Used by Admin for subject management and by Teachers for subject dropdown population.
"""

from sqlalchemy import Column, Integer, String, DateTime, Enum as SAEnum, UniqueConstraint
from sqlalchemy.sql import func
from core.database import Base
import enum


class SubjectStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"


class Subject(Base):
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    subject_code = Column(String(30), nullable=False, index=True)
    subject_name = Column(String(200), nullable=False)
    branch = Column(String(50), nullable=False, index=True)
    semester = Column(Integer, nullable=False, index=True)
    status = Column(SAEnum(SubjectStatus), nullable=False, default=SubjectStatus.active)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Prevent duplicate (subject_code, branch, semester) combinations
    __table_args__ = (
        UniqueConstraint('subject_code', 'branch', 'semester', name='uq_subject_branch_semester'),
    )

    def __repr__(self):
        return f"<Subject(id={self.id}, code={self.subject_code}, name={self.subject_name}, branch={self.branch}, sem={self.semester})>"
