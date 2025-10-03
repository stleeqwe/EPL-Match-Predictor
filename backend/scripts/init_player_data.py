"""
선수 데이터 초기화 스크립트
EPL 20개 팀의 선수 데이터를 수집하여 데이터베이스에 저장
"""

import sys
import os

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_collection.squad_scraper import SquadScraper
from database.player_schema import (
    init_player_db,
    get_player_session,
    Team,
    Player,
    init_position_attributes
)
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def init_database():
    """데이터베이스 초기화"""
    logger.info("🔧 Initializing database...")
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'player_analysis.db')
    engine = init_player_db(db_path)
    logger.info(f"✅ Database initialized at {db_path}")
    return db_path


def populate_teams(session, team_names):
    """팀 데이터 저장"""
    logger.info(f"📋 Populating {len(team_names)} teams...")

    team_mapping = {}
    for team_name in team_names:
        existing = session.query(Team).filter_by(name=team_name).first()
        if existing:
            team_mapping[team_name] = existing
        else:
            team = Team(name=team_name)
            session.add(team)
            team_mapping[team_name] = team

    session.commit()
    logger.info(f"✅ Teams populated")
    return team_mapping


def populate_players(session, all_squads, team_mapping):
    """선수 데이터 저장"""
    logger.info("👥 Populating players...")

    total_players = 0
    for team_name, players in all_squads.items():
        team = team_mapping.get(team_name)
        if not team:
            logger.warning(f"Team not found: {team_name}")
            continue

        for player_data in players:
            # 기존 선수 확인 (같은 팀, 같은 이름)
            existing = session.query(Player).filter_by(
                team_id=team.id,
                name=player_data['name']
            ).first()

            if existing:
                # 업데이트
                existing.position = player_data.get('position', 'MF')
                existing.detailed_position = player_data.get('detailed_position', '')
                existing.number = player_data.get('number', 0)
                existing.age = player_data.get('age', 0)
                existing.nationality = player_data.get('nationality', '')
                existing.appearances = player_data.get('appearances', 0)
                existing.goals = player_data.get('goals', 0)
                existing.assists = player_data.get('assists', 0)
            else:
                # 신규 생성
                player = Player(
                    team_id=team.id,
                    name=player_data['name'],
                    position=player_data.get('position', 'MF'),
                    detailed_position=player_data.get('detailed_position', ''),
                    number=player_data.get('number', 0),
                    age=player_data.get('age', 0),
                    nationality=player_data.get('nationality', ''),
                    appearances=player_data.get('appearances', 0),
                    goals=player_data.get('goals', 0),
                    assists=player_data.get('assists', 0)
                )
                session.add(player)
                total_players += 1

    session.commit()
    logger.info(f"✅ {total_players} players populated")


def main():
    """메인 실행 함수"""
    logger.info("="*80)
    logger.info("EPL Player Analysis Platform - Data Initialization")
    logger.info("="*80)

    # 1. 데이터베이스 초기화
    db_path = init_database()
    session = get_player_session(db_path)

    # 2. 포지션 속성 초기화
    logger.info("🎯 Initializing position attributes...")
    init_position_attributes(session)
    logger.info("✅ Position attributes initialized")

    # 3. 선수 데이터 스크래핑
    logger.info("\n📡 Starting data collection from FBref...")
    scraper = SquadScraper()

    # 전체 팀 스크래핑 (캐시 사용하지 않음 - 최신 데이터)
    all_squads = scraper.get_all_squads(use_cache=False)

    if not all_squads:
        logger.error("❌ Failed to collect squad data")
        return

    # 4. 팀 데이터 저장
    team_names = list(all_squads.keys())
    team_mapping = populate_teams(session, team_names)

    # 5. 선수 데이터 저장
    populate_players(session, all_squads, team_mapping)

    # 6. 통계 출력
    total_teams = session.query(Team).count()
    total_players = session.query(Player).count()

    logger.info("\n" + "="*80)
    logger.info("✅ Data initialization complete!")
    logger.info(f"   Teams: {total_teams}")
    logger.info(f"   Players: {total_players}")
    logger.info(f"   Database: {db_path}")
    logger.info("="*80)

    session.close()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n⚠️  Interrupted by user")
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}", exc_info=True)
