"""
Stripe Payment Configuration
AI Match Simulation v3.0

Manages Stripe API keys, product IDs, prices, and webhook settings.
"""

import os
from typing import Dict, Optional


class StripeConfig:
    """Stripe payment configuration and constants."""

    def __init__(self):
        """Initialize Stripe configuration from environment variables."""
        self.api_key = os.getenv('STRIPE_SECRET_KEY', '')
        self.publishable_key = os.getenv('STRIPE_PUBLISHABLE_KEY', '')
        self.webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET', '')

        # Product IDs (set in Stripe dashboard)
        self.pro_price_id = os.getenv('STRIPE_PRO_PRICE_ID', '')

        # Price amounts (in cents)
        self.prices = {
            'PRO': 1999  # $19.99/month
        }

        # URLs
        self.success_url = os.getenv('STRIPE_SUCCESS_URL', 'http://localhost:3000/subscription/success')
        self.cancel_url = os.getenv('STRIPE_CANCEL_URL', 'http://localhost:3000/subscription/cancel')
        self.customer_portal_url = os.getenv('STRIPE_PORTAL_URL', 'http://localhost:3000/account')

        # Webhook endpoint
        self.webhook_endpoint = '/api/v1/payment/webhook'

        # Subscription settings
        self.trial_period_days = int(os.getenv('STRIPE_TRIAL_DAYS', '0'))

    def validate(self) -> tuple[bool, Optional[str]]:
        """
        Validate that all required Stripe configuration is present.

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self.api_key:
            return False, "STRIPE_SECRET_KEY not set"

        if not self.webhook_secret:
            return False, "STRIPE_WEBHOOK_SECRET not set"

        if not self.pro_price_id:
            return False, "STRIPE_PRO_PRICE_ID not set"

        return True, None

    def get_price_id(self, tier: str) -> Optional[str]:
        """
        Get Stripe Price ID for a subscription tier.

        Args:
            tier: Subscription tier ('PRO')

        Returns:
            Stripe Price ID or None
        """
        if tier == 'PRO':
            return self.pro_price_id
        return None

    def get_tier_from_price_id(self, price_id: str) -> Optional[str]:
        """
        Get tier name from Stripe Price ID.

        Args:
            price_id: Stripe Price ID

        Returns:
            Tier name or None
        """
        if price_id == self.pro_price_id:
            return 'PRO'
        return None

    def get_metadata(self, tier: str) -> Dict:
        """
        Get metadata to attach to Stripe objects.

        Args:
            tier: Subscription tier

        Returns:
            Dictionary of metadata
        """
        return {
            'tier': tier,
            'product': 'AI Match Simulation',
            'version': 'v3.0'
        }


# Global configuration instance
stripe_config = StripeConfig()


def get_stripe_config() -> StripeConfig:
    """Get global Stripe configuration instance."""
    return stripe_config
