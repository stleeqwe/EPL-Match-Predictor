"""
Key Player Weighted Model

선수별 영향력 지수 계산:
1. Overall rating + Position weight
2. Key strengths bonus
3. 상대 취약 구역 vs 핵심 선수 교차 분석

사용자 도메인 데이터 100% 기반
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from dataclasses import dataclass
from typing import Dict, List, Optional
import logging

from ai.enriched_data_models import EnrichedTeamInput, EnrichedPlayerInput

# Import zone dominance (absolute for __main__ execution)
try:
    from .zone_dominance_calculator import ZoneDominanceResult, POSITION_TO_ZONES
except ImportError:
    from zone_dominance_calculator import ZoneDominanceResult, POSITION_TO_ZONES

logger = logging.getLogger(__name__)


@dataclass
class PlayerInfluence:
    """선수별 영향력 정보"""
    player_name: str
    position: str
    sub_position: Optional[str]
    overall_rating: float
    influence: float                  # 0-10 scale
    top_attributes: List[str]         # Key strengths
    zones: List[str]                  # 활동 구역


@dataclass
class MatchupAdvantage:
    """매치업 우위 정보"""
    player_name: str
    team: str                         # 'home' or 'away'
    zones: List[str]                  # 우위를 가진 구역
    expected_impact: float            # 0-1 scale


@dataclass
class KeyPlayerInfluenceResult:
    """Key Player 모델 출력"""
    home_influences: Dict[str, PlayerInfluence]       # {player_name: PlayerInfluence}
    away_influences: Dict[str, PlayerInfluence]
    home_advantages: List[MatchupAdvantage]           # 홈팀 matchup advantages
    away_advantages: List[MatchupAdvantage]           # 원정팀 matchup advantages
    top_home_player: Optional[PlayerInfluence]        # 홈팀 최고 영향력 선수
    top_away_player: Optional[PlayerInfluence]        # 원정팀 최고 영향력 선수


class KeyPlayerInfluenceCalculator:
    """
    Key Player Weighted Model

    사용자 도메인 데이터로 선수별 영향력 계산:
    1. Overall rating + Position weight → Influence (0-10)
    2. Key strengths bonus
    3. 상대 취약 구역 분석 → Matchup advantages
    """

    # Position weights (공격수 > 미드필더 > 수비수)
    POSITION_WEIGHTS = {
        # Attackers
        'ST': 1.5,
        'CF': 1.5,
        'LW': 1.3,
        'RW': 1.3,

        # Attacking Midfielders
        'CAM': 1.2,

        # Midfielders
        'CM': 1.0,
        'CM1': 1.0,
        'CM2': 1.0,
        'CM-L': 1.0,
        'CM-R': 1.0,
        'DM': 1.0,
        'LM': 1.0,
        'RM': 1.0,

        # Defenders
        'LB': 0.8,
        'RB': 0.8,
        'CB': 0.7,
        'CB1': 0.7,
        'CB2': 0.7,
        'CB-L': 0.7,
        'CB-R': 0.7,

        # Goalkeeper
        'GK': 0.6,
    }

    # Elite attribute threshold
    ELITE_THRESHOLD = 4.5

    # Influence bonus for elite attributes
    ELITE_BONUS_MULTIPLIER = 1.15

    # Zone dominance threshold (상대 취약 구역 판정)
    WEAK_ZONE_THRESHOLD = 0.45  # 45% 이하면 취약

    def __init__(self):
        """Initialize Key Player Influence Calculator"""
        pass

    def calculate(self,
                  home_team: EnrichedTeamInput,
                  away_team: EnrichedTeamInput,
                  zone_result: Optional[ZoneDominanceResult] = None) -> KeyPlayerInfluenceResult:
        """
        Key Player Influence 계산

        Args:
            home_team: 홈팀 데이터 (11명 선수)
            away_team: 원정팀 데이터 (11명 선수)
            zone_result: Zone Dominance 결과 (matchup analysis용)

        Returns:
            KeyPlayerInfluenceResult with player influences and matchup advantages
        """
        logger.info(f"[Key Player] Calculating for {home_team.name} vs {away_team.name}")

        # 1. 선수별 영향력 계산
        home_influences = self._calculate_team_influences(home_team, 'home')
        away_influences = self._calculate_team_influences(away_team, 'away')

        # 2. Top players
        top_home = max(home_influences.values(), key=lambda x: x.influence) if home_influences else None
        top_away = max(away_influences.values(), key=lambda x: x.influence) if away_influences else None

        if top_home:
            logger.info(f"[Key Player] Top home player: {top_home.player_name} (influence {top_home.influence:.1f})")
        if top_away:
            logger.info(f"[Key Player] Top away player: {top_away.player_name} (influence {top_away.influence:.1f})")

        # 3. Matchup advantages (zone_result가 있으면)
        home_advantages = []
        away_advantages = []

        if zone_result:
            home_advantages = self._calculate_matchup_advantages(
                team_influences=home_influences,
                zone_control=zone_result.zone_control,
                team_side='home'
            )
            away_advantages = self._calculate_matchup_advantages(
                team_influences=away_influences,
                zone_control=zone_result.zone_control,
                team_side='away'
            )

            logger.info(f"[Key Player] Matchup advantages: Home {len(home_advantages)}, Away {len(away_advantages)}")

        return KeyPlayerInfluenceResult(
            home_influences=home_influences,
            away_influences=away_influences,
            home_advantages=home_advantages,
            away_advantages=away_advantages,
            top_home_player=top_home,
            top_away_player=top_away
        )

    def _calculate_team_influences(self,
                                    team: EnrichedTeamInput,
                                    team_side: str) -> Dict[str, PlayerInfluence]:
        """
        팀 전체 선수 영향력 계산

        Args:
            team: 팀 데이터 (11명)
            team_side: 'home' or 'away'

        Returns:
            {player_name: PlayerInfluence}
        """
        influences = {}

        for lineup_pos, player in team.lineup.items():
            # Skip if overall_rating is 0 (data issue)
            if player.overall_rating == 0.0:
                logger.warning(f"[Key Player] Skipping {player.name} (rating=0.0)")
                continue

            # Calculate influence
            influence = self._calculate_player_influence(player, lineup_pos)

            # Get player zones
            zones = self._get_player_zones(player, lineup_pos)

            # Top attributes
            top_attrs = player.get_key_strengths(3)

            influences[player.name] = PlayerInfluence(
                player_name=player.name,
                position=player.position,
                sub_position=player.sub_position,
                overall_rating=player.overall_rating,
                influence=influence,
                top_attributes=top_attrs,
                zones=zones
            )

        return influences

    def _calculate_player_influence(self,
                                     player: EnrichedPlayerInput,
                                     lineup_pos: str) -> float:
        """
        선수별 영향력 지수 계산 (0-10)

        Influence = (overall_rating / 5.0) * 10 * position_weight * elite_bonus

        Args:
            player: 선수 데이터
            lineup_pos: 라인업 포지션

        Returns:
            Influence (0-10)
        """
        # Base influence (overall_rating을 0-10 스케일로 변환)
        base_influence = (player.overall_rating / 5.0) * 10

        # Position weight (공격수가 영향력 높음)
        position_weight = self.POSITION_WEIGHTS.get(lineup_pos, 1.0)

        # Calculate influence
        influence = base_influence * position_weight

        # Elite attributes bonus
        if player.ratings:
            top_attrs = player.get_key_strengths(3)
            if top_attrs:
                avg_top = sum(player.ratings[attr] for attr in top_attrs) / len(top_attrs)
                if avg_top >= self.ELITE_THRESHOLD:
                    influence *= self.ELITE_BONUS_MULTIPLIER
                    logger.debug(f"[Key Player] Elite bonus for {player.name}: avg_top={avg_top:.2f}")

        # Cap at 10.0
        return min(10.0, influence)

    def _get_player_zones(self, player: EnrichedPlayerInput, lineup_pos: str) -> List[str]:
        """
        선수가 활동하는 구역 리스트

        Args:
            player: 선수 데이터
            lineup_pos: 라인업 포지션

        Returns:
            [zone1, zone2, ...]
        """
        # Use lineup_pos first (same logic as Zone Dominance)
        if lineup_pos in POSITION_TO_ZONES:
            return POSITION_TO_ZONES[lineup_pos]

        if player.sub_position and player.sub_position in POSITION_TO_ZONES:
            return POSITION_TO_ZONES[player.sub_position]

        return ['CM']  # Default

    def _calculate_matchup_advantages(self,
                                       team_influences: Dict[str, PlayerInfluence],
                                       zone_control: Dict[str, any],
                                       team_side: str) -> List[MatchupAdvantage]:
        """
        상대 취약 구역 vs 핵심 선수 교차 분석

        Args:
            team_influences: {player_name: PlayerInfluence}
            zone_control: Zone Dominance 결과
            team_side: 'home' or 'away'

        Returns:
            [MatchupAdvantage, ...]
        """
        advantages = []

        # 상대 취약 구역 추출
        weak_zones = []
        for zone, ctrl in zone_control.items():
            # 우리 팀이 지배하는 구역 = 상대 취약 구역
            our_control = ctrl.home_control if team_side == 'home' else ctrl.away_control
            if our_control >= (1.0 - self.WEAK_ZONE_THRESHOLD):  # 55% 이상 지배
                weak_zones.append(zone)

        logger.debug(f"[Key Player] {team_side} weak zones (opponent): {weak_zones}")

        # 핵심 선수가 취약 구역에서 활동하는지
        for player_name, player_inf in team_influences.items():
            # 영향력 높은 선수만 (6.0 이상)
            if player_inf.influence < 6.0:
                continue

            # 선수 활동 구역 vs 취약 구역 교차
            overlap_zones = list(set(player_inf.zones) & set(weak_zones))

            if overlap_zones:
                # Expected impact (영향력 * 구역 수)
                impact = (player_inf.influence / 10.0) * len(overlap_zones) / 2.0
                impact = min(1.0, impact)  # Cap at 1.0

                advantages.append(MatchupAdvantage(
                    player_name=player_name,
                    team=team_side,
                    zones=overlap_zones,
                    expected_impact=impact
                ))

        # 영향력 높은 순으로 정렬
        advantages.sort(key=lambda x: x.expected_impact, reverse=True)

        return advantages[:3]  # Top 3


if __name__ == "__main__":
    # 간단한 테스트
    logging.basicConfig(level=logging.DEBUG)

    from services.enriched_data_loader import EnrichedDomainDataLoader
    from zone_dominance_calculator import ZoneDominanceCalculator

    loader = EnrichedDomainDataLoader()
    arsenal = loader.load_team_data("Arsenal")
    liverpool = loader.load_team_data("Liverpool")

    # Zone Dominance 먼저 계산
    zone_calc = ZoneDominanceCalculator()
    zone_result = zone_calc.calculate(arsenal, liverpool)

    # Key Player Influence 계산
    calculator = KeyPlayerInfluenceCalculator()
    result = calculator.calculate(arsenal, liverpool, zone_result)

    print("\n" + "="*80)
    print("Key Player Influence Test")
    print("="*80)

    print(f"\nTop Home Players (Arsenal):")
    home_players = sorted(result.home_influences.values(), key=lambda x: x.influence, reverse=True)[:3]
    for i, player in enumerate(home_players, 1):
        print(f"  {i}. {player.player_name} ({player.sub_position or 'N/A'})")
        print(f"     Influence: {player.influence:.1f}/10")
        print(f"     Overall: {player.overall_rating:.2f}")
        print(f"     Top attrs: {', '.join(player.top_attributes[:2])}")

    print(f"\nTop Away Players (Liverpool):")
    away_players = sorted(result.away_influences.values(), key=lambda x: x.influence, reverse=True)[:3]
    for i, player in enumerate(away_players, 1):
        print(f"  {i}. {player.player_name} ({player.sub_position or 'N/A'})")
        print(f"     Influence: {player.influence:.1f}/10")
        print(f"     Overall: {player.overall_rating:.2f}")
        print(f"     Top attrs: {', '.join(player.top_attributes[:2])}")

    print(f"\nMatchup Advantages (Home):")
    for adv in result.home_advantages:
        print(f"  - {adv.player_name}: zones {adv.zones}, impact {adv.expected_impact:.2f}")

    print(f"\nMatchup Advantages (Away):")
    for adv in result.away_advantages:
        print(f"  - {adv.player_name}: zones {adv.zones}, impact {adv.expected_impact:.2f}")

    print()
