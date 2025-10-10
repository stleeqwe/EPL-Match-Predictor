import requests
import json

# FPL API에서 데이터 가져오기
response = requests.get('https://fantasy.premierleague.com/api/bootstrap-static/')
data = response.json()

# 에버튼 팀 ID 찾기
everton_id = None
for team in data['teams']:
    if 'Everton' in team['name']:
        everton_id = team['id']
        print(f'Everton Team ID: {everton_id}')
        print(f'Everton Team Name: {team["name"]}')
        break

# 에버튼 선수들 확인
print('\n=== Everton Players from FPL API ===')
everton_players = [p for p in data['elements'] if p['team'] == everton_id]
print(f'Total Everton players: {len(everton_players)}')

# Calvert-Lewin과 Beto 찾기
print('\n--- Key Players ---')
for player in everton_players:
    if 'Calvert' in player['web_name'] or 'Beto' in player['web_name']:
        print(f"\nName: {player['web_name']} ({player['first_name']} {player['second_name']})")
        print(f"  FPL ID: {player['id']}")
        print(f"  Team ID: {player['team']}")
        print(f"  Starts: {player['starts']}")
        print(f"  Minutes: {player['minutes']}")
        print(f"  Goals: {player['goals_scored']}")
        print(f"  Assists: {player['assists']}")

# 리즈 유나이티드 확인
print('\n\n=== Leeds United Check ===')
leeds_id = None
for team in data['teams']:
    if 'Leeds' in team['name']:
        leeds_id = team['id']
        print(f'Leeds Team ID: {leeds_id}')
        print(f'Leeds Team Name: {team["name"]}')
        
        # 리즈 선수 중 Calvert-Lewin 찾기
        leeds_players = [p for p in data['elements'] if p['team'] == leeds_id]
        print(f'Total Leeds players: {len(leeds_players)}')
        
        for player in leeds_players:
            if 'Calvert' in player['web_name']:
                print(f"\nFound in Leeds: {player['web_name']}")
                print(f"  FPL ID: {player['id']}")
        break

if not leeds_id:
    print('Leeds United not found in FPL API (might not be in Premier League)')
