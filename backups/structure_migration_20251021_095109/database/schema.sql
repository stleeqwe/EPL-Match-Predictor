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
-- TEAM DATA TABLES (Domain Knowledge Storage)
-- =============================================================================

-- Teams table (central entity for team data)
CREATE TABLE IF NOT EXISTS teams (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_teams_name_lookup ON teams(name);

COMMENT ON TABLE teams IS 'EPL teams master table';

-- Formations table
CREATE TABLE IF NOT EXISTS formations (
    id SERIAL PRIMARY KEY,
    team_id INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    formation VARCHAR(10) NOT NULL,  -- "4-3-3", "3-5-2", etc.
    formation_data JSONB,  -- {defensive_line: "high", width: "narrow", ...}
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,

    -- Ensure only one active formation per team
    CONSTRAINT unique_active_formation UNIQUE (team_id, is_active)
        WHERE is_active = TRUE
);

CREATE INDEX idx_formations_team_active ON formations(team_id) WHERE is_active = TRUE;
CREATE INDEX idx_formations_created ON formations(created_at DESC);

COMMENT ON TABLE formations IS 'Team formation data with versioning';

-- Lineups table
CREATE TABLE IF NOT EXISTS lineups (
    id SERIAL PRIMARY KEY,
    team_id INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    formation VARCHAR(10) NOT NULL,
    lineup JSONB NOT NULL,  -- {GK: "Player Name", LB: "Player", ...}
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,

    CONSTRAINT unique_active_lineup UNIQUE (team_id, is_active)
        WHERE is_active = TRUE
);

CREATE INDEX idx_lineups_team_active ON lineups(team_id) WHERE is_active = TRUE;
CREATE INDEX idx_lineups_created ON lineups(created_at DESC);

COMMENT ON TABLE lineups IS 'Team lineup data with versioning';

-- Team Strengths table (18 attributes + derived + PCA)
CREATE TABLE IF NOT EXISTS team_strengths (
    id SERIAL PRIMARY KEY,
    team_id INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,

    -- ========================================================================
    -- 18 Core Attributes (0.0 to 5.0 scale)
    -- ========================================================================

    -- Tactical Foundation (전술 기반)
    tactical_understanding NUMERIC(3,2) CHECK (tactical_understanding BETWEEN 0 AND 5),
    positioning_balance NUMERIC(3,2) CHECK (positioning_balance BETWEEN 0 AND 5),
    role_clarity NUMERIC(3,2) CHECK (role_clarity BETWEEN 0 AND 5),

    -- Attack (공격)
    buildup_quality NUMERIC(3,2) CHECK (buildup_quality BETWEEN 0 AND 5),
    pass_network NUMERIC(3,2) CHECK (pass_network BETWEEN 0 AND 5),
    final_third_penetration NUMERIC(3,2) CHECK (final_third_penetration BETWEEN 0 AND 5),
    goal_conversion NUMERIC(3,2) CHECK (goal_conversion BETWEEN 0 AND 5),

    -- Defense (수비)
    backline_organization NUMERIC(3,2) CHECK (backline_organization BETWEEN 0 AND 5),
    central_control NUMERIC(3,2) CHECK (central_control BETWEEN 0 AND 5),
    flank_defense NUMERIC(3,2) CHECK (flank_defense BETWEEN 0 AND 5),
    counter_prevention NUMERIC(3,2) CHECK (counter_prevention BETWEEN 0 AND 5),

    -- Transitions (전환)
    pressing_organization NUMERIC(3,2) CHECK (pressing_organization BETWEEN 0 AND 5),
    attack_to_defense_transition NUMERIC(3,2) CHECK (attack_to_defense_transition BETWEEN 0 AND 5),
    defense_to_attack_transition NUMERIC(3,2) CHECK (defense_to_attack_transition BETWEEN 0 AND 5),

    -- Special Situations (특수 상황)
    set_piece_threat NUMERIC(3,2) CHECK (set_piece_threat BETWEEN 0 AND 5),
    defensive_resilience NUMERIC(3,2) CHECK (defensive_resilience BETWEEN 0 AND 5),

    -- Intangibles (무형 요소)
    game_reading NUMERIC(3,2) CHECK (game_reading BETWEEN 0 AND 5),
    team_chemistry NUMERIC(3,2) CHECK (team_chemistry BETWEEN 0 AND 5),

    -- ========================================================================
    -- Derived Attributes (computed automatically via trigger, 0-100 scale)
    -- ========================================================================
    attack_strength_manual NUMERIC(5,2),
    defense_strength_manual NUMERIC(5,2),
    press_intensity_manual NUMERIC(5,2),

    -- ========================================================================
    -- PCA Components (Principal Component Analysis)
    -- ========================================================================
    pc1 NUMERIC(5,2),
    pc2 NUMERIC(5,2),
    pc3 NUMERIC(5,2),
    pc4 NUMERIC(5,2),

    -- ========================================================================
    -- Metadata
    -- ========================================================================
    comment TEXT,  -- Analyst notes (e.g., "Post-transfer window update")
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,

    -- Ensure only one active strength per team
    CONSTRAINT unique_active_strength UNIQUE (team_id, is_active)
        WHERE is_active = TRUE
);

CREATE INDEX idx_strengths_team_active ON team_strengths(team_id) WHERE is_active = TRUE;
CREATE INDEX idx_strengths_created ON team_strengths(created_at DESC);
CREATE INDEX idx_strengths_attack ON team_strengths(attack_strength_manual DESC);
CREATE INDEX idx_strengths_defense ON team_strengths(defense_strength_manual DESC);

COMMENT ON TABLE team_strengths IS 'Team strength ratings with 18 attributes';
COMMENT ON COLUMN team_strengths.attack_strength_manual IS 'Auto-calculated from 4 attack attributes (0-100)';
COMMENT ON COLUMN team_strengths.defense_strength_manual IS 'Auto-calculated from 4 defense attributes (0-100)';
COMMENT ON COLUMN team_strengths.press_intensity_manual IS 'Auto-calculated from 2 pressing attributes (0-100)';

-- Tactics table
CREATE TABLE IF NOT EXISTS tactics (
    id SERIAL PRIMARY KEY,
    team_id INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,

    defensive_line VARCHAR(20),  -- "high", "medium", "low"
    pressing_trigger VARCHAR(50),  -- "loss_of_possession", "final_third", etc.
    width VARCHAR(20),  -- "narrow", "balanced", "wide"
    buildup_tempo VARCHAR(20),  -- "slow", "medium", "fast"

    version INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,

    CONSTRAINT unique_active_tactics UNIQUE (team_id, is_active)
        WHERE is_active = TRUE
);

CREATE INDEX idx_tactics_team_active ON tactics(team_id) WHERE is_active = TRUE;

COMMENT ON TABLE tactics IS 'Team tactical settings with versioning';

-- =============================================================================
-- TEAM DATA TRIGGERS
-- =============================================================================

-- Auto-calculate derived attributes (attack/defense/press)
CREATE OR REPLACE FUNCTION update_team_derived_attributes()
RETURNS TRIGGER AS $$
BEGIN
    -- Attack Strength (0-100): Average of 4 attack attributes * 20
    NEW.attack_strength_manual := (
        COALESCE(NEW.buildup_quality, 0) +
        COALESCE(NEW.pass_network, 0) +
        COALESCE(NEW.final_third_penetration, 0) +
        COALESCE(NEW.goal_conversion, 0)
    ) / 4.0 * 20.0;

    -- Defense Strength (0-100): Average of 4 defense attributes * 20
    NEW.defense_strength_manual := (
        COALESCE(NEW.backline_organization, 0) +
        COALESCE(NEW.central_control, 0) +
        COALESCE(NEW.flank_defense, 0) +
        COALESCE(NEW.counter_prevention, 0)
    ) / 4.0 * 20.0;

    -- Press Intensity (0-100): Average of 2 pressing attributes * 20
    NEW.press_intensity_manual := (
        COALESCE(NEW.pressing_organization, 0) +
        COALESCE(NEW.attack_to_defense_transition, 0)
    ) / 2.0 * 20.0;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER compute_team_derived_attributes
BEFORE INSERT OR UPDATE ON team_strengths
FOR EACH ROW
EXECUTE FUNCTION update_team_derived_attributes();

-- Auto-versioning (deactivate old versions)
CREATE OR REPLACE FUNCTION create_team_version()
RETURNS TRIGGER AS $$
BEGIN
    -- Deactivate all previous versions for this team
    IF TG_TABLE_NAME = 'team_strengths' THEN
        UPDATE team_strengths
        SET is_active = FALSE
        WHERE team_id = NEW.team_id AND id != NEW.id;

        NEW.version := COALESCE(
            (SELECT MAX(version) FROM team_strengths WHERE team_id = NEW.team_id),
            0
        ) + 1;
    ELSIF TG_TABLE_NAME = 'formations' THEN
        UPDATE formations
        SET is_active = FALSE
        WHERE team_id = NEW.team_id AND id != NEW.id;

        NEW.version := COALESCE(
            (SELECT MAX(version) FROM formations WHERE team_id = NEW.team_id),
            0
        ) + 1;
    ELSIF TG_TABLE_NAME = 'lineups' THEN
        UPDATE lineups
        SET is_active = FALSE
        WHERE team_id = NEW.team_id AND id != NEW.id;

        NEW.version := COALESCE(
            (SELECT MAX(version) FROM lineups WHERE team_id = NEW.team_id),
            0
        ) + 1;
    ELSIF TG_TABLE_NAME = 'tactics' THEN
        UPDATE tactics
        SET is_active = FALSE
        WHERE team_id = NEW.team_id AND id != NEW.id;

        NEW.version := COALESCE(
            (SELECT MAX(version) FROM tactics WHERE team_id = NEW.team_id),
            0
        ) + 1;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER version_team_strengths
BEFORE INSERT ON team_strengths
FOR EACH ROW
EXECUTE FUNCTION create_team_version();

CREATE TRIGGER version_formations
BEFORE INSERT ON formations
FOR EACH ROW
EXECUTE FUNCTION create_team_version();

CREATE TRIGGER version_lineups
BEFORE INSERT ON lineups
FOR EACH ROW
EXECUTE FUNCTION create_team_version();

CREATE TRIGGER version_tactics
BEFORE INSERT ON tactics
FOR EACH ROW
EXECUTE FUNCTION create_team_version();

-- Update team timestamp when data changes
CREATE OR REPLACE FUNCTION update_team_data_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE teams SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.team_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_teams_on_strength_change
AFTER INSERT OR UPDATE ON team_strengths
FOR EACH ROW
EXECUTE FUNCTION update_team_data_timestamp();

CREATE TRIGGER update_teams_on_formation_change
AFTER INSERT OR UPDATE ON formations
FOR EACH ROW
EXECUTE FUNCTION update_team_data_timestamp();

CREATE TRIGGER update_teams_on_lineup_change
AFTER INSERT OR UPDATE ON lineups
FOR EACH ROW
EXECUTE FUNCTION update_team_data_timestamp();

CREATE TRIGGER update_teams_on_tactics_change
AFTER INSERT OR UPDATE ON tactics
FOR EACH ROW
EXECUTE FUNCTION update_team_data_timestamp();

-- =============================================================================
-- TEAM DATA VIEWS
-- =============================================================================

-- Latest team data (active versions only)
CREATE OR REPLACE VIEW v_teams_latest AS
SELECT
    t.id,
    t.name,
    ts.attack_strength_manual,
    ts.defense_strength_manual,
    ts.press_intensity_manual,
    ts.tactical_understanding,
    ts.team_chemistry,
    f.formation,
    tac.defensive_line,
    tac.pressing_trigger,
    ts.created_at AS last_updated
FROM teams t
LEFT JOIN team_strengths ts ON t.id = ts.team_id AND ts.is_active = TRUE
LEFT JOIN formations f ON t.id = f.team_id AND f.is_active = TRUE
LEFT JOIN tactics tac ON t.id = tac.team_id AND tac.is_active = TRUE;

COMMENT ON VIEW v_teams_latest IS 'Latest active team data for all teams';

-- Team strength rankings
CREATE OR REPLACE VIEW v_team_rankings AS
SELECT
    t.name,
    ts.attack_strength_manual,
    ts.defense_strength_manual,
    ts.press_intensity_manual,
    (ts.attack_strength_manual + ts.defense_strength_manual) / 2.0 AS overall_strength,
    RANK() OVER (ORDER BY (ts.attack_strength_manual + ts.defense_strength_manual) DESC) AS rank
FROM teams t
JOIN team_strengths ts ON t.id = ts.team_id
WHERE ts.is_active = TRUE
ORDER BY rank;

COMMENT ON VIEW v_team_rankings IS 'Team strength rankings by overall score';

-- =============================================================================
-- TEAM DATA UTILITY FUNCTIONS
-- =============================================================================

-- Compare two teams
CREATE OR REPLACE FUNCTION compare_teams(
    team1_name VARCHAR,
    team2_name VARCHAR
)
RETURNS TABLE(
    attribute VARCHAR,
    team1_value NUMERIC,
    team2_value NUMERIC,
    difference NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        attr AS attribute,
        t1_val AS team1_value,
        t2_val AS team2_value,
        (t2_val - t1_val) AS difference
    FROM (
        SELECT 'Attack' AS attr,
               (SELECT attack_strength_manual FROM team_strengths ts JOIN teams t ON ts.team_id = t.id WHERE t.name = team1_name AND ts.is_active) AS t1_val,
               (SELECT attack_strength_manual FROM team_strengths ts JOIN teams t ON ts.team_id = t.id WHERE t.name = team2_name AND ts.is_active) AS t2_val
        UNION ALL
        SELECT 'Defense',
               (SELECT defense_strength_manual FROM team_strengths ts JOIN teams t ON ts.team_id = t.id WHERE t.name = team1_name AND ts.is_active),
               (SELECT defense_strength_manual FROM team_strengths ts JOIN teams t ON ts.team_id = t.id WHERE t.name = team2_name AND ts.is_active)
        UNION ALL
        SELECT 'Press',
               (SELECT press_intensity_manual FROM team_strengths ts JOIN teams t ON ts.team_id = t.id WHERE t.name = team1_name AND ts.is_active),
               (SELECT press_intensity_manual FROM team_strengths ts JOIN teams t ON ts.team_id = t.id WHERE t.name = team2_name AND ts.is_active)
    ) AS comparison;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION compare_teams IS 'Compare strength attributes between two teams';

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
