"""
AI Rating Generator Service
Gemini AI를 활용한 선수 능력치 자동 생성 (82개 능력치)
"""

import json
import logging
from typing import Dict, Optional
from dataclasses import dataclass

from ai.ai_factory import get_ai_client

logger = logging.getLogger(__name__)


# 포지션별 능력치 정의 (frontend/src/config/positionAttributes.js와 동일)
POSITION_ATTRIBUTES = {
    'GK': {
        'name': '골키퍼',
        'name_en': 'Goalkeeper',
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
    'CB': {
        'name': '센터백',
        'name_en': 'Center Back',
        'attributes': [
            {'key': 'positioning_reading', 'label': '포지셔닝 & 공간 읽기', 'weight': 0.15},
            {'key': 'composure_judgement', 'label': '침착성 & 판단력', 'weight': 0.12},
            {'key': 'interception', 'label': '인터셉트', 'weight': 0.10},
            {'key': 'aerial_duel', 'label': '공중볼 경합', 'weight': 0.09},
            {'key': 'tackle_marking', 'label': '태클 & 마킹', 'weight': 0.11},
            {'key': 'speed', 'label': '스피드', 'weight': 0.10},
            {'key': 'passing', 'label': '패스 능력', 'weight': 0.13},
            {'key': 'physical_jumping', 'label': '피지컬 & 점프력', 'weight': 0.08},
            {'key': 'buildup_contribution', 'label': '빌드업 기여도', 'weight': 0.10},
            {'key': 'leadership', 'label': '리더십', 'weight': 0.02}
        ]
    },
    'FB': {
        'name': '풀백',
        'name_en': 'Fullback/Wingback',
        'attributes': [
            {'key': 'stamina', 'label': '지구력', 'weight': 0.16},
            {'key': 'speed', 'label': '스피드', 'weight': 0.15},
            {'key': 'defensive_positioning', 'label': '수비 포지셔닝', 'weight': 0.12},
            {'key': 'one_on_one_tackle', 'label': '1:1 수비 & 태클', 'weight': 0.13},
            {'key': 'overlapping', 'label': '오버래핑', 'weight': 0.11},
            {'key': 'crossing_accuracy', 'label': '크로스 정확도', 'weight': 0.11},
            {'key': 'covering', 'label': '백업 커버링', 'weight': 0.09},
            {'key': 'agility', 'label': '민첩성', 'weight': 0.07},
            {'key': 'press_resistance', 'label': '압박 저항력', 'weight': 0.04},
            {'key': 'long_shot', 'label': '중거리 슈팅', 'weight': 0.02}
        ]
    },
    'DM': {
        'name': '수비형 미드필더',
        'name_en': 'Defensive Midfielder',
        'attributes': [
            {'key': 'positioning', 'label': '포지셔닝', 'weight': 0.12},
            {'key': 'ball_winning', 'label': '볼 차단 & 회수', 'weight': 0.12},
            {'key': 'pass_accuracy', 'label': '패스 정확도', 'weight': 0.10},
            {'key': 'composure_press_resistance', 'label': '침착성 & 압박 해소', 'weight': 0.12},
            {'key': 'backline_protection', 'label': '백라인 보호', 'weight': 0.10},
            {'key': 'pressing_transition_blocking', 'label': '공간 압박 & 전환 차단', 'weight': 0.10},
            {'key': 'progressive_play', 'label': '공격 전개', 'weight': 0.09},
            {'key': 'tempo_control', 'label': '템포 조절', 'weight': 0.07},
            {'key': 'stamina', 'label': '지구력', 'weight': 0.06},
            {'key': 'physicality_mobility', 'label': '피지컬 & 기동력', 'weight': 0.10},
            {'key': 'leadership', 'label': '리더십', 'weight': 0.02}
        ]
    },
    'CM': {
        'name': '중앙 미드필더',
        'name_en': 'Central Midfielder',
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
    },
    'CAM': {
        'name': '공격형 미드필더',
        'name_en': 'Attacking Midfielder',
        'attributes': [
            {'key': 'creativity', 'label': '창의성', 'weight': 0.13},
            {'key': 'vision_killpass', 'label': '시야 & 킬패스', 'weight': 0.12},
            {'key': 'dribbling', 'label': '드리블 돌파', 'weight': 0.11},
            {'key': 'decision_making', 'label': '결정적 순간 판단', 'weight': 0.11},
            {'key': 'penetration', 'label': '공간 침투', 'weight': 0.10},
            {'key': 'shooting_finishing', 'label': '슈팅 & 마무리', 'weight': 0.11},
            {'key': 'one_touch_pass', 'label': '원터치 패스', 'weight': 0.08},
            {'key': 'pass_and_move', 'label': '패스 & 무브', 'weight': 0.07},
            {'key': 'acceleration', 'label': '가속력', 'weight': 0.07},
            {'key': 'agility', 'label': '민첩성', 'weight': 0.06},
            {'key': 'set_piece', 'label': '세트피스', 'weight': 0.04}
        ]
    },
    'WG': {
        'name': '윙어',
        'name_en': 'Winger',
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
    'ST': {
        'name': '스트라이커',
        'name_en': 'Striker',
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
    }
}


@dataclass
class AIRatingResult:
    """AI 능력치 생성 결과"""
    ratings: Dict[str, float]  # {attribute_key: rating_value}
    comment: str
    confidence: float
    reasoning: str


class AIRatingGenerator:
    """AI 기반 선수 능력치 생성기"""

    def __init__(self, ai_client=None):
        """
        Initialize AI Rating Generator

        Args:
            ai_client: AI client (Gemini, Claude, etc.)
        """
        self.ai_client = ai_client or get_ai_client()
        logger.info(f"AIRatingGenerator initialized with {self.ai_client.__class__.__name__}")

    def generate(
        self,
        player_name: str,
        position: str,
        team: str,
        fpl_stats: Dict
    ) -> AIRatingResult:
        """
        선수 능력치 생성

        Args:
            player_name: 선수 이름
            position: 세부 포지션 (GK, CB, FB, DM, CM, CAM, WG, ST)
            team: 팀 이름
            fpl_stats: FPL 통계 (minutes, goals, assists, form, etc.)

        Returns:
            AIRatingResult
        """
        logger.info(f"Generating ratings for {player_name} ({position}, {team})")

        # 포지션 검증
        if position not in POSITION_ATTRIBUTES:
            raise ValueError(f"Unknown position: {position}. Must be one of {list(POSITION_ATTRIBUTES.keys())}")

        # 프롬프트 생성
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(player_name, position, team, fpl_stats)

        # AI 호출
        logger.debug("Calling Gemini AI for rating generation...")
        success, response_text, usage, error = self.ai_client.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.7,  # 다양성 허용
            max_tokens=2000
        )

        if not success:
            raise RuntimeError(f"AI generation failed: {error}")

        logger.info(f"AI response received ({usage['total_tokens']} tokens, ${usage.get('cost', 0):.4f})")

        # 응답 파싱
        result = self._parse_response(response_text, position)
        logger.info(f"Ratings generated successfully (avg: {sum(result.ratings.values()) / len(result.ratings):.2f}/5.0)")

        return result

    def _build_system_prompt(self) -> str:
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

    def _build_user_prompt(
        self,
        player_name: str,
        position: str,
        team: str,
        fpl_stats: Dict
    ) -> str:
        """유저 프롬프트 생성"""

        position_data = POSITION_ATTRIBUTES[position]
        attributes = position_data['attributes']

        # 능력치 목록
        attr_list = '\n'.join([
            f"  - {attr['key']}: {attr['label']} (가중치 {attr['weight']:.0%})"
            for attr in attributes
        ])

        minutes = fpl_stats.get('minutes', 0)
        low_playtime_warning = ""

        if minutes < 100:
            low_playtime_warning = f"""
⚠️ 주의: 출전 시간이 매우 적습니다 ({minutes}분).
- 데이터 부족으로 능력치 평가가 부정확할 수 있습니다
- 보수적으로 평가하되, 팀의 수준과 포지션을 고려하세요
- 코멘트에 "출전 시간 부족으로 평가 제한적" 언급 필수
"""

        prompt = f"""# 선수 정보
- 이름: {player_name}
- 포지션: {position_data['name']} ({position})
- 팀: {team}

# FPL 통계 (2024/25 시즌)
- 출전 시간: {minutes}분
- 골: {fpl_stats.get('goals', 0)}개
- 어시스트: {fpl_stats.get('assists', 0)}개
- 폼: {fpl_stats.get('form', '0.0')}/10
- 선발률: {fpl_stats.get('selected_by', '0.0')}%
- 보너스: {fpl_stats.get('bonus', 0)}점
{low_playtime_warning}
# 평가 항목 ({len(attributes)}개)
{attr_list}

# 요구사항
1. 각 능력치를 0.0-5.0 스케일로 평가 (0.25 단위만)
2. FPL 통계를 근거로 합리적 추론 (출전 시간이 적으면 보수적 평가)
3. 100자 이내 코멘트 작성 (출전 시간 부족 시 명시)

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

    def _parse_response(self, response_text: str, position: str) -> AIRatingResult:
        """AI 응답 파싱"""

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

            # JSON 파싱
            data = json.loads(response_clean)

            ratings = data.get('ratings', {})
            comment = data.get('comment', '')
            reasoning = data.get('reasoning', '')

            # 능력치 검증 및 정규화
            attributes = POSITION_ATTRIBUTES[position]['attributes']
            validated_ratings = {}

            for attr in attributes:
                key = attr['key']
                value = ratings.get(key)

                if value is None:
                    logger.warning(f"Missing rating for {key}, using default 2.5")
                    value = 2.5
                elif not (0.0 <= value <= 5.0):
                    logger.warning(f"Invalid rating {value} for {key}, clamping to 0-5")
                    value = max(0.0, min(5.0, value))

                # 0.25 단위로 반올림
                value = round(value * 4) / 4
                validated_ratings[key] = value

            # Confidence 계산 (평균 능력치 기반)
            avg_rating = sum(validated_ratings.values()) / len(validated_ratings)
            confidence = min(0.95, 0.70 + (avg_rating / 5.0) * 0.25)  # 0.70-0.95

            return AIRatingResult(
                ratings=validated_ratings,
                comment=comment[:100],  # 100자 제한
                confidence=confidence,
                reasoning=reasoning
            )

        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {e}")
            logger.error(f"Response: {response_text[:500]}")
            raise ValueError(f"Failed to parse AI response: {e}")
        except Exception as e:
            logger.error(f"Response parsing error: {e}")
            raise


# Singleton instance
_ai_rating_generator = None


def get_ai_rating_generator() -> AIRatingGenerator:
    """Get global AI rating generator instance"""
    global _ai_rating_generator
    if _ai_rating_generator is None:
        _ai_rating_generator = AIRatingGenerator()
    return _ai_rating_generator


if __name__ == "__main__":
    # 테스트
    logging.basicConfig(level=logging.INFO)

    generator = AIRatingGenerator()

    # Test: Bukayo Saka
    result = generator.generate(
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

    print("\n" + "=" * 80)
    print(f"AI Generated Ratings for Bukayo Saka (WG)")
    print("=" * 80)
    print(f"\nRatings:")
    for key, value in result.ratings.items():
        print(f"  {key}: {value:.2f}")
    print(f"\nComment: {result.comment}")
    print(f"Confidence: {result.confidence:.1%}")
    print(f"Reasoning: {result.reasoning}")
