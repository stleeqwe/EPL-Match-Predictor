"""
User Repository
AI Match Simulation v3.0

Database operations for User management.
"""

from typing import Optional, Dict, List
from datetime import datetime
import secrets
import logging

from database.connection import db_pool

logger = logging.getLogger(__name__)


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
        self.is_active = data.get('is_active', True)
        self.is_verified = data.get('is_verified', False)
        self.verification_token = data.get('verification_token')
        self.verification_token_expires = data.get('verification_token_expires')
        self.reset_token = data.get('reset_token')
        self.reset_token_expires = data.get('reset_token_expires')
        self.preferences = data.get('preferences', {})
        self.metadata = data.get('metadata', {})

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
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None,
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
    """User database operations"""

    @staticmethod
    def create(
        email: str,
        password_hash: str,
        display_name: Optional[str] = None,
        tier: str = 'BASIC'
    ) -> User:
        """
        Create new user

        Args:
            email: User email
            password_hash: Hashed password
            display_name: Display name (optional)
            tier: User tier (default: BASIC)

        Returns:
            Created User object

        Raises:
            Exception: If user creation fails
        """
        try:
            # Generate verification token
            verification_token = secrets.token_urlsafe(32)

            with db_pool.get_cursor() as cur:
                cur.execute("""
                    INSERT INTO users (
                        email, password_hash, display_name, tier,
                        verification_token, is_verified
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING *
                """, (
                    email,
                    password_hash,
                    display_name,
                    tier,
                    verification_token,
                    False  # Email not verified yet
                ))

                row = cur.fetchone()

                logger.info(f"Created user: {email}")

                return User(row)

        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            raise

    @staticmethod
    def get_by_id(user_id: str) -> Optional[User]:
        """
        Get user by ID

        Args:
            user_id: User UUID

        Returns:
            User object or None
        """
        try:
            with db_pool.get_cursor() as cur:
                cur.execute("""
                    SELECT * FROM users WHERE id = %s
                """, (user_id,))

                row = cur.fetchone()

                if row:
                    return User(row)

                return None

        except Exception as e:
            logger.error(f"Failed to get user by ID: {e}")
            return None

    @staticmethod
    def get_by_email(email: str) -> Optional[User]:
        """
        Get user by email

        Args:
            email: User email

        Returns:
            User object or None
        """
        try:
            with db_pool.get_cursor() as cur:
                cur.execute("""
                    SELECT * FROM users WHERE email = %s
                """, (email,))

                row = cur.fetchone()

                if row:
                    return User(row)

                return None

        except Exception as e:
            logger.error(f"Failed to get user by email: {e}")
            return None

    @staticmethod
    def update_last_login(user_id: str) -> bool:
        """
        Update user's last login timestamp

        Args:
            user_id: User UUID

        Returns:
            True if successful
        """
        try:
            with db_pool.get_cursor() as cur:
                cur.execute("""
                    UPDATE users
                    SET last_login_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (user_id,))

                logger.debug(f"Updated last login for user {user_id}")
                return True

        except Exception as e:
            logger.error(f"Failed to update last login: {e}")
            return False

    @staticmethod
    def update_tier(user_id: str, tier: str) -> bool:
        """
        Update user tier

        Args:
            user_id: User UUID
            tier: New tier (BASIC/PRO)

        Returns:
            True if successful
        """
        try:
            with db_pool.get_cursor() as cur:
                cur.execute("""
                    UPDATE users
                    SET tier = %s
                    WHERE id = %s
                """, (tier, user_id))

                logger.info(f"Updated tier for user {user_id} to {tier}")
                return True

        except Exception as e:
            logger.error(f"Failed to update tier: {e}")
            return False

    @staticmethod
    def update_stripe_customer(user_id: str, stripe_customer_id: str) -> bool:
        """
        Update Stripe customer ID

        Args:
            user_id: User UUID
            stripe_customer_id: Stripe customer ID

        Returns:
            True if successful
        """
        try:
            with db_pool.get_cursor() as cur:
                cur.execute("""
                    UPDATE users
                    SET stripe_customer_id = %s
                    WHERE id = %s
                """, (stripe_customer_id, user_id))

                logger.info(f"Updated Stripe customer for user {user_id}")
                return True

        except Exception as e:
            logger.error(f"Failed to update Stripe customer: {e}")
            return False

    @staticmethod
    def verify_email(verification_token: str) -> bool:
        """
        Verify user email with token

        Args:
            verification_token: Email verification token

        Returns:
            True if successful
        """
        try:
            with db_pool.get_cursor() as cur:
                cur.execute("""
                    UPDATE users
                    SET is_verified = true,
                        verification_token = NULL
                    WHERE verification_token = %s
                    AND is_verified = false
                    RETURNING id
                """, (verification_token,))

                row = cur.fetchone()

                if row:
                    logger.info(f"Verified email for user {row['id']}")
                    return True

                return False

        except Exception as e:
            logger.error(f"Failed to verify email: {e}")
            return False

    @staticmethod
    def create_reset_token(email: str) -> Optional[str]:
        """
        Create password reset token

        Args:
            email: User email

        Returns:
            Reset token or None
        """
        try:
            reset_token = secrets.token_urlsafe(32)

            with db_pool.get_cursor() as cur:
                cur.execute("""
                    UPDATE users
                    SET reset_token = %s,
                        reset_token_expires = CURRENT_TIMESTAMP + INTERVAL '1 hour'
                    WHERE email = %s
                    AND is_active = true
                    RETURNING id
                """, (reset_token, email))

                row = cur.fetchone()

                if row:
                    logger.info(f"Created reset token for user {row['id']}")
                    return reset_token

                return None

        except Exception as e:
            logger.error(f"Failed to create reset token: {e}")
            return None

    @staticmethod
    def reset_password(reset_token: str, new_password_hash: str) -> bool:
        """
        Reset password with token

        Args:
            reset_token: Password reset token
            new_password_hash: New hashed password

        Returns:
            True if successful
        """
        try:
            with db_pool.get_cursor() as cur:
                cur.execute("""
                    UPDATE users
                    SET password_hash = %s,
                        reset_token = NULL,
                        reset_token_expires = NULL
                    WHERE reset_token = %s
                    AND reset_token_expires > CURRENT_TIMESTAMP
                    RETURNING id
                """, (new_password_hash, reset_token))

                row = cur.fetchone()

                if row:
                    logger.info(f"Reset password for user {row['id']}")
                    return True

                return False

        except Exception as e:
            logger.error(f"Failed to reset password: {e}")
            return False

    @staticmethod
    def update_profile(
        user_id: str,
        display_name: Optional[str] = None,
        avatar_url: Optional[str] = None,
        preferences: Optional[Dict] = None
    ) -> bool:
        """
        Update user profile

        Args:
            user_id: User UUID
            display_name: New display name
            avatar_url: New avatar URL
            preferences: Updated preferences

        Returns:
            True if successful
        """
        try:
            updates = []
            params = []

            if display_name is not None:
                updates.append("display_name = %s")
                params.append(display_name)

            if avatar_url is not None:
                updates.append("avatar_url = %s")
                params.append(avatar_url)

            if preferences is not None:
                updates.append("preferences = %s")
                params.append(str(preferences))  # JSONB

            if not updates:
                return True  # Nothing to update

            params.append(user_id)

            with db_pool.get_cursor() as cur:
                query = f"""
                    UPDATE users
                    SET {', '.join(updates)}
                    WHERE id = %s
                """
                cur.execute(query, params)

                logger.info(f"Updated profile for user {user_id}")
                return True

        except Exception as e:
            logger.error(f"Failed to update profile: {e}")
            return False

    @staticmethod
    def deactivate(user_id: str) -> bool:
        """
        Deactivate user account

        Args:
            user_id: User UUID

        Returns:
            True if successful
        """
        try:
            with db_pool.get_cursor() as cur:
                cur.execute("""
                    UPDATE users
                    SET is_active = false
                    WHERE id = %s
                """, (user_id,))

                logger.info(f"Deactivated user {user_id}")
                return True

        except Exception as e:
            logger.error(f"Failed to deactivate user: {e}")
            return False

    @staticmethod
    def get_all(
        limit: int = 100,
        offset: int = 0,
        tier: Optional[str] = None
    ) -> List[User]:
        """
        Get all users (admin function)

        Args:
            limit: Max results
            offset: Offset for pagination
            tier: Filter by tier (optional)

        Returns:
            List of User objects
        """
        try:
            with db_pool.get_cursor() as cur:
                if tier:
                    cur.execute("""
                        SELECT * FROM users
                        WHERE tier = %s
                        ORDER BY created_at DESC
                        LIMIT %s OFFSET %s
                    """, (tier, limit, offset))
                else:
                    cur.execute("""
                        SELECT * FROM users
                        ORDER BY created_at DESC
                        LIMIT %s OFFSET %s
                    """, (limit, offset))

                rows = cur.fetchall()

                return [User(row) for row in rows]

        except Exception as e:
            logger.error(f"Failed to get users: {e}")
            return []
