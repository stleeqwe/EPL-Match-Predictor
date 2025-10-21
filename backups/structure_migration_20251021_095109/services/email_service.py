"""
Email Service
AI Match Simulation v3.0

Handles email notifications for subscriptions, payments, and account events.
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, List
import logging
from datetime import datetime


# Configure logging
logger = logging.getLogger(__name__)


class EmailConfig:
    """Email service configuration."""

    def __init__(self):
        """Initialize from environment variables."""
        self.smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_user = os.getenv('SMTP_USER', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.smtp_use_tls = os.getenv('SMTP_USE_TLS', 'true').lower() == 'true'

        self.from_email = os.getenv('FROM_EMAIL', 'noreply@aimatchsim.com')
        self.from_name = os.getenv('FROM_NAME', 'AI Match Simulation')
        self.support_email = os.getenv('SUPPORT_EMAIL', 'support@aimatchsim.com')

        # Feature flag
        self.enabled = os.getenv('EMAIL_ENABLED', 'false').lower() == 'true'

    def validate(self) -> tuple[bool, Optional[str]]:
        """Validate email configuration."""
        if not self.enabled:
            return True, "Email service disabled"

        if not self.smtp_user or not self.smtp_password:
            return False, "SMTP credentials not configured"

        return True, None


class EmailService:
    """
    Email notification service.

    Handles sending transactional emails for:
    - Account verification
    - Password reset
    - Subscription events
    - Payment notifications
    """

    def __init__(self):
        """Initialize email service."""
        self.config = EmailConfig()
        self.base_url = os.getenv('APP_BASE_URL', 'http://localhost:3000')

    # ============================================================================
    # PUBLIC METHODS
    # ============================================================================

    def send_verification_email(self, to_email: str, verification_token: str,
                               display_name: Optional[str] = None) -> bool:
        """
        Send account verification email.

        Args:
            to_email: Recipient email address
            verification_token: Verification token
            display_name: User's display name

        Returns:
            True if sent successfully, False otherwise
        """
        verification_url = f"{self.base_url}/verify-email?token={verification_token}"

        subject = "Verify your AI Match Simulation account"
        html_body = self._render_verification_email(verification_url, display_name)

        return self._send_email(to_email, subject, html_body)

    def send_password_reset_email(self, to_email: str, reset_token: str,
                                  display_name: Optional[str] = None) -> bool:
        """
        Send password reset email.

        Args:
            to_email: Recipient email address
            reset_token: Password reset token
            display_name: User's display name

        Returns:
            True if sent successfully, False otherwise
        """
        reset_url = f"{self.base_url}/reset-password?token={reset_token}"

        subject = "Reset your AI Match Simulation password"
        html_body = self._render_password_reset_email(reset_url, display_name)

        return self._send_email(to_email, subject, html_body)

    def send_welcome_email(self, to_email: str, tier: str,
                          display_name: Optional[str] = None) -> bool:
        """
        Send welcome email for new subscription.

        Args:
            to_email: Recipient email address
            tier: Subscription tier
            display_name: User's display name

        Returns:
            True if sent successfully, False otherwise
        """
        subject = f"Welcome to AI Match Simulation {tier}!"
        html_body = self._render_welcome_email(tier, display_name)

        return self._send_email(to_email, subject, html_body)

    def send_payment_receipt(self, to_email: str, amount: float, tier: str,
                           period_end: datetime,
                           display_name: Optional[str] = None) -> bool:
        """
        Send payment receipt email.

        Args:
            to_email: Recipient email address
            amount: Payment amount
            tier: Subscription tier
            period_end: Subscription period end date
            display_name: User's display name

        Returns:
            True if sent successfully, False otherwise
        """
        subject = "Your AI Match Simulation payment receipt"
        html_body = self._render_payment_receipt(amount, tier, period_end, display_name)

        return self._send_email(to_email, subject, html_body)

    def send_trial_ending_email(self, to_email: str, trial_end: datetime,
                               display_name: Optional[str] = None) -> bool:
        """
        Send trial ending reminder email.

        Args:
            to_email: Recipient email address
            trial_end: Trial end date
            display_name: User's display name

        Returns:
            True if sent successfully, False otherwise
        """
        subject = "Your AI Match Simulation trial is ending soon"
        html_body = self._render_trial_ending_email(trial_end, display_name)

        return self._send_email(to_email, subject, html_body)

    def send_subscription_canceled_email(self, to_email: str, period_end: datetime,
                                        display_name: Optional[str] = None) -> bool:
        """
        Send subscription cancellation confirmation.

        Args:
            to_email: Recipient email address
            period_end: Access end date
            display_name: User's display name

        Returns:
            True if sent successfully, False otherwise
        """
        subject = "Your AI Match Simulation subscription has been canceled"
        html_body = self._render_subscription_canceled_email(period_end, display_name)

        return self._send_email(to_email, subject, html_body)

    def send_payment_failed_email(self, to_email: str,
                                 display_name: Optional[str] = None) -> bool:
        """
        Send payment failed notification.

        Args:
            to_email: Recipient email address
            display_name: User's display name

        Returns:
            True if sent successfully, False otherwise
        """
        subject = "Payment failed for your AI Match Simulation subscription"
        html_body = self._render_payment_failed_email(display_name)

        return self._send_email(to_email, subject, html_body)

    # ============================================================================
    # CORE EMAIL SENDING
    # ============================================================================

    def _send_email(self, to_email: str, subject: str, html_body: str,
                   text_body: Optional[str] = None) -> bool:
        """
        Send an email.

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_body: HTML email body
            text_body: Optional plain text fallback

        Returns:
            True if sent successfully, False otherwise
        """
        if not self.config.enabled:
            logger.info(f"Email service disabled. Would send to {to_email}: {subject}")
            return True

        is_valid, error = self.config.validate()
        if not is_valid:
            logger.error(f"Email configuration invalid: {error}")
            return False

        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.config.from_name} <{self.config.from_email}>"
            msg['To'] = to_email

            # Add plain text version (auto-generate if not provided)
            if not text_body:
                text_body = self._html_to_text(html_body)
            msg.attach(MIMEText(text_body, 'plain'))

            # Add HTML version
            msg.attach(MIMEText(html_body, 'html'))

            # Send email
            with smtplib.SMTP(self.config.smtp_host, self.config.smtp_port) as server:
                if self.config.smtp_use_tls:
                    server.starttls()
                server.login(self.config.smtp_user, self.config.smtp_password)
                server.send_message(msg)

            logger.info(f"Email sent to {to_email}: {subject}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False

    # ============================================================================
    # EMAIL TEMPLATES
    # ============================================================================

    def _render_verification_email(self, verification_url: str,
                                   display_name: Optional[str]) -> str:
        """Render verification email HTML."""
        name = display_name or "there"
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2>Welcome to AI Match Simulation!</h2>
            <p>Hi {name},</p>
            <p>Thanks for signing up! Please verify your email address to get started.</p>
            <p style="margin: 30px 0;">
                <a href="{verification_url}"
                   style="background-color: #4CAF50; color: white; padding: 12px 24px;
                          text-decoration: none; border-radius: 4px; display: inline-block;">
                    Verify Email Address
                </a>
            </p>
            <p>Or copy and paste this link into your browser:</p>
            <p style="color: #666; word-break: break-all;">{verification_url}</p>
            <p>This link will expire in 24 hours.</p>
            <hr style="margin: 30px 0; border: none; border-top: 1px solid #ddd;">
            <p style="color: #666; font-size: 12px;">
                If you didn't create an account, you can safely ignore this email.
            </p>
        </body>
        </html>
        """

    def _render_password_reset_email(self, reset_url: str,
                                     display_name: Optional[str]) -> str:
        """Render password reset email HTML."""
        name = display_name or "there"
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2>Reset Your Password</h2>
            <p>Hi {name},</p>
            <p>We received a request to reset your password. Click the button below to create a new password:</p>
            <p style="margin: 30px 0;">
                <a href="{reset_url}"
                   style="background-color: #2196F3; color: white; padding: 12px 24px;
                          text-decoration: none; border-radius: 4px; display: inline-block;">
                    Reset Password
                </a>
            </p>
            <p>Or copy and paste this link into your browser:</p>
            <p style="color: #666; word-break: break-all;">{reset_url}</p>
            <p>This link will expire in 1 hour.</p>
            <hr style="margin: 30px 0; border: none; border-top: 1px solid #ddd;">
            <p style="color: #666; font-size: 12px;">
                If you didn't request a password reset, you can safely ignore this email.
            </p>
        </body>
        </html>
        """

    def _render_welcome_email(self, tier: str, display_name: Optional[str]) -> str:
        """Render welcome email HTML."""
        name = display_name or "there"
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2>Welcome to AI Match Simulation {tier}! 🎉</h2>
            <p>Hi {name},</p>
            <p>Thank you for subscribing! You now have access to premium AI-powered match predictions.</p>
            <h3>What's included:</h3>
            <ul>
                <li>Unlimited match simulations</li>
                <li>Claude Sonnet 4.5 AI analysis</li>
                <li>Sharp bookmaker insights</li>
                <li>Advanced analytics</li>
            </ul>
            <p style="margin: 30px 0;">
                <a href="{self.base_url}/dashboard"
                   style="background-color: #4CAF50; color: white; padding: 12px 24px;
                          text-decoration: none; border-radius: 4px; display: inline-block;">
                    Get Started
                </a>
            </p>
            <p>Need help? Contact us at {self.config.support_email}</p>
        </body>
        </html>
        """

    def _render_payment_receipt(self, amount: float, tier: str, period_end: datetime,
                               display_name: Optional[str]) -> str:
        """Render payment receipt email HTML."""
        name = display_name or "there"
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2>Payment Receipt</h2>
            <p>Hi {name},</p>
            <p>Thank you for your payment! Here are your receipt details:</p>
            <table style="width: 100%; margin: 20px 0; border-collapse: collapse;">
                <tr style="border-bottom: 1px solid #ddd;">
                    <td style="padding: 10px;"><strong>Subscription:</strong></td>
                    <td style="padding: 10px;">AI Match Simulation {tier}</td>
                </tr>
                <tr style="border-bottom: 1px solid #ddd;">
                    <td style="padding: 10px;"><strong>Amount:</strong></td>
                    <td style="padding: 10px;">${amount:.2f}</td>
                </tr>
                <tr style="border-bottom: 1px solid #ddd;">
                    <td style="padding: 10px;"><strong>Next billing date:</strong></td>
                    <td style="padding: 10px;">{period_end.strftime('%B %d, %Y')}</td>
                </tr>
            </table>
            <p style="margin: 30px 0;">
                <a href="{self.base_url}/account"
                   style="background-color: #2196F3; color: white; padding: 12px 24px;
                          text-decoration: none; border-radius: 4px; display: inline-block;">
                    Manage Subscription
                </a>
            </p>
        </body>
        </html>
        """

    def _render_trial_ending_email(self, trial_end: datetime,
                                   display_name: Optional[str]) -> str:
        """Render trial ending email HTML."""
        name = display_name or "there"
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2>Your Trial is Ending Soon</h2>
            <p>Hi {name},</p>
            <p>Your free trial of AI Match Simulation PRO will end on {trial_end.strftime('%B %d, %Y')}.</p>
            <p>After your trial ends, your subscription will automatically renew at $19.99/month.</p>
            <p>Want to continue enjoying unlimited AI match predictions?</p>
            <p style="margin: 30px 0;">
                <a href="{self.base_url}/account"
                   style="background-color: #4CAF50; color: white; padding: 12px 24px;
                          text-decoration: none; border-radius: 4px; display: inline-block;">
                    Manage Subscription
                </a>
            </p>
            <p>You can cancel anytime before {trial_end.strftime('%B %d, %Y')} to avoid charges.</p>
        </body>
        </html>
        """

    def _render_subscription_canceled_email(self, period_end: datetime,
                                           display_name: Optional[str]) -> str:
        """Render subscription canceled email HTML."""
        name = display_name or "there"
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2>Subscription Canceled</h2>
            <p>Hi {name},</p>
            <p>Your AI Match Simulation PRO subscription has been canceled.</p>
            <p>You'll continue to have access until {period_end.strftime('%B %d, %Y')}.</p>
            <p>Changed your mind? You can reactivate anytime.</p>
            <p style="margin: 30px 0;">
                <a href="{self.base_url}/pricing"
                   style="background-color: #4CAF50; color: white; padding: 12px 24px;
                          text-decoration: none; border-radius: 4px; display: inline-block;">
                    Reactivate Subscription
                </a>
            </p>
            <p>We're sorry to see you go! If you have feedback, please let us know at {self.config.support_email}</p>
        </body>
        </html>
        """

    def _render_payment_failed_email(self, display_name: Optional[str]) -> str:
        """Render payment failed email HTML."""
        name = display_name or "there"
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2>Payment Failed</h2>
            <p>Hi {name},</p>
            <p>We were unable to process your payment for AI Match Simulation PRO.</p>
            <p>Please update your payment method to continue your subscription.</p>
            <p style="margin: 30px 0;">
                <a href="{self.base_url}/account"
                   style="background-color: #f44336; color: white; padding: 12px 24px;
                          text-decoration: none; border-radius: 4px; display: inline-block;">
                    Update Payment Method
                </a>
            </p>
            <p>If you need assistance, contact us at {self.config.support_email}</p>
        </body>
        </html>
        """

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================

    def _html_to_text(self, html: str) -> str:
        """
        Convert HTML to plain text (simple version).

        Args:
            html: HTML content

        Returns:
            Plain text version
        """
        # Remove HTML tags (simple regex approach)
        import re
        text = re.sub('<[^<]+?>', '', html)
        text = text.replace('&nbsp;', ' ')
        return text.strip()


# Global service instance
_email_service = None


def get_email_service() -> EmailService:
    """Get global email service instance (singleton)."""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
