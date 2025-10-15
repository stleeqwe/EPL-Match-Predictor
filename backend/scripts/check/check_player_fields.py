import requests
import json

# FPL API에서 데이터 가져오기
response = requests.get('https://fantasy.premierleague.com/api/bootstrap-static/')
data = response.json()

# 맨체스터 유나이티드 팀 ID 14
man_u_players = [p for p in data['elements'] if p['team'] == 14]

if man_u_players:
    print('=== 첫 번째 맨유 선수의 전체 필드 ===')
    player = man_u_players[0]
    for key in sorted(player.keys()):
        value = player[key]
        if isinstance(value, str) and len(value) > 50:
            value = value[:50] + '...'
        print(f"{key:30} : {value}")

    print('\n=== Mainoo 선수 전체 정보 ===')
    mainoo = [p for p in man_u_players if 'mainoo' in p['web_name'].lower()]
    if mainoo:
        player = mainoo[0]
        for key in ['id', 'first_name', 'second_name', 'web_name', 'team', 'squad_number', 'element_type', 'now_cost']:
            print(f"{key:20} : {player.get(key, 'N/A')}")
else:
    print('맨유 선수를 찾을 수 없습니다.')
