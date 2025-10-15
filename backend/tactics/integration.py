"""
기존 프로젝트와의 통합 인터페이스

독립적으로 구축된 전술 프레임워크를 기존 시스템과 병합할 때 사용하는 인터페이스
"""

from typing import Dict, List, Optional
from core.formations import FormationSystem
from core.tactical_styles import TacticalStyle
from analyzer.effectiveness_calculator import EffectivenessCalculator
from analyzer.goal_path_classifier import GoalPathClassifier, GoalData


class TacticsIntegration:
    """
    전술 프레임워크 통합 인터페이스

    기존 프로젝트의 선수/팀 데이터와 전술 시스템을 연결
    """

    def __init__(self):
        """초기화"""
        self.formation_system = FormationSystem()
        self.calculator = EffectivenessCalculator()
        self.classifier = GoalPathClassifier()

    # ========================================================================
    # 선수 능력치 통합
    # ========================================================================

    @staticmethod
    def apply_tactics_to_player(
        player_data: Dict,
        tactics: Dict,
        position: str
    ) -> Dict:
        """
        선수 능력치에 전술 가중치 적용

        Args:
            player_data: 기존 프로젝트의 선수 데이터
                {
                    'id': int,
                    'name': str,
                    'position': str,
                    'technical_attributes': {...},
                    'pace': float,
                    'stamina': float,
                    ...
                }
            tactics: 전술 파라미터 딕셔너리
            position: 전술적 역할 (예: 'DM', 'CB', 'RW')

        Returns:
            전술 가중치가 적용된 선수 데이터

        Example:
            >>> integration = TacticsIntegration()
            >>> player = {'name': 'Rodri', 'position': 'DM', ...}
            >>> tactics = {'pressing_intensity': 9, ...}
            >>> adjusted = integration.apply_tactics_to_player(player, tactics, 'DM')
        """
        adjusted_player = player_data.copy()

        # 전술에 따른 능력치 가중치
        tactical_weights = TacticsIntegration._get_tactical_attribute_weights(
            position,
            tactics
        )

        # 기술 능력치에 가중치 적용
        if 'technical_attributes' in adjusted_player:
            tech_attrs = adjusted_player['technical_attributes']
            weighted_attrs = {}

            for attr, value in tech_attrs.items():
                weight = tactical_weights.get(attr, 1.0)
                weighted_attrs[attr] = value * weight

            adjusted_player['technical_attributes_weighted'] = weighted_attrs

        # 전술 적합도 점수 계산
        adjusted_player['tactical_fit_score'] = TacticsIntegration._calculate_tactical_fit(
            player_data,
            tactics,
            position
        )

        return adjusted_player

    @staticmethod
    def _get_tactical_attribute_weights(
        position: str,
        tactics: Dict
    ) -> Dict[str, float]:
        """
        전술에 따른 능력치 가중치

        예: 하이 프레스 전술 → 스피드/지구력 가중치 증가
        """
        base_weights = {}

        pressing_intensity = tactics.get('pressing_intensity', 5)
        defensive_line = tactics.get('defensive_line', 5)

        # DM 포지션 예시
        if position == 'DM':
            if pressing_intensity >= 8:
                # 하이 프레스 → 체력/압박 능력 중요
                base_weights['stamina'] = 1.3
                base_weights['pressing'] = 1.4
                base_weights['work_rate'] = 1.3
            else:
                # 로우 블록 → 포지셔닝/인터셉트 중요
                base_weights['positioning'] = 1.3
                base_weights['interceptions'] = 1.3
                base_weights['composure'] = 1.2

        # CB 포지션 예시
        elif position == 'CB':
            if defensive_line >= 8:
                # 높은 라인 → 스피드 중요
                base_weights['pace'] = 1.4
                base_weights['recovery_speed'] = 1.4
            else:
                # 낮은 라인 → 공중볼/포지셔닝 중요
                base_weights['aerial_ability'] = 1.3
                base_weights['positioning'] = 1.3

        return base_weights

    @staticmethod
    def _calculate_tactical_fit(
        player_data: Dict,
        tactics: Dict,
        position: str
    ) -> float:
        """
        선수의 전술 적합도 점수 (0-100)

        선수의 능력치가 전술 요구사항과 얼마나 부합하는지 평가
        """
        # 간단한 예시 구현
        # 실제로는 더 정교한 알고리즘 필요

        fit_score = 70.0  # 기본값

        pressing_intensity = tactics.get('pressing_intensity', 5)

        # 체력 관련
        if 'stamina' in player_data:
            stamina = player_data['stamina']
            if pressing_intensity >= 8:
                # 하이 프레스 → 체력 중요
                if stamina >= 80:
                    fit_score += 10
                elif stamina < 60:
                    fit_score -= 10

        return min(100, max(0, fit_score))

    # ========================================================================
    # 팀 전술 통합
    # ========================================================================

    def calculate_team_tactical_score(
        self,
        squad: List[Dict],
        formation: str,
        tactics: Dict
    ) -> float:
        """
        팀 스쿼드의 전술 적합도 점수

        Args:
            squad: 선수 리스트
            formation: 포메이션 (예: "4-3-3")
            tactics: 전술 파라미터

        Returns:
            팀 전술 적합도 점수 (0-100)

        Example:
            >>> squad = [player1, player2, ..., player11]
            >>> score = integration.calculate_team_tactical_score(
            ...     squad, "4-3-3", {'pressing_intensity': 9}
            ... )
            >>> print(f"팀 전술 적합도: {score:.1f}/100")
        """
        if not squad:
            return 0.0

        # 포지션별 중요도 가져오기
        position_importance = self.formation_system.get_position_importance(formation)

        total_score = 0.0
        total_weight = 0.0

        for player in squad:
            position = player.get('position', 'Unknown')

            # 전술 적합도 계산
            fit_score = self._calculate_tactical_fit(player, tactics, position)

            # 포지션 중요도 가중치
            weight = position_importance.get(position, 0.1)

            total_score += fit_score * weight
            total_weight += weight

        if total_weight == 0:
            return 0.0

        return total_score / total_weight

    def get_tactical_advantage(
        self,
        home_tactics: Dict,
        away_tactics: Dict
    ) -> Dict:
        """
        전술 매칭 분석 및 우위 계산

        Args:
            home_tactics: 홈팀 전술
                {
                    'formation': str,
                    'team_ability': float,
                    'tactics': {...}
                }
            away_tactics: 원정팀 전술

        Returns:
            {
                'home_score': float,
                'away_score': float,
                'advantage': str,
                'key_matchups': list
            }

        Example:
            >>> home = {'formation': '4-3-3', 'team_ability': 1.12}
            >>> away = {'formation': '4-2-3-1', 'team_ability': 1.08}
            >>> advantage = integration.get_tactical_advantage(home, away)
        """
        # 매칭 분석
        matchup = self.calculator.calculate_matchup_advantage(
            home_formation=home_tactics['formation'],
            away_formation=away_tactics['formation'],
            home_ability=home_tactics.get('team_ability', 1.0),
            away_ability=away_tactics.get('team_ability', 1.0)
        )

        # 핵심 매칭 분석
        key_matchups = []
        for category, analysis in matchup['analysis_by_category'].items():
            diff = abs(analysis['difference'])
            if diff > 10:  # 10% 이상 차이
                key_matchups.append({
                    'category': analysis['name'],
                    'home_blocking': analysis['home_blocking'],
                    'away_blocking': analysis['away_blocking'],
                    'advantage': 'home' if analysis['difference'] > 0 else 'away'
                })

        return {
            'home_score': matchup['home_defensive_score'],
            'away_score': matchup['away_defensive_score'],
            'advantage': matchup['advantage'],
            'difference': matchup['difference'],
            'key_matchups': key_matchups
        }

    # ========================================================================
    # 경기 결과 예측 통합
    # ========================================================================

    def predict_match_outcome(
        self,
        home_team: Dict,
        away_team: Dict,
        match_conditions: Optional[Dict] = None
    ) -> Dict:
        """
        경기 결과 예측 (전술 분석 기반)

        Args:
            home_team: 홈팀 데이터
                {
                    'formation': str,
                    'squad': list,
                    'team_ability': float,
                    'tactics': {...}
                }
            away_team: 원정팀 데이터
            match_conditions: 경기 조건
                {
                    'home_fatigue': float,
                    'away_fatigue': float,
                    'weather': float,
                    ...
                }

        Returns:
            {
                'home_win_probability': float,
                'draw_probability': float,
                'away_win_probability': float,
                'tactical_analysis': {...}
            }
        """
        if match_conditions is None:
            match_conditions = {
                'home_fatigue': 1.0,
                'away_fatigue': 1.0,
                'weather': 1.0
            }

        # 전술 우위 분석
        tactical_advantage = self.get_tactical_advantage(
            home_tactics={'formation': home_team['formation'], 'team_ability': home_team.get('team_ability', 1.0)},
            away_tactics={'formation': away_team['formation'], 'team_ability': away_team.get('team_ability', 1.0)}
        )

        # 간단한 확률 계산 (실제로는 더 정교한 모델 필요)
        home_score = tactical_advantage['home_score']
        away_score = tactical_advantage['away_score']

        score_diff = home_score - away_score

        # 홈 어드밴티지 (+5%)
        base_home_win = 40.0 + (score_diff * 0.5) + 5.0
        base_draw = 30.0
        base_away_win = 30.0 - (score_diff * 0.5) - 5.0

        # 정규화
        total = base_home_win + base_draw + base_away_win
        home_win_prob = (base_home_win / total) * 100
        draw_prob = (base_draw / total) * 100
        away_win_prob = (base_away_win / total) * 100

        return {
            'home_win_probability': round(home_win_prob, 2),
            'draw_probability': round(draw_prob, 2),
            'away_win_probability': round(away_win_prob, 2),
            'tactical_analysis': tactical_advantage,
            'confidence': 'medium'  # 'high', 'medium', 'low'
        }


# 사용 예시
if __name__ == "__main__":
    integration = TacticsIntegration()

    print("=== 전술 통합 인터페이스 예시 ===\n")

    # 1. 선수 능력치에 전술 적용
    print("1. 선수 능력치 전술 가중치 적용")
    player = {
        'id': 1,
        'name': 'Rodri',
        'position': 'DM',
        'stamina': 85,
        'technical_attributes': {
            'tackling': 88,
            'interceptions': 90,
            'passing': 92
        }
    }
    tactics = {
        'pressing_intensity': 9,
        'defensive_line': 8
    }
    adjusted = integration.apply_tactics_to_player(player, tactics, 'DM')
    print(f"원본 체력: {player['stamina']}")
    print(f"전술 적합도: {adjusted['tactical_fit_score']:.1f}/100\n")

    # 2. 팀 전술 적합도
    print("2. 팀 전술 적합도 계산")
    squad = [player] * 11  # 간단한 예시
    team_score = integration.calculate_team_tactical_score(
        squad, "4-3-3", tactics
    )
    print(f"팀 전술 적합도: {team_score:.1f}/100\n")

    # 3. 전술 매칭 분석
    print("3. 전술 매칭 분석 (맨시티 vs 리버풀)")
    home = {
        'formation': '4-3-3',
        'team_ability': 1.12
    }
    away = {
        'formation': '4-3-3',
        'team_ability': 1.10
    }
    advantage = integration.get_tactical_advantage(home, away)
    print(f"홈팀 수비력: {advantage['home_score']:.1f}")
    print(f"원정팀 수비력: {advantage['away_score']:.1f}")
    print(f"우위: {advantage['advantage']}\n")

    # 4. 경기 결과 예측
    print("4. 경기 결과 예측")
    home_team = {
        'formation': '4-3-3',
        'squad': squad,
        'team_ability': 1.12
    }
    away_team = {
        'formation': '4-2-3-1',
        'squad': squad,
        'team_ability': 1.08
    }
    prediction = integration.predict_match_outcome(home_team, away_team)
    print(f"홈 승: {prediction['home_win_probability']:.1f}%")
    print(f"무승부: {prediction['draw_probability']:.1f}%")
    print(f"원정 승: {prediction['away_win_probability']:.1f}%")
