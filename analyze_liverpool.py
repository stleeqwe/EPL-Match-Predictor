#!/usr/bin/env python3
import re

# squad_data.py 파일 읽기
with open('/Users/pukaworks/Desktop/soccer-predictor/backend/data/squad_data.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Liverpool 섹션 찾기
liverpool_start = content.find('"Liverpool":')
if liverpool_start == -1:
    print("Liverpool 섹션을 찾을 수 없습니다.")
    exit(1)

# Liverpool 다음 팀 찾기 (종료 지점 찾기)
# 다음 팀의 시작은 "    ],\n    \"" 패턴
next_team_pattern = re.compile(r'    \],\n    "(?!Liverpool)', re.MULTILINE)
match = next_team_pattern.search(content, liverpool_start)

if match:
    liverpool_end = match.start() + 6  # "    ]," 까지 포함
else:
    # 파일 끝까지
    liverpool_end = len(content)

liverpool_section = content[liverpool_start:liverpool_end]

# photo 필드 추출
photo_pattern = re.compile(r'"name":\s*"([^"]+)"[^}]*?"photo":\s*"([^"]*)"', re.MULTILINE)
matches = photo_pattern.findall(liverpool_section)

print(f"\n🔍 리버풀 선수 Photo 필드 분석")
print(f"총 선수 수: {len(matches)}\n")

empty_count = 0
url_count = 0
valid_count = 0

for i, (name, photo) in enumerate(matches, 1):
    if photo == '':
        print(f"❌ {i}. {name} - EMPTY")
        empty_count += 1
    elif photo.startswith('http'):
        print(f"⚠️  {i}. {name} - URL: {photo}")
        url_count += 1
    else:
        print(f"✅ {i}. {name} - {photo}")
        valid_count += 1

print(f"\n📊 통계:")
print(f"❌ Photo가 비어있는 선수: {empty_count}명")
print(f"⚠️  Photo가 URL인 선수: {url_count}명")
print(f"✅ Photo 코드가 정상인 선수: {valid_count}명")
