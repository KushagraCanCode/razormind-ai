"""
Generates production-grade Jupyter Notebooks for RazorMind AI.
Outputs:
- notebooks/fraud_detection.ipynb
- notebooks/revenue_prediction.ipynb
"""

import json
import os

NOTEBOOKS_DIR = os.path.dirname(os.path.abspath(__file__))

def make_notebook(cells):
    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3 (ipykernel)",
                "language": "python",
                "name": "python3"
            },
            "language_info": {
                "codemirror_mode": {"name": "ipython", "version": 3},
                "file_extension": ".py",
                "mimetype": "text/x-python",
                "name": "python",
                "nbconvert_exporter": "python",
                "pygments_lexer": "ipython3",
                "version": "3.11.9"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 4
    }

def md_cell(source):
    lines = [line + "\n" for line in source.strip().split("\n")]
    if lines:
        lines[-1] = lines[-1].rstrip("\n")
    return {"cell_type": "markdown", "metadata": {}, "source": lines}

def code_cell(source):
    lines = [line + "\n" for line in source.strip().split("\n")]
    if lines:
        lines[-1] = lines[-1].rstrip("\n")
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": lines
    }

def build_fraud_notebook():
    cells = [
        md_cell("""# RazorMind AI: Machine Learning Fraud Detection Engine
### Inspired by Razorpay Thirdwatch & Real-Time Risk Intelligence
**Objective**: Build, evaluate, and interpret an ensemble ML classifier to detect fraudulent payment transactions (stolen cards, velocity bursts, account takeover) while minimizing false positive declines for legitimate merchants."""),
        
        md_cell("## 1. Environment Setup & Data Loading"),
        code_cell("""import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score, roc_curve, precision_recall_curve, average_precision_score
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
import joblib

# Set aesthetic styling
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
np.random.seed(42)

# Load synthetic FinTech dataset
data_path = os.path.join("..", "data", "raw", "transactions.csv")
if not os.path.exists(data_path):
    print("Generating data first...")
    import sys
    sys.path.append(os.path.join("..", "data"))
    import generate_data
    m = generate_data.generate_merchants()
    c = generate_data.generate_customers()
    df = generate_data.generate_transactions(m, c)
else:
    df = pd.read_csv(data_path)

print(f"Dataset Shape: {df.shape}")
df.head()"""),

        md_cell("## 2. Exploratory Data Analysis (EDA) & Imbalance Check"),
        code_cell("""fraud_counts = df['is_fraud'].value_counts()
print(f"Non-Fraud: {fraud_counts[0]} ({fraud_counts[0]/len(df)*100:.2f}%)")
print(f"Fraud: {fraud_counts[1]} ({fraud_counts[1]/len(df)*100:.2f}%)")

fig, axes = plt.subplots(1, 3, figsize=(18, 5))

# Plot 1: Target distribution
sns.countplot(data=df, x='is_fraud', palette=['#10b981', '#ef4444'], ax=axes[0])
axes[0].set_title("Fraud Distribution (Class Imbalance)", fontsize=13, fontweight='bold')
axes[0].set_xticklabels(['Legitimate (0)', 'Fraud (1)'])

# Plot 2: Amount distribution by fraud
sns.boxplot(data=df, x='is_fraud', y='amount', palette=['#10b981', '#ef4444'], ax=axes[1])
axes[1].set_yscale('log')
axes[1].set_title("Transaction Amount (Log Scale)", fontsize=13, fontweight='bold')
axes[1].set_xticklabels(['Legitimate', 'Fraud'])

# Plot 3: Fraud rate across payment methods
method_fraud = df.groupby('payment_method')['is_fraud'].mean().reset_index()
sns.barplot(data=method_fraud, x='payment_method', y='is_fraud', palette='mako', ax=axes[2])
axes[2].set_title("Fraud Rate by Payment Method", fontsize=13, fontweight='bold')
axes[2].set_ylabel("Fraud Probability")
plt.xticks(rotation=20)
plt.tight_layout()
plt.show()"""),

        md_cell("## 3. Feature Engineering & Preparation"),
        code_cell("""NUMERIC_FEATURES = [
    "amount", "hour_of_day", "day_of_week", "velocity_1h", 
    "velocity_24h", "amount_to_avg_ratio", "geo_distance_km", "is_vpn_or_proxy"
]
CATEGORICAL_FEATURES = ["payment_method", "device_type"]

X = df[NUMERIC_FEATURES + CATEGORICAL_FEATURES]
y = df["is_fraud"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print(f"Training set: {X_train.shape}, Test set: {X_test.shape}")
print(f"Fraud cases in test set: {y_test.sum()}")"""),

        md_cell("## 4. Model Training & Comparison\nWe compare a Baseline Logistic Regression against cost-sensitive Random Forest and Gradient Boosting."),
        code_cell("""preprocessor = ColumnTransformer(
    transformers=[
        ("num", "passthrough", NUMERIC_FEATURES),
        ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES)
    ]
)

models = {
    "Logistic Regression (Balanced)": LogisticRegression(class_weight="balanced", max_iter=1000, random_state=42),
    "Random Forest (Balanced)": RandomForestClassifier(n_estimators=120, max_depth=12, min_samples_split=4, class_weight="balanced", random_state=42, n_jobs=-1),
    "Gradient Boosting": GradientBoostingClassifier(n_estimators=120, learning_rate=0.08, max_depth=5, random_state=42)
}

results = {}
for name, clf in models.items():
    pipe = Pipeline([("prep", preprocessor), ("clf", clf)])
    pipe.fit(X_train, y_train)
    y_prob = pipe.predict_proba(X_test)[:, 1]
    y_pred = pipe.predict(X_test)
    auc = roc_auc_score(y_test, y_prob)
    pr_auc = average_precision_score(y_test, y_prob)
    results[name] = {"pipeline": pipe, "auc": auc, "pr_auc": pr_auc, "y_prob": y_prob, "y_pred": y_pred}
    print(f"[{name}] -> ROC-AUC: {auc:.4f} | PR-AUC: {pr_auc:.4f}")"""),

        md_cell("## 5. ROC & Precision-Recall Curves Evaluation"),
        code_cell("""fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# ROC Curves
for name, res in results.items():
    fpr, tpr, _ = roc_curve(y_test, res["y_prob"])
    axes[0].plot(fpr, tpr, label=f"{name} (AUC = {res['auc']:.3f})")
axes[0].plot([0, 1], [0, 1], 'k--', alpha=0.5)
axes[0].set_title("ROC Curves", fontsize=13, fontweight='bold')
axes[0].set_xlabel("False Positive Rate")
axes[0].set_ylabel("True Positive Rate")
axes[0].legend()

# Precision-Recall Curves
for name, res in results.items():
    prec, rec, _ = precision_recall_curve(y_test, res["y_prob"])
    axes[1].plot(rec, prec, label=f"{name} (PR-AUC = {res['pr_auc']:.3f})")
axes[1].set_title("Precision-Recall Curves (Critical for Rare Fraud)", fontsize=13, fontweight='bold')
axes[1].set_xlabel("Recall")
axes[1].set_ylabel("Precision")
axes[1].legend()

plt.tight_layout()
plt.show()"""),

        md_cell("## 6. Confusion Matrix & Decision Threshold Optimization"),
        code_cell("""best_pipe = results["Random Forest (Balanced)"]["pipeline"]
y_probs = results["Random Forest (Balanced)"]["y_prob"]

# Optimize threshold: standard 0.5 vs custom risk cutoff 0.40
chosen_threshold = 0.40
y_custom_pred = (y_probs >= chosen_threshold).astype(int)

cm = confusion_matrix(y_test, y_custom_pred)

plt.figure(figsize=(6, 5))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
            xticklabels=['Predicted Legitimate', 'Predicted Fraud'],
            yticklabels=['Actual Legitimate', 'Actual Fraud'])
plt.title(f"Confusion Matrix (Threshold = {chosen_threshold})", fontsize=13, fontweight='bold')
plt.show()

print(classification_report(y_test, y_custom_pred, target_names=['Legitimate', 'Fraud']))"""),

        md_cell("## 7. Explainability & Feature Importance"),
        code_cell("""rf_model = best_pipe.named_steps["clf"]
ohe = best_pipe.named_steps["prep"].named_transformers_["cat"]
ohe_feature_names = list(ohe.get_feature_names_out(CATEGORICAL_FEATURES))
all_feature_names = NUMERIC_FEATURES + ohe_feature_names

importances = rf_model.feature_importances_
feat_df = pd.DataFrame({"feature": all_feature_names, "importance": importances}).sort_values("importance", ascending=False)

plt.figure(figsize=(10, 6))
sns.barplot(data=feat_df.head(10), x='importance', y='feature', palette='viridis')
plt.title("Top 10 Feature Importances (Razorpay Risk Factors)", fontsize=13, fontweight='bold')
plt.xlabel("Gini Importance")
plt.tight_layout()
plt.show()

feat_df.head(10)"""),

        md_cell("## 8. Exporting Production Pipeline"),
        code_cell("""artifact_dir = os.path.join("..", "backend", "artifacts")
os.makedirs(artifact_dir, exist_ok=True)
export_path = os.path.join(artifact_dir, "fraud_model.joblib")

joblib.dump(best_pipe, export_path)
print(f"Production Fraud Pipeline exported to: {export_path}")""")
    ]
    nb = make_notebook(cells)
    with open(os.path.join(NOTEBOOKS_DIR, "fraud_detection.ipynb"), "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=2)
    print("[+] Generated fraud_detection.ipynb")

def build_revenue_notebook():
    cells = [
        md_cell("""# RazorMind AI: Payment Success Prediction & Revenue Intelligence
### Inspired by Razorpay Optimizer & Merchant Analytics
**Objective**:
1. Predict transaction failure probabilities due to issuer bank downtime and channel latency.
2. Simulate Smart Routing to dynamically redirect transactions and uplift merchant success rates.
3. Perform RFM (Recency, Frequency, Monetary) customer churn segmentation and revenue drop attribution."""),

        md_cell("## 1. Environment Setup & Data Loading"),
        code_cell("""import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import roc_auc_score, classification_report
import joblib

data_path = os.path.join("..", "data", "raw", "transactions.csv")
df = pd.read_csv(data_path)
print(f"Transactions: {len(df)}")
df.head()"""),

        md_cell("## 2. Bank Downtimes & Payment Gateway Failure Analysis"),
        code_cell("""# Analyze failure rate by bank
bank_analysis = df.groupby('bank_code').agg(
    total_tx=('transaction_id', 'count'),
    failed_tx=('status', lambda x: (x == 'failed').sum()),
    lost_revenue=('amount', lambda x: x[df.loc[x.index, 'status'] == 'failed'].sum())
).reset_index()

bank_analysis['failure_rate'] = (bank_analysis['failed_tx'] / bank_analysis['total_tx']) * 100
bank_analysis['success_rate'] = 100 - bank_analysis['failure_rate']
bank_analysis = bank_analysis.sort_values('failure_rate', ascending=False)

fig, axes = plt.subplots(1, 2, figsize=(15, 5))

sns.barplot(data=bank_analysis, x='bank_code', y='failure_rate', palette='Reds_r', ax=axes[0])
axes[0].set_title("Payment Failure Rate by Bank (%)", fontsize=13, fontweight='bold')
axes[0].set_ylabel("Failure Rate (%)")

sns.barplot(data=bank_analysis, x='bank_code', y='lost_revenue', palette='Oranges_r', ax=axes[1])
axes[1].set_title("Lost Revenue due to Payment Failures (INR)", fontsize=13, fontweight='bold')
axes[1].set_ylabel("Lost GMV (INR)")

plt.tight_layout()
plt.show()
bank_analysis"""),

        md_cell("## 3. Training the Payment Success / Failure Model"),
        code_cell("""FEATURES = ["amount", "hour_of_day", "day_of_week", "bank_code", "payment_method"]
NUMERIC_FEATURES = ["amount", "hour_of_day", "day_of_week"]
CATEGORICAL_FEATURES = ["bank_code", "payment_method"]

df_target = df.copy()
df_target["is_failed"] = (df_target["status"] == "failed").astype(int)

X = df_target[FEATURES]
y = df_target["is_failed"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

preprocessor = ColumnTransformer(
    transformers=[
        ("num", "passthrough", NUMERIC_FEATURES),
        ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES)
    ]
)

failure_pipeline = Pipeline([
    ("prep", preprocessor),
    ("clf", GradientBoostingClassifier(n_estimators=100, max_depth=5, learning_rate=0.08, random_state=42))
])

failure_pipeline.fit(X_train, y_train)
y_prob = failure_pipeline.predict_proba(X_test)[:, 1]
auc = roc_auc_score(y_test, y_prob)

print(f"Payment Failure Prediction ROC-AUC: {auc:.4f}")"""),

        md_cell("## 4. Smart Routing Simulation (Razorpay Optimizer)\nSimulating revenue uplift by rerouting high-failure payments to alternative healthy banks/methods."),
        code_cell("""# Simulation scenario: For all high failure transactions (> 30% failure probability),
# evaluate rerouting to ICICI UPI or HDFC Credit Card.
test_df = X_test.copy()
test_df['actual_failed'] = y_test.values
test_df['predicted_fail_prob'] = y_prob

high_risk_routes = test_df[test_df['predicted_fail_prob'] > 0.25].copy()
print(f"Transactions flagged for smart dynamic rerouting: {len(high_risk_routes)}")

# Simulate route switch to alternate high-availability gateway
simulated_alternate = high_risk_routes.copy()
simulated_alternate['bank_code'] = 'ICICI'
simulated_alternate['payment_method'] = 'upi'

rerouted_fail_prob = failure_pipeline.predict_proba(simulated_alternate[FEATURES])[:, 1]
avg_original_success = (1 - high_risk_routes['predicted_fail_prob']).mean() * 100
avg_rerouted_success = (1 - rerouted_fail_prob).mean() * 100

uplift = avg_rerouted_success - avg_original_success

print(f"Original Channel Success Rate: {avg_original_success:.1f}%")
print(f"Rerouted Channel Success Rate: {avg_rerouted_success:.1f}%")
print(f"Net Conversion Uplift through Smart Routing: +{uplift:.1f}%")"""),

        md_cell("## 5. RFM Customer Churn Modeling\nSegmenting merchant customer base to identify accounts at risk of churning."),
        code_cell("""customers_path = os.path.join("..", "data", "raw", "customers.csv")
cust_df = pd.read_csv(customers_path)

# Calculate aggregate transaction metrics per customer
cust_tx = df.groupby('customer_id').agg(
    total_orders=('transaction_id', 'count'),
    total_spent=('amount', lambda x: x[df.loc[x.index, 'status'] == 'captured'].sum()),
    latest_order=('created_at', 'max')
).reset_index()

merged_cust = pd.merge(cust_df, cust_tx, on='customer_id', how='left').fillna(0)

# High churn risk: churn_score > 0.70 and order count > 0
at_risk = merged_cust[merged_cust['churn_score'] > 0.70].sort_values('total_spent', ascending=False)

plt.figure(figsize=(8, 5))
sns.scatterplot(
    data=merged_cust, 
    x='total_spent', 
    y='churn_score', 
    hue=merged_cust['churn_score'] > 0.70,
    palette=['#10b981', '#ef4444'],
    alpha=0.7
)
plt.title("Customer Spend vs Churn Probability (Red = At Risk Cohort)", fontsize=13, fontweight='bold')
plt.xlabel("Total Lifetime Spend (INR)")
plt.ylabel("Churn Risk Score")
plt.show()

print(f"Identified {len(at_risk)} at-risk customers representing ₹{at_risk['total_spent'].sum():,.2f} in historical revenue.")
at_risk.head()"""),

        md_cell("## 6. Exporting Production Pipeline"),
        code_cell("""artifact_dir = os.path.join("..", "backend", "artifacts")
os.makedirs(artifact_dir, exist_ok=True)
export_path = os.path.join(artifact_dir, "failure_model.joblib")

joblib.dump(failure_pipeline, export_path)
print(f"Production Failure Pipeline exported to: {export_path}")""")
    ]
    nb = make_notebook(cells)
    with open(os.path.join(NOTEBOOKS_DIR, "revenue_prediction.ipynb"), "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=2)
    print("[+] Generated revenue_prediction.ipynb")

if __name__ == "__main__":
    build_fraud_notebook()
    build_revenue_notebook()
