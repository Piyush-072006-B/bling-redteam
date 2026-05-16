-- ============================================================
-- BLING Red Team Engine — PostgreSQL Schema
-- ============================================================

-- Simulation registry
CREATE TABLE IF NOT EXISTS simulations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    simulation_id VARCHAR(64) UNIQUE NOT NULL,
    attack_type VARCHAR(64) NOT NULL,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    ended_at TIMESTAMPTZ,
    status VARCHAR(32) DEFAULT 'running',
    config JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Transaction log
CREATE TABLE IF NOT EXISTS transactions_log (
    id BIGSERIAL PRIMARY KEY,
    transaction_id VARCHAR(64) UNIQUE NOT NULL,
    simulation_id VARCHAR(64) NOT NULL,
    sender_account VARCHAR(64) NOT NULL,
    receiver_account VARCHAR(64) NOT NULL,
    amount NUMERIC(18,4) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    device_id VARCHAR(64),
    ip_address VARCHAR(45),
    geo_location VARCHAR(64),
    transaction_type VARCHAR(64),
    attack_type VARCHAR(64),
    mutation_generation INT DEFAULT 0,
    payload JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Fraud alerts
CREATE TABLE IF NOT EXISTS fraud_alerts (
    id BIGSERIAL PRIMARY KEY,
    alert_id VARCHAR(64) UNIQUE NOT NULL,
    transaction_id VARCHAR(64) NOT NULL,
    simulation_id VARCHAR(64) NOT NULL,
    alert_type VARCHAR(64) NOT NULL,
    risk_score NUMERIC(5,4) NOT NULL,
    detection_method VARCHAR(64) NOT NULL,
    detected_accounts JSONB,
    details JSONB,
    timestamp TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Metrics per simulation loop
CREATE TABLE IF NOT EXISTS simulation_metrics (
    id BIGSERIAL PRIMARY KEY,
    simulation_id VARCHAR(64) NOT NULL,
    attack_type VARCHAR(64) NOT NULL,
    mutation_generation INT DEFAULT 0,
    total_transactions INT DEFAULT 0,
    detected INT DEFAULT 0,
    evaded INT DEFAULT 0,
    detection_rate NUMERIC(5,4),
    false_positive_rate NUMERIC(5,4),
    avg_detection_latency_ms NUMERIC(10,2),
    graph_nodes INT,
    graph_edges INT,
    recorded_at TIMESTAMPTZ DEFAULT NOW()
);

-- Attack evolution history
CREATE TABLE IF NOT EXISTS evolution_history (
    id BIGSERIAL PRIMARY KEY,
    simulation_id VARCHAR(64) NOT NULL,
    mutation_generation INT NOT NULL,
    original_pattern VARCHAR(64),
    mutated_pattern VARCHAR(64),
    mutations_applied JSONB,
    evasion_success BOOLEAN,
    detection_rate_before NUMERIC(5,4),
    detection_rate_after NUMERIC(5,4),
    recorded_at TIMESTAMPTZ DEFAULT NOW()
);

-- Account pool
CREATE TABLE IF NOT EXISTS account_pool (
    id BIGSERIAL PRIMARY KEY,
    account_id VARCHAR(64) UNIQUE NOT NULL,
    account_type VARCHAR(32) DEFAULT 'normal',
    risk_profile VARCHAR(32) DEFAULT 'low',
    is_mule BOOLEAN DEFAULT FALSE,
    is_dormant BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_active TIMESTAMPTZ
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_transactions_simulation ON transactions_log(simulation_id);
CREATE INDEX IF NOT EXISTS idx_transactions_timestamp ON transactions_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_alerts_simulation ON fraud_alerts(simulation_id);
CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON fraud_alerts(timestamp);
CREATE INDEX IF NOT EXISTS idx_metrics_simulation ON simulation_metrics(simulation_id);
CREATE INDEX IF NOT EXISTS idx_evolution_simulation ON evolution_history(simulation_id);
