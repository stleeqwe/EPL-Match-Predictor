"""
Fantasy Premier League API에서 실제 선수 데이터 가져와서 squad_data.py 업데이트
"""
import requests
import json
from datetime import datetime
import os
import sys

# 2025-26 시즌 EPL 팀 (20개) - 정확한 현재 시즌 팀 목록
CURRENT_EPL_TEAMS = {
    'Arsenal', 'Aston Villa', 'Bournemouth', 'Brentford', 'Brighton', 'Burnley',
    'Chelsea', 'Crystal Palace', 'Everton', 'Fulham',
    'Leeds', 'Liverpool', 'Man City', 'Man Utd',
    'Newcastle', "Nott'm Forest", 'Sunderland', 'Spurs', 'West Ham', 'Wolves'
}

# Fantasy API 팀 이름 매핑
TEAM_NAME_MAPPING = {
    'Manchester City': 'Man City',
    'Manchester United': 'Man Utd',
    'Tottenham': 'Spurs',
    'Nottingham Forest': "Nott'm Forest",
    'Newcastle United': 'Newcastle',
    'Wolverhampton Wanderers': 'Wolves',
}

def calculate_age(birth_date_str):
    """생년월일로부터 나이 계산"""
    if not birth_date_str:
        return 0
    try:
        birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d')
        today = datetime.now()
        age = today.year - birth_date.year
        # 생일이 지나지 않았으면 1살 빼기
        if (today.month, today.day) < (birth_date.month, birth_date.day):
            age -= 1
        return age
    except:
        return 0

def fetch_real_squad_data():
    """Fantasy API에서 실제 선수 데이터 가져오기"""

    print("="*60)
    print("Fantasy Premier League API에서 데이터 가져오는 중...")
    print("시즌: 2025-26 (현재 진행 중)")
    print("="*60)

    try:
        # Bootstrap 데이터 (팀 + 선수 전체)
        url = 'https://fantasy.premierleague.com/api/bootstrap-static/'
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        print(f"\n✅ API 응답 성공")
        print(f"   팀 수: {len(data['teams'])} 개")
        print(f"   선수 수: {len(data['elements'])} 명")
        
        # 팀 매핑 (Fantasy API 이름 → 우리 이름)
        teams = {}
        reverse_mapping = {v: k for k, v in TEAM_NAME_MAPPING.items()}
        
        for team in data['teams']:
            # Fantasy API 팀 이름을 우리 형식으로 변환
            our_name = TEAM_NAME_MAPPING.get(team['name'], team['name'])
            
            # EPL 팀만 선택
            if our_name in CURRENT_EPL_TEAMS:
                teams[team['id']] = our_name
                print(f"   ✓ {team['name']:30s} → {our_name}")
        
        print(f"\n✅ 2025-26 EPL 팀 확인: {len(teams)} 개")
        
        # 선수 데이터 구조화
        squad_data = {}
        for team_name in teams.values():
            squad_data[team_name] = []
        
        # 선수 데이터 추출
        position_map = ['GK', 'DF', 'MF', 'FW']
        
        player_count_by_team = {}
        
        for player in data['elements']:
            # EPL 팀 선수만
            if player['team'] not in teams:
                continue
                
            team_name = teams[player['team']]
            
            # 주전 판단 (starts >= 3 또는 minutes >= 300)
            starts = player.get('starts', 0)
            minutes = player.get('minutes', 0)
            is_starter = starts >= 3 or minutes >= 300

            # 생년월일로부터 나이 계산
            age = calculate_age(player.get('birth_date'))

            # 선수 사진 코드 추출 (예: "446008.jpg" → "446008")
            photo = player.get('photo', '').replace('.jpg', '').replace('.png', '')

            player_data = {
                'id': player['id'],
                'name': f"{player['first_name']} {player['second_name']}",
                'position': position_map[player['element_type'] - 1],
                'number': player.get('squad_number') or 0,
                'age': age,
                'nationality': '',
                'photo': photo,  # 선수 사진 코드
                'is_starter': is_starter,
                'stats': {
                    'appearances': starts + player.get('substitute_appearances', 0),
                    'starts': starts,
                    'minutes': minutes,
                    'goals': player.get('goals_scored', 0),
                    'assists': player.get('assists', 0),
                    'clean_sheets': player.get('clean_sheets', 0),
                }
            }
            
            squad_data[team_name].append(player_data)
            player_count_by_team[team_name] = player_count_by_team.get(team_name, 0) + 1
        
        # 팀별 정렬 (주전 먼저, 그 다음 등번호 순)
        for team_name in squad_data:
            squad_data[team_name].sort(
                key=lambda p: (not p['is_starter'], p['number'] if p['number'] else 999)
            )
        
        # 통계 출력
        print("\n" + "="*60)
        print("팀별 선수 수:")
        print("="*60)
        for team_name, players in sorted(squad_data.items()):
            starters = sum(1 for p in players if p['is_starter'])
            print(f"  {team_name:25s}: {len(players):2d} 명 (주전: {starters:2d})")
        
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
            f.write('데이터 소스: Fantasy Premier League API\n')
            f.write('"""\n\n')
            # JSON으로 변환 후 true/false를 True/False로 변경 (Python 호환)
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
        
        # 에버튼 샘플 (칼버트-르윈 확인)
        if 'Everton' in squad_data:
            print("\n📋 에버튼 선수단 샘플:")
            print("-"*60)
            everton_players = squad_data['Everton'][:10]
            for p in everton_players:
                starter_mark = "⭐" if p['is_starter'] else "  "
                number = p['number'] if p['number'] else 0
                print(f"{starter_mark} #{number:2d} {p['name']:30s} ({p['position']}) - {p['stats']['starts']}선발/{p['stats']['appearances']}경기")
        
        # 전체 통계
        total_players = sum(len(players) for players in squad_data.values())
        total_starters = sum(
            sum(1 for p in players if p['is_starter'])
            for players in squad_data.values()
        )
        
        print("\n" + "="*60)
        print(f"📊 2025-26 시즌 통계")
        print("="*60)
        print(f"총 {len(squad_data)}개 팀, {total_players}명 선수")
        print(f"주전: {total_starters}명, 벤치: {total_players - total_starters}명")
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
    success = fetch_real_squad_data()
    
    if success:
        print("\n✅ 업데이트 완료!")
        print("\n다음 단계:")
        print("  1. 백엔드 서버 재시작")
        print("  2. 브라우저에서 확인: http://localhost:5001/api/teams")
    else:
        print("\n❌ 업데이트 실패")
        sys.exit(1)
