#!/usr/bin/env python3
"""
AI Rating Generator - Prompt 테스트 스크립트
선수 능력치 생성 AI 프롬프트 검증
"""

import sys
import os
import json
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(__file__))

from ai.ai_factory import get_ai_client

# 포지션별 능력치 정의 (frontend/src/config/positionAttributes.js와 동일)
POSITION_ATTRIBUTES = {
    'GK': {
        'name': '골키퍼',
        'attributes': [
            {'key': 'reflexes', 'label': '반응속도', 'weight': 0.17},
            {'key': 'positioning', 'label': '포지셔닝', 'weight': 0.17},
            {'key': 'handling', 'label': '핸들링', 'weight': 0.15},
            {'key': 'one_on_one', 'label': '1:1 대응', 'weight': 0.14},
            {'key': 'aerial_control', 'label': '공중볼 지배력', 'weight': 0.12},
            {'key': 'buildup', 'label': '빌드업 능력', 'weight': 0.13},
            {'key': 'leadership_communication', 'label': '리더십&의사소통', 'weight': 0.07},
            {'key': 'long_kick', 'label': '롱볼 킥력', 'weight': 0.05}
        ]
    },
    'ST': {
        'name': '스트라이커',
        'attributes': [
            {'key': 'finishing', 'label': '골 결정력', 'weight': 0.15},
            {'key': 'shot_power', 'label': '슈팅 정확도 & 파워', 'weight': 0.14},
            {'key': 'composure', 'label': '침착성', 'weight': 0.12},
            {'key': 'off_ball_movement', 'label': '오프더볼 무브먼트', 'weight': 0.13},
            {'key': 'hold_up_play', 'label': '홀딩 & 연결', 'weight': 0.11},
            {'key': 'heading', 'label': '헤딩 득점력', 'weight': 0.09},
            {'key': 'acceleration', 'label': '가속력', 'weight': 0.08},
            {'key': 'physicality_balance', 'label': '피지컬 & 밸런스', 'weight': 0.11},
            {'key': 'jumping', 'label': '점프력', 'weight': 0.07}
        ]
    },
    'WG': {
        'name': '윙어',
        'attributes': [
            {'key': 'speed_dribbling', 'label': '스피드 드리블', 'weight': 0.12},
            {'key': 'one_on_one_beating', 'label': '1:1 제치기', 'weight': 0.11},
            {'key': 'speed', 'label': '스피드', 'weight': 0.10},
            {'key': 'acceleration', 'label': '가속력', 'weight': 0.09},
            {'key': 'crossing_accuracy', 'label': '크로스 정확도', 'weight': 0.10},
            {'key': 'shooting_accuracy', 'label': '슈팅 정확도', 'weight': 0.09},
            {'key': 'agility_direction_change', 'label': '민첩성 & 방향 전환', 'weight': 0.10},
            {'key': 'cutting_in', 'label': '컷인 무브', 'weight': 0.08},
            {'key': 'creativity', 'label': '창의성', 'weight': 0.06},
            {'key': 'defensive_contribution', 'label': '수비 가담 & 압박', 'weight': 0.07},
            {'key': 'cutback_pass', 'label': '컷백 패스', 'weight': 0.04},
            {'key': 'link_up_play', 'label': '연계 플레이', 'weight': 0.04}
        ]
    },
    'CM': {
        'name': '중앙 미드필더',
        'attributes': [
            {'key': 'stamina', 'label': '지구력', 'weight': 0.11},
            {'key': 'ball_possession_circulation', 'label': '볼 소유 & 순환', 'weight': 0.11},
            {'key': 'pass_accuracy_vision', 'label': '패스 정확도 & 시야', 'weight': 0.13},
            {'key': 'transition', 'label': '전환 플레이', 'weight': 0.10},
            {'key': 'dribbling_press_resistance', 'label': '드리블 & 탈압박', 'weight': 0.10},
            {'key': 'space_creation', 'label': '공간 창출/침투', 'weight': 0.09},
            {'key': 'defensive_contribution', 'label': '수비 가담', 'weight': 0.09},
            {'key': 'ball_retention', 'label': '볼 키핑', 'weight': 0.07},
            {'key': 'long_shot', 'label': '중거리 슈팅', 'weight': 0.06},
            {'key': 'agility_acceleration', 'label': '민첩성 & 가속력', 'weight': 0.09},
            {'key': 'physicality', 'label': '피지컬', 'weight': 0.05}
        ]
    }
}


def build_system_prompt():
    """시스템 프롬프트 생성"""
    return """당신은 EPL 선수 스카우팅 전문가입니다.
선수의 통계 데이터를 기반으로 세밀한 능력치를 평가합니다.

평가 기준 (0.0-5.0 스케일):
- 0.0-1.0: 매우 부족
- 1.0-2.0: 부족
- 2.0-3.0: 평균
- 3.0-4.0: 우수
- 4.0-5.0: 월드클래스

중요:
1. 반드시 JSON 형식으로만 응답
2. 능력치는 0.25 단위로만 설정 (예: 3.00, 3.25, 3.50, 3.75, 4.00)
3. FPL 통계를 근거로 합리적 추론
4. 코멘트는 100자 이내"""


def build_user_prompt(player_name, position, team, fpl_stats):
    """유저 프롬프트 생성"""

    position_data = POSITION_ATTRIBUTES.get(position)
    if not position_data:
        raise ValueError(f"Unknown position: {position}")

    attributes = position_data['attributes']

    # 능력치 목록 (key: label 형태)
    attr_list = '\n'.join([f"  - {attr['key']}: {attr['label']} (가중치 {attr['weight']:.0%})"
                           for attr in attributes])

    prompt = f"""# 선수 정보
- 이름: {player_name}
- 포지션: {position_data['name']} ({position})
- 팀: {team}

# FPL 통계 (2024/25 시즌)
- 출전 시간: {fpl_stats.get('minutes', 0)}분
- 골: {fpl_stats.get('goals', 0)}개
- 어시스트: {fpl_stats.get('assists', 0)}개
- 폼: {fpl_stats.get('form', '0.0')}/10
- 선발률: {fpl_stats.get('selected_by', '0.0')}%
- 보너스: {fpl_stats.get('bonus', 0)}점

# 평가 항목 ({len(attributes)}개)
{attr_list}

# 요구사항
1. 각 능력치를 0.0-5.0 스케일로 평가 (0.25 단위만)
2. FPL 통계를 근거로 합리적 추론
3. 100자 이내 코멘트 작성

# 출력 형식 (JSON만)
{{
  "ratings": {{
    "{attributes[0]['key']}": 4.25,
    "{attributes[1]['key']}": 3.75,
    ...
  }},
  "comment": "100자 이내 평가",
  "reasoning": "평가 근거 간략히"
}}

JSON만 반환하세요."""

    return prompt


def test_ai_rating_generation(player_name, position, team, fpl_stats):
    """AI 능력치 생성 테스트"""

    print("=" * 100)
    print(f"🧪 AI Rating Generation Test: {player_name} ({position})")
    print("=" * 100)

    # 1. 프롬프트 생성
    system_prompt = build_system_prompt()
    user_prompt = build_user_prompt(player_name, position, team, fpl_stats)

    print("\n📋 SYSTEM PROMPT:")
    print("-" * 100)
    print(system_prompt)

    print("\n📋 USER PROMPT:")
    print("-" * 100)
    print(user_prompt)

    # 2. AI 호출
    print("\n🤖 Calling Gemini AI...")
    ai_client = get_ai_client()

    success, response_text, usage, error = ai_client.generate(
        prompt=user_prompt,
        system_prompt=system_prompt,
        temperature=0.7,
        max_tokens=2000
    )

    if not success:
        print(f"\n❌ AI 호출 실패: {error}")
        return None

    print(f"\n✅ AI 응답 받음 ({usage['total_tokens']} tokens)")
    print(f"   - Input: {usage['input_tokens']} tokens")
    print(f"   - Output: {usage['output_tokens']} tokens")
    if 'thinking_tokens' in usage:
        print(f"   - Thinking: {usage['thinking_tokens']} tokens")

    # 3. 응답 파싱
    print("\n📄 RAW RESPONSE:")
    print("-" * 100)
    print(response_text)

    try:
        # JSON 추출
        response_clean = response_text.strip()
        if '```json' in response_clean:
            json_start = response_clean.find('```json') + 7
            json_end = response_clean.find('```', json_start)
            response_clean = response_clean[json_start:json_end].strip()
        elif '```' in response_clean:
            json_start = response_clean.find('```') + 3
            json_end = response_clean.find('```', json_start)
            response_clean = response_clean[json_start:json_end].strip()

        data = json.loads(response_clean)

        # 4. 검증
        print("\n✅ JSON 파싱 성공!")
        print("\n📊 생성된 능력치:")
        print("-" * 100)

        ratings = data.get('ratings', {})
        position_attrs = POSITION_ATTRIBUTES[position]['attributes']

        # 능력치 출력
        for attr in position_attrs:
            value = ratings.get(attr['key'], 0)
            bar = '█' * int(value * 10)
            print(f"  {attr['label']:20s} [{value:.2f}/5.0] {bar}")

        # 능력치 합계 검증
        total_rating = sum(ratings.values())
        avg_rating = total_rating / len(ratings) if ratings else 0

        print(f"\n📈 통계:")
        print(f"  - 평균 능력치: {avg_rating:.2f}/5.0")
        print(f"  - 최고 능력치: {max(ratings.values()):.2f}")
        print(f"  - 최저 능력치: {min(ratings.values()):.2f}")

        print(f"\n💬 코멘트:")
        print(f"  {data.get('comment', 'N/A')}")

        print(f"\n🧠 추론 근거:")
        print(f"  {data.get('reasoning', 'N/A')}")

        # 5. 0.25 단위 검증
        print("\n🔍 0.25 단위 검증:")
        valid = True
        for key, value in ratings.items():
            if round(value * 4) != value * 4:
                print(f"  ❌ {key}: {value} (0.25 단위 아님)")
                valid = False

        if valid:
            print("  ✅ 모든 능력치가 0.25 단위입니다")

        return data

    except json.JSONDecodeError as e:
        print(f"\n❌ JSON 파싱 실패: {e}")
        print(f"   Response: {response_text[:500]}...")
        return None
    except Exception as e:
        print(f"\n❌ 검증 실패: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    print("\n" + "=" * 100)
    print("🧪 AI Rating Generator - Prompt Test")
    print("=" * 100 + "\n")

    # 테스트 케이스 1: Bukayo Saka (윙어)
    print("\n" + "🎯" * 50)
    test_ai_rating_generation(
        player_name="Bukayo Saka",
        position="WG",
        team="Arsenal",
        fpl_stats={
            'minutes': 2500,
            'goals': 8,
            'assists': 10,
            'form': '7.5',
            'selected_by': '35.2',
            'bonus': 15
        }
    )

    # 테스트 케이스 2: Erling Haaland (스트라이커)
    print("\n\n" + "🎯" * 50)
    test_ai_rating_generation(
        player_name="Erling Haaland",
        position="ST",
        team="Man City",
        fpl_stats={
            'minutes': 2800,
            'goals': 27,
            'assists': 5,
            'form': '8.5',
            'selected_by': '45.8',
            'bonus': 25
        }
    )

    # 테스트 케이스 3: Kevin De Bruyne (중앙 미드필더)
    print("\n\n" + "🎯" * 50)
    test_ai_rating_generation(
        player_name="Kevin De Bruyne",
        position="CM",
        team="Man City",
        fpl_stats={
            'minutes': 2200,
            'goals': 4,
            'assists': 18,
            'form': '7.8',
            'selected_by': '28.5',
            'bonus': 18
        }
    )

    print("\n" + "=" * 100)
    print("✅ 테스트 완료!")
    print("=" * 100 + "\n")
