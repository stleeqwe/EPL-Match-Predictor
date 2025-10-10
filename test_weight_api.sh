#!/bin/bash

# Weight Customization API Test Script
# Tests the new weight customization endpoints

BASE_URL="http://localhost:5001"

echo "=================================================="
echo "Weight Customization API Test"
echo "=================================================="
echo ""

# Test 1: Get Weight Presets (no auth required)
echo "Test 1: GET /api/v1/simulation/weight-presets"
echo "--------------------------------------------------"
curl -s -X GET "${BASE_URL}/api/v1/simulation/weight-presets" \
  -H "Content-Type: application/json" | jq '.'
echo ""
echo ""

# Test 2: Simulate with default weights (requires auth)
echo "Test 2: POST /api/v1/simulation/simulate (default weights)"
echo "--------------------------------------------------"
echo "Note: This requires authentication. Please login first and set TOKEN variable."
echo ""
echo "Example command:"
echo 'TOKEN="your_access_token"'
echo 'curl -X POST "${BASE_URL}/api/v1/simulation/simulate" \'
echo '  -H "Content-Type: application/json" \'
echo '  -H "Authorization: Bearer ${TOKEN}" \'
echo '  -d "{\"home_team\": \"Liverpool\", \"away_team\": \"Man City\"}"'
echo ""

# Test 3: Simulate with custom weights (requires auth)
echo "Test 3: POST /api/v1/simulation/simulate (custom weights)"
echo "--------------------------------------------------"
echo "Example command with custom weights:"
echo 'curl -X POST "${BASE_URL}/api/v1/simulation/simulate" \'
echo '  -H "Content-Type: application/json" \'
echo '  -H "Authorization: Bearer ${TOKEN}" \'
echo '  -d "{"'
echo '    \"home_team\": \"Liverpool\",'
echo '    \"away_team\": \"Man City\",'
echo '    \"weights\": {'
echo '      \"user_value\": 0.8,'
echo '      \"odds\": 0.1,'
echo '      \"stats\": 0.1'
echo '    }'
echo '  }"'
echo ""

echo "=================================================="
echo "Tests Complete!"
echo "=================================================="
