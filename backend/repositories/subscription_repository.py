"""
Subscription Repository
AI Match Simulation v3.0

Database operations for subscription records.
"""

from typing import Optional, List, Dict
from datetime import datetime
import logging

from database.connection import db_pool


# Configure logging
logger = logging.getLogger(__name__)


class Subscription:
    """Subscription model."""

    def __init__(self, row: tuple):
        """
        Initialize from database row.

        Args:
            row: Database row tuple
        """
        if row:
            self.id = row[0]
            self.user_id = row[1]
            self.stripe_subscription_id = row[2]
            self.tier = row[3]
            self.status = row[4]
            self.current_period_start = row[5]
            self.current_period_end = row[6]
            self.trial_start = row[7]
            self.trial_end = row[8]
            self.cancel_at_period_end = row[9]
            self.canceled_at = row[10]
            self.cancellation_reason = row[11]
            self.created_at = row[12]
            self.updated_at = row[13]
            self.metadata = row[14] or {}

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'stripe_subscription_id': self.stripe_subscription_id,
            'tier': self.tier,
            'status': self.status,
            'current_period_start': self.current_period_start.isoformat() if self.current_period_start else None,
            'current_period_end': self.current_period_end.isoformat() if self.current_period_end else None,
            'trial_start': self.trial_start.isoformat() if self.trial_start else None,
            'trial_end': self.trial_end.isoformat() if self.trial_end else None,
            'cancel_at_period_end': self.cancel_at_period_end,
            'canceled_at': self.canceled_at.isoformat() if self.canceled_at else None,
            'cancellation_reason': self.cancellation_reason,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'metadata': self.metadata
        }


class SubscriptionRepository:
    """Repository for subscription database operations."""

    @staticmethod
    def create(user_id: str, stripe_subscription_id: str, tier: str, status: str,
               current_period_start: Optional[datetime] = None,
               current_period_end: Optional[datetime] = None,
               trial_start: Optional[datetime] = None,
               trial_end: Optional[datetime] = None,
               metadata: Optional[Dict] = None) -> Optional[Subscription]:
        """
        Create a new subscription record.

        Args:
            user_id: User ID
            stripe_subscription_id: Stripe subscription ID
            tier: Subscription tier
            status: Subscription status
            current_period_start: Period start date
            current_period_end: Period end date
            trial_start: Trial start date
            trial_end: Trial end date
            metadata: Additional metadata

        Returns:
            Subscription instance or None if failed
        """
        try:
            with db_pool.get_cursor() as cur:
                cur.execute("""
                    INSERT INTO subscriptions (
                        user_id, stripe_subscription_id, tier, status,
                        current_period_start, current_period_end,
                        trial_start, trial_end, metadata
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING *
                """, (user_id, stripe_subscription_id, tier, status,
                      current_period_start, current_period_end,
                      trial_start, trial_end, metadata or {}))

                row = cur.fetchone()
                logger.info(f"Created subscription for user {user_id}")
                return Subscription(row) if row else None

        except Exception as e:
            logger.error(f"Error creating subscription: {str(e)}")
            return None

    @staticmethod
    def get_by_id(subscription_id: str) -> Optional[Subscription]:
        """
        Get subscription by ID.

        Args:
            subscription_id: Subscription ID

        Returns:
            Subscription instance or None
        """
        try:
            with db_pool.get_cursor() as cur:
                cur.execute("SELECT * FROM subscriptions WHERE id = %s", (subscription_id,))
                row = cur.fetchone()
                return Subscription(row) if row else None

        except Exception as e:
            logger.error(f"Error retrieving subscription {subscription_id}: {str(e)}")
            return None

    @staticmethod
    def get_by_stripe_id(stripe_subscription_id: str) -> Optional[Subscription]:
        """
        Get subscription by Stripe subscription ID.

        Args:
            stripe_subscription_id: Stripe subscription ID

        Returns:
            Subscription instance or None
        """
        try:
            with db_pool.get_cursor() as cur:
                cur.execute(
                    "SELECT * FROM subscriptions WHERE stripe_subscription_id = %s",
                    (stripe_subscription_id,)
                )
                row = cur.fetchone()
                return Subscription(row) if row else None

        except Exception as e:
            logger.error(f"Error retrieving subscription by Stripe ID: {str(e)}")
            return None

    @staticmethod
    def get_active_by_user(user_id: str) -> Optional[Subscription]:
        """
        Get active subscription for a user.

        Args:
            user_id: User ID

        Returns:
            Active subscription or None
        """
        try:
            with db_pool.get_cursor() as cur:
                cur.execute("""
                    SELECT * FROM subscriptions
                    WHERE user_id = %s AND status IN ('active', 'trialing')
                    ORDER BY created_at DESC
                    LIMIT 1
                """, (user_id,))
                row = cur.fetchone()
                return Subscription(row) if row else None

        except Exception as e:
            logger.error(f"Error retrieving active subscription for user {user_id}: {str(e)}")
            return None

    @staticmethod
    def get_all_by_user(user_id: str) -> List[Subscription]:
        """
        Get all subscriptions for a user.

        Args:
            user_id: User ID

        Returns:
            List of subscriptions
        """
        try:
            with db_pool.get_cursor() as cur:
                cur.execute("""
                    SELECT * FROM subscriptions
                    WHERE user_id = %s
                    ORDER BY created_at DESC
                """, (user_id,))
                rows = cur.fetchall()
                return [Subscription(row) for row in rows]

        except Exception as e:
            logger.error(f"Error retrieving subscriptions for user {user_id}: {str(e)}")
            return []

    @staticmethod
    def update_status(subscription_id: str, status: str,
                     canceled_at: Optional[datetime] = None,
                     cancellation_reason: Optional[str] = None) -> bool:
        """
        Update subscription status.

        Args:
            subscription_id: Subscription ID
            status: New status
            canceled_at: Cancellation timestamp
            cancellation_reason: Reason for cancellation

        Returns:
            True if successful, False otherwise
        """
        try:
            with db_pool.get_cursor() as cur:
                cur.execute("""
                    UPDATE subscriptions
                    SET status = %s,
                        canceled_at = %s,
                        cancellation_reason = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (status, canceled_at, cancellation_reason, subscription_id))

                logger.info(f"Updated subscription {subscription_id} status to {status}")
                return True

        except Exception as e:
            logger.error(f"Error updating subscription status: {str(e)}")
            return False

    @staticmethod
    def update_from_stripe(subscription_id: str, stripe_data: Dict) -> bool:
        """
        Update subscription from Stripe webhook data.

        Args:
            subscription_id: Subscription ID (can be internal ID or Stripe ID)
            stripe_data: Data from Stripe webhook

        Returns:
            True if successful, False otherwise
        """
        try:
            with db_pool.get_cursor() as cur:
                # Try to find by Stripe ID first, then by internal ID
                if 'id' in stripe_data:
                    cur.execute(
                        "SELECT id FROM subscriptions WHERE stripe_subscription_id = %s",
                        (stripe_data['id'],)
                    )
                    result = cur.fetchone()
                    if result:
                        subscription_id = result[0]

                cur.execute("""
                    UPDATE subscriptions
                    SET status = %s,
                        current_period_start = %s,
                        current_period_end = %s,
                        cancel_at_period_end = %s,
                        canceled_at = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s OR stripe_subscription_id = %s
                """, (
                    stripe_data.get('status'),
                    datetime.fromtimestamp(stripe_data['current_period_start']) if 'current_period_start' in stripe_data else None,
                    datetime.fromtimestamp(stripe_data['current_period_end']) if 'current_period_end' in stripe_data else None,
                    stripe_data.get('cancel_at_period_end', False),
                    datetime.fromtimestamp(stripe_data['canceled_at']) if stripe_data.get('canceled_at') else None,
                    subscription_id,
                    stripe_data.get('id')
                ))

                logger.info(f"Updated subscription {subscription_id} from Stripe")
                return True

        except Exception as e:
            logger.error(f"Error updating subscription from Stripe: {str(e)}")
            return False

    @staticmethod
    def set_cancel_at_period_end(subscription_id: str, cancel: bool,
                                 reason: Optional[str] = None) -> bool:
        """
        Set cancel_at_period_end flag.

        Args:
            subscription_id: Subscription ID
            cancel: True to cancel at period end, False to reactivate
            reason: Cancellation reason (if canceling)

        Returns:
            True if successful, False otherwise
        """
        try:
            with db_pool.get_cursor() as cur:
                if cancel:
                    cur.execute("""
                        UPDATE subscriptions
                        SET cancel_at_period_end = TRUE,
                            cancellation_reason = %s,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """, (reason, subscription_id))
                else:
                    cur.execute("""
                        UPDATE subscriptions
                        SET cancel_at_period_end = FALSE,
                            cancellation_reason = NULL,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """, (subscription_id,))

                action = "scheduled cancellation" if cancel else "reactivated"
                logger.info(f"Subscription {subscription_id} {action}")
                return True

        except Exception as e:
            logger.error(f"Error setting cancel_at_period_end: {str(e)}")
            return False

    @staticmethod
    def delete(subscription_id: str) -> bool:
        """
        Delete a subscription record.

        Args:
            subscription_id: Subscription ID

        Returns:
            True if successful, False otherwise
        """
        try:
            with db_pool.get_cursor() as cur:
                cur.execute("DELETE FROM subscriptions WHERE id = %s", (subscription_id,))
                logger.info(f"Deleted subscription {subscription_id}")
                return True

        except Exception as e:
            logger.error(f"Error deleting subscription: {str(e)}")
            return False

    @staticmethod
    def get_expiring_soon(days: int = 7) -> List[Subscription]:
        """
        Get subscriptions expiring within specified days.

        Args:
            days: Number of days to look ahead

        Returns:
            List of subscriptions
        """
        try:
            with db_pool.get_cursor() as cur:
                cur.execute("""
                    SELECT * FROM subscriptions
                    WHERE status IN ('active', 'trialing')
                      AND current_period_end <= CURRENT_TIMESTAMP + INTERVAL '%s days'
                      AND current_period_end > CURRENT_TIMESTAMP
                    ORDER BY current_period_end ASC
                """, (days,))
                rows = cur.fetchall()
                return [Subscription(row) for row in rows]

        except Exception as e:
            logger.error(f"Error retrieving expiring subscriptions: {str(e)}")
            return []


# Convenience function for getting repository
def get_subscription_repository() -> SubscriptionRepository:
    """Get subscription repository instance."""
    return SubscriptionRepository()
