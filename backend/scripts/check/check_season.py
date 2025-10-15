import requests
import json

# FPL API에서 데이터 가져오기
response = requests.get('https://fantasy.premierleague.com/api/bootstrap-static/')
data = response.json()

events = data['events']
current = [e for e in events if e.get('is_current')]
next_event = [e for e in events if e.get('is_next')]

print('=== FPL 시즌 상태 ===')
print(f"전체 게임위크 수: {len(events)}")
print(f"완료된 게임위크: {len([e for e in events if e.get('finished')])}")
print(f"진행 중인 게임위크: {current[0]['id'] if current else 'None'}")
print(f"다음 게임위크: {next_event[0]['id'] if next_event else 'None'}")

print('\n=== 최근 3개 게임위크 ===')
for e in events[-3:]:
    print(f"GW{e['id']:2}: {e['name']:20} - 완료: {e.get('finished')}, 현재: {e.get('is_current')}")

print('\n=== 데이터 최종 업데이트 시점 추정 ===')
# 가장 최근 완료된 게임위크 찾기
finished = [e for e in events if e.get('finished')]
if finished:
    last_finished = finished[-1]
    print(f"마지막 완료 GW: {last_finished['id']} - {last_finished['name']}")
    print(f"Deadline: {last_finished.get('deadline_time')}")
