"""
AI Merchant Assistant API Routes
"""

from fastapi import APIRouter, HTTPException
from backend.models.schemas import AssistantChatRequest, AssistantChatResponse
from backend.services.ai_assistant_service import AIAssistantService
from backend.models.analytics_engine import AnalyticsEngine
from backend.config import settings

router = APIRouter(prefix="/assistant", tags=["AI Merchant Assistant"])

@router.post("/chat", response_model=AssistantChatResponse)
def ask_assistant(payload: AssistantChatRequest):
    """
    Conversational Merchant Assistant.
    Translates business questions into quantitative insights with actionable recommendations.
    """
    try:
        analytics = AnalyticsEngine(settings.DATABASE_PATH)
        assistant = AIAssistantService(analytics)
        response = assistant.answer_query(payload.question, payload.merchant_id)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Assistant processing failed: {str(e)}")
