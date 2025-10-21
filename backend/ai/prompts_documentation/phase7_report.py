"""
Phase 7 Prompt: Final Report Generation
최종 경기 리포트 생성 (마크다운)

This prompt generates a comprehensive match report in markdown format,
including summary, timeline, statistics, and tactical analysis.
"""

from typing import Dict, Any, List
from ai.data_models import MatchInput, SimulationResult


# ==========================================================================
# System Prompt
# ==========================================================================

SYSTEM_PROMPT = """당신은 EPL 경기 분석 전문 기자입니다.

시뮬레이션된 경기 결과를 바탕으로 **상세한 경기 리포트**를 작성하세요.

## 리포트 구조 (마크다운)

### 1. 경기 요약 (Summary)
- 3-4문장으로 경기 흐름 요약
- 승부의 핵심 요인 언급
- 객관적이고 흥미로운 서술

### 2. 주요 순간 (Key Moments)
- 득점 이벤트를 시간순으로 나열
- 각 골의 상황 설명
- 이모지 활용 (⚽, 🔥, ⚡ 등)

### 3. 팀별 통계 (Team Statistics)
- 슛, 온타겟, 점유율 등을 표로 정리
- 양 팀 비교

### 4. 선수 평가 (Player Ratings) - 선택사항
- 주요 선수 3-4명 평가
- 평점 (0-10점) 및 간단한 코멘트

### 5. 전술 분석 (Tactical Analysis)
- 포메이션 및 전술 분석
- 승부의 전술적 요인
- 2-3개 인사이트

### 6. 결론 (Conclusion)
- 1-2문장으로 경기 마무리
- 향후 전망 또는 의미

## 스타일 가이드
- **어조**: 전문적이면서도 흥미롭게
- **길이**: 중간 (너무 길거나 짧지 않게)
- **객관성**: 양 팀을 공정하게 다룸
- **데이터 기반**: 통계를 근거로 분석

## 출력 형식
**반드시 마크다운으로만 출력**하세요. JSON이나 다른 형식 사용 금지.

## 예시 구조

```markdown
# 경기 리포트: Arsenal 2-1 Tottenham

**일시**: 2024-10-16 | **경기장**: Emirates Stadium | **대회**: Premier League

---

## 📊 경기 요약

Arsenal이 홈에서 라이벌 Tottenham을 2-1로 꺾으며 귀중한 3점을 획득했다.
전반 초반부터 측면 공격으로 주도권을 잡은 홈팀은 Saka와 Martinelli의 활약으로
2골을 넣었고, Tottenham의 후반 만회골에도 불구하고 승리를 지켜냈다.
홈팀의 공격적 전술과 원정팀의 역습 사이 치열한 공방이 펼쳐진 명승부였다.

---

## ⚽ 주요 순간

- **18분** ⚡ **Arsenal 1-0** - Saka의 측면 돌파 후 크로스, Martinelli 헤더 골
- **34분** 🔥 **Arsenal 2-0** - Odegaard의 중거리 슛, 골키퍼 손끝을 스쳐 골인
- **72분** ⚽ **Arsenal 2-1** - Son의 역습 돌파 후 마무리, Tottenham 추격골

---

## 📈 팀별 통계

| 항목 | Arsenal | Tottenham |
|------|---------|-----------|
| 슛 | 15 | 12 |
| 온타겟 | 7 | 5 |
| 점유율 | 58% | 42% |
| 코너킥 | 6 | 4 |
| 파울 | 11 | 13 |

---

## 🎯 선수 평가

### Arsenal
- **Bukayo Saka**: 8.5/10 - 1어시스트, 측면 돌파로 상대 수비진 괴롭힘
- **Martin Odegaard**: 8.0/10 - 1골, 중원 장악력 뛰어남
- **Gabriel Martinelli**: 7.5/10 - 1골, 적극적인 움직임

### Tottenham
- **Son Heung-min**: 8.0/10 - 1골, 역습에서 위협적
- **James Maddison**: 7.0/10 - 창의적인 플레이메이킹
- **Cristian Romero**: 6.5/10 - 수비 안정감 부족

---

## 🧠 전술 분석

Arsenal의 4-3-3 vs Tottenham의 4-2-3-1 대결에서 홈팀의 측면 공격이 승부의
핵심이었다. Arteta 감독은 양 윙어를 높이 배치해 상대 풀백을 고립시켰고,
이것이 전반 2골로 이어졌다.

Tottenham은 후반 들어 라인을 올리며 압박을 강화했으나, Arsenal의 역습 위협으로
인해 완전한 공세를 펼치기 어려웠다. Son의 개인 기량으로 1골을 만회했지만,
시간이 부족했다.

홈팀의 58% 점유율과 15개 슛은 경기 장악력을 보여주는 수치다. 원정팀은 역습
기회를 더 효율적으로 활용했다면 다른 결과가 나올 수 있었다.

---

## 🏆 결론

Arsenal이 라이벌전에서 중요한 승리를 거두며 리그 상위권 경쟁에서 우위를
점했다. Tottenham은 아쉬운 패배지만 후반 경기력은 긍정적이었다.
```
"""


# ==========================================================================
# User Prompt Template
# ==========================================================================

USER_PROMPT_TEMPLATE = """# 경기 정보

## 기본 정보
- **홈팀**: {home_team}
- **원정팀**: {away_team}
- **최종 스코어**: {final_score}
- **경기장**: {venue}
- **대회**: {competition}

## 이벤트 타임라인

{event_timeline}

## 경기 통계

```json
{stats}
```

## 팀 정보

### 홈팀 ({home_team})
- **포메이션**: {home_formation}
- **최근 폼**: {home_form}
- **주요 선수**: {home_key_players}

### 원정팀 ({away_team})
- **포메이션**: {away_formation}
- **최근 폼**: {away_form}
- **주요 선수**: {away_key_players}

---

# 요구사항

위 정보를 바탕으로 **마크다운 형식의 상세한 경기 리포트**를 작성하세요.

**출력**: 마크다운 리포트 (JSON이나 다른 형식 사용 금지)
"""


# ==========================================================================
# Helper Functions
# ==========================================================================

def generate_phase7_prompt(
    match_input: MatchInput,
    final_result: SimulationResult
) -> tuple[str, str]:
    """
    Phase 7 프롬프트 생성

    Args:
        match_input: 경기 입력 정보
        final_result: 최종 시뮬레이션 결과

    Returns:
        (system_prompt, user_prompt) 튜플
    """
    import json

    # 이벤트 타임라인 생성
    timeline = _create_event_timeline(final_result.events)

    # match_input을 dict로 변환
    match_dict = match_input.to_dict()

    # User prompt 생성
    user_prompt = USER_PROMPT_TEMPLATE.format(
        home_team=match_input.home_team.name,
        away_team=match_input.away_team.name,
        final_score=f"{final_result.final_score['home']}-{final_result.final_score['away']}",
        venue=match_input.venue,
        competition=match_input.competition,
        event_timeline=timeline,
        stats=json.dumps(final_result.stats, indent=2, ensure_ascii=False),
        home_formation=match_input.home_team.formation,
        home_form=match_input.home_team.recent_form,
        home_key_players=', '.join(match_input.home_team.key_players[:3]),
        away_formation=match_input.away_team.formation,
        away_form=match_input.away_team.recent_form,
        away_key_players=', '.join(match_input.away_team.key_players[:3]),
    )

    return SYSTEM_PROMPT, user_prompt


def _create_event_timeline(events: List[Dict]) -> str:
    """
    이벤트 타임라인 생성 (텍스트)

    Args:
        events: 이벤트 리스트

    Returns:
        타임라인 텍스트
    """
    if not events:
        return "이벤트 기록 없음"

    # 득점 이벤트만 필터링
    goal_events = [e for e in events if e.get('type') == 'goal']

    if not goal_events:
        return f"총 {len(events)}개 이벤트 발생 (득점 없음)"

    timeline_lines = []
    for event in goal_events:
        minute = event.get('minute', '?')
        team = event.get('team', '?')
        team_name = team.capitalize()  # home → Home
        timeline_lines.append(f"- **{minute}분**: {team_name} 득점 ⚽")

    return "\n".join(timeline_lines)


def estimate_token_count(text: str) -> int:
    """
    토큰 수 추정

    Args:
        text: 텍스트

    Returns:
        예상 토큰 수
    """
    words = text.split()
    return int(len(words) * 1.3)


# ==========================================================================
# Testing
# ==========================================================================

def test_phase7_prompt():
    """Phase 7 프롬프트 테스트"""
    print("=== Phase 7 Prompt 테스트 ===\n")

    from ai.data_models import TeamInput

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
        match_id="EPL_2024_NLD_001",
        home_team=home_team,
        away_team=away_team,
        venue="Emirates Stadium",
        competition="Premier League",
        weather="Clear",
        importance="derby"
    )

    # 테스트 시뮬레이션 결과
    result = SimulationResult(
        final_score={'home': 2, 'away': 1},
        events=[
            {'type': 'goal', 'minute': 18, 'team': 'home'},
            {'type': 'shot', 'minute': 25, 'team': 'away'},
            {'type': 'goal', 'minute': 34, 'team': 'home'},
            {'type': 'goal', 'minute': 72, 'team': 'away'},
        ],
        narrative_adherence=0.75,
        stats={
            'home_shots': 15,
            'away_shots': 12,
            'home_possession': 58,
            'away_possession': 42,
        }
    )

    # Test 1: 프롬프트 생성
    print("Test 1: 프롬프트 생성")
    system_prompt, user_prompt = generate_phase7_prompt(match_input, result)

    print(f"  System Prompt 길이: {len(system_prompt)} 문자")
    print(f"  User Prompt 길이: {len(user_prompt)} 문자")
    print(f"  예상 토큰 수 (System): {estimate_token_count(system_prompt)}")
    print(f"  예상 토큰 수 (User): {estimate_token_count(user_prompt)}")
    print(f"  예상 총 토큰: {estimate_token_count(system_prompt + user_prompt)}")
    print(f"  ✅ 프롬프트 생성 성공\n")

    # Test 2: User Prompt 샘플
    print("Test 2: User Prompt 샘플")
    print("-" * 60)
    print(user_prompt[:700] + "...")
    print("-" * 60)
    print(f"  ✅ User Prompt 형식 확인\n")

    # 검증 기준
    total_tokens = estimate_token_count(system_prompt + user_prompt)
    print("=" * 60)
    print("검증 결과:")
    if total_tokens < 2500:
        print(f"  ✅ 토큰 수 목표 달성: {total_tokens} < 2,500")
    else:
        print(f"  ⚠️ 토큰 수 초과: {total_tokens} >= 2,500 (조정 필요)")

    print("=" * 60)
    print("✅ Phase 7 Prompt 테스트 완료!")
    print("=" * 60)


if __name__ == "__main__":
    test_phase7_prompt()
