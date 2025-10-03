"""
FBref.com EPL 선수 명단 스크래퍼
각 팀의 선수 정보를 수집
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import logging
import os
import json
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SquadScraper:
    """EPL 팀 선수 명단 스크래퍼"""

    def __init__(self):
        self.base_url = "https://fbref.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        self.request_delay = 4  # FBref은 3초 이상 권장

        # EPL 팀 URL 매핑 (2024-25 시즌)
        self.team_urls = {
            'Arsenal': '/en/squads/18bb7c10/Arsenal-Stats',
            'Aston Villa': '/en/squads/8602292d/Aston-Villa-Stats',
            'Bournemouth': '/en/squads/4ba7cbea/Bournemouth-Stats',
            'Brentford': '/en/squads/cd051869/Brentford-Stats',
            'Brighton': '/en/squads/d07537b9/Brighton-and-Hove-Albion-Stats',
            'Chelsea': '/en/squads/cff3d9bb/Chelsea-Stats',
            'Crystal Palace': '/en/squads/47c64c55/Crystal-Palace-Stats',
            'Everton': '/en/squads/d3fd31cc/Everton-Stats',
            'Fulham': '/en/squads/fd962109/Fulham-Stats',
            'Ipswich': '/en/squads/e297cd13/Ipswich-Town-Stats',
            'Leicester': '/en/squads/a2d435b3/Leicester-City-Stats',
            'Liverpool': '/en/squads/822bd0ba/Liverpool-Stats',
            'Manchester City': '/en/squads/b8fd03ef/Manchester-City-Stats',
            'Manchester United': '/en/squads/19538871/Manchester-United-Stats',
            'Newcastle United': '/en/squads/b2b47a98/Newcastle-United-Stats',
            'Nottingham Forest': '/en/squads/e4a775cb/Nottingham-Forest-Stats',
            'Southampton': '/en/squads/33c895d4/Southampton-Stats',
            'Tottenham': '/en/squads/361ca564/Tottenham-Hotspur-Stats',
            'West Ham': '/en/squads/7c21e445/West-Ham-United-Stats',
            'Wolverhampton Wanderers': '/en/squads/8cec06e1/Wolverhampton-Wanderers-Stats'
        }

        # 캐시 디렉토리
        self.cache_dir = os.path.join(os.path.dirname(__file__), 'data_cache')
        os.makedirs(self.cache_dir, exist_ok=True)

    def get_team_squad(self, team_name, use_cache=True):
        """
        특정 팀의 선수 명단 가져오기

        Args:
            team_name: 팀 이름
            use_cache: 캐시 사용 여부

        Returns:
            list: 선수 정보 리스트
        """
        logger.info(f"Fetching squad for {team_name}")

        # 캐시 확인
        cache_file = os.path.join(self.cache_dir, f'{team_name.replace(" ", "_")}_squad.json')
        if use_cache and os.path.exists(cache_file):
            # 캐시가 24시간 이내인지 확인
            cache_age = time.time() - os.path.getmtime(cache_file)
            if cache_age < 86400:  # 24시간
                logger.info(f"Using cached data for {team_name}")
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)

        # 팀 URL 가져오기
        team_url = self.team_urls.get(team_name)
        if not team_url:
            logger.warning(f"No URL found for team: {team_name}")
            return []

        url = self.base_url + team_url

        try:
            time.sleep(self.request_delay)
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'lxml')

            # 선수 테이블 찾기 - 'Standard Stats' 테이블
            stats_table = soup.find('table', {'id': 'stats_standard_9'})

            if not stats_table:
                logger.warning(f"Squad table not found for {team_name}")
                return []

            players = []
            tbody = stats_table.find('tbody')

            if not tbody:
                return []

            player_id = 1
            for row in tbody.find_all('tr'):
                # 헤더 행 스킵
                if row.get('class') and 'thead' in row.get('class'):
                    continue

                player_data = self._parse_player_row(row, team_name, player_id)
                if player_data:
                    players.append(player_data)
                    player_id += 1

            logger.info(f"Found {len(players)} players for {team_name}")

            # 캐시에 저장
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(players, f, ensure_ascii=False, indent=2)

            return players

        except requests.RequestException as e:
            logger.error(f"Network error fetching squad for {team_name}: {e}")
            return []
        except Exception as e:
            logger.error(f"Error fetching squad for {team_name}: {e}")
            return []

    def _parse_player_row(self, row, team_name, player_id):
        """선수 정보 행 파싱"""
        try:
            cells = row.find_all(['th', 'td'])

            if len(cells) < 5:
                return None

            # 선수 이름 (첫 번째 th 또는 td)
            name_cell = cells[0]
            name_link = name_cell.find('a')
            if not name_link:
                return None

            player_name = name_link.text.strip()

            # 국적 (두 번째 셀)
            nationality = ''
            if len(cells) > 1:
                nat_cell = cells[1]
                nat_span = nat_cell.find('span', class_='f-i')
                if nat_span:
                    nationality = nat_span.get('class', [''])[1].replace('f-', '') if len(nat_span.get('class', [])) > 1 else ''

            # 포지션 (세 번째 셀)
            position = cells[2].text.strip() if len(cells) > 2 else 'Unknown'

            # 나이 (네 번째 셀)
            age = 0
            if len(cells) > 3:
                age_text = cells[3].text.strip()
                if age_text and age_text.isdigit():
                    age = int(age_text)

            # 출전 경기 수 (다섯 번째 셀)
            appearances = 0
            if len(cells) > 4:
                apps_text = cells[4].text.strip()
                if apps_text and apps_text.isdigit():
                    appearances = int(apps_text)

            # 등번호 (선택적 - 없을 수 있음)
            number = 0

            return {
                'id': player_id,
                'name': player_name,
                'team': team_name,
                'position': self._normalize_position(position),
                'detailed_position': position,
                'number': number,
                'age': age,
                'nationality': nationality,
                'appearances': appearances,
                'goals': 0,  # 추가 데이터 필요 시 파싱
                'assists': 0
            }

        except Exception as e:
            logger.error(f"Error parsing player row: {e}")
            return None

    def _normalize_position(self, position):
        """
        포지션을 표준 카테고리로 정규화
        GK, DF, MF, FW
        """
        position_upper = position.upper()

        if 'GK' in position_upper or 'GOALKEEPER' in position_upper:
            return 'GK'
        elif any(pos in position_upper for pos in ['DF', 'CB', 'LB', 'RB', 'FB', 'WB']):
            return 'DF'
        elif any(pos in position_upper for pos in ['MF', 'CM', 'DM', 'AM', 'CDM', 'CAM']):
            return 'MF'
        elif any(pos in position_upper for pos in ['FW', 'ST', 'CF', 'LW', 'RW', 'W']):
            return 'FW'
        else:
            # 기본값은 MF
            return 'MF'

    def get_all_squads(self, use_cache=True):
        """
        EPL 전체 20개 팀의 선수 명단 가져오기

        Args:
            use_cache: 캐시 사용 여부

        Returns:
            dict: {team_name: [players]}
        """
        logger.info("Fetching all EPL team squads...")

        all_squads = {}
        total_teams = len(self.team_urls)

        for idx, team_name in enumerate(self.team_urls.keys(), 1):
            logger.info(f"[{idx}/{total_teams}] Fetching {team_name}...")
            players = self.get_team_squad(team_name, use_cache=use_cache)
            all_squads[team_name] = players

            # API 부담을 줄이기 위한 딜레이 (캐시 사용 시 제외)
            if not use_cache and idx < total_teams:
                time.sleep(self.request_delay)

        total_players = sum(len(players) for players in all_squads.values())
        logger.info(f"✅ Collected {total_players} players from {total_teams} teams")

        return all_squads

    def export_to_python_file(self, all_squads, output_file='../data/squad_data.py'):
        """
        수집한 선수 데이터를 Python 파일로 저장

        Args:
            all_squads: get_all_squads()의 결과
            output_file: 저장할 파일 경로
        """
        logger.info(f"Exporting squad data to {output_file}")

        output_path = os.path.join(os.path.dirname(__file__), output_file)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('"""\n')
            f.write('EPL 전체 팀 선수 명단\n')
            f.write(f'자동 생성됨: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
            f.write('"""\n\n')
            f.write('SQUAD_DATA = {\n')

            for team_name, players in sorted(all_squads.items()):
                f.write(f"    '{team_name}': [\n")
                for player in players:
                    f.write('        {\n')
                    for key, value in player.items():
                        if isinstance(value, str):
                            f.write(f"            '{key}': '{value}',\n")
                        else:
                            f.write(f"            '{key}': {value},\n")
                    f.write('        },\n')
                f.write('    ],\n')

            f.write('}\n')

        logger.info(f"✅ Squad data exported to {output_path}")


if __name__ == '__main__':
    # 테스트 실행
    scraper = SquadScraper()

    # 단일 팀 테스트
    print("Testing single team (Arsenal)...")
    arsenal_squad = scraper.get_team_squad('Arsenal', use_cache=False)
    print(f"Arsenal: {len(arsenal_squad)} players")
    if arsenal_squad:
        print("Sample player:", arsenal_squad[0])

    # 전체 팀 수집 (주석 처리 - 필요 시 실행)
    # print("\nCollecting all teams...")
    # all_squads = scraper.get_all_squads(use_cache=False)
    # scraper.export_to_python_file(all_squads)
