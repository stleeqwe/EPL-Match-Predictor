"""
관리자 엔드포인트 - 데이터 업데이트
"""
import json
import os
from datetime import datetime
from flask import jsonify
import logging

logger = logging.getLogger(__name__)


def update_squad_data_endpoint(fetch_fantasy_data_func, cache):
    """
    Fantasy API에서 최신 선수 데이터를 가져와서 squad_data.py 업데이트
    """
    try:
        logger.info("🚀 Squad data update started")
        
        # Fantasy API에서 데이터 가져오기
        fantasy_data = fetch_fantasy_data_func()
        if not fantasy_data:
            return jsonify({
                'success': False,
                'error': 'Failed to fetch Fantasy API data'
            }), 500
        
        teams_dict = {team['id']: team['name'] for team in fantasy_data['teams']}
        
        # 선수 데이터 구조화
        squad_data = {}
        for team_name in teams_dict.values():
            squad_data[team_name] = []
        
        # 포지션 매핑
        position_map = ['GK', 'DF', 'MF', 'FW']
        
        for player in fantasy_data['elements']:
            team_name = teams_dict[player['team']]
            
            # 주전 판단
            starts = player.get('starts', 0)
            minutes = player.get('minutes', 0)
            is_starter = starts >= 4 or minutes >= 400
            
            player_data = {
                'id': player['id'],
                'name': f"{player['first_name']} {player['second_name']}",
                'position': position_map[player['element_type'] - 1],
                'number': player.get('squad_number', 0),
                'age': player.get('age', 0),
                'nationality': '',
                'is_starter': is_starter,
                'stats': {
                    'appearances': starts + player.get('substitute_appearances', 0),
                    'starts': starts,
                    'minutes': minutes,
                    'goals': player.get('goals_scored', 0),
                    'assists': player.get('assists', 0),
                    'clean_sheets': player.get('clean_sheets', 0),
                }
            }
            
            squad_data[team_name].append(player_data)
        
        # 팀별 정렬
        for team_name in squad_data:
            squad_data[team_name].sort(
                key=lambda p: (not p['is_starter'], p['number'] if p['number'] else 999)
            )
        
        # squad_data.py 파일 생성
        # __file__ 대신 현재 디렉토리 기준으로 경로 설정
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        output_path = os.path.join(backend_dir, 'data', 'squad_data.py')
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('"""\n')
            f.write('EPL 전체 팀 선수 명단\n')
            f.write(f'자동 생성됨: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
            f.write('데이터 소스: Fantasy Premier League API\n')
            f.write('"""\n\n')
            f.write(f'SQUAD_DATA = {json.dumps(squad_data, indent=4, ensure_ascii=False)}\n\n')
            f.write('def get_squad(team_name):\n')
            f.write('    """팀 이름으로 선수 명단 가져오기"""\n')
            f.write('    return SQUAD_DATA.get(team_name, [])\n\n')
            f.write('def get_all_teams():\n')
            f.write('    """모든 팀 이름 리스트"""\n')
            f.write('    return list(SQUAD_DATA.keys())\n')
        
        # 캐시 초기화
        cache.clear()
        
        # 통계 계산
        total_players = sum(len(players) for players in squad_data.values())
        total_starters = sum(
            sum(1 for p in players if p['is_starter'])
            for players in squad_data.values()
        )
        
        logger.info(f"✅ Squad data updated successfully")
        logger.info(f"   Teams: {len(squad_data)}")
        logger.info(f"   Total players: {total_players}")
        logger.info(f"   Total starters: {total_starters}")
        
        return jsonify({
            'success': True,
            'message': 'Squad data updated successfully',
            'stats': {
                'teams': len(squad_data),
                'total_players': total_players,
                'total_starters': total_starters,
                'updated_at': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error updating squad data: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
