"""
Security Audit Trail & Logging Service.

Records security-relevant events without logging any sensitive credentials,
tokens, passwords, or session IDs.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger("security.audit")
logger.setLevel(logging.INFO)


def log_security_event(
    event_type: str,
    user_id: Optional[int] = None,
    email: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    status: str = "SUCCESS",
    detail: Optional[str] = None,
) -> None:
    """
    Log a security-critical action into the audit trail.
    
    CRITICAL: Never pass plain passwords, session tokens, reset tokens, or secret keys!
    """
    now = datetime.now(timezone.utc).isoformat()
    record = {
        "timestamp": now,
        "event": event_type,
        "status": status,
        "user_id": user_id,
        "email": email,
        "ip_address": ip_address or "unknown",
        "user_agent": (user_agent[:120] + "...") if user_agent and len(user_agent) > 120 else (user_agent or "unknown"),
    }
    if detail:
        record["detail"] = detail

    log_msg = (
        f"[AUDIT] {now} | {event_type:<22} | Status: {status:<7} | "
        f"User: {user_id or 'anon'} ({email or 'N/A'}) | IP: {record['ip_address']} | Detail: {detail or ''}"
    )

    if status in ("FAILURE", "BLOCKED", "UNAUTHORIZED"):
        logger.warning(log_msg)
    else:
        logger.info(log_msg)
