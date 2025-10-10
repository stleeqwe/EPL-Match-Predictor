"""
User Repository (SQLite version)
AI Match Simulation v3.0

Database operations for User management using SQLite.
"""

from typing import Optional, Dict, List
from datetime import datetime
import secrets
import logging
import sqlite3
import json
import uuid
from pathlib import Path

logger = logging.getLogger(__name__)

# Database path
DB_PATH = Path(__file__).parent.parent / 'data' / 'auth.db'


class User:
    """User model"""

    def __init__(self, data: Dict):
        """Initialize user from database row"""
        self.id = data.get('id')
        self.email = data.get('email')
        self.password_hash = data.get('password_hash')
        self.display_name = data.get('display_name')
        self.avatar_url = data.get('avatar_url')
        self.tier = data.get('tier', 'BASIC')
        self.stripe_customer_id = data.get('stripe_customer_id')
        self.created_at = data.get('created_at')
        self.updated_at = data.get('updated_at')
        self.last_login_at = data.get('last_login_at')
        self.is_active = bool(data.get('is_active', True))
        self.is_verified = bool(data.get('is_verified', False))
        self.verification_token = data.get('verification_token')
        self.verification_token_expires = data.get('verification_token_expires')
        self.reset_token = data.get('reset_token')
        self.reset_token_expires = data.get('reset_token_expires')

        # Parse JSON fields
        preferences_str = data.get('preferences', '{}')
        self.preferences = json.loads(preferences_str) if isinstance(preferences_str, str) else preferences_str

        metadata_str = data.get('metadata', '{}')
        self.metadata = json.loads(metadata_str) if isinstance(metadata_str, str) else metadata_str

    def to_dict(self, include_sensitive: bool = False) -> Dict:
        """
        Convert user to dictionary

        Args:
            include_sensitive: Whether to include sensitive fields

        Returns:
            User dict
        """
        user_dict = {
            'id': str(self.id),
            'email': self.email,
            'display_name': self.display_name,
            'avatar_url': self.avatar_url,
            'tier': self.tier,
            'created_at': self.created_at if isinstance(self.created_at, str) else (self.created_at.isoformat() if self.created_at else None),
            'last_login_at': self.last_login_at if isinstance(self.last_login_at, str) else (self.last_login_at.isoformat() if self.last_login_at else None),
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'preferences': self.preferences
        }

        if include_sensitive:
            user_dict.update({
                'password_hash': self.password_hash,
                'stripe_customer_id': self.stripe_customer_id,
                'verification_token': self.verification_token,
                'reset_token': self.reset_token,
                'metadata': self.metadata
            })

        return user_dict


class UserRepository:
    """User database operations (SQLite)"""

    @staticmethod
    def _get_connection():
        """Get database connection"""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        return conn

    @staticmethod
    def create_user(email: str, password_hash: str, display_name: Optional[str] = None,
                   tier: str = 'BASIC') -> Optional[User]:
        """
        Create a new user

        Args:
            email: User email (unique)
            password_hash: Hashed password
            display_name: User's display name
            tier: Subscription tier (BASIC or PRO)

        Returns:
            User object if created, None if failed
        """
        try:
            conn = UserRepository._get_connection()
            cursor = conn.cursor()

            user_id = str(uuid.uuid4())
            now = datetime.utcnow().isoformat()

            cursor.execute("""
                INSERT INTO users (
                    id, email, password_hash, display_name, tier,
                    created_at, updated_at, is_active, is_verified
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, 1, 0)
            """, (user_id, email.lower(), password_hash, display_name, tier, now, now))

            conn.commit()

            # Fetch created user
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            conn.close()

            if row:
                user_data = dict(row)
                logger.info(f"User created: {email}")
                return User(user_data)

            return None

        except sqlite3.IntegrityError as e:
            logger.error(f"User creation failed (duplicate email?): {e}")
            return None
        except Exception as e:
            logger.error(f"User creation error: {e}")
            return None

    @staticmethod
    def get_user_by_email(email: str) -> Optional[User]:
        """
        Get user by email

        Args:
            email: User email

        Returns:
            User object if found, None otherwise
        """
        try:
            conn = UserRepository._get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM users WHERE email = ?", (email.lower(),))
            row = cursor.fetchone()
            conn.close()

            if row:
                return User(dict(row))

            return None

        except Exception as e:
            logger.error(f"Get user by email error: {e}")
            return None

    @staticmethod
    def get_user_by_id(user_id: str) -> Optional[User]:
        """
        Get user by ID

        Args:
            user_id: User ID

        Returns:
            User object if found, None otherwise
        """
        try:
            conn = UserRepository._get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            conn.close()

            if row:
                return User(dict(row))

            return None

        except Exception as e:
            logger.error(f"Get user by ID error: {e}")
            return None

    @staticmethod
    def update_last_login(user_id: str) -> bool:
        """
        Update user's last login timestamp

        Args:
            user_id: User ID

        Returns:
            True if updated, False otherwise
        """
        try:
            conn = UserRepository._get_connection()
            cursor = conn.cursor()

            now = datetime.utcnow().isoformat()
            cursor.execute("""
                UPDATE users
                SET last_login_at = ?, updated_at = ?
                WHERE id = ?
            """, (now, now, user_id))

            conn.commit()
            success = cursor.rowcount > 0
            conn.close()

            return success

        except Exception as e:
            logger.error(f"Update last login error: {e}")
            return False

    @staticmethod
    def update_tier(user_id: str, tier: str) -> bool:
        """
        Update user's subscription tier

        Args:
            user_id: User ID
            tier: New tier (BASIC or PRO)

        Returns:
            True if updated, False otherwise
        """
        try:
            conn = UserRepository._get_connection()
            cursor = conn.cursor()

            now = datetime.utcnow().isoformat()
            cursor.execute("""
                UPDATE users
                SET tier = ?, updated_at = ?
                WHERE id = ?
            """, (tier, now, user_id))

            conn.commit()
            success = cursor.rowcount > 0
            conn.close()

            logger.info(f"User {user_id} tier updated to {tier}")
            return success

        except Exception as e:
            logger.error(f"Update tier error: {e}")
            return False

    @staticmethod
    def get_all_users(limit: int = 100, offset: int = 0) -> List[User]:
        """
        Get all users (paginated)

        Args:
            limit: Maximum number of users
            offset: Offset for pagination

        Returns:
            List of User objects
        """
        try:
            conn = UserRepository._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM users
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """, (limit, offset))

            rows = cursor.fetchall()
            conn.close()

            return [User(dict(row)) for row in rows]

        except Exception as e:
            logger.error(f"Get all users error: {e}")
            return []

    @staticmethod
    def count_users() -> int:
        """
        Count total number of users

        Returns:
            Total user count
        """
        try:
            conn = UserRepository._get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM users")
            count = cursor.fetchone()[0]
            conn.close()

            return count

        except Exception as e:
            logger.error(f"Count users error: {e}")
            return 0
