"""
Stripe Webhook Handler
AI Match Simulation v3.0

Processes Stripe webhook events for subscriptions and payments.
"""

from typing import Dict, Tuple, Optional
from datetime import datetime
import logging

from payment.stripe_handler import get_stripe_handler
from repositories.subscription_repository import SubscriptionRepository
from repositories.user_repository import UserRepository


# Configure logging
logger = logging.getLogger(__name__)


class WebhookHandler:
    """
    Handles Stripe webhook events.

    Supported events:
    - customer.subscription.created
    - customer.subscription.updated
    - customer.subscription.deleted
    - invoice.payment_succeeded
    - invoice.payment_failed
    - customer.subscription.trial_will_end
    """

    def __init__(self):
        """Initialize webhook handler."""
        self.stripe_handler = get_stripe_handler()
        self.subscription_repo = SubscriptionRepository()
        self.user_repo = UserRepository()

        # Map event types to handler methods
        self.event_handlers = {
            'customer.subscription.created': self._handle_subscription_created,
            'customer.subscription.updated': self._handle_subscription_updated,
            'customer.subscription.deleted': self._handle_subscription_deleted,
            'invoice.payment_succeeded': self._handle_payment_succeeded,
            'invoice.payment_failed': self._handle_payment_failed,
            'customer.subscription.trial_will_end': self._handle_trial_ending,
        }

    # ============================================================================
    # PUBLIC METHODS
    # ============================================================================

    def process_webhook(self, payload: bytes, signature: str) -> Tuple[bool, Optional[str]]:
        """
        Process incoming webhook event.

        Args:
            payload: Raw webhook payload
            signature: Stripe signature header

        Returns:
            Tuple of (success, error_message)
        """
        # Verify webhook signature
        success, event, error = self.stripe_handler.verify_webhook_signature(payload, signature)
        if not success:
            logger.error(f"Webhook signature verification failed: {error}")
            return False, error

        event_type = event['type']
        event_data = event['data']['object']

        logger.info(f"Processing webhook event: {event_type} (ID: {event['id']})")

        # Find appropriate handler
        handler = self.event_handlers.get(event_type)
        if handler:
            try:
                handler(event_data)
                logger.info(f"Successfully processed {event_type}")
                return True, None
            except Exception as e:
                error_msg = f"Error processing {event_type}: {str(e)}"
                logger.error(error_msg)
                return False, error_msg
        else:
            logger.warning(f"No handler for event type: {event_type}")
            return True, None  # Return success for unhandled events

    # ============================================================================
    # EVENT HANDLERS
    # ============================================================================

    def _handle_subscription_created(self, subscription: Dict) -> None:
        """
        Handle subscription.created event.

        Args:
            subscription: Stripe subscription object
        """
        logger.info(f"Handling subscription created: {subscription['id']}")

        # Get user by customer ID
        customer_id = subscription['customer']
        user = self.user_repo.get_by_stripe_customer_id(customer_id)
        if not user:
            logger.error(f"User not found for Stripe customer {customer_id}")
            return

        # Extract tier from metadata or price
        tier = subscription.get('metadata', {}).get('tier', 'PRO')

        # Create subscription record
        self.subscription_repo.create(
            user_id=str(user.id),
            stripe_subscription_id=subscription['id'],
            tier=tier,
            status=subscription['status'],
            current_period_start=datetime.fromtimestamp(subscription['current_period_start']),
            current_period_end=datetime.fromtimestamp(subscription['current_period_end']),
            trial_start=datetime.fromtimestamp(subscription['trial_start']) if subscription.get('trial_start') else None,
            trial_end=datetime.fromtimestamp(subscription['trial_end']) if subscription.get('trial_end') else None,
            metadata=subscription.get('metadata', {})
        )

        # Update user tier (triggers will handle this, but we can do it explicitly too)
        self.user_repo.update_tier(str(user.id), tier)

        logger.info(f"Created subscription record for user {user.id}")

        # TODO: Send welcome email

    def _handle_subscription_updated(self, subscription: Dict) -> None:
        """
        Handle subscription.updated event.

        Args:
            subscription: Stripe subscription object
        """
        logger.info(f"Handling subscription updated: {subscription['id']}")

        # Get existing subscription
        sub = self.subscription_repo.get_by_stripe_id(subscription['id'])
        if not sub:
            logger.warning(f"Subscription {subscription['id']} not found in database")
            # Try to create it
            self._handle_subscription_created(subscription)
            return

        # Update subscription from Stripe data
        self.subscription_repo.update_from_stripe(str(sub.id), subscription)

        # Update user tier based on subscription status
        if subscription['status'] in ('active', 'trialing'):
            tier = subscription.get('metadata', {}).get('tier', 'PRO')
            self.user_repo.update_tier(str(sub.user_id), tier)
        elif subscription['status'] in ('canceled', 'incomplete_expired', 'unpaid'):
            # Downgrade to BASIC
            self.user_repo.update_tier(str(sub.user_id), 'BASIC')

        logger.info(f"Updated subscription {subscription['id']}")

        # TODO: Send update notification if needed

    def _handle_subscription_deleted(self, subscription: Dict) -> None:
        """
        Handle subscription.deleted event.

        Args:
            subscription: Stripe subscription object
        """
        logger.info(f"Handling subscription deleted: {subscription['id']}")

        # Get existing subscription
        sub = self.subscription_repo.get_by_stripe_id(subscription['id'])
        if not sub:
            logger.warning(f"Subscription {subscription['id']} not found in database")
            return

        # Update subscription status
        self.subscription_repo.update_status(
            subscription_id=str(sub.id),
            status='canceled',
            canceled_at=datetime.utcnow(),
            cancellation_reason='Canceled in Stripe'
        )

        # Downgrade user to BASIC tier
        self.user_repo.update_tier(str(sub.user_id), 'BASIC')

        logger.info(f"Canceled subscription {subscription['id']}, downgraded user to BASIC")

        # TODO: Send cancellation confirmation email

    def _handle_payment_succeeded(self, invoice: Dict) -> None:
        """
        Handle invoice.payment_succeeded event.

        Args:
            invoice: Stripe invoice object
        """
        logger.info(f"Handling payment succeeded: {invoice['id']}")

        subscription_id = invoice.get('subscription')
        if not subscription_id:
            logger.warning("Payment succeeded but no subscription ID found")
            return

        # Get subscription
        sub = self.subscription_repo.get_by_stripe_id(subscription_id)
        if not sub:
            logger.warning(f"Subscription {subscription_id} not found")
            return

        # Ensure user has correct tier
        if sub.status in ('active', 'trialing'):
            self.user_repo.update_tier(str(sub.user_id), sub.tier)

        logger.info(f"Payment succeeded for subscription {subscription_id}")

        # TODO: Send payment receipt email

    def _handle_payment_failed(self, invoice: Dict) -> None:
        """
        Handle invoice.payment_failed event.

        Args:
            invoice: Stripe invoice object
        """
        logger.info(f"Handling payment failed: {invoice['id']}")

        subscription_id = invoice.get('subscription')
        if not subscription_id:
            logger.warning("Payment failed but no subscription ID found")
            return

        # Get subscription
        sub = self.subscription_repo.get_by_stripe_id(subscription_id)
        if not sub:
            logger.warning(f"Subscription {subscription_id} not found")
            return

        # Update subscription status to past_due
        self.subscription_repo.update_status(
            subscription_id=str(sub.id),
            status='past_due'
        )

        logger.warning(f"Payment failed for subscription {subscription_id}")

        # TODO: Send payment failed notification email

    def _handle_trial_ending(self, subscription: Dict) -> None:
        """
        Handle customer.subscription.trial_will_end event.

        Args:
            subscription: Stripe subscription object
        """
        logger.info(f"Handling trial ending: {subscription['id']}")

        # Get subscription
        sub = self.subscription_repo.get_by_stripe_id(subscription['id'])
        if not sub:
            logger.warning(f"Subscription {subscription['id']} not found")
            return

        logger.info(f"Trial ending for subscription {subscription['id']}")

        # TODO: Send trial ending reminder email

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================

    def get_supported_events(self) -> list:
        """
        Get list of supported webhook event types.

        Returns:
            List of event type strings
        """
        return list(self.event_handlers.keys())


# Global handler instance
_webhook_handler = None


def get_webhook_handler() -> WebhookHandler:
    """Get global webhook handler instance (singleton)."""
    global _webhook_handler
    if _webhook_handler is None:
        _webhook_handler = WebhookHandler()
    return _webhook_handler
