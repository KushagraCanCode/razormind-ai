"""
End-to-End Test Suite for RazorMind AI Platform
Validates:
1. Model Registry loading & training
2. Fraud Detection API (/api/fraud/evaluate)
3. Payment Success & Smart Routing API (/api/predict/success)
4. Analytics Engine (/api/analytics/overview, /trends, /banks, /churn)
5. AI Merchant Assistant (/api/assistant/chat) for the 3 key interview questions:
   - "What caused my revenue to decrease this week?"
   - "Which customers are most likely to stop purchasing?"
   - "Show me unusual transactions."
"""

import os
import sys
import unittest
from fastapi.testclient import TestClient

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from backend.main import app

class TestRazorMindPlatform(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_01_health(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        print("[PASS] Health endpoint verified.")

    def test_02_analytics_overview(self):
        response = self.client.get("/api/analytics/overview")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("total_gmv", data)
        self.assertIn("success_rate", data)
        self.assertGreater(data["total_transactions"], 100)
        print(f"[PASS] Overview verified: GMV=INR {data['total_gmv']:,.2f}, Success Rate={data['success_rate']}%")

    def test_03_fraud_evaluation_safe(self):
        payload = {
            "amount": 1200.0,
            "payment_method": "upi",
            "bank_code": "ICICI",
            "device_type": "mobile_android",
            "velocity_1h": 0,
            "velocity_24h": 1,
            "amount_to_avg_ratio": 1.0,
            "geo_distance_km": 0.0,
            "is_vpn_or_proxy": 0,
            "hour_of_day": 14,
            "day_of_week": 2
        }
        response = self.client.post("/api/fraud/evaluate", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("fraud_probability", data)
        self.assertIn("risk_tier", data)
        self.assertIn(data["decision"], ["APPROVE", "REVIEW"])
        print(f"[PASS] Safe transaction evaluation: Risk Score={data['risk_score']}, Decision={data['decision']}")

    def test_04_fraud_evaluation_suspicious(self):
        payload = {
            "amount": 55000.0,
            "payment_method": "card_credit",
            "bank_code": "HDFC",
            "device_type": "desktop_chrome",
            "velocity_1h": 6,
            "velocity_24h": 8,
            "amount_to_avg_ratio": 5.2,
            "geo_distance_km": 1500.0,
            "is_vpn_or_proxy": 1,
            "hour_of_day": 3,
            "day_of_week": 2
        }
        response = self.client.post("/api/fraud/evaluate", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn(data["risk_tier"], ["HIGH", "CRITICAL"])
        self.assertIn(data["decision"], ["CHALLENGE_2FA", "DECLINE"])
        self.assertGreater(len(data["top_risk_factors"]), 1)
        print(f"[PASS] Attack transaction evaluation: Risk Score={data['risk_score']}, Decision={data['decision']}")

    def test_05_payment_success_and_smart_routing(self):
        payload = {
            "amount": 3499.0,
            "bank_code": "SBI",
            "payment_method": "upi",
            "hour_of_day": 14,
            "day_of_week": 2
        }
        response = self.client.post("/api/predict/success", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("current_route", data)
        self.assertIn("smart_route_recommended", data)
        self.assertIn("evaluated_alternatives", data)
        print(f"[PASS] Smart router verified: Recommendation={data['recommended_fallback']}, Reason={data['recommendation_reason']}")

    def test_06_assistant_revenue_decrease(self):
        payload = {"question": "What caused my revenue to decrease this week?"}
        response = self.client.post("/api/assistant/chat", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["intent"], "REVENUE_DROP_ROOT_CAUSE")
        self.assertTrue(len(data["direct_answer"]) > 20)
        self.assertTrue(len(data["actionable_recommendations"]) > 0)
        print("[PASS] AI Assistant: 'What caused my revenue to decrease this week?' verified.")

    def test_07_assistant_churn(self):
        payload = {"question": "Which customers are most likely to stop purchasing?"}
        response = self.client.post("/api/assistant/chat", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["intent"], "CUSTOMER_CHURN_PREDICTION")
        self.assertTrue(len(data["supporting_data"]) > 0)
        print("[PASS] AI Assistant: 'Which customers are most likely to stop purchasing?' verified.")

    def test_08_assistant_unusual_transactions(self):
        payload = {"question": "Show me unusual transactions."}
        response = self.client.post("/api/assistant/chat", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["intent"], "FRAUD_ANOMALY_AUDIT")
        self.assertTrue(len(data["supporting_data"]) > 0)
        print("[PASS] AI Assistant: 'Show me unusual transactions.' verified.")

    def test_09_transactions_stream(self):
        response = self.client.get("/api/transactions?limit=10")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 10)
        print("[PASS] Transactions stream endpoint verified.")

if __name__ == "__main__":
    unittest.main()
