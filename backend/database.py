"""
Database connection and session management for RazorMind AI.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from backend.config import settings

# SQLite connection with check_same_thread=False for FastAPI multi-threading
connect_args = {"check_same_thread": False} if "sqlite" in settings.SQLALCHEMY_DATABASE_URI else {}

engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    connect_args=connect_args
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
