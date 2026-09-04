"""
Transaction Management & Audit Routes
"""

from fastapi import APIRouter, Query, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Optional, List
from backend.database import get_db
from backend.models.db_models import Transaction
from backend.models.schemas import TransactionSchema

router = APIRouter(prefix="/transactions", tags=["Transactions"])

@router.get("", response_model=List[TransactionSchema])
def list_transactions(
    status: Optional[str] = Query(None, description="captured, failed, or refunded"),
    bank_code: Optional[str] = Query(None, description="HDFC, ICICI, SBI, etc."),
    is_fraud: Optional[int] = Query(None, description="0 or 1"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Lists transactions with flexible filtering by status, bank, fraud flag, and pagination.
    """
    query = db.query(Transaction)
    if status:
        query = query.filter(Transaction.status == status)
    if bank_code:
        query = query.filter(Transaction.bank_code == bank_code)
    if is_fraud is not None:
        query = query.filter(Transaction.is_fraud == is_fraud)

    results = query.order_by(Transaction.created_at.desc()).offset(offset).limit(limit).all()
    
    # Format created_at to string for schema compatibility
    output = []
    for r in results:
        data = {
            "transaction_id": r.transaction_id,
            "merchant_id": r.merchant_id,
            "customer_id": r.customer_id,
            "amount": float(r.amount),
            "currency": r.currency,
            "payment_method": r.payment_method,
            "bank_code": r.bank_code,
            "status": r.status,
            "failure_reason": r.failure_reason,
            "risk_score": float(r.risk_score),
            "is_fraud": int(r.is_fraud),
            "created_at": str(r.created_at)
        }
        output.append(data)
    return output

@router.get("/{transaction_id}")
def get_transaction_details(transaction_id: str, db: Session = Depends(get_db)):
    """
    Fetches full transaction payload with risk evaluation logs.
    """
    tx = db.query(Transaction).filter(Transaction.transaction_id == transaction_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    return {
        "transaction_id": tx.transaction_id,
        "merchant_id": tx.merchant_id,
        "customer_id": tx.customer_id,
        "amount": tx.amount,
        "currency": tx.currency,
        "payment_method": tx.payment_method,
        "bank_code": tx.bank_code,
        "status": tx.status,
        "failure_reason": tx.failure_reason,
        "is_fraud": tx.is_fraud,
        "fraud_type": tx.fraud_type,
        "risk_score": tx.risk_score,
        "velocity_1h": tx.velocity_1h,
        "velocity_24h": tx.velocity_24h,
        "amount_to_avg_ratio": tx.amount_to_avg_ratio,
        "geo_distance_km": tx.geo_distance_km,
        "is_vpn_or_proxy": tx.is_vpn_or_proxy,
        "device_type": tx.device_type,
        "billing_city": tx.billing_city,
        "shipping_city": tx.shipping_city,
        "created_at": str(tx.created_at)
    }
