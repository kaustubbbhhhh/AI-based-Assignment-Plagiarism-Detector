"""
Auth Token SQLAlchemy models.
Stores cryptographically hashed, single-use, expiring tokens for:
- Password Reset
- Email Verification
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from core.database import Base


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(64), unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    is_used = Column(Boolean, default=False, nullable=False, index=True)
    used_at = Column(DateTime(timezone=True), nullable=True)

    # Security & Risk Assessment Tracking
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(255), nullable=True)
    requires_otp = Column(Boolean, default=False, nullable=False)
    otp_hash = Column(String(64), nullable=True)
    otp_expires_at = Column(DateTime(timezone=True), nullable=True)
    otp_attempts = Column(Integer, default=0, nullable=False)

    # Relationships
    user = relationship("User")

    __table_args__ = (
        Index("ix_reset_token_valid", "token_hash", "is_used", "expires_at"),
        Index("ix_reset_token_user_active", "user_id", "is_used"),
    )

    def __repr__(self):
        return f"<PasswordResetToken(id={self.id}, user_id={self.user_id}, is_used={self.is_used})>"


def cleanup_expired_reset_tokens(db) -> int:
    """
    Remove expired or used password reset tokens older than 7 days.
    Prevents database bloat while preserving recent audit trail records.
    Returns the number of deleted records.
    """
    from datetime import datetime, timezone, timedelta
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    deleted = db.query(PasswordResetToken).filter(
        (PasswordResetToken.expires_at < cutoff) |
        ((PasswordResetToken.is_used == True) & (PasswordResetToken.used_at < cutoff))
    ).delete(synchronize_session=False)
    db.commit()
    return deleted



class EmailVerificationToken(Base):
    __tablename__ = "email_verification_tokens"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(64), unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    is_used = Column(Boolean, default=False, nullable=False, index=True)

    # Relationships
    user = relationship("User")

    __table_args__ = (
        Index("ix_verify_token_valid", "token_hash", "is_used", "expires_at"),
    )

    def __repr__(self):
        return f"<EmailVerificationToken(id={self.id}, user_id={self.user_id}, is_used={self.is_used})>"
