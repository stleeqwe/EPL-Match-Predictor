#!/usr/bin/env python3
"""
Simple Claude API Test
"""

import os
import anthropic

# Get API key from environment variable
api_key = os.getenv('CLAUDE_API_KEY')
if not api_key:
    raise ValueError("CLAUDE_API_KEY environment variable not set")

print("=" * 70)
print("Simple Claude API Test")
print("=" * 70)
print()

print(f"✅ API Key: {api_key[:20]}...")
print()

try:
    # Initialize client
    client = anthropic.Anthropic(api_key=api_key)
    print("✅ Client initialized")
    print()

    # Test API call - try multiple models
    models_to_try = [
        "claude-3-opus-20240229",
        "claude-3-sonnet-20240229",
        "claude-3-haiku-20240307",
        "claude-3-5-sonnet-20241022"
    ]

    message = None
    for model_name in models_to_try:
        print(f"🧪 Trying model: {model_name}...")
        try:
            message = client.messages.create(
                model=model_name,
                max_tokens=100,
                messages=[
                    {
                        "role": "user",
                        "content": "Say 'Hello from EPL Predictor!' in one sentence."
                    }
                ]
            )
            print(f"✅ Success with {model_name}!")
            break
        except Exception as e:
            print(f"❌ Failed: {str(e)[:80]}")
            continue

    if not message:
        raise Exception("No models available with this API key")

    print("✅ API call successful!")
    print()
    print("📊 Response:")
    print(f"   Model: {message.model}")
    print(f"   Input tokens: {message.usage.input_tokens}")
    print(f"   Output tokens: {message.usage.output_tokens}")
    print()
    print("💬 Claude says:")
    print(f"   {message.content[0].text}")
    print()

    # Calculate cost
    cost = (message.usage.input_tokens / 1_000_000 * 3.0) + \
           (message.usage.output_tokens / 1_000_000 * 15.0)
    print(f"💰 Cost: ${cost:.6f}")
    print()
    print("=" * 70)
    print("✅ SUCCESS! Claude API is working perfectly!")
    print("=" * 70)

except Exception as e:
    print(f"❌ ERROR: {e}")
    print()
    import traceback
    traceback.print_exc()
