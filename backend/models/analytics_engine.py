"""
RazorMind AI - Analytics & Merchant Intelligence Engine
Executes statistical aggregation, RFM cohort churn calculations, root cause failure attribution, and anomaly auditing.
"""

import sqlite3
import pandas as pd
import numpy as np

class AnalyticsEngine:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def get_overview_metrics(self, merchant_id: str = None):
        """
        Calculates executive KPIs: Total GMV, Success Rate, Fraud Rate, At-Risk Revenue.
        """
        conn = self.get_connection()
        where_clause = f"WHERE merchant_id = '{merchant_id}'" if merchant_id else ""

        query = f"""
            SELECT 
                COUNT(*) AS total_transactions,
                SUM(CASE WHEN status = 'captured' THEN amount ELSE 0 END) AS total_gmv,
                SUM(CASE WHEN status = 'captured' THEN 1 ELSE 0 END) AS captured_count,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed_count,
                SUM(CASE WHEN status = 'failed' THEN amount ELSE 0 END) AS failed_gmv,
                SUM(CASE WHEN is_fraud = 1 THEN 1 ELSE 0 END) AS fraud_count,
                SUM(CASE WHEN is_fraud = 1 THEN amount ELSE 0 END) AS fraud_gmv,
                SUM(CASE WHEN is_fraud = 1 AND status = 'failed' THEN amount ELSE 0 END) AS fraud_prevented_gmv
            FROM transactions
            {where_clause}
        """
        df = pd.read_sql_query(query, conn)
        conn.close()

        row = df.iloc[0]
        total_tx = int(row["total_transactions"]) or 1
        captured = int(row["captured_count"]) or 0
        failed = int(row["failed_count"]) or 0
        fraud_cnt = int(row["fraud_count"]) or 0
        
        success_rate = round((captured / total_tx) * 100, 2)
        fraud_rate = round((fraud_cnt / total_tx) * 100, 2)

        return {
            "total_transactions": total_tx,
            "total_gmv": round(float(row["total_gmv"] or 0), 2),
            "captured_count": captured,
            "failed_count": failed,
            "failed_gmv": round(float(row["failed_gmv"] or 0), 2),
            "success_rate": success_rate,
            "fraud_count": fraud_cnt,
            "fraud_gmv": round(float(row["fraud_gmv"] or 0), 2),
            "fraud_prevented_gmv": round(float(row["fraud_prevented_gmv"] or 0), 2),
            "fraud_rate": fraud_rate
        }

    def get_bank_health_metrics(self):
        """
        Aggregates transaction volume, success rates, and failure breakdowns per bank.
        """
        conn = self.get_connection()
        query = """
            SELECT 
                bank_code,
                COUNT(*) as total_tx,
                SUM(CASE WHEN status = 'captured' THEN 1 ELSE 0 END) as captured_tx,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_tx,
                ROUND(AVG(CASE WHEN status = 'captured' THEN 1.0 ELSE 0.0 END) * 100, 1) as success_rate,
                SUM(CASE WHEN failure_reason = 'issuer_bank_down' THEN 1 ELSE 0 END) as downtime_incidents
            FROM transactions
            GROUP BY bank_code
            ORDER BY total_tx DESC
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df.to_dict(orient="records")

    def get_payment_method_breakdown(self):
        """
        Returns distribution and success rates per payment channel.
        """
        conn = self.get_connection()
        query = """
            SELECT 
                payment_method,
                COUNT(*) as count,
                ROUND(SUM(amount), 2) as volume_inr,
                ROUND(AVG(CASE WHEN status = 'captured' THEN 1.0 ELSE 0.0 END) * 100, 1) as success_rate,
                SUM(CASE WHEN is_fraud = 1 THEN 1 ELSE 0 END) as fraud_incidents
            FROM transactions
            GROUP BY payment_method
            ORDER BY volume_inr DESC
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df.to_dict(orient="records")

    def get_recent_revenue_trends(self, days: int = 14):
        """
        Returns daily GMV, success rates, and failure counts for trend charts.
        """
        conn = self.get_connection()
        query = """
            SELECT 
                DATE(created_at) as tx_date,
                COUNT(*) as tx_count,
                ROUND(SUM(CASE WHEN status = 'captured' THEN amount ELSE 0 END), 2) as captured_revenue,
                ROUND(SUM(CASE WHEN status = 'failed' THEN amount ELSE 0 END), 2) as lost_revenue,
                ROUND(AVG(CASE WHEN status = 'captured' THEN 1.0 ELSE 0.0 END) * 100, 1) as success_rate,
                SUM(is_fraud) as fraud_count
            FROM transactions
            GROUP BY DATE(created_at)
            ORDER BY tx_date DESC
            LIMIT ?
        """
        df = pd.read_sql_query(query, conn, params=(days,))
        conn.close()
        return df.iloc[::-1].to_dict(orient="records")

    def get_rfm_churn_candidates(self, limit: int = 15):
        """
        Calculates RFM (Recency, Frequency, Monetary) metrics to detect at-risk churn customers.
        """
        conn = self.get_connection()
        query = """
            SELECT 
                c.customer_id,
                c.customer_name,
                c.registered_city,
                c.churn_score,
                COUNT(t.transaction_id) as total_orders,
                ROUND(SUM(CASE WHEN t.status = 'captured' THEN t.amount ELSE 0 END), 2) as lifetime_spent,
                MAX(t.created_at) as last_order_date
            FROM customers c
            LEFT JOIN transactions t ON c.customer_id = t.customer_id
            GROUP BY c.customer_id
            HAVING total_orders > 0
            ORDER BY c.churn_score DESC, lifetime_spent DESC
            LIMIT ?
        """
        df = pd.read_sql_query(query, conn, params=(limit,))
        conn.close()
        return df.to_dict(orient="records")

    def get_unusual_transactions(self, limit: int = 20):
        """
        Fetches high-risk and anomaly transactions with explainable risk flags.
        """
        conn = self.get_connection()
        query = """
            SELECT 
                t.transaction_id,
                t.merchant_id,
                t.customer_id,
                t.amount,
                t.currency,
                t.payment_method,
                t.bank_code,
                t.status,
                t.failure_reason,
                t.risk_score,
                t.fraud_type,
                t.is_vpn_or_proxy,
                t.velocity_1h,
                t.amount_to_avg_ratio,
                t.geo_distance_km,
                t.created_at
            FROM transactions t
            WHERE t.risk_score >= 60 OR t.is_fraud = 1
            ORDER BY t.risk_score DESC, t.amount DESC
            LIMIT ?
        """
        df = pd.read_sql_query(query, conn, params=(limit,))
        conn.close()
        return df.to_dict(orient="records")

    def diagnose_revenue_decrease(self):
        """
        Deep automated root-cause analysis for recent revenue drop.
        Breaks down impact into:
        1. Bank downtime spikes (e.g. SBI/HDFC downtime)
        2. Payment method failure anomalies
        3. High-ticket order dropoffs
        4. Fraud mitigation impact
        """
        conn = self.get_connection()
        
        # Check bank-level failure surges
        bank_surge_query = """
            SELECT 
                bank_code,
                payment_method,
                COUNT(*) as total_attempts,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_attempts,
                ROUND(SUM(CASE WHEN status = 'failed' THEN amount ELSE 0 END), 2) as lost_revenue,
                ROUND(AVG(CASE WHEN status = 'failed' THEN 1.0 ELSE 0.0 END) * 100, 1) as failure_rate
            FROM transactions
            GROUP BY bank_code, payment_method
            HAVING failure_rate > 15.0 AND total_attempts > 10
            ORDER BY lost_revenue DESC
        """
        bank_surges = pd.read_sql_query(bank_surge_query, conn).to_dict(orient="records")

        # Total failed revenue across all causes
        total_failed_query = """
            SELECT 
                SUM(CASE WHEN status = 'failed' THEN amount ELSE 0 END) as total_lost_revenue,
                SUM(CASE WHEN failure_reason = 'issuer_bank_down' THEN amount ELSE 0 END) as bank_downtime_lost_revenue,
                SUM(CASE WHEN failure_reason = 'risk_blocked' THEN amount ELSE 0 END) as fraud_blocked_revenue
            FROM transactions
        """
        loss_summary = pd.read_sql_query(total_failed_query, conn).iloc[0].to_dict()
        conn.close()

        return {
            "root_causes": bank_surges,
            "loss_summary": loss_summary
        }
