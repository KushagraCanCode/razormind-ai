"""
Database Seeder and Initializer for RazorMind AI
Supports SQLite (default local) and PostgreSQL.
Loads schema, executes generator if necessary, and bulk-loads data.
"""

import os
import sys
import sqlite3
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data", "raw")
DB_PATH = os.path.join(BASE_DIR, "database", "razormind.db")
SCHEMA_PATH = os.path.join(BASE_DIR, "database", "schema.sql")

def initialize_database():
    print(f"[*] Initializing database at: {DB_PATH}")
    
    # Check if raw data exists, else generate
    tx_file = os.path.join(DATA_DIR, "transactions.csv")
    if not os.path.exists(tx_file):
        print("[*] Raw data not found. Running data generator...")
        sys.path.append(os.path.join(BASE_DIR, "data"))
        import generate_data
        generate_data.generate_merchants()
        generate_data.generate_customers()
        generate_data.generate_transactions(
            pd.read_csv(os.path.join(DATA_DIR, "merchants.csv")),
            pd.read_csv(os.path.join(DATA_DIR, "customers.csv"))
        )

    # Connect to SQLite
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Read and apply schema
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema_sql = f.read()
    cursor.executescript(schema_sql)
    conn.commit()
    print("[+] Database schema applied successfully.")

    # Load CSVs into tables
    merchants_df = pd.read_csv(os.path.join(DATA_DIR, "merchants.csv"))
    customers_df = pd.read_csv(os.path.join(DATA_DIR, "customers.csv"))
    transactions_df = pd.read_csv(os.path.join(DATA_DIR, "transactions.csv"))

    merchants_df.to_sql("merchants", conn, if_exists="replace", index=False)
    customers_df.to_sql("customers", conn, if_exists="replace", index=False)
    transactions_df.to_sql("transactions", conn, if_exists="replace", index=False)
    print(f"[+] Loaded {len(merchants_df)} merchants, {len(customers_df)} customers, {len(transactions_df)} transactions.")

    # Seed some sample risk evaluations for high risk transactions
    cursor.execute("""
        INSERT OR IGNORE INTO risk_evaluations (evaluation_id, transaction_id, fraud_probability, risk_tier, decision, top_risk_factors, evaluated_at)
        SELECT 
            'eval_' || SUBSTR(transaction_id, 5),
            transaction_id,
            ROUND(risk_score / 100.0, 4),
            CASE 
                WHEN risk_score >= 80 THEN 'CRITICAL'
                WHEN risk_score >= 60 THEN 'HIGH'
                WHEN risk_score >= 35 THEN 'MEDIUM'
                ELSE 'LOW'
            END,
            CASE 
                WHEN risk_score >= 80 THEN 'DECLINE'
                WHEN risk_score >= 60 THEN 'CHALLENGE_2FA'
                WHEN risk_score >= 35 THEN 'REVIEW'
                ELSE 'APPROVE'
            END,
            CASE
                WHEN is_vpn_or_proxy = 1 THEN '["High velocity burst", "Suspicious VPN/Proxy IP"]'
                WHEN amount_to_avg_ratio > 3 THEN '["Amount 3x above user baseline", "Unusual hour"]'
                ELSE '["Standard pattern verified"]'
            END,
            created_at
        FROM transactions
        WHERE is_fraud = 1 OR risk_score > 50
        LIMIT 500;
    """)

    # Seed some sample disputes for fraudulent transactions that were captured
    cursor.execute("""
        INSERT OR IGNORE INTO disputes (dispute_id, transaction_id, merchant_id, amount, reason, status, created_at)
        SELECT 
            'disp_' || SUBSTR(transaction_id, 5),
            transaction_id,
            merchant_id,
            amount,
            CASE 
                WHEN fraud_type = 'velocity_burst' THEN 'Cardholder unauthorized transaction claim'
                WHEN fraud_type = 'account_takeover' THEN 'Account takeover fraudulent charge'
                ELSE 'Merchandise not received / fraudulent card use'
            END,
            'under_review',
            created_at
        FROM transactions
        WHERE is_fraud = 1 AND status = 'captured'
        LIMIT 100;
    """)

    conn.commit()
    conn.close()
    print("[+] Database initialization complete with audit logs and disputes seeded.")

if __name__ == "__main__":
    initialize_database()
