"""
20개 EPL 팀 전체 데이터 자동 생성
각 팀마다 11명 선수 평가 + 코멘트 + 전술 + 라인업
"""

import os
import sys
import json
from datetime import datetime

current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from database.player_schema import Player, get_player_session
from sqlalchemy import func

DATA_DIR = os.path.join(backend_dir, 'data')
DB_PATH = os.path.join(DATA_DIR, 'epl_data.db')


def get_team_id(session, team_name):
    """팀 ID 조회"""
    from database.player_schema import Team
    team = session.query(Team).filter_by(name=team_name).first()
    return team.id if team else None


def get_team_players(session, team_id, limit=30):
    """팀의 선수 목록 조회"""
    players = session.query(Player).filter_by(team_id=team_id).limit(limit).all()
    return players


def generate_rating(base, variation=0.5):
    """평점 생성 (base ± variation)"""
    import random
    return round(max(1.0, min(5.0, base + random.uniform(-variation, variation))), 2)


def generate_player_ratings_by_position(position_type, base_level='good'):
    """포지션별 평점 생성"""
    import random

    # 기본 레벨 설정
    level_map = {
        'world_class': 4.5,
        'excellent': 4.0,
        'good': 3.5,
        'average': 3.0,
        'below_average': 2.5
    }
    base = level_map.get(base_level, 3.5)

    if 'Goalkeeper' in position_type:
        attrs = ['reflexes', 'positioning_reading', 'handling', 'kicking',
                'aerial_duel', 'one_on_one', 'composure_judgement', 'distribution',
                'speed', 'leadership']
    elif any(x in position_type for x in ['Defender', 'Back']):
        attrs = ['positioning_reading', 'composure_judgement', 'interception',
                'aerial_duel', 'tackle_marking', 'speed', 'passing',
                'physical_jumping', 'buildup_contribution', 'leadership']
    elif any(x in position_type for x in ['Midfielder', 'Midfield']):
        attrs = ['passing', 'vision', 'positioning_reading', 'interception',
                'tackle_marking', 'stamina', 'composure_judgement',
                'buildup_contribution', 'leadership', 'speed']
    elif any(x in position_type for x in ['Winger', 'Wing']):
        attrs = ['speed_dribbling', 'one_on_one_beating', 'speed', 'acceleration',
                'crossing_accuracy', 'shooting_accuracy', 'agility_direction_change',
                'cutting_in', 'defensive_contribution', 'creativity',
                'link_up_play', 'cutback_pass']
    elif any(x in position_type for x in ['Striker', 'Forward']):
        attrs = ['finishing', 'positioning_reading', 'shooting_accuracy',
                'heading', 'one_on_one_beating', 'speed', 'acceleration',
                'link_up_play', 'physical_jumping', 'composure_judgement']
    else:
        # Default midfielder
        attrs = ['passing', 'vision', 'positioning_reading', 'stamina',
                'composure_judgement', 'speed', 'leadership', 'tackle_marking',
                'buildup_contribution', 'interception']

    ratings = {}
    for attr in attrs:
        ratings[attr] = generate_rating(base, variation=0.5)

    return ratings


def generate_player_comment(player_name, position_type, rating_level):
    """선수 코멘트 생성"""
    templates = {
        'world_class': [
            f"Elite {position_type.lower()} with exceptional technical quality.",
            f"World-class player who dominates their position.",
            f"Outstanding {position_type.lower()} with consistent top performance."
        ],
        'excellent': [
            f"High-quality {position_type.lower()} with strong all-round ability.",
            f"Reliable and consistent performer in key matches.",
            f"Technically gifted {position_type.lower()} who contributes significantly."
        ],
        'good': [
            f"Solid {position_type.lower()} who performs their role effectively.",
            f"Dependable player with good technical skills.",
            f"Consistent performer who contributes to team play."
        ],
        'average': [
            f"Capable {position_type.lower()} with room for development.",
            f"Decent player who fills their position adequately.",
            f"Functional {position_type.lower()} with basic qualities."
        ],
        'below_average': [
            f"Developing {position_type.lower()} still finding consistency.",
            f"Squad player who provides depth options.",
            f"Young {position_type.lower()} with potential to improve."
        ]
    }

    import random
    return random.choice(templates.get(rating_level, templates['good']))


def generate_tactics(team_style='balanced'):
    """전술 생성"""
    import random

    styles = {
        'attacking': {
            'defensive': {'pressing_intensity': 8, 'defensive_line': 8, 'defensive_width': 7,
                         'compactness': 6, 'line_distance': 12.0},
            'offensive': {'tempo': 8, 'buildup_style': 'short_passing', 'width': 9,
                         'creativity': 9, 'passing_directness': 4},
            'transition': {'counter_press': 9, 'counter_speed': 9, 'transition_time': 2.0,
                          'recovery_speed': 8}
        },
        'balanced': {
            'defensive': {'pressing_intensity': 7, 'defensive_line': 7, 'defensive_width': 7,
                         'compactness': 7, 'line_distance': 10.0},
            'offensive': {'tempo': 7, 'buildup_style': 'mixed', 'width': 7,
                         'creativity': 7, 'passing_directness': 5},
            'transition': {'counter_press': 7, 'counter_speed': 7, 'transition_time': 2.5,
                          'recovery_speed': 7}
        },
        'defensive': {
            'defensive': {'pressing_intensity': 6, 'defensive_line': 5, 'defensive_width': 8,
                         'compactness': 9, 'line_distance': 8.0},
            'offensive': {'tempo': 6, 'buildup_style': 'long_ball', 'width': 6,
                         'creativity': 6, 'passing_directness': 7},
            'transition': {'counter_press': 6, 'counter_speed': 8, 'transition_time': 3.0,
                          'recovery_speed': 6}
        }
    }

    return styles.get(team_style, styles['balanced'])


def generate_team_comment(team_name, style):
    """팀 전략 코멘트 생성"""
    templates = {
        'attacking': f"{team_name} play an aggressive, high-pressing style with quick transitions. Emphasis on creative play and attacking width.",
        'balanced': f"{team_name} deploy a well-organized system balancing defensive solidity with attacking threat. Focus on tactical discipline.",
        'defensive': f"{team_name} prioritize defensive stability with compact shape. Counter-attacking opportunities when possession is won."
    }
    return templates.get(style, templates['balanced'])


def generate_team_strength_ratings(team_level):
    """팀 전력 평가 생성"""
    level_map = {
        'top': {'tactical_understanding': 4.5, 'positioning_balance': 4.25, 'buildup_quality': 4.5},
        'upper': {'tactical_understanding': 4.0, 'positioning_balance': 4.0, 'buildup_quality': 4.0},
        'mid': {'tactical_understanding': 3.5, 'positioning_balance': 3.5, 'buildup_quality': 3.5},
        'lower': {'tactical_understanding': 3.0, 'positioning_balance': 3.0, 'buildup_quality': 3.0}
    }
    return level_map.get(team_level, level_map['mid'])


# 20개 팀 설정
TEAMS_CONFIG = {
    'Arsenal': {'formation': '4-3-3', 'style': 'attacking', 'level': 'top', 'player_level': 'excellent'},
    'Liverpool': {'formation': '4-3-3', 'style': 'attacking', 'level': 'top', 'player_level': 'excellent'},
    'Man City': {'formation': '4-3-3', 'style': 'attacking', 'level': 'top', 'player_level': 'world_class'},
    'Chelsea': {'formation': '4-2-3-1', 'style': 'balanced', 'level': 'top', 'player_level': 'excellent'},
    'Man Utd': {'formation': '4-2-3-1', 'style': 'balanced', 'level': 'upper', 'player_level': 'good'},
    'Spurs': {'formation': '4-3-3', 'style': 'attacking', 'level': 'upper', 'player_level': 'good'},
    'Newcastle': {'formation': '4-3-3', 'style': 'balanced', 'level': 'upper', 'player_level': 'good'},
    'Aston Villa': {'formation': '4-4-2', 'style': 'balanced', 'level': 'upper', 'player_level': 'good'},
    'Brighton': {'formation': '4-2-3-1', 'style': 'attacking', 'level': 'mid', 'player_level': 'good'},
    'West Ham': {'formation': '4-2-3-1', 'style': 'balanced', 'level': 'mid', 'player_level': 'average'},
    'Fulham': {'formation': '4-3-3', 'style': 'balanced', 'level': 'mid', 'player_level': 'average'},
    'Brentford': {'formation': '3-5-2', 'style': 'balanced', 'level': 'mid', 'player_level': 'average'},
    'Crystal Palace': {'formation': '4-3-3', 'style': 'balanced', 'level': 'mid', 'player_level': 'average'},
    'Wolves': {'formation': '3-4-3', 'style': 'defensive', 'level': 'mid', 'player_level': 'average'},
    'Bournemouth': {'formation': '4-4-2', 'style': 'balanced', 'level': 'lower', 'player_level': 'average'},
    'Everton': {'formation': '4-4-2', 'style': 'defensive', 'level': 'lower', 'player_level': 'average'},
    'Nott\'m Forest': {'formation': '4-2-3-1', 'style': 'defensive', 'level': 'lower', 'player_level': 'average'},
    'Burnley': {'formation': '4-4-2', 'style': 'defensive', 'level': 'lower', 'player_level': 'below_average'},
    'Leeds': {'formation': '4-1-4-1', 'style': 'attacking', 'level': 'lower', 'player_level': 'average'},
    'Sunderland': {'formation': '4-4-2', 'style': 'defensive', 'level': 'lower', 'player_level': 'below_average'}
}


FORMATION_POSITIONS = {
    '4-3-3': ['GK', 'LB', 'CB1', 'CB2', 'RB', 'DM', 'CM1', 'CM2', 'LW', 'ST', 'RW'],
    '4-2-3-1': ['GK', 'LB', 'CB1', 'CB2', 'RB', 'DM1', 'DM2', 'CAM', 'LW', 'ST', 'RW'],
    '4-4-2': ['GK', 'LB', 'CB1', 'CB2', 'RB', 'LM', 'CM1', 'CM2', 'RM', 'ST1', 'ST2'],
    '3-5-2': ['GK', 'CB1', 'CB2', 'CB3', 'LWB', 'RWB', 'DM', 'CM1', 'CM2', 'ST1', 'ST2'],
    '3-4-3': ['GK', 'CB1', 'CB2', 'CB3', 'LWB', 'RWB', 'CM1', 'CM2', 'LW', 'ST', 'RW'],
    '4-1-4-1': ['GK', 'LB', 'CB1', 'CB2', 'RB', 'DM', 'LM', 'CM1', 'CM2', 'RM', 'ST']
}


def process_team(session, team_name, config):
    """팀 데이터 생성"""
    print(f"\n{'#'*70}")
    print(f"# Processing: {team_name}")
    print(f"{'#'*70}\n")

    # 팀 ID 조회
    team_id = get_team_id(session, team_name)
    if not team_id:
        print(f"  ❌ Team '{team_name}' not found in database")
        return False

    # 선수 목록 조회
    players = get_team_players(session, team_id, limit=30)
    if len(players) < 11:
        print(f"  ❌ Team '{team_name}' has only {len(players)} players (need 11)")
        return False

    # 포메이션 포지션
    formation = config['formation']
    positions = FORMATION_POSITIONS.get(formation, FORMATION_POSITIONS['4-3-3'])

    # 11명 선수 선택 및 평가 생성
    lineup = {}
    player_level = config['player_level']

    for i, position in enumerate(positions):
        if i >= len(players):
            break

        player = players[i]
        ratings = generate_player_ratings_by_position(player.position, base_level=player_level)
        comment = generate_player_comment(player.name, player.position, player_level)

        lineup[position] = {
            'id': player.id,
            'name': player.name,
            'position_type': player.position,
            'ratings': ratings,
            'comment': comment
        }

        print(f"  [{position:6s}] {player.name:30s} (Rating: {sum(ratings.values())/len(ratings):.2f})")

    if len(lineup) != 11:
        print(f"  ⚠️  Only {len(lineup)} players assigned (need 11)")
        return False

    # DB에 평점 삽입
    from database.player_schema import PlayerRating
    inserted = 0

    for position, player_data in lineup.items():
        player_id = player_data['id']

        # 기존 평가 삭제
        session.query(PlayerRating).filter_by(
            player_id=player_id,
            user_id='default'
        ).delete()

        # 속성 평가 삽입
        for attr_name, rating_value in player_data['ratings'].items():
            rating = PlayerRating(
                player_id=player_id,
                user_id='default',
                attribute_name=attr_name,
                rating=rating_value
            )
            session.add(rating)
            inserted += 1

        # 코멘트 삽입
        comment_rating = PlayerRating(
            player_id=player_id,
            user_id='default',
            attribute_name='_comment',
            rating=0.0,
            notes=player_data['comment']
        )
        session.add(comment_rating)
        inserted += 1

        # 세부 포지션 삽입
        sub_pos_rating = PlayerRating(
            player_id=player_id,
            user_id='default',
            attribute_name='_subPosition',
            rating=0.0,
            notes=position
        )
        session.add(sub_pos_rating)
        inserted += 1

    session.commit()
    print(f"\n  ✅ Inserted {inserted} rating records")

    # JSON 파일 생성
    print(f"\n  Creating JSON files...")

    # 1. Formation
    formation_data = {
        'team_name': team_name,
        'formation': formation,
        'formation_data': {},
        'timestamp': datetime.now().isoformat()
    }
    formation_path = os.path.join(DATA_DIR, 'formations', f"{team_name}.json")
    with open(formation_path, 'w', encoding='utf-8') as f:
        json.dump(formation_data, f, indent=2, ensure_ascii=False)

    # 2. Lineup
    lineup_positions = {pos: data['id'] for pos, data in lineup.items()}
    lineup_data = {
        'team_name': team_name,
        'formation': formation,
        'lineup': lineup_positions,
        'timestamp': datetime.now().isoformat()
    }
    lineup_path = os.path.join(DATA_DIR, 'lineups', f"{team_name}.json")
    with open(lineup_path, 'w', encoding='utf-8') as f:
        json.dump(lineup_data, f, indent=2, ensure_ascii=False)

    # 3. Tactics
    tactics = generate_tactics(config['style'])
    tactics_data = {
        'team_name': team_name,
        'defensive': tactics['defensive'],
        'offensive': tactics['offensive'],
        'transition': tactics['transition'],
        'timestamp': datetime.now().isoformat()
    }
    tactics_path = os.path.join(DATA_DIR, 'tactics', f"{team_name}.json")
    with open(tactics_path, 'w', encoding='utf-8') as f:
        json.dump(tactics_data, f, indent=2, ensure_ascii=False)

    # 4. Team Strength
    team_ratings = generate_team_strength_ratings(config['level'])
    team_comment = generate_team_comment(team_name, config['style'])
    strength_data = {
        'team_name': team_name,
        'ratings': team_ratings,
        'comment': team_comment,
        'timestamp': datetime.now().isoformat()
    }
    strength_path = os.path.join(DATA_DIR, 'team_strength', f"{team_name}.json")
    with open(strength_path, 'w', encoding='utf-8') as f:
        json.dump(strength_data, f, indent=2, ensure_ascii=False)

    print(f"  ✅ All JSON files created")
    print(f"  ✅ {team_name} complete!")

    return True


def main():
    print("="*70)
    print("20개 EPL 팀 전체 데이터 자동 생성")
    print("="*70)

    session = None
    success_count = 0
    failed_teams = []

    try:
        session = get_player_session(DB_PATH)

        for team_name, config in TEAMS_CONFIG.items():
            try:
                if process_team(session, team_name, config):
                    success_count += 1
                else:
                    failed_teams.append(team_name)
            except Exception as e:
                print(f"\n  ❌ Error processing {team_name}: {str(e)}")
                failed_teams.append(team_name)
                session.rollback()

        print(f"\n{'='*70}")
        print(f"✅ Successfully processed: {success_count}/20 teams")
        if failed_teams:
            print(f"❌ Failed teams: {', '.join(failed_teams)}")
        print(f"{'='*70}\n")

    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        if session:
            session.rollback()
    finally:
        if session:
            session.close()


if __name__ == '__main__':
    main()
