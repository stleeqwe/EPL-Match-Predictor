"""
Payment API Routes
AI Match Simulation v3.0

Flask routes for Stripe payment and subscription management.
"""

from flask import Blueprint, request, jsonify, g
from typing import Dict
import logging

from payment.stripe_handler import get_stripe_handler
from payment.webhook_handler import get_webhook_handler
from repositories.user_repository import UserRepository
from repositories.subscription_repository import SubscriptionRepository
from middleware.auth_middleware import require_auth


# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
payment_bp = Blueprint('payment', __name__, url_prefix='/api/v1/payment')

# Initialize handlers
stripe_handler = get_stripe_handler()
webhook_handler = get_webhook_handler()
user_repo = UserRepository()
subscription_repo = SubscriptionRepository()


# ============================================================================
# SUBSCRIPTION ENDPOINTS
# ============================================================================

@payment_bp.route('/create-checkout-session', methods=['POST'])
@require_auth
def create_checkout_session():
    """
    Create a Stripe Checkout session for PRO subscription.

    Required in request body:
    - tier: 'PRO'

    Optional:
    - success_url: Custom success URL
    - cancel_url: Custom cancel URL

    Returns:
        JSON with checkout session URL
    """
    try:
        data = request.get_json() or {}
        tier = data.get('tier', 'PRO')

        # Validate tier
        if tier not in ['PRO']:
            return jsonify({
                'error': 'Invalid tier',
                'message': 'Only PRO tier is available'
            }), 400

        # Get user
        user = user_repo.get_by_id(g.user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Check if user already has active subscription
        active_sub = subscription_repo.get_active_by_user(str(user.id))
        if active_sub:
            return jsonify({
                'error': 'Already subscribed',
                'message': 'You already have an active subscription',
                'subscription': active_sub.to_dict()
            }), 400

        # Create or get Stripe customer
        if not user.stripe_customer_id:
            success, customer_id, error = stripe_handler.create_customer(
                email=user.email,
                user_id=str(user.id),
                display_name=user.display_name
            )
            if not success:
                return jsonify({
                    'error': 'Failed to create customer',
                    'message': error
                }), 500

            # Update user with customer ID
            user_repo.update_stripe_customer_id(str(user.id), customer_id)
            user.stripe_customer_id = customer_id

        # Create checkout session
        success, session_url, error = stripe_handler.create_checkout_session(
            customer_id=user.stripe_customer_id,
            tier=tier,
            user_id=str(user.id),
            success_url=data.get('success_url'),
            cancel_url=data.get('cancel_url')
        )

        if not success:
            return jsonify({
                'error': 'Failed to create checkout session',
                'message': error
            }), 500

        logger.info(f"Created checkout session for user {user.id}")
        return jsonify({
            'success': True,
            'url': session_url
        }), 200

    except Exception as e:
        logger.error(f"Error creating checkout session: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500


@payment_bp.route('/create-portal-session', methods=['POST'])
@require_auth
def create_portal_session():
    """
    Create a Stripe Customer Portal session.

    Allows users to manage their subscription, payment methods, and billing.

    Optional in request body:
    - return_url: URL to return to after portal session

    Returns:
        JSON with portal session URL
    """
    try:
        data = request.get_json() or {}

        # Get user
        user = user_repo.get_by_id(g.user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Check if user has Stripe customer ID
        if not user.stripe_customer_id:
            return jsonify({
                'error': 'No subscription',
                'message': 'You do not have a subscription to manage'
            }), 400

        # Create portal session
        success, portal_url, error = stripe_handler.create_portal_session(
            customer_id=user.stripe_customer_id,
            return_url=data.get('return_url')
        )

        if not success:
            return jsonify({
                'error': 'Failed to create portal session',
                'message': error
            }), 500

        logger.info(f"Created portal session for user {user.id}")
        return jsonify({
            'success': True,
            'url': portal_url
        }), 200

    except Exception as e:
        logger.error(f"Error creating portal session: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500


@payment_bp.route('/subscription', methods=['GET'])
@require_auth
def get_subscription():
    """
    Get current subscription status.

    Returns:
        JSON with subscription details
    """
    try:
        # Get active subscription
        subscription = subscription_repo.get_active_by_user(g.user_id)

        if not subscription:
            return jsonify({
                'success': True,
                'subscription': None,
                'tier': 'BASIC'
            }), 200

        return jsonify({
            'success': True,
            'subscription': subscription.to_dict(),
            'tier': subscription.tier
        }), 200

    except Exception as e:
        logger.error(f"Error retrieving subscription: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500


@payment_bp.route('/subscription/history', methods=['GET'])
@require_auth
def get_subscription_history():
    """
    Get subscription history for the current user.

    Returns:
        JSON with list of all subscriptions
    """
    try:
        subscriptions = subscription_repo.get_all_by_user(g.user_id)

        return jsonify({
            'success': True,
            'subscriptions': [sub.to_dict() for sub in subscriptions]
        }), 200

    except Exception as e:
        logger.error(f"Error retrieving subscription history: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500


# ============================================================================
# WEBHOOK ENDPOINT
# ============================================================================

@payment_bp.route('/webhook', methods=['POST'])
def stripe_webhook():
    """
    Handle Stripe webhook events.

    Processes events like subscription created/updated/canceled, payments, etc.

    Returns:
        JSON success response
    """
    try:
        # Get raw payload and signature
        payload = request.get_data()
        signature = request.headers.get('Stripe-Signature')

        if not signature:
            logger.error("Missing Stripe signature")
            return jsonify({'error': 'Missing signature'}), 400

        # Process webhook
        success, error = webhook_handler.process_webhook(payload, signature)

        if not success:
            logger.error(f"Webhook processing failed: {error}")
            return jsonify({'error': error}), 400

        return jsonify({'success': True}), 200

    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500


# ============================================================================
# UTILITY ENDPOINTS
# ============================================================================

@payment_bp.route('/config', methods=['GET'])
def get_payment_config():
    """
    Get public payment configuration.

    Returns:
        JSON with pricing and available tiers
    """
    return jsonify({
        'success': True,
        'tiers': [
            {
                'name': 'BASIC',
                'price': 0,
                'features': [
                    '5 simulations per hour',
                    'Claude Sonnet 3.5 AI',
                    'Basic analytics'
                ]
            },
            {
                'name': 'PRO',
                'price': 19.99,
                'features': [
                    'Unlimited simulations',
                    'Claude Sonnet 4.5 AI',
                    'Sharp bookmaker insights',
                    'Advanced analytics',
                    'Priority support'
                ]
            }
        ]
    }), 200


@payment_bp.route('/supported-events', methods=['GET'])
def get_supported_events():
    """
    Get list of supported webhook events (for debugging).

    Returns:
        JSON with supported event types
    """
    return jsonify({
        'success': True,
        'events': webhook_handler.get_supported_events()
    }), 200


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@payment_bp.errorhandler(400)
def bad_request(e):
    """Handle 400 errors."""
    return jsonify({'error': 'Bad request', 'message': str(e)}), 400


@payment_bp.errorhandler(404)
def not_found(e):
    """Handle 404 errors."""
    return jsonify({'error': 'Not found', 'message': str(e)}), 404


@payment_bp.errorhandler(500)
def internal_error(e):
    """Handle 500 errors."""
    logger.error(f"Internal error: {str(e)}")
    return jsonify({'error': 'Internal server error'}), 500


# Export blueprint
def register_payment_routes(app):
    """
    Register payment routes with Flask app.

    Args:
        app: Flask application instance
    """
    app.register_blueprint(payment_bp)
    logger.info("Payment routes registered")
