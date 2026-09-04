"""
RazorMind AI - Fraud Detection Engine (Razorpay Thirdwatch Equivalent)
Ensemble ML model with explainable risk scoring, velocity analysis, and heuristic guards.
"""

import os
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score

NUMERIC_FEATURES = [
    "amount", "hour_of_day", "day_of_week", "velocity_1h", 
    "velocity_24h", "amount_to_avg_ratio", "geo_distance_km", "is_vpn_or_proxy"
]
CATEGORICAL_FEATURES = ["payment_method", "device_type"]

class FraudDetectionEngine:
    def __init__(self, model_path=None):
        self.model_path = model_path
        self.pipeline = None
        if model_path and os.path.exists(model_path):
            self.load(model_path)

    def build_pipeline(self):
        preprocessor = ColumnTransformer(
            transformers=[
                ("num", "passthrough", NUMERIC_FEATURES),
                ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES)
            ]
        )
        model = RandomForestClassifier(
            n_estimators=120,
            max_depth=12,
            min_samples_split=4,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1
        )
        self.pipeline = Pipeline(steps=[
            ("preprocessor", preprocessor),
            ("classifier", model)
        ])

    def train(self, df: pd.DataFrame):
        X = df[NUMERIC_FEATURES + CATEGORICAL_FEATURES]
        y = df["is_fraud"]

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        self.build_pipeline()
        print("[*] Training Fraud Detection Ensemble...")
        self.pipeline.fit(X_train, y_train)

        y_pred = self.pipeline.predict(X_test)
        y_prob = self.pipeline.predict_proba(X_test)[:, 1]
        
        auc = roc_auc_score(y_test, y_prob)
        print(f"[+] Fraud Model Trained! ROC-AUC: {auc:.4f}")
        print(f"Classification Report:\n{classification_report(y_test, y_pred)}")

        if self.model_path:
            self.save(self.model_path)
        return {"roc_auc": float(auc)}

    def predict_risk(self, data: dict):
        """
        Evaluates a single transaction payload.
        Returns fraud_probability, risk_tier, recommended_action, and explainability factors.
        """
        # Ensure fallback pipeline if not loaded
        if self.pipeline is None:
            raise ValueError("Fraud model pipeline is not trained or loaded.")

        df_row = pd.DataFrame([data])
        
        # Ensure all columns exist
        for col in NUMERIC_FEATURES:
            if col not in df_row.columns:
                df_row[col] = 0
        for col in CATEGORICAL_FEATURES:
            if col not in df_row.columns:
                df_row[col] = "unknown"

        prob = float(self.pipeline.predict_proba(df_row[NUMERIC_FEATURES + CATEGORICAL_FEATURES])[0, 1])

        # Explainability & risk factor extraction
        risk_factors = []
        if data.get("is_vpn_or_proxy", 0) == 1:
            risk_factors.append("Suspicious VPN / Proxy IP connection detected")
        if data.get("velocity_1h", 0) >= 3:
            risk_factors.append(f"High velocity alert: {data['velocity_1h']} attempts within 1 hour")
        if data.get("amount_to_avg_ratio", 1.0) >= 2.5:
            risk_factors.append(f"Ticket size {data['amount_to_avg_ratio']:.1f}x higher than customer average")
        if data.get("geo_distance_km", 0) > 800:
            risk_factors.append(f"Shipping destination {data['geo_distance_km']} km away from billing address")
        if data.get("hour_of_day", 12) in [1, 2, 3, 4]:
            risk_factors.append("Transaction attempted during high-risk nocturnal hours (1 AM - 5 AM)")

        # Risk tier & decision policy (Razorpay Risk Policy)
        if prob >= 0.75 or (len(risk_factors) >= 3 and prob >= 0.45):
            tier = "CRITICAL"
            decision = "DECLINE"
        elif prob >= 0.45 or len(risk_factors) >= 2:
            tier = "HIGH"
            decision = "CHALLENGE_2FA"
        elif prob >= 0.20 or len(risk_factors) >= 1:
            tier = "MEDIUM"
            decision = "REVIEW"
        else:
            tier = "LOW"
            decision = "APPROVE"

        if not risk_factors:
            risk_factors.append("Nominal behavioral parameters verified")

        return {
            "fraud_probability": round(prob, 4),
            "risk_score": round(prob * 100, 1),
            "risk_tier": tier,
            "decision": decision,
            "top_risk_factors": risk_factors
        }

    def save(self, path):
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        joblib.dump(self.pipeline, path)
        print(f"[+] Fraud model saved to {path}")

    def load(self, path):
        if os.path.exists(path):
            self.pipeline = joblib.load(path)
            print(f"[+] Fraud model loaded from {path}")
