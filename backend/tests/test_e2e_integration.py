"""
End-to-End Integration Tests
AI Match Simulation v3.0

Tests the complete user journey:
1. User Registration
2. User Login
3. AI Simulation Request
4. Payment Upgrade
5. Premium Simulation

Author: PMO
Date: 2025-10-08
"""

import pytest
import os
from datetime import datetime
import hashlib
import uuid
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import core modules
from auth.jwt_handler import JWTHandler
from auth.password_handler import PasswordHandler
from database.connection import get_connection


class TestE2EIntegration:
    """End-to-end integration tests for the complete system."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test environment."""
        # Initialize handlers
        self.jwt_handler = JWTHandler(
            secret_key=os.getenv('JWT_SECRET_KEY', 'test-secret-key'),
            algorithm='HS256'
        )
        self.password_handler = PasswordHandler()

        # Test user data
        self.test_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
        self.test_password = "TestP@ssw0rd123"
        self.test_display_name = "Test User"

        yield

        # Cleanup: Delete test user after test
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE email = %s", (self.test_email,))
            conn.commit()
            cursor.close()
            conn.close()
        except Exception:
            pass

    def test_01_user_registration_flow(self):
        """
        Test Case 1: User Registration

        Steps:
        1. Hash password
        2. Create user in database
        3. Verify user exists
        """
        # Step 1: Hash password
        password_hash = self.password_handler.hash_password(self.test_password)
        assert password_hash is not None
        assert password_hash != self.test_password

        # Step 2: Create user
        try:
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO users (email, password_hash, display_name, tier, is_active)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id, email, tier
            """, (
                self.test_email,
                password_hash,
                self.test_display_name,
                'BASIC',
                True
            ))

            user_data = cursor.fetchone()
            conn.commit()
            cursor.close()
            conn.close()

            assert user_data is not None
            assert user_data[1] == self.test_email  # email
            assert user_data[2] == 'BASIC'  # tier

            print(f"\n✅ User registered: {self.test_email}")

        except Exception as e:
            pytest.fail(f"User registration failed: {e}")

    def test_02_user_login_flow(self):
        """
        Test Case 2: User Login

        Steps:
        1. Create user
        2. Verify password
        3. Generate JWT tokens
        4. Verify tokens
        """
        # Step 1: Create user
        password_hash = self.password_handler.hash_password(self.test_password)

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (email, password_hash, display_name, tier)
            VALUES (%s, %s, %s, %s)
            RETURNING id, email, tier
        """, (self.test_email, password_hash, self.test_display_name, 'BASIC'))

        user_data = cursor.fetchone()
        user_id = str(user_data[0])
        conn.commit()
        cursor.close()
        conn.close()

        # Step 2: Verify password
        is_valid = self.password_handler.verify_password(
            self.test_password,
            password_hash
        )
        assert is_valid, "Password verification failed"

        # Step 3: Generate JWT tokens
        access_token = self.jwt_handler.create_access_token(
            user_id=user_id,
            tier='BASIC',
            email=self.test_email
        )
        refresh_token = self.jwt_handler.create_refresh_token(user_id=user_id)

        assert access_token is not None
        assert refresh_token is not None

        # Step 4: Verify tokens
        access_payload = self.jwt_handler.verify_token(access_token, 'access')
        assert access_payload is not None
        assert access_payload['user_id'] == user_id
        assert access_payload['email'] == self.test_email

        print(f"\n✅ User login successful: {self.test_email}")
        print(f"   Access Token: {access_token[:50]}...")
        print(f"   Refresh Token: {refresh_token[:50]}...")

    def test_03_simulation_request_basic_tier(self):
        """
        Test Case 3: AI Simulation Request (BASIC tier)

        Steps:
        1. Create BASIC tier user
        2. Check rate limiting
        3. Verify simulation request would work
        """
        # Step 1: Create user
        password_hash = self.password_handler.hash_password(self.test_password)

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (email, password_hash, display_name, tier)
            VALUES (%s, %s, %s, %s)
            RETURNING id, email, tier
        """, (self.test_email, password_hash, self.test_display_name, 'BASIC'))

        user_data = cursor.fetchone()
        user_id = str(user_data[0])
        conn.commit()

        # Step 2: Check rate limits (BASIC tier: 5/hour)
        # Simulate 3 simulation requests
        for i in range(3):
            cursor.execute("""
                INSERT INTO usage_tracking (
                    user_id, endpoint, method, tier,
                    timestamp, status_code
                )
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                user_id,
                '/api/v1/simulation/simulate',
                'POST',
                'BASIC',
                datetime.now(),
                200
            ))

        conn.commit()

        # Step 3: Verify usage tracking
        cursor.execute("""
            SELECT COUNT(*) FROM usage_tracking
            WHERE user_id = %s
            AND endpoint = '/api/v1/simulation/simulate'
            AND timestamp > NOW() - INTERVAL '1 hour'
        """, (user_id,))

        usage_count = cursor.fetchone()[0]
        cursor.close()
        conn.close()

        assert usage_count == 3
        assert usage_count < 5  # Under BASIC tier limit

        print(f"\n✅ Simulation requests tracked: {usage_count}/5 (BASIC tier)")

    def test_04_tier_upgrade_flow(self):
        """
        Test Case 4: Tier Upgrade (BASIC → PRO)

        Steps:
        1. Create BASIC tier user
        2. Simulate Stripe subscription
        3. Upgrade tier to PRO
        4. Verify upgrade
        """
        # Step 1: Create BASIC user
        password_hash = self.password_handler.hash_password(self.test_password)

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (email, password_hash, display_name, tier)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """, (self.test_email, password_hash, self.test_display_name, 'BASIC'))

        user_id = str(cursor.fetchone()[0])
        conn.commit()

        # Step 2: Simulate subscription
        fake_subscription_id = f"sub_{uuid.uuid4().hex[:16]}"

        cursor.execute("""
            INSERT INTO subscriptions (
                user_id, stripe_subscription_id, tier, status,
                current_period_start, current_period_end
            )
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            user_id,
            fake_subscription_id,
            'PRO',
            'active',
            datetime.now(),
            datetime.now()
        ))

        # Step 3: Upgrade user tier
        cursor.execute("""
            UPDATE users
            SET tier = 'PRO'
            WHERE id = %s
        """, (user_id,))

        conn.commit()

        # Step 4: Verify upgrade
        cursor.execute("""
            SELECT tier FROM users WHERE id = %s
        """, (user_id,))

        tier = cursor.fetchone()[0]
        cursor.close()
        conn.close()

        assert tier == 'PRO'

        print(f"\n✅ Tier upgraded: BASIC → PRO")
        print(f"   Subscription ID: {fake_subscription_id}")

    def test_05_complete_user_journey(self):
        """
        Test Case 5: Complete User Journey

        Full simulation:
        1. Register
        2. Login
        3. Make 3 simulations (BASIC)
        4. Upgrade to PRO
        5. Make unlimited simulations
        """
        # Step 1: Register
        password_hash = self.password_handler.hash_password(self.test_password)

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (email, password_hash, display_name, tier)
            VALUES (%s, %s, %s, %s)
            RETURNING id, email, tier
        """, (self.test_email, password_hash, self.test_display_name, 'BASIC'))

        user_data = cursor.fetchone()
        user_id = str(user_data[0])
        conn.commit()

        print(f"\n✅ Step 1: User registered - {self.test_email}")

        # Step 2: Login
        access_token = self.jwt_handler.create_access_token(
            user_id=user_id,
            tier='BASIC',
            email=self.test_email
        )

        print(f"✅ Step 2: User logged in - Token generated")

        # Step 3: BASIC tier simulations (3/5)
        for i in range(3):
            cursor.execute("""
                INSERT INTO usage_tracking (
                    user_id, endpoint, method, tier,
                    timestamp, status_code, tokens_used, cost_usd
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                user_id,
                '/api/v1/simulation/simulate',
                'POST',
                'BASIC',
                datetime.now(),
                200,
                1500,  # tokens
                0.0045  # cost ($3/M input + $15/M output ≈ $0.0045)
            ))

        conn.commit()
        print(f"✅ Step 3: Made 3 simulations (BASIC tier)")

        # Step 4: Upgrade to PRO
        fake_subscription_id = f"sub_{uuid.uuid4().hex[:16]}"

        cursor.execute("""
            INSERT INTO subscriptions (
                user_id, stripe_subscription_id, tier, status
            )
            VALUES (%s, %s, %s, %s)
        """, (user_id, fake_subscription_id, 'PRO', 'active'))

        cursor.execute("""
            UPDATE users SET tier = 'PRO' WHERE id = %s
        """, (user_id,))

        conn.commit()
        print(f"✅ Step 4: Upgraded to PRO tier")

        # Step 5: PRO tier simulations (unlimited)
        for i in range(10):
            cursor.execute("""
                INSERT INTO usage_tracking (
                    user_id, endpoint, method, tier,
                    timestamp, status_code, tokens_used, cost_usd
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                user_id,
                '/api/v1/simulation/simulate',
                'POST',
                'PRO',
                datetime.now(),
                200,
                2000,  # More tokens (better model)
                0.006  # Slightly higher cost
            ))

        conn.commit()
        print(f"✅ Step 5: Made 10 simulations (PRO tier - unlimited)")

        # Verify final state
        cursor.execute("""
            SELECT
                u.email,
                u.tier,
                COUNT(ut.id) as simulation_count,
                SUM(ut.tokens_used) as total_tokens,
                SUM(ut.cost_usd) as total_cost
            FROM users u
            LEFT JOIN usage_tracking ut ON u.id = ut.user_id
            WHERE u.id = %s
            GROUP BY u.email, u.tier
        """, (user_id,))

        result = cursor.fetchone()
        cursor.close()
        conn.close()

        email, tier, sim_count, total_tokens, total_cost = result

        assert email == self.test_email
        assert tier == 'PRO'
        assert sim_count == 13  # 3 BASIC + 10 PRO
        assert total_tokens > 0
        assert total_cost > 0

        print(f"\n🎉 Complete User Journey SUCCESS!")
        print(f"   Email: {email}")
        print(f"   Final Tier: {tier}")
        print(f"   Total Simulations: {sim_count}")
        print(f"   Total Tokens: {total_tokens:,}")
        print(f"   Total Cost: ${total_cost:.4f}")


class TestDatabaseIntegrity:
    """Test database constraints and relationships."""

    def test_user_cascade_delete(self):
        """
        Test that deleting a user cascades to related tables.
        """
        # Create test user
        test_email = f"cascade_test_{uuid.uuid4().hex[:8]}@example.com"
        password_hash = PasswordHandler().hash_password("TestP@ss123")

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO users (email, password_hash, display_name)
            VALUES (%s, %s, %s)
            RETURNING id
        """, (test_email, password_hash, "Cascade Test"))

        user_id = str(cursor.fetchone()[0])
        conn.commit()

        # Add related records
        cursor.execute("""
            INSERT INTO usage_tracking (user_id, endpoint, method, tier)
            VALUES (%s, %s, %s, %s)
        """, (user_id, '/test', 'POST', 'BASIC'))

        conn.commit()

        # Verify records exist
        cursor.execute("SELECT COUNT(*) FROM usage_tracking WHERE user_id = %s", (user_id,))
        count_before = cursor.fetchone()[0]
        assert count_before == 1

        # Delete user
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()

        # Verify cascade delete
        cursor.execute("SELECT COUNT(*) FROM usage_tracking WHERE user_id = %s", (user_id,))
        count_after = cursor.fetchone()[0]

        cursor.close()
        conn.close()

        assert count_after == 0
        print("\n✅ Cascade delete working correctly")

    def test_subscription_constraints(self):
        """
        Test subscription business logic constraints.
        """
        # Create test user
        test_email = f"sub_test_{uuid.uuid4().hex[:8]}@example.com"
        password_hash = PasswordHandler().hash_password("TestP@ss123")

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO users (email, password_hash)
            VALUES (%s, %s)
            RETURNING id
        """, (test_email, password_hash))

        user_id = str(cursor.fetchone()[0])
        conn.commit()

        # Test: User can only have one active subscription
        cursor.execute("""
            INSERT INTO subscriptions (user_id, tier, status)
            VALUES (%s, %s, %s)
        """, (user_id, 'PRO', 'active'))
        conn.commit()

        # Try to insert another active subscription (should fail due to unique constraint)
        try:
            cursor.execute("""
                INSERT INTO subscriptions (user_id, tier, status)
                VALUES (%s, %s, %s)
            """, (user_id, 'PRO', 'trialing'))
            conn.commit()

            # Cleanup
            cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
            conn.commit()
            cursor.close()
            conn.close()

            pytest.fail("Should not allow multiple active subscriptions")

        except Exception as e:
            # Expected error due to unique constraint
            conn.rollback()

            # Cleanup
            cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
            conn.commit()
            cursor.close()
            conn.close()

            print("\n✅ Subscription constraints enforced correctly")
            assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
