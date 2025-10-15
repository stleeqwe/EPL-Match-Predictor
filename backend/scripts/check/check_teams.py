import requests
import json

# FPL API에서 팀 데이터 가져오기
response = requests.get('https://fantasy.premierleague.com/api/bootstrap-static/')
data = response.json()

print('=== FPL 팀 ID 목록 ===')
for team in data['teams']:
    print(f"ID {team['id']:2} - {team['name']:30} ({team['short_name']})")

# 맨체스터 유나이티드 찾기
print('\n=== 맨체스터 유나이티드 ===')
man_u = [t for t in data['teams'] if 'Man' in t['name'] and 'Utd' in t['name']]
if man_u:
    team = man_u[0]
    print(f"ID: {team['id']}")
    print(f"이름: {team['name']}")
    print(f"짧은 이름: {team['short_name']}")
