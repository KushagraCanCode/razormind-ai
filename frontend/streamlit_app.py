"""
RazorMind AI — Streamlit Companion Dashboard
Intelligent Payment Risk & Merchant Intelligence Platform
"""

import os
import sys
import pandas as pd
import streamlit as st
import sqlite3
import requests

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from backend.config import settings
from backend.models.analytics_engine import AnalyticsEngine
from backend.services.model_registry import registry

st.set_page_config(
    page_title="RazorMind AI — FinTech Risk Platform",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Styling
st.markdown("""
<style>
    .main { background-color: #070b14; color: #f8fafc; }
    .stMetric { background: rgba(16, 26, 48, 0.7); padding: 16px; border-radius: 12px; border: 1px solid rgba(59, 130, 246, 0.2); }
    h1, h2, h3 { font-family: 'Outfit', sans-serif; color: #f8fafc; }
</style>
""", unsafe_allow_html=True)

# Initialize engines
analytics = AnalyticsEngine(settings.DATABASE_PATH)

st.sidebar.title("⚡ RazorMind AI")
st.sidebar.markdown("**Intelligent Payment Risk & Merchant Intelligence**")
st.sidebar.markdown("---")

menu = st.sidebar.radio(
    "Navigation",
    ["Executive Overview", "Fraud Simulator (Thirdwatch)", "Smart Fallback Router (Optimizer)", "AI Merchant Assistant", "Transaction Audit Log"]
)

# 1. Executive Overview
if menu == "Executive Overview":
    st.title("📊 Executive Merchant Dashboard")
    st.markdown("Real-time telemetry across payment gateways, risk engines, and network conversion.")

    try:
        kpis = analytics.get_overview_metrics()
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total GMV", f"₹{kpis['total_gmv']:,.2f}", f"{kpis['captured_count']} txns")
        col2.metric("Success Rate", f"{kpis['success_rate']}%", "Network Conversion")
        col3.metric("Prevented Fraud", f"₹{kpis['fraud_prevented_gmv']:,.2f}", f"{kpis['fraud_count']} threats", delta_color="inverse")
        col4.metric("Failed Revenue", f"₹{kpis['failed_gmv']:,.2f}", f"{kpis['failed_count']} drops", delta_color="inverse")

        st.markdown("---")
        col_left, col_right = st.columns([7, 5])

        with col_left:
            st.subheader("📈 14-Day Revenue & Success Rate Trends")
            trends = analytics.get_recent_revenue_trends(14)
            df_trends = pd.DataFrame(trends)
            if not df_trends.empty:
                st.line_chart(df_trends.set_index("tx_date")[["captured_revenue", "lost_revenue"]])

        with col_right:
            st.subheader("🏦 Bank Gateway Health")
            banks = analytics.get_bank_health_metrics()
            df_banks = pd.DataFrame(banks)
            if not df_banks.empty:
                st.dataframe(df_banks[["bank_code", "total_tx", "success_rate", "downtime_incidents"]], use_container_width=True)

    except Exception as e:
        st.error(f"Error loading overview: {e}. Please ensure database is initialized.")

# 2. Fraud Simulator
elif menu == "Fraud Simulator (Thirdwatch)":
    st.title("🛡️ Real-Time Fraud Simulator")
    st.markdown("Test live machine learning risk inference against synthetic attack signals.")

    col_form, col_res = st.columns([6, 6])

    with col_form:
        amount = st.number_input("Transaction Amount (INR)", min_value=100.0, max_value=250000.0, value=35000.0, step=500.0)
        method = st.selectbox("Payment Method", ["card_credit", "upi", "card_debit", "netbanking", "wallet"])
        bank = st.selectbox("Bank", ["HDFC", "ICICI", "SBI", "AXIS", "KOTAK"])
        device = st.selectbox("Device Fingerprint", ["desktop_chrome", "mobile_android", "mobile_ios", "desktop_windows"])
        velocity_1h = st.slider("Velocity (Attempts in 1 Hour)", 0, 10, 4)
        ratio = st.slider("Amount vs Customer Average Ratio", 0.5, 10.0, 4.2)
        geo_dist = st.slider("Billing vs Shipping Distance (km)", 0, 2000, 1200)
        is_vpn = st.checkbox("VPN / Residential Proxy IP Detected", value=True)
        hour = st.slider("Hour of Attempt", 0, 23, 3)

        btn_eval = st.button("⚡ Score Transaction Risk", type="primary")

    with col_res:
        if btn_eval:
            engine = registry.get_fraud_engine()
            res = engine.predict_risk({
                "amount": amount,
                "payment_method": method,
                "bank_code": bank,
                "device_type": device,
                "velocity_1h": velocity_1h,
                "velocity_24h": velocity_1h + 2,
                "amount_to_avg_ratio": ratio,
                "geo_distance_km": geo_dist,
                "is_vpn_or_proxy": 1 if is_vpn else 0,
                "hour_of_day": hour,
                "day_of_week": 2
            })

            st.metric("Model Risk Score", f"{res['risk_score']} / 100", f"Tier: {res['risk_tier']}")
            st.info(f"**Recommended Policy Decision:** {res['decision']}")
            st.markdown("### Decision Factors (Explainable AI):")
            for factor in res["top_risk_factors"]:
                st.write(f"- ⚠️ {factor}")

# 3. Smart Router
elif menu == "Smart Fallback Router (Optimizer)":
    st.title("🔀 Smart Dynamic Router")
    st.markdown("Simulate gateway downtime and evaluate dynamic fallback routing.")

    col_in, col_out = st.columns([5, 7])
    with col_in:
        r_bank = st.selectbox("Primary Bank Switch", ["SBI", "HDFC", "ICICI", "AXIS"], index=0)
        r_method = st.selectbox("Payment Mode", ["upi", "netbanking", "card_credit"], index=0)
        r_amt = st.number_input("Order Value (₹)", value=1999.0)
        btn_route = st.button("Run Optimizer Evaluation", type="primary")

    with col_out:
        if btn_route:
            f_engine = registry.get_failure_engine()
            res = f_engine.evaluate_and_smart_route({
                "bank_code": r_bank,
                "payment_method": r_method,
                "amount": r_amt,
                "hour_of_day": 14,
                "day_of_week": 2
            })

            st.subheader("Routing Evaluation")
            st.write(f"**Primary Route:** {res['current_route']['bank_code']} ({res['current_route']['payment_method'].upper()})")
            st.write(f"**Predicted Success Rate:** {res['current_route']['predicted_success_rate']}%")
            
            if res["smart_route_recommended"]:
                st.success(f"**Optimizer Recommendation:** Proactively switch to **{res['recommended_fallback']}**")
                st.write(f"**Expected Success Rate:** {res['expected_success_rate']}%")
            st.write(f"**Reason:** {res['recommendation_reason']}")

            st.dataframe(pd.DataFrame(res["evaluated_alternatives"]))

# 4. AI Assistant
elif menu == "AI Merchant Assistant":
    st.title("🤖 AI Merchant Assistant")
    st.markdown("Ask complex financial and operational questions about your store.")

    question = st.text_input(
        "Ask a question:", 
        placeholder="e.g. 'What caused my revenue to decrease this week?'"
    )

    col_btn1, col_btn2, col_btn3 = st.columns(3)
    if col_btn1.button("📉 Revenue Drop Analysis"):
        question = "What caused my revenue to decrease this week?"
    if col_btn2.button("👥 Churn Candidates"):
        question = "Which customers are most likely to stop purchasing?"
    if col_btn3.button("🚨 Unusual Transactions"):
        question = "Show me unusual transactions."

    if question:
        from backend.services.ai_assistant_service import AIAssistantService
        service = AIAssistantService(analytics)
        ans = service.answer_query(question)

        st.markdown(f"### Answer:\n{ans['direct_answer']}")
        if ans["key_metrics"]:
            st.write("**Key Metrics:**")
            st.json(ans["key_metrics"])
        if ans["actionable_recommendations"]:
            st.write("**Recommendations:**")
            for r in ans["actionable_recommendations"]:
                st.write(f"- ✅ {r}")
        if ans.get("supporting_data"):
            st.write("**Supporting Data:**")
            st.dataframe(pd.DataFrame(ans["supporting_data"]))

# 5. Audit Log
elif menu == "Transaction Audit Log":
    st.title("📋 Real-Time Transaction Stream")
    conn = sqlite3.connect(settings.DATABASE_PATH)
    df_tx = pd.read_sql_query("SELECT * FROM transactions ORDER BY created_at DESC LIMIT 100", conn)
    conn.close()
    st.dataframe(df_tx, use_container_width=True)
