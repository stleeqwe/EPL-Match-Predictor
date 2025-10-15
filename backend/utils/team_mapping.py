"""
팀 이름 매핑 유틸리티
EPL 팀 이름의 다양한 형식 간 매핑을 관리
"""

# 팀 이름 매핑 (Squad Data 형식 -> Fantasy API 형식)
TEAM_NAME_MAPPING = {
    'Arsenal': 'Arsenal',
    'Aston Villa': 'Aston Villa',
    'Bournemouth': 'Bournemouth',
    'Brentford': 'Brentford',
    'Brighton': 'Brighton',
    'Chelsea': 'Chelsea',
    'Crystal Palace': 'Crystal Palace',
    'Everton': 'Everton',
    'Fulham': 'Fulham',
    'Ipswich': 'Ipswich',
    'Leicester': 'Leicester',
    'Liverpool': 'Liverpool',
    'Man City': 'Manchester City',
    'Man Utd': 'Manchester United',
    'Newcastle': 'Newcastle United',
    "Nott'm Forest": 'Nottingham Forest',
    'Southampton': 'Southampton',
    'Spurs': 'Tottenham',
    'West Ham': 'West Ham',
    'Wolves': 'Wolverhampton Wanderers'
}

# 역매핑 (Fantasy API 형식 -> Squad Data 형식)
REVERSE_TEAM_MAPPING = {v: k for k, v in TEAM_NAME_MAPPING.items()}

# 팀 이름 별칭 (다양한 형식 처리)
TEAM_ALIASES = {
    'Manchester United': 'Man Utd',
    'Manchester City': 'Man City',
    'Tottenham Hotspur': 'Spurs',
    'Nottingham Forest': "Nott'm Forest",
    'Newcastle United': 'Newcastle',
    'Wolverhampton': 'Wolves',
    'Brighton and Hove Albion': 'Brighton',
    'West Ham United': 'West Ham'
}

# 강등팀 목록 (2024-25 시즌)
RELEGATED_TEAMS = ['Leicester City', 'Ipswich Town', 'Southampton']


def normalize_team_name(team_name, to_format='squad'):
    """
    팀 이름을 지정된 형식으로 정규화

    Args:
        team_name: 입력 팀 이름
        to_format: 'squad' (Squad Data 형식) 또는 'fantasy' (Fantasy API 형식)

    Returns:
        정규화된 팀 이름
    """
    # 먼저 별칭 확인
    if team_name in TEAM_ALIASES:
        team_name = TEAM_ALIASES[team_name]

    if to_format == 'squad':
        # Fantasy -> Squad 형식
        if team_name in REVERSE_TEAM_MAPPING:
            return REVERSE_TEAM_MAPPING[team_name]
        # 이미 Squad 형식이거나 매핑이 없는 경우
        return team_name
    elif to_format == 'fantasy':
        # Squad -> Fantasy 형식
        if team_name in TEAM_NAME_MAPPING:
            return TEAM_NAME_MAPPING[team_name]
        # 이미 Fantasy 형식이거나 매핑이 없는 경우
        return team_name
    else:
        return team_name


def get_team_id_mapping(fantasy_teams):
    """
    Fantasy API 팀 리스트에서 팀 이름과 ID 매핑 생성

    Args:
        fantasy_teams: Fantasy API의 teams 리스트

    Returns:
        dict: {squad_team_name: team_id}
    """
    team_id_map = {}

    for team in fantasy_teams:
        fantasy_name = team.get('name', '')
        squad_name = normalize_team_name(fantasy_name, to_format='squad')
        team_id_map[squad_name] = team.get('id')

    return team_id_map


def is_relegated_team(team_name):
    """
    강등팀 여부 확인

    Args:
        team_name: 팀 이름

    Returns:
        bool: 강등팀이면 True
    """
    return team_name in RELEGATED_TEAMS