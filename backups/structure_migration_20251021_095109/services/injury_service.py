"""
Injury Service - Hybrid approach
부상자 데이터 수집 및 관리 (API-Football + FBref Fallback)

Update Strategy (경기 근접도 기반):
- 5일 전: 1일 1회
- 4일 전: 1일 1회
- 3일 전: 1일 2회
- 2일 전: 1일 3회
- 1일 전: 1일 4회
- 당일: 2시간마다
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class InjuryService:
    """부상자 정보 관리 서비스 (하이브리드)"""

    # EPL League ID for API-Football
    EPL_LEAGUE_ID = 39
    SEASON = 2024

    # API-Football 팀 ID 매핑 (EPL 주요 팀)
    TEAM_ID_MAP = {
        'Arsenal': 42,
        'Aston Villa': 66,
        'Brighton': 51,
        'Burnley': 44,
        'Chelsea': 49,
        'Crystal Palace': 52,
        'Everton': 45,
        'Fulham': 36,
        'Liverpool': 40,
        'Man City': 50,
        'Man Utd': 33,
        'Newcastle': 34,
        'Nott\'m Forest': 65,
        'Sheffield Utd': 62,
        'Tottenham': 47,
        'West Ham': 48,
        'Wolves': 39,
        'Bournemouth': 35,
        'Brentford': 55,
        'Luton': 163
    }

    def __init__(self, api_key: Optional[str] = None, cache_dir: str = None):
        """
        Initialize Injury Service

        Args:
            api_key: API-Football RapidAPI key (optional, uses env var if not provided)
            cache_dir: Directory to store injury data cache
        """
        self.api_key = api_key or os.getenv('RAPIDAPI_KEY')

        if cache_dir is None:
            cache_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'injuries')

        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)

        self.api_base_url = "https://api-football-v1.p.rapidapi.com/v3"
        self.headers = {
            "X-RapidAPI-Key": self.api_key or "",
            "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
        }

        logger.info("InjuryService initialized")

    # ==========================================================================
    # PRIMARY: API-Football
    # ==========================================================================

    def fetch_injuries_from_api(self, team_name: str) -> Tuple[bool, Optional[List[Dict]], Optional[str]]:
        """
        API-Football에서 부상자 정보 가져오기 (Primary Source)

        Args:
            team_name: 팀 이름

        Returns:
            (success, injuries_list, error_message)
        """
        try:
            team_id = self.TEAM_ID_MAP.get(team_name)
            if not team_id:
                return False, None, f"Team '{team_name}' not found in mapping"

            if not self.api_key:
                logger.warning("RAPIDAPI_KEY not set, skipping API call")
                return False, None, "API key not configured"

            url = f"{self.api_base_url}/injuries"
            params = {
                'league': self.EPL_LEAGUE_ID,
                'season': self.SEASON,
                'team': team_id
            }

            logger.info(f"Fetching injuries from API-Football for {team_name} (team_id={team_id})")
            response = requests.get(url, headers=self.headers, params=params, timeout=10)

            if response.status_code != 200:
                return False, None, f"API returned status {response.status_code}"

            data = response.json()

            if 'response' not in data:
                return False, None, "Invalid API response format"

            # Parse injuries
            injuries = []
            for item in data['response']:
                player = item.get('player', {})
                fixture = item.get('fixture', {})

                injury = {
                    'player_id': player.get('id'),
                    'player_name': player.get('name'),
                    'player_photo': player.get('photo'),
                    'injury_type': item.get('type', 'Unknown'),
                    'reason': item.get('reason', 'Injury'),
                    'status': 'injured',
                    'fixture_id': fixture.get('id'),
                    'fixture_date': fixture.get('date'),
                    'source': 'api-football'
                }

                injuries.append(injury)

            logger.info(f"✅ API-Football: Found {len(injuries)} injuries for {team_name}")
            return True, injuries, None

        except requests.Timeout:
            return False, None, "API request timeout"
        except Exception as e:
            logger.error(f"API-Football error: {str(e)}", exc_info=True)
            return False, None, str(e)

    # ==========================================================================
    # FALLBACK: FBref Web Scraping
    # ==========================================================================

    def fetch_injuries_from_fbref(self, team_name: str) -> Tuple[bool, Optional[List[Dict]], Optional[str]]:
        """
        FBref에서 부상자 정보 스크래핑 (Fallback Source)

        Args:
            team_name: 팀 이름

        Returns:
            (success, injuries_list, error_message)
        """
        try:
            # FBref 팀 ID 매핑 (필요 시 확장)
            fbref_team_map = {
                'Arsenal': '18bb7c10',
                'Liverpool': '822bd0ba',
                'Man City': 'b8fd03ef',
                'Man Utd': '19538871',
                'Chelsea': 'cff3d9bb',
                'Tottenham': '361ca564',
                # 추가 필요...
            }

            team_id = fbref_team_map.get(team_name)
            if not team_id:
                return False, None, f"FBref mapping not found for {team_name}"

            url = f"https://fbref.com/en/squads/{team_id}/injuries/{team_name}-Injuries"

            logger.info(f"Scraping injuries from FBref for {team_name}")
            response = requests.get(url, timeout=10)

            if response.status_code != 200:
                return False, None, f"FBref returned status {response.status_code}"

            soup = BeautifulSoup(response.content, 'html.parser')

            # Parse injury table
            injuries = []
            injury_table = soup.find('table', {'id': 'injuries'})

            if injury_table:
                rows = injury_table.find('tbody').find_all('tr')

                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 4:
                        player_name = cols[0].text.strip()
                        injury_type = cols[1].text.strip()
                        days_out = cols[2].text.strip()

                        injury = {
                            'player_id': None,
                            'player_name': player_name,
                            'player_photo': None,
                            'injury_type': injury_type,
                            'days_out': days_out,
                            'status': 'injured',
                            'source': 'fbref'
                        }

                        injuries.append(injury)

            logger.info(f"✅ FBref: Found {len(injuries)} injuries for {team_name}")
            return True, injuries, None

        except Exception as e:
            logger.error(f"FBref scraping error: {str(e)}", exc_info=True)
            return False, None, str(e)

    # ==========================================================================
    # HYBRID: Primary + Fallback
    # ==========================================================================

    def get_team_injuries(self, team_name: str, force_refresh: bool = False) -> Dict:
        """
        팀의 부상자 정보 가져오기 (하이브리드)

        1. Cache 확인 (유효한 경우 반환)
        2. API-Football 시도
        3. 실패 시 FBref Fallback
        4. Cache 저장

        Args:
            team_name: 팀 이름
            force_refresh: 강제 갱신 여부

        Returns:
            {
                'team_name': str,
                'last_updated': str,
                'source': str,
                'injuries': List[Dict],
                'total_injured': int
            }
        """
        # 1. Check cache
        if not force_refresh:
            cached = self._get_from_cache(team_name)
            if cached:
                logger.info(f"📦 Cache hit for {team_name} injuries")
                return cached

        # 2. Try API-Football (Primary)
        success, injuries, error = self.fetch_injuries_from_api(team_name)
        source = 'api-football'

        # 3. Fallback to FBref
        if not success:
            logger.warning(f"API-Football failed for {team_name}: {error}, trying FBref...")
            success, injuries, error = self.fetch_injuries_from_fbref(team_name)
            source = 'fbref'

        # 4. Return empty if both failed
        if not success:
            logger.error(f"Both sources failed for {team_name}: {error}")
            return {
                'team_name': team_name,
                'last_updated': datetime.utcnow().isoformat(),
                'source': 'none',
                'injuries': [],
                'total_injured': 0,
                'error': error
            }

        # 5. Build result
        result = {
            'team_name': team_name,
            'last_updated': datetime.utcnow().isoformat(),
            'source': source,
            'injuries': injuries or [],
            'total_injured': len(injuries or [])
        }

        # 6. Save to cache
        self._save_to_cache(team_name, result)

        return result

    # ==========================================================================
    # CACHING
    # ==========================================================================

    def _get_cache_path(self, team_name: str) -> str:
        """Get cache file path for team"""
        return os.path.join(self.cache_dir, f"{team_name}.json")

    def _get_from_cache(self, team_name: str) -> Optional[Dict]:
        """Get injury data from cache if valid"""
        cache_path = self._get_cache_path(team_name)

        if not os.path.exists(cache_path):
            return None

        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Check if cache is still valid (based on match proximity)
            last_updated = datetime.fromisoformat(data['last_updated'])
            cache_duration = self._get_cache_duration()

            if datetime.utcnow() - last_updated < timedelta(seconds=cache_duration):
                return data

            logger.info(f"Cache expired for {team_name}")
            return None

        except Exception as e:
            logger.error(f"Cache read error: {str(e)}")
            return None

    def _save_to_cache(self, team_name: str, data: Dict):
        """Save injury data to cache"""
        try:
            cache_path = self._get_cache_path(team_name)

            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.info(f"💾 Cached injury data for {team_name}")

        except Exception as e:
            logger.error(f"Cache save error: {str(e)}")

    def _get_cache_duration(self) -> int:
        """
        경기 근접도 기반 캐시 유효 시간 계산

        Returns:
            Cache duration in seconds
        """
        # TODO: 실제 다음 경기일을 가져와서 계산
        # 현재는 기본값으로 6시간 설정
        days_until_match = self._get_days_until_next_match()

        if days_until_match is None or days_until_match >= 5:
            # 5일 이상: 1일 1회 → 24시간 캐시
            return 24 * 3600
        elif days_until_match == 4:
            # 4일 전: 1일 1회 → 24시간 캐시
            return 24 * 3600
        elif days_until_match == 3:
            # 3일 전: 1일 2회 → 12시간 캐시
            return 12 * 3600
        elif days_until_match == 2:
            # 2일 전: 1일 3회 → 8시간 캐시
            return 8 * 3600
        elif days_until_match == 1:
            # 1일 전: 1일 4회 → 6시간 캐시
            return 6 * 3600
        else:
            # 당일: 2시간마다 → 2시간 캐시
            return 2 * 3600

    def _get_days_until_next_match(self) -> Optional[int]:
        """
        다음 경기까지 남은 일수 계산

        Returns:
            Days until next match, or None if not available
        """
        # TODO: EPL 경기 일정 API와 연동하여 실제 다음 경기일 가져오기
        # 현재는 임시로 None 반환 (기본값 사용)
        return None

    # ==========================================================================
    # UPDATE SCHEDULER
    # ==========================================================================

    def update_all_teams(self, force: bool = False) -> Dict[str, Dict]:
        """
        모든 팀의 부상자 정보 업데이트

        Args:
            force: 강제 갱신 여부

        Returns:
            {team_name: result_dict}
        """
        results = {}

        for team_name in self.TEAM_ID_MAP.keys():
            logger.info(f"Updating injuries for {team_name}...")
            result = self.get_team_injuries(team_name, force_refresh=force)
            results[team_name] = result

        return results

    def get_update_frequency_info(self) -> Dict:
        """
        현재 업데이트 빈도 정보 반환

        Returns:
            {
                'days_until_match': int,
                'updates_per_day': int,
                'cache_duration_hours': float,
                'strategy': str
            }
        """
        days_until_match = self._get_days_until_next_match()
        cache_seconds = self._get_cache_duration()
        cache_hours = cache_seconds / 3600
        updates_per_day = 24 / cache_hours

        if days_until_match is None or days_until_match >= 5:
            strategy = "5일 이상: 1일 1회"
        elif days_until_match == 4:
            strategy = "4일 전: 1일 1회"
        elif days_until_match == 3:
            strategy = "3일 전: 1일 2회"
        elif days_until_match == 2:
            strategy = "2일 전: 1일 3회"
        elif days_until_match == 1:
            strategy = "1일 전: 1일 4회"
        else:
            strategy = "당일: 2시간마다"

        return {
            'days_until_match': days_until_match,
            'updates_per_day': updates_per_day,
            'cache_duration_hours': cache_hours,
            'strategy': strategy
        }


# Global service instance
_injury_service = None


def get_injury_service() -> InjuryService:
    """Get global injury service instance (singleton)"""
    global _injury_service
    if _injury_service is None:
        _injury_service = InjuryService()
    return _injury_service


# CLI usage example
if __name__ == "__main__":
    service = InjuryService()

    # Test Arsenal injuries
    print("=== Arsenal Injuries ===")
    result = service.get_team_injuries('Arsenal', force_refresh=True)
    print(f"Source: {result['source']}")
    print(f"Total Injured: {result['total_injured']}")
    print(f"Last Updated: {result['last_updated']}")

    for injury in result['injuries']:
        print(f"  - {injury['player_name']}: {injury['injury_type']}")

    # Test update frequency
    print("\n=== Update Frequency ===")
    freq_info = service.get_update_frequency_info()
    print(f"Strategy: {freq_info['strategy']}")
    print(f"Updates per day: {freq_info['updates_per_day']}")
    print(f"Cache duration: {freq_info['cache_duration_hours']} hours")
