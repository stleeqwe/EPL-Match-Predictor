"""
Payment System Tests
AI Match Simulation v3.0

Unit tests for Stripe payment integration.
"""

import os
import sys
import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Set test environment variables before importing modules
os.environ['STRIPE_SECRET_KEY'] = 'sk_test_mock_key_12345'
os.environ['STRIPE_WEBHOOK_SECRET'] = 'whsec_test_mock_secret_12345'
os.environ['STRIPE_PRO_PRICE_ID'] = 'price_test_pro_12345'
os.environ['EMAIL_ENABLED'] = 'false'

from config.stripe_config import StripeConfig
from payment.stripe_handler import StripeHandler


class TestStripeConfig(unittest.TestCase):
    """Test Stripe configuration."""

    def test_config_initialization(self):
        """Test that config initializes from environment."""
        config = StripeConfig()
        self.assertEqual(config.api_key, 'sk_test_mock_key_12345')
        self.assertEqual(config.webhook_secret, 'whsec_test_mock_secret_12345')
        self.assertEqual(config.pro_price_id, 'price_test_pro_12345')

    def test_config_validation(self):
        """Test config validation."""
        config = StripeConfig()
        is_valid, error = config.validate()
        self.assertTrue(is_valid)
        self.assertIsNone(error)

    def test_get_price_id(self):
        """Test getting price ID for tier."""
        config = StripeConfig()
        self.assertEqual(config.get_price_id('PRO'), 'price_test_pro_12345')
        self.assertIsNone(config.get_price_id('INVALID'))

    def test_get_tier_from_price_id(self):
        """Test reverse lookup of tier from price ID."""
        config = StripeConfig()
        self.assertEqual(config.get_tier_from_price_id('price_test_pro_12345'), 'PRO')
        self.assertIsNone(config.get_tier_from_price_id('invalid_price'))

    def test_get_metadata(self):
        """Test metadata generation."""
        config = StripeConfig()
        metadata = config.get_metadata('PRO')
        self.assertEqual(metadata['tier'], 'PRO')
        self.assertEqual(metadata['product'], 'AI Match Simulation')
        self.assertEqual(metadata['version'], 'v3.0')


class TestStripeHandler(unittest.TestCase):
    """Test Stripe handler operations."""

    def setUp(self):
        """Set up test fixtures."""
        self.handler = StripeHandler()

    @patch('stripe.Customer.create')
    def test_create_customer_success(self, mock_create):
        """Test successful customer creation."""
        # Mock Stripe response
        mock_customer = Mock()
        mock_customer.id = 'cus_test_12345'
        mock_create.return_value = mock_customer

        success, customer_id, error = self.handler.create_customer(
            email='test@example.com',
            user_id='user-123',
            display_name='Test User'
        )

        self.assertTrue(success)
        self.assertEqual(customer_id, 'cus_test_12345')
        self.assertIsNone(error)
        mock_create.assert_called_once()

    @patch('stripe.Customer.create')
    def test_create_customer_failure(self, mock_create):
        """Test customer creation failure."""
        # Mock Stripe error
        import stripe
        mock_create.side_effect = stripe.error.StripeError('Test error')

        success, customer_id, error = self.handler.create_customer(
            email='test@example.com',
            user_id='user-123'
        )

        self.assertFalse(success)
        self.assertIsNone(customer_id)
        self.assertIsNotNone(error)

    @patch('stripe.Customer.retrieve')
    def test_get_customer_success(self, mock_retrieve):
        """Test successful customer retrieval."""
        # Mock Stripe response
        mock_customer = Mock()
        mock_customer.id = 'cus_test_12345'
        mock_customer.email = 'test@example.com'
        mock_customer.name = 'Test User'
        mock_customer.created = int(datetime.now().timestamp())
        mock_customer.metadata = {'user_id': 'user-123'}
        mock_retrieve.return_value = mock_customer

        success, customer_data, error = self.handler.get_customer('cus_test_12345')

        self.assertTrue(success)
        self.assertIsNotNone(customer_data)
        self.assertEqual(customer_data['email'], 'test@example.com')
        self.assertIsNone(error)

    @patch('stripe.checkout.Session.create')
    def test_create_checkout_session_success(self, mock_create):
        """Test successful checkout session creation."""
        # Mock Stripe response
        mock_session = Mock()
        mock_session.id = 'cs_test_12345'
        mock_session.url = 'https://checkout.stripe.com/test'
        mock_create.return_value = mock_session

        success, session_url, error = self.handler.create_checkout_session(
            customer_id='cus_test_12345',
            tier='PRO',
            user_id='user-123'
        )

        self.assertTrue(success)
        self.assertEqual(session_url, 'https://checkout.stripe.com/test')
        self.assertIsNone(error)

    @patch('stripe.checkout.Session.create')
    def test_create_checkout_session_invalid_tier(self, mock_create):
        """Test checkout session with invalid tier."""
        success, session_url, error = self.handler.create_checkout_session(
            customer_id='cus_test_12345',
            tier='INVALID',
            user_id='user-123'
        )

        self.assertFalse(success)
        self.assertIsNone(session_url)
        self.assertIn('Invalid tier', error)
        mock_create.assert_not_called()

    @patch('stripe.billing_portal.Session.create')
    def test_create_portal_session_success(self, mock_create):
        """Test successful portal session creation."""
        # Mock Stripe response
        mock_session = Mock()
        mock_session.url = 'https://billing.stripe.com/portal/test'
        mock_create.return_value = mock_session

        success, portal_url, error = self.handler.create_portal_session(
            customer_id='cus_test_12345'
        )

        self.assertTrue(success)
        self.assertEqual(portal_url, 'https://billing.stripe.com/portal/test')
        self.assertIsNone(error)

    @patch('stripe.Subscription.retrieve')
    def test_get_subscription_success(self, mock_retrieve):
        """Test successful subscription retrieval."""
        # Mock Stripe response
        now = int(datetime.now().timestamp())
        mock_sub = Mock()
        mock_sub.id = 'sub_test_12345'
        mock_sub.customer = 'cus_test_12345'
        mock_sub.status = 'active'
        mock_sub.current_period_start = now
        mock_sub.current_period_end = now + 2592000  # 30 days
        mock_sub.cancel_at_period_end = False
        mock_sub.canceled_at = None
        mock_sub.trial_end = None
        mock_sub.metadata = {'tier': 'PRO'}
        mock_retrieve.return_value = mock_sub

        success, sub_data, error = self.handler.get_subscription('sub_test_12345')

        self.assertTrue(success)
        self.assertIsNotNone(sub_data)
        self.assertEqual(sub_data['status'], 'active')
        self.assertIsNone(error)

    @patch('stripe.Subscription.modify')
    def test_cancel_subscription_at_period_end(self, mock_modify):
        """Test canceling subscription at period end."""
        success, error = self.handler.cancel_subscription(
            subscription_id='sub_test_12345',
            immediate=False
        )

        self.assertTrue(success)
        self.assertIsNone(error)
        mock_modify.assert_called_once_with(
            'sub_test_12345',
            cancel_at_period_end=True
        )

    @patch('stripe.Subscription.delete')
    def test_cancel_subscription_immediate(self, mock_delete):
        """Test immediate subscription cancellation."""
        success, error = self.handler.cancel_subscription(
            subscription_id='sub_test_12345',
            immediate=True
        )

        self.assertTrue(success)
        self.assertIsNone(error)
        mock_delete.assert_called_once_with('sub_test_12345')

    @patch('stripe.Subscription.modify')
    def test_reactivate_subscription_success(self, mock_modify):
        """Test successful subscription reactivation."""
        success, error = self.handler.reactivate_subscription('sub_test_12345')

        self.assertTrue(success)
        self.assertIsNone(error)
        mock_modify.assert_called_once_with(
            'sub_test_12345',
            cancel_at_period_end=False
        )

    @patch('stripe.Webhook.construct_event')
    def test_verify_webhook_signature_success(self, mock_construct):
        """Test successful webhook signature verification."""
        # Mock Stripe webhook event
        mock_event = {
            'id': 'evt_test_12345',
            'type': 'customer.subscription.created',
            'data': {'object': {'id': 'sub_test_12345'}}
        }
        mock_construct.return_value = mock_event

        payload = b'{"test": "data"}'
        signature = 'test_signature'

        success, event, error = self.handler.verify_webhook_signature(payload, signature)

        self.assertTrue(success)
        self.assertIsNotNone(event)
        self.assertEqual(event['type'], 'customer.subscription.created')
        self.assertIsNone(error)

    @patch('stripe.Webhook.construct_event')
    def test_verify_webhook_signature_invalid(self, mock_construct):
        """Test webhook signature verification failure."""
        import stripe
        mock_construct.side_effect = stripe.error.SignatureVerificationError(
            'Invalid signature', 'sig_header'
        )

        payload = b'{"test": "data"}'
        signature = 'invalid_signature'

        success, event, error = self.handler.verify_webhook_signature(payload, signature)

        self.assertFalse(success)
        self.assertIsNone(event)
        self.assertIn('Invalid webhook signature', error)


class TestEmailService(unittest.TestCase):
    """Test email service."""

    def setUp(self):
        """Set up test fixtures."""
        from services.email_service import EmailService
        self.service = EmailService()

    def test_email_disabled_by_default(self):
        """Test that email is disabled in test environment."""
        self.assertFalse(self.service.config.enabled)

    def test_send_verification_email_disabled(self):
        """Test sending verification email when disabled."""
        # Should return True but not actually send
        result = self.service.send_verification_email(
            to_email='test@example.com',
            verification_token='test_token_12345'
        )
        self.assertTrue(result)

    def test_send_welcome_email_disabled(self):
        """Test sending welcome email when disabled."""
        result = self.service.send_welcome_email(
            to_email='test@example.com',
            tier='PRO',
            display_name='Test User'
        )
        self.assertTrue(result)


def run_tests():
    """Run all payment system tests."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestStripeConfig))
    suite.addTests(loader.loadTestsFromTestCase(TestStripeHandler))
    suite.addTests(loader.loadTestsFromTestCase(TestEmailService))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "=" * 70)
    print("PAYMENT SYSTEM TEST SUMMARY")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("=" * 70)

    # Return exit code
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(run_tests())
