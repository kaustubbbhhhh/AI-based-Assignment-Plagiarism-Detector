"""
Session SQLAlchemy model.
Stores server-side session records for authenticated users.
Tokens are stored as SHA-256 hashes to mitigate database exposure risks.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from core.database import Base


class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_token_hash = Column(String(64), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)  # Absolute expiration
    last_activity_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)  # Idle timeout tracking
    
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    is_revoked = Column(Boolean, default=False, nullable=False, index=True)

    # Relationships
    user = relationship("User", back_populates="sessions")

    __table_args__ = (
        Index("ix_sessions_user_active", "user_id", "is_revoked", "expires_at"),
    )

    def __repr__(self):
        return f"<Session(id={self.id}, user_id={self.user_id}, is_revoked={self.is_revoked})>"
