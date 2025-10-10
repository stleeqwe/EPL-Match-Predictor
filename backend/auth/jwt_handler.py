"""
JWT Token Handler
AI Match Simulation v3.0

Handles JWT token creation, verification, and management.
- Access Token: 15 minutes lifetime
- Refresh Token: 30 days lifetime
- Token rotation and blacklisting support
"""

import jwt
import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class TokenError(Exception):
    """Base exception for token errors"""
    pass


class TokenExpiredError(TokenError):
    """Token has expired"""
    pass


class InvalidTokenError(TokenError):
    """Token is invalid"""
    pass


class JWTHandler:
    """JWT token management"""

    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        access_token_expires: int = 900,  # 15 minutes
        refresh_token_expires: int = 2592000  # 30 days
    ):
        """
        Initialize JWT handler

        Args:
            secret_key: Secret key for signing tokens
            algorithm: JWT algorithm (default: HS256)
            access_token_expires: Access token lifetime in seconds
            refresh_token_expires: Refresh token lifetime in seconds
        """
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expires = access_token_expires
        self.refresh_token_expires = refresh_token_expires

    def create_access_token(
        self,
        user_id: str,
        tier: str,
        email: str,
        additional_claims: Optional[Dict] = None
    ) -> str:
        """
        Create access token

        Args:
            user_id: User UUID
            tier: User tier (BASIC/PRO)
            email: User email
            additional_claims: Additional claims to include

        Returns:
            JWT access token string
        """
        now = datetime.utcnow()

        payload = {
            'user_id': user_id,
            'tier': tier,
            'email': email,
            'type': 'access',
            'exp': now + timedelta(seconds=self.access_token_expires),
            'iat': now,
            'jti': secrets.token_urlsafe(32)  # JWT ID for revocation
        }

        # Add additional claims if provided
        if additional_claims:
            payload.update(additional_claims)

        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

        logger.debug(f"Created access token for user {user_id}")

        return token

    def create_refresh_token(self, user_id: str) -> str:
        """
        Create refresh token

        Args:
            user_id: User UUID

        Returns:
            JWT refresh token string
        """
        now = datetime.utcnow()

        payload = {
            'user_id': user_id,
            'type': 'refresh',
            'exp': now + timedelta(seconds=self.refresh_token_expires),
            'iat': now,
            'jti': secrets.token_urlsafe(32)
        }

        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

        logger.debug(f"Created refresh token for user {user_id}")

        return token

    def verify_token(
        self,
        token: str,
        token_type: str = 'access',
        check_blacklist: bool = True
    ) -> Dict:
        """
        Verify and decode JWT token

        Args:
            token: JWT token string
            token_type: Expected token type ('access' or 'refresh')
            check_blacklist: Whether to check if token is blacklisted

        Returns:
            Decoded token payload

        Raises:
            TokenExpiredError: Token has expired
            InvalidTokenError: Token is invalid
        """
        try:
            # Decode token
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )

            # Verify token type
            if payload.get('type') != token_type:
                raise InvalidTokenError(f"Expected {token_type} token")

            # Check blacklist if requested
            if check_blacklist and self._is_blacklisted(payload.get('jti')):
                raise InvalidTokenError("Token has been revoked")

            logger.debug(f"Verified {token_type} token for user {payload.get('user_id')}")

            return payload

        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            raise TokenExpiredError("Token has expired")

        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            raise InvalidTokenError(f"Invalid token: {str(e)}")

    def refresh_access_token(self, refresh_token: str) -> Dict[str, str]:
        """
        Create new access token from refresh token

        Args:
            refresh_token: Valid refresh token

        Returns:
            Dict with new access_token and refresh_token

        Raises:
            TokenExpiredError: Refresh token expired
            InvalidTokenError: Refresh token invalid
        """
        # Verify refresh token
        payload = self.verify_token(refresh_token, token_type='refresh')

        user_id = payload['user_id']

        # Get user tier from database (would need to be passed in)
        # For now, we'll need to fetch it externally
        # This method should be called with tier information

        # Create new tokens
        new_access_token = self.create_access_token(
            user_id=user_id,
            tier=payload.get('tier', 'BASIC'),  # Should be fetched from DB
            email=payload.get('email', '')
        )

        # Optionally create new refresh token (token rotation)
        new_refresh_token = self.create_refresh_token(user_id)

        # Blacklist old refresh token
        self._blacklist_token(payload['jti'])

        logger.info(f"Refreshed tokens for user {user_id}")

        return {
            'access_token': new_access_token,
            'refresh_token': new_refresh_token
        }

    def revoke_token(self, token: str) -> bool:
        """
        Revoke a token by adding it to blacklist

        Args:
            token: JWT token to revoke

        Returns:
            True if successful
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={'verify_exp': False}  # Don't check expiration
            )

            jti = payload.get('jti')
            if jti:
                self._blacklist_token(jti)
                logger.info(f"Revoked token {jti}")
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to revoke token: {e}")
            return False

    def _is_blacklisted(self, jti: str) -> bool:
        """
        Check if token JTI is blacklisted

        This should be implemented using Redis for production.
        Returns False for now (placeholder).

        Args:
            jti: JWT ID

        Returns:
            True if blacklisted, False otherwise
        """
        # TODO: Implement Redis blacklist check
        # from database.connection import get_redis
        # redis_client = get_redis()
        # return redis_client.exists(f"blacklist:{jti}")

        return False

    def _blacklist_token(self, jti: str, ttl: Optional[int] = None) -> bool:
        """
        Add token JTI to blacklist

        This should be implemented using Redis for production.

        Args:
            jti: JWT ID
            ttl: Time to live in seconds (default: refresh_token_expires)

        Returns:
            True if successful
        """
        # TODO: Implement Redis blacklist
        # from database.connection import get_redis
        # redis_client = get_redis()
        # ttl = ttl or self.refresh_token_expires
        # redis_client.setex(f"blacklist:{jti}", ttl, "1")

        logger.debug(f"Blacklisted token {jti}")
        return True

    @staticmethod
    def decode_token_without_verification(token: str) -> Optional[Dict]:
        """
        Decode token without verification (for inspection only)

        Args:
            token: JWT token

        Returns:
            Decoded payload or None
        """
        try:
            return jwt.decode(
                token,
                options={"verify_signature": False}
            )
        except Exception:
            return None


# ============================================================================
# Singleton Instance
# ============================================================================

_jwt_handler_instance = None


def get_jwt_handler():
    """Get singleton JWTHandler instance."""
    global _jwt_handler_instance
    if _jwt_handler_instance is None:
        import os
        secret_key = os.getenv('JWT_SECRET_KEY', secrets.token_urlsafe(32))
        _jwt_handler_instance = JWTHandler(
            secret_key=secret_key,
            access_token_expires=int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 900)),
            refresh_token_expires=int(os.getenv('JWT_REFRESH_TOKEN_EXPIRES', 2592000))
        )
        logger.info("JWTHandler singleton initialized")
    return _jwt_handler_instance
