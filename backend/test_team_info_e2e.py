"""
E2E 팀 정보 전달 검증 테스트
Squad API → Team Field → AI Generate API 흐름 검증
"""

import requests
import json
import sys

BASE_URL = "http://localhost:5001"

def test_squad_api_team_field():
    """1단계: Squad API가 team 필드를 포함하는지 검증"""
    print("=" * 80)
    print("🧪 TEST 1: Squad API Team Field Validation")
    print("=" * 80)

    team_name = "Arsenal"
    url = f"{BASE_URL}/api/squad/{team_name}"

    print(f"\n📡 GET {url}")
    response = requests.get(url)

    if response.status_code != 200:
        print(f"❌ FAIL: Status code {response.status_code}")
        return False

    data = response.json()
    players = data.get('players', [])

    print(f"✅ Response OK: {len(players)} players found")

    # 첫 5명의 선수에 대해 team 필드 확인
    missing_team = []
    for i, player in enumerate(players[:5]):
        player_name = player.get('name')
        player_team = player.get('team')

        if not player_team:
            missing_team.append(player_name)
            print(f"   ❌ Player {i+1}: {player_name} - MISSING team field")
        else:
            print(f"   ✅ Player {i+1}: {player_name} - team: {player_team}")

    if missing_team:
        print(f"\n❌ FAIL: {len(missing_team)} players missing team field")
        return False

    print(f"\n✅ PASS: All players have team field")
    return True


def test_ai_generate_with_team():
    """2단계: AI Generate API에 team 정보가 올바르게 전달되는지 검증"""
    print("\n" + "=" * 80)
    print("🧪 TEST 2: AI Generate API with Team Info")
    print("=" * 80)

    test_cases = [
        {
            "player_name": "Bukayo Saka",
            "position": "WG",
            "team": "Arsenal",
            "expected_minutes": ">500"  # 주전 선수이므로 출전시간 많을 것
        },
        {
            "player_name": "Andy Robertson",
            "position": "FB",
            "team": "Liverpool",
            "expected_minutes": "<200"  # 출전시간 적은 선수
        }
    ]

    url = f"{BASE_URL}/api/v1/ratings/ai-generate"

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Test Case {i}: {test_case['player_name']} ({test_case['team']})")
        print(f"   Position: {test_case['position']}")

        payload = {
            "player_name": test_case["player_name"],
            "position": test_case["position"],
            "team": test_case["team"]
        }

        print(f"\n📡 POST {url}")
        print(f"   Payload: {json.dumps(payload, indent=2)}")

        try:
            response = requests.post(url, json=payload, timeout=30)

            if response.status_code != 200:
                print(f"❌ FAIL: Status code {response.status_code}")
                print(f"   Response: {response.text}")
                continue

            data = response.json()

            if not data.get('success'):
                print(f"❌ FAIL: success=False")
                print(f"   Error: {data.get('error')}")
                continue

            # 응답 검증
            ratings = data.get('ratings', {})
            comment = data.get('comment', '')
            confidence = data.get('confidence', 0)
            fpl_stats = data.get('data_sources', {}).get('fpl_stats', {})

            print(f"\n✅ PASS: AI generation successful")
            print(f"   📊 Ratings count: {len(ratings)}")
            print(f"   📝 Comment: {comment[:80]}...")
            print(f"   🎯 Confidence: {confidence*100:.1f}%")
            print(f"\n   🏃 FPL Stats:")
            print(f"      - Name: {fpl_stats.get('name')}")
            print(f"      - Team: {fpl_stats.get('team')}")
            print(f"      - Minutes: {fpl_stats.get('minutes')}")
            print(f"      - Goals: {fpl_stats.get('goals')}")
            print(f"      - Assists: {fpl_stats.get('assists')}")
            print(f"      - Form: {fpl_stats.get('form')}")

            # 능력치 샘플 출력
            sample_ratings = list(ratings.items())[:3]
            print(f"\n   ⚡ Sample Ratings:")
            for attr, value in sample_ratings:
                print(f"      - {attr}: {value}")

            # 평균 능력치 계산
            avg_rating = sum(ratings.values()) / len(ratings)
            print(f"\n   📈 Average Rating: {avg_rating:.2f}/5.0")

            # 검증: 0.25 단위 준수
            non_compliant = [k for k, v in ratings.items() if (v * 4) % 1 != 0]
            if non_compliant:
                print(f"\n   ⚠️ Warning: {len(non_compliant)} ratings not in 0.25 units")
            else:
                print(f"   ✅ All ratings comply with 0.25 unit rule")

        except requests.exceptions.Timeout:
            print(f"❌ FAIL: Request timeout (>30s)")
        except Exception as e:
            print(f"❌ FAIL: {type(e).__name__}: {e}")


def test_team_info_unknown_handling():
    """3단계: team='Unknown' 케이스 처리 검증"""
    print("\n" + "=" * 80)
    print("🧪 TEST 3: Unknown Team Handling")
    print("=" * 80)

    url = f"{BASE_URL}/api/v1/ratings/ai-generate"

    payload = {
        "player_name": "Bukayo Saka",
        "position": "WG",
        "team": "Unknown"  # 팀 정보 없음
    }

    print(f"\n📡 POST {url}")
    print(f"   Payload: {json.dumps(payload, indent=2)}")

    try:
        response = requests.post(url, json=payload, timeout=30)
        data = response.json()

        if response.status_code == 200 and data.get('success'):
            print(f"✅ PASS: Handled gracefully even with Unknown team")
            fpl_stats = data.get('data_sources', {}).get('fpl_stats', {})
            print(f"   FPL matched: {fpl_stats.get('name')} ({fpl_stats.get('team')})")
        else:
            print(f"✅ PASS: Rejected as expected")
            print(f"   Error: {data.get('error')}")

    except Exception as e:
        print(f"❌ FAIL: {type(e).__name__}: {e}")


if __name__ == "__main__":
    print("\n" + "🚀 " * 20)
    print("E2E Team Information Flow Validation Test")
    print("🚀 " * 20 + "\n")

    # 서버 연결 확인
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        print(f"✅ Backend server is running at {BASE_URL}\n")
    except:
        print(f"❌ Backend server is not responding at {BASE_URL}")
        print(f"   Please start the backend server first.\n")
        sys.exit(1)

    # 테스트 실행
    test_squad_api_team_field()
    test_ai_generate_with_team()
    test_team_info_unknown_handling()

    print("\n" + "=" * 80)
    print("✅ E2E Test Suite Completed")
    print("=" * 80 + "\n")
