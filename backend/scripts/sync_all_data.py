"""
Premier League 공식 API에서 모든 데이터를 가져와 백엔드 전체 업데이트
- SQLite 데이터베이스 (teams, players)
- squad_data.py
- 팀 이름 일관성 유지
"""
import requests
import json
import sqlite3
from datetime import datetime
import os
import sys

# 2025-26 시즌 ID
SEASON_ID = 777

# 팀 이름 매핑 (Premier League 공식 → 우리 시스템)
TEAM_NAME_MAPPING = {
    'Arsenal': 'Arsenal',
    'Aston Villa': 'Aston Villa',
    'Bournemouth': 'Bournemouth',
    'Brentford': 'Brentford',
    'Brighton & Hove Albion': 'Brighton',
    'Burnley': 'Burnley',
    'Chelsea': 'Chelsea',
    'Crystal Palace': 'Crystal Palace',
    'Everton': 'Everton',
    'Fulham': 'Fulham',
    'Leeds United': 'Leeds',
    'Liverpool': 'Liverpool',
    'Manchester City': 'Man City',
    'Manchester United': 'Man Utd',
    'Newcastle United': 'Newcastle',
    'Nottingham Forest': "Nott'm Forest",
    'Sunderland': 'Sunderland',
    'Tottenham Hotspur': 'Spurs',
    'West Ham United': 'West Ham',
    'Wolverhampton Wanderers': 'Wolves'
}

def get_position(position_info):
    """포지션 정보를 간단한 형태로 변환"""
    if not position_info:
        return 'MF'
    if 'Goalkeeper' in position_info:
        return 'GK'
    elif 'Defender' in position_info or 'Back' in position_info:
        return 'DF'
    elif 'Forward' in position_info or 'Striker' in position_info or 'Winger' in position_info:
        return 'FW'
    else:
        return 'MF'

def fetch_fpl_photos():
    """FPL API에서 선수 사진 코드만 가져오기 (통계는 Premier League API 사용)"""
    try:
        print("\n🖼️  FPL API에서 선수 사진 코드 가져오는 중...")
        fpl_url = 'https://fantasy.premierleague.com/api/bootstrap-static/'
        response = requests.get(fpl_url, timeout=30)
        response.raise_for_status()
        fpl_data = response.json()

        # 선수 이름 -> photo code 매핑
        photo_map = {}
        for player in fpl_data['elements']:
            name = player.get('web_name', '')
            first_name = player.get('first_name', '')
            second_name = player.get('second_name', '')
            full_name = f"{first_name} {second_name}".strip()
            photo = str(player.get('code', ''))

            if photo:
                # 여러 이름 형식으로 저장
                photo_map[name] = photo
                photo_map[full_name] = photo
                photo_map[second_name] = photo

        print(f"   ✅ {len(fpl_data['elements'])}명 선수 사진 정보 로드")
        return photo_map
    except Exception as e:
        print(f"   ⚠️  FPL 사진 정보 로드 실패: {e}")
        return {}

def fetch_premier_league_data():
    """Premier League API에서 데이터 가져오기"""

    print("="*80)
    print("Premier League 공식 API 데이터 동기화 시작")
    print(f"시즌: 2025-26 (ID: {SEASON_ID})")
    print("="*80)

    headers = {
        'Origin': 'https://www.premierleague.com',
        'User-Agent': 'Mozilla/5.0'
    }

    try:
        # 0. FPL 사진 정보만 가져오기 (통계는 Premier League API 사용)
        fpl_photos = fetch_fpl_photos()

        # 1. 팀 목록 가져오기
        print("\n[1/3] 팀 데이터 가져오는 중...")
        teams_url = f'https://footballapi.pulselive.com/football/teams?pageSize=100&compSeasons={SEASON_ID}'
        teams_response = requests.get(teams_url, headers=headers, timeout=30)
        teams_response.raise_for_status()
        teams_data = teams_response.json()

        teams_info = {}
        for team in teams_data['content']:
            pl_name = team['name']
            our_name = TEAM_NAME_MAPPING.get(pl_name, pl_name)
            teams_info[int(team['id'])] = {
                'id': int(team['id']),
                'name': our_name,
                'full_name': pl_name,
                'short_name': team.get('shortName', our_name),
                'abbr': team['club']['abbr']
            }
            print(f"   ✓ {pl_name:35s} → {our_name}")

        print(f"\n✅ {len(teams_info)}개 팀 로드 완료")

        # 2. 선수 데이터 가져오기
        print("\n[2/3] 선수 데이터 가져오는 중...")
        all_players = {}
        seen_player_ids = set()  # 중복 체크용
        duplicate_count = 0

        for team_id, team_info in teams_info.items():
            print(f"\n📋 {team_info['name']} 선수단...")

            staff_url = f'https://footballapi.pulselive.com/football/teams/{team_id}/compseasons/{SEASON_ID}/staff'
            staff_response = requests.get(staff_url, headers=headers, timeout=30)
            staff_response.raise_for_status()
            staff_data = staff_response.json()

            team_players = []

            for player in staff_data.get('players', []):
                if player.get('info', {}).get('loan'):
                    continue

                info = player.get('info', {})
                name_data = player.get('name', {})
                player_id = int(player.get('id', 0))

                # 중복 ID 체크 및 스킵
                if player_id in seen_player_ids:
                    duplicate_count += 1
                    print(f"   ⚠️  중복 ID 스킵: {name_data.get('display', '')} (ID: {player_id})")
                    continue

                seen_player_ids.add(player_id)

                # 나이 계산
                age_str = player.get('age', '')
                age = 0
                if 'years' in age_str:
                    try:
                        age = int(age_str.split('years')[0].strip())
                    except:
                        age = 0

                position = get_position(info.get('positionInfo', ''))
                shirt_num = int(info.get('shirtNum', 0)) if info.get('shirtNum') else 0

                # Premier League API 통계 직접 사용
                player_name = name_data.get('display', '')
                first_name = name_data.get('first', '')
                last_name = name_data.get('last', '')

                # FPL에서 사진 코드만 가져오기
                photo_code = ''
                if player_name in fpl_photos:
                    photo_code = fpl_photos[player_name]
                elif last_name in fpl_photos:
                    photo_code = fpl_photos[last_name]
                elif f"{first_name} {last_name}" in fpl_photos:
                    photo_code = fpl_photos[f"{first_name} {last_name}"]

                # Premier League API의 통계 사용
                appearances = player.get('appearances', 0)
                goals = player.get('goals', 0) if player.get('goals') is not None else 0
                assists = player.get('assists', 0) if player.get('assists') is not None else 0
                clean_sheets = player.get('cleanSheets', 0)

                # 골키퍼는 goals/assists가 N/A일 수 있음
                if position == 'GK':
                    goals = 0
                    assists = 0

                player_data = {
                    'id': player_id,
                    'name': player_name,
                    'position': position,
                    'number': shirt_num,
                    'age': age,
                    'team_id': team_id,
                    'team_name': team_info['name'],
                    'nationality': '',
                    'photo': photo_code,
                    'is_starter': appearances > 5,  # 5경기 이상 출전 시 주전
                    'stats': {
                        'appearances': appearances,
                        'starts': appearances,
                        'minutes': 0,  # Premier League API에는 minutes 없음
                        'goals': goals,
                        'assists': assists,
                        'clean_sheets': clean_sheets
                    }
                }

                team_players.append(player_data)

            all_players[team_info['name']] = team_players
            print(f"   ✅ {len(team_players)}명")

        total_players = sum(len(p) for p in all_players.values())
        print(f"\n✅ 총 {total_players}명 선수 로드 완료")
        if duplicate_count > 0:
            print(f"⚠️  {duplicate_count}명 중복 ID 제외됨")

        return teams_info, all_players

    except Exception as e:
        print(f"\n❌ API 오류: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def update_database(teams_info, all_players):
    """SQLite 데이터베이스 업데이트"""

    print("\n[3/3] 데이터베이스 업데이트 중...")

    db_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'data',
        'epl_data.db'
    )

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # teams 테이블 업데이트
        print("\n📊 teams 테이블 업데이트...")
        cursor.execute("DELETE FROM teams")

        for team_info in teams_info.values():
            cursor.execute("""
                INSERT INTO teams (id, name, short_name, stadium, manager, founded, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            """, (
                team_info['id'],
                team_info['name'],
                team_info['short_name'],
                '',  # stadium
                '',  # manager
                0    # founded
            ))

        print(f"   ✅ {len(teams_info)}개 팀 삽입")

        # players 테이블 업데이트
        print("\n📊 players 테이블 업데이트...")

        # 기존 player_ratings 백업
        cursor.execute("SELECT player_id FROM player_ratings")
        rated_players = [row[0] for row in cursor.fetchall()]
        print(f"   ℹ️  평가된 선수: {len(rated_players)}명 (유지됨)")

        cursor.execute("DELETE FROM players")

        player_count = 0
        for team_name, players in all_players.items():
            for player in players:
                cursor.execute("""
                    INSERT INTO players (
                        id, team_id, name, position, detailed_position, number, age,
                        nationality, height, foot, market_value, contract_until,
                        appearances, goals, assists, photo_url,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
                """, (
                    player['id'],
                    player['team_id'],
                    player['name'],
                    player['position'],
                    '',  # detailed_position
                    player['number'],
                    player['age'],
                    player['nationality'],
                    '',  # height
                    '',  # foot
                    '',  # market_value
                    '',  # contract_until
                    player['stats']['appearances'],
                    player['stats']['goals'],
                    player['stats']['assists'],
                    player['photo'],  # photo_url
                ))
                player_count += 1

        print(f"   ✅ {player_count}명 선수 삽입")

        # player_ratings 정리 (존재하지 않는 선수 제거)
        cursor.execute("""
            DELETE FROM player_ratings
            WHERE player_id NOT IN (SELECT id FROM players)
        """)
        deleted = cursor.rowcount
        if deleted > 0:
            print(f"   ⚠️  {deleted}개 평가 제거됨 (선수 이적/제외)")

        conn.commit()
        print("\n✅ 데이터베이스 업데이트 완료")

    except Exception as e:
        conn.rollback()
        print(f"\n❌ 데이터베이스 오류: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        conn.close()

    return True

def update_squad_data_file(all_players):
    """squad_data.py 파일 업데이트"""

    print("\n📝 squad_data.py 업데이트 중...")

    output_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'data',
        'squad_data.py'
    )

    # 팀별 선수 정렬
    squad_data = {}
    for team_name, players in all_players.items():
        position_order = {'GK': 0, 'DF': 1, 'MF': 2, 'FW': 3}
        sorted_players = sorted(players, key=lambda p: (
            position_order.get(p['position'], 4),
            p['number'] if p['number'] else 999
        ))
        squad_data[team_name] = sorted_players

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('"""\n')
        f.write('EPL 전체 팀 선수 명단\n')
        f.write(f'자동 생성됨: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
        f.write('시즌: 2025-26\n')
        f.write('데이터 소스: Premier League Official API (Pulselive)\n')
        f.write('"""\n\n')
        json_str = json.dumps(squad_data, indent=4, ensure_ascii=False)
        json_str = json_str.replace(': true', ': True').replace(': false', ': False')
        f.write(f'SQUAD_DATA = {json_str}\n\n')
        f.write('def get_squad(team_name):\n')
        f.write('    """팀 이름으로 선수 명단 가져오기"""\n')
        f.write('    return SQUAD_DATA.get(team_name, [])\n\n')
        f.write('def get_all_teams():\n')
        f.write('    """모든 팀 이름 리스트"""\n')
        f.write('    return list(SQUAD_DATA.keys())\n')

    print(f"   ✅ 파일 저장: {output_path}")

if __name__ == '__main__':
    print("\n🚀 백엔드 데이터 전체 동기화\n")

    # 1. API에서 데이터 가져오기
    teams_info, all_players = fetch_premier_league_data()

    if not teams_info or not all_players:
        print("\n❌ 동기화 실패")
        sys.exit(1)

    # 2. 데이터베이스 업데이트
    if not update_database(teams_info, all_players):
        print("\n❌ 데이터베이스 업데이트 실패")
        sys.exit(1)

    # 3. squad_data.py 업데이트
    update_squad_data_file(all_players)

    # 4. 최종 통계
    print("\n" + "="*80)
    print("📊 최종 통계")
    print("="*80)
    print(f"팀: {len(teams_info)}개")
    print(f"선수: {sum(len(p) for p in all_players.values())}명")
    print("\n팀별 선수 수:")
    for team_name, players in sorted(all_players.items()):
        print(f"  {team_name:25s}: {len(players):2d}명")

    print("\n" + "="*80)
    print("✅ 모든 데이터 동기화 완료!")
    print("="*80)
    print("\n다음 단계:")
    print("  1. 백엔드 서버 재시작")
    print("  2. 프론트엔드 새로고침")
    print("  3. 팀/선수 데이터 확인")
