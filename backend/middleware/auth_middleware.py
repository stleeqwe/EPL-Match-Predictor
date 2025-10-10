"""
Authentication Middleware
AI Match Simulation v3.0

JWT-based authentication middleware for Flask.
"""

from functools import wraps
from flask import request, jsonify, g
from typing import Optional, Callable
import logging

from auth.jwt_handler import JWTHandler, TokenExpiredError, InvalidTokenError

logger = logging.getLogger(__name__)


class AuthMiddleware:
    """Authentication middleware"""

    def __init__(self, jwt_handler: JWTHandler):
        """
        Initialize auth middleware

        Args:
            jwt_handler: JWT handler instance
        """
        self.jwt_handler = jwt_handler

    def extract_token_from_header(self) -> Optional[str]:
        """
        Extract JWT token from Authorization header

        Returns:
            Token string or None
        """
        auth_header = request.headers.get('Authorization')

        if not auth_header:
            return None

        # Expected format: "Bearer <token>"
        parts = auth_header.split()

        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return None

        return parts[1]

    def verify_request(self) -> tuple[bool, Optional[dict], Optional[str]]:
        """
        Verify current request

        Returns:
            Tuple of (is_valid, payload, error_message)
        """
        # Extract token
        token = self.extract_token_from_header()

        if not token:
            return False, None, "Missing authorization token"

        # Verify token
        try:
            payload = self.jwt_handler.verify_token(token, token_type='access')
            return True, payload, None

        except TokenExpiredError:
            return False, None, "Token has expired"

        except InvalidTokenError as e:
            return False, None, f"Invalid token: {str(e)}"

        except Exception as e:
            logger.error(f"Token verification error: {e}")
            return False, None, "Authentication failed"


# Global auth middleware instance
_auth_middleware: Optional[AuthMiddleware] = None


def init_auth_middleware(jwt_handler: JWTHandler):
    """Initialize global auth middleware"""
    global _auth_middleware
    _auth_middleware = AuthMiddleware(jwt_handler)
    logger.info("Auth middleware initialized")


def get_auth_middleware() -> AuthMiddleware:
    """Get auth middleware instance"""
    if _auth_middleware is None:
        raise RuntimeError("Auth middleware not initialized")
    return _auth_middleware


def require_auth(f: Callable) -> Callable:
    """
    Decorator to require authentication

    Usage:
        @app.route('/protected')
        @require_auth
        def protected_endpoint():
            user_id = g.user_id
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        middleware = get_auth_middleware()
        is_valid, payload, error = middleware.verify_request()

        if not is_valid:
            return jsonify({
                'error': 'Unauthorized',
                'message': error
            }), 401

        # Store user info in g (Flask request context)
        g.user_id = payload['user_id']
        g.user_tier = payload['tier']
        g.user_email = payload['email']
        g.token_payload = payload

        return f(*args, **kwargs)

    return decorated_function


def optional_auth(f: Callable) -> Callable:
    """
    Decorator for optional authentication
    Sets g.user_id if authenticated, but doesn't require it

    Usage:
        @app.route('/public-but-personalized')
        @optional_auth
        def endpoint():
            user_id = getattr(g, 'user_id', None)
            if user_id:
                # Personalized response
            else:
                # Public response
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        middleware = get_auth_middleware()
        is_valid, payload, error = middleware.verify_request()

        if is_valid:
            # Store user info
            g.user_id = payload['user_id']
            g.user_tier = payload['tier']
            g.user_email = payload['email']
            g.token_payload = payload
        else:
            # No auth, but continue anyway
            g.user_id = None
            g.user_tier = None
            g.user_email = None
            g.token_payload = None

        return f(*args, **kwargs)

    return decorated_function


def require_tier(min_tier: str):
    """
    Decorator to require minimum user tier

    Args:
        min_tier: Minimum tier required (BASIC/PRO)

    Usage:
        @app.route('/pro-only')
        @require_auth
        @require_tier('PRO')
        def pro_endpoint():
            ...
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_tier = getattr(g, 'user_tier', None)

            if not user_tier:
                return jsonify({
                    'error': 'Unauthorized',
                    'message': 'Authentication required'
                }), 401

            # Tier hierarchy: PRO > BASIC
            tier_levels = {'BASIC': 0, 'PRO': 1}

            if tier_levels.get(user_tier, 0) < tier_levels.get(min_tier, 999):
                return jsonify({
                    'error': 'Forbidden',
                    'message': f'This endpoint requires {min_tier} tier',
                    'current_tier': user_tier,
                    'upgrade_url': '/pricing'
                }), 403

            return f(*args, **kwargs)

        return decorated_function
    return decorator
