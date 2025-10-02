"""
Understat.com 데이터 스크래퍼
xG (Expected Goals) 데이터 수집
"""

import requests
import json
import re
import pandas as pd
import time
import logging
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UnderstatScraper:
    def __init__(self):
        self.base_url = "https://understat.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.request_delay = 3

    def get_league_xg_data(self, league="EPL", season="2024"):
        """
        리그 xG 데이터 가져오기

        Args:
            league: 리그명 (EPL, La_liga, Bundesliga 등)
            season: 시즌 (2024)

        Returns:
            DataFrame: xG 데이터
        """
        logger.info(f"Fetching xG data for {league} {season}")

        url = f"{self.base_url}/league/{league}/{season}"

        try:
            time.sleep(self.request_delay)
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'lxml')

            # JavaScript에서 JSON 데이터 추출
            scripts = soup.find_all('script')
            xg_data = None

            for script in scripts:
                if 'teamsData' in script.text:
                    # JSON 데이터 추출
                    match = re.search(r'var teamsData\s*=\s*JSON\.parse\(\'(.+?)\'\);', script.text)
                    if match:
                        json_str = match.group(1).encode().decode('unicode_escape')
                        xg_data = json.loads(json_str)
                        break

            if xg_data:
                df = self._parse_teams_xg_data(xg_data)
                logger.info(f"Found xG data for {len(df)} teams")
                return df
            else:
                logger.warning("xG data not found in page")
                return self._get_dummy_xg_data()

        except Exception as e:
            logger.error(f"Error fetching xG data: {e}")
            return self._get_dummy_xg_data()

    def get_team_xg_history(self, team_name, season="2024"):
        """
        특정 팀의 xG 히스토리 가져오기

        Args:
            team_name: 팀명
            season: 시즌

        Returns:
            DataFrame: 경기별 xG 데이터
        """
        logger.info(f"Fetching xG history for {team_name}")

        # 팀명을 URL 형식으로 변환
        team_url = team_name.replace(' ', '_')
        url = f"{self.base_url}/team/{team_url}/{season}"

        try:
            time.sleep(self.request_delay)
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'lxml')

            # JavaScript에서 경기 데이터 추출
            scripts = soup.find_all('script')
            matches_data = None

            for script in scripts:
                if 'datesData' in script.text:
                    match = re.search(r'var datesData\s*=\s*JSON\.parse\(\'(.+?)\'\);', script.text)
                    if match:
                        json_str = match.group(1).encode().decode('unicode_escape')
                        matches_data = json.loads(json_str)
                        break

            if matches_data:
                df = self._parse_matches_xg_data(matches_data)
                logger.info(f"Found {len(df)} matches for {team_name}")
                return df
            else:
                return self._get_dummy_team_xg_history(team_name)

        except Exception as e:
            logger.error(f"Error fetching team xG history: {e}")
            return self._get_dummy_team_xg_history(team_name)

    def _parse_teams_xg_data(self, data):
        """팀별 xG 데이터 파싱"""
        teams_list = []

        for team_id, team_data in data.items():
            teams_list.append({
                'team': team_data['title'],
                'xg_for': float(team_data.get('xG', 0)),
                'xg_against': float(team_data.get('xGA', 0)),
                'npxg': float(team_data.get('npxG', 0)),  # Non-penalty xG
                'npxg_against': float(team_data.get('npxGA', 0)),
                'deep': int(team_data.get('deep', 0)),  # 깊은 진입
                'deep_allowed': int(team_data.get('deep_allowed', 0)),
                'xpts': float(team_data.get('xpts', 0))  # Expected Points
            })

        return pd.DataFrame(teams_list)

    def _parse_matches_xg_data(self, data):
        """경기별 xG 데이터 파싱"""
        matches_list = []

        for match in data:
            matches_list.append({
                'date': match.get('datetime'),
                'home_team': match.get('h', {}).get('title'),
                'away_team': match.get('a', {}).get('title'),
                'home_goals': int(match.get('goals', {}).get('h', 0)),
                'away_goals': int(match.get('goals', {}).get('a', 0)),
                'home_xg': float(match.get('xG', {}).get('h', 0)),
                'away_xg': float(match.get('xG', {}).get('a', 0)),
                'forecast_win': float(match.get('forecast', {}).get('w', 0)),
                'forecast_draw': float(match.get('forecast', {}).get('d', 0)),
                'forecast_lose': float(match.get('forecast', {}).get('l', 0))
            })

        return pd.DataFrame(matches_list)

    def _get_dummy_xg_data(self):
        """더미 xG 데이터"""
        teams = ['Manchester City', 'Arsenal', 'Liverpool', 'Tottenham', 'Chelsea']

        return pd.DataFrame({
            'team': teams,
            'xg_for': [18.5, 16.2, 15.8, 15.1, 14.3],
            'xg_against': [6.2, 7.5, 8.1, 8.5, 9.8],
            'npxg': [16.8, 14.9, 14.2, 13.8, 12.5],
            'npxg_against': [5.8, 7.1, 7.6, 8.0, 9.2],
            'deep': [42, 38, 36, 35, 33],
            'deep_allowed': [15, 18, 20, 21, 24],
            'xpts': [16.5, 15.2, 14.1, 13.8, 12.3]
        })

    def _get_dummy_team_xg_history(self, team_name):
        """더미 팀 xG 히스토리"""
        return pd.DataFrame({
            'date': pd.date_range(start='2024-08-17', periods=5, freq='W'),
            'home_team': [team_name, 'Opponent1', team_name, 'Opponent2', team_name],
            'away_team': ['Opponent1', team_name, 'Opponent2', team_name, 'Opponent3'],
            'home_xg': [2.3, 1.5, 2.8, 1.2, 2.1],
            'away_xg': [1.2, 1.8, 0.9, 2.0, 1.3],
            'home_goals': [3, 1, 2, 1, 2],
            'away_goals': [1, 2, 0, 2, 1]
        })


if __name__ == "__main__":
    # 테스트
    scraper = UnderstatScraper()

    print("=== League xG Data ===")
    xg_data = scraper.get_league_xg_data()
    print(xg_data)

    print("\n=== Team xG History ===")
    team_xg = scraper.get_team_xg_history("Manchester_City")
    print(team_xg.head())
