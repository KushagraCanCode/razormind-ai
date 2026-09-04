"""
SQLAlchemy ORM Models for RazorMind AI
"""

from sqlalchemy import Column, String, Float, Integer, DateTime, Text, ForeignKey, Numeric
from sqlalchemy.sql import func
from backend.database import Base

class Merchant(Base):
    __tablename__ = "merchants"

    merchant_id = Column(String(32), primary_key=True, index=True)
    merchant_name = Column(String(128), nullable=False)
    category = Column(String(64), nullable=False)
    mcc = Column(String(16), nullable=False)
    min_amount = Column(Float, default=100.0)
    max_amount = Column(Float, default=50000.0)
    risk_threshold = Column(Float, default=75.0)
    tier = Column(String(32), default="Growth")
    created_at = Column(DateTime, default=func.now())

class Customer(Base):
    __tablename__ = "customers"

    customer_id = Column(String(32), primary_key=True, index=True)
    customer_name = Column(String(128), nullable=False)
    email = Column(String(128), nullable=False)
    phone = Column(String(32))
    registered_city = Column(String(64))
    avg_transaction_amount = Column(Float, default=1000.0)
    risk_profile = Column(String(32), default="low")
    churn_score = Column(Float, default=0.25)
    created_at = Column(DateTime, default=func.now())

class Transaction(Base):
    __tablename__ = "transactions"

    transaction_id = Column(String(64), primary_key=True, index=True)
    merchant_id = Column(String(32), ForeignKey("merchants.merchant_id"), index=True)
    customer_id = Column(String(32), ForeignKey("customers.customer_id"), index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(8), default="INR")
    payment_method = Column(String(32), nullable=False)
    bank_code = Column(String(32), nullable=False, index=True)
    status = Column(String(32), nullable=False, index=True)
    failure_reason = Column(String(64))
    is_fraud = Column(Integer, default=0, index=True)
    fraud_type = Column(String(64), default="none")
    risk_score = Column(Float, default=10.0)
    hour_of_day = Column(Integer)
    day_of_week = Column(Integer)
    velocity_1h = Column(Integer, default=0)
    velocity_24h = Column(Integer, default=0)
    amount_to_avg_ratio = Column(Float, default=1.0)
    geo_distance_km = Column(Float, default=0.0)
    is_vpn_or_proxy = Column(Integer, default=0)
    device_type = Column(String(64))
    billing_city = Column(String(64))
    shipping_city = Column(String(64))
    created_at = Column(DateTime, default=func.now(), index=True)

class RiskEvaluation(Base):
    __tablename__ = "risk_evaluations"

    evaluation_id = Column(String(64), primary_key=True, index=True)
    transaction_id = Column(String(64), ForeignKey("transactions.transaction_id"), index=True)
    fraud_probability = Column(Float, nullable=False)
    risk_tier = Column(String(16), nullable=False)
    decision = Column(String(32), nullable=False)
    top_risk_factors = Column(Text)
    evaluated_at = Column(DateTime, default=func.now())

class Dispute(Base):
    __tablename__ = "disputes"

    dispute_id = Column(String(64), primary_key=True, index=True)
    transaction_id = Column(String(64), ForeignKey("transactions.transaction_id"), index=True)
    merchant_id = Column(String(32), ForeignKey("merchants.merchant_id"), index=True)
    amount = Column(Float, nullable=False)
    reason = Column(String(128))
    status = Column(String(32), default="under_review")
    created_at = Column(DateTime, default=func.now())
