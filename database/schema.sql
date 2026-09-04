-- ==========================================================
-- RazorMind AI: Enterprise FinTech Database Schema
-- Compatible with PostgreSQL and SQLite
-- ==========================================================

-- 1. Merchants Table
CREATE TABLE IF NOT EXISTS merchants (
    merchant_id VARCHAR(32) PRIMARY KEY,
    merchant_name VARCHAR(128) NOT NULL,
    category VARCHAR(64) NOT NULL,
    mcc VARCHAR(16) NOT NULL,
    min_amount NUMERIC(12, 2) DEFAULT 100.0,
    max_amount NUMERIC(12, 2) DEFAULT 50000.0,
    risk_threshold NUMERIC(5, 2) DEFAULT 75.0,
    tier VARCHAR(32) DEFAULT 'Growth',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Customers Table
CREATE TABLE IF NOT EXISTS customers (
    customer_id VARCHAR(32) PRIMARY KEY,
    customer_name VARCHAR(128) NOT NULL,
    email VARCHAR(128) NOT NULL,
    phone VARCHAR(32),
    registered_city VARCHAR(64),
    avg_transaction_amount NUMERIC(12, 2) DEFAULT 1000.0,
    risk_profile VARCHAR(32) DEFAULT 'low',
    churn_score NUMERIC(5, 3) DEFAULT 0.25,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Transactions Table
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id VARCHAR(64) PRIMARY KEY,
    merchant_id VARCHAR(32) NOT NULL,
    customer_id VARCHAR(32) NOT NULL,
    amount NUMERIC(12, 2) NOT NULL,
    currency VARCHAR(8) DEFAULT 'INR',
    payment_method VARCHAR(32) NOT NULL,   -- upi, card_credit, card_debit, netbanking, wallet
    bank_code VARCHAR(32) NOT NULL,        -- HDFC, ICICI, SBI, AXIS, etc.
    status VARCHAR(32) NOT NULL,           -- captured, failed, refunded
    failure_reason VARCHAR(64),            -- issuer_bank_down, auth_timeout, insufficient_funds, risk_blocked, etc.
    is_fraud INTEGER DEFAULT 0,            -- 0 or 1
    fraud_type VARCHAR(64) DEFAULT 'none', -- velocity_burst, account_takeover, geo_anomaly, etc.
    risk_score NUMERIC(5, 2) DEFAULT 10.0, -- 0 to 100
    hour_of_day INTEGER,
    day_of_week INTEGER,
    velocity_1h INTEGER DEFAULT 0,
    velocity_24h INTEGER DEFAULT 0,
    amount_to_avg_ratio NUMERIC(8, 2) DEFAULT 1.0,
    geo_distance_km NUMERIC(8, 2) DEFAULT 0.0,
    is_vpn_or_proxy INTEGER DEFAULT 0,
    device_type VARCHAR(64),
    billing_city VARCHAR(64),
    shipping_city VARCHAR(64),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (merchant_id) REFERENCES merchants(merchant_id),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- Indexes for lightning fast analytics and fraud evaluation queries
CREATE INDEX IF NOT EXISTS idx_tx_merchant ON transactions (merchant_id);
CREATE INDEX IF NOT EXISTS idx_tx_customer ON transactions (customer_id);
CREATE INDEX IF NOT EXISTS idx_tx_status ON transactions (status);
CREATE INDEX IF NOT EXISTS idx_tx_is_fraud ON transactions (is_fraud);
CREATE INDEX IF NOT EXISTS idx_tx_bank ON transactions (bank_code);
CREATE INDEX IF NOT EXISTS idx_tx_created_at ON transactions (created_at);

-- 4. Real-time Risk Evaluations Audit Trail
CREATE TABLE IF NOT EXISTS risk_evaluations (
    evaluation_id VARCHAR(64) PRIMARY KEY,
    transaction_id VARCHAR(64) NOT NULL,
    fraud_probability NUMERIC(5, 4) NOT NULL,
    risk_tier VARCHAR(16) NOT NULL,        -- LOW, MEDIUM, HIGH, CRITICAL
    decision VARCHAR(32) NOT NULL,         -- APPROVE, CHALLENGE_2FA, REVIEW, DECLINE
    top_risk_factors TEXT,                 -- JSON array of key decision flags
    evaluated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (transaction_id) REFERENCES transactions(transaction_id)
);

-- 5. Smart Routing Audit Trail
CREATE TABLE IF NOT EXISTS smart_routing_logs (
    routing_id VARCHAR(64) PRIMARY KEY,
    transaction_id VARCHAR(64) NOT NULL,
    original_bank VARCHAR(32) NOT NULL,
    predicted_failure_prob NUMERIC(5, 4) NOT NULL,
    recommended_route VARCHAR(64) NOT NULL,
    route_switched INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. Merchant Disputes & Chargebacks
CREATE TABLE IF NOT EXISTS disputes (
    dispute_id VARCHAR(64) PRIMARY KEY,
    transaction_id VARCHAR(64) NOT NULL,
    merchant_id VARCHAR(32) NOT NULL,
    amount NUMERIC(12, 2) NOT NULL,
    reason VARCHAR(128),
    status VARCHAR(32) DEFAULT 'under_review', -- under_review, accepted, won, lost
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (transaction_id) REFERENCES transactions(transaction_id),
    FOREIGN KEY (merchant_id) REFERENCES merchants(merchant_id)
);
