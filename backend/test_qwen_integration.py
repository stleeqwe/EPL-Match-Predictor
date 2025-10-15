"""
Qwen AI Integration Test
실제 Qwen AI (Ollama)를 사용한 통합 테스트
"""

import sys
import os

# 경로 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from ai.qwen_client import QwenClient
from ai.data_models import MatchInput, TeamInput
from simulation.v3.ai_integration import AIIntegrationLayer


def test_qwen_health_check():
    """Test 1: Qwen Health Check"""
    print("=== Test 1: Qwen Health Check ===\n")

    client = QwenClient()
    is_healthy, error = client.health_check()

    if is_healthy:
        print("✅ Qwen (Ollama) is healthy and ready!")
        model_info = client.get_model_info()
        print(f"\nModel Info:")
        print(f"  Provider: {model_info['provider']}")
        print(f"  Model: {model_info['model']}")
        print(f"  Parameters: {model_info['parameters']}")
        print(f"  Cost: ${model_info['cost_per_1k_tokens']}/1k tokens (FREE!)")
    else:
        print(f"❌ Qwen health check failed: {error}")
        print("\n💡 Tip: Ollama 서버가 실행 중인지 확인하세요:")
        print("   ollama serve")
        return False

    print()
    return True


def test_qwen_simple_generate():
    """Test 2: Simple Generation Test"""
    print("=== Test 2: Simple Generation Test ===\n")

    client = QwenClient()

    prompt = "다음 경기를 간단히 예측해주세요: Arsenal vs Tottenham"
    system_prompt = "당신은 EPL 경기 분석 전문가입니다."

    print(f"Prompt: {prompt}")
    print("Calling Qwen AI...")

    success, response, usage, error = client.generate(
        prompt=prompt,
        system_prompt=system_prompt,
        temperature=0.7,
        max_tokens=200
    )

    if success:
        print(f"\n✅ Generation successful!")
        print(f"\nResponse:")
        print(f"{response[:300]}...")
        print(f"\nUsage:")
        print(f"  Input tokens: ~{usage['input_tokens']:.0f}")
        print(f"  Output tokens: ~{usage['output_tokens']:.0f}")
        print(f"  Total tokens: ~{usage['total_tokens']:.0f}")
        print(f"  Cost: ${usage['cost_usd']} (FREE)")
    else:
        print(f"❌ Generation failed: {error}")
        return False

    print()
    return True


def test_qwen_with_ai_integration():
    """Test 3: Qwen + AI Integration Layer"""
    print("=== Test 3: Qwen + AI Integration Layer ===\n")

    # Qwen Client 생성
    qwen_client = QwenClient()
    ai_integration = AIIntegrationLayer(qwen_client, provider='qwen')

    # 테스트 경기 입력
    home_team = TeamInput(
        name="Arsenal",
        formation="4-3-3",
        recent_form="WWDWL",
        injuries=["Partey"],
        key_players=["Saka", "Odegaard", "Martinelli"],
        attack_strength=85.0,
        defense_strength=82.0,
    )

    away_team = TeamInput(
        name="Tottenham",
        formation="4-2-3-1",
        recent_form="LWWDW",
        injuries=["Romero"],
        key_players=["Son", "Maddison", "Kulusevski"],
        attack_strength=83.0,
        defense_strength=78.0,
    )

    match_input = MatchInput(
        match_id="QWEN_TEST_001",
        home_team=home_team,
        away_team=away_team,
        venue="Emirates Stadium",
        competition="Premier League",
        weather="Clear",
        importance="derby"
    )

    # Phase 1: 시나리오 생성
    print("Phase 1: AI 시나리오 생성 (Qwen)...")
    try:
        scenario = ai_integration.generate_scenario(match_input)
        print(f"✅ 시나리오 생성 성공!")
        print(f"  Scenario ID: {scenario.scenario_id}")
        print(f"  Description: {scenario.description[:100]}...")
        print(f"  Events: {len(scenario.events)}개")

        # 이벤트 샘플 출력
        if scenario.events:
            print(f"\n  첫 번째 이벤트:")
            event = scenario.events[0]
            print(f"    Type: {event.type}")
            print(f"    Team: {event.team}")
            print(f"    Minute Range: {event.minute_range}")
            print(f"    Probability Boost: {event.probability_boost}")
            print(f"    Reason: {event.reason}")

        return True

    except Exception as e:
        print(f"❌ 시나리오 생성 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """메인 테스트 실행"""
    print("\n" + "="*60)
    print("Qwen AI Integration Test")
    print("="*60 + "\n")

    # Test 1: Health Check
    if not test_qwen_health_check():
        print("\n⚠️  Ollama 서버가 실행되지 않았습니다. 테스트 중단.")
        return

    # Test 2: Simple Generation
    if not test_qwen_simple_generate():
        print("\n⚠️  Simple generation 실패. 테스트 중단.")
        return

    # Test 3: AI Integration
    if not test_qwen_with_ai_integration():
        print("\n⚠️  AI Integration 테스트 실패.")
        return

    # 성공!
    print("\n" + "="*60)
    print("✅ 모든 Qwen AI 통합 테스트 통과!")
    print("="*60)
    print("\n🎉 실제 Qwen AI를 사용한 시뮬레이션 준비 완료!")
    print("\n다음 단계:")
    print("  1. Match Simulator V3에서 provider='qwen' 사용")
    print("  2. 전체 시뮬레이션 실행 (Phase 1-7)")
    print("  3. 실제 AI 분석 결과 확인")


if __name__ == "__main__":
    main()
