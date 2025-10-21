"""
Zone Dominance Matrix Calculator

경기장을 9개 구역으로 분할하여 팀별 지배율 계산:

   LD  |  CD  |  RD      Left Defense | Center Defense | Right Defense
  -----+------+-----
   LM  |  CM  |  RM      Left Midfield | Center Midfield | Right Midfield
  -----+------+-----
   LA  |  CA  |  RA      Left Attack | Center Attack | Right Attack

사용자 도메인 데이터 기반:
- player.sub_position → zone mapping
- player.overall_rating → zone strength
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from dataclasses import dataclass
from typing import Dict, List, Tuple
import logging

from ai.enriched_data_models import EnrichedTeamInput, EnrichedPlayerInput

logger = logging.getLogger(__name__)


# 9개 구역 정의
ZONES = ['LD', 'CD', 'RD', 'LM', 'CM', 'RM', 'LA', 'CA', 'RA']


# Position → Zone 매핑 (재설계 문서 기반)
POSITION_TO_ZONES = {
    # Goalkeepers (Center Defense)
    'GK': ['CD'],

    # Defenders
    'LB': ['LD', 'LM'],          # Left Back covers defense + midfield
    'CB': ['CD'],                 # Center Back
    'CB1': ['CD'],                # Center Back 1
    'CB2': ['CD'],                # Center Back 2
    'CB-L': ['CD', 'LD'],        # Left Center Back
    'CB-R': ['CD', 'RD'],        # Right Center Back
    'RB': ['RD', 'RM'],          # Right Back

    # Midfielders
    'DM': ['CM', 'CD'],          # Defensive Mid (center + drops back)
    'CM': ['CM'],                 # Center Mid
    'CM1': ['CM'],                # Center Mid 1
    'CM2': ['CM'],                # Center Mid 2
    'CM-L': ['CM', 'LM'],        # Left Center Mid
    'CM-R': ['CM', 'RM'],        # Right Center Mid
    'LM': ['LM', 'LA'],          # Left Mid (midfield + attack)
    'RM': ['RM', 'RA'],          # Right Mid (midfield + attack)
    'CAM': ['CM', 'CA'],         # Attacking Mid

    # Attackers
    'LW': ['LA', 'LM'],          # Left Wing
    'RW': ['RA', 'RM'],          # Right Wing
    'ST': ['CA'],                 # Striker
    'CF': ['CA'],                 # Center Forward
    'ST1': ['CA'],                # Striker 1
    'ST2': ['CA'],                # Striker 2
}


@dataclass
class ZoneControl:
    """단일 구역 지배율"""
    zone: str                    # 'LD', 'CM', etc.
    home_control: float          # 0.0 ~ 1.0
    away_control: float          # 0.0 ~ 1.0
    home_rating: float           # Home team presence (raw)
    away_rating: float           # Away team presence (raw)


@dataclass
class ZoneDominanceResult:
    """Zone Dominance 모델 출력"""
    zone_control: Dict[str, ZoneControl]              # {zone: ZoneControl}
    xG_home: float                                     # Expected goals (home)
    xG_away: float                                     # Expected goals (away)
    attack_control_home: float                         # Home attack zone control (0-1)
    attack_control_away: float                         # Away attack zone control (0-1)
    dominant_zones_home: List[str]                     # Home team dominant zones
    dominant_zones_away: List[str]                     # Away team dominant zones


class ZoneDominanceCalculator:
    """
    Zone Dominance Matrix Calculator

    사용자 도메인 데이터 (선수 11명)로 경기장 9구역별 지배율 계산:
    1. Position → Zone 매핑
    2. Overall rating으로 구역별 strength 계산
    3. 공격 구역 지배율 → xG 변환
    """

    # Zone weights
    PRIMARY_ZONE_WEIGHT = 1.0
    SECONDARY_ZONE_WEIGHT = 0.5

    # xG 계산 constants
    BASE_XG_HOME = 1.5           # Home team base xG
    BASE_XG_AWAY = 1.2           # Away team base xG

    # Dominance threshold (구역 지배 판정)
    DOMINANCE_THRESHOLD = 0.55   # 55% 이상이면 지배

    def __init__(self):
        """Initialize Zone Dominance Calculator"""
        pass

    def calculate(self,
                  home_team: EnrichedTeamInput,
                  away_team: EnrichedTeamInput) -> ZoneDominanceResult:
        """
        Zone Dominance 계산

        Args:
            home_team: 홈팀 데이터 (11명 선수)
            away_team: 원정팀 데이터 (11명 선수)

        Returns:
            ZoneDominanceResult with zone control and xG
        """
        logger.info(f"[Zone Dominance] Calculating for {home_team.name} vs {away_team.name}")

        # 1. 각 구역별 지배율 계산
        zone_control = {}
        for zone in ZONES:
            home_presence = self._calculate_zone_presence(home_team, zone)
            away_presence = self._calculate_zone_presence(away_team, zone)

            total = home_presence + away_presence
            if total > 0:
                home_control = home_presence / total
                away_control = away_presence / total
            else:
                home_control = 0.5
                away_control = 0.5

            zone_control[zone] = ZoneControl(
                zone=zone,
                home_control=home_control,
                away_control=away_control,
                home_rating=home_presence,
                away_rating=away_presence
            )

            logger.debug(f"[Zone Dominance] {zone}: Home {home_control:.1%}, Away {away_control:.1%}")

        # 2. 공격 구역 지배율 계산
        attack_zones = ['LA', 'CA', 'RA']
        attack_control_home = sum(zone_control[z].home_control for z in attack_zones) / len(attack_zones)
        attack_control_away = sum(zone_control[z].away_control for z in attack_zones) / len(attack_zones)

        logger.debug(f"[Zone Dominance] Attack control: Home {attack_control_home:.1%}, Away {attack_control_away:.1%}")

        # 3. xG 변환
        xG_home = self._convert_control_to_xg(attack_control_home, is_home=True)
        xG_away = self._convert_control_to_xg(attack_control_away, is_home=False)

        logger.info(f"[Zone Dominance] xG: Home {xG_home:.2f}, Away {xG_away:.2f}")

        # 4. 지배 구역 추출 (threshold 이상)
        dominant_zones_home = [
            z for z, ctrl in zone_control.items()
            if ctrl.home_control >= self.DOMINANCE_THRESHOLD
        ]
        dominant_zones_away = [
            z for z, ctrl in zone_control.items()
            if ctrl.away_control >= self.DOMINANCE_THRESHOLD
        ]

        logger.info(f"[Zone Dominance] Dominant zones: Home {dominant_zones_home}, Away {dominant_zones_away}")

        return ZoneDominanceResult(
            zone_control=zone_control,
            xG_home=xG_home,
            xG_away=xG_away,
            attack_control_home=attack_control_home,
            attack_control_away=attack_control_away,
            dominant_zones_home=dominant_zones_home,
            dominant_zones_away=dominant_zones_away
        )

    def _calculate_zone_presence(self, team: EnrichedTeamInput, zone: str) -> float:
        """
        특정 구역에서 팀의 presence 계산

        Args:
            team: 팀 데이터 (11명 선수)
            zone: 구역 (LD, CM, etc.)

        Returns:
            Presence (overall_rating 합산)
        """
        presence = 0.0

        for pos, player in team.lineup.items():
            # Position → Zones 매핑
            player_zones = self._get_player_zones(player, pos)

            if zone in player_zones:
                # Primary zone인지 확인
                is_primary = (player_zones.index(zone) == 0)
                weight = self.PRIMARY_ZONE_WEIGHT if is_primary else self.SECONDARY_ZONE_WEIGHT

                # Overall rating * weight
                contribution = player.overall_rating * weight
                presence += contribution

        return presence

    def _get_player_zones(self, player: EnrichedPlayerInput, lineup_pos: str) -> List[str]:
        """
        선수가 활동하는 구역 리스트 반환

        우선순위 (revised):
        1. lineup_pos (라인업 포지션 - 사용자가 설정한 실제 위치)
        2. player.sub_position (보조)
        3. Default: 중앙 미드필드

        데이터 로더 버그 대응:
        - Sub_position이 잘못 매핑된 경우가 있어서 lineup_pos 우선

        Args:
            player: 선수 데이터
            lineup_pos: 라인업 포지션 (GK, LB, etc.)

        Returns:
            [zone1, zone2, ...] (첫 번째가 primary)
        """
        # 1. Try lineup_pos first (사용자가 설정한 실제 포지션)
        if lineup_pos in POSITION_TO_ZONES:
            return POSITION_TO_ZONES[lineup_pos]

        # 2. Try sub_position as fallback
        if player.sub_position and player.sub_position in POSITION_TO_ZONES:
            logger.debug(f"[Zone Dominance] Using sub_position for {player.name}: {player.sub_position}")
            return POSITION_TO_ZONES[player.sub_position]

        # 3. Default: Center Midfield
        logger.warning(f"[Zone Dominance] Unknown position for {player.name}: lineup={lineup_pos}, sub={player.sub_position}, defaulting to CM")
        return ['CM']

    def _convert_control_to_xg(self, attack_control: float, is_home: bool) -> float:
        """
        공격 구역 지배율 → xG 변환

        xG = attack_control * BASE_XG

        Args:
            attack_control: 공격 구역 지배율 (0-1)
            is_home: 홈팀 여부

        Returns:
            xG
        """
        base_xg = self.BASE_XG_HOME if is_home else self.BASE_XG_AWAY

        # xG = control * base
        # attack_control이 높을수록 xG 증가
        # 예: 0.6 control * 1.5 base = 0.9 xG (낮음)
        #     공격 구역 지배만으로는 부족, 추가 배수 필요

        # 배수 적용 (공격 지배율이 높을수록 더 큰 영향)
        # control=0.5 → 1.0x, control=0.6 → 1.2x, control=0.7 → 1.4x
        multiplier = 1.0 + (attack_control - 0.5) * 2.0

        xG = base_xg * multiplier

        # 최소값/최대값 제한
        return max(0.1, min(xG, 4.0))


if __name__ == "__main__":
    # 간단한 테스트
    logging.basicConfig(level=logging.DEBUG)

    from services.enriched_data_loader import EnrichedDomainDataLoader

    loader = EnrichedDomainDataLoader()
    arsenal = loader.load_team_data("Arsenal")
    liverpool = loader.load_team_data("Liverpool")

    calculator = ZoneDominanceCalculator()
    result = calculator.calculate(arsenal, liverpool)

    print("\n" + "="*80)
    print("Zone Dominance Matrix Test")
    print("="*80)
    print(f"\nZone Control:")
    for zone in ZONES:
        ctrl = result.zone_control[zone]
        print(f"  {zone}: Home {ctrl.home_control:.1%}, Away {ctrl.away_control:.1%}")

    print(f"\nAttack Zone Control:")
    print(f"  Home: {result.attack_control_home:.1%}")
    print(f"  Away: {result.attack_control_away:.1%}")

    print(f"\nExpected Goals (Zone-based):")
    print(f"  Home: {result.xG_home:.2f}")
    print(f"  Away: {result.xG_away:.2f}")

    print(f"\nDominant Zones:")
    print(f"  Home: {result.dominant_zones_home}")
    print(f"  Away: {result.dominant_zones_away}")
    print()
