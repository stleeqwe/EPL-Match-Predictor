#!/usr/bin/env python3
"""
선수 로스터 자동 업데이트 스크립트
- FBref에서 EPL 20개 팀의 선수명단 스크래핑
- Player DB 테이블 업데이트
- squad_data.py 파일 업데이트 (기존 코드 호환성)
"""

import sys
import os
from datetime import datetime

# 프로젝트 루트를 경로에 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from data_collection.fbref_scraper import FBrefScraper
from database.schema import Team, Player, get_session, init_db
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RosterUpdater:
    """선수 로스터 업데이트 관리"""

    def __init__(self, season="2024-2025"):
        # DB 연결
        db_path = os.path.join(os.path.dirname(__file__), '..', 'soccer_predictor.db')
        db_url = f'sqlite:///{os.path.abspath(db_path)}'
        engine = init_db(db_url)
        self.session = get_session(engine)

        # 스크래퍼 초기화
        self.scraper = FBrefScraper()
        self.season = season

        # 20개 EPL 팀
        self.epl_teams = [
            'Manchester City', 'Liverpool', 'Arsenal', 'Chelsea',
            'Tottenham', 'Manchester United', 'Newcastle United', 'Brighton',
            'Aston Villa', 'West Ham', 'Brentford', 'Fulham',
            'Crystal Palace', 'Everton', 'Wolverhampton Wanderers', 'Bournemouth',
            'Nottingham Forest', 'Leicester', 'Ipswich', 'Southampton'
        ]

    def update_all_rosters(self):
        """모든 EPL 팀의 로스터 업데이트"""
        logger.info(f"=== Starting roster update for {len(self.epl_teams)} teams ===")

        updated_teams = 0
        total_players = 0

        for team_name in self.epl_teams:
            try:
                count = self.update_team_roster(team_name)
                if count > 0:
                    updated_teams += 1
                    total_players += count
                    logger.info(f"✓ {team_name}: {count} players updated")
                else:
                    logger.warning(f"⚠ {team_name}: No players updated")
            except Exception as e:
                logger.error(f"✗ {team_name}: Failed - {e}")

        logger.info(f"\n=== Roster update complete ===")
        logger.info(f"Teams updated: {updated_teams}/{len(self.epl_teams)}")
        logger.info(f"Total players: {total_players}")

        return updated_teams, total_players

    def update_team_roster(self, team_name):
        """특정 팀의 로스터 업데이트"""
        # FBref에서 선수명단 가져오기
        squad_df = self.scraper.get_team_squad(team_name, season=self.season)

        if squad_df.empty:
            logger.warning(f"No squad data for {team_name}")
            return 0

        # 팀 찾기 또는 생성
        team = self.session.query(Team).filter_by(name=team_name).first()
        if not team:
            team = Team(name=team_name, league='EPL')
            self.session.add(team)
            self.session.commit()
            logger.info(f"Created new team: {team_name}")

        # 기존 선수 삭제 (전체 교체)
        self.session.query(Player).filter_by(team_id=team.id).delete()

        # 새 선수 추가
        player_count = 0
        for _, row in squad_df.iterrows():
            player = Player(
                team_id=team.id,
                name=row['name'],
                position=row.get('position', 'Unknown'),
                number=int(row['number']) if row.get('number') and str(row['number']).isdigit() else None,
                age=int(row['age']) if row.get('age') and str(row['age']).isdigit() else None,
                nationality=row.get('nationality', '')
            )
            self.session.add(player)
            player_count += 1

        self.session.commit()
        return player_count

    def update_squad_data_file(self):
        """squad_data.py 파일 업데이트 (기존 코드 호환성)"""
        logger.info("\n=== Updating squad_data.py file ===")

        squad_data_path = os.path.join(
            os.path.dirname(__file__), '..', 'data', 'squad_data.py'
        )

        # DB에서 모든 팀과 선수 정보 가져오기
        teams = self.session.query(Team).filter_by(league='EPL').all()

        # squad_data.py 파일 생성
        with open(squad_data_path, 'w', encoding='utf-8') as f:
            f.write('"""\n')
            f.write('EPL 전체 팀 선수 명단\n')
            f.write(f'자동 생성됨: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
            f.write('"""\n\n')
            f.write('SQUAD_DATA = {\n')

            for team in teams:
                players = self.session.query(Player).filter_by(team_id=team.id).all()
                if not players:
                    continue

                f.write(f"    '{team.name}': [\n")

                for player in players:
                    f.write('        {\n')
                    f.write(f"            'id': {player.id},\n")
                    f.write(f"            'name': '{player.name}',\n")
                    f.write(f"            'position': '{player.position}',\n")
                    f.write(f"            'number': {player.number if player.number else 0},\n")
                    f.write(f"            'age': {player.age if player.age else 0},\n")
                    f.write(f"            'nationality': '{player.nationality if player.nationality else ''}'\n")
                    f.write('        },\n')

                f.write('    ],\n\n')

            f.write('}\n\n')
            f.write('def get_squad(team_name):\n')
            f.write('    """팀 이름으로 선수 명단 가져오기"""\n')
            f.write('    return SQUAD_DATA.get(team_name, [])\n\n')
            f.write('def get_all_teams():\n')
            f.write('    """모든 팀 이름 리스트"""\n')
            f.write('    return list(SQUAD_DATA.keys())\n')

        logger.info(f"✓ squad_data.py updated: {len(teams)} teams")
        return squad_data_path

    def display_summary(self):
        """현재 DB의 선수 통계 출력"""
        logger.info("\n=== Current Squad Database Summary ===")

        teams = self.session.query(Team).filter_by(league='EPL').all()

        print(f"\n{'Team':<25} {'Players':>8}")
        print("-" * 35)

        total_players = 0
        for team in teams:
            player_count = self.session.query(Player).filter_by(team_id=team.id).count()
            total_players += player_count
            print(f"{team.name:<25} {player_count:>8}")

        print("-" * 35)
        print(f"{'TOTAL':<25} {total_players:>8}")
        print()

    def close(self):
        """DB 세션 종료"""
        self.session.close()


def main():
    """메인 실행 함수"""
    logger.info("Starting EPL Squad Roster Update")
    logger.info("=" * 50)

    updater = RosterUpdater(season="2024-2025")

    try:
        # 1. 모든 팀의 로스터 업데이트
        updated_teams, total_players = updater.update_all_rosters()

        # 2. squad_data.py 파일 업데이트
        if updated_teams > 0:
            squad_file = updater.update_squad_data_file()
            logger.info(f"✓ Squad data file saved: {squad_file}")

        # 3. 요약 출력
        updater.display_summary()

        logger.info("✓ Roster update completed successfully!")

    except Exception as e:
        logger.error(f"✗ Roster update failed: {e}", exc_info=True)
    finally:
        updater.close()


if __name__ == '__main__':
    main()
