"""
순위표 업데이트 스크립트
FBref에서 최신 순위표를 가져와 DB 업데이트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.schema import init_db, get_session, Standings, Team
from data_collection.fbref_scraper import FBrefScraper
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class StandingsUpdater:
    def __init__(self, season="2024-2025"):
        db_path = os.path.join(os.path.dirname(__file__), '..', 'soccer_predictor.db')
        db_url = f'sqlite:///{os.path.abspath(db_path)}'
        engine = init_db(db_url)
        self.session = get_session(engine)
        self.scraper = FBrefScraper()
        self.season = season

    def update_standings(self):
        """
        FBref에서 최신 순위표를 가져와 DB 업데이트
        """
        logger.info(f"Fetching latest standings for season {self.season}...")

        try:
            # FBref에서 순위표 가져오기
            standings_df = self.scraper.get_league_standings(season=self.season)

            if standings_df.empty:
                logger.warning("No standings data found")
                return 0

            logger.info(f"Found standings for {len(standings_df)} teams")

            updated_count = 0

            for _, row in standings_df.iterrows():
                team_name = row['team']
                rank = int(row['rank'])
                matches_played = int(row['matches_played'])
                wins = int(row['wins'])
                draws = int(row['draws'])
                losses = int(row['losses'])
                goals_for = int(row['goals_for'])
                goals_against = int(row['goals_against'])
                goal_difference = int(row['goal_difference'])
                points = int(row['points'])

                # DB에서 팀 찾기
                team = self.session.query(Team).filter_by(name=team_name).first()

                if not team:
                    logger.warning(f"Team not found in DB: {team_name}, creating...")
                    team = Team(name=team_name, league='EPL')
                    self.session.add(team)
                    self.session.commit()

                # 기존 순위표 레코드 찾기
                standing = self.session.query(Standings).filter(
                    Standings.team_id == team.id,
                    Standings.season == self.season
                ).first()

                if standing:
                    # 업데이트
                    standing.rank = rank
                    standing.matches_played = matches_played
                    standing.wins = wins
                    standing.draws = draws
                    standing.losses = losses
                    standing.goals_for = goals_for
                    standing.goals_against = goals_against
                    standing.goal_difference = goal_difference
                    standing.points = points
                    standing.updated_at = datetime.utcnow()
                    logger.info(f"✓ Updated: {rank}. {team_name} - {points}pts")
                else:
                    # 새 레코드 생성
                    standing = Standings(
                        team_id=team.id,
                        season=self.season,
                        rank=rank,
                        matches_played=matches_played,
                        wins=wins,
                        draws=draws,
                        losses=losses,
                        goals_for=goals_for,
                        goals_against=goals_against,
                        goal_difference=goal_difference,
                        points=points
                    )
                    self.session.add(standing)
                    logger.info(f"✓ Created: {rank}. {team_name} - {points}pts")

                updated_count += 1

            self.session.commit()
            logger.info(f"\n✅ Updated standings for {updated_count} teams")
            return updated_count

        except Exception as e:
            logger.error(f"Error updating standings: {e}")
            self.session.rollback()
            return 0

    def display_standings(self):
        """
        현재 순위표 출력
        """
        logger.info(f"\n📊 Current Standings ({self.season}):")
        logger.info("=" * 80)

        standings = self.session.query(Standings, Team).join(Team).filter(
            Standings.season == self.season
        ).order_by(Standings.rank).all()

        if not standings:
            logger.info("No standings data available")
            return

        logger.info(f"{'Rank':<5} {'Team':<30} {'MP':<5} {'W':<4} {'D':<4} {'L':<4} {'GF':<4} {'GA':<4} {'GD':<5} {'Pts':<4}")
        logger.info("-" * 80)

        for standing, team in standings:
            logger.info(
                f"{standing.rank:<5} {team.name:<30} {standing.matches_played:<5} "
                f"{standing.wins:<4} {standing.draws:<4} {standing.losses:<4} "
                f"{standing.goals_for:<4} {standing.goals_against:<4} "
                f"{standing.goal_difference:<5} {standing.points:<4}"
            )

    def close(self):
        self.session.close()


if __name__ == "__main__":
    updater = StandingsUpdater()

    try:
        logger.info("=" * 60)
        logger.info("Standings Update Script")
        logger.info("=" * 60)

        # 순위표 업데이트
        updated = updater.update_standings()

        # 업데이트된 순위표 출력
        if updated > 0:
            updater.display_standings()

        logger.info("\n" + "=" * 60)
        logger.info("✅ Update complete!")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Error: {e}")
        raise
    finally:
        updater.close()
