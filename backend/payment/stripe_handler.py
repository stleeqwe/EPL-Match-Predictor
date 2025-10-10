"""
Stripe Payment Handler
AI Match Simulation v3.0

Handles all Stripe payment operations including customers, subscriptions, and checkout.
"""

import stripe
from typing import Dict, Optional, Tuple
import logging
from datetime import datetime

from config.stripe_config import get_stripe_config


# Configure logging
logger = logging.getLogger(__name__)


class StripeError(Exception):
    """Base exception for Stripe-related errors."""
    pass


class StripeCustomerError(StripeError):
    """Error related to customer operations."""
    pass


class StripeSubscriptionError(StripeError):
    """Error related to subscription operations."""
    pass


class StripeCheckoutError(StripeError):
    """Error related to checkout operations."""
    pass


class StripeHandler:
    """
    Handles all Stripe payment operations.

    Features:
    - Customer creation and management
    - Checkout session creation
    - Customer portal sessions
    - Subscription management
    - Error handling and logging
    """

    def __init__(self):
        """Initialize Stripe handler with configuration."""
        self.config = get_stripe_config()
        stripe.api_key = self.config.api_key

        # Validate configuration
        is_valid, error = self.config.validate()
        if not is_valid:
            logger.error(f"Stripe configuration invalid: {error}")
            raise StripeError(f"Configuration error: {error}")

    # ============================================================================
    # CUSTOMER OPERATIONS
    # ============================================================================

    def create_customer(self, email: str, user_id: str,
                       display_name: Optional[str] = None,
                       metadata: Optional[Dict] = None) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Create a Stripe customer.

        Args:
            email: Customer email address
            user_id: Internal user ID
            display_name: Optional display name
            metadata: Optional additional metadata

        Returns:
            Tuple of (success, customer_id, error_message)
        """
        try:
            customer_metadata = {
                'user_id': user_id,
                'platform': 'ai_match_simulation_v3'
            }
            if metadata:
                customer_metadata.update(metadata)

            customer = stripe.Customer.create(
                email=email,
                name=display_name or email,
                metadata=customer_metadata,
                description=f"AI Match Simulation user: {email}"
            )

            logger.info(f"Created Stripe customer {customer.id} for user {user_id}")
            return True, customer.id, None

        except stripe.error.StripeError as e:
            error_msg = f"Failed to create customer: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
        except Exception as e:
            error_msg = f"Unexpected error creating customer: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg

    def get_customer(self, customer_id: str) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Retrieve a Stripe customer.

        Args:
            customer_id: Stripe customer ID

        Returns:
            Tuple of (success, customer_data, error_message)
        """
        try:
            customer = stripe.Customer.retrieve(customer_id)

            customer_data = {
                'id': customer.id,
                'email': customer.email,
                'name': customer.name,
                'created': datetime.fromtimestamp(customer.created),
                'metadata': customer.metadata
            }

            return True, customer_data, None

        except stripe.error.StripeError as e:
            error_msg = f"Failed to retrieve customer: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
        except Exception as e:
            error_msg = f"Unexpected error retrieving customer: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg

    def update_customer(self, customer_id: str, **updates) -> Tuple[bool, Optional[str]]:
        """
        Update a Stripe customer.

        Args:
            customer_id: Stripe customer ID
            **updates: Fields to update (email, name, metadata, etc.)

        Returns:
            Tuple of (success, error_message)
        """
        try:
            stripe.Customer.modify(customer_id, **updates)
            logger.info(f"Updated Stripe customer {customer_id}")
            return True, None

        except stripe.error.StripeError as e:
            error_msg = f"Failed to update customer: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Unexpected error updating customer: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    # ============================================================================
    # CHECKOUT OPERATIONS
    # ============================================================================

    def create_checkout_session(self, customer_id: str, tier: str, user_id: str,
                                success_url: Optional[str] = None,
                                cancel_url: Optional[str] = None) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Create a Stripe Checkout session for subscription.

        Args:
            customer_id: Stripe customer ID
            tier: Subscription tier ('PRO')
            user_id: Internal user ID
            success_url: Optional custom success URL
            cancel_url: Optional custom cancel URL

        Returns:
            Tuple of (success, session_url, error_message)
        """
        try:
            price_id = self.config.get_price_id(tier)
            if not price_id:
                return False, None, f"Invalid tier: {tier}"

            metadata = self.config.get_metadata(tier)
            metadata['user_id'] = user_id

            session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=['card'],
                line_items=[{
                    'price': price_id,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=success_url or self.config.success_url,
                cancel_url=cancel_url or self.config.cancel_url,
                metadata=metadata,
                subscription_data={
                    'metadata': metadata,
                    'trial_period_days': self.config.trial_period_days if self.config.trial_period_days > 0 else None
                },
                allow_promotion_codes=True,
                billing_address_collection='auto'
            )

            logger.info(f"Created checkout session {session.id} for customer {customer_id}")
            return True, session.url, None

        except stripe.error.StripeError as e:
            error_msg = f"Failed to create checkout session: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
        except Exception as e:
            error_msg = f"Unexpected error creating checkout session: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg

    # ============================================================================
    # CUSTOMER PORTAL
    # ============================================================================

    def create_portal_session(self, customer_id: str,
                             return_url: Optional[str] = None) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Create a Stripe Customer Portal session.

        Allows customers to manage their subscription, payment methods, and billing.

        Args:
            customer_id: Stripe customer ID
            return_url: URL to return to after portal session

        Returns:
            Tuple of (success, portal_url, error_message)
        """
        try:
            session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=return_url or self.config.customer_portal_url
            )

            logger.info(f"Created portal session for customer {customer_id}")
            return True, session.url, None

        except stripe.error.StripeError as e:
            error_msg = f"Failed to create portal session: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
        except Exception as e:
            error_msg = f"Unexpected error creating portal session: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg

    # ============================================================================
    # SUBSCRIPTION OPERATIONS
    # ============================================================================

    def get_subscription(self, subscription_id: str) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Retrieve a subscription.

        Args:
            subscription_id: Stripe subscription ID

        Returns:
            Tuple of (success, subscription_data, error_message)
        """
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)

            subscription_data = {
                'id': subscription.id,
                'customer': subscription.customer,
                'status': subscription.status,
                'current_period_start': datetime.fromtimestamp(subscription.current_period_start),
                'current_period_end': datetime.fromtimestamp(subscription.current_period_end),
                'cancel_at_period_end': subscription.cancel_at_period_end,
                'canceled_at': datetime.fromtimestamp(subscription.canceled_at) if subscription.canceled_at else None,
                'trial_end': datetime.fromtimestamp(subscription.trial_end) if subscription.trial_end else None,
                'metadata': subscription.metadata
            }

            return True, subscription_data, None

        except stripe.error.StripeError as e:
            error_msg = f"Failed to retrieve subscription: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
        except Exception as e:
            error_msg = f"Unexpected error retrieving subscription: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg

    def cancel_subscription(self, subscription_id: str,
                           immediate: bool = False) -> Tuple[bool, Optional[str]]:
        """
        Cancel a subscription.

        Args:
            subscription_id: Stripe subscription ID
            immediate: If True, cancel immediately. If False, cancel at period end.

        Returns:
            Tuple of (success, error_message)
        """
        try:
            if immediate:
                stripe.Subscription.delete(subscription_id)
                logger.info(f"Immediately canceled subscription {subscription_id}")
            else:
                stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True
                )
                logger.info(f"Scheduled subscription {subscription_id} for cancellation")

            return True, None

        except stripe.error.StripeError as e:
            error_msg = f"Failed to cancel subscription: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Unexpected error canceling subscription: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    def reactivate_subscription(self, subscription_id: str) -> Tuple[bool, Optional[str]]:
        """
        Reactivate a subscription scheduled for cancellation.

        Args:
            subscription_id: Stripe subscription ID

        Returns:
            Tuple of (success, error_message)
        """
        try:
            stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=False
            )
            logger.info(f"Reactivated subscription {subscription_id}")
            return True, None

        except stripe.error.StripeError as e:
            error_msg = f"Failed to reactivate subscription: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Unexpected error reactivating subscription: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================

    def verify_webhook_signature(self, payload: bytes, signature: str) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Verify Stripe webhook signature.

        Args:
            payload: Raw request body
            signature: Stripe signature header

        Returns:
            Tuple of (success, event_data, error_message)
        """
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, self.config.webhook_secret
            )
            return True, event, None

        except ValueError as e:
            error_msg = f"Invalid webhook payload: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
        except stripe.error.SignatureVerificationError as e:
            error_msg = f"Invalid webhook signature: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
        except Exception as e:
            error_msg = f"Unexpected error verifying webhook: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg


# Global handler instance
_stripe_handler = None


def get_stripe_handler() -> StripeHandler:
    """Get global Stripe handler instance (singleton)."""
    global _stripe_handler
    if _stripe_handler is None:
        _stripe_handler = StripeHandler()
    return _stripe_handler
