#!/usr/bin/env python3
"""
Test V3 Auth API
Quick test script for SQLite-based auth system
"""

import requests
import json

BASE_URL = "http://localhost:5001"

def test_signup():
    """Test signup endpoint"""
    print("\n" + "="*50)
    print("TEST 1: Signup")
    print("="*50)

    response = requests.post(
        f"{BASE_URL}/api/v1/auth/signup",
        json={
            "email": "test@example.com",
            "password": "SecurePass123!",
            "display_name": "Test User"
        }
    )

    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    return response.json() if response.ok else None

def test_login(email, password):
    """Test login endpoint"""
    print("\n" + "="*50)
    print("TEST 2: Login")
    print("="*50)

    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        json={
            "email": email,
            "password": password
        }
    )

    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    return response.json() if response.ok else None

if __name__ == "__main__":
    print("\n🚀 V3 Auth API Test (SQLite)")
    print("="*50)

    # Test signup
    signup_data = test_signup()

    # Test login
    if signup_data or True:  # Try login even if signup fails (user might exist)
        login_data = test_login("test@example.com", "SecurePass123!")

        if login_data and login_data.get('success'):
            print("\n✅ V3 Auth system is working!")
            print(f"   - Access Token: {login_data.get('access_token', '')[:20]}...")
            print(f"   - User Tier: {login_data.get('user', {}).get('tier')}")
        else:
            print("\n❌ Login failed")
    else:
        print("\n❌ Signup failed")

    print("\n" + "="*50)
