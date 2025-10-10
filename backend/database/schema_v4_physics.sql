-- =============================================================================
-- AI Match Simulation v4.0 - Physics Engine Extension
-- =============================================================================
-- Created: 2025-10-10
-- Purpose: Add physics-based simulation capabilities to existing v3 schema
--
-- This schema extends the existing v3 database with:
-- - Player models with position-specific attributes
-- - Team tactical profiles (migrated from frontend localStorage)
-- - Match physics states for real-time simulation
-- - Enhanced match metadata
-- =============================================================================

-- Enable required extensions (if not already enabled)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =============================================================================
-- TEAMS TABLE
-- =============================================================================
CREATE TABLE IF NOT EXISTS teams (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Basic info
    name VARCHAR(100) UNIQUE NOT NULL,
    short_name VARCHAR(20),
    code VARCHAR(10), -- e.g., "LIV", "MUN"

    -- League info
    league VARCHAR(50) DEFAULT 'Premier League',
    season VARCHAR(10), -- e.g., "2024-25"

    -- Tactical Profile (5 categories from existing framework)
    -- Each category contains weighted sub-attributes (0-100 scale)
    tactical_organization JSONB NOT NULL DEFAULT '{}',
    attacking_efficiency JSONB NOT NULL DEFAULT '{}',
    defensive_stability JSONB NOT NULL DEFAULT '{}',
    physicality_stamina JSONB NOT NULL DEFAULT '{}',
    psychological_factors JSONB NOT NULL DEFAULT '{}',

    -- Overall team rating (calculated from tactical profile)
    overall_rating DECIMAL(5,2),

    -- Formation & Style
    default_formation VARCHAR(10), -- e.g., "4-3-3", "3-5-2"
    playing_style JSONB, -- e.g., {"possession": 65, "pressing": 80, "tempo": 75}

    -- External IDs
    fpl_team_id INTEGER UNIQUE,
    external_ids JSONB DEFAULT '{}',

    -- Status
    is_active BOOLEAN DEFAULT TRUE,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_teams_name ON teams(name);
CREATE INDEX idx_teams_code ON teams(code);
CREATE INDEX idx_teams_fpl ON teams(fpl_team_id) WHERE fpl_team_id IS NOT NULL;
CREATE INDEX idx_teams_active ON teams(is_active) WHERE is_active = TRUE;

COMMENT ON TABLE teams IS 'EPL teams with tactical profiles and formations';
COMMENT ON COLUMN teams.tactical_organization IS 'Team organization: shape_discipline, positional_awareness, defensive_line, etc.';
COMMENT ON COLUMN teams.attacking_efficiency IS 'Attack metrics: chance_creation, finishing, movement, etc.';
COMMENT ON COLUMN teams.defensive_stability IS 'Defense metrics: marking, tackling, aerial, positioning, etc.';

-- =============================================================================
-- PLAYERS TABLE
-- =============================================================================
CREATE TABLE IF NOT EXISTS players (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID REFERENCES teams(id) ON DELETE CASCADE,

    -- Basic info
    name VARCHAR(100) NOT NULL,
    position VARCHAR(10) NOT NULL CHECK (position IN ('GK', 'CB', 'FB', 'DM', 'CM', 'CAM', 'WG', 'ST')),
    squad_number INTEGER,

    -- Physical attributes (0-100 scale)
    -- These directly map to physics simulation parameters
    pace DECIMAL(5,2), -- Sprint speed (80 pace = 8 m/s max speed)
    acceleration DECIMAL(5,2), -- Acceleration rate (80 accel = 8 m/s² max)
    stamina DECIMAL(5,2), -- Endurance (affects stamina drain rate)
    strength DECIMAL(5,2), -- Physical power (affects duels)
    agility DECIMAL(5,2), -- Change of direction speed

    -- Technical attributes (position-specific, stored as JSONB)
    -- Attributes vary by position:
    -- GK: reflexes, positioning, handling, diving, kicking, command_area
    -- CB: tackling, marking, heading, positioning, passing, composure
    -- FB: tackling, marking, crossing, stamina, positioning, pace
    -- DM: tackling, interceptions, passing, vision, positioning, stamina
    -- CM: passing, vision, dribbling, stamina, tackling, long_shots
    -- CAM: passing, vision, dribbling, shooting, creativity, weak_foot
    -- WG: pace, dribbling, crossing, shooting, stamina, weak_foot
    -- ST: shooting, finishing, positioning, heading, dribbling, pace
    technical_attributes JSONB NOT NULL DEFAULT '{}',

    -- Mental attributes
    mental_attributes JSONB DEFAULT '{}', -- composure, decisions, concentration, etc.

    -- Overall rating (calculated from all attributes)
    overall_rating DECIMAL(5,2),

    -- External IDs
    fpl_player_id INTEGER UNIQUE,
    external_ids JSONB DEFAULT '{}',

    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    injury_status VARCHAR(20), -- 'healthy', 'doubtful', 'injured', 'suspended'
    injury_return_date DATE,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_players_team ON players(team_id);
CREATE INDEX idx_players_position ON players(position);
CREATE INDEX idx_players_name ON players(name);
CREATE INDEX idx_players_fpl ON players(fpl_player_id) WHERE fpl_player_id IS NOT NULL;
CREATE INDEX idx_players_active ON players(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_players_rating ON players(overall_rating DESC);

COMMENT ON TABLE players IS 'EPL players with position-specific attributes for physics simulation';
COMMENT ON COLUMN players.pace IS 'Sprint speed: 70 = 7.0 m/s max speed';
COMMENT ON COLUMN players.acceleration IS 'Acceleration: 70 = 7.0 m/s² max acceleration';
COMMENT ON COLUMN players.technical_attributes IS 'Position-specific technical skills (0-100 each)';

-- =============================================================================
-- MATCH SIMULATIONS TABLE
-- =============================================================================
CREATE TABLE IF NOT EXISTS match_simulations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    match_id VARCHAR(100) NOT NULL REFERENCES matches(id),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,

    -- Simulation metadata
    simulation_type VARCHAR(20) CHECK (simulation_type IN ('basic', 'physics', 'full')),
    tier VARCHAR(20) NOT NULL CHECK (tier IN ('BASIC', 'PRO')),

    -- Input data hash (for caching)
    input_hash VARCHAR(64) NOT NULL,

    -- Simulation parameters
    parameters JSONB NOT NULL, -- weights, tactics, formations, etc.

    -- Results
    final_score JSONB NOT NULL, -- {"home": 2, "away": 1}
    probabilities JSONB NOT NULL, -- {"home_win": 0.45, "draw": 0.30, "away_win": 0.25}
    expected_goals JSONB, -- {"home": 1.8, "away": 1.2}

    -- Analysis
    analysis JSONB, -- key_factors, tactical_insight, etc.

    -- Events
    match_events JSONB, -- Array of events: goals, shots, passes, etc.

    -- Statistics
    statistics JSONB, -- possession, shots, passes, etc.

    -- Performance metrics
    simulation_duration_ms INTEGER, -- How long simulation took
    physics_ticks INTEGER, -- Number of physics update cycles

    -- AI metrics
    tokens_used INTEGER,
    cost_usd DECIMAL(10, 6),

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP DEFAULT (CURRENT_TIMESTAMP + INTERVAL '1 hour')
);

CREATE INDEX idx_simulations_match ON match_simulations(match_id);
CREATE INDEX idx_simulations_user ON match_simulations(user_id);
CREATE INDEX idx_simulations_hash ON match_simulations(input_hash);
CREATE INDEX idx_simulations_created ON match_simulations(created_at DESC);
CREATE INDEX idx_simulations_expires ON match_simulations(expires_at);

COMMENT ON TABLE match_simulations IS 'Physics-based match simulation results with full event tracking';
COMMENT ON COLUMN match_simulations.physics_ticks IS 'Number of 0.1s physics updates (5400 = 90 min)';

-- =============================================================================
-- MATCH PHYSICS STATES TABLE (Optional - for real-time playback)
-- =============================================================================
-- This table stores physics state at each time step (0.1s intervals)
-- WARNING: This will be VERY large (5400 rows per 90-min match)
-- Only enable if you need frame-by-frame playback
CREATE TABLE IF NOT EXISTS match_physics_states (
    id BIGSERIAL PRIMARY KEY,
    simulation_id UUID NOT NULL REFERENCES match_simulations(id) ON DELETE CASCADE,

    -- Time
    tick INTEGER NOT NULL, -- 0 to 5400 (0.1s intervals for 90 minutes)
    game_time DECIMAL(6,2), -- Seconds (0.0 to 5400.0)

    -- Ball state
    ball_position JSONB NOT NULL, -- {"x": 0.0, "y": 0.0, "z": 0.5} in meters
    ball_velocity JSONB NOT NULL, -- {"vx": 5.0, "vy": 0.0, "vz": 0.0} m/s
    ball_spin JSONB, -- {"wx": 0, "wy": 100, "wz": 0} rad/s

    -- Player states (array of 22 players)
    -- Each player: {id, position: [x,y], velocity: [vx,vy], stamina, action}
    home_players JSONB NOT NULL,
    away_players JSONB NOT NULL,

    -- Game state
    score JSONB NOT NULL, -- {"home": 0, "away": 0}
    possession VARCHAR(10), -- 'home' or 'away'

    -- Event flag (if something important happened at this tick)
    event_type VARCHAR(20), -- 'goal', 'shot', 'pass', 'tackle', null
    event_data JSONB,

    -- Compression: Only store states when something changes significantly
    -- is_keyframe: true = important state, false = can be interpolated
    is_keyframe BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_physics_states_sim ON match_physics_states(simulation_id);
CREATE INDEX idx_physics_states_tick ON match_physics_states(simulation_id, tick);
CREATE INDEX idx_physics_states_keyframes ON match_physics_states(simulation_id) WHERE is_keyframe = TRUE;

COMMENT ON TABLE match_physics_states IS 'Frame-by-frame physics states for match playback (LARGE table)';
COMMENT ON COLUMN match_physics_states.tick IS '0.1s time steps: 0-5400 for 90 minutes';
COMMENT ON COLUMN match_physics_states.is_keyframe IS 'True for important states, false for interpolatable states';

-- =============================================================================
-- PLAYER MATCH STATS TABLE
-- =============================================================================
CREATE TABLE IF NOT EXISTS player_match_stats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    simulation_id UUID NOT NULL REFERENCES match_simulations(id) ON DELETE CASCADE,
    player_id UUID NOT NULL REFERENCES players(id),
    team_id UUID NOT NULL REFERENCES teams(id),

    -- Basic stats
    minutes_played INTEGER,
    goals INTEGER DEFAULT 0,
    assists INTEGER DEFAULT 0,
    shots INTEGER DEFAULT 0,
    shots_on_target INTEGER DEFAULT 0,

    -- Passing
    passes INTEGER DEFAULT 0,
    passes_completed INTEGER DEFAULT 0,
    pass_accuracy DECIMAL(5,2),
    key_passes INTEGER DEFAULT 0,

    -- Defensive
    tackles INTEGER DEFAULT 0,
    tackles_won INTEGER DEFAULT 0,
    interceptions INTEGER DEFAULT 0,
    clearances INTEGER DEFAULT 0,

    -- Physical
    distance_covered_km DECIMAL(5,2), -- Total distance in km
    sprints INTEGER DEFAULT 0,
    avg_speed_kmh DECIMAL(5,2),
    max_speed_kmh DECIMAL(5,2),

    -- Advanced metrics
    expected_goals DECIMAL(5,2),
    expected_assists DECIMAL(5,2),

    -- Rating
    match_rating DECIMAL(4,2), -- 0-10 scale

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_player_stats_sim ON player_match_stats(simulation_id);
CREATE INDEX idx_player_stats_player ON player_match_stats(player_id);
CREATE INDEX idx_player_stats_rating ON player_match_stats(match_rating DESC);

COMMENT ON TABLE player_match_stats IS 'Individual player statistics from physics simulation';

-- =============================================================================
-- USER CUSTOM RATINGS TABLE
-- =============================================================================
-- Stores user's custom player ratings (overrides default ratings)
CREATE TABLE IF NOT EXISTS user_player_ratings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    player_id UUID NOT NULL REFERENCES players(id) ON DELETE CASCADE,

    -- Custom ratings
    custom_overall DECIMAL(5,2),
    custom_pace DECIMAL(5,2),
    custom_acceleration DECIMAL(5,2),
    custom_stamina DECIMAL(5,2),
    custom_strength DECIMAL(5,2),
    custom_agility DECIMAL(5,2),

    -- Custom technical attributes
    custom_technical JSONB,

    -- Notes
    notes TEXT,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(user_id, player_id)
);

CREATE INDEX idx_user_ratings_user ON user_player_ratings(user_id);
CREATE INDEX idx_user_ratings_player ON user_player_ratings(player_id);

COMMENT ON TABLE user_player_ratings IS 'User-specific custom player ratings (override defaults)';

-- =============================================================================
-- USER TEAM TACTICS TABLE
-- =============================================================================
-- Stores user's custom team tactical profiles
CREATE TABLE IF NOT EXISTS user_team_tactics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,

    -- Custom tactical profile
    custom_tactical_organization JSONB,
    custom_attacking_efficiency JSONB,
    custom_defensive_stability JSONB,
    custom_physicality_stamina JSONB,
    custom_psychological_factors JSONB,

    -- Custom formation
    custom_formation VARCHAR(10),
    custom_playing_style JSONB,

    -- Notes
    notes TEXT,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(user_id, team_id)
);

CREATE INDEX idx_user_tactics_user ON user_team_tactics(user_id);
CREATE INDEX idx_user_tactics_team ON user_team_tactics(team_id);

COMMENT ON TABLE user_team_tactics IS 'User-specific custom team tactical profiles';

-- =============================================================================
-- TRIGGERS
-- =============================================================================

-- Auto-update updated_at timestamp for new tables
CREATE TRIGGER update_teams_updated_at BEFORE UPDATE ON teams
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_players_updated_at BEFORE UPDATE ON players
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_ratings_updated_at BEFORE UPDATE ON user_player_ratings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_tactics_updated_at BEFORE UPDATE ON user_team_tactics
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- VIEWS
-- =============================================================================

-- Player stats with team info
CREATE OR REPLACE VIEW player_stats_view AS
SELECT
    p.id,
    p.name,
    p.position,
    p.squad_number,
    p.overall_rating,
    t.name as team_name,
    t.short_name as team_short_name,
    p.pace,
    p.acceleration,
    p.stamina,
    p.strength,
    p.agility,
    p.technical_attributes,
    p.is_active,
    p.injury_status
FROM players p
JOIN teams t ON p.team_id = t.id;

COMMENT ON VIEW player_stats_view IS 'Player statistics with team information';

-- Team strength summary
CREATE OR REPLACE VIEW team_strength_view AS
SELECT
    t.id,
    t.name,
    t.short_name,
    t.overall_rating,
    t.default_formation,
    COUNT(p.id) as squad_size,
    AVG(p.overall_rating) as avg_player_rating,
    MAX(p.overall_rating) as best_player_rating,
    COUNT(p.id) FILTER (WHERE p.position = 'ST') as strikers,
    COUNT(p.id) FILTER (WHERE p.position IN ('CM', 'CAM', 'DM')) as midfielders,
    COUNT(p.id) FILTER (WHERE p.position IN ('CB', 'FB')) as defenders,
    COUNT(p.id) FILTER (WHERE p.position = 'GK') as goalkeepers
FROM teams t
LEFT JOIN players p ON t.id = p.team_id AND p.is_active = TRUE
GROUP BY t.id;

COMMENT ON VIEW team_strength_view IS 'Team strength summary with squad composition';

-- Recent simulations summary
CREATE OR REPLACE VIEW recent_simulations_view AS
SELECT
    ms.id,
    ms.match_id,
    m.home_team,
    m.away_team,
    ms.final_score,
    ms.probabilities,
    ms.expected_goals,
    ms.simulation_type,
    ms.tier,
    ms.simulation_duration_ms,
    ms.created_at,
    u.email as user_email
FROM match_simulations ms
JOIN matches m ON ms.match_id = m.id
LEFT JOIN users u ON ms.user_id = u.id
ORDER BY ms.created_at DESC
LIMIT 100;

COMMENT ON VIEW recent_simulations_view IS 'Recent match simulations with match info';

-- =============================================================================
-- FUNCTIONS
-- =============================================================================

-- Function to get player with custom ratings (user overrides)
CREATE OR REPLACE FUNCTION get_player_with_custom_ratings(
    p_player_id UUID,
    p_user_id UUID DEFAULT NULL
)
RETURNS JSONB AS $$
DECLARE
    result JSONB;
BEGIN
    SELECT jsonb_build_object(
        'id', p.id,
        'name', p.name,
        'position', p.position,
        'overall_rating', COALESCE(upr.custom_overall, p.overall_rating),
        'pace', COALESCE(upr.custom_pace, p.pace),
        'acceleration', COALESCE(upr.custom_acceleration, p.acceleration),
        'stamina', COALESCE(upr.custom_stamina, p.stamina),
        'strength', COALESCE(upr.custom_strength, p.strength),
        'agility', COALESCE(upr.custom_agility, p.agility),
        'technical_attributes', COALESCE(upr.custom_technical, p.technical_attributes),
        'has_custom_ratings', (upr.id IS NOT NULL)
    ) INTO result
    FROM players p
    LEFT JOIN user_player_ratings upr ON p.id = upr.player_id AND upr.user_id = p_user_id
    WHERE p.id = p_player_id;

    RETURN result;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_player_with_custom_ratings IS 'Get player data with user custom ratings applied';

-- Function to get team with custom tactics
CREATE OR REPLACE FUNCTION get_team_with_custom_tactics(
    p_team_id UUID,
    p_user_id UUID DEFAULT NULL
)
RETURNS JSONB AS $$
DECLARE
    result JSONB;
BEGIN
    SELECT jsonb_build_object(
        'id', t.id,
        'name', t.name,
        'tactical_organization', COALESCE(utt.custom_tactical_organization, t.tactical_organization),
        'attacking_efficiency', COALESCE(utt.custom_attacking_efficiency, t.attacking_efficiency),
        'defensive_stability', COALESCE(utt.custom_defensive_stability, t.defensive_stability),
        'physicality_stamina', COALESCE(utt.custom_physicality_stamina, t.physicality_stamina),
        'psychological_factors', COALESCE(utt.custom_psychological_factors, t.psychological_factors),
        'formation', COALESCE(utt.custom_formation, t.default_formation),
        'playing_style', COALESCE(utt.custom_playing_style, t.playing_style),
        'has_custom_tactics', (utt.id IS NOT NULL)
    ) INTO result
    FROM teams t
    LEFT JOIN user_team_tactics utt ON t.id = utt.team_id AND utt.user_id = p_user_id
    WHERE t.id = p_team_id;

    RETURN result;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_team_with_custom_tactics IS 'Get team data with user custom tactics applied';

-- =============================================================================
-- SAMPLE DATA (Optional - for testing)
-- =============================================================================

-- Uncomment to insert sample EPL teams
/*
INSERT INTO teams (name, short_name, code, overall_rating, default_formation) VALUES
('Liverpool', 'Liverpool', 'LIV', 88.5, '4-3-3'),
('Manchester City', 'Man City', 'MCI', 89.0, '4-3-3'),
('Arsenal', 'Arsenal', 'ARS', 86.0, '4-3-3'),
('Manchester United', 'Man Utd', 'MUN', 82.0, '4-2-3-1')
ON CONFLICT (name) DO NOTHING;
*/

-- =============================================================================
-- GRANTS (Adjust based on your setup)
-- =============================================================================

-- Grant permissions to application user (adjust username as needed)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_user;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO app_user;

-- =============================================================================
-- END OF SCHEMA
-- =============================================================================

-- Validation query to check schema version
DO $$
BEGIN
    RAISE NOTICE 'Soccer Predictor v4.0 Physics Schema loaded successfully';
    RAISE NOTICE 'Tables created: teams, players, match_simulations, match_physics_states';
    RAISE NOTICE 'Ready for physics-based simulation';
END $$;
