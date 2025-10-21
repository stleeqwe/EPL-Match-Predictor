"""
Enriched Data Models - Phase 1 Accurate Reconstruction
사용자 실제 Domain Input에 기반한 정확한 데이터 모델

실제 확인된 구조:
1. 선수 평가: SQLite DB (포지션별 속성, 10-12개)
2. 팀 데이터: JSON 파일 (formations, lineups, tactics, team_strength)
3. 코멘터리: _comment (선수별), comment (팀 전략)

제거된 필드 (사용자 피드백):
- recent_form: 선수 속성에 이미 반영됨
- injuries: 라인업 구성 시 이미 제외됨
- key_players: 선수 속성에 이미 반영됨

추가된 필드:
- 선수별 코멘터리 (_comment in notes)
- 팀 전략 코멘터리 (team_strength/comment)
- 포지션별 속성 (10-12개, 포지션 의존적)
- 전술 파라미터 (3개 카테고리, 0-10 스케일)
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum


# ==========================================================================
# Player Data Models
# ==========================================================================

@dataclass
class PlayerRating:
    """선수 능력치 (단일 속성)"""
    attribute_name: str       # 'positioning_reading', 'speed_dribbling', etc.
    rating: float             # 0.0-5.0, 0.25 step
    notes: Optional[str] = None  # 일반 속성의 notes (사용 안 함)

    def __post_init__(self):
        assert 0.0 <= self.rating <= 5.0, f"Rating must be 0.0-5.0: {self.rating}"
        # 0.25 단위 검증
        assert round(self.rating * 4) == self.rating * 4, \
            f"Rating must be in 0.25 steps: {self.rating}"


@dataclass
class EnrichedPlayerInput:
    """
    선수 Domain Input (실제 DB 구조 기반)

    SQLite player_ratings 테이블에서 로드:
    - 포지션별로 다른 속성 (CB: 10개, Winger: 12개, etc.)
    - _comment: notes 컬럼에 저장 (attribute로 취급)
    - _subPosition: notes 컬럼에 저장
    """
    player_id: int
    name: str
    position: str                     # 'Goalkeeper', 'Centre Central Defender', etc.

    # 포지션별 속성 (10-12개, 가변적)
    # 예: CB: positioning_reading, interception, aerial_duel, ...
    # 예: Winger: speed_dribbling, crossing_accuracy, cutting_in, ...
    ratings: Dict[str, float]         # {attribute_name: rating_value}

    # 메타 필드 (DB에서 _comment, _subPosition로 저장)
    sub_position: Optional[str] = None      # "CB", "WG", "ST", etc.
    user_commentary: Optional[str] = None   # 선수별 코멘터리 (핵심!)

    # 계산된 값
    overall_rating: float = 0.0              # ratings의 평균

    def __post_init__(self):
        """Overall rating 자동 계산"""
        if self.ratings and self.overall_rating == 0.0:
            self.overall_rating = sum(self.ratings.values()) / len(self.ratings)

    def get_key_strengths(self, top_n: int = 3) -> List[str]:
        """주요 강점 속성 추출 (상위 N개)"""
        if not self.ratings:
            return []
        sorted_attrs = sorted(
            self.ratings.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return [attr for attr, _ in sorted_attrs[:top_n]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            'player_id': self.player_id,
            'name': self.name,
            'position': self.position,
            'sub_position': self.sub_position,
            'ratings': self.ratings,
            'user_commentary': self.user_commentary,
            'overall_rating': self.overall_rating
        }


# ==========================================================================
# Tactics Data Models (REMOVED - Static 데이터 제거)
# ==========================================================================
# TacticsInput, DefensiveTactics, OffensiveTactics, TransitionTactics
# 미리 정의된 전술 파라미터가 AI 시나리오 생성에 영향을 주지 않도록 완전 제거


# ==========================================================================
# Formation Tactics Data Models
# ==========================================================================

@dataclass
class FormationTactics:
    """포메이션 전술 특성 (사용자 선택 기반)"""
    formation: str                          # "4-3-3", "4-2-3-1", etc.
    name: str                               # "공격형 4-3-3", "수비형 4-3-3", etc.
    style: str                              # "공격적", "수비적", "균형잡힌", etc.
    buildup: str                            # 빌드업 방식
    pressing: str                           # 압박 방식
    space_utilization: str                  # 공간 활용
    strengths: List[str]                    # 강점 리스트
    weaknesses: List[str]                   # 취약점 리스트
    note: Optional[str] = None              # 추가 설명

    def to_dict(self) -> Dict[str, Any]:
        return {
            'formation': self.formation,
            'name': self.name,
            'style': self.style,
            'buildup': self.buildup,
            'pressing': self.pressing,
            'space_utilization': self.space_utilization,
            'strengths': self.strengths,
            'weaknesses': self.weaknesses,
            'note': self.note
        }


# ==========================================================================
# Team Strength Data Models
# ==========================================================================

@dataclass
class TeamStrengthRatings:
    """팀 전력 평가 (실제 JSON 구조 기반)"""
    tactical_understanding: float    # 0.0-5.0
    positioning_balance: float       # 0.0-5.0
    buildup_quality: float           # 0.0-5.0

    def __post_init__(self):
        assert 0.0 <= self.tactical_understanding <= 5.0
        assert 0.0 <= self.positioning_balance <= 5.0
        assert 0.0 <= self.buildup_quality <= 5.0


# ==========================================================================
# Enriched Team Input
# ==========================================================================

@dataclass
class EnrichedTeamInput:
    """
    팀 Domain Input (100% 사용자 입력 기반)

    데이터 소스:
    1. SQLite: player_ratings (선수별 속성 + _comment) - 사용자 입력
    2. JSON: formations/{team}.json - 사용자 선택
    3. JSON: lineups/{team}.json - 사용자 구성
    4. JSON: team_strength/{team}.json (comment 포함) - 사용자 평가
    5. JSON: formation_tactics.json - 포메이션별 전술 특성 (사용자 선택에 따른 매핑)

    제거된 필드 (Static 데이터 제거):
    - tactics: 미리 정의된 전술 파라미터 제거
    - injuries: 라인업 구성 시 이미 제외됨
    - overall_scores: 계산값이므로 제거
    """
    name: str
    formation: str                              # "4-3-3", "4-4-2", etc. (사용자 선택)

    # 라인업 (포지션 → 선수 매핑) - 사용자 구성
    lineup: Dict[str, EnrichedPlayerInput]      # {"GK": player, "LB": player, ...}

    # 팀 전력 평가 (team_strength.json) - 사용자 평가
    team_strength_ratings: TeamStrengthRatings

    # 팀 전략 코멘터리 (핵심!) - team_strength.json의 comment (사용자 입력)
    team_strategy_commentary: Optional[str] = None

    # 포메이션 전술 특성 - 사용자가 선택한 포메이션에 매핑된 전술 정보
    formation_tactics: Optional[FormationTactics] = None

    # 계산된 팀 전력 (AI 프롬프트용) - 선수 속성에서 자동 계산
    derived_strengths: Optional['DerivedTeamStrengths'] = None

    def __post_init__(self):
        """검증 및 자동 계산"""
        # 라인업이 11명인지 확인
        if len(self.lineup) != 11:
            raise ValueError(f"Lineup must have exactly 11 players, got {len(self.lineup)}")

        # derived_strengths가 없으면 자동 계산
        if self.derived_strengths is None:
            self.derived_strengths = self._calculate_derived_strengths()

    def _calculate_derived_strengths(self) -> 'DerivedTeamStrengths':
        """
        11명 선수의 포지션별 속성에서 팀 전력 계산 (100% 사용자 입력 기반)

        계산 방법:
        1. Attack Strength: 공격수들의 공격 관련 속성 평균 (가중치 적용)
        2. Defense Strength: 수비수들의 수비 관련 속성 평균 (가중치 적용)
        3. Midfield Control: 미드필더들의 패스/컨트롤 속성 평균
        4. Physical Intensity: 전체 선수의 스피드/스태미나 속성 평균
        """
        # 포지션 분류
        attackers = []
        midfielders = []
        defenders = []

        for pos, player in self.lineup.items():
            if pos in ['ST', 'LW', 'RW', 'CF']:
                attackers.append(player)
            elif pos in ['CM', 'CDM', 'CAM', 'CM1', 'CM2', 'DM']:
                midfielders.append(player)
            elif pos in ['CB', 'LB', 'RB', 'CB1', 'CB2', 'CB-L', 'CB-R']:
                defenders.append(player)
            elif pos == 'GK':
                pass  # GK는 팀 전력 계산에서 제외 (특수 역할)
            else:
                # 알 수 없는 포지션은 미드필더로 분류
                midfielders.append(player)

        # 1. Attack Strength (0-100)
        attack_strength = self._calculate_attack_strength(attackers, midfielders)

        # 2. Defense Strength (0-100)
        defense_strength = self._calculate_defense_strength(defenders, midfielders)

        # 3. Midfield Control (0-100)
        midfield_control = self._calculate_midfield_control(midfielders)

        # 4. Physical Intensity (0-100)
        physical_intensity = self._calculate_physical_intensity(list(self.lineup.values()))

        return DerivedTeamStrengths(
            attack_strength=attack_strength,
            defense_strength=defense_strength,
            midfield_control=midfield_control,
            physical_intensity=physical_intensity
        )

    def _calculate_attack_strength(self,
                                   attackers: List[EnrichedPlayerInput],
                                   midfielders: List[EnrichedPlayerInput]) -> float:
        """
        공격력 계산 (0-100)

        가중치:
        - 공격수: 0.7
        - 미드필더: 0.3

        공격 관련 속성:
        - shooting_accuracy, cutting_in, one_on_one_beating (윙어/공격수)
        - 기타 공격 속성
        """
        if not attackers and not midfielders:
            return 50.0  # 기본값

        total_score = 0.0
        total_weight = 0.0

        # 공격수들의 overall_rating (가중치 0.7)
        for attacker in attackers:
            total_score += attacker.overall_rating * 20 * 0.7  # 5.0 → 100 스케일
            total_weight += 0.7

        # 미드필더들의 overall_rating (가중치 0.3)
        for midfielder in midfielders:
            total_score += midfielder.overall_rating * 20 * 0.3
            total_weight += 0.3

        return min(100.0, total_score / total_weight if total_weight > 0 else 50.0)

    def _calculate_defense_strength(self,
                                    defenders: List[EnrichedPlayerInput],
                                    midfielders: List[EnrichedPlayerInput]) -> float:
        """
        수비력 계산 (0-100)

        가중치:
        - 수비수: 0.7
        - 미드필더: 0.3

        수비 관련 속성:
        - tackle_marking, interception, positioning_reading (수비수)
        - defensive_contribution (미드필더/윙어)
        """
        if not defenders and not midfielders:
            return 50.0

        total_score = 0.0
        total_weight = 0.0

        # 수비수들의 overall_rating (가중치 0.7)
        for defender in defenders:
            total_score += defender.overall_rating * 20 * 0.7
            total_weight += 0.7

        # 미드필더들의 overall_rating (가중치 0.3)
        for midfielder in midfielders:
            total_score += midfielder.overall_rating * 20 * 0.3
            total_weight += 0.3

        return min(100.0, total_score / total_weight if total_weight > 0 else 50.0)

    def _calculate_midfield_control(self, midfielders: List[EnrichedPlayerInput]) -> float:
        """
        중원 지배력 계산 (0-100)

        미드필더들의 평균 rating 기반
        """
        if not midfielders:
            return 50.0

        avg_rating = sum(p.overall_rating for p in midfielders) / len(midfielders)
        return min(100.0, avg_rating * 20)  # 5.0 → 100 스케일

    def _calculate_physical_intensity(self, all_players: List[EnrichedPlayerInput]) -> float:
        """
        피지컬 강도 계산 (0-100)

        전체 선수들의 speed, acceleration 관련 속성 평균
        """
        if not all_players:
            return 50.0

        speed_attrs = ['speed', 'acceleration', 'speed_dribbling']

        total_speed = 0.0
        count = 0

        for player in all_players:
            for attr in speed_attrs:
                if attr in player.ratings:
                    total_speed += player.ratings[attr]
                    count += 1

        if count == 0:
            # speed 속성이 없으면 overall_rating 사용
            avg_overall = sum(p.overall_rating for p in all_players) / len(all_players)
            return min(100.0, avg_overall * 20)

        avg_speed = total_speed / count
        return min(100.0, avg_speed * 20)  # 5.0 → 100 스케일


    def get_key_players(self, top_n: int = 5) -> List[EnrichedPlayerInput]:
        """핵심 선수 top N 추출 (overall_rating 기준)"""
        sorted_players = sorted(
            self.lineup.values(),
            key=lambda p: p.overall_rating,
            reverse=True
        )
        return sorted_players[:top_n]

    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'formation': self.formation,
            'lineup': {pos: player.to_dict() for pos, player in self.lineup.items()},
            'team_strength_ratings': {
                'tactical_understanding': self.team_strength_ratings.tactical_understanding,
                'positioning_balance': self.team_strength_ratings.positioning_balance,
                'buildup_quality': self.team_strength_ratings.buildup_quality
            },
            'team_strategy_commentary': self.team_strategy_commentary,
            'formation_tactics': self.formation_tactics.to_dict() if self.formation_tactics else None,
            'derived_strengths': self.derived_strengths.to_dict() if self.derived_strengths else None
        }


@dataclass
class DerivedTeamStrengths:
    """
    계산된 팀 전력 (AI 프롬프트용, 100% 사용자 입력 기반)

    EnrichedTeamInput의 11명 선수 속성에서 자동 계산
    Static 데이터 제거: press_intensity, buildup_style (tactics 의존성 제거)
    """
    attack_strength: float        # 0-100
    defense_strength: float       # 0-100
    midfield_control: float       # 0-100
    physical_intensity: float     # 0-100

    def __post_init__(self):
        assert 0 <= self.attack_strength <= 100
        assert 0 <= self.defense_strength <= 100
        assert 0 <= self.midfield_control <= 100
        assert 0 <= self.physical_intensity <= 100

    def to_dict(self) -> Dict[str, Any]:
        return {
            'attack_strength': self.attack_strength,
            'defense_strength': self.defense_strength,
            'midfield_control': self.midfield_control,
            'physical_intensity': self.physical_intensity
        }


# ==========================================================================
# Testing
# ==========================================================================

def test_enriched_models():
    """Enriched Data Models 테스트"""
    print("=== Enriched Data Models 테스트 ===\n")

    # Test 1: EnrichedPlayerInput (CB 예시)
    print("Test 1: EnrichedPlayerInput (CB)")
    cb_player = EnrichedPlayerInput(
        player_id=67776,
        name="Jurriën Timber",
        position="Centre Central Defender",
        ratings={
            'positioning_reading': 4.25,
            'speed': 4.0,
            'aerial_duel': 2.5,
            'tackle_marking': 2.5,
            'interception': 2.5,
            'composure_judgement': 2.5,
            'buildup_contribution': 2.5,
            'leadership': 2.5,
            'passing': 2.5,
            'physical_jumping': 2.5
        },
        sub_position="CB",
        user_commentary="빠른 속도와 뛰어난 포지셔닝. 빌드업 능력 보통."
    )
    print(f"  Player: {cb_player.name} ({cb_player.position})")
    print(f"  Overall: {cb_player.overall_rating:.2f}")
    print(f"  Key strengths: {cb_player.get_key_strengths()}")
    print(f"  Commentary: {cb_player.user_commentary}")
    print(f"  ✅ EnrichedPlayerInput 생성 성공\n")

    print("=" * 50)
    print("✅ Enriched Data Models 테스트 통과!")
    print("  Note: TacticsInput 제거됨 (Static 데이터 제거)")
    print("=" * 50)


if __name__ == "__main__":
    test_enriched_models()
