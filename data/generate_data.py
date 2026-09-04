"""
RazorMind AI - Synthetic FinTech Transaction Data Generator
Generates realistic Indian payment transactions modeled on Razorpay's ecosystem.
Includes UPI, Cards, NetBanking, Bank Downtimes, Fraud Rings, and RFM Customer Behavior.
"""

import os
import random
import uuid
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# Seed for reproducibility
np.random.seed(42)
random.seed(42)

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "raw")
os.makedirs(DATA_DIR, exist_ok=True)

NUM_TRANSACTIONS = 6000
NUM_CUSTOMERS = 600
NUM_MERCHANTS = 40

# FinTech Constants
PAYMENT_METHODS = ["upi", "card_credit", "card_debit", "netbanking", "wallet"]
PAYMENT_METHOD_WEIGHTS = [0.55, 0.20, 0.12, 0.08, 0.05]

BANKS = ["HDFC", "ICICI", "SBI", "AXIS", "KOTAK", "PAYTM_BANK"]
BANK_WEIGHTS = [0.32, 0.26, 0.20, 0.12, 0.06, 0.04]

MERCHANT_CATEGORIES = [
    ("Fashion & Apparel", "mcc_5651", (500, 8000)),
    ("Electronics & Gadgets", "mcc_5732", (2000, 85000)),
    ("SaaS & Subscriptions", "mcc_5818", (999, 15000)),
    ("Food & Quick Commerce", "mcc_5411", (150, 2500)),
    ("Travel & Hospitality", "mcc_4722", (3000, 45000)),
    ("Gaming & Digital Goods", "mcc_7994", (100, 5000)),
]

INDIAN_CITIES = [
    "Bengaluru", "Mumbai", "Delhi NCR", "Hyderabad", "Pune", 
    "Chennai", "Kolkata", "Ahmedabad", "Jaipur", "Kochi"
]

DEVICE_TYPES = ["mobile_android", "mobile_ios", "desktop_chrome", "desktop_safari", "desktop_windows"]

def generate_merchants():
    merchants = []
    for i in range(1, NUM_MERCHANTS + 1):
        cat, mcc, amt_range = random.choice(MERCHANT_CATEGORIES)
        m_id = f"mer_{1000 + i}"
        merchants.append({
            "merchant_id": m_id,
            "merchant_name": f"{cat.split()[0]} Hub {i}",
            "category": cat,
            "mcc": mcc,
            "min_amount": amt_range[0],
            "max_amount": amt_range[1],
            "risk_threshold": round(random.uniform(65.0, 80.0), 1),
            "tier": random.choice(["Enterprise", "Growth", "Starter"]),
            "created_at": (datetime.now() - timedelta(days=random.randint(180, 720))).isoformat()
        })
    df_merchants = pd.DataFrame(merchants)
    df_merchants.to_csv(os.path.join(DATA_DIR, "merchants.csv"), index=False)
    print(f"Generated {len(df_merchants)} merchants.")
    return df_merchants

def generate_customers():
    customers = []
    for i in range(1, NUM_CUSTOMERS + 1):
        c_id = f"cust_{20000 + i}"
        city = random.choice(INDIAN_CITIES)
        avg_amt = round(random.lognormvariate(7.2, 0.8), 2)
        avg_amt = max(300.0, min(avg_amt, 45000.0))
        customers.append({
            "customer_id": c_id,
            "customer_name": f"User_{i}",
            "email": f"user{i}@example.in",
            "phone": f"+9198{random.randint(10000000, 99999999)}",
            "registered_city": city,
            "avg_transaction_amount": avg_amt,
            "risk_profile": random.choices(["low", "medium", "high"], weights=[0.85, 0.12, 0.03])[0],
            "churn_score": round(random.uniform(0.05, 0.95), 3),
            "created_at": (datetime.now() - timedelta(days=random.randint(60, 400))).isoformat()
        })
    df_customers = pd.DataFrame(customers)
    df_customers.to_csv(os.path.join(DATA_DIR, "customers.csv"), index=False)
    print(f"Generated {len(df_customers)} customers.")
    return df_customers

def generate_transactions(merchants_df, customers_df):
    merchants_map = {m["merchant_id"]: m for m in merchants_df.to_dict(orient="records")}
    customers_map = {c["customer_id"]: c for c in customers_df.to_dict(orient="records")}
    
    merchant_ids = list(merchants_map.keys())
    customer_ids = list(customers_map.keys())
    
    now = datetime.now()
    transactions = []

    # Historical customer tracking for velocities
    customer_history = {c_id: [] for c_id in customer_ids}

    # Generate chronologically over last 45 days
    timestamps = [now - timedelta(seconds=random.randint(0, 45 * 86400)) for _ in range(NUM_TRANSACTIONS)]
    timestamps.sort()

    for idx, ts in enumerate(timestamps):
        tx_id = f"pay_{uuid.uuid4().hex[:14]}"
        m_id = random.choice(merchant_ids)
        c_id = random.choice(customer_ids)
        merchant = merchants_map[m_id]
        customer = customers_map[c_id]

        method = random.choices(PAYMENT_METHODS, weights=PAYMENT_METHOD_WEIGHTS)[0]
        bank = random.choices(BANKS, weights=BANK_WEIGHTS)[0]
        
        # Base amount conditioned on merchant category + lognormal distribution
        base_amt = random.uniform(merchant["min_amount"], merchant["max_amount"])
        amount = round(base_amt * random.uniform(0.8, 1.2), 2)
        
        # Customer history & velocity
        c_hist = customer_history[c_id]
        recent_1h = sum(1 for t in c_hist if (ts - t).total_seconds() <= 3600)
        recent_24h = sum(1 for t in c_hist if (ts - t).total_seconds() <= 86400)
        customer_history[c_id].append(ts)

        # Geo & Device details
        billing_city = customer["registered_city"]
        is_traveling = random.random() < 0.12
        shipping_city = random.choice(INDIAN_CITIES) if is_traveling else billing_city
        geo_distance_km = 0 if shipping_city == billing_city else random.randint(150, 1800)
        is_vpn = random.random() < 0.04
        device = random.choice(DEVICE_TYPES)
        hour_of_day = ts.hour

        # Fraud simulation logic (approx ~3.5% fraud rate)
        is_fraud = 0
        fraud_type = "none"
        
        # Synthetic Fraud Ring scenarios:
        # 1. Stolen Card Velocity Burst (Multiple fast attempts, high amount)
        if method.startswith("card") and recent_1h >= 3 and random.random() < 0.70:
            is_fraud = 1
            fraud_type = "velocity_burst"
            amount *= random.uniform(2.5, 5.0)

        # 2. Account Takeover (Late night, foreign IP/VPN, amount >> customer avg)
        elif is_vpn and (hour_of_day >= 1 and hour_of_day <= 5) and amount > customer["avg_transaction_amount"] * 2.5:
            if random.random() < 0.75:
                is_fraud = 1
                fraud_type = "account_takeover"

        # 3. High amount anomaly on new device / long distance
        elif geo_distance_km > 1000 and amount > 45000 and is_vpn:
            if random.random() < 0.80:
                is_fraud = 1
                fraud_type = "geo_anomaly"

        # 4. Pure random testing attacks (~1%)
        elif random.random() < 0.008:
            is_fraud = 1
            fraud_type = "card_testing"
            amount = round(random.uniform(50, 150), 2)

        amount = round(amount, 2)
        amt_ratio = round(amount / max(customer["avg_transaction_amount"], 50.0), 2)

        # Payment Success / Failure Logic
        # Realistic failure reasons: Bank downtime, auth timeout, insufficient funds, etc.
        status = "captured"
        failure_reason = "none"
        
        # Injected Downtime Scenario: SBI and HDFC NetBanking has higher downtime in last 7-14 days
        is_recent_week = (now - ts).days <= 10
        bank_failure_rate = 0.04 # base failure rate
        
        if bank == "SBI" and is_recent_week and method in ["upi", "netbanking"]:
            bank_failure_rate = 0.28  # 28% failure spike simulating real-world bank outage!
        elif bank == "HDFC" and method == "netbanking" and is_recent_week:
            bank_failure_rate = 0.18
        elif method == "upi" and random.random() < 0.05:
            bank_failure_rate = 0.12

        if is_fraud:
            # 65% of fraudulent transactions get blocked by risk engine
            if random.random() < 0.65:
                status = "failed"
                failure_reason = "risk_blocked"
            else:
                status = "captured"  # Fraud slips through and will be disputed!
        elif random.random() < bank_failure_rate:
            status = "failed"
            failure_reason = random.choices(
                ["issuer_bank_down", "auth_timeout", "insufficient_funds", "incorrect_otp"],
                weights=[0.45, 0.25, 0.20, 0.10]
            )[0]
        elif random.random() < 0.02:
            # 2% refunds
            status = "refunded"
            failure_reason = "customer_return"

        # Calculate synthetic risk score
        risk_score = 10.0
        if is_fraud:
            risk_score = random.uniform(75.0, 98.0)
        else:
            if is_vpn: risk_score += 15.0
            if amt_ratio > 3.0: risk_score += 20.0
            if recent_1h >= 2: risk_score += 15.0
            if hour_of_day in [1, 2, 3, 4]: risk_score += 10.0
            if geo_distance_km > 500: risk_score += 10.0
            risk_score += random.uniform(-5.0, 10.0)
        risk_score = round(max(2.0, min(risk_score, 99.0)), 1)

        transactions.append({
            "transaction_id": tx_id,
            "merchant_id": m_id,
            "customer_id": c_id,
            "amount": amount,
            "currency": "INR",
            "payment_method": method,
            "bank_code": bank,
            "status": status,
            "failure_reason": failure_reason,
            "is_fraud": is_fraud,
            "fraud_type": fraud_type,
            "risk_score": risk_score,
            "hour_of_day": hour_of_day,
            "day_of_week": ts.weekday(),
            "velocity_1h": recent_1h,
            "velocity_24h": recent_24h,
            "amount_to_avg_ratio": amt_ratio,
            "geo_distance_km": geo_distance_km,
            "is_vpn_or_proxy": int(is_vpn),
            "device_type": device,
            "billing_city": billing_city,
            "shipping_city": shipping_city,
            "created_at": ts.isoformat()
        })

    df_tx = pd.DataFrame(transactions)
    df_tx.to_csv(os.path.join(DATA_DIR, "transactions.csv"), index=False)
    print(f"Generated {len(df_tx)} transactions.")
    print(f"Fraud count: {df_tx['is_fraud'].sum()} ({df_tx['is_fraud'].mean()*100:.2f}%)")
    print(f"Status distribution:\n{df_tx['status'].value_counts(normalize=True)}")
    return df_tx

if __name__ == "__main__":
    print("Generating FinTech synthetic dataset for RazorMind AI...")
    merchants = generate_merchants()
    customers = generate_customers()
    generate_transactions(merchants, customers)
    print("Dataset generation complete!")
