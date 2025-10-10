#!/usr/bin/env python3
"""
Initialize SQLite Auth Database
Quick setup for V3 Auth testing with SQLite
"""

import sqlite3
import os
from pathlib import Path

# Database path
DB_PATH = Path(__file__).parent / 'data' / 'auth.db'

def init_database():
    """Initialize SQLite database with users table"""

    # Ensure data directory exists
    DB_PATH.parent.mkdir(exist_ok=True)

    print(f"📁 Database path: {DB_PATH}")

    # Connect to database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            display_name TEXT,
            avatar_url TEXT,
            tier TEXT DEFAULT 'BASIC' CHECK (tier IN ('BASIC', 'PRO')),
            stripe_customer_id TEXT UNIQUE,

            -- Status fields
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            last_login_at TEXT,
            is_active INTEGER DEFAULT 1,
            is_verified INTEGER DEFAULT 0,

            -- Verification tokens
            verification_token TEXT,
            verification_token_expires TEXT,
            reset_token TEXT,
            reset_token_expires TEXT,

            -- JSON fields (stored as TEXT)
            preferences TEXT DEFAULT '{}',
            metadata TEXT DEFAULT '{}'
        )
    """)

    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_tier ON users(tier)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active) WHERE is_active = 1")

    # Create subscriptions table (for future use)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subscriptions (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            stripe_subscription_id TEXT UNIQUE,
            tier TEXT NOT NULL CHECK (tier IN ('BASIC', 'PRO')),
            status TEXT NOT NULL,
            current_period_start TEXT,
            current_period_end TEXT,
            cancel_at_period_end INTEGER DEFAULT 0,
            canceled_at TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            metadata TEXT DEFAULT '{}'
        )
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_subs_user_id ON subscriptions(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_subs_status ON subscriptions(status)")

    conn.commit()
    conn.close()

    print("✅ Database initialized successfully!")
    print(f"   - users table created")
    print(f"   - subscriptions table created")
    print(f"   - indexes created")
    print(f"\n🎉 Ready for V3 Auth testing!")

if __name__ == '__main__':
    init_database()
