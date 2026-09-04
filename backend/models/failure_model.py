"""
RazorMind AI - Payment Success & Smart Routing Engine (Razorpay Optimizer Equivalent)
Predicts transaction success/failure probabilities and dynamically recommends optimal fallback routes.
"""

import os
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score

FEATURES = ["amount", "hour_of_day", "day_of_week", "bank_code", "payment_method"]
NUMERIC_FEATURES = ["amount", "hour_of_day", "day_of_week"]
CATEGORICAL_FEATURES = ["bank_code", "payment_method"]

class PaymentSuccessEngine:
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
        model = GradientBoostingClassifier(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.08,
            random_state=42
        )
        self.pipeline = Pipeline(steps=[
            ("preprocessor", preprocessor),
            ("classifier", model)
        ])

    def train(self, df: pd.DataFrame):
        # Target: 1 if failed, 0 if succeeded/captured
        df_target = df.copy()
        df_target["is_failed"] = (df_target["status"] == "failed").astype(int)

        X = df_target[FEATURES]
        y = df_target["is_failed"]

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        self.build_pipeline()
        print("[*] Training Payment Failure Prediction Engine...")
        self.pipeline.fit(X_train, y_train)

        y_prob = self.pipeline.predict_proba(X_test)[:, 1]
        auc = roc_auc_score(y_test, y_prob)
        print(f"[+] Failure Model Trained! ROC-AUC: {auc:.4f}")

        if self.model_path:
            self.save(self.model_path)
        return {"roc_auc": float(auc)}

    def predict_failure_prob(self, bank_code: str, payment_method: str, amount: float, hour: int = 12, day: int = 2) -> float:
        if self.pipeline is None:
            raise ValueError("Failure model is not trained or loaded.")

        df_row = pd.DataFrame([{
            "amount": amount,
            "hour_of_day": hour,
            "day_of_week": day,
            "bank_code": bank_code,
            "payment_method": payment_method
        }])
        prob_failed = float(self.pipeline.predict_proba(df_row[FEATURES])[0, 1])
        return prob_failed

    def evaluate_and_smart_route(self, data: dict):
        """
        Evaluates transaction failure probability and provides smart routing alternatives.
        """
        bank = data.get("bank_code", "HDFC")
        method = data.get("payment_method", "upi")
        amount = float(data.get("amount", 1000.0))
        hour = int(data.get("hour_of_day", 14))
        day = int(data.get("day_of_week", 2))

        fail_prob = self.predict_failure_prob(bank, method, amount, hour, day)
        success_prob = 1.0 - fail_prob

        # Smart fallback candidate routes
        candidate_routes = [
            {"bank_code": "ICICI", "payment_method": "upi"},
            {"bank_code": "HDFC", "payment_method": "card_credit"},
            {"bank_code": "AXIS", "payment_method": "upi"},
            {"bank_code": "KOTAK", "payment_method": "netbanking"},
        ]

        # Filter out current route
        alternatives = [c for c in candidate_routes if not (c["bank_code"] == bank and c["payment_method"] == method)]

        recommended_route = None
        best_candidate_success = success_prob
        
        # Test alternatives
        evaluated_candidates = []
        for cand in alternatives:
            c_fail = self.predict_failure_prob(cand["bank_code"], cand["payment_method"], amount, hour, day)
            c_success = 1.0 - c_fail
            evaluated_candidates.append({
                "route": f"{cand['bank_code']} ({cand['payment_method'].upper()})",
                "predicted_success_rate": round(c_success * 100, 1),
                "failure_rate": round(c_fail * 100, 1)
            })
            if c_success > best_candidate_success:
                best_candidate_success = c_success
                recommended_route = cand

        needs_reroute = fail_prob >= 0.25 # If failure risk >= 25%
        
        recommendation_reason = "Nominal route health; standard gateway assigned."
        if needs_reroute and recommended_route:
            uplift = round((best_candidate_success - success_prob) * 100, 1)
            recommendation_reason = (
                f"Elevated failure rate detected on {bank} ({method.upper()}). "
                f"Proactively switch to {recommended_route['bank_code']} ({recommended_route['payment_method'].upper()}) "
                f"for +{uplift}% expected success uplift."
            )
        elif needs_reroute and not recommended_route:
            recommendation_reason = "Gateway latency elevated across all channels; enable 1-click retry."

        return {
            "current_route": {
                "bank_code": bank,
                "payment_method": method,
                "predicted_success_rate": round(success_prob * 100, 1),
                "predicted_failure_rate": round(fail_prob * 100, 1)
            },
            "smart_route_recommended": needs_reroute and recommended_route is not None,
            "recommended_fallback": (
                f"{recommended_route['bank_code']} ({recommended_route['payment_method'].upper()})"
                if recommended_route else None
            ),
            "expected_success_rate": round(best_candidate_success * 100, 1),
            "recommendation_reason": recommendation_reason,
            "evaluated_alternatives": evaluated_candidates
        }

    def save(self, path):
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        joblib.dump(self.pipeline, path)
        print(f"[+] Failure model saved to {path}")

    def load(self, path):
        if os.path.exists(path):
            self.pipeline = joblib.load(path)
            print(f"[+] Failure model loaded from {path}")
