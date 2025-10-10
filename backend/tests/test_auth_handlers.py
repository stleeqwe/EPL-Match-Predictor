"""
Test Authentication Handlers
AI Match Simulation v3.0

Tests for JWT and Password handlers
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from auth.jwt_handler import JWTHandler, TokenExpiredError, InvalidTokenError
from auth.password_handler import PasswordHandler
import time


def test_password_handler():
    """Test Password Handler"""
    print("\n" + "="*70)
    print("TESTING PASSWORD HANDLER")
    print("="*70)

    handler = PasswordHandler(rounds=10)  # Lower rounds for faster testing

    # Test 1: Password Hashing
    print("\n[Test 1] Password Hashing")
    password = "MySecurePassword123!"
    hashed = handler.hash_password(password)
    print(f"✓ Password hashed: {hashed[:50]}...")
    assert hashed != password
    assert len(hashed) > 50

    # Test 2: Password Verification
    print("\n[Test 2] Password Verification")
    is_valid = handler.verify_password(password, hashed)
    print(f"✓ Correct password verified: {is_valid}")
    assert is_valid == True

    is_invalid = handler.verify_password("WrongPassword", hashed)
    print(f"✓ Wrong password rejected: {not is_invalid}")
    assert is_invalid == False

    # Test 3: Password Strength Check
    print("\n[Test 3] Password Strength Check")

    # Weak password
    weak_pass = "123456"
    valid, checks, score = handler.check_password_strength(weak_pass)
    print(f"Weak password: {weak_pass}")
    print(f"  Valid: {valid}, Score: {score}/5")
    print(f"  Checks: {checks}")
    assert valid == False

    # Strong password
    strong_pass = "MySecure@Pass2024"
    valid, checks, score = handler.check_password_strength(strong_pass)
    print(f"\nStrong password: {strong_pass}")
    print(f"  Valid: {valid}, Score: {score}/5")
    print(f"  Checks: {checks}")
    assert valid == True

    # Test 4: Password Feedback
    print("\n[Test 4] Password Feedback")
    feedback = handler.generate_password_feedback(checks, score)
    print(f"Strength: {feedback['strength']}")
    print(f"Message: {feedback['message']}")
    if feedback['suggestions']:
        print(f"Suggestions: {feedback['suggestions']}")

    # Test 5: Common Password Check
    print("\n[Test 5] Common Password Check")
    is_common = handler.is_common_password("password123")
    print(f"✓ 'password123' is common: {is_common}")
    assert is_common == True

    is_common = handler.is_common_password("MyUniqueP@ss2024")
    print(f"✓ 'MyUniqueP@ss2024' is not common: {not is_common}")
    assert is_common == False

    print("\n" + "="*70)
    print("✅ ALL PASSWORD HANDLER TESTS PASSED")
    print("="*70)


def test_jwt_handler():
    """Test JWT Handler"""
    print("\n" + "="*70)
    print("TESTING JWT HANDLER")
    print("="*70)

    handler = JWTHandler(
        secret_key="test-secret-key-do-not-use-in-production",
        access_token_expires=5,  # 5 seconds for testing
        refresh_token_expires=10  # 10 seconds for testing
    )

    user_id = "test-user-123"
    tier = "PRO"
    email = "test@example.com"

    # Test 1: Create Access Token
    print("\n[Test 1] Create Access Token")
    access_token = handler.create_access_token(user_id, tier, email)
    print(f"✓ Access token created: {access_token[:50]}...")
    assert len(access_token) > 50

    # Test 2: Verify Access Token
    print("\n[Test 2] Verify Access Token")
    payload = handler.verify_token(access_token, token_type='access', check_blacklist=False)
    print(f"✓ Token verified")
    print(f"  User ID: {payload['user_id']}")
    print(f"  Tier: {payload['tier']}")
    print(f"  Email: {payload['email']}")
    assert payload['user_id'] == user_id
    assert payload['tier'] == tier
    assert payload['email'] == email

    # Test 3: Create Refresh Token
    print("\n[Test 3] Create Refresh Token")
    refresh_token = handler.create_refresh_token(user_id)
    print(f"✓ Refresh token created: {refresh_token[:50]}...")
    assert len(refresh_token) > 50

    # Test 4: Verify Refresh Token
    print("\n[Test 4] Verify Refresh Token")
    payload = handler.verify_token(refresh_token, token_type='refresh', check_blacklist=False)
    print(f"✓ Refresh token verified")
    print(f"  User ID: {payload['user_id']}")
    assert payload['user_id'] == user_id

    # Test 5: Token Type Mismatch
    print("\n[Test 5] Token Type Validation")
    try:
        handler.verify_token(access_token, token_type='refresh', check_blacklist=False)
        assert False, "Should have raised InvalidTokenError"
    except InvalidTokenError as e:
        print(f"✓ Token type mismatch detected: {e}")

    # Test 6: Invalid Token
    print("\n[Test 6] Invalid Token Detection")
    try:
        handler.verify_token("invalid.token.here", check_blacklist=False)
        assert False, "Should have raised InvalidTokenError"
    except InvalidTokenError as e:
        print(f"✓ Invalid token detected: {e}")

    # Test 7: Token Expiration
    print("\n[Test 7] Token Expiration")
    print("Waiting 6 seconds for access token to expire...")
    time.sleep(6)
    try:
        handler.verify_token(access_token, check_blacklist=False)
        assert False, "Should have raised TokenExpiredError"
    except TokenExpiredError as e:
        print(f"✓ Expired token detected: {e}")

    # Test 8: Decode Without Verification
    print("\n[Test 8] Decode Without Verification (Inspection)")
    decoded = handler.decode_token_without_verification(access_token)
    print(f"✓ Token decoded without verification")
    print(f"  User ID: {decoded['user_id']}")
    print(f"  Type: {decoded['type']}")

    print("\n" + "="*70)
    print("✅ ALL JWT HANDLER TESTS PASSED")
    print("="*70)


def main():
    """Run all tests"""
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*10 + "AI Match Simulation v3.0 - Auth Handler Tests" + " "*12 + "║")
    print("╚" + "="*68 + "╝")

    try:
        # Test Password Handler
        test_password_handler()

        # Test JWT Handler
        test_jwt_handler()

        # Summary
        print("\n")
        print("╔" + "="*68 + "╗")
        print("║" + " "*20 + "🎉 ALL TESTS PASSED! 🎉" + " "*25 + "║")
        print("╚" + "="*68 + "╝")
        print("\n")

        return 0

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return 1

    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(main())
