"""
EPL 공식 사이트 스쿼드 스크래핑 v2
개선된 URL 패턴과 파싱 로직
"""
import requests
from bs4 import BeautifulSoup
import json
import time
import re

# EPL 2024-25 시즌 20개 팀
EPL_TEAMS_2024 = {
    'Aston Villa': 7,
    'Bournemouth': 91,
    'Brentford': 94,
    'Brighton': 131,
    'Crystal Palace': 31,
    'Everton': 11,
    'Fulham': 36,
    'Ipswich Town': 40,
    'Leicester City': 13,
    'Newcastle': 4,
    "Nott'm Forest": 15,
    'Southampton': 20,
    'West Ham': 21,
    'Wolves': 38
}

def scrape_team_squad(team_name, team_id):
    """EPL 공식 사이트에서 팀 스쿼드 정보 스크래핑"""

    # 여러 URL 패턴 시도
    urls_to_try = [
        f"https://www.premierleague.com/clubs/{team_id}/squad",
        f"https://www.premierleague.com/clubs/{team_id}/players",
    ]

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    }

    squad = []

    for url in urls_to_try:
        try:
            print(f"  Trying: {url}")
            response = requests.get(url, headers=headers, timeout=15)

            if response.status_code == 404:
                print(f"  404 Not Found")
                continue

            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            # HTML 내용 일부 출력하여 구조 확인
            print(f"  Response length: {len(response.content)} bytes")

            # 다양한 선수 컨테이너 패턴 시도
            player_containers = (
                soup.find_all('div', class_=re.compile(r'player', re.I)) +
                soup.find_all('li', class_=re.compile(r'player', re.I)) +
                soup.find_all('tr', class_=re.compile(r'player', re.I))
            )

            print(f"  Found {len(player_containers)} potential player elements")

            if player_containers:
                for container in player_containers[:50]:  # 최대 50개만 확인
                    try:
                        # 등번호 찾기
                        number_elem = container.find(['span', 'div'], class_=re.compile(r'number|shirt', re.I))
                        if not number_elem:
                            number_elem = container.find(text=re.compile(r'^\d+$'))

                        if number_elem:
                            number_text = number_elem.get_text().strip() if hasattr(number_elem, 'get_text') else str(number_elem)
                            number_match = re.search(r'\d+', number_text)
                            if number_match:
                                number = int(number_match.group())
                            else:
                                continue
                        else:
                            continue

                        # 이름 찾기
                        name_elem = container.find(['a', 'span', 'div'], class_=re.compile(r'name', re.I))
                        if not name_elem:
                            # a 태그 중에서 선수 이름이 있을 만한 것 찾기
                            links = container.find_all('a')
                            for link in links:
                                if len(link.get_text().strip()) > 2:
                                    name_elem = link
                                    break

                        if name_elem:
                            name = name_elem.get_text().strip()
                            name = re.sub(r'\s+', ' ', name)  # 중복 공백 제거
                        else:
                            continue

                        # 포지션 찾기
                        pos_elem = container.find(['span', 'div'], class_=re.compile(r'position|pos', re.I))
                        if pos_elem:
                            position_text = pos_elem.get_text().strip()
                            # 포지션 매핑
                            if 'GK' in position_text.upper() or 'GOALKEEPER' in position_text.upper():
                                position = 'GK'
                            elif 'DEF' in position_text.upper() or 'BACK' in position_text.upper():
                                position = 'DF'
                            elif 'MID' in position_text.upper() or 'MF' in position_text.upper():
                                position = 'MF'
                            elif 'FW' in position_text.upper() or 'FOR' in position_text.upper() or 'ATT' in position_text.upper():
                                position = 'FW'
                            else:
                                position = position_text[:2].upper()
                        else:
                            position = 'Unknown'

                        if name and number and len(name) > 1:
                            squad.append({
                                'number': number,
                                'name': name,
                                'position': position
                            })
                    except Exception as e:
                        continue

                if squad:
                    break  # 성공했으면 다른 URL 시도 안 함

        except requests.exceptions.RequestException as e:
            print(f"  Request failed: {e}")
            continue
        except Exception as e:
            print(f"  Error: {e}")
            continue

    # 등번호 순 정렬 및 중복 제거
    if squad:
        unique_squad = []
        seen = set()
        for player in sorted(squad, key=lambda x: x['number']):
            key = (player['number'], player['name'])
            if key not in seen:
                seen.add(key)
                unique_squad.append(player)
        squad = unique_squad

    print(f"{'✓' if squad else '✗'} {team_name}: {len(squad)} players")
    return squad

def main():
    print("=== EPL Squad Scraper v2 ===\n")

    all_squads = {}

    for team_name, team_id in EPL_TEAMS_2024.items():
        print(f"\n{team_name}:")
        squad = scrape_team_squad(team_name, team_id)
        if squad:
            all_squads[team_name] = squad
        time.sleep(2)  # 서버 부하 방지

    print(f"\n\n=== 총 {len(all_squads)}개 팀 수집 완료 ===")

    # 결과 저장
    output_file = '../data/epl_remaining_squads.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_squads, f, indent=2, ensure_ascii=False)

    print(f"저장 완료: {output_file}")

    return all_squads

if __name__ == '__main__':
    squads = main()

    # 결과 미리보기
    for team_name, squad in squads.items():
        print(f"\n{team_name}: {len(squad)}명")
        for player in squad[:3]:
            print(f"  #{player['number']} {player['name']} ({player['position']})")
