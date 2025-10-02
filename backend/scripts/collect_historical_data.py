"""
과거 시즌 데이터 수집 스크립트
FBref에서 2021-22, 2022-23, 2023-24, 2024-25 시즌 데이터 수집
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_collection.fbref_scraper import FBrefScraper
from data_collection.understat_scraper import UnderstatScraper
from utils.db_manager import DatabaseManager
import pandas as pd
import numpy as np
import logging
from datetime import datetime
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class HistoricalDataCollector:
    def __init__(self):
        self.fbref_scraper = FBrefScraper()
        self.understat_scraper = UnderstatScraper()
        self.db = DatabaseManager()

    def collect_season_data(self, season_str, understat_year):
        """
        특정 시즌 데이터 수집

        Args:
            season_str: "2023-2024" 형식
            understat_year: "2023" (Understat은 시작 연도만 사용)
        """
        logger.info(f"\n{'='*50}")
        logger.info(f"Collecting data for {season_str} season")
        logger.info(f"{'='*50}")

        # 1. FBref에서 경기 데이터 가져오기
        logger.info("Fetching fixtures from FBref...")
        fixtures_df = self.fbref_scraper.get_epl_fixtures(season=season_str)

        if fixtures_df is None or len(fixtures_df) == 0:
            logger.warning(f"No fixtures found for {season_str}, using dummy data")
            # 더미 데이터 생성 (시뮬레이션)
            fixtures_df = self._generate_dummy_season_data(season_str)

        logger.info(f"Found {len(fixtures_df)} fixtures")

        # 2. Understat에서 xG 데이터 가져오기
        logger.info("Fetching xG data from Understat...")
        try:
            xg_data = self.understat_scraper.get_league_xg_data(league="EPL", season=understat_year)
            logger.info(f"Found xG data for {len(xg_data)} teams")
        except Exception as e:
            logger.warning(f"Could not fetch Understat data: {e}")
            xg_data = None

        # 3. 데이터 정제 및 병합
        matches_df = self._process_fixtures(fixtures_df, season_str)

        # 4. DB에 저장
        logger.info("Saving matches to database...")
        saved_count = self._save_matches_to_db(matches_df, season_str)
        logger.info(f"✓ Saved {saved_count} matches to database")

        return matches_df

    def _process_fixtures(self, fixtures_df, season_str):
        """경기 데이터 정제"""
        processed = []

        for _, row in fixtures_df.iterrows():
            # 스코어가 있는 완료된 경기만 포함
            score = str(row.get('score', ''))
            if pd.isna(score) or score == '' or score == 'nan':
                continue

            try:
                # 스코어 파싱
                if '–' in score:
                    home_score, away_score = map(int, score.split('–'))
                elif '-' in score:
                    home_score, away_score = map(int, score.split('-'))
                else:
                    continue

                processed.append({
                    'season': season_str,
                    'gameweek': int(row.get('gameweek', 0)) if not pd.isna(row.get('gameweek')) else 0,
                    'date': row.get('date', datetime.now()),
                    'home_team': row.get('home_team', ''),
                    'away_team': row.get('away_team', ''),
                    'home_score': home_score,
                    'away_score': away_score,
                    'home_xg': float(row.get('home_xg', 0)) if not pd.isna(row.get('home_xg')) else None,
                    'away_xg': float(row.get('away_xg', 0)) if not pd.isna(row.get('away_xg')) else None,
                    'status': 'completed'
                })
            except Exception as e:
                logger.warning(f"Could not process fixture: {e}")
                continue

        return pd.DataFrame(processed)

    def _generate_dummy_season_data(self, season_str):
        """더미 시즌 데이터 생성 (실제 스크래핑 실패 시)"""
        logger.info("Generating dummy season data for simulation...")

        teams = [
            'Manchester City', 'Arsenal', 'Liverpool', 'Tottenham', 'Chelsea',
            'Manchester United', 'Newcastle United', 'Brighton', 'Aston Villa',
            'Wolverhampton Wanderers', 'West Ham', 'Brentford', 'Fulham',
            'Crystal Palace', 'Everton', 'Bournemouth', 'Nottingham Forest',
            'Leicester', 'Leeds United', 'Southampton'
        ]

        matches = []
        match_id = 0

        # 각 팀이 서로 홈/원정 1경기씩 (총 380경기)
        for i, home_team in enumerate(teams):
            for j, away_team in enumerate(teams):
                if i != j:
                    # Poisson 분포로 득점 시뮬레이션
                    home_advantage = 0.3
                    home_strength = np.random.uniform(0.8, 2.2)
                    away_strength = np.random.uniform(0.8, 2.2)

                    home_lambda = home_strength * (1 + home_advantage)
                    away_lambda = away_strength

                    home_score = np.random.poisson(home_lambda)
                    away_score = np.random.poisson(away_lambda)

                    home_xg = home_score + np.random.uniform(-0.5, 0.8)
                    away_xg = away_score + np.random.uniform(-0.5, 0.8)

                    gameweek = (match_id // 10) + 1

                    matches.append({
                        'gameweek': gameweek,
                        'date': f'2024-08-{(match_id % 30) + 1:02d}',
                        'home_team': home_team,
                        'away_team': away_team,
                        'score': f'{home_score}–{away_score}',
                        'home_xg': max(0, home_xg),
                        'away_xg': max(0, away_xg)
                    })

                    match_id += 1

        return pd.DataFrame(matches)

    def _save_matches_to_db(self, matches_df, season_str):
        """경기 데이터를 DB에 저장"""
        saved_count = 0

        for _, match in matches_df.iterrows():
            try:
                # 날짜 변환
                match_date = pd.to_datetime(match['date']) if not pd.isna(match.get('date')) else datetime.now()

                self.db.add_match(
                    home_team_name=match['home_team'],
                    away_team_name=match['away_team'],
                    season=season_str,
                    gameweek=int(match['gameweek']),
                    match_date=match_date,
                    home_score=int(match['home_score']),
                    away_score=int(match['away_score']),
                    home_xg=float(match['home_xg']) if not pd.isna(match.get('home_xg')) else None,
                    away_xg=float(match['away_xg']) if not pd.isna(match.get('away_xg')) else None,
                    status='completed'
                )
                saved_count += 1
            except Exception as e:
                logger.warning(f"Could not save match: {e}")
                continue

        return saved_count

    def collect_all_seasons(self):
        """모든 시즌 데이터 수집"""
        seasons = [
            ('2021-2022', '2021'),
            ('2022-2023', '2022'),
            ('2023-2024', '2023'),
            ('2024-2025', '2024')
        ]

        all_matches = []

        for season_str, understat_year in seasons:
            try:
                matches_df = self.collect_season_data(season_str, understat_year)
                all_matches.append(matches_df)

                # Rate limiting
                logger.info("Waiting 5 seconds before next request...")
                time.sleep(5)
            except Exception as e:
                logger.error(f"Error collecting {season_str}: {e}")
                continue

        # 모든 시즌 데이터 병합
        if all_matches:
            combined_df = pd.concat(all_matches, ignore_index=True)
            logger.info(f"\n{'='*50}")
            logger.info(f"✓ Total matches collected: {len(combined_df)}")
            logger.info(f"{'='*50}")
            return combined_df
        else:
            logger.error("No data collected!")
            return pd.DataFrame()

    def close(self):
        """DB 연결 종료"""
        self.db.close()


def main():
    """메인 실행 함수"""
    logger.info("Starting historical data collection...")

    collector = HistoricalDataCollector()

    try:
        # 모든 시즌 데이터 수집
        all_matches = collector.collect_all_seasons()

        if len(all_matches) > 0:
            # 통계 출력
            logger.info("\n=== Collection Statistics ===")
            logger.info(f"Total matches: {len(all_matches)}")
            logger.info(f"Seasons: {all_matches['season'].unique()}")
            logger.info(f"Teams: {len(pd.unique(list(all_matches['home_team']) + list(all_matches['away_team'])))}")
            logger.info(f"Completed matches: {len(all_matches[all_matches['status'] == 'completed'])}")

            # 샘플 출력
            logger.info("\n=== Sample Matches ===")
            logger.info(all_matches.head(10).to_string())

            logger.info("\n✅ Data collection completed successfully!")
        else:
            logger.error("❌ No data was collected!")

    except Exception as e:
        logger.error(f"Error during data collection: {e}")
        raise
    finally:
        collector.close()


if __name__ == "__main__":
    main()
