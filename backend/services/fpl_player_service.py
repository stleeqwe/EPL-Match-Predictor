"""
FPL Player Service
Fantasy Premier League API에서 선수 통계 조회
"""

import requests
import logging
from typing import Dict, Optional, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class FPLPlayerService:
    """FPL API 선수 스탯 조회 서비스"""

    FPL_BASE_URL = "https://fantasy.premierleague.com/api"
    CACHE_TTL = 3600  # 1시간 캐시

    def __init__(self):
        self._cache = {}
        self._cache_time = None

    def _fetch_bootstrap_data(self) -> Optional[Dict]:
        """
        FPL Bootstrap 데이터 조회 (전체 선수 목록)

        Returns:
            Dict with 'elements' (players), 'teams', 'element_types' (positions)
        """
        # 캐시 확인
        if self._cache and self._cache_time:
            if datetime.now() - self._cache_time < timedelta(seconds=self.CACHE_TTL):
                logger.debug("FPL bootstrap data from cache")
                return self._cache

        try:
            url = f"{self.FPL_BASE_URL}/bootstrap-static/"
            logger.info(f"Fetching FPL bootstrap data from: {url}")

            response = requests.get(url, timeout=10)
            response.raise_for_status()

            data = response.json()

            # 캐시 저장
            self._cache = data
            self._cache_time = datetime.now()

            logger.info(f"FPL bootstrap data fetched: {len(data.get('elements', []))} players")
            return data

        except requests.RequestException as e:
            logger.error(f"FPL API request failed: {e}")
            return None
        except Exception as e:
            logger.error(f"FPL data fetch error: {e}")
            return None

    def get_player_by_name(self, player_name: str, team_name: Optional[str] = None) -> Optional[Dict]:
        """
        선수 이름으로 FPL 데이터 조회

        Args:
            player_name: 선수 이름
            team_name: 팀 이름 (선택, 동명이인 구분용)

        Returns:
            FPL 선수 데이터 또는 None
        """
        bootstrap = self._fetch_bootstrap_data()
        if not bootstrap:
            return None

        players = bootstrap.get('elements', [])
        teams = {team['id']: team['name'] for team in bootstrap.get('teams', [])}

        # 정확한 이름 매칭
        matches = []
        for player in players:
            fpl_name = player.get('web_name', '') or player.get('second_name', '')

            # 이름 매칭 (대소문자 무시)
            if player_name.lower() in fpl_name.lower() or fpl_name.lower() in player_name.lower():
                player['team_name'] = teams.get(player['team'])
                matches.append(player)

        if not matches:
            logger.warning(f"No FPL player found for: {player_name}")
            return None

        # 팀 이름으로 필터링
        if team_name and len(matches) > 1:
            team_matches = [p for p in matches if team_name.lower() in p.get('team_name', '').lower()]
            if team_matches:
                matches = team_matches

        # 첫 번째 매칭 반환
        player = matches[0]
        logger.info(f"FPL player found: {player.get('web_name')} ({player.get('team_name')})")
        return player

    def get_player_stats(self, player_name: str, team_name: Optional[str] = None) -> Optional[Dict]:
        """
        선수 통계 조회 (AI 생성용)

        Args:
            player_name: 선수 이름
            team_name: 팀 이름 (선택)

        Returns:
            {
                'name': str,
                'team': str,
                'position': str,  # GK, DEF, MID, FWD
                'minutes': int,
                'goals': int,
                'assists': int,
                'clean_sheets': int,
                'form': str,
                'selected_by': str,  # percentage
                'bonus': int,
                'total_points': int,
                'value': float  # millions
            }
        """
        player = self.get_player_by_name(player_name, team_name)
        if not player:
            return None

        # 포지션 매핑
        position_map = {
            1: 'GK',   # Goalkeeper
            2: 'DEF',  # Defender
            3: 'MID',  # Midfielder
            4: 'FWD'   # Forward
        }

        stats = {
            'name': player.get('web_name') or player.get('second_name', ''),
            'full_name': f"{player.get('first_name', '')} {player.get('second_name', '')}".strip(),
            'team': player.get('team_name', 'Unknown'),
            'position': position_map.get(player.get('element_type'), 'MID'),
            'minutes': player.get('minutes', 0),
            'goals': player.get('goals_scored', 0),
            'assists': player.get('assists', 0),
            'clean_sheets': player.get('clean_sheets', 0),
            'form': player.get('form', '0.0'),
            'selected_by': player.get('selected_by_percent', '0.0'),
            'bonus': player.get('bonus', 0),
            'total_points': player.get('total_points', 0),
            'value': player.get('now_cost', 0) / 10.0,  # Convert to millions
            'ict_index': player.get('ict_index', '0.0')
        }

        logger.info(f"FPL stats for {stats['name']}: {stats['goals']}G {stats['assists']}A in {stats['minutes']}min")
        return stats

    def search_players(self, query: str, limit: int = 10) -> List[Dict]:
        """
        선수 검색 (자동완성용)

        Args:
            query: 검색어
            limit: 최대 결과 수

        Returns:
            List of player dicts
        """
        bootstrap = self._fetch_bootstrap_data()
        if not bootstrap:
            return []

        players = bootstrap.get('elements', [])
        teams = {team['id']: team['name'] for team in bootstrap.get('teams', [])}

        results = []
        query_lower = query.lower()

        for player in players:
            name = player.get('web_name', '') or player.get('second_name', '')
            if query_lower in name.lower():
                results.append({
                    'id': player['id'],
                    'name': name,
                    'team': teams.get(player['team']),
                    'position': ['GK', 'DEF', 'MID', 'FWD'][player.get('element_type', 1) - 1]
                })

                if len(results) >= limit:
                    break

        return results


# Singleton instance
_fpl_service = None


def get_fpl_service() -> FPLPlayerService:
    """Get global FPL service instance"""
    global _fpl_service
    if _fpl_service is None:
        _fpl_service = FPLPlayerService()
    return _fpl_service


if __name__ == "__main__":
    # 테스트
    logging.basicConfig(level=logging.INFO)

    service = FPLPlayerService()

    # Test 1: Bukayo Saka
    print("\n" + "=" * 80)
    print("Test 1: Bukayo Saka")
    print("=" * 80)
    stats = service.get_player_stats("Saka", "Arsenal")
    if stats:
        print(f"Name: {stats['name']}")
        print(f"Team: {stats['team']}")
        print(f"Position: {stats['position']}")
        print(f"Stats: {stats['goals']}G, {stats['assists']}A in {stats['minutes']} minutes")
        print(f"Form: {stats['form']}")
        print(f"Selected by: {stats['selected_by']}%")

    # Test 2: Erling Haaland
    print("\n" + "=" * 80)
    print("Test 2: Erling Haaland")
    print("=" * 80)
    stats = service.get_player_stats("Haaland", "Man City")
    if stats:
        print(f"Name: {stats['name']}")
        print(f"Team: {stats['team']}")
        print(f"Stats: {stats['goals']}G, {stats['assists']}A")

    # Test 3: Search
    print("\n" + "=" * 80)
    print("Test 3: Search 'Salah'")
    print("=" * 80)
    results = service.search_players("Salah")
    for player in results:
        print(f"  - {player['name']} ({player['team']}, {player['position']})")
