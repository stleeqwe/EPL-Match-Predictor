"""
Flask API 서버 - EPL 팀 선수 분석 플랫폼
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_caching import Cache
import sys
import os
import logging
from datetime import datetime
import requests

# 부모 디렉토리를 path에 추가
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from data_collection import FBrefScraper
from data.squad_data import SQUAD_DATA
from database.player_schema import get_player_session, Player, PlayerRating, Team, PositionAttribute
import pandas as pd
import json

app = Flask(__name__)
CORS(app)  # React에서 접근 가능하도록

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


# ==================== Error Handlers ====================

class APIError(Exception):
    """Base API Error"""
    status_code = 500

    def __init__(self, message, status_code=None, payload=None):
        super().__init__()
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['error'] = {
            'code': self.__class__.__name__,
            'message': self.message,
            'status': self.status_code
        }
        return rv


class ValidationError(APIError):
    """Validation Error - 400"""
    status_code = 400


class NotFoundError(APIError):
    """Resource Not Found - 404"""
    status_code = 404


@app.errorhandler(APIError)
def handle_api_error(error):
    """Handle custom API errors"""
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.errorhandler(404)
def handle_404(error):
    """Handle 404 errors"""
    return jsonify({
        'error': {
            'code': 'NOT_FOUND',
            'message': 'The requested resource was not found',
            'status': 404
        }
    }), 404


@app.errorhandler(500)
def handle_500(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {str(error)}", exc_info=True)
    return jsonify({
        'error': {
            'code': 'INTERNAL_SERVER_ERROR',
            'message': 'An internal server error occurred',
            'status': 500
        }
    }), 500


@app.errorhandler(Exception)
def handle_exception(error):
    """Handle all uncaught exceptions"""
    logger.error(f"Unhandled exception: {str(error)}", exc_info=True)
    return jsonify({
        'error': {
            'code': 'UNHANDLED_EXCEPTION',
            'message': str(error),
            'status': 500
        }
    }), 500

# Flask-Caching 설정
cache = Cache(app, config={
    'CACHE_TYPE': 'simple',
    'CACHE_DEFAULT_TIMEOUT': 300
})

# FBref 스크래퍼 초기화
fbref_scraper = FBrefScraper()

logger.info("✅ EPL Player Analysis API Server initialized")


# ==================== Helper Functions ====================

@cache.memoize(timeout=3600)  # 1시간 캐싱
def fetch_fantasy_data():
    """
    Premier League Fantasy API에서 선수 데이터 가져오기
    """
    try:
        url = 'https://fantasy.premierleague.com/api/bootstrap-static/'
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        logger.info(f"✅ Fetched Fantasy API data: {len(data.get('elements', []))} players")
        return data
    except Exception as e:
        logger.error(f"❌ Error fetching Fantasy API data: {str(e)}")
        return None


# ==================== API Endpoints ====================

@app.route('/api/health', methods=['GET'])
def health_check():
    """서버 상태 확인"""
    return jsonify({
        'status': 'healthy',
        'service': 'EPL Player Analysis API',
        'version': '2.0.1'
    })


# ============================================================================
# 데이터 업데이트 API
# ============================================================================

@app.route('/api/admin/update-squad-data', methods=['POST'])
def update_squad_data():
    """
    Fantasy API에서 최신 선수 데이터를 가져와서 squad_data.py 업데이트
    
    사용법:
        curl -X POST http://localhost:5001/api/admin/update-squad-data
    """
    try:
        logger.info("🚀 Squad data update started")
        
        # Fantasy API에서 데이터 가져오기
        fantasy_data = fetch_fantasy_data()
        if not fantasy_data:
            raise APIError("Failed to fetch Fantasy API data", status_code=500)
        
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
        raise APIError(f"Failed to update squad data: {str(e)}", status_code=500)


if __name__ == '__main__':
    logger.info("\n" + "="*60)
    logger.info("🚀 Starting EPL Player Analysis API Server")
    logger.info("="*60)
    logger.info(f"   Port: 5001")
    logger.info(f"   Debug: True")
    logger.info(f"   Update endpoint: POST /api/admin/update-squad-data")
    logger.info("="*60 + "\n")
    app.run(host='0.0.0.0', port=5001, debug=True)
