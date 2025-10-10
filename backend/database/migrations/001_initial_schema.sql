-- Migration: 001_initial_schema
-- Created: 2025-10-08
-- Description: Initial database schema for AI Match Simulation v3.0

-- This migration creates all core tables for the system

BEGIN;

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Import main schema
\i ../schema.sql

-- Migration metadata
CREATE TABLE IF NOT EXISTS schema_migrations (
    version VARCHAR(50) PRIMARY KEY,
    description TEXT,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO schema_migrations (version, description)
VALUES ('001', 'Initial schema setup');

COMMIT;
