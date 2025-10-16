"""
Quick speed test for Qwen 2.5 14B vs 32B
"""

import time
from ai.qwen_client import QwenClient

def test_speed():
    """Test 14B model speed"""
    print("\n🚀 Testing Qwen 2.5 14B Speed\n")

    client = QwenClient(model="qwen2.5:14b")

    # Health check
    is_healthy, error = client.health_check()
    if not is_healthy:
        print(f"❌ Error: {error}")
        return

    print("✅ Qwen 2.5 14B loaded\n")

    # Simple test
    prompt = "Analyze: Arsenal vs Liverpool. Generate a brief scenario (2 sentences)."

    print("Testing simple prompt...")
    start = time.time()

    success, response, usage, error = client.generate(
        prompt=prompt,
        temperature=0.7,
        max_tokens=100
    )

    elapsed = time.time() - start

    if success:
        print(f"✅ Success!")
        print(f"⏱️  Time: {elapsed:.2f} seconds")
        print(f"📝 Response: {response[:200]}...")
    else:
        print(f"❌ Failed: {error}")

if __name__ == "__main__":
    test_speed()
