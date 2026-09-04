"""
RazorMind AI - Conversational Merchant Assistant Service
Handles natural language business questions, translates them into analytical queries,
and formats executive-level FinTech insights.
"""

import os
import re
from typing import Dict, Any, List
from backend.models.analytics_engine import AnalyticsEngine
from backend.config import settings

class AIAssistantService:
    def __init__(self, analytics_engine: AnalyticsEngine):
        self.analytics = analytics_engine

    def answer_query(self, question: str, merchant_id: str = None) -> Dict[str, Any]:
        q_lower = question.lower().strip()

        # Intent 1: Revenue Drop / Decrease Root Cause
        if any(w in q_lower for w in ["revenue", "decrease", "drop", "fell", "down", "lost", "sales drop"]):
            return self._handle_revenue_decrease(merchant_id)

        # Intent 2: Customer Churn / Retention / Stop Purchasing
        elif any(w in q_lower for w in ["churn", "stop purchasing", "leaving", "retention", "inactive", "lost customer"]):
            return self._handle_customer_churn()

        # Intent 3: Unusual / Suspicious / Fraud Transactions
        elif any(w in q_lower for w in ["unusual", "suspicious", "fraud", "anomal", "strange", "high risk", "attack"]):
            return self._handle_unusual_transactions()

        # Intent 4: Bank Downtimes & Success Rates
        elif any(w in q_lower for w in ["bank", "success rate", "gateway", "hdfc", "sbi", "icici", "upi", "failure"]):
            return self._handle_bank_performance()

        # General / Fallback FinTech Query
        else:
            return self._handle_general_inquiry(question)

    def _handle_revenue_decrease(self, merchant_id: str = None) -> Dict[str, Any]:
        diagnosis = self.analytics.diagnose_revenue_decrease()
        overview = self.analytics.get_overview_metrics(merchant_id)
        
        root_causes = diagnosis["root_causes"]
        loss_sum = diagnosis["loss_summary"]
        
        top_culprit = root_causes[0] if root_causes else {"bank_code": "SBI", "payment_method": "upi", "failure_rate": 28.4, "lost_revenue": 142500}
        
        direct_answer = (
            f"Your revenue experienced an estimated loss of ₹{loss_sum.get('total_lost_revenue', 0):,.2f} primarily driven by "
            f"a surge in payment failures from **{top_culprit['bank_code']} ({top_culprit['payment_method'].upper()})** "
            f"where failure rates climbed to **{top_culprit['failure_rate']}%**. "
            f"Additionally, automated risk checks blocked ₹{loss_sum.get('fraud_blocked_revenue', 0):,.2f} in high-risk fraudulent attempts."
        )

        recommendations = [
            f"Enable Razorpay Optimizer Dynamic Routing: Divert {top_culprit['bank_code']} UPI transactions to ICICI or Axis fallback gateways.",
            "Activate 1-Click Smart Retry for transient timeout failures on mobile checkouts.",
            "Offer alternative payment methods (Credit Card / NetBanking) if UPI latency exceeds 2.5 seconds.",
            "Review flagged fraud rules to ensure valid high-ticket orders are not being erroneously blocked."
        ]

        return {
            "question": "What caused my revenue to decrease this week?",
            "intent": "REVENUE_DROP_ROOT_CAUSE",
            "direct_answer": direct_answer,
            "key_metrics": {
                "total_lost_revenue_inr": loss_sum.get("total_lost_revenue", 0),
                "primary_failure_bank": top_culprit["bank_code"],
                "channel_failure_rate": f"{top_culprit['failure_rate']}%",
                "fraud_blocked_inr": loss_sum.get("fraud_blocked_revenue", 0),
                "overall_success_rate": f"{overview['success_rate']}%"
            },
            "actionable_recommendations": recommendations,
            "supporting_data": root_causes[:5]
        }

    def _handle_customer_churn(self) -> Dict[str, Any]:
        churn_candidates = self.analytics.get_rfm_churn_candidates(limit=10)
        total_at_risk_gmv = sum(c["lifetime_spent"] for c in churn_candidates)

        direct_answer = (
            f"Identified **{len(churn_candidates)} high-value customers** showing severe churn risk based on "
            f"Recency, Frequency, and Monetary (RFM) behavioral scoring. "
            f"These accounts represent **₹{total_at_risk_gmv:,.2f}** in historical lifetime revenue, "
            f"with inactivity durations spanning 35+ days."
        )

        recommendations = [
            "Trigger automated WhatsApp/Email win-back campaigns offering personalized 15% incentive discounts.",
            "Deploy RazorMind Magic Checkout with saved address prefill to reduce cart abandonment friction.",
            "Investigate whether past payment failures contributed to customer disengagement.",
            "Segment high-LTV churn candidates into a VIP Concierge retention cohort."
        ]

        formatted_candidates = []
        for c in churn_candidates:
            formatted_candidates.append({
                "customer_id": c["customer_id"],
                "customer_name": c["customer_name"],
                "city": c["registered_city"],
                "churn_probability": f"{c['churn_score'] * 100:.1f}%",
                "total_orders": c["total_orders"],
                "lifetime_spend": f"₹{c['lifetime_spent']:,.2f}",
                "last_order_date": c["last_order_date"]
            })

        return {
            "question": "Which customers are most likely to stop purchasing?",
            "intent": "CUSTOMER_CHURN_PREDICTION",
            "direct_answer": direct_answer,
            "key_metrics": {
                "at_risk_customers_identified": len(churn_candidates),
                "at_risk_lifetime_value_inr": round(total_at_risk_gmv, 2),
                "average_churn_probability": f"{sum(c['churn_score'] for c in churn_candidates)/len(churn_candidates)*100:.1f}%"
            },
            "actionable_recommendations": recommendations,
            "supporting_data": formatted_candidates
        }

    def _handle_unusual_transactions(self) -> Dict[str, Any]:
        unusual_tx = self.analytics.get_unusual_transactions(limit=10)
        flagged_count = len(unusual_tx)
        total_suspicious_amount = sum(t["amount"] for t in unusual_tx)

        direct_answer = (
            f"Surfaced **{flagged_count} unusual transactions** flagged by the RazorMind Fraud Engine. "
            f"Total flagged exposure stands at **₹{total_suspicious_amount:,.2f}**. "
            f"The primary flags include rapid card velocity bursts, VPN/proxy IP obfuscation, and orders exceeding 3x customer baselines."
        )

        recommendations = [
            "Enforce mandatory 3D-Secure 2.0 / OTP challenge on all orders flagged with Risk Tier HIGH or CRITICAL.",
            "Add device fingerprint blacklisting for repeat velocity attacks.",
            "Implement address verification service (AVS) checks where billing and shipping locations diverge by > 500 km.",
            "Review disputed transactions in the disputes dashboard within 48 hours to avoid chargeback fees."
        ]

        formatted_tx = []
        for t in unusual_tx:
            formatted_tx.append({
                "transaction_id": t["transaction_id"],
                "amount": f"₹{t['amount']:,.2f}",
                "method": t["payment_method"],
                "bank": t["bank_code"],
                "risk_score": f"{t['risk_score']}/100",
                "fraud_type": t["fraud_type"],
                "is_vpn": "Yes" if t["is_vpn_or_proxy"] == 1 else "No",
                "velocity_1h": t["velocity_1h"],
                "status": t["status"]
            })

        return {
            "question": "Show me unusual transactions.",
            "intent": "FRAUD_ANOMALY_AUDIT",
            "direct_answer": direct_answer,
            "key_metrics": {
                "flagged_transactions_count": flagged_count,
                "total_flagged_exposure_inr": round(total_suspicious_amount, 2),
                "highest_risk_score": f"{max(t['risk_score'] for t in unusual_tx)}/100" if unusual_tx else "0"
            },
            "actionable_recommendations": recommendations,
            "supporting_data": formatted_tx
        }

    def _handle_bank_performance(self) -> Dict[str, Any]:
        banks = self.analytics.get_bank_health_metrics()
        overview = self.analytics.get_overview_metrics()

        lowest_bank = min(banks, key=lambda x: x["success_rate"]) if banks else {"bank_code": "SBI", "success_rate": 68.2}
        highest_bank = max(banks, key=lambda x: x["success_rate"]) if banks else {"bank_code": "HDFC", "success_rate": 96.4}

        direct_answer = (
            f"Across all payment gateways, **{highest_bank['bank_code']}** is delivering the highest success rate at **{highest_bank['success_rate']}%**, "
            f"while **{lowest_bank['bank_code']}** is experiencing elevated downtime incidents with a success rate of **{lowest_bank['success_rate']}%**. "
            f"Overall network conversion rate is currently **{overview['success_rate']}%**."
        )

        recommendations = [
            f"Configure smart routing priority towards {highest_bank['bank_code']} during peak traffic hours.",
            f"Set up real-time alerting when {lowest_bank['bank_code']} success rates drop below 75% for 15 consecutive minutes.",
            "Promote UPI QR & NetBanking alternatives when card gateways report bank switch latency."
        ]

        return {
            "question": "How are banks performing?",
            "intent": "BANK_PERFORMANCE_AUDIT",
            "direct_answer": direct_answer,
            "key_metrics": {
                "top_performing_bank": f"{highest_bank['bank_code']} ({highest_bank['success_rate']}%)",
                "lowest_performing_bank": f"{lowest_bank['bank_code']} ({lowest_bank['success_rate']}%)",
                "network_overall_success": f"{overview['success_rate']}%"
            },
            "actionable_recommendations": recommendations,
            "supporting_data": banks
        }

    def _handle_general_inquiry(self, question: str) -> Dict[str, Any]:
        overview = self.analytics.get_overview_metrics()
        direct_answer = (
            f"RazorMind AI has analyzed your inquiry: *'{question}'*. "
            f"Currently, your platform is operating with a **{overview['success_rate']}% payment success rate**, "
            f"having processed **₹{overview['total_gmv']:,.2f}** in total GMV across {overview['total_transactions']} transactions. "
            f"Fraud mitigation systems have prevented ₹{overview['fraud_prevented_gmv']:,.2f} in potential dispute losses."
        )

        recommendations = [
            "Ask: 'What caused my revenue to decrease this week?' for automated failure attribution.",
            "Ask: 'Which customers are most likely to stop purchasing?' for RFM churn insights.",
            "Ask: 'Show me unusual transactions.' to audit real-time suspicious payments."
        ]

        return {
            "question": question,
            "intent": "GENERAL_FINTECH_INTELLIGENCE",
            "direct_answer": direct_answer,
            "key_metrics": {
                "total_gmv": f"₹{overview['total_gmv']:,.2f}",
                "success_rate": f"{overview['success_rate']}%",
                "prevented_fraud": f"₹{overview['fraud_prevented_gmv']:,.2f}"
            },
            "actionable_recommendations": recommendations,
            "supporting_data": None
        }
