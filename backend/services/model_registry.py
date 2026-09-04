"""
Model Registry Service for RazorMind AI
Maintains in-memory singletons of FraudDetectionEngine and PaymentSuccessEngine.
Automatically triggers training on startup if artifacts are absent.
"""

import os
import pandas as pd
from backend.config import settings
from backend.models.fraud_model import FraudDetectionEngine
from backend.models.failure_model import PaymentSuccessEngine

class ModelRegistry:
    def __init__(self):
        self.fraud_engine = None
        self.failure_engine = None

    def initialize(self):
        print("[*] Initializing Model Registry...")
        
        self.fraud_engine = FraudDetectionEngine(model_path=settings.FRAUD_MODEL_PATH)
        self.failure_engine = PaymentSuccessEngine(model_path=settings.FAILURE_MODEL_PATH)

        # Check if saved models exist, otherwise train them
        data_csv = os.path.join(settings.BASE_DIR, "data", "raw", "transactions.csv")

        needs_training = (
            not os.path.exists(settings.FRAUD_MODEL_PATH) or 
            not os.path.exists(settings.FAILURE_MODEL_PATH)
        )

        if needs_training:
            if not os.path.exists(data_csv):
                print("[*] Data CSV missing. Running synthetic generator...")
                import sys
                sys.path.append(os.path.join(settings.BASE_DIR, "data"))
                import generate_data
                merchants = generate_data.generate_merchants()
                customers = generate_data.generate_customers()
                generate_data.generate_transactions(merchants, customers)

            df = pd.read_csv(data_csv)
            print("[*] Training ML models for registry...")
            self.fraud_engine.train(df)
            self.failure_engine.train(df)
        else:
            print("[+] Loaded pre-trained models from artifacts directory.")

    def get_fraud_engine(self) -> FraudDetectionEngine:
        if not self.fraud_engine or not self.fraud_engine.pipeline:
            self.initialize()
        return self.fraud_engine

    def get_failure_engine(self) -> PaymentSuccessEngine:
        if not self.failure_engine or not self.failure_engine.pipeline:
            self.initialize()
        return self.failure_engine

registry = ModelRegistry()
