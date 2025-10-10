"""
Premier League 공식 API에서 실제 선수 데이터 가져와서 squad_data.py 업데이트
"""
import requests
import json
from datetime import datetime
import os
import sys

# 2025-26 시즌 ID
SEASON_ID = 777

# Position 매핑
POSITION_MAP = {
    'Goalkeeper': 'GK',
    'Defender': 'DF',
    'Midfielder': 'MF',
    'Forward': 'FW'
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

def fetch_premier_league_data():
    """Premier League API에서 실제 선수 데이터 가져오기"""

    print("="*60)
    print("Premier League 공식 API에서 데이터 가져오는 중...")
    print(f"시즌: 2025-26 (ID: {SEASON_ID})")
    print("="*60)

    try:
        headers = {
            'Origin': 'https://www.premierleague.com',
            'User-Agent': 'Mozilla/5.0'
        }

        # 1. 팀 목록 가져오기
        teams_url = f'https://footballapi.pulselive.com/football/teams?pageSize=100&compSeasons={SEASON_ID}'
        teams_response = requests.get(teams_url, headers=headers, timeout=30)
        teams_response.raise_for_status()
        teams_data = teams_response.json()

        teams = {}
        for team in teams_data['content']:
            team_id = int(team['id'])
            team_name = team['name']
            teams[team_id] = team_name
            print(f"   ✓ {team_name}")

        print(f"\n✅ 총 {len(teams)}개 팀 확인")

        # 2. 각 팀별 선수 데이터 가져오기
        squad_data = {}

        for team_id, team_name in teams.items():
            print(f"\n📋 {team_name} 선수단 로딩...")

            # 팀 선수 명단 가져오기
            staff_url = f'https://footballapi.pulselive.com/football/teams/{team_id}/compseasons/{SEASON_ID}/staff'
            staff_response = requests.get(staff_url, headers=headers, timeout=30)
            staff_response.raise_for_status()
            staff_data = staff_response.json()

            players_list = []

            for player in staff_data.get('players', []):
                # loan 선수 제외
                if player.get('info', {}).get('loan'):
                    continue

                # 선수 정보 추출
                info = player.get('info', {})
                name_data = player.get('name', {})
                birth_data = player.get('birth', {})

                # 나이 계산
                age_str = player.get('age', '')
                age = 0
                if 'years' in age_str:
                    try:
                        age = int(age_str.split('years')[0].strip())
                    except:
                        age = 0

                # 포지션
                position_info = info.get('positionInfo', '')
                position = get_position(position_info)

                # 등번호
                shirt_num = info.get('shirtNum', 0)
                if shirt_num:
                    shirt_num = int(shirt_num)
                else:
                    shirt_num = 0

                player_data = {
                    'id': int(player.get('id', 0)),
                    'name': name_data.get('display', ''),
                    'position': position,
                    'number': shirt_num,
                    'age': age,
                    'nationality': '',
                    'photo': str(player.get('altIds', {}).get('opta', '')).replace('p', ''),
                    'is_starter': False,  # Premier League API는 주전 정보 없음
                    'stats': {
                        'appearances': 0,
                        'starts': 0,
                        'minutes': 0,
                        'goals': 0,
                        'assists': 0,
                        'clean_sheets': 0
                    }
                }

                players_list.append(player_data)

            # 포지션별 정렬 (GK -> DF -> MF -> FW)
            position_order = {'GK': 0, 'DF': 1, 'MF': 2, 'FW': 3}
            players_list.sort(key=lambda p: (
                position_order.get(p['position'], 4),
                p['number'] if p['number'] else 999
            ))

            squad_data[team_name] = players_list
            print(f"   ✅ {len(players_list)}명 선수 로드 완료")

        # 통계 출력
        print("\n" + "="*60)
        print("팀별 선수 수:")
        print("="*60)
        for team_name, players in sorted(squad_data.items()):
            print(f"  {team_name:25s}: {len(players):2d} 명")

        # squad_data.py 생성
        output_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'data',
            'squad_data.py'
        )

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

        print("\n" + "="*60)
        print(f"✅ 파일 저장 완료: {output_path}")
        print("="*60)

        # Manchester United 샘플
        if 'Manchester United' in squad_data:
            print("\n📋 Manchester United 선수단 샘플:")
            print("-"*60)
            man_utd_players = squad_data['Manchester United'][:15]
            for p in man_utd_players:
                number = p['number'] if p['number'] else 0
                print(f"#{number:2d} {p['name']:35s} ({p['position']})")

        # 전체 통계
        total_players = sum(len(players) for players in squad_data.values())

        print("\n" + "="*60)
        print(f"📊 2025-26 시즌 통계")
        print("="*60)
        print(f"총 {len(squad_data)}개 팀, {total_players}명 선수")
        print("="*60)

        return True

    except requests.RequestException as e:
        print(f"\n❌ API 요청 실패: {e}")
        return False
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("\n🚀 EPL 선수 데이터 업데이트 시작 (2025-26 시즌)\n")
    print("⚠️  Premier League 공식 API 사용\n")
    success = fetch_premier_league_data()

    if success:
        print("\n✅ 업데이트 완료!")
        print("\n다음 단계:")
        print("  1. 백엔드 서버 재시작")
        print("  2. 브라우저에서 확인: http://localhost:5001/api/teams")
    else:
        print("\n❌ 업데이트 실패")
        sys.exit(1)
