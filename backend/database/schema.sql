-- AI Match Simulation v3.0 - PostgreSQL Schema
-- Created: 2025-10-08
-- Database: soccer_predictor_v3

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =============================================================================
-- USERS TABLE
-- =============================================================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    display_name VARCHAR(100),
    avatar_url TEXT,
    tier VARCHAR(20) DEFAULT 'BASIC' CHECK (tier IN ('BASIC', 'PRO')),
    stripe_customer_id VARCHAR(255) UNIQUE,

    -- Status fields
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,

    -- Verification tokens
    verification_token VARCHAR(255),
    verification_token_expires TIMESTAMP,
    reset_token VARCHAR(255),
    reset_token_expires TIMESTAMP,

    -- JSON fields for flexible data
    preferences JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_tier ON users(tier);
CREATE INDEX idx_users_stripe ON users(stripe_customer_id) WHERE stripe_customer_id IS NOT NULL;
CREATE INDEX idx_users_active ON users(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_users_created ON users(created_at DESC);

COMMENT ON TABLE users IS 'User accounts with authentication and subscription info';
COMMENT ON COLUMN users.tier IS 'Subscription tier: BASIC (free) or PRO ($19.99/mo)';
COMMENT ON COLUMN users.preferences IS 'User preferences: theme, notifications, etc';
COMMENT ON COLUMN users.metadata IS 'Additional user metadata';

-- =============================================================================
-- SUBSCRIPTIONS TABLE
-- =============================================================================
CREATE TABLE IF NOT EXISTS subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    stripe_subscription_id VARCHAR(255) UNIQUE,

    -- Subscription details
    tier VARCHAR(20) NOT NULL CHECK (tier IN ('BASIC', 'PRO')),
    status VARCHAR(50) NOT NULL CHECK (status IN ('active', 'canceled', 'past_due', 'trialing', 'incomplete', 'incomplete_expired', 'unpaid')),

    -- Period tracking
    current_period_start TIMESTAMP,
    current_period_end TIMESTAMP,
    trial_start TIMESTAMP,
    trial_end TIMESTAMP,

    -- Cancellation
    cancel_at_period_end BOOLEAN DEFAULT FALSE,
    canceled_at TIMESTAMP,
    cancellation_reason TEXT,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Metadata
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_subs_user_id ON subscriptions(user_id);
CREATE INDEX idx_subs_status ON subscriptions(status);
CREATE INDEX idx_subs_stripe ON subscriptions(stripe_subscription_id) WHERE stripe_subscription_id IS NOT NULL;
CREATE INDEX idx_subs_period_end ON subscriptions(current_period_end);
CREATE UNIQUE INDEX idx_subs_user_active ON subscriptions(user_id) WHERE status IN ('active', 'trialing');

COMMENT ON TABLE subscriptions IS 'User subscription records linked to Stripe';
COMMENT ON COLUMN subscriptions.status IS 'Stripe subscription status';

-- =============================================================================
-- USAGE TRACKING TABLE
-- =============================================================================
CREATE TABLE IF NOT EXISTS usage_tracking (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,

    -- Request details
    endpoint VARCHAR(100) NOT NULL,
    method VARCHAR(10) NOT NULL,
    tier VARCHAR(20) NOT NULL,

    -- Performance metrics
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    response_time_ms INTEGER,
    status_code INTEGER,

    -- AI metrics
    tokens_used INTEGER,
    cost_usd DECIMAL(10, 6),

    -- Client info
    ip_address INET,
    user_agent TEXT,

    -- Additional data
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_usage_user_id ON usage_tracking(user_id);
CREATE INDEX idx_usage_timestamp ON usage_tracking(timestamp DESC);
CREATE INDEX idx_usage_endpoint ON usage_tracking(endpoint);
CREATE INDEX idx_usage_date ON usage_tracking(DATE(timestamp));

COMMENT ON TABLE usage_tracking IS 'API usage tracking for analytics and billing';
COMMENT ON COLUMN usage_tracking.tokens_used IS 'Claude API tokens consumed';
COMMENT ON COLUMN usage_tracking.cost_usd IS 'Actual cost in USD';

-- =============================================================================
-- SIMULATION RESULTS TABLE
-- =============================================================================
CREATE TABLE IF NOT EXISTS simulation_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Match identification
    match_id VARCHAR(100) NOT NULL,
    tier VARCHAR(20) NOT NULL CHECK (tier IN ('BASIC', 'PRO')),

    -- Caching
    user_evaluation_hash VARCHAR(64) NOT NULL,

    -- Results
    scenarios JSONB NOT NULL,
    confidence JSONB,
    analysis JSONB,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP DEFAULT (CURRENT_TIMESTAMP + INTERVAL '1 hour'),

    -- Cache metrics
    hit_count INTEGER DEFAULT 1,

    -- Cost tracking
    tokens_used INTEGER,
    cost_usd DECIMAL(10, 6),

    -- Metadata
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_sim_user_id ON simulation_results(user_id);
CREATE INDEX idx_sim_match ON simulation_results(match_id);
CREATE INDEX idx_sim_hash ON simulation_results(user_evaluation_hash);
CREATE INDEX idx_sim_expires ON simulation_results(expires_at);
CREATE INDEX idx_sim_created ON simulation_results(created_at DESC);

COMMENT ON TABLE simulation_results IS 'Cached AI simulation results';
COMMENT ON COLUMN simulation_results.user_evaluation_hash IS 'SHA256 hash of user input for cache key';
COMMENT ON COLUMN simulation_results.expires_at IS 'Cache expiration time (default 1 hour)';

-- =============================================================================
-- RATE LIMITS TABLE
-- =============================================================================
CREATE TABLE IF NOT EXISTS rate_limits (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Rate limit key
    endpoint VARCHAR(100) NOT NULL,
    window_start TIMESTAMP NOT NULL,

    -- Count
    count INTEGER DEFAULT 1,

    -- Timestamp
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Unique constraint for window
    UNIQUE(user_id, endpoint, window_start)
);

CREATE INDEX idx_rate_user_window ON rate_limits(user_id, window_start);
CREATE INDEX idx_rate_endpoint ON rate_limits(endpoint);
CREATE INDEX idx_rate_window_start ON rate_limits(window_start);

COMMENT ON TABLE rate_limits IS 'Rate limiting tracking per user/endpoint/hour';
COMMENT ON COLUMN rate_limits.window_start IS 'Start of the hour window (rounded)';

-- =============================================================================
-- AUDIT LOGS TABLE
-- =============================================================================
CREATE TABLE IF NOT EXISTS audit_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,

    -- Action details
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id VARCHAR(255),

    -- Changes
    changes JSONB,

    -- Client info
    ip_address INET,
    user_agent TEXT,

    -- Timestamp
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Success/failure
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT
);

CREATE INDEX idx_audit_user ON audit_logs(user_id);
CREATE INDEX idx_audit_timestamp ON audit_logs(timestamp DESC);
CREATE INDEX idx_audit_action ON audit_logs(action);
CREATE INDEX idx_audit_resource ON audit_logs(resource_type, resource_id);

COMMENT ON TABLE audit_logs IS 'Security and compliance audit trail';
COMMENT ON COLUMN audit_logs.changes IS 'JSON diff of changes made';

-- =============================================================================
-- MATCHES TABLE
-- =============================================================================
CREATE TABLE IF NOT EXISTS matches (
    id VARCHAR(100) PRIMARY KEY,
    home_team VARCHAR(100) NOT NULL,
    away_team VARCHAR(100) NOT NULL,

    -- Schedule
    gameweek INTEGER,
    kickoff_time TIMESTAMP,

    -- Status
    status VARCHAR(20) CHECK (status IN ('scheduled', 'live', 'finished', 'postponed', 'canceled')),

    -- Result
    home_score INTEGER,
    away_score INTEGER,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- External IDs
    fpl_fixture_id INTEGER,
    external_ids JSONB DEFAULT '{}'
);

CREATE INDEX idx_matches_gameweek ON matches(gameweek);
CREATE INDEX idx_matches_kickoff ON matches(kickoff_time);
CREATE INDEX idx_matches_status ON matches(status);
CREATE INDEX idx_matches_teams ON matches(home_team, away_team);

COMMENT ON TABLE matches IS 'EPL match fixtures and results';

-- =============================================================================
-- TRIGGERS
-- =============================================================================

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_subscriptions_updated_at BEFORE UPDATE ON subscriptions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_matches_updated_at BEFORE UPDATE ON matches
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Sync user tier with active subscription
CREATE OR REPLACE FUNCTION sync_user_tier()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status IN ('active', 'trialing') THEN
        UPDATE users SET tier = NEW.tier WHERE id = NEW.user_id;
    ELSIF OLD.status IN ('active', 'trialing') AND NEW.status NOT IN ('active', 'trialing') THEN
        UPDATE users SET tier = 'BASIC' WHERE id = NEW.user_id;
    END IF;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER sync_user_tier_on_subscription_change
    AFTER INSERT OR UPDATE ON subscriptions
    FOR EACH ROW EXECUTE FUNCTION sync_user_tier();

-- =============================================================================
-- VIEWS
-- =============================================================================

-- Active subscriptions view
CREATE OR REPLACE VIEW active_subscriptions AS
SELECT
    s.*,
    u.email,
    u.display_name
FROM subscriptions s
JOIN users u ON s.user_id = u.id
WHERE s.status IN ('active', 'trialing');

COMMENT ON VIEW active_subscriptions IS 'Currently active subscriptions with user info';

-- Daily usage stats view
CREATE OR REPLACE VIEW daily_usage_stats AS
SELECT
    DATE(timestamp) as date,
    tier,
    endpoint,
    COUNT(*) as request_count,
    AVG(response_time_ms) as avg_response_time,
    SUM(tokens_used) as total_tokens,
    SUM(cost_usd) as total_cost
FROM usage_tracking
GROUP BY DATE(timestamp), tier, endpoint;

COMMENT ON VIEW daily_usage_stats IS 'Daily aggregated usage statistics';

-- =============================================================================
-- INITIAL DATA
-- =============================================================================

-- None for now - will be seeded separately

-- =============================================================================
-- GRANTS (Adjust based on your user setup)
-- =============================================================================

-- Grant permissions to application user (adjust username as needed)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_user;
