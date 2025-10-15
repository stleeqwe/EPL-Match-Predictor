#!/usr/bin/env python3
"""
리버풀 선수 photo 필드 확인 스크립트
"""
import sys
sys.path.append('backend/data')

from squad_data import SQUAD_DATA

if 'Liverpool' in SQUAD_DATA:
    players = SQUAD_DATA['Liverpool']
    print(f"\n🔍 Liverpool 선수 데이터 분석")
    print(f"총 선수 수: {len(players)}\n")
    
    empty_photos = []
    valid_photos = []
    
    for i, player in enumerate(players, 1):
        name = player.get('name', 'Unknown')
        photo = player.get('photo', '')
        
        if photo == '':
            print(f"❌ {i}. {name} - EMPTY")
            empty_photos.append(name)
        elif photo.startswith('http'):
            print(f"⚠️  {i}. {name} - URL: {photo}")
            empty_photos.append(name)
        else:
            print(f"✅ {i}. {name} - {photo}")
            valid_photos.append((name, photo))
    
    print(f"\n📊 통계:")
    print(f"❌ Photo가 비어있거나 URL인 선수: {len(empty_photos)}명")
    print(f"✅ Photo 코드가 정상인 선수: {len(valid_photos)}명")
    
    if empty_photos:
        print(f"\n문제가 있는 선수 목록:")
        for name in empty_photos:
            print(f"  - {name}")
else:
    print("Liverpool 팀을 찾을 수 없습니다.")
