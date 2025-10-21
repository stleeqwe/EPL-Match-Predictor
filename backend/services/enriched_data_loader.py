"""
Enriched Domain Data Loader
실제 프론트엔드 저장 구조에서 EnrichedTeamInput으로 데이터 로드 (100% 사용자 입력 기반)

데이터 소스:
1. SQLite: player_ratings (선수별 속성 + _comment) - 사용자 입력
2. JSON: formations/{team}.json - 사용자 선택
3. JSON: lineups/{team}.json - 사용자 구성
4. JSON: team_strength/{team}.json (comment 포함) - 사용자 평가

제거된 데이터:
- tactics (Static 데이터 제거: AI 시나리오 생성에 영향 방지)
"""

import os
import sys
import json
from typing import Dict, List, Optional, Tuple
from pathlib import Path

# 경로 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from database.player_schema import Player, PlayerRating, get_player_session
from ai.enriched_data_models import (
    EnrichedPlayerInput,
    EnrichedTeamInput,
    TeamStrengthRatings
)


# ==========================================================================
# Constants
# ==========================================================================

# SQLite DB 경로 (절대 경로로 변환)
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'epl_data.db'))

# JSON 디렉토리 경로
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
FORMATIONS_DIR = os.path.join(DATA_DIR, 'formations')
LINEUPS_DIR = os.path.join(DATA_DIR, 'lineups')
TEAM_STRENGTH_DIR = os.path.join(DATA_DIR, 'team_strength')


# ==========================================================================
# Exceptions
# ==========================================================================

class DataLoaderError(Exception):
    """데이터 로더 기본 예외"""
    pass


class PlayerNotFoundError(DataLoaderError):
    """선수를 찾을 수 없음"""
    pass


class FileNotFoundError(DataLoaderError):
    """필수 파일을 찾을 수 없음"""
    pass


class IncompleteDataError(DataLoaderError):
    """불완전한 데이터"""
    pass


# ==========================================================================
# SQLite Repository
# ==========================================================================

class PlayerRatingsRepository:
    """
    SQLite player_ratings 테이블에서 데이터 로드

    데이터 구조:
    - 포지션별로 다른 속성 (10-12개)
    - _comment: attribute로 저장, notes에 코멘터리
    - _subPosition: attribute로 저장, notes에 포지션
    """

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    def get_player_ratings(self,
                          player_id: int,
                          user_id: str = 'default') -> Tuple[Player, Dict[str, float], Optional[str], Optional[str]]:
        """
        선수 평가 데이터 조회

        Returns:
            (Player, ratings_dict, sub_position, user_commentary)

        Raises:
            PlayerNotFoundError: 선수를 찾을 수 없음
        """
        session = None
        try:
            session = get_player_session(self.db_path)

            # 선수 정보 조회
            player = session.query(Player).filter_by(id=player_id).first()
            if not player:
                raise PlayerNotFoundError(f"Player with ID {player_id} not found in database")

            # 선수 평가 조회
            ratings_records = session.query(PlayerRating).filter_by(
                player_id=player_id,
                user_id=user_id
            ).all()

            if not ratings_records:
                # 평가가 없는 경우
                return (player, {}, None, None)

            # 데이터 파싱
            ratings_dict = {}
            sub_position = None
            user_commentary = None

            for record in ratings_records:
                if record.attribute_name == '_comment':
                    # 코멘터리는 notes에 저장됨
                    user_commentary = record.notes if record.notes else None
                elif record.attribute_name == '_subPosition':
                    # 세부 포지션은 notes에 저장됨
                    sub_position = record.notes if record.notes else None
                elif not record.attribute_name.startswith('_'):
                    # 일반 속성
                    ratings_dict[record.attribute_name] = record.rating

            return (player, ratings_dict, sub_position, user_commentary)

        except Exception as e:
            if isinstance(e, PlayerNotFoundError):
                raise
            raise DataLoaderError(f"Failed to load player ratings: {str(e)}")
        finally:
            if session:
                session.close()

    def get_player_by_id(self, player_id: int) -> Optional[Player]:
        """선수 기본 정보만 조회"""
        session = None
        try:
            session = get_player_session(self.db_path)
            return session.query(Player).filter_by(id=player_id).first()
        finally:
            if session:
                session.close()


# ==========================================================================
# JSON Loaders
# ==========================================================================

def load_json_file(file_path: str) -> Dict:
    """JSON 파일 로드 (에러 처리 포함)"""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"JSON file not found: {file_path}")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise DataLoaderError(f"Invalid JSON format in {file_path}: {str(e)}")


def load_formation(team_name: str) -> str:
    """포메이션 로드"""
    file_path = os.path.join(FORMATIONS_DIR, f"{team_name}.json")
    data = load_json_file(file_path)

    if 'formation' not in data:
        raise IncompleteDataError(f"Formation data missing 'formation' field: {file_path}")

    return data['formation']


def load_lineup(team_name: str) -> Dict[str, int]:
    """
    라인업 로드

    Returns:
        {"GK": player_id, "LB": player_id, ...}
    """
    file_path = os.path.join(LINEUPS_DIR, f"{team_name}.json")
    data = load_json_file(file_path)

    if 'lineup' not in data:
        raise IncompleteDataError(f"Lineup data missing 'lineup' field: {file_path}")

    lineup = data['lineup']

    if len(lineup) != 11:
        raise IncompleteDataError(
            f"Lineup must have exactly 11 players, got {len(lineup)}: {file_path}"
        )

    return lineup


# load_tactics() REMOVED - Static 데이터 제거 (AI 시나리오 생성에 영향 방지)


def load_formation_tactics(formation: str) -> Optional['FormationTactics']:
    """
    포메이션 전술 정보 로드

    Args:
        formation: 포메이션 이름 (예: "4-3-3", "4-2-3-1")

    Returns:
        FormationTactics or None if not found
    """
    from ai.enriched_data_models import FormationTactics

    file_path = os.path.join(DATA_DIR, 'formation_tactics.json')

    try:
        data = load_json_file(file_path)

        if 'formation_tactics' not in data:
            print(f"⚠️  Formation tactics file missing 'formation_tactics' field")
            return None

        tactics_data = data['formation_tactics'].get(formation)
        if not tactics_data:
            print(f"⚠️  Formation tactics not found for: {formation}")
            return None

        return FormationTactics(
            formation=formation,
            name=tactics_data['name'],
            style=tactics_data['style'],
            buildup=tactics_data['buildup'],
            pressing=tactics_data['pressing'],
            space_utilization=tactics_data['space_utilization'],
            strengths=tactics_data['strengths'],
            weaknesses=tactics_data['weaknesses'],
            note=tactics_data.get('note')
        )
    except FileNotFoundError:
        print(f"⚠️  Formation tactics file not found: {file_path}")
        return None
    except Exception as e:
        print(f"⚠️  Failed to load formation tactics: {str(e)}")
        return None


def load_team_strength(team_name: str) -> Tuple[TeamStrengthRatings, Optional[str]]:
    """
    팀 전력 평가 로드

    Returns:
        (TeamStrengthRatings, team_strategy_commentary)
    """
    file_path = os.path.join(TEAM_STRENGTH_DIR, f"{team_name}.json")
    data = load_json_file(file_path)

    if 'ratings' not in data:
        raise IncompleteDataError(f"Team strength data missing 'ratings' field: {file_path}")

    ratings = data['ratings']

    try:
        team_strength_ratings = TeamStrengthRatings(
            tactical_understanding=ratings['tactical_understanding'],
            positioning_balance=ratings['positioning_balance'],
            buildup_quality=ratings['buildup_quality']
        )

        # 팀 전략 코멘터리 (선택 필드)
        team_commentary = data.get('comment', None)

        return (team_strength_ratings, team_commentary)
    except KeyError as e:
        raise IncompleteDataError(f"Team strength ratings missing field: {str(e)}")


# ==========================================================================
# Main Data Loader
# ==========================================================================

class EnrichedDomainDataLoader:
    """
    프론트엔드 저장 데이터를 EnrichedTeamInput으로 로드

    사용법:
        loader = EnrichedDomainDataLoader()
        team_input = loader.load_team_data("Arsenal")
    """

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.player_repo = PlayerRatingsRepository(db_path)

    def load_team_data(self, team_name: str) -> EnrichedTeamInput:
        """
        팀 전체 데이터 로드 (100% 사용자 입력 기반)

        단계:
        1. Formation 로드
        2. Lineup 로드 (11명 player_id)
        3. 각 선수의 평가 데이터 로드 (SQLite)
        4. Team Strength 로드
        5. EnrichedTeamInput 조합

        Args:
            team_name: 팀 이름 (예: "Arsenal")

        Returns:
            EnrichedTeamInput

        Raises:
            FileNotFoundError: 필수 파일 없음
            IncompleteDataError: 불완전한 데이터
            PlayerNotFoundError: 선수 평가 없음
        """
        print(f"\n{'='*70}")
        print(f"📂 Loading team data: {team_name}")
        print(f"{'='*70}\n")

        try:
            # Step 1: Formation 로드
            print("Step 1/5: Loading formation...")
            formation = load_formation(team_name)
            print(f"  ✅ Formation: {formation}")

            # Step 1.5: Formation Tactics 로드
            print("\nStep 1.5/5: Loading formation tactics...")
            formation_tactics = load_formation_tactics(formation)
            if formation_tactics:
                print(f"  ✅ Formation Tactics: {formation_tactics.name} ({formation_tactics.style})")
                print(f"      Buildup: {formation_tactics.buildup[:50]}...")
                print(f"      Pressing: {formation_tactics.pressing[:50]}...")
            else:
                print(f"  ⚠️  Formation tactics not found for {formation}")

            # Step 2: Lineup 로드
            print("\nStep 2/5: Loading lineup...")
            lineup_dict = load_lineup(team_name)
            print(f"  ✅ Lineup: {len(lineup_dict)} players")

            # Step 3: 각 선수의 평가 데이터 로드
            print("\nStep 3/5: Loading player ratings from database...")
            enriched_lineup = {}

            for position, player_id in lineup_dict.items():
                try:
                    player, ratings, sub_pos, commentary = self.player_repo.get_player_ratings(player_id)

                    enriched_player = EnrichedPlayerInput(
                        player_id=player_id,
                        name=player.name,
                        position=player.position,
                        ratings=ratings,
                        sub_position=sub_pos,
                        user_commentary=commentary
                    )

                    enriched_lineup[position] = enriched_player

                    # 로그 출력
                    rating_str = f"{enriched_player.overall_rating:.2f}" if ratings else "N/A"
                    commentary_str = f" | Commentary: {commentary[:30]}..." if commentary else ""
                    print(f"    [{position:6s}] {player.name:25s} (Rating: {rating_str}){commentary_str}")

                except PlayerNotFoundError as e:
                    print(f"    ⚠️  [{position}] Player {player_id} not found in database")
                    raise

            print(f"  ✅ Loaded {len(enriched_lineup)} player ratings")

            # Step 4: Team Strength 로드
            print("\nStep 4/5: Loading team strength...")
            team_strength_ratings, team_commentary = load_team_strength(team_name)
            print(f"  ✅ Team strength loaded:")
            print(f"      Tactical Understanding: {team_strength_ratings.tactical_understanding:.2f}")
            print(f"      Positioning Balance: {team_strength_ratings.positioning_balance:.2f}")
            print(f"      Buildup Quality: {team_strength_ratings.buildup_quality:.2f}")
            if team_commentary:
                print(f"      Team Commentary: {team_commentary}")

            # Step 5: EnrichedTeamInput 조합
            print("\nStep 5/5: Creating EnrichedTeamInput...")
            team_input = EnrichedTeamInput(
                name=team_name,
                formation=formation,
                lineup=enriched_lineup,
                team_strength_ratings=team_strength_ratings,
                team_strategy_commentary=team_commentary,
                formation_tactics=formation_tactics
            )

            # derived_strengths 자동 계산됨 (__post_init__)
            print(f"  ✅ Derived team strengths (auto-calculated from user input):")
            if team_input.derived_strengths:
                ds = team_input.derived_strengths
                print(f"      Attack Strength: {ds.attack_strength:.1f}/100")
                print(f"      Defense Strength: {ds.defense_strength:.1f}/100")
                print(f"      Midfield Control: {ds.midfield_control:.1f}/100")
                print(f"      Physical Intensity: {ds.physical_intensity:.1f}/100")

            print(f"\n{'='*70}")
            print(f"✅ Successfully loaded {team_name} data!")
            print(f"{'='*70}\n")

            return team_input

        except (FileNotFoundError, IncompleteDataError, PlayerNotFoundError) as e:
            print(f"\n❌ Failed to load {team_name} data: {str(e)}\n")
            raise
        except Exception as e:
            print(f"\n❌ Unexpected error loading {team_name} data: {str(e)}\n")
            raise DataLoaderError(f"Unexpected error: {str(e)}")

    def check_team_data_availability(self, team_name: str) -> Dict[str, bool]:
        """
        팀 데이터 가용성 확인 (실제 로드 없이)

        Returns:
            {
                'formation': True/False,
                'lineup': True/False,
                'team_strength': True/False,
                'all_ready': True/False
            }
        """
        status = {}

        # Formation 확인
        formation_path = os.path.join(FORMATIONS_DIR, f"{team_name}.json")
        status['formation'] = os.path.exists(formation_path)

        # Lineup 확인
        lineup_path = os.path.join(LINEUPS_DIR, f"{team_name}.json")
        status['lineup'] = os.path.exists(lineup_path)

        # Team Strength 확인
        team_strength_path = os.path.join(TEAM_STRENGTH_DIR, f"{team_name}.json")
        status['team_strength'] = os.path.exists(team_strength_path)

        # 모두 준비됨
        status['all_ready'] = all([
            status['formation'],
            status['lineup'],
            status['team_strength']
        ])

        return status


# ==========================================================================
# Testing
# ==========================================================================

def test_loader():
    """EnrichedDomainDataLoader 테스트"""
    print("=== EnrichedDomainDataLoader 테스트 ===\n")

    loader = EnrichedDomainDataLoader()

    # Arsenal 데이터 로드
    team_name = "Arsenal"

    try:
        # 가용성 확인
        print(f"Checking data availability for {team_name}...")
        status = loader.check_team_data_availability(team_name)
        print(f"  Formation: {'✅' if status['formation'] else '❌'}")
        print(f"  Lineup: {'✅' if status['lineup'] else '❌'}")
        print(f"  Team Strength: {'✅' if status['team_strength'] else '❌'}")
        print(f"  All Ready: {'✅' if status['all_ready'] else '❌'}\n")

        if not status['all_ready']:
            print(f"⚠️  {team_name} data is not complete. Skipping load test.")
            return

        # 실제 로드
        team_input = loader.load_team_data(team_name)

        # 결과 검증
        print("\n=== Validation ===")
        print(f"✅ Team Name: {team_input.name}")
        print(f"✅ Formation: {team_input.formation}")
        print(f"✅ Lineup Size: {len(team_input.lineup)} players")
        print(f"✅ Team Commentary: {team_input.team_strategy_commentary}")

        # 핵심 선수 확인
        key_players = team_input.get_key_players(top_n=3)
        print(f"\n🌟 Top 3 Key Players:")
        for i, player in enumerate(key_players, 1):
            commentary = f" - {player.user_commentary}" if player.user_commentary else ""
            print(f"  {i}. {player.name} (Rating: {player.overall_rating:.2f}){commentary}")

        print("\n✅ All tests passed!")

    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_loader()
