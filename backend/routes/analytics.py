"""
Analytics & Merchant Intelligence API Routes
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from backend.models.analytics_engine import AnalyticsEngine
from backend.config import settings

router = APIRouter(prefix="/analytics", tags=["Merchant Analytics"])

def get_engine():
    return AnalyticsEngine(settings.DATABASE_PATH)

@router.get("/overview")
def get_overview(merchant_id: Optional[str] = None):
    """
    Returns high-level business KPIs: GMV, Success Rate, Fraud Rate, At-Risk Revenue.
    """
    try:
        engine = get_engine()
        return engine.get_overview_metrics(merchant_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trends")
def get_trends(days: int = Query(14, ge=1, le=60)):
    """
    Returns daily transaction trends, GMV, and success rate timelines.
    """
    try:
        engine = get_engine()
        return engine.get_recent_revenue_trends(days=days)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/banks")
def get_bank_metrics():
    """
    Returns volume and success rate distribution across Indian banks.
    """
    try:
        engine = get_engine()
        return engine.get_bank_health_metrics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/methods")
def get_method_metrics():
    """
    Returns volume and success rate breakdown across payment methods (UPI, Card, etc.).
    """
    try:
        engine = get_engine()
        return engine.get_payment_method_breakdown()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/churn")
def get_churn_candidates(limit: int = Query(15, ge=1, le=50)):
    """
    Returns customers exhibiting highest churn risk using RFM behavioral metrics.
    """
    try:
        engine = get_engine()
        return engine.get_rfm_churn_candidates(limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/revenue-diagnosis")
def get_revenue_diagnosis():
    """
    Automated root cause failure attribution for recent revenue drops.
    """
    try:
        engine = get_engine()
        return engine.diagnose_revenue_decrease()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
