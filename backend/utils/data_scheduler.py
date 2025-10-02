"""
데이터 자동 업데이트 스케줄러
"""

import schedule
import time
import logging
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from data_collection import FBrefScraper, UnderstatScraper
from database.schema import init_db, get_session, Match, Team, TeamStats
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataScheduler:
    def __init__(self, db_path='sqlite:///soccer_predictor.db'):
        self.engine = init_db(db_path)
        self.fbref = FBrefScraper()
        self.understat = UnderstatScraper()

    def update_fixtures(self):
        """경기 일정 업데이트"""
        logger.info("=== Updating fixtures ===")
        try:
            fixtures = self.fbref.get_epl_fixtures()
            session = get_session(self.engine)

            for _, fixture in fixtures.iterrows():
                # 팀 찾기 또는 생성
                home_team = session.query(Team).filter_by(name=fixture['home_team']).first()
                if not home_team:
                    home_team = Team(name=fixture['home_team'], league='EPL')
                    session.add(home_team)
                    session.commit()

                away_team = session.query(Team).filter_by(name=fixture['away_team']).first()
                if not away_team:
                    away_team = Team(name=fixture['away_team'], league='EPL')
                    session.add(away_team)
                    session.commit()

                # 경기 찾기 또는 생성
                match = session.query(Match).filter_by(
                    home_team_id=home_team.id,
                    away_team_id=away_team.id,
                    gameweek=fixture.get('gameweek'),
                    season='2024-25'
                ).first()

                if not match:
                    match = Match(
                        season='2024-25',
                        gameweek=fixture.get('gameweek'),
                        match_date=pd.to_datetime(fixture.get('date')),
                        home_team_id=home_team.id,
                        away_team_id=away_team.id,
                        status=fixture.get('status', 'scheduled')
                    )
                    session.add(match)
                else:
                    # 기존 경기 업데이트
                    if pd.notna(fixture.get('home_score')):
                        match.home_score = int(fixture['home_score'])
                        match.away_score = int(fixture['away_score'])
                        match.status = 'completed'

            session.commit()
            session.close()
            logger.info(f"Updated {len(fixtures)} fixtures")

        except Exception as e:
            logger.error(f"Error updating fixtures: {e}")

    def update_xg_data(self):
        """xG 데이터 업데이트"""
        logger.info("=== Updating xG data ===")
        try:
            xg_data = self.understat.get_league_xg_data()
            session = get_session(self.engine)

            for _, team_xg in xg_data.iterrows():
                team = session.query(Team).filter_by(name=team_xg['team']).first()
                if team:
                    # TeamStats 업데이트
                    stats = session.query(TeamStats).filter_by(
                        team_id=team.id,
                        season='2024-25'
                    ).first()

                    if stats:
                        stats.xg_for = team_xg['xg_for']
                        stats.xg_against = team_xg['xg_against']

            session.commit()
            session.close()
            logger.info(f"Updated xG data for {len(xg_data)} teams")

        except Exception as e:
            logger.error(f"Error updating xG data: {e}")

    def update_team_stats(self):
        """팀 통계 업데이트"""
        logger.info("=== Updating team stats ===")
        try:
            stats = self.fbref.get_team_stats()
            session = get_session(self.engine)

            for _, team_stat in stats.iterrows():
                team = session.query(Team).filter_by(name=team_stat['team']).first()
                if team:
                    db_stats = session.query(TeamStats).filter_by(
                        team_id=team.id,
                        season='2024-25'
                    ).first()

                    if not db_stats:
                        db_stats = TeamStats(team_id=team.id, season='2024-25')
                        session.add(db_stats)

                    db_stats.matches_played = team_stat.get('matches_played', 0)
                    db_stats.wins = team_stat.get('wins', 0)
                    db_stats.draws = team_stat.get('draws', 0)
                    db_stats.losses = team_stat.get('losses', 0)
                    db_stats.goals_for = team_stat.get('goals_for', 0)
                    db_stats.goals_against = team_stat.get('goals_against', 0)
                    db_stats.points = team_stat.get('points', 0)

            session.commit()
            session.close()
            logger.info(f"Updated stats for {len(stats)} teams")

        except Exception as e:
            logger.error(f"Error updating team stats: {e}")

    def run_all_updates(self):
        """모든 업데이트 실행"""
        logger.info(f"\n{'='*50}")
        logger.info(f"Running scheduled updates at {datetime.now()}")
        logger.info(f"{'='*50}\n")

        self.update_fixtures()
        self.update_team_stats()
        self.update_xg_data()

        logger.info(f"\n{'='*50}")
        logger.info(f"All updates completed at {datetime.now()}")
        logger.info(f"{'='*50}\n")

    def start_scheduler(self):
        """스케줄러 시작"""
        logger.info("Starting data scheduler...")

        # 즉시 1회 실행
        self.run_all_updates()

        # 스케줄 설정
        schedule.every().day.at("06:00").do(self.run_all_updates)  # 매일 오전 6시
        schedule.every().day.at("18:00").do(self.run_all_updates)  # 매일 오후 6시
        schedule.every().hour.do(self.update_fixtures)  # 매시간 경기 일정 체크

        logger.info("Scheduler started. Press Ctrl+C to stop.")
        logger.info("Schedule:")
        logger.info("  - Full update: 06:00, 18:00")
        logger.info("  - Fixtures check: Every hour")

        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # 1분마다 체크
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")

if __name__ == "__main__":
    scheduler = DataScheduler()
    scheduler.start_scheduler()
