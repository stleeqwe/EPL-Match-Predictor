"""
EPL Official Website Squad Scraper
프리미어리그 공식 웹사이트에서 팀별 스쿼드 정보 스크래핑
"""
import requests
from bs4 import BeautifulSoup
import json
import time
import re

# EPL 공식 사이트 팀 정보 (club_id와 slug)
EPL_TEAMS = {
    'Arsenal': {'id': 3, 'slug': 'Arsenal'},
    'Aston Villa': {'id': 7, 'slug': 'Aston-Villa'},
    'Bournemouth': {'id': 91, 'slug': 'AFC-Bournemouth'},
    'Brentford': {'id': 94, 'slug': 'Brentford'},
    'Brighton': {'id': 131, 'slug': 'Brighton-and-Hove-Albion'},
    'Chelsea': {'id': 8, 'slug': 'Chelsea'},
    'Crystal Palace': {'id': 31, 'slug': 'Crystal-Palace'},
    'Everton': {'id': 11, 'slug': 'Everton'},
    'Fulham': {'id': 36, 'slug': 'Fulham'},
    'Ipswich Town': {'id': 40, 'slug': 'Ipswich-Town'},
    'Leicester City': {'id': 13, 'slug': 'Leicester-City'},
    'Liverpool': {'id': 10, 'slug': 'Liverpool'},
    'Man City': {'id': 43, 'slug': 'Manchester-City'},
    'Man Utd': {'id': 12, 'slug': 'Manchester-United'},
    'Newcastle': {'id': 4, 'slug': 'Newcastle-United'},
    "Nott'm Forest": {'id': 15, 'slug': 'Nottingham-Forest'},
    'Southampton': {'id': 20, 'slug': 'Southampton'},
    'Spurs': {'id': 6, 'slug': 'Tottenham-Hotspur'},
    'West Ham': {'id': 21, 'slug': 'West-Ham-United'},
    'Wolves': {'id': 38, 'slug': 'Wolverhampton-Wanderers'}
}

def scrape_team_squad_epl(team_name, team_info):
    """
    EPL 공식 사이트에서 특정 팀의 스쿼드 정보 스크래핑
    """
    club_id = team_info['id']
    slug = team_info['slug']
    url = f"https://www.premierleague.com/clubs/{club_id}/{slug}/squad"

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # 선수 카드 찾기 (EPL 사이트 구조에 따라 조정 필요)
        players = []

        # 방법 1: 선수 목록 테이블
        player_table = soup.find('table', class_='squad-table')
        if player_table:
            rows = player_table.find_all('tr')[1:]  # 헤더 제외
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 3:
                    try:
                        number_text = cols[0].get_text().strip()
                        number = int(re.findall(r'\d+', number_text)[0]) if re.findall(r'\d+', number_text) else None
                        name = cols[1].get_text().strip()
                        position = cols[2].get_text().strip()

                        if name and number:
                            players.append({
                                'number': number,
                                'name': name,
                                'position': position,
                                'team': team_name
                            })
                    except:
                        continue

        # 방법 2: 선수 카드 (일반적인 구조)
        if not players:
            player_cards = soup.find_all(['div', 'li'], class_=re.compile(r'player|squad'))
            for card in player_cards[:50]:  # 최대 50개만 확인
                try:
                    # 등번호 추출
                    number_elem = card.find(['span', 'div'], class_=re.compile(r'number|shirt'))
                    if number_elem:
                        number_text = number_elem.get_text().strip()
                        number = int(re.findall(r'\d+', number_text)[0]) if re.findall(r'\d+', number_text) else None
                    else:
                        continue

                    # 이름 추출
                    name_elem = card.find(['span', 'div', 'a'], class_=re.compile(r'name'))
                    if name_elem:
                        name = name_elem.get_text().strip()
                    else:
                        continue

                    # 포지션 추출
                    pos_elem = card.find(['span', 'div'], class_=re.compile(r'position|pos'))
                    position = pos_elem.get_text().strip() if pos_elem else 'Unknown'

                    if name and number:
                        players.append({
                            'number': number,
                            'name': name,
                            'position': position,
                            'team': team_name
                        })
                except:
                    continue

        print(f"{'✓' if players else '✗'} {team_name}: {len(players)} players")
        return players

    except requests.exceptions.RequestException as e:
        print(f"✗ {team_name}: Failed to fetch - {e}")
        return []
    except Exception as e:
        print(f"✗ {team_name}: Error - {e}")
        return []

def scrape_all_squads_epl():
    """
    모든 EPL 팀의 스쿼드 정보 스크래핑
    """
    all_players = []

    print("=== EPL Official Website Squad Scraper ===\n")

    for team_name, team_info in EPL_TEAMS.items():
        players = scrape_team_squad_epl(team_name, team_info)
        all_players.extend(players)
        time.sleep(2)  # 서버 부하 방지

    print(f"\n=== Total: {len(all_players)} players from {len(EPL_TEAMS)} teams ===")
    return all_players

def save_squads_to_json(filename='epl_squads_official.json'):
    """
    스쿼드 정보를 JSON 파일로 저장
    """
    players = scrape_all_squads_epl()

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
    print("\n=== Manchester United Squad ===")
    man_u_players = squads.get('Man Utd', [])
    print(f"Total players: {len(man_u_players)}")

    if man_u_players:
        player_19 = [p for p in man_u_players if p['number'] == 19]
        if player_19:
            print(f"\n#19: {player_19[0]['name']} - {player_19[0]['position']}")
        else:
            print("\nNo player with #19")

        # Mainoo 확인
        mainoo = [p for p in man_u_players if 'Mainoo' in p['name']]
        if mainoo:
            print(f"Kobbie Mainoo: #{mainoo[0]['number']} - {mainoo[0]['position']}")
