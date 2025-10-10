"""
데이터베이스 초기화 스크립트
선수 데이터를 데이터베이스에 로드
"""

import sys
import os

# 부모 디렉토리를 path에 추가
sys.path.append(os.path.dirname(__file__))

from database.player_schema import Base, Team, Player, init_player_db, get_player_session
from data.squad_data import SQUAD_DATA
from sqlalchemy import create_engine

def init_database():
    """데이터베이스 초기화 및 선수 데이터 로드"""

    # 데이터베이스 경로
    db_path = os.path.join(os.path.dirname(__file__), 'data', 'epl_data.db')

    print(f"📁 Database path: {db_path}")

    # 기존 데이터베이스 삭제 (깨끗한 시작)
    if os.path.exists(db_path):
        os.remove(db_path)
        print("🗑️  Removed old database")

    # 데이터베이스 초기화
    engine = create_engine(f'sqlite:///{db_path}', echo=False)
    Base.metadata.create_all(engine)
    print("✅ Database schema created")

    # 세션 생성
    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(bind=engine)
    session = Session()

    # 팀 및 선수 데이터 로드
    print("\n📊 Loading team and player data...")

    teams_created = 0
    players_created = 0

    for team_name, players in SQUAD_DATA.items():
        # 팀 생성
        team = Team(name=team_name)
        session.add(team)
        session.flush()  # team.id를 얻기 위해
        teams_created += 1

        print(f"\n  ⚽ {team_name}")

        # 선수 생성
        for player_data in players:
            player = Player(
                team_id=team.id,
                id=player_data['id'],
                name=player_data['name'],
                position=player_data['position'],
                detailed_position=player_data.get('detailed_position', player_data['position']),
                number=player_data.get('number'),
                age=player_data.get('age', 0),
                nationality=player_data.get('nationality', ''),
                appearances=player_data.get('appearances', 0),
                goals=player_data.get('goals', 0),
                assists=player_data.get('assists', 0)
            )
            session.add(player)
            players_created += 1

        print(f"    ✅ {len(players)} players added")

    # 커밋
    session.commit()
    session.close()

    print(f"\n🎉 Database initialized successfully!")
    print(f"   📊 Teams: {teams_created}")
    print(f"   👥 Players: {players_created}")
    print(f"   💾 Database: {db_path}")


if __name__ == '__main__':
    init_database()
