#!/usr/bin/env python3
"""
Claude API Connection Test
Tests if the API key is valid and working

Usage:
    export CLAUDE_API_KEY="sk-ant-api03-your-key-here"
    python test_claude_api.py
"""

import os
import sys
from datetime import datetime

def test_claude_api():
    """Test Claude API connection"""

    print("=" * 70)
    print("Claude API Connection Test")
    print("=" * 70)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Step 1: Check API key
    api_key = os.getenv('CLAUDE_API_KEY')

    if not api_key:
        print("❌ ERROR: CLAUDE_API_KEY not found in environment variables")
        print()
        print("Please set it using:")
        print("  export CLAUDE_API_KEY='your-key-here'")
        print()
        print("Or add it to .env file:")
        print("  CLAUDE_API_KEY=your-key-here")
        return False

    # Validate key format
    if not api_key.startswith('sk-ant-api'):
        print(f"⚠️  WARNING: API key format looks incorrect")
        print(f"Expected format: sk-ant-api03-...")
        print(f"Your key starts with: {api_key[:15]}...")
        print()

    print(f"✅ API Key found")
    print(f"   Prefix: {api_key[:20]}...")
    print(f"   Length: {len(api_key)} characters")
    print()

    # Step 2: Check if anthropic package is installed
    try:
        from anthropic import Anthropic
        print("✅ anthropic package installed")
    except ImportError:
        print("❌ ERROR: anthropic package not installed")
        print()
        print("Please install it using:")
        print("  pip install anthropic")
        return False

    # Step 3: Initialize client
    try:
        client = Anthropic(api_key=api_key)
        print("✅ Client initialized successfully")
        print()
    except Exception as e:
        print(f"❌ ERROR: Failed to initialize client")
        print(f"   {str(e)}")
        return False

    # Step 4: Test API call
    print("🧪 Testing API call...")
    print("   Model: claude-sonnet-3-5-20250219")
    print("   Max tokens: 100")
    print()

    try:
        response = client.messages.create(
            model="claude-sonnet-3-5-20250219",
            max_tokens=100,
            temperature=0.7,
            messages=[
                {
                    "role": "user",
                    "content": "Say 'Hello from EPL Predictor AI Simulation!' in one enthusiastic sentence."
                }
            ]
        )

        # Display results
        print("✅ API call successful!")
        print()
        print("📊 Response Details:")
        print(f"   Model: {response.model}")
        print(f"   Stop reason: {response.stop_reason}")
        print()

        print("📊 Token Usage:")
        print(f"   Input tokens:  {response.usage.input_tokens:,}")
        print(f"   Output tokens: {response.usage.output_tokens:,}")
        print(f"   Total tokens:  {response.usage.input_tokens + response.usage.output_tokens:,}")
        print()

        # Calculate cost
        input_cost = (response.usage.input_tokens / 1_000_000) * 3.0
        output_cost = (response.usage.output_tokens / 1_000_000) * 15.0
        total_cost = input_cost + output_cost

        print("💰 Cost Breakdown:")
        print(f"   Input cost:  ${input_cost:.6f}")
        print(f"   Output cost: ${output_cost:.6f}")
        print(f"   Total cost:  ${total_cost:.6f}")
        print()

        print("💬 Claude's Response:")
        print("   " + "─" * 66)
        print(f"   {response.content[0].text}")
        print("   " + "─" * 66)
        print()

        return True

    except Exception as e:
        print(f"❌ ERROR: API call failed")
        print(f"   {str(e)}")
        print()

        if "Invalid API Key" in str(e):
            print("💡 Tip: Make sure your API key is correct")
            print("   You can generate a new key at: https://console.anthropic.com/settings/keys")
        elif "Insufficient credits" in str(e):
            print("💡 Tip: Add credits to your Anthropic account")
            print("   Visit: https://console.anthropic.com/settings/billing")
        elif "rate limit" in str(e).lower():
            print("💡 Tip: You've hit the rate limit")
            print("   Wait a moment and try again")

        return False

def test_multiple_models():
    """Test multiple Claude models"""

    try:
        from anthropic import Anthropic
    except ImportError:
        print("❌ anthropic package not installed")
        return

    api_key = os.getenv('CLAUDE_API_KEY')
    if not api_key:
        print("❌ CLAUDE_API_KEY not set")
        return

    client = Anthropic(api_key=api_key)

    models = [
        "claude-sonnet-3-5-20250219",
        "claude-sonnet-4-5-20250514"
    ]

    print("=" * 70)
    print("Testing Multiple Models")
    print("=" * 70)
    print()

    for model in models:
        print(f"Testing {model}...")
        try:
            response = client.messages.create(
                model=model,
                max_tokens=50,
                messages=[{"role": "user", "content": "Hi!"}]
            )
            print(f"✅ {model} - OK")
            print(f"   Tokens: {response.usage.input_tokens + response.usage.output_tokens}")
        except Exception as e:
            print(f"❌ {model} - FAILED")
            print(f"   Error: {str(e)[:50]}...")
        print()

if __name__ == "__main__":
    # Basic test
    success = test_claude_api()

    print("=" * 70)

    if success:
        print("✅ ALL TESTS PASSED!")
        print()
        print("🚀 You are ready to proceed with AI simulation development!")
        print()
        print("Next steps:")
        print("  1. Review DEEP_SIMULATION_ARCHITECTURE.md")
        print("  2. Start with Standard AI implementation (Phase 1)")
        print("  3. Test with real match data")
        print()

        # Optional: Test multiple models
        if len(sys.argv) > 1 and sys.argv[1] == "--full":
            print()
            test_multiple_models()
    else:
        print("❌ TESTS FAILED")
        print()
        print("Please fix the issues above and try again.")
        print()
        print("Resources:")
        print("  - Setup guide: CLAUDE_API_SETUP_GUIDE.md")
        print("  - Anthropic Console: https://console.anthropic.com")
        print("  - Documentation: https://docs.anthropic.com")

    print("=" * 70)

    sys.exit(0 if success else 1)
