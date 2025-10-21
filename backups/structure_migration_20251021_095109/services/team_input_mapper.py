"""
Team Input Mapper
DomainDataLoader에서 로드한 데이터를 AI 시뮬레이션용 TeamInput 객체로 변환
"""

from typing import List, Optional
from ai.data_models import TeamInput
from services.domain_data_loader import TeamDomainData


class TeamInputMapper:
    """TeamDomainData → TeamInput 변환"""

    # 18개 Team Strength 속성을 4개 기본 속성으로 매핑
    STRENGTH_MAPPING = {
        # attack_strength: 공격 효율성 카테고리 평균
        'attack_strength': [
            'buildup_quality',
            'pass_network',
            'final_third_penetration',
            'goal_conversion'
        ],
        # defense_strength: 수비 안정성 카테고리 평균
        'defense_strength': [
            'backline_organization',
            'central_control',
            'flank_defense',
            'counter_prevention'
        ],
        # press_intensity: 압박 조직력 관련
        'press_intensity': [
            'pressing_organization',
            'attack_to_defense_transition'
        ],
        # buildup_style: 빌드업 완성도 기반 (높으면 possession, 낮으면 direct)
        'buildup_style_score': [
            'buildup_quality',
            'pass_network'
        ]
    }

    @staticmethod
    def calculate_aggregate_score(ratings: dict, attributes: List[str]) -> float:
        """
        여러 속성의 평균 계산

        Args:
            ratings: {attribute: rating, ...}
            attributes: 평균을 낼 속성 리스트

        Returns:
            평균값 (0.0~5.0) → 0~100 스케일로 변환
        """
        values = [ratings.get(attr, 2.5) for attr in attributes if attr in ratings]

        if not values:
            return 80.0  # 기본값

        avg = sum(values) / len(values)
        # 0~5 → 0~100 스케일 변환
        return (avg / 5.0) * 100.0

    @staticmethod
    def determine_buildup_style(ratings: dict) -> str:
        """
        빌드업 스타일 결정

        Args:
            ratings: {attribute: rating, ...}

        Returns:
            "possession", "mixed", "direct"
        """
        buildup_score = TeamInputMapper.calculate_aggregate_score(
            ratings,
            TeamInputMapper.STRENGTH_MAPPING['buildup_style_score']
        )

        # 70점 이상: possession
        # 50~70: mixed (balanced)
        # 50 미만: direct
        if buildup_score >= 70:
            return "possession"
        elif buildup_score >= 50:
            return "mixed"  # TeamInput에서 "mixed"만 허용
        else:
            return "direct"

    @staticmethod
    def map_to_team_input(
        team_name: str,
        domain_data: TeamDomainData,
        recent_form: str = "WWDWL",
        injuries: List[str] = None,
        key_players: List[str] = None
    ) -> TeamInput:
        """
        TeamDomainData를 TeamInput으로 변환

        Args:
            team_name: 팀 이름
            domain_data: 로드된 domain 데이터
            recent_form: 최근 5경기 결과 (기본값)
            injuries: 부상자 리스트 (기본값: [])
            key_players: 주요 선수 리스트 (기본값: [])

        Returns:
            TeamInput 객체
        """
        if injuries is None:
            injuries = []
        if key_players is None:
            key_players = []

        # Formation
        formation = domain_data.formation or "4-3-3"

        # Team Strength → attack/defense/press 변환
        attack_strength = 80.0
        defense_strength = 80.0
        press_intensity = 70.0
        buildup_style = "mixed"  # TeamInput에서 "mixed"만 허용

        if domain_data.team_strength:
            ratings = domain_data.team_strength

            attack_strength = TeamInputMapper.calculate_aggregate_score(
                ratings,
                TeamInputMapper.STRENGTH_MAPPING['attack_strength']
            )

            defense_strength = TeamInputMapper.calculate_aggregate_score(
                ratings,
                TeamInputMapper.STRENGTH_MAPPING['defense_strength']
            )

            press_intensity = TeamInputMapper.calculate_aggregate_score(
                ratings,
                TeamInputMapper.STRENGTH_MAPPING['press_intensity']
            )

            buildup_style = TeamInputMapper.determine_buildup_style(ratings)

        return TeamInput(
            name=team_name,
            formation=formation,
            recent_form=recent_form,
            injuries=injuries,
            key_players=key_players,
            attack_strength=attack_strength,
            defense_strength=defense_strength,
            press_intensity=press_intensity,
            buildup_style=buildup_style
        )

    @staticmethod
    def get_enriched_description(domain_data: TeamDomainData) -> str:
        """
        Domain 데이터를 기반으로 팀 설명 생성 (AI 프롬프트용)

        Returns:
            팀에 대한 상세 설명 텍스트
        """
        parts = []

        # Formation
        if domain_data.formation:
            parts.append(f"Formation: {domain_data.formation}")

        # Team Strength Comment
        if domain_data.team_strength_comment:
            parts.append(f"Analysis: {domain_data.team_strength_comment}")

        # Team Strength 주요 강점/약점
        if domain_data.team_strength:
            ratings = domain_data.team_strength

            # 상위 3개 속성
            sorted_attrs = sorted(ratings.items(), key=lambda x: x[1], reverse=True)
            if len(sorted_attrs) >= 3:
                top_3 = sorted_attrs[:3]
                strengths = [f"{attr.replace('_', ' ').title()} ({rating:.1f})"
                             for attr, rating in top_3]
                parts.append(f"Key Strengths: {', '.join(strengths)}")

            # 하위 3개 속성
            if len(sorted_attrs) >= 3:
                bottom_3 = sorted_attrs[-3:]
                weaknesses = [f"{attr.replace('_', ' ').title()} ({rating:.1f})"
                              for attr, rating in bottom_3]
                parts.append(f"Areas to Improve: {', '.join(weaknesses)}")

        # Overall Score
        if domain_data.overall_score:
            overall = domain_data.overall_score.get('overallScore', 0)
            parts.append(f"Overall Rating: {overall:.1f}/100")

        return " | ".join(parts) if parts else "No detailed analysis available"
