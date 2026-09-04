"""
Payment Success Prediction & Smart Routing API Routes
"""

from fastapi import APIRouter, HTTPException
from backend.models.schemas import PaymentSuccessRequest, PaymentSuccessResponse
from backend.services.model_registry import registry
from backend.config import settings

router = APIRouter(prefix="/predict", tags=["Payment Success & Smart Routing"])

@router.post("/success", response_model=PaymentSuccessResponse)
def predict_success_and_route(payload: PaymentSuccessRequest):
    """
    Predicts transaction failure probability and provides smart routing alternatives.
    """
    try:
        engine = registry.get_failure_engine()
        result = engine.evaluate_and_smart_route(payload.model_dump())
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@router.get("/banks")
def get_bank_health_summary():
    """
    Returns real-time gateway health and success rate metrics per bank.
    """
    from backend.models.analytics_engine import AnalyticsEngine
    analytics = AnalyticsEngine(settings.DATABASE_PATH)
    return analytics.get_bank_health_metrics()
