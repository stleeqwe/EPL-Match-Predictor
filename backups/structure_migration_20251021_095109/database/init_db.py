"""
데이터베이스 초기화 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.schema import init_db, get_session, Team
from data_collection.fbref_scraper import FBrefScraper
from data_collection.understat_scraper import UnderstatScraper
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def initialize_database():
    """데이터베이스 초기화 및 팀 데이터 삽입"""

    # 데이터베이스 생성
    db_path = os.path.join(os.path.dirname(__file__), '..', 'soccer_predictor.db')
    db_url = f'sqlite:///{os.path.abspath(db_path)}'

    logger.info(f"Initializing database at: {db_url}")
    engine = init_db(db_url)
    session = get_session(engine)

    try:
        # EPL 팀 데이터 삽입
        epl_teams = [
            ('Arsenal', 'ARS'),
            ('Aston Villa', 'AVL'),
            ('Bournemouth', 'BOU'),
            ('Brentford', 'BRE'),
            ('Brighton', 'BHA'),
            ('Chelsea', 'CHE'),
            ('Crystal Palace', 'CRY'),
            ('Everton', 'EVE'),
            ('Fulham', 'FUL'),
            ('Ipswich', 'IPS'),
            ('Leicester', 'LEI'),
            ('Liverpool', 'LIV'),
            ('Manchester City', 'MCI'),
            ('Manchester United', 'MUN'),
            ('Newcastle United', 'NEW'),
            ('Nottingham Forest', 'NFO'),
            ('Southampton', 'SOU'),
            ('Tottenham', 'TOT'),
            ('West Ham', 'WHU'),
            ('Wolverhampton Wanderers', 'WOL')
        ]

        # 기존 팀이 있는지 확인
        existing_teams = session.query(Team).count()

        if existing_teams == 0:
            logger.info("Inserting EPL teams...")
            for team_name, short_name in epl_teams:
                team = Team(
                    name=team_name,
                    short_name=short_name,
                    league='EPL'
                )
                session.add(team)

            session.commit()
            logger.info(f"Successfully inserted {len(epl_teams)} teams")
        else:
            logger.info(f"Teams already exist in database ({existing_teams} teams)")

        # 팀 목록 출력
        teams = session.query(Team).all()
        logger.info("\n=== Teams in Database ===")
        for team in teams:
            logger.info(f"  {team.id}: {team.name} ({team.short_name})")

        return True

    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        session.rollback()
        return False
    finally:
        session.close()

if __name__ == "__main__":
    success = initialize_database()
    if success:
        print("\n✅ Database initialization completed successfully!")
    else:
        print("\n❌ Database initialization failed!")
        sys.exit(1)
