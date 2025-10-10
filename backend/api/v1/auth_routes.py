"""
Authentication API Routes
AI Match Simulation v3.0

Flask routes for user authentication and session management.
"""

from flask import Blueprint, request, jsonify
from typing import Dict
import logging

from auth.jwt_handler import get_jwt_handler
from auth.password_handler import get_password_handler
# Use SQLite version for quick testing
from repositories.user_repository_sqlite import UserRepository

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/api/v1/auth')

# Initialize handlers
jwt_handler = get_jwt_handler()
password_handler = get_password_handler()


# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@auth_bp.route('/signup', methods=['POST'])
def signup():
    """
    User registration endpoint.

    Required in request body:
    - email: User's email address
    - password: User's password (min 8 chars)

    Optional:
    - display_name: User's display name

    Returns:
        JSON with access_token, refresh_token, and user info
    """
    try:
        data = request.get_json() or {}
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        display_name = data.get('display_name', '').strip()

        # Validate input
        if not email or not password:
            return jsonify({
                'error': 'Missing required fields',
                'message': 'Email and password are required'
            }), 400

        # Validate email format
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return jsonify({
                'error': 'Invalid email',
                'message': 'Please provide a valid email address'
            }), 400

        # Validate password strength
        is_valid, checks, score = password_handler.check_password_strength(password)
        if not is_valid:
            return jsonify({
                'error': 'Weak password',
                'message': 'Password must be at least 8 characters with mixed case and numbers'
            }), 400

        # Check if user already exists
        existing_user = UserRepository.get_user_by_email(email)
        if existing_user:
            return jsonify({
                'error': 'User already exists',
                'message': 'An account with this email already exists'
            }), 409

        # Hash password
        password_hash = password_handler.hash_password(password)

        # Create user
        user = UserRepository.create_user(
            email=email,
            password_hash=password_hash,
            display_name=display_name or email.split('@')[0],
            tier='BASIC'  # New users start with BASIC tier
        )

        # Generate tokens
        access_token = jwt_handler.create_access_token(
            user_id=str(user.id),
            tier=user.tier,
            email=user.email
        )
        refresh_token = jwt_handler.create_refresh_token(
            user_id=str(user.id)
        )

        logger.info(f"New user registered: {email}")

        return jsonify({
            'success': True,
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': {
                'id': str(user.id),
                'email': user.email,
                'display_name': user.display_name,
                'tier': user.tier
            }
        }), 201

    except Exception as e:
        logger.error(f"Signup error: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Failed to create account'
        }), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    User login endpoint.

    Required in request body:
    - email: User's email address
    - password: User's password

    Returns:
        JSON with access_token, refresh_token, and user info
    """
    try:
        data = request.get_json() or {}
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')

        # Validate input
        if not email or not password:
            return jsonify({
                'error': 'Missing credentials',
                'message': 'Email and password are required'
            }), 400

        # Get user
        user = UserRepository.get_user_by_email(email)
        if not user:
            return jsonify({
                'error': 'Invalid credentials',
                'message': 'Email or password is incorrect'
            }), 401

        # Verify password
        if not password_handler.verify_password(password, user.password_hash):
            return jsonify({
                'error': 'Invalid credentials',
                'message': 'Email or password is incorrect'
            }), 401

        # Generate tokens
        access_token = jwt_handler.create_access_token(
            user_id=str(user.id),
            tier=user.tier,
            email=user.email
        )
        refresh_token = jwt_handler.create_refresh_token(
            user_id=str(user.id)
        )

        logger.info(f"User logged in: {email}")

        return jsonify({
            'success': True,
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': {
                'id': str(user.id),
                'email': user.email,
                'display_name': user.display_name,
                'tier': user.tier
            }
        }), 200

    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Login failed'
        }), 500


@auth_bp.route('/refresh', methods=['POST'])
def refresh():
    """
    Refresh access token using refresh token.

    Required in request body:
    - refresh_token: Valid refresh token

    Returns:
        JSON with new access_token
    """
    try:
        data = request.get_json() or {}
        refresh_token = data.get('refresh_token', '')

        if not refresh_token:
            return jsonify({
                'error': 'Missing token',
                'message': 'Refresh token is required'
            }), 400

        # Verify refresh token
        is_valid, payload = jwt_handler.verify_token(refresh_token, 'refresh')
        if not is_valid:
            return jsonify({
                'error': 'Invalid token',
                'message': 'Refresh token is invalid or expired'
            }), 401

        # Get user (to get current tier)
        user_id = payload.get('sub')
        user = UserRepository.get_user_by_id(user_id)
        if not user:
            return jsonify({
                'error': 'User not found',
                'message': 'Associated user no longer exists'
            }), 404

        # Generate new access token
        access_token = jwt_handler.create_access_token(
            user_id=str(user.id),
            tier=user.tier,
            email=user.email
        )

        return jsonify({
            'success': True,
            'access_token': access_token
        }), 200

    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Failed to refresh token'
        }), 500


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """
    User logout endpoint (client-side token invalidation).

    Note: In this implementation, token blacklisting is not implemented.
    Clients should simply discard the tokens.

    Returns:
        JSON success message
    """
    # TODO: Implement token blacklisting in Redis if needed
    return jsonify({
        'success': True,
        'message': 'Logged out successfully'
    }), 200


def register_auth_routes(app):
    """Register authentication routes with Flask app."""
    app.register_blueprint(auth_bp)
    logger.info("Authentication routes registered")
