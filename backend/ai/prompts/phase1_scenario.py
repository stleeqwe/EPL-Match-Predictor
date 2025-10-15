"""
Phase 1 Prompt: Scenario Generation
경기 입력 정보 → AI 시나리오 생성

This prompt guides the AI to generate a realistic match scenario
with event sequences and probability boosts for simulation.
"""

from typing import Dict, Any
from ai.data_models import MatchInput


# ==========================================================================
# System Prompt
# ==========================================================================

SYSTEM_PROMPT = """당신은 EPL(English Premier League) 전문 축구 분석가입니다.

주어진 경기 정보를 바탕으로 **현실적이고 구체적인 경기 시나리오**를 생성하세요.

## 시나리오 작성 가이드라인

### 1. 이벤트 타입 (허용되는 타입만 사용)
- `wing_breakthrough`: 측면 돌파 (윙어가 측면을 뚫고 크로스)
- `goal`: 득점 시도 강화
- `corner`: 코너킥 기회
- `set_piece`: 세트피스 (프리킥, 코너킥 등)
- `counter_attack`: 역습 기회
- `central_penetration`: 중앙 돌파
- `shot`: 슛 시도

### 2. 이벤트 구성 요소
각 이벤트는 다음을 포함해야 합니다:
- **minute_range**: [시작분, 종료분] (예: [10, 25])
  - 범위: 0-90분
  - 시작 ≤ 종료
  - 경기 흐름을 고려한 현실적 타이밍
- **type**: 위 7개 타입 중 하나
- **team**: 'home' 또는 'away'
- **probability_boost**: 1.0-3.0 사이의 배수
  - 1.0-1.5: 약한 영향
  - 1.5-2.0: 중간 영향
  - 2.0-3.0: 강한 영향
- **actor**: 주요 선수 이름 (선택사항)
- **reason**: 부스트 이유 (최근 폼, 전술적 우위 등)

### 3. 시나리오 구조
- **이벤트 수**: 5-7개 권장
- **시간 분배**: 전반(0-45분), 후반(45-90분) 균형
- **팀 분배**: 양 팀 모두 이벤트 포함 (일방적이지 않게)
- **현실성**: 팀 폼, 전술, 선수 능력을 반영

### 4. 출력 형식
**반드시 JSON 형식으로만 출력**하세요:

```json
{
  "scenario_id": "EPL_2024_MATCH_XXX",
  "description": "시나리오 설명 (1-2 문장)",
  "events": [
    {
      "minute_range": [10, 25],
      "type": "wing_breakthrough",
      "team": "home",
      "probability_boost": 2.5,
      "actor": "Son Heung-min",
      "reason": "최근 5경기 3골 1어시스트, 측면 돌파 강세"
    },
    {
      "minute_range": [15, 30],
      "type": "goal",
      "team": "home",
      "probability_boost": 2.0,
      "reason": "초반 압박으로 홈 어드밴티지 극대화"
    }
  ]
}
```

## 중요 유의사항
- 텍스트 설명 없이 JSON만 출력
- 모든 필수 필드 포함
- probability_boost는 1.0-3.0 범위 엄수
- minute_range는 [시작, 종료] 형태
- 이벤트 타입은 위 7개 중 하나만 사용
"""


# ==========================================================================
# User Prompt Template
# ==========================================================================

USER_PROMPT_TEMPLATE = """# 경기 정보

## 홈팀: {home_team_name}
- **포메이션**: {home_team_formation}
- **최근 폼**: {home_team_recent_form}
- **부상자**: {home_team_injuries}
- **주요 선수**: {home_team_key_players}
- **팀 전력** (Domain 지식):
  - 공격력: {home_team_attack_strength}/100
  - 수비력: {home_team_defense_strength}/100
  - 압박 강도: {home_team_press_intensity}/100
  - 빌드업 스타일: {home_team_buildup_style}

## 원정팀: {away_team_name}
- **포메이션**: {away_team_formation}
- **최근 폼**: {away_team_recent_form}
- **부상자**: {away_team_injuries}
- **주요 선수**: {away_team_key_players}
- **팀 전력** (Domain 지식):
  - 공격력: {away_team_attack_strength}/100
  - 수비력: {away_team_defense_strength}/100
  - 압박 강도: {away_team_press_intensity}/100
  - 빌드업 스타일: {away_team_buildup_style}

## 경기 세부 정보
- **경기장**: {venue}
- **대회**: {competition}
- **날씨**: {weather}
- **중요도**: {importance}

# 요구사항
위 정보를 바탕으로 이 경기의 **가능한 시나리오**를 생성하세요.

**특히 주의할 점**:
1. 팀 전력 수치를 반영하여 현실적인 시나리오 작성
2. 공격력이 높은 팀은 더 많은 공격 이벤트 생성
3. 수비력이 높은 팀은 상대의 probability_boost를 낮게 설정
4. 압박 강도가 높은 팀은 counter_press, 역습 차단 이벤트 추가
5. 빌드업 스타일(possession/direct/balanced)에 맞는 전개 패턴 반영

**출력**: JSON 형식 시나리오 (다른 텍스트 없이)
"""


# ==========================================================================
# Few-Shot Examples
# ==========================================================================

FEW_SHOT_EXAMPLES = """
## 예시 1: 강팀 vs 약팀

**입력**:
- 홈팀: Manchester City (폼: WWWWW, 공격적 4-3-3)
- 원정팀: Sheffield United (폼: LLLDD, 수비적 5-4-1)

**출력**:
```json
{
  "scenario_id": "CITY_DOM_001",
  "description": "맨시티가 압도적 점유율로 초반부터 주도권을 잡고 측면 공격을 집중하는 시나리오",
  "events": [
    {
      "minute_range": [5, 20],
      "type": "wing_breakthrough",
      "team": "home",
      "probability_boost": 2.8,
      "actor": "Phil Foden",
      "reason": "상대 수비진이 5백으로 밀집, 측면 공간 활용"
    },
    {
      "minute_range": [10, 25],
      "type": "goal",
      "team": "home",
      "probability_boost": 2.5,
      "reason": "초반 압박으로 홈 어드밴티지, 공격력 차이"
    },
    {
      "minute_range": [30, 45],
      "type": "corner",
      "team": "home",
      "probability_boost": 2.2,
      "reason": "지속적인 압박으로 코너킥 기회 증가"
    },
    {
      "minute_range": [50, 65],
      "type": "central_penetration",
      "team": "home",
      "probability_boost": 2.0,
      "actor": "Kevin De Bruyne",
      "reason": "후반 교체로 중앙 돌파력 강화"
    },
    {
      "minute_range": [70, 85],
      "type": "counter_attack",
      "team": "away",
      "probability_boost": 1.8,
      "reason": "대량 실점 후 역습 시도"
    }
  ]
}
```

## 예시 2: 라이벌전 (접전)

**입력**:
- 홈팀: Arsenal (폼: WWDWL, 공격적 4-3-3)
- 원정팀: Tottenham (폼: LWWDW, 공격적 4-2-3-1)
- 중요도: derby

**출력**:
```json
{
  "scenario_id": "NLD_DERBY_001",
  "description": "양 팀이 공격적으로 맞불을 놓는 박진감 넘치는 더비 경기 시나리오",
  "events": [
    {
      "minute_range": [8, 22],
      "type": "wing_breakthrough",
      "team": "home",
      "probability_boost": 2.3,
      "actor": "Bukayo Saka",
      "reason": "더비 경기에서 홈 초반 압박, 사카의 측면 능력"
    },
    {
      "minute_range": [15, 28],
      "type": "goal",
      "team": "home",
      "probability_boost": 2.0,
      "reason": "홈 관중 압박 + 초반 기세"
    },
    {
      "minute_range": [32, 45],
      "type": "counter_attack",
      "team": "away",
      "probability_boost": 2.4,
      "actor": "Son Heung-min",
      "reason": "실점 후 역습 전환, 손흥민 스피드 활용"
    },
    {
      "minute_range": [38, 45],
      "type": "goal",
      "team": "away",
      "probability_boost": 2.2,
      "reason": "전반 막판 역습 득점 가능성"
    },
    {
      "minute_range": [55, 68],
      "type": "set_piece",
      "team": "home",
      "probability_boost": 2.0,
      "reason": "후반 압박으로 세트피스 기회"
    },
    {
      "minute_range": [75, 88],
      "type": "wing_breakthrough",
      "team": "away",
      "probability_boost": 2.1,
      "reason": "홈팀 체력 저하, 원정팀 후반 역습"
    }
  ]
}
```

## 예시 3: 중위권 대결

**입력**:
- 홈팀: Brighton (폼: WDWLD, 점유형 4-2-3-1)
- 원정팀: Brentford (폼: DWLWW, 직접형 3-5-2)

**출력**:
```json
{
  "scenario_id": "MID_TABLE_001",
  "description": "브라이튼이 점유율로 주도하지만 브렌트포드의 역습이 위협적인 시나리오",
  "events": [
    {
      "minute_range": [12, 28],
      "type": "central_penetration",
      "team": "home",
      "probability_boost": 1.9,
      "reason": "점유형 전술로 중앙 빌드업 우세"
    },
    {
      "minute_range": [18, 32],
      "type": "goal",
      "team": "home",
      "probability_boost": 1.7,
      "reason": "점유율 우세로 득점 기회 증가"
    },
    {
      "minute_range": [40, 55],
      "type": "counter_attack",
      "team": "away",
      "probability_boost": 2.2,
      "reason": "직접형 플레이로 빠른 전환 공격"
    },
    {
      "minute_range": [48, 58],
      "type": "goal",
      "team": "away",
      "probability_boost": 1.9,
      "reason": "역습 득점 가능성"
    },
    {
      "minute_range": [65, 78],
      "type": "set_piece",
      "team": "home",
      "probability_boost": 1.8,
      "reason": "후반 압박으로 세트피스 기회"
    }
  ]
}
```
"""


# ==========================================================================
# Helper Functions
# ==========================================================================

def generate_phase1_prompt(match_input: MatchInput, include_examples: bool = True) -> tuple[str, str]:
    """
    Phase 1 프롬프트 생성

    Args:
        match_input: 경기 입력 정보
        include_examples: Few-shot examples 포함 여부

    Returns:
        (system_prompt, user_prompt) 튜플
    """
    # User prompt 생성
    match_dict = match_input.to_dict()

    user_prompt = USER_PROMPT_TEMPLATE.format(
        home_team_name=match_dict['home_team']['name'],
        home_team_formation=match_dict['home_team']['formation'],
        home_team_recent_form=match_dict['home_team']['recent_form'],
        home_team_injuries=match_dict['home_team']['injuries'],
        home_team_key_players=match_dict['home_team']['key_players'],
        home_team_attack_strength=match_dict['home_team']['attack_strength'],
        home_team_defense_strength=match_dict['home_team']['defense_strength'],
        home_team_press_intensity=match_dict['home_team']['press_intensity'],
        home_team_buildup_style=match_dict['home_team']['buildup_style'],
        away_team_name=match_dict['away_team']['name'],
        away_team_formation=match_dict['away_team']['formation'],
        away_team_recent_form=match_dict['away_team']['recent_form'],
        away_team_injuries=match_dict['away_team']['injuries'],
        away_team_key_players=match_dict['away_team']['key_players'],
        away_team_attack_strength=match_dict['away_team']['attack_strength'],
        away_team_defense_strength=match_dict['away_team']['defense_strength'],
        away_team_press_intensity=match_dict['away_team']['press_intensity'],
        away_team_buildup_style=match_dict['away_team']['buildup_style'],
        venue=match_dict['venue'],
        competition=match_dict['competition'],
        weather=match_dict['weather'],
        importance=match_dict['importance'],
    )

    # System prompt (예시 포함 여부 결정)
    if include_examples:
        system_prompt = SYSTEM_PROMPT + "\n\n" + FEW_SHOT_EXAMPLES
    else:
        system_prompt = SYSTEM_PROMPT

    return system_prompt, user_prompt


def estimate_token_count(text: str) -> int:
    """
    토큰 수 추정 (간단한 approximation)

    Args:
        text: 텍스트

    Returns:
        예상 토큰 수
    """
    # 간단한 추정: 영어 단어 ~1.3토큰, 한글 글자 ~1.5토큰
    words = text.split()
    return int(len(words) * 1.3)


# ==========================================================================
# Testing
# ==========================================================================

def test_phase1_prompt():
    """Phase 1 프롬프트 테스트"""
    print("=== Phase 1 Prompt 테스트 ===\n")

    # 테스트 데이터 생성
    from ai.data_models import TeamInput

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
        match_id="EPL_2024_NLD_001",
        home_team=home_team,
        away_team=away_team,
        venue="Emirates Stadium",
        competition="Premier League",
        weather="Clear",
        importance="derby"
    )

    # 프롬프트 생성
    print("Test 1: 프롬프트 생성 (예시 포함)")
    system_prompt, user_prompt = generate_phase1_prompt(match_input, include_examples=True)

    print(f"  System Prompt 길이: {len(system_prompt)} 문자")
    print(f"  User Prompt 길이: {len(user_prompt)} 문자")
    print(f"  예상 토큰 수 (System): {estimate_token_count(system_prompt)}")
    print(f"  예상 토큰 수 (User): {estimate_token_count(user_prompt)}")
    print(f"  예상 총 토큰: {estimate_token_count(system_prompt + user_prompt)}")
    print(f"  ✅ 프롬프트 생성 성공\n")

    # 프롬프트 내용 일부 출력
    print("Test 2: User Prompt 샘플")
    print("-" * 60)
    print(user_prompt[:500] + "...")
    print("-" * 60)
    print(f"  ✅ User Prompt 형식 확인\n")

    # 예시 없이 생성
    print("Test 3: 프롬프트 생성 (예시 제외)")
    system_prompt_no_ex, user_prompt_no_ex = generate_phase1_prompt(match_input, include_examples=False)
    print(f"  예상 토큰 수 (예시 제외): {estimate_token_count(system_prompt_no_ex + user_prompt_no_ex)}")
    print(f"  ✅ 간단한 버전 생성 성공\n")

    # 검증 기준
    total_tokens = estimate_token_count(system_prompt + user_prompt)
    print("=" * 60)
    print("검증 결과:")
    if total_tokens < 2000:
        print(f"  ✅ 토큰 수 목표 달성: {total_tokens} < 2,000")
    else:
        print(f"  ⚠️ 토큰 수 초과: {total_tokens} >= 2,000 (조정 필요)")

    print("=" * 60)
    print("✅ Phase 1 Prompt 테스트 완료!")
    print("=" * 60)


if __name__ == "__main__":
    test_phase1_prompt()
