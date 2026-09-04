"""
Fraud Detection API Routes
"""

import uuid
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models.schemas import FraudEvaluationRequest, FraudEvaluationResponse
from backend.models.db_models import RiskEvaluation
from backend.services.model_registry import registry
from backend.config import settings

router = APIRouter(prefix="/fraud", tags=["Fraud Detection"])

@router.post("/evaluate", response_model=FraudEvaluationResponse)
def evaluate_transaction_risk(payload: FraudEvaluationRequest, db: Session = Depends(get_db)):
    """
    Evaluates transaction fraud probability in real time.
    Returns probability, risk tier, action decision, and explainability factors.
    """
    try:
        engine = registry.get_fraud_engine()
        result = engine.predict_risk(payload.model_dump())

        # Save evaluation to audit log if possible
        try:
            eval_record = RiskEvaluation(
                evaluation_id=f"eval_{uuid.uuid4().hex[:12]}",
                transaction_id=f"sim_{uuid.uuid4().hex[:10]}",
                fraud_probability=result["fraud_probability"],
                risk_tier=result["risk_tier"],
                decision=result["decision"],
                top_risk_factors=str(result["top_risk_factors"])
            )
            db.add(eval_record)
            db.commit()
        except Exception as e:
            db.rollback()
            # Non-blocking audit failure

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fraud evaluation failed: {str(e)}")

@router.get("/anomalies")
def get_fraud_anomalies(limit: int = 15):
    """
    Returns latest anomalous high-risk transactions detected by the system.
    """
    from backend.models.analytics_engine import AnalyticsEngine
    analytics = AnalyticsEngine(settings.DATABASE_PATH)
    return analytics.get_unusual_transactions(limit=limit)
