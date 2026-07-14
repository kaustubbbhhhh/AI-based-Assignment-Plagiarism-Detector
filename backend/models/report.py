"""
Report SQLAlchemy model.
Stores the results of AI detection and plagiarism analysis.
"""

from sqlalchemy import Column, Integer, Float, String, Text, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from core.database import Base
import enum


class ContentLabel(str, enum.Enum):
    original = "Original"
    ai_generated = "AI-generated"
    mixed = "Mixed"


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    submission_id = Column(Integer, ForeignKey("submissions.id"), unique=True, nullable=False, index=True)

    # ── AI Detection Scores ───────────────────────────────────
    ai_score = Column(Float, nullable=False, default=0.0)             # 0-100%
    label = Column(SAEnum(ContentLabel), nullable=False, default=ContentLabel.original)

    # ── Plagiarism Scores ─────────────────────────────────────
    plagiarism_score = Column(Float, nullable=False, default=0.0)     # 0-100%

    # ── Processed Insights ────────────────────────────────────
    processed_text = Column(Text, nullable=True)           # cleaned extracted text
    word_count = Column(Integer, nullable=True)
    sentence_count = Column(Integer, nullable=True)
    visual_hash = Column(String(64), nullable=True)        # perceptual hash for images

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    submission = relationship("Submission", back_populates="report")

    def __repr__(self):
        return f"<Report(id={self.id}, ai={self.ai_score}%, plag={self.plagiarism_score}%)>"
