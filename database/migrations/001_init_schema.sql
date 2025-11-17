-- ChainMonitor Database Schema
-- PostgreSQL 14+
-- Purpose: DeFi Market Risk Monitoring System

-- ============================================
-- 1. MARKETS TABLE (核心实体)
-- ============================================
CREATE TABLE IF NOT EXISTS markets (
    market_id VARCHAR(100) PRIMARY KEY,
    label VARCHAR(100) NOT NULL,
    market_type VARCHAR(20) NOT NULL CHECK (market_type IN ('dex_pool', 'whale', 'exchange')),
    chain VARCHAR(20) NOT NULL DEFAULT 'ethereum',
    contract_address VARCHAR(42) NOT NULL,
    token0_address VARCHAR(42),
    token0_symbol VARCHAR(20),
    token1_address VARCHAR(42),
    token1_symbol VARCHAR(20),
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_markets_type ON markets(market_type);
CREATE INDEX idx_markets_active ON markets(is_active) WHERE is_active = TRUE;

COMMENT ON TABLE markets IS '监控的市场/池子/地址列表';
COMMENT ON COLUMN markets.market_id IS '市场唯一标识符（如UNISWAP_USDC_WETH）';
COMMENT ON COLUMN markets.market_type IS '市场类型：dex_pool(DEX池)/whale(巨鲸)/exchange(交易所)';

-- ============================================
-- 2. RISK_LEVELS TABLE (风险等级历史)
-- ============================================
CREATE TABLE IF NOT EXISTS risk_levels (
    id SERIAL PRIMARY KEY,
    market_id VARCHAR(100) NOT NULL REFERENCES markets(market_id) ON DELETE CASCADE,
    risk_level SMALLINT NOT NULL CHECK (risk_level BETWEEN 0 AND 3),
    risk_score DECIMAL(5,2) NOT NULL CHECK (risk_score BETWEEN 0 AND 100),
    block_number BIGINT,
    tx_hash VARCHAR(66),
    source VARCHAR(50) DEFAULT 'backend',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_risk_levels_market ON risk_levels(market_id, created_at DESC);
CREATE INDEX idx_risk_levels_time ON risk_levels(created_at DESC);
CREATE INDEX idx_risk_levels_level ON risk_levels(risk_level);

COMMENT ON TABLE risk_levels IS '风险等级历史记录（时序数据）';
COMMENT ON COLUMN risk_levels.risk_level IS '风险等级：0=正常,1=注意,2=警告,3=高危';
COMMENT ON COLUMN risk_levels.risk_score IS '综合风险评分(0-100)';

-- ============================================
-- 3. RISK_FACTORS TABLE (风险因子明细)
-- ============================================
CREATE TABLE IF NOT EXISTS risk_factors (
    id SERIAL PRIMARY KEY,
    market_id VARCHAR(100) NOT NULL REFERENCES markets(market_id) ON DELETE CASCADE,
    -- DEX因子
    dex_score DECIMAL(5,2) DEFAULT 0,
    dex_volume_ratio DECIMAL(10,6),
    dex_tx_count INTEGER,
    dex_liquidity DECIMAL(20,2),
    -- 巨鲸因子
    whale_score DECIMAL(5,2) DEFAULT 0,
    whale_sell_volume DECIMAL(20,2),
    whale_active_count INTEGER,
    whale_sell_ratio DECIMAL(10,6),
    -- CEX因子
    cex_score DECIMAL(5,2) DEFAULT 0,
    cex_total_inflow DECIMAL(20,2),
    cex_total_outflow DECIMAL(20,2),
    cex_net_inflow DECIMAL(20,2),
    cex_net_inflow_ratio DECIMAL(10,6),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_risk_factors_market ON risk_factors(market_id, created_at DESC);
CREATE INDEX idx_risk_factors_time ON risk_factors(created_at DESC);

COMMENT ON TABLE risk_factors IS '详细的风险因子数据';

-- ============================================
-- 4. DEX_TRANSACTIONS TABLE (DEX交易记录)
-- Partitioned by month for better performance
-- ============================================
CREATE TABLE IF NOT EXISTS dex_transactions (
    id BIGSERIAL,
    market_id VARCHAR(100) NOT NULL REFERENCES markets(market_id) ON DELETE CASCADE,
    tx_hash VARCHAR(66) NOT NULL,
    block_number BIGINT NOT NULL,
    timestamp BIGINT NOT NULL,
    token_in VARCHAR(20),
    token_out VARCHAR(20),
    amount_in DECIMAL(30,0),
    amount_out DECIMAL(30,0),
    trader_address VARCHAR(42),
    gas_used BIGINT,
    gas_price BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) PARTITION BY RANGE (timestamp);

-- 创建分区表（2025年全年）
-- 使用正确的2025年Unix时间戳
CREATE TABLE dex_transactions_2025_01 PARTITION OF dex_transactions
    FOR VALUES FROM (1735689600) TO (1738368000); -- 2025-01-01 to 2025-02-01

CREATE TABLE dex_transactions_2025_02 PARTITION OF dex_transactions
    FOR VALUES FROM (1738368000) TO (1740787200); -- 2025-02-01 to 2025-03-01

CREATE TABLE dex_transactions_2025_03 PARTITION OF dex_transactions
    FOR VALUES FROM (1740787200) TO (1743465600); -- 2025-03-01 to 2025-04-01

CREATE TABLE dex_transactions_2025_04 PARTITION OF dex_transactions
    FOR VALUES FROM (1743465600) TO (1746057600); -- 2025-04-01 to 2025-05-01

CREATE TABLE dex_transactions_2025_05 PARTITION OF dex_transactions
    FOR VALUES FROM (1746057600) TO (1748736000); -- 2025-05-01 to 2025-06-01

CREATE TABLE dex_transactions_2025_06 PARTITION OF dex_transactions
    FOR VALUES FROM (1748736000) TO (1751328000); -- 2025-06-01 to 2025-07-01

CREATE TABLE dex_transactions_2025_07 PARTITION OF dex_transactions
    FOR VALUES FROM (1751328000) TO (1754006400); -- 2025-07-01 to 2025-08-01

CREATE TABLE dex_transactions_2025_08 PARTITION OF dex_transactions
    FOR VALUES FROM (1754006400) TO (1756684800); -- 2025-08-01 to 2025-09-01

CREATE TABLE dex_transactions_2025_09 PARTITION OF dex_transactions
    FOR VALUES FROM (1756684800) TO (1759276800); -- 2025-09-01 to 2025-10-01

CREATE TABLE dex_transactions_2025_10 PARTITION OF dex_transactions
    FOR VALUES FROM (1759276800) TO (1761955200); -- 2025-10-01 to 2025-11-01

CREATE TABLE dex_transactions_2025_11 PARTITION OF dex_transactions
    FOR VALUES FROM (1761955200) TO (1764547200); -- 2025-11-01 to 2025-12-01

CREATE TABLE dex_transactions_2025_12 PARTITION OF dex_transactions
    FOR VALUES FROM (1764547200) TO (1767225600); -- 2025-12-01 to 2026-01-01

CREATE INDEX idx_dex_tx_market_time ON dex_transactions(market_id, timestamp DESC);
CREATE INDEX idx_dex_tx_hash ON dex_transactions(tx_hash);
CREATE INDEX idx_dex_tx_block ON dex_transactions(block_number);

COMMENT ON TABLE dex_transactions IS 'DEX交易记录（按月分区）';

-- ============================================
-- 5. WHALE_TRANSACTIONS TABLE (巨鲸交易)
-- ============================================
CREATE TABLE IF NOT EXISTS whale_transactions (
    id BIGSERIAL PRIMARY KEY,
    market_id VARCHAR(100) NOT NULL REFERENCES markets(market_id) ON DELETE CASCADE,
    whale_address VARCHAR(42) NOT NULL,
    tx_hash VARCHAR(66) NOT NULL,
    block_number BIGINT NOT NULL,
    timestamp BIGINT NOT NULL,
    to_address VARCHAR(42),
    token_symbol VARCHAR(20),
    amount DECIMAL(30,0),
    usd_value DECIMAL(20,2),
    tx_type VARCHAR(20) CHECK (tx_type IN ('buy', 'sell', 'transfer')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_whale_tx_market ON whale_transactions(market_id, timestamp DESC);
CREATE INDEX idx_whale_tx_address ON whale_transactions(whale_address);
CREATE INDEX idx_whale_tx_time ON whale_transactions(timestamp DESC);

COMMENT ON TABLE whale_transactions IS '巨鲸地址交易记录';

-- ============================================
-- 6. CEX_FLOWS TABLE (交易所资金流动)
-- ============================================
CREATE TABLE IF NOT EXISTS cex_flows (
    id BIGSERIAL PRIMARY KEY,
    market_id VARCHAR(100) NOT NULL REFERENCES markets(market_id) ON DELETE CASCADE,
    cex_address VARCHAR(42) NOT NULL,
    cex_name VARCHAR(50),
    tx_hash VARCHAR(66) NOT NULL,
    block_number BIGINT NOT NULL,
    timestamp BIGINT NOT NULL,
    flow_type VARCHAR(10) CHECK (flow_type IN ('inflow', 'outflow')),
    token_symbol VARCHAR(20),
    amount DECIMAL(30,0),
    usd_value DECIMAL(20,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_cex_flows_market ON cex_flows(market_id, timestamp DESC);
CREATE INDEX idx_cex_flows_cex ON cex_flows(cex_address);
CREATE INDEX idx_cex_flows_time ON cex_flows(timestamp DESC);

COMMENT ON TABLE cex_flows IS '中心化交易所资金流入流出记录';

-- ============================================
-- 7. LIQUIDITY_SNAPSHOTS TABLE (流动性快照)
-- ============================================
CREATE TABLE IF NOT EXISTS liquidity_snapshots (
    id BIGSERIAL PRIMARY KEY,
    market_id VARCHAR(100) NOT NULL REFERENCES markets(market_id) ON DELETE CASCADE,
    timestamp BIGINT NOT NULL,
    reserve0 DECIMAL(30,0),
    reserve1 DECIMAL(30,0),
    total_liquidity_usd DECIMAL(20,2),
    token0_price_usd DECIMAL(20,10),
    token1_price_usd DECIMAL(20,10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_liquidity_market_time ON liquidity_snapshots(market_id, timestamp DESC);

COMMENT ON TABLE liquidity_snapshots IS '流动性池储备快照（定期采样）';

-- ============================================
-- 8. ALERTS TABLE (告警记录)
-- ============================================
CREATE TABLE IF NOT EXISTS alerts (
    id BIGSERIAL PRIMARY KEY,
    market_id VARCHAR(100) NOT NULL REFERENCES markets(market_id) ON DELETE CASCADE,
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    previous_level SMALLINT,
    new_level SMALLINT NOT NULL,
    message TEXT,
    tx_hash VARCHAR(66),
    user_address VARCHAR(42),
    is_resolved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_alerts_market ON alerts(market_id, created_at DESC);
CREATE INDEX idx_alerts_severity ON alerts(severity) WHERE is_resolved = FALSE;
CREATE INDEX idx_alerts_user ON alerts(user_address);

COMMENT ON TABLE alerts IS '风险告警事件记录';

-- ============================================
-- 9. USER_CONFIGS TABLE (用户配置)
-- ============================================
CREATE TABLE IF NOT EXISTS user_configs (
    id SERIAL PRIMARY KEY,
    user_address VARCHAR(42) NOT NULL,
    market_id VARCHAR(100) NOT NULL REFERENCES markets(market_id) ON DELETE CASCADE,
    threshold SMALLINT NOT NULL CHECK (threshold BETWEEN 0 AND 3),
    alert_enabled BOOLEAN DEFAULT TRUE,
    email_notification BOOLEAN DEFAULT FALSE,
    email VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_address, market_id)
);

CREATE INDEX idx_user_configs_address ON user_configs(user_address);
CREATE INDEX idx_user_configs_market ON user_configs(market_id);

COMMENT ON TABLE user_configs IS '用户告警配置';

-- ============================================
-- 10. MONITORING_STATS TABLE (监控统计)
-- ============================================
CREATE TABLE IF NOT EXISTS monitoring_stats (
    id SERIAL PRIMARY KEY,
    stat_date DATE NOT NULL UNIQUE,
    total_markets INTEGER DEFAULT 0,
    total_transactions BIGINT DEFAULT 0,
    total_alerts INTEGER DEFAULT 0,
    avg_risk_score DECIMAL(5,2),
    max_risk_level SMALLINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_monitoring_stats_date ON monitoring_stats(stat_date DESC);

COMMENT ON TABLE monitoring_stats IS '每日监控统计数据';

-- ============================================
-- VIEWS (视图)
-- ============================================

-- 最新风险等级视图
CREATE OR REPLACE VIEW v_latest_risk AS
SELECT DISTINCT ON (market_id)
    market_id,
    risk_level,
    risk_score,
    block_number,
    tx_hash,
    created_at
FROM risk_levels
ORDER BY market_id, created_at DESC;

COMMENT ON VIEW v_latest_risk IS '每个市场的最新风险等级';

-- 市场概览视图
CREATE OR REPLACE VIEW v_market_overview AS
SELECT
    m.market_id,
    m.label,
    m.market_type,
    lr.risk_level AS current_risk_level,
    lr.risk_score AS current_risk_score,
    lr.created_at AS last_updated,
    m.is_active
FROM markets m
LEFT JOIN v_latest_risk lr ON m.market_id = lr.market_id
WHERE m.is_active = TRUE;

COMMENT ON VIEW v_market_overview IS '市场概览（包含最新风险信息）';

-- ============================================
-- FUNCTIONS (函数)
-- ============================================

-- 自动更新 updated_at 时间戳
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为需要的表创建触发器
CREATE TRIGGER update_markets_updated_at BEFORE UPDATE ON markets
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_configs_updated_at BEFORE UPDATE ON user_configs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 完成
SELECT 'ChainMonitor database schema created successfully!' AS status;
