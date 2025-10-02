"""
FBref.com 데이터 스크래퍼
EPL 경기 일정, 결과, 팀 통계 수집
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FBrefScraper:
    def __init__(self):
        self.base_url = "https://fbref.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        # Rate limiting
        self.request_delay = 3  # seconds

    def get_epl_fixtures(self, season="2024-2025", use_cache=True):
        """
        EPL 경기 일정 가져오기

        Args:
            season: 시즌 (예: "2024-2025")
            use_cache: 캐시 사용 여부

        Returns:
            DataFrame: 경기 일정 데이터
        """
        logger.info(f"Fetching EPL fixtures for season {season}")

        # FBref EPL URL
        url = f"{self.base_url}/en/comps/9/schedule/Premier-League-Scores-and-Fixtures"

        try:
            time.sleep(self.request_delay)
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'lxml')

            # 경기 일정 테이블 찾기 (여러 ID 시도)
            fixtures_table = None
            possible_ids = [f'sched_{season}_9_1', 'sched_all']

            for table_id in possible_ids:
                fixtures_table = soup.find('table', {'id': table_id})
                if fixtures_table:
                    break

            # class로도 시도
            if not fixtures_table:
                fixtures_table = soup.find('table', class_='stats_table')

            if not fixtures_table:
                logger.warning("Fixtures table not found, using dummy data")
                return self._get_dummy_fixtures()

            # 테이블을 DataFrame으로 변환
            df = pd.read_html(str(fixtures_table))[0]

            # 컬럼 정리
            df = self._clean_fixtures_dataframe(df)

            # 빈 행 제거
            df = df.dropna(subset=['home_team', 'away_team'], how='all')

            # 향후 경기만 필터링 (Score가 비어있는 경기)
            if 'score' in df.columns:
                # Score가 NaN이거나 빈 문자열인 경기만
                df = df[df['score'].isna() | (df['score'] == '')]
                logger.info(f"Filtered to {len(df)} upcoming fixtures")

            # 날짜로 정렬
            if 'date' in df.columns:
                try:
                    df = df.sort_values('date')
                except:
                    pass

            # 최대 20경기로 제한
            df = df.head(20)

            logger.info(f"Returning {len(df)} fixtures")
            return df

        except requests.RequestException as e:
            logger.error(f"Network error fetching fixtures: {e}")
            return self._get_dummy_fixtures()
        except Exception as e:
            logger.error(f"Error fetching fixtures: {e}")
            return self._get_dummy_fixtures()

    def get_team_stats(self, season="2024-2025"):
        """
        팀 통계 가져오기

        Returns:
            DataFrame: 팀 통계 데이터
        """
        logger.info(f"Fetching team stats for season {season}")

        url = f"{self.base_url}/en/comps/9/Premier-League-Stats"

        try:
            time.sleep(self.request_delay)
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'lxml')

            # 팀 통계 테이블
            stats_table = soup.find('table', {'id': 'stats_squads_standard_for'})

            if not stats_table:
                logger.warning("Stats table not found")
                return self._get_dummy_team_stats()

            df = pd.read_html(str(stats_table))[0]
            df = self._clean_team_stats_dataframe(df)

            logger.info(f"Found stats for {len(df)} teams")
            return df

        except Exception as e:
            logger.error(f"Error fetching team stats: {e}")
            return self._get_dummy_team_stats()

    def _clean_fixtures_dataframe(self, df):
        """경기 일정 DataFrame 정리"""
        # 컬럼명 정리 (실제 FBref 구조에 맞춰 조정 필요)
        column_mapping = {
            'Wk': 'gameweek',
            'Date': 'date',
            'Home': 'home_team',
            'Away': 'away_team',
            'Score': 'score',
            'xG': 'home_xg',
            'xG.1': 'away_xg'
        }

        # 가능한 컬럼만 매핑
        for old_col, new_col in column_mapping.items():
            if old_col in df.columns:
                df.rename(columns={old_col: new_col}, inplace=True)

        return df

    def _clean_team_stats_dataframe(self, df):
        """팀 통계 DataFrame 정리"""
        # Multi-level 컬럼 처리
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = ['_'.join(col).strip() for col in df.columns.values]

        return df

    def _get_dummy_fixtures(self):
        """더미 경기 일정 데이터"""
        return pd.DataFrame({
            'gameweek': [8, 8, 8, 8, 8],
            'date': ['2024-10-05', '2024-10-05', '2024-10-05', '2024-10-06', '2024-10-06'],
            'home_team': ['Manchester City', 'Arsenal', 'Tottenham', 'Newcastle', 'Aston Villa'],
            'away_team': ['Liverpool', 'Chelsea', 'Manchester United', 'Brighton', 'Wolves'],
            'home_score': [None, None, None, None, None],
            'away_score': [None, None, None, None, None],
            'home_xg': [None, None, None, None, None],
            'away_xg': [None, None, None, None, None],
            'status': ['scheduled', 'scheduled', 'scheduled', 'scheduled', 'scheduled']
        })

    def _get_dummy_team_stats(self):
        """더미 팀 통계 데이터"""
        teams = ['Manchester City', 'Arsenal', 'Liverpool', 'Tottenham', 'Chelsea',
                 'Manchester United', 'Newcastle', 'Brighton', 'Aston Villa', 'Wolves']

        return pd.DataFrame({
            'team': teams,
            'matches_played': [7] * 10,
            'wins': [5, 5, 4, 4, 4, 3, 3, 3, 3, 2],
            'draws': [2, 1, 2, 2, 1, 2, 2, 2, 1, 3],
            'losses': [0, 1, 1, 1, 2, 2, 2, 2, 3, 2],
            'goals_for': [18, 16, 14, 15, 13, 10, 11, 10, 9, 8],
            'goals_against': [5, 7, 8, 8, 10, 9, 10, 9, 11, 10],
            'points': [17, 16, 14, 14, 13, 11, 11, 11, 10, 9]
        })

    def get_league_standings(self, season="2024-2025"):
        """
        프리미어리그 순위표 가져오기

        Args:
            season: 시즌 (예: "2024-2025")

        Returns:
            DataFrame: 순위표 데이터
        """
        logger.info(f"Fetching EPL standings for season {season}")

        # 현재 시즌 페이지 URL (리그 테이블 포함)
        url = f"{self.base_url}/en/comps/9/Premier-League-Stats"

        try:
            time.sleep(self.request_delay)
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'lxml')

            # Premier League 순위표 테이블 찾기
            # FBref는 'results' 접두사와 시즌 코드를 사용
            standings_table = None

            # 먼저 class로 찾기 (가장 확실한 방법)
            all_tables = soup.find_all('table', class_='stats_table')

            for table in all_tables:
                caption = table.find('caption')
                if caption and 'League Table' in caption.text:
                    standings_table = table
                    logger.info("Found standings table by caption: League Table")
                    break

            # ID로도 시도
            if not standings_table:
                season_id = season.replace('-', '')
                possible_table_ids = [
                    f'results{season_id}91_overall',
                    'results_overall',
                    'standings'
                ]

                for table_id in possible_table_ids:
                    standings_table = soup.find('table', {'id': table_id})
                    if standings_table:
                        logger.info(f"Found standings table with ID: {table_id}")
                        break

            if not standings_table:
                logger.warning("Standings table not found, using dummy data")
                return self._get_dummy_standings()

            # 테이블을 DataFrame으로 변환
            df = pd.read_html(str(standings_table))[0]

            # 컬럼 정리
            df = self._clean_standings_dataframe(df)

            logger.info(f"Found standings for {len(df)} teams")
            return df

        except requests.RequestException as e:
            logger.error(f"Network error fetching standings: {e}")
            return self._get_dummy_standings()
        except Exception as e:
            logger.error(f"Error fetching standings: {e}")
            return self._get_dummy_standings()

    def _clean_standings_dataframe(self, df):
        """순위표 DataFrame 정리"""
        # Multi-level 컬럼 처리
        if isinstance(df.columns, pd.MultiIndex):
            # 마지막 레벨만 사용 (가장 구체적인 컬럼명)
            df.columns = [col[-1] if isinstance(col, tuple) else col for col in df.columns]

        # 중복 컬럼 제거 (첫 번째 것만 유지)
        df = df.loc[:, ~df.columns.duplicated()]

        # 컬럼명 표준화 매핑
        column_mapping = {
            'Squad': 'team',
            'MP': 'matches_played',
            'W': 'wins',
            'D': 'draws',
            'L': 'losses',
            'GF': 'goals_for',
            'GA': 'goals_against',
            'GD': 'goal_difference',
            'Pts': 'points',
            'Rk': 'rank'
        }

        # 컬럼명 변경 (딕셔너리 한번에 적용)
        rename_dict = {}
        for old_col in df.columns:
            for pattern, new_col in column_mapping.items():
                if pattern in str(old_col):
                    rename_dict[old_col] = new_col
                    break

        df = df.rename(columns=rename_dict)

        # 필수 컬럼 확인 및 생성
        required_cols = ['team', 'matches_played', 'wins', 'draws', 'losses',
                        'goals_for', 'goals_against', 'points']

        for col in required_cols:
            if col not in df.columns:
                df[col] = 0

        # 득실차 계산 (없으면)
        if 'goal_difference' not in df.columns:
            df['goal_difference'] = df['goals_for'] - df['goals_against']

        # 순위 생성 (없으면)
        if 'rank' not in df.columns:
            df = df.sort_values('points', ascending=False).reset_index(drop=True)
            df['rank'] = range(1, len(df) + 1)

        return df

    def _get_dummy_standings(self):
        """더미 순위표 데이터"""
        teams = [
            'Manchester City', 'Arsenal', 'Liverpool', 'Aston Villa', 'Tottenham',
            'Chelsea', 'Newcastle United', 'Manchester United', 'West Ham', 'Brighton',
            'Brentford', 'Fulham', 'Wolverhampton Wanderers', 'Crystal Palace', 'Everton',
            'Nottingham Forest', 'Bournemouth', 'Leicester', 'Ipswich', 'Southampton'
        ]

        # 현실적인 순위표 데이터 생성
        standings_data = []
        for i, team in enumerate(teams):
            mp = 10
            # 상위팀일수록 높은 승점
            if i < 4:  # 상위 4개 팀
                w, d, l = 7 + (4-i), 2, 1
            elif i < 10:  # 중위권
                w, d, l = 5, 3, 2
            elif i < 17:  # 하위권
                w, d, l = 3, 3, 4
            else:  # 강등권
                w, d, l = 2, 2, 6

            gf = 20 - i
            ga = 8 + i
            pts = w * 3 + d

            standings_data.append({
                'rank': i + 1,
                'team': team,
                'matches_played': mp,
                'wins': w,
                'draws': d,
                'losses': l,
                'goals_for': gf,
                'goals_against': ga,
                'goal_difference': gf - ga,
                'points': pts
            })

        return pd.DataFrame(standings_data)

    def get_team_squad(self, team_name, season="2024-2025"):
        """
        특정 팀의 선수명단 가져오기

        Args:
            team_name: 팀 이름
            season: 시즌

        Returns:
            DataFrame: 선수명단 데이터
        """
        logger.info(f"Fetching squad for {team_name} ({season})")

        # FBref 팀 URL 매핑 (간소화된 버전)
        team_url_map = {
            'Manchester City': 'b8fd03ef/Manchester-City',
            'Arsenal': '18bb7c10/Arsenal',
            'Liverpool': '822bd0ba/Liverpool',
            'Chelsea': 'cff3d9bb/Chelsea',
            'Manchester United': '19538871/Manchester-United',
            'Tottenham': '361ca564/Tottenham-Hotspur',
            'Newcastle United': 'b2b47a98/Newcastle-United',
            'Aston Villa': '8602292d/Aston-Villa',
            'Brighton': 'd07537b9/Brighton-and-Hove-Albion',
            'West Ham': '7c21e445/West-Ham-United'
        }

        team_url = team_url_map.get(team_name)
        if not team_url:
            logger.warning(f"No URL mapping for {team_name}, using dummy data")
            return self._get_dummy_squad(team_name)

        url = f"{self.base_url}/en/squads/{team_url}-Stats"

        try:
            time.sleep(self.request_delay)
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'lxml')

            # 선수 통계 테이블 찾기
            squad_table = soup.find('table', {'id': 'stats_standard_9'})

            if not squad_table:
                logger.warning(f"Squad table not found for {team_name}, using dummy data")
                return self._get_dummy_squad(team_name)

            df = pd.read_html(str(squad_table))[0]
            df = self._clean_squad_dataframe(df, team_name)

            logger.info(f"Found {len(df)} players for {team_name}")
            return df

        except requests.RequestException as e:
            logger.error(f"Network error fetching squad: {e}")
            return self._get_dummy_squad(team_name)
        except Exception as e:
            logger.error(f"Error fetching squad: {e}")
            return self._get_dummy_squad(team_name)

    def _clean_squad_dataframe(self, df, team_name):
        """선수명단 DataFrame 정리"""
        # Multi-level 컬럼 처리
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = ['_'.join(str(col).strip() for col in cols if col) for cols in df.columns.values]

        # 필요한 컬럼 추출 및 이름 변경
        column_mapping = {
            'Player': 'name',
            'Nation': 'nationality',
            'Pos': 'position',
            'Age': 'age',
            '#': 'number'
        }

        # 컬럼 매핑
        for old_col in df.columns:
            for pattern, new_col in column_mapping.items():
                if pattern in old_col:
                    df.rename(columns={old_col: new_col}, inplace=True)
                    break

        # 필수 컬럼만 남기기
        required_cols = ['name', 'position', 'age', 'nationality']
        available_cols = [col for col in required_cols if col in df.columns]

        if not available_cols:
            return pd.DataFrame()

        df = df[available_cols].copy()

        # 데이터 정제
        if 'nationality' in df.columns:
            # 국기 이모지 추출 (예: "eng ENG" -> "🏴󠁧󠁢󠁥󠁮󠁧󠁿")
            df['nationality'] = df['nationality'].str.split().str[0]

        if 'age' in df.columns:
            df['age'] = pd.to_numeric(df['age'], errors='coerce').fillna(0).astype(int)

        # 등번호 추가 (없으면 순서대로)
        if 'number' not in df.columns:
            df['number'] = range(1, len(df) + 1)

        df['team'] = team_name

        return df.dropna(subset=['name'])

    def _get_dummy_squad(self, team_name):
        """더미 선수명단 데이터"""
        # squad_data.py에서 가져오기
        try:
            from data.squad_data import get_squad
            squad = get_squad(team_name)
            if squad:
                return pd.DataFrame(squad)
        except:
            pass

        # 완전 더미 데이터
        return pd.DataFrame({
            'name': [f'Player {i}' for i in range(1, 16)],
            'position': ['GK', 'CB', 'CB', 'CB', 'FB', 'FB', 'DM', 'DM', 'AM', 'AM', 'W', 'W', 'W', 'ST', 'ST'],
            'age': [25] * 15,
            'number': range(1, 16),
            'nationality': ['🏴'] * 15,
            'team': [team_name] * 15
        })


if __name__ == "__main__":
    # 테스트
    scraper = FBrefScraper()

    print("=== EPL Fixtures ===")
    fixtures = scraper.get_epl_fixtures()
    print(fixtures.head())

    print("\n=== Team Stats ===")
    stats = scraper.get_team_stats()
    print(stats.head())

    print("\n=== League Standings ===")
    standings = scraper.get_league_standings()
    print(standings.head(10))

    print("\n=== Team Squad (Manchester City) ===")
    squad = scraper.get_team_squad('Manchester City')
    print(squad.head(10))
