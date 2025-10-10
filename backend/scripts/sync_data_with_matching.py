"""
EPL 데이터 동기화 (정합성 체크 포함)
- Premier League API: 팀, 선수단 기본 정보 (공식 로스터)
- FPL API: 상세 정보 (사진, 통계)
- 두 API의 선수 데이터를 매칭하여 하나로 통합
"""
import requests
import json
import sqlite3
from datetime import datetime
from difflib import SequenceMatcher
import os
import sys

SEASON_ID = 777

# 팀 이름 매핑 (Premier League → 우리 시스템)
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

# FPL 팀 ID 매핑 (우리 시스템 이름 → FPL 팀 ID)
FPL_TEAM_ID_MAPPING = {
    'Arsenal': 1,
    'Aston Villa': 2,
    'Burnley': 3,
    'Bournemouth': 4,
    'Brentford': 5,
    'Brighton': 6,
    'Chelsea': 7,
    'Crystal Palace': 8,
    'Everton': 9,
    'Fulham': 10,
    'Leeds': 11,
    'Liverpool': 12,
    'Man City': 13,
    'Man Utd': 14,
    'Newcastle': 15,
    "Nott'm Forest": 16,
    'Sunderland': 17,
    'Spurs': 18,
    'West Ham': 19,
    'Wolves': 20
}

# get_position() 함수 제거 - Premier League API의 positionInfo를 그대로 사용

def similarity(a, b):
    """두 문자열의 유사도 계산 (0~1)"""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def match_player(pl_player, fpl_players):
    """
    Premier League 선수와 FPL 선수 매칭

    Returns:
        (fpl_player, match_type) 또는 (None, None)
    """
    pl_name = pl_player['name']
    pl_first = pl_player['first_name']
    pl_last = pl_player['last_name']

    best_match = None
    best_score = 0
    match_type = None

    for fpl_player in fpl_players:
        fpl_web = fpl_player['web_name']
        fpl_first = fpl_player['first_name']
        fpl_second = fpl_player['second_name']
        fpl_full = fpl_player['full_name']

        # 방법 1: Full name exact match
        if pl_name.lower() == fpl_full.lower():
            return fpl_player, 'FULL_NAME_EXACT'

        # 방법 2: Last name exact match
        if pl_last and fpl_second and pl_last.lower() == fpl_second.lower():
            score = similarity(pl_name, fpl_full)
            if score > best_score:
                best_match = fpl_player
                best_score = score
                match_type = 'LAST_NAME'

        # 방법 3: Web name in PL name
        if fpl_web.lower() in pl_name.lower() or pl_name.lower() in fpl_web.lower():
            score = similarity(pl_name, fpl_full)
            if score > best_score:
                best_match = fpl_player
                best_score = score
                match_type = 'WEB_NAME'

        # 방법 4: Fuzzy matching (similarity > 0.8)
        score = similarity(pl_name, fpl_full)
        if score > 0.8 and score > best_score:
            best_match = fpl_player
            best_score = score
            match_type = f'FUZZY_{score:.2f}'

    if best_match and best_score > 0.7:
        return best_match, match_type

    return None, None

def fetch_premier_league_teams():
    """Premier League API에서 팀 목록 가져오기"""
    print("\n[1/4] Premier League API - 팀 목록 가져오기...")

    headers = {
        'Origin': 'https://www.premierleague.com',
        'User-Agent': 'Mozilla/5.0'
    }

    teams_url = f'https://footballapi.pulselive.com/football/teams?pageSize=100&compSeasons={SEASON_ID}'
    response = requests.get(teams_url, headers=headers, timeout=30)
    response.raise_for_status()
    teams_data = response.json()

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
    return teams_info

def fetch_fpl_data():
    """FPL API에서 전체 데이터 가져오기"""
    print("\n[2/4] FPL API - 선수 상세 정보 가져오기...")

    fpl_url = 'https://fantasy.premierleague.com/api/bootstrap-static/'
    response = requests.get(fpl_url, timeout=30)
    response.raise_for_status()
    data = response.json()

    # 팀별로 선수 분류
    fpl_by_team = {}
    for team_name, fpl_team_id in FPL_TEAM_ID_MAPPING.items():
        team_players = []
        for player in data['elements']:
            if player['team'] == fpl_team_id:
                team_players.append({
                    'id': player['id'],
                    'web_name': player['web_name'],
                    'first_name': player['first_name'],
                    'second_name': player['second_name'],
                    'full_name': f"{player['first_name']} {player['second_name']}".strip(),
                    'photo_code': str(player['code']),
                    'position': player['element_type'],  # 1=GK, 2=DF, 3=MF, 4=FW
                    'now_cost': player['now_cost'],
                    'appearances': player.get('starts', 0),  # FPL API는 'starts' 사용
                    'goals': player.get('goals_scored', 0),
                    'assists': player.get('assists', 0),
                    'clean_sheets': player.get('clean_sheets', 0),
                    'minutes': player.get('minutes', 0)
                })
        fpl_by_team[team_name] = team_players

    total_fpl = sum(len(p) for p in fpl_by_team.values())
    print(f"   ✅ {total_fpl}명 선수 로드 (20개 팀)")

    return fpl_by_team

def fetch_and_match_players(teams_info, fpl_by_team):
    """Premier League API에서 선수 가져와서 FPL 데이터와 매칭"""
    print("\n[3/4] 선수 데이터 가져오기 및 매칭...")

    headers = {
        'Origin': 'https://www.premierleague.com',
        'User-Agent': 'Mozilla/5.0'
    }

    all_players = {}
    total_matched = 0
    total_unmatched = 0
    total_fpl_only = 0

    for team_id, team_info in teams_info.items():
        team_name = team_info['name']
        print(f"\n📋 {team_name}...")

        # Premier League API에서 선수단 가져오기
        staff_url = f'https://footballapi.pulselive.com/football/teams/{team_id}/compseasons/{SEASON_ID}/staff'
        staff_response = requests.get(staff_url, headers=headers, timeout=30)
        staff_response.raise_for_status()
        staff_data = staff_response.json()

        team_players = []
        matched_fpl_ids = set()

        # Premier League 선수 처리
        for player in staff_data.get('players', []):
            if player.get('info', {}).get('loan'):
                continue

            info = player.get('info', {})
            name_data = player.get('name', {})
            player_id = int(player.get('id', 0))

            # 나이 계산
            age_str = player.get('age', '')
            age = 0
            if 'years' in age_str:
                try:
                    age = int(age_str.split('years')[0].strip())
                except:
                    age = 0

            # Premier League API의 positionInfo를 그대로 사용
            position = info.get('positionInfo', 'Central Midfielder')
            shirt_num = int(info.get('shirtNum', 0)) if info.get('shirtNum') else 0

            pl_player = {
                'id': player_id,
                'name': name_data.get('display', ''),
                'first_name': name_data.get('first', ''),
                'last_name': name_data.get('last', ''),
                'position': position,
                'number': shirt_num,
                'age': age
            }

            # FPL 데이터와 매칭
            fpl_players = fpl_by_team.get(team_name, [])
            fpl_match, match_type = match_player(pl_player, fpl_players)

            if fpl_match:
                matched_fpl_ids.add(fpl_match['id'])
                player_data = {
                    'id': player_id,
                    'name': pl_player['name'],
                    'position': position,
                    'number': shirt_num,
                    'age': age,
                    'team_id': team_id,
                    'team_name': team_name,
                    'nationality': '',
                    'photo': fpl_match['photo_code'],
                    'is_starter': fpl_match['appearances'] > 5,
                    'stats': {
                        'appearances': fpl_match['appearances'],
                        'starts': fpl_match['appearances'],
                        'minutes': fpl_match['minutes'],
                        'goals': fpl_match['goals'],
                        'assists': fpl_match['assists'],
                        'clean_sheets': fpl_match['clean_sheets']
                    }
                }
                total_matched += 1
                print(f"   ✓ {pl_player['name']:30s} ↔ {fpl_match['web_name']:20s} ({match_type})")
            else:
                # FPL 매칭 실패 - PL 데이터만 사용
                player_data = {
                    'id': player_id,
                    'name': pl_player['name'],
                    'position': position,
                    'number': shirt_num,
                    'age': age,
                    'team_id': team_id,
                    'team_name': team_name,
                    'nationality': '',
                    'photo': '',
                    'is_starter': False,
                    'stats': {
                        'appearances': player.get('appearances', 0),
                        'starts': player.get('appearances', 0),
                        'minutes': 0,
                        'goals': player.get('goals', 0) if player.get('goals') else 0,
                        'assists': player.get('assists', 0) if player.get('assists') else 0,
                        'clean_sheets': player.get('cleanSheets', 0)
                    }
                }
                total_unmatched += 1
                print(f"   ⚠️ {pl_player['name']:30s} (매칭 실패 - PL 데이터만 사용)")

            team_players.append(player_data)

        # FPL에만 있는 선수 추가 (중요 선수 누락 방지)
        fpl_players = fpl_by_team.get(team_name, [])
        for fpl_player in fpl_players:
            # 출전 기록이 있고 매칭 안된 선수만 추가
            if fpl_player['id'] not in matched_fpl_ids:
                # FPL element_type을 Premier League API 포지션 형식으로 매핑
                # 1=GK, 2=DF, 3=MF, 4=FW → Premier League API 포지션 문자열
                fpl_position_map = {
                    1: 'Goalkeeper',
                    2: 'Central Defender',
                    3: 'Central Midfielder',
                    4: 'Striker'
                }
                position = fpl_position_map.get(fpl_player['position'], 'Central Midfielder')

                # FPL ID를 매우 큰 수로 변환하여 중복 방지 (100억대)
                synthetic_id = 10000000000 + fpl_player['id']

                player_data = {
                    'id': synthetic_id,
                    'name': fpl_player['full_name'],
                    'position': position,
                    'number': 0,  # 등번호 정보 없음
                    'age': 0,
                    'team_id': team_id,
                    'team_name': team_name,
                    'nationality': '',
                    'photo': fpl_player['photo_code'],
                    'is_starter': fpl_player['appearances'] > 5,
                    'stats': {
                        'appearances': fpl_player['appearances'],
                        'starts': fpl_player['appearances'],
                        'minutes': fpl_player['minutes'],
                        'goals': fpl_player['goals'],
                        'assists': fpl_player['assists'],
                        'clean_sheets': fpl_player['clean_sheets']
                    }
                }
                team_players.append(player_data)
                total_fpl_only += 1
                print(f"   + {fpl_player['full_name']:30s} (FPL에만 있음 - 추가, App:{fpl_player['appearances']})")

        all_players[team_name] = team_players
        print(f"   ✅ {len(team_players)}명")

    print(f"\n📊 매칭 통계:")
    print(f"   ✓ 매칭 성공: {total_matched}명")
    print(f"   ⚠️ PL만 사용: {total_unmatched}명")
    print(f"   + FPL만 추가: {total_fpl_only}명")

    return all_players

def update_database(teams_info, all_players):
    """SQLite 데이터베이스 업데이트"""
    print("\n[4/4] 데이터베이스 업데이트 중...")

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
                '',
                '',
                0
            ))

        print(f"   ✅ {len(teams_info)}개 팀 삽입")

        # players 테이블 업데이트
        print("\n📊 players 테이블 업데이트...")

        cursor.execute("SELECT player_id FROM player_ratings")
        rated_players = [row[0] for row in cursor.fetchall()]
        print(f"   ℹ️  평가된 선수: {len(rated_players)}명 (유지됨)")

        cursor.execute("DELETE FROM players")

        player_count = 0
        seen_ids = set()
        skipped_duplicates = 0

        for team_name, players in all_players.items():
            for player in players:
                # ID 중복 체크
                if player['id'] in seen_ids:
                    skipped_duplicates += 1
                    print(f"   ⚠️  중복 ID 스킵: {player['name']} (ID: {player['id']})")
                    continue

                seen_ids.add(player['id'])

                try:
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
                        '',
                        player['number'],
                        player['age'],
                        player['nationality'],
                        '',
                        '',
                        '',
                        '',
                        player['stats']['appearances'],
                        player['stats']['goals'],
                        player['stats']['assists'],
                        player['photo'],
                    ))
                    player_count += 1
                except sqlite3.IntegrityError as e:
                    print(f"   ⚠️  삽입 실패: {player['name']} - {e}")
                    continue

        print(f"   ✅ {player_count}명 선수 삽입")
        if skipped_duplicates > 0:
            print(f"   ⚠️  {skipped_duplicates}명 중복 스킵됨")

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
        f.write('데이터 소스: Premier League API + FPL API (정합성 매칭)\n')
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
    print("\n" + "="*80)
    print("🚀 EPL 데이터 동기화 (정합성 체크 포함)")
    print("="*80)

    try:
        # 1. Premier League API - 팀
        teams_info = fetch_premier_league_teams()

        # 2. FPL API - 선수 상세 정보
        fpl_by_team = fetch_fpl_data()

        # 3. 선수 매칭
        all_players = fetch_and_match_players(teams_info, fpl_by_team)

        # 4. 데이터베이스 업데이트
        if not update_database(teams_info, all_players):
            print("\n❌ 데이터베이스 업데이트 실패")
            sys.exit(1)

        # 5. squad_data.py 업데이트
        update_squad_data_file(all_players)

        # 최종 통계
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

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
