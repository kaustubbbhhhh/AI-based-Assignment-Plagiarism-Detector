"""
Submission SQLAlchemy model.
Tracks uploaded assignments and their processing status.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from core.database import Base
import enum


class SubmissionStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    subject = Column(String(150), nullable=False)
    assignment_title = Column(String(200), nullable=True, default="Assignment 1")
    filename = Column(String(255), nullable=False)
    filepath = Column(String(500), nullable=False)
    status = Column(
        SAEnum(SubmissionStatus),
        nullable=False,
        default=SubmissionStatus.pending,
    )
    is_locked = Column(Boolean, nullable=False, default=False)
    locked_at = Column(DateTime(timezone=True), nullable=True)
    verification_token = Column(String(100), nullable=True)
    celery_task_id = Column(String(255), nullable=True)    # track the background job
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    student = relationship("User", back_populates="submissions")
    report = relationship("Report", back_populates="submission", uselist=False)

    def __repr__(self):
        return f"<Submission(id={self.id}, title={self.assignment_title}, status={self.status}, locked={self.is_locked})>"
