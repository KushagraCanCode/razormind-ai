"""
Pydantic Schemas for API Requests and Responses
"""

from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field

# --- Fraud Evaluation Schemas ---
class FraudEvaluationRequest(BaseModel):
    amount: float = Field(..., example=12500.0, description="Transaction amount in INR")
    payment_method: str = Field(..., example="upi", description="upi, card_credit, card_debit, netbanking, wallet")
    bank_code: str = Field(..., example="HDFC", description="HDFC, ICICI, SBI, AXIS, etc.")
    device_type: str = Field("mobile_android", example="mobile_android")
    velocity_1h: int = Field(0, example=1, description="Number of attempts by user in last hour")
    velocity_24h: int = Field(1, example=3, description="Number of attempts by user in last 24 hours")
    amount_to_avg_ratio: float = Field(1.0, example=1.8, description="Ratio of current amount to customer 30-day average")
    geo_distance_km: float = Field(0.0, example=12.5, description="Distance between shipping and registered billing address")
    is_vpn_or_proxy: int = Field(0, example=0, description="1 if VPN or proxy IP detected, else 0")
    hour_of_day: Optional[int] = Field(14, example=14, description="Hour of transaction (0-23)")
    day_of_week: Optional[int] = Field(2, example=2, description="Day of week (0=Mon, 6=Sun)")

class FraudEvaluationResponse(BaseModel):
    fraud_probability: float
    risk_score: float
    risk_tier: str
    decision: str
    top_risk_factors: List[str]

# --- Payment Success & Smart Routing Schemas ---
class PaymentSuccessRequest(BaseModel):
    amount: float = Field(..., example=3499.0)
    bank_code: str = Field(..., example="SBI")
    payment_method: str = Field(..., example="upi")
    hour_of_day: Optional[int] = Field(14, example=14)
    day_of_week: Optional[int] = Field(2, example=2)

class SmartRouteAlternative(BaseModel):
    route: str
    predicted_success_rate: float
    failure_rate: float

class CurrentRouteStats(BaseModel):
    bank_code: str
    payment_method: str
    predicted_success_rate: float
    predicted_failure_rate: float

class PaymentSuccessResponse(BaseModel):
    current_route: CurrentRouteStats
    smart_route_recommended: bool
    recommended_fallback: Optional[str]
    expected_success_rate: float
    recommendation_reason: str
    evaluated_alternatives: List[SmartRouteAlternative]

# --- AI Assistant Schemas ---
class AssistantChatRequest(BaseModel):
    question: str = Field(..., example="What caused my revenue to decrease this week?")
    merchant_id: Optional[str] = None

class AssistantChatResponse(BaseModel):
    question: str
    intent: str
    direct_answer: str
    key_metrics: Dict[str, Any]
    actionable_recommendations: List[str]
    supporting_data: Optional[List[Dict[str, Any]]] = None

# --- Transaction Schemas ---
class TransactionSchema(BaseModel):
    transaction_id: str
    merchant_id: str
    customer_id: str
    amount: float
    currency: str
    payment_method: str
    bank_code: str
    status: str
    failure_reason: Optional[str]
    risk_score: float
    is_fraud: int
    created_at: str

    class Config:
        from_attributes = True
