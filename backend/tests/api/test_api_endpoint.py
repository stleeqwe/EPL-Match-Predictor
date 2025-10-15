"""
Test API Endpoint
Quick test of the new /api/v1/simulation/predict endpoint
"""

import requests
import json

# Test data
test_request = {
    "home_team": "Manchester City",
    "away_team": "Arsenal",
    "home_rating": 90.0,
    "away_rating": 85.0
}

print("Testing /api/v1/simulation/predict endpoint...")
print(f"Request: {json.dumps(test_request, indent=2)}")
print("\n" + "="*80)

try:
    response = requests.post(
        "http://localhost:5001/api/v1/simulation/predict",
        json=test_request,
        timeout=120
    )

    print(f"Status Code: {response.status_code}")
    print("\nResponse:")
    print(json.dumps(response.json(), indent=2))

    if response.status_code == 200:
        print("\n✅ API Test PASSED")
    else:
        print("\n❌ API Test FAILED")

except Exception as e:
    print(f"\n❌ Error: {e}")
