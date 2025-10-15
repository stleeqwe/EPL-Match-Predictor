import requests
import json

# FPL API에서 데이터 가져오기
response = requests.get('https://fantasy.premierleague.com/api/bootstrap-static/')
data = response.json()

# 맨체스터 유나이티드는 팀 ID 14
man_u_players = [p for p in data['elements'] if p['team'] == 14]

print('=== 맨체스터 유나이티드 19번 선수 ===')
player_19 = [p for p in man_u_players if p.get('squad_number') == 19]
if player_19:
    p = player_19[0]
    print(f"이름: {p['first_name']} {p['second_name']}")
    print(f"웹 이름: {p['web_name']}")
    print(f"등번호: {p.get('squad_number', 'N/A')}")
    print(f"포지션: {p['element_type']}")
else:
    print('19번 선수 없음')

print('\n=== 맨유 전체 선수 (등번호 순) ===')
sorted_players = sorted(man_u_players, key=lambda x: (x.get('squad_number') is None, x.get('squad_number', 999)))
for p in sorted_players:
    squad_num = p.get('squad_number', 'N/A')
    print(f"{str(squad_num):>4} - {p['web_name']:20} - {p['first_name']} {p['second_name']}")

# Mainoo 검색
print('\n=== "Mainoo" 검색 ===')
mainoo = [p for p in man_u_players if 'mainoo' in p['web_name'].lower() or 'mainoo' in p['second_name'].lower()]
for p in mainoo:
    print(f"{p.get('squad_number', '?'):3} - {p['web_name']:20} - {p['first_name']} {p['second_name']}")
