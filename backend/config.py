"""
RazorMind AI Configuration Settings
"""

import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "RazorMind AI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATABASE_PATH: str = os.path.join(BASE_DIR, "database", "razormind.db")
    SQLALCHEMY_DATABASE_URI: str = f"sqlite:///{DATABASE_PATH}"
    
    ARTIFACTS_DIR: str = os.path.join(BASE_DIR, "backend", "artifacts")
    FRAUD_MODEL_PATH: str = os.path.join(ARTIFACTS_DIR, "fraud_model.joblib")
    FAILURE_MODEL_PATH: str = os.path.join(ARTIFACTS_DIR, "failure_model.joblib")
    
    # Optional Gemini / OpenAI API key for extended LLM queries
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    
    CORS_ORIGINS: list = ["*"]

    class Config:
        case_sensitive = True

settings = Settings()
os.makedirs(settings.ARTIFACTS_DIR, exist_ok=True)
