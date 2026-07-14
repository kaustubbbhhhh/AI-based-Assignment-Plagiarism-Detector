"""
Analytics API Router.
Endpoints:
- GET /api/analytics/summary — Quick metrics for dashboard cards
- GET /api/analytics/cheating-rings — Connected components of similarity
- GET /api/analytics/stylometric-anomalies — Style-shift anomalies
- GET /api/analytics/risk-factors — Submission hour-based risk analysis
- GET /api/analytics/insights — Subject rankings and ROI metrics
"""

import logging
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.dependencies import get_db, get_current_user
from models.user import User
from services.analytics import data_mining

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/analytics", tags=["Forensic Analytics"])


def check_authorized(current_user: User):
    """Ensure only HOD and Teacher accounts can view advanced analytics."""
    if current_user.role.value not in ("hod", "teacher"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Only HODs and Teachers are authorized to view forensic analytics.",
        )


@router.get("/summary", response_model=Dict[str, Any])
def get_analytics_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Returns quick metrics suitable for analytics dashboard overview cards."""
    check_authorized(current_user)

    try:
        rings = data_mining.get_cheating_rings(db)
        anomalies = data_mining.get_stylometric_anomalies(db)
        insights = data_mining.get_institutional_insights(db)

        return {
            "total_evaluated": insights["total_evaluated"],
            "hours_saved": insights["hours_saved"],
            "active_cheating_rings": len(rings),
            "stylometric_anomalies": len(anomalies)
        }
    except Exception as e:
        logger.error(f"Failed to fetch analytics summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analytics query failed: {str(e)}"
        )


@router.get("/cheating-rings", response_model=List[Dict[str, Any]])
def get_cheating_rings_list(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Connected cheating rings (networks of students with high similarities)."""
    check_authorized(current_user)

    try:
        return data_mining.get_cheating_rings(db)
    except Exception as e:
        logger.error(f"Failed to fetch cheating rings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analytics query failed: {str(e)}"
        )


@router.get("/stylometric-anomalies", response_model=List[Dict[str, Any]])
def get_stylometric_anomalies_list(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List of submissions with significant stylometric style shifts."""
    check_authorized(current_user)

    try:
        return data_mining.get_stylometric_anomalies(db)
    except Exception as e:
        logger.error(f"Failed to fetch stylometric anomalies: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analytics query failed: {str(e)}"
        )


@router.get("/risk-factors", response_model=List[Dict[str, Any]])
def get_risk_factors(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Temporal and hour-binned submission risk factors."""
    check_authorized(current_user)

    try:
        return data_mining.get_temporal_risk_factors(db)
    except Exception as e:
        logger.error(f"Failed to fetch risk factors: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analytics query failed: {str(e)}"
        )


@router.get("/insights", response_model=Dict[str, Any])
def get_insights(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Comprehensive institutional vulnerability rankings and time saved."""
    check_authorized(current_user)

    try:
        return data_mining.get_institutional_insights(db)
    except Exception as e:
        logger.error(f"Failed to fetch insights: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analytics query failed: {str(e)}"
        )
