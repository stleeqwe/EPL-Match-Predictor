"""
Wikipedia EPL Squad Scraper
각 EPL 팀의 2024-25 시즌 스쿼드 정보를 Wikipedia에서 스크래핑
"""
import requests
from bs4 import BeautifulSoup
import json
import re
import time

# EPL 팀 목록 (Wikipedia 페이지 이름)
EPL_TEAMS = {
    'Arsenal': 'Arsenal_F.C.',
    'Aston Villa': 'Aston_Villa_F.C.',
    'Bournemouth': 'AFC_Bournemouth',
    'Brentford': 'Brentford_F.C.',
    'Brighton': 'Brighton_%26_Hove_Albion_F.C.',
    'Chelsea': 'Chelsea_F.C.',
    'Crystal Palace': 'Crystal_Palace_F.C.',
    'Everton': 'Everton_F.C.',
    'Fulham': 'Fulham_F.C.',
    'Ipswich Town': 'Ipswich_Town_F.C.',
    'Leicester City': 'Leicester_City_F.C.',
    'Liverpool': 'Liverpool_F.C.',
    'Man City': 'Manchester_City_F.C.',
    'Man Utd': 'Manchester_United_F.C.',
    'Newcastle': 'Newcastle_United_F.C.',
    "Nott'm Forest": 'Nottingham_Forest_F.C.',
    'Southampton': 'Southampton_F.C.',
    'Spurs': 'Tottenham_Hotspur_F.C.',
    'West Ham': 'West_Ham_United_F.C.',
    'Wolves': 'Wolverhampton_Wanderers_F.C.'
}

def scrape_team_squad(team_name, wiki_page):
    """
    특정 팀의 스쿼드 정보를 Wikipedia에서 스크래핑
    """
    url = f"https://en.wikipedia.org/wiki/2024–25_{wiki_page}_season"

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # 스쿼드 테이블 찾기
        squad_table = None
        for table in soup.find_all('table', class_='wikitable'):
            # 테이블 헤더에 "No." 또는 "Pos" 포함 여부 확인
            headers = [th.get_text().strip() for th in table.find_all('th')]
            if any('No' in h or 'Pos' in h for h in headers):
                squad_table = table
                break

        if not squad_table:
            print(f"⚠️  {team_name}: Squad table not found")
            return []

        players = []
        rows = squad_table.find_all('tr')[1:]  # 헤더 제외

        for row in rows:
            cols = row.find_all(['td', 'th'])
            if len(cols) < 3:
                continue

            try:
                # 등번호 추출
                number_text = cols[0].get_text().strip()
                number = int(re.findall(r'\d+', number_text)[0]) if re.findall(r'\d+', number_text) else None

                # 포지션 추출 (보통 2번째 열)
                position = cols[1].get_text().strip()

                # 선수 이름 추출
                name_col = cols[2]
                # 링크가 있으면 링크 텍스트 사용, 없으면 전체 텍스트 사용
                link = name_col.find('a')
                if link:
                    name = link.get_text().strip()
                else:
                    name = name_col.get_text().strip()

                # 국적 정보 제거 (괄호 안 내용 제거)
                name = re.sub(r'\([^)]*\)', '', name).strip()

                if name and number:
                    players.append({
                        'number': number,
                        'name': name,
                        'position': position,
                        'team': team_name
                    })
            except Exception as e:
                continue

        print(f"✓ {team_name}: {len(players)} players")
        return players

    except requests.exceptions.RequestException as e:
        print(f"✗ {team_name}: Failed to fetch - {e}")
        return []
    except Exception as e:
        print(f"✗ {team_name}: Error parsing - {e}")
        return []

def scrape_all_squads():
    """
    모든 EPL 팀의 스쿼드 정보를 스크래핑
    """
    all_players = []

    print("=== Wikipedia EPL Squad Scraper ===\n")

    for team_name, wiki_page in EPL_TEAMS.items():
        players = scrape_team_squad(team_name, wiki_page)
        all_players.extend(players)
        time.sleep(1)  # Wikipedia 서버 부하 방지

    print(f"\n=== Total: {len(all_players)} players from {len(EPL_TEAMS)} teams ===")

    return all_players

def save_squads_to_json(filename='epl_squads.json'):
    """
    스쿼드 정보를 JSON 파일로 저장
    """
    players = scrape_all_squads()

    # 팀별로 그룹화
    squads = {}
    for player in players:
        team = player['team']
        if team not in squads:
            squads[team] = []
        squads[team].append({
            'number': player['number'],
            'name': player['name'],
            'position': player['position']
        })

    # 각 팀의 선수를 등번호 순으로 정렬
    for team in squads:
        squads[team] = sorted(squads[team], key=lambda x: x['number'])

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(squads, f, indent=2, ensure_ascii=False)

    print(f"\nSaved to {filename}")
    return squads

if __name__ == '__main__':
    squads = save_squads_to_json()

    # 맨유 19번 선수 확인
    print("\n=== Manchester United #19 ===")
    man_u_players = squads.get('Man Utd', [])
    player_19 = [p for p in man_u_players if p['number'] == 19]
    if player_19:
        print(f"Name: {player_19[0]['name']}")
        print(f"Position: {player_19[0]['position']}")
    else:
        print("No player with #19")

    # Mainoo 확인
    mainoo = [p for p in man_u_players if 'Mainoo' in p['name']]
    if mainoo:
        print(f"\nKobbie Mainoo: #{mainoo[0]['number']} - {mainoo[0]['position']}")
