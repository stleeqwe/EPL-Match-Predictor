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
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# 부모 디렉토리를 path에 추가
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from data_collection import FBrefScraper
from data.squad_data import SQUAD_DATA
from database.player_schema import get_player_session, Player, PlayerRating, Team, PositionAttribute
import pandas as pd
import json

# Odds and Value Betting modules
from odds_collection import OddsAPIClient, OddsAggregator
from value_betting import ValueDetector

# React 빌드 폴더 경로
REACT_BUILD_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'frontend', 'epl-predictor', 'build')

app = Flask(__name__, static_folder=REACT_BUILD_PATH, static_url_path='')
CORS(app)  # React에서 접근 가능하도록

# 데이터베이스 경로
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'epl_data.db')

# ==================== Squad Number Mapping ====================

# 등번호 매핑 데이터 로드
SQUAD_NUMBERS = None

def load_squad_numbers():
    """등번호 매핑 JSON 파일 로드"""
    global SQUAD_NUMBERS
    if SQUAD_NUMBERS is None:
        squad_file_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'epl_squad_numbers.json')
        try:
            with open(squad_file_path, 'r', encoding='utf-8') as f:
                SQUAD_NUMBERS = json.load(f)
            logger.info(f"Loaded squad numbers for {len(SQUAD_NUMBERS)} teams")
        except Exception as e:
            logger.error(f"Failed to load squad numbers: {e}")
            SQUAD_NUMBERS = {}
    return SQUAD_NUMBERS

def get_player_shirt_number(player_name, team_name):
    """
    선수 이름과 팀 이름으로 등번호 조회

    Args:
        player_name: 선수 이름 (예: "Bruno Fernandes", "Mainoo")
        team_name: 팀 이름 (예: "Man Utd", "Manchester United")

    Returns:
        등번호 (int) 또는 None
    """
    squad_numbers = load_squad_numbers()

    # 팀 이름 정규화
    team_aliases = {
        'Manchester United': 'Man Utd',
        'Manchester City': 'Man City',
        'Tottenham Hotspur': 'Spurs',
        'Nottingham Forest': "Nott'm Forest"
    }
    normalized_team = team_aliases.get(team_name, team_name)

    if normalized_team not in squad_numbers:
        return None

    # 선수 이름 매칭 (부분 문자열 매칭 지원)
    team_squad = squad_numbers[normalized_team]
    player_name_lower = player_name.lower()

    for player in team_squad:
        if player_name_lower in player['name'].lower() or player['name'].lower() in player_name_lower:
            return player['number']

    return None

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Odds API 모듈 초기화
odds_client = OddsAPIClient()
odds_aggregator = OddsAggregator()
value_detector = ValueDetector(min_edge=0.02, min_confidence=0.65)

# Match Predictor 초기화
from value_betting.match_predictor import MatchPredictor
match_predictor = MatchPredictor()


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


def normalize_name(name):
    """
    선수 이름 정규화 (매칭을 위해)
    """
    # 특수 문자 제거, 소문자 변환
    import re
    normalized = re.sub(r'[^a-zA-Z\s]', '', name.lower())
    normalized = ' '.join(normalized.split())  # 공백 정리
    return normalized


def get_team_matches_played(fantasy_data):
    """
    현재까지 진행된 경기 수 확인
    """
    try:
        events = fantasy_data.get('events', [])
        # 완료된 gameweek 수 계산
        completed_gameweeks = sum(1 for event in events if event.get('finished', False))
        return completed_gameweeks if completed_gameweeks > 0 else 1  # 최소 1경기
    except Exception as e:
        logger.error(f"Error getting matches played: {str(e)}")
        return 5  # 기본값: 5경기


def calculate_age_from_birthdate(birth_date_str):
    """생년월일로부터 나이 계산"""
    if not birth_date_str:
        return 0
    try:
        birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d')
        today = datetime.now()
        age = today.year - birth_date.year
        # 생일이 지나지 않았으면 1살 빼기
        if (today.month, today.day) < (birth_date.month, birth_date.day):
            age -= 1
        return age
    except:
        return 0

def get_player_stats_from_fantasy(player_name, team_name, fantasy_data):
    """
    Fantasy API에서 선수의 통계 정보 가져오기

    Returns:
        dict: {
            'age': int,
            'goals': int,
            'assists': int,
            'minutes': int,
            'starts': int,
            'is_starter': bool
        } or None
    """
    if not fantasy_data:
        return None

    try:
        elements = fantasy_data.get('elements', [])
        teams = fantasy_data.get('teams', [])

        # 팀 이름 매핑
        team_name_mapping = {
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

        reverse_mapping = {v: k for k, v in team_name_mapping.items()}
        fantasy_team_name = reverse_mapping.get(team_name, team_name)

        # 팀 ID 찾기
        team_id = None
        for team in teams:
            if team['name'] == fantasy_team_name:
                team_id = team['id']
                break

        if not team_id:
            return None

        # 전체 경기 수
        total_matches = get_team_matches_played(fantasy_data)
        max_possible_minutes = total_matches * 90

        # 선수 이름 정규화
        normalized_player_name = normalize_name(player_name)

        # 해당 팀 선수 찾기
        for player in elements:
            if player['team'] != team_id:
                continue

            fantasy_name = f"{player['first_name']} {player['second_name']}"
            normalized_fantasy_name = normalize_name(fantasy_name)

            # 이름 매칭
            if normalized_player_name in normalized_fantasy_name or normalized_fantasy_name in normalized_player_name:
                starts = player.get('starts', 0)
                minutes = player.get('minutes', 0)

                # 비율 계산
                start_ratio = starts / total_matches if total_matches > 0 else 0
                minutes_ratio = minutes / max_possible_minutes if max_possible_minutes > 0 else 0

                # 주전 여부
                is_regular_starter = start_ratio >= 0.5 and minutes_ratio >= 0.4

                # 생년월일에서 나이 계산
                age = calculate_age_from_birthdate(player.get('birth_date'))

                return {
                    'age': age,
                    'goals': player.get('goals_scored', 0),
                    'assists': player.get('assists', 0),
                    'minutes': minutes,
                    'starts': starts,
                    'appearances': starts + player.get('substitute_appearances', 0),  # 선발 + 교체 출전
                    'is_starter': is_regular_starter,
                    'matched_name': fantasy_name
                }

        return None
    except Exception as e:
        logger.error(f"Error getting player stats: {str(e)}")
        return None


def map_fpl_player_to_squad(fpl_player, team_name):
    """
    FPL 선수를 SQUAD_DATA 선수와 매핑
    데이터 정합성을 위해 SQUAD_DATA의 ID와 이름을 사용
    """
    if team_name not in SQUAD_DATA:
        return None

    squad_players = SQUAD_DATA[team_name]
    fpl_id = fpl_player['id']
    fpl_name = f"{fpl_player['first_name']} {fpl_player['second_name']}"
    fpl_web_name = fpl_player.get('web_name', '')

    # 1. ID 매칭 (가장 정확)
    for sp in squad_players:
        if sp['id'] == fpl_id:
            logger.debug(f"✅ ID 매칭: {sp['name']} (ID: {sp['id']})")
            return sp

    # 2. 정확한 이름 매칭
    for sp in squad_players:
        if sp['name'] == fpl_name or sp['name'] == fpl_web_name:
            logger.debug(f"✅ 이름 매칭: {sp['name']} (ID: {sp['id']})")
            return sp

    # 3. 부분 이름 매칭 (성이 같거나 포함)
    fpl_last_name = fpl_player['second_name'].lower()
    for sp in squad_players:
        sp_name_lower = sp['name'].lower()
        if fpl_last_name in sp_name_lower or fpl_web_name.lower() in sp_name_lower:
            logger.debug(f"✅ 부분 이름 매칭: {sp['name']} (ID: {sp['id']}) <- FPL: {fpl_name}")
            return sp

    # 매칭 실패
    logger.warning(f"❌ 매칭 실패: FPL {fpl_name} (ID: {fpl_id}) in {team_name}")
    return None


def get_player_role_by_ict(team_name, fantasy_data):
    """
    팀 내 ICT Index 기반으로 선수 역할 결정

    역할 구분:
    - starter: 팀 내 ICT Index 상위 15명 (주전)
    - substitute: 팀 내 ICT Index 16-25위 (후보)
    - other: 나머지 (기타)

    Returns:
        dict: {squad_data_player_id: {'role': str, 'ict_index': float, 'rank': int}}
        ⚠️ SQUAD_DATA 선수 ID를 키로 사용 (FPL ID가 아님!)
    """
    if not fantasy_data:
        return {}

    try:
        elements = fantasy_data.get('elements', [])
        teams = fantasy_data.get('teams', [])

        # 팀 이름 매핑
        team_name_mapping = {
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

        # 역매핑
        reverse_mapping = {v: k for k, v in team_name_mapping.items()}
        fantasy_team_name = reverse_mapping.get(team_name, team_name)

        # 팀 ID 찾기
        team_id = None
        for team in teams:
            if team['name'] == fantasy_team_name:
                team_id = team['id']
                break

        if not team_id:
            logger.warning(f"⚠️ Team not found in Fantasy API: {team_name}")
            return {}

        # 해당 팀 선수들 필터링 및 ICT Index 기준 정렬
        team_players = []
        for player in elements:
            if player['team'] == team_id:
                ict_index = float(player.get('ict_index', '0.0'))

                # FPL 선수를 SQUAD_DATA 선수와 매핑
                squad_player = map_fpl_player_to_squad(player, team_name)

                if squad_player:
                    team_players.append({
                        'squad_id': squad_player['id'],  # SQUAD_DATA ID 사용
                        'fpl_id': player['id'],
                        'name': squad_player['name'],  # SQUAD_DATA 이름 사용
                        'ict_index': ict_index
                    })

        # ICT Index 내림차순 정렬
        team_players.sort(key=lambda x: x['ict_index'], reverse=True)

        # 역할 할당 (SQUAD_DATA ID를 키로 사용)
        player_roles = {}
        for rank, player in enumerate(team_players, start=1):
            if rank <= 15:
                role = 'starter'
            elif rank <= 25:
                role = 'substitute'
            else:
                role = 'other'

            player_roles[player['squad_id']] = {  # SQUAD_DATA ID를 키로 사용
                'role': role,
                'ict_index': player['ict_index'],
                'rank': rank
            }

        logger.info(
            f"📊 {team_name} ICT Index 역할 할당: "
            f"주전 {sum(1 for p in player_roles.values() if p['role'] == 'starter')}명, "
            f"후보 {sum(1 for p in player_roles.values() if p['role'] == 'substitute')}명, "
            f"기타 {sum(1 for p in player_roles.values() if p['role'] == 'other')}명 "
            f"(매핑된 선수 {len(team_players)}명)"
        )

        return player_roles

    except Exception as e:
        logger.error(f"Error calculating player roles for {team_name}: {str(e)}")
        return {}


def is_starter(player_name, team_name, fantasy_data):
    """
    ICT Index 기반 주전 여부 판단 (하위 호환성 유지)

    주전 기준:
    - 팀 내 ICT Index 상위 15명
    """
    player_roles = get_player_role_by_ict(team_name, fantasy_data)

    if not player_roles:
        return False

    # 선수 매칭
    elements = fantasy_data.get('elements', [])
    normalized_player_name = normalize_name(player_name)

    for player in elements:
        fantasy_name = f"{player['first_name']} {player['second_name']}"
        normalized_fantasy_name = normalize_name(fantasy_name)

        if normalized_player_name in normalized_fantasy_name or normalized_fantasy_name in normalized_player_name:
            player_id = player['id']
            role_info = player_roles.get(player_id, {})
            is_regular_starter = role_info.get('role') == 'starter'

            logger.info(
                f"✅ ICT Matched: {player_name} → {fantasy_name} | "
                f"ICT Index: {role_info.get('ict_index', 0):.1f} | "
                f"Rank: {role_info.get('rank', 'N/A')} | "
                f"Role: {role_info.get('role', 'unknown')} | "
                f"Starter: {is_regular_starter}"
            )

            return is_regular_starter

    logger.warning(f"⚠️ Player not matched in Fantasy API: {player_name} (team: {team_name})")
    return False


# ==================== API Endpoints ====================

@app.route('/api', methods=['GET'])
def api_root():
    """API 루트 - 서비스 정보 및 사용 가능한 엔드포인트 안내"""
    return jsonify({
        'service': 'EPL Player Analysis API',
        'version': '2.0.0',
        'status': 'running',
        'description': 'Premier League player analysis and match prediction system',
        'endpoints': {
            'health': '/api/health',
            'teams': '/api/teams',
            'squad': '/api/squad/<team_name>',
            'player': '/api/player/<player_id>',
            'positions': '/api/positions',
            'ratings': {
                'get': '/api/ratings/<player_id>',
                'save': '/api/ratings (POST)',
                'update': '/api/ratings/<player_id>/<attribute_name> (PUT)'
            },
            'epl_data': {
                'standings': '/api/epl/standings',
                'fixtures': '/api/epl/fixtures',
                'leaderboard': '/api/epl/leaderboard'
            },
            'predictions': {
                'match_predictions': '/api/match-predictions',
                'live_odds': '/api/odds/live',
                'value_bets': '/api/value-bets',
                'dashboard': '/api/dashboard'
            }
        },
        'v3_features': v3_routes_registered if v3_routes_registered else 'Not activated',
        'documentation': 'Visit /api/health for server health check'
    })


@app.route('/api/health', methods=['GET'])
def health_check():
    """서버 상태 확인"""
    return jsonify({
        'status': 'healthy',
        'service': 'EPL Player Analysis API',
        'version': '2.0.0'
    })


@app.route('/api/teams', methods=['GET'])
@cache.cached(timeout=3600)
def get_teams():
    """
    EPL 전체 팀 목록 가져오기 (엠블럼 포함)
    """
    try:
        teams = list(SQUAD_DATA.keys())
        logger.info(f"🔍 [DEBUG] SQUAD_DATA keys: {teams}")
        logger.info(f"🔍 [DEBUG] Number of teams: {len(teams)}")

        # Fantasy API에서 팀 데이터 가져오기
        fantasy_data = fetch_fantasy_data()
        team_emblems = {}

        if fantasy_data:
            fantasy_teams = fantasy_data.get('teams', [])
            # 팀 이름 매핑
            team_mapping = {
                'Man Utd': 'Manchester Utd',
                'Man City': 'Manchester City',
                'Spurs': 'Tottenham',
                "Nott'm Forest": 'Nottingham Forest',
                'Newcastle': 'Newcastle Utd',
                'Wolves': 'Wolverhampton',
                'Brighton': 'Brighton and Hove Albion',
                'West Ham': 'West Ham United'
            }

            for fantasy_team in fantasy_teams:
                team_name = fantasy_team.get('name', '')
                team_code = fantasy_team.get('code', '')

                # 매핑된 팀 이름 찾기
                for squad_name in teams:
                    mapped_name = team_mapping.get(squad_name, squad_name)
                    if team_name == mapped_name or team_name == squad_name:
                        # Premier League 공식 엠블럼 URL
                        emblem_url = f"https://resources.premierleague.com/premierleague/badges/50/t{team_code}.png"
                        team_emblems[squad_name] = emblem_url
                        break

        sorted_teams = sorted(teams)
        teams_with_emblems = [
            {
                'name': team,
                'emblem': team_emblems.get(team, '')
            }
            for team in sorted_teams
        ]

        response_data = {'teams': teams_with_emblems}

        logger.info(f"🔍 [DEBUG] Response teams count: {len(response_data['teams'])}")

        return jsonify(response_data)
    except Exception as e:
        logger.error(f"Error fetching teams: {str(e)}", exc_info=True)
        raise APIError(f"Failed to fetch teams: {str(e)}", status_code=500)


@app.route('/api/squad/<team_name>', methods=['GET'])
@cache.cached(timeout=1800, query_string=True)
def get_squad(team_name):
    """
    특정 팀의 선수 명단 가져오기 (ICT Index 기반 주전/후보/기타 정보 포함)
    """
    try:
        if team_name not in SQUAD_DATA:
            raise NotFoundError(f"Team '{team_name}' not found")

        players = SQUAD_DATA[team_name]
        logger.info(f"🔍 Fetching squad for team: {team_name}")
        logger.info(f"📋 Retrieved {len(players)} players")

        # FPL API에서 ICT Index 기반 역할 정보 가져오기
        fantasy_data = fetch_fantasy_data()
        player_roles = get_player_role_by_ict(team_name, fantasy_data) if fantasy_data else {}

        # squad_data.py의 데이터를 그대로 사용 (Premier League 공식 API 기반)
        squad_players = []
        for player in players:
            player_copy = player.copy()

            # stats 데이터가 없으면 기본값 설정
            if 'stats' not in player_copy:
                player_copy['stats'] = {
                    'appearances': 0,
                    'starts': 0,
                    'minutes': 0,
                    'goals': 0,
                    'assists': 0,
                    'clean_sheets': 0
                }

            # 편의를 위해 루트 레벨에도 통계 정보 추가
            player_copy['goals'] = player_copy['stats'].get('goals', 0)
            player_copy['assists'] = player_copy['stats'].get('assists', 0)
            player_copy['minutes'] = player_copy['stats'].get('minutes', 0)
            player_copy['starts'] = player_copy['stats'].get('starts', 0)
            player_copy['appearances'] = player_copy['stats'].get('appearances', 0)

            # ICT Index 기반 역할 정보 추가
            player_id = player.get('id')
            role_info = player_roles.get(player_id, {})
            player_copy['role'] = role_info.get('role', 'other')  # starter/substitute/other
            player_copy['ict_index'] = role_info.get('ict_index', 0.0)
            player_copy['ict_rank'] = role_info.get('rank', 999)

            # is_starter 필드도 업데이트 (하위 호환성)
            player_copy['is_starter'] = (player_copy['role'] == 'starter')

            squad_players.append(player_copy)

        # ICT Index 순위로 정렬 (주전 → 후보 → 기타 순)
        role_order = {'starter': 0, 'substitute': 1, 'other': 2}
        squad_players.sort(key=lambda p: (
            role_order.get(p.get('role', 'other'), 3),
            p.get('ict_rank', 999)
        ))

        response_data = {'squad': squad_players}
        starters_count = sum(1 for p in squad_players if p.get('role') == 'starter')
        substitute_count = sum(1 for p in squad_players if p.get('role') == 'substitute')
        other_count = sum(1 for p in squad_players if p.get('role') == 'other')
        logger.info(
            f"📊 {team_name} Squad: "
            f"주전 {starters_count}명, 후보 {substitute_count}명, 기타 {other_count}명 "
            f"(총 {len(squad_players)}명)"
        )

        return jsonify(response_data)
    except NotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error fetching squad: {str(e)}", exc_info=True)
        raise APIError(f"Failed to fetch squad: {str(e)}", status_code=500)


@app.route('/api/player/<int:player_id>', methods=['GET'])
def get_player(player_id):
    """
    특정 선수 정보 가져오기
    """
    try:
        # 모든 팀에서 선수 찾기
        for team_name, players in SQUAD_DATA.items():
            for player in players:
                if player.get('id') == player_id:
                    player_with_team = {**player, 'team': team_name}
                    return jsonify(player_with_team)

        raise NotFoundError(f"Player with ID {player_id} not found")
    except NotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error fetching player: {str(e)}", exc_info=True)
        raise APIError(f"Failed to fetch player: {str(e)}", status_code=500)


@app.route('/api/fixtures', methods=['GET'])
@cache.cached(timeout=300, query_string=True)
def get_fixtures():
    """
    경기 일정 가져오기 (선택적 - 향후 제거 가능)
    """
    try:
        import numpy as np
        fixtures = fbref_scraper.get_epl_fixtures()

        # NaN을 None으로 변환
        fixtures_dict = fixtures.to_dict(orient='records')
        for fixture in fixtures_dict:
            for key, value in fixture.items():
                if isinstance(value, float) and np.isnan(value):
                    fixture[key] = None

        return jsonify(fixtures_dict)
    except Exception as e:
        logger.error(f"Error fetching fixtures: {str(e)}", exc_info=True)
        raise APIError(f"Failed to fetch fixtures: {str(e)}", status_code=500)


@app.route('/api/player-photo/<photo_code>', methods=['GET'])
@cache.cached(timeout=86400, query_string=True)  # 24시간 캐시
def get_player_photo(photo_code):
    """
    선수 사진 프록시 (CORS 우회)
    Premier League CDN에서 이미지를 가져와서 반환
    """
    try:
        from flask import send_file, Response
        import io

        # 사이즈 파라미터 (기본값: 250x250)
        size = request.args.get('size', '250x250')

        # Premier League CDN URL
        photo_url = f'https://resources.premierleague.com/premierleague/photos/players/{size}/p{photo_code}.png'

        # 이미지 가져오기
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Referer': 'https://www.premierleague.com/'
        }

        response = requests.get(photo_url, headers=headers, timeout=10)
        response.raise_for_status()

        # 이미지 반환
        return Response(
            response.content,
            mimetype='image/png',
            headers={
                'Cache-Control': 'public, max-age=86400',  # 24시간 캐시
                'Access-Control-Allow-Origin': '*'  # CORS 허용
            }
        )

    except requests.RequestException as e:
        logger.error(f"Failed to fetch player photo {photo_code}: {str(e)}")
        # 404 이미지 또는 에러 반환
        return jsonify({'error': 'Photo not found'}), 404
    except Exception as e:
        logger.error(f"Error fetching player photo: {str(e)}", exc_info=True)
        raise APIError(f"Failed to fetch player photo: {str(e)}", status_code=500)


@app.route('/api/positions', methods=['GET'])
def get_positions():
    """
    포지션 목록 및 포지션별 능력치 카테고리 (가중치 포함)
    """
    positions_config = {
        'GK': {
            'name': '골키퍼',
            'name_en': 'Goalkeeper',
            'attributes': [
                {'key': 'reflexes', 'label': '반응속도', 'weight': 0.18},
                {'key': 'positioning', 'label': '포지셔닝', 'weight': 0.18},
                {'key': 'handling', 'label': '핸들링', 'weight': 0.16},
                {'key': 'one_on_one', 'label': '1:1 대응', 'weight': 0.15},
                {'key': 'aerial_control', 'label': '공중볼 지배력', 'weight': 0.13},
                {'key': 'buildup', 'label': '빌드업 능력', 'weight': 0.10},
                {'key': 'long_kick', 'label': '롱볼 킥력', 'weight': 0.06},
                {'key': 'leadership_communication', 'label': '리더십&의사소통', 'weight': 0.04}
            ]
        },
        'CB': {
            'name': '센터백',
            'name_en': 'Center Back',
            'attributes': [
                {'key': 'positioning_sense', 'label': '포지셔닝 센스', 'weight': 0.12},
                {'key': 'composure', 'label': '침착성', 'weight': 0.11},
                {'key': 'interception', 'label': '인터셉트', 'weight': 0.10},
                {'key': 'aerial_duel', 'label': '공중볼 경합', 'weight': 0.09},
                {'key': 'marking', 'label': '마킹', 'weight': 0.09},
                {'key': 'tackling', 'label': '태클', 'weight': 0.08},
                {'key': 'short_pass', 'label': '패스(숏)', 'weight': 0.08},
                {'key': 'speed', 'label': '스피드', 'weight': 0.07},
                {'key': 'press_resistance', 'label': '압박 상황 판단력', 'weight': 0.07},
                {'key': 'long_pass', 'label': '패스(롱)', 'weight': 0.05},
                {'key': 'progressive_pass_vision', 'label': '전진 패스 시야', 'weight': 0.05},
                {'key': 'physicality', 'label': '피지컬', 'weight': 0.04},
                {'key': 'jumping', 'label': '점프력', 'weight': 0.03},
                {'key': 'leadership', 'label': '리더십', 'weight': 0.02}
            ]
        },
        'FB': {
            'name': '풀백',
            'name_en': 'Fullback/Wingback',
            'attributes': [
                {'key': 'stamina', 'label': '지구력', 'weight': 0.18},
                {'key': 'speed', 'label': '스피드', 'weight': 0.16},
                {'key': 'one_on_one_defense', 'label': '1:1 수비', 'weight': 0.14},
                {'key': 'overlapping', 'label': '오버래핑', 'weight': 0.13},
                {'key': 'crossing_accuracy', 'label': '크로스 정확도와 다양성', 'weight': 0.12},
                {'key': 'covering', 'label': '백업 커버링', 'weight': 0.10},
                {'key': 'agility', 'label': '민첩성', 'weight': 0.08},
                {'key': 'cross_blocking', 'label': '크로스 차단', 'weight': 0.06},
                {'key': 'long_shot', 'label': '중거리 슈팅', 'weight': 0.03}
            ]
        },
        'DM': {
            'name': '수비형 미드필더',
            'name_en': 'Defensive Midfielder',
            'attributes': [
                {'key': 'positioning', 'label': '포지셔닝', 'weight': 0.12},
                {'key': 'ball_winning', 'label': '볼 차단 및 회수', 'weight': 0.11},
                {'key': 'pass_accuracy', 'label': '패스 정확도', 'weight': 0.10},
                {'key': 'composure', 'label': '침착성', 'weight': 0.10},
                {'key': 'press_resistance', 'label': '압박 해소 능력', 'weight': 0.09},
                {'key': 'defensive_positioning', 'label': '백라인 보호 포지셔닝', 'weight': 0.09},
                {'key': 'pressing', 'label': '공간 압박', 'weight': 0.08},
                {'key': 'progressive_play', 'label': '공격전개능력', 'weight': 0.08},
                {'key': 'tempo_control', 'label': '템포 조절', 'weight': 0.07},
                {'key': 'stamina', 'label': '지구력', 'weight': 0.06},
                {'key': 'physicality', 'label': '피지컬', 'weight': 0.04},
                {'key': 'mobility', 'label': '기동력', 'weight': 0.04},
                {'key': 'leadership', 'label': '리더십', 'weight': 0.02}
            ]
        },
        'CM': {
            'name': '중앙 미드필더',
            'name_en': 'Central Midfielder',
            'attributes': [
                {'key': 'stamina', 'label': '지구력', 'weight': 0.11},
                {'key': 'game_control', 'label': '경기 지배력', 'weight': 0.11},
                {'key': 'pass_accuracy', 'label': '패스 정확도', 'weight': 0.10},
                {'key': 'transition', 'label': '전환 플레이', 'weight': 0.09},
                {'key': 'vision', 'label': '시야', 'weight': 0.09},
                {'key': 'dribbling_press_resistance', 'label': '드리블 및 탈압박', 'weight': 0.08},
                {'key': 'space_creation', 'label': '공간 창출/침투', 'weight': 0.08},
                {'key': 'defensive_contribution', 'label': '수비 가담', 'weight': 0.08},
                {'key': 'ball_retention', 'label': '볼 키핑', 'weight': 0.07},
                {'key': 'long_shot', 'label': '중거리 슈팅', 'weight': 0.06},
                {'key': 'acceleration', 'label': '가속력', 'weight': 0.05},
                {'key': 'agility', 'label': '민첩성', 'weight': 0.04},
                {'key': 'physicality', 'label': '피지컬', 'weight': 0.04}
            ]
        },
        'CAM': {
            'name': '공격형 미드필더',
            'name_en': 'Attacking Midfielder',
            'attributes': [
                {'key': 'creativity', 'label': '창의성', 'weight': 0.14},
                {'key': 'dribbling', 'label': '드리블 돌파', 'weight': 0.12},
                {'key': 'decision_making', 'label': '결정적 순간 판단력', 'weight': 0.11},
                {'key': 'penetration', 'label': '공간 침투', 'weight': 0.10},
                {'key': 'shooting', 'label': '슈팅', 'weight': 0.09},
                {'key': 'finishing_accuracy', 'label': '마무리 정확도', 'weight': 0.09},
                {'key': 'one_touch_pass', 'label': '원터치 패스', 'weight': 0.08},
                {'key': 'pass_and_move', 'label': '패스 & 무브', 'weight': 0.07},
                {'key': 'acceleration', 'label': '가속력', 'weight': 0.07},
                {'key': 'agility', 'label': '민첩성', 'weight': 0.06},
                {'key': 'set_piece', 'label': '세트피스 킥', 'weight': 0.04},
                {'key': 'balance', 'label': '밸런스', 'weight': 0.03}
            ]
        },
        'WG': {
            'name': '윙어',
            'name_en': 'Winger',
            'attributes': [
                {'key': 'speed_dribbling', 'label': '스피드 드리블', 'weight': 0.12},
                {'key': 'one_on_one_beating', 'label': '1:1 제치기', 'weight': 0.11},
                {'key': 'speed', 'label': '스피드', 'weight': 0.11},
                {'key': 'acceleration', 'label': '가속력', 'weight': 0.10},
                {'key': 'crossing_timing', 'label': '크로스 정확도와 타이밍', 'weight': 0.10},
                {'key': 'shooting_accuracy', 'label': '슈팅 정확도', 'weight': 0.09},
                {'key': 'agility', 'label': '민첩성', 'weight': 0.08},
                {'key': 'feinting', 'label': '페인팅/방향 전환', 'weight': 0.07},
                {'key': 'cutting_in', 'label': '컷인 무브', 'weight': 0.07},
                {'key': 'creativity', 'label': '창의성', 'weight': 0.06},
                {'key': 'cutback_pass', 'label': '컷백 패스', 'weight': 0.04},
                {'key': 'finishing_composure', 'label': '마무리 침착성', 'weight': 0.03},
                {'key': 'link_up_play', 'label': '연계 플레이', 'weight': 0.02}
            ]
        },
        'ST': {
            'name': '스트라이커',
            'name_en': 'Striker',
            'attributes': [
                {'key': 'finishing', 'label': '골 결정력', 'weight': 0.15},
                {'key': 'shot_power', 'label': '슈팅 정확도와 파워', 'weight': 0.14},
                {'key': 'composure', 'label': '침착성', 'weight': 0.13},
                {'key': 'penetration', 'label': '공간 침투', 'weight': 0.12},
                {'key': 'hold_up_play', 'label': '홀딩 및 연결', 'weight': 0.10},
                {'key': 'heading', 'label': '헤딩 득점력', 'weight': 0.09},
                {'key': 'acceleration', 'label': '가속력', 'weight': 0.09},
                {'key': 'physicality', 'label': '피지컬', 'weight': 0.07},
                {'key': 'jumping', 'label': '점프력', 'weight': 0.06},
                {'key': 'balance', 'label': '밸런스', 'weight': 0.05}
            ]
        }
    }

    # 포지션 매핑 정보 추가
    position_mapping = {
        'GK': ['GK'],
        'DF': ['CB', 'FB'],
        'MF': ['DM', 'CM', 'CAM'],
        'FW': ['WG', 'ST']
    }

    return jsonify({
        'positions': positions_config,
        'mapping': position_mapping
    })


@app.route('/api/rating-scale', methods=['GET'])
def get_rating_scale():
    """
    능력치 평가 척도 정보
    """
    rating_scale = {
        'min': 0.0,
        'max': 5.0,
        'step': 0.25,
        'labels': {
            '5.0': '월드클래스 (세계 최정상)',
            '4.0-4.75': '리그 최상위권',
            '3.0-3.75': '리그 상위권',
            '2.0-2.75': '리그 평균',
            '1.0-1.75': '리그 평균 이하',
            '0.0-0.75': '보완 필요'
        }
    }

    return jsonify(rating_scale)


# ==================== Team Overall Score API ====================

# 종합 점수 저장 경로
OVERALL_SCORES_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'overall_scores')

def ensure_overall_scores_dir():
    """종합 점수 저장 디렉토리 생성"""
    os.makedirs(OVERALL_SCORES_DIR, exist_ok=True)

@app.route('/api/teams/<team_name>/overall_score', methods=['POST'])
def save_team_overall_score(team_name):
    """
    팀 종합 점수 저장

    Body: {
        "overallScore": 85.5,
        "playerScore": 90.0,
        "strengthScore": 80.0,
        "playerWeight": 60,
        "strengthWeight": 40
    }
    """
    try:
        data = request.json or {}

        # 필수 필드 검증
        required_fields = ['overallScore', 'playerScore', 'strengthScore', 'playerWeight', 'strengthWeight']
        for field in required_fields:
            if field not in data:
                raise ValidationError(f"Missing required field: {field}")

        # 데이터 검증
        if not (0 <= data['overallScore'] <= 100):
            raise ValidationError("overallScore must be between 0 and 100")
        if not (0 <= data['playerScore'] <= 100):
            raise ValidationError("playerScore must be between 0 and 100")
        if not (0 <= data['strengthScore'] <= 100):
            raise ValidationError("strengthScore must be between 0 and 100")
        if not (0 <= data['playerWeight'] <= 100):
            raise ValidationError("playerWeight must be between 0 and 100")
        if not (0 <= data['strengthWeight'] <= 100):
            raise ValidationError("strengthWeight must be between 0 and 100")

        # 가중치 합계 검증
        if data['playerWeight'] + data['strengthWeight'] != 100:
            raise ValidationError("playerWeight + strengthWeight must equal 100")

        # 저장할 데이터
        score_data = {
            'team_name': team_name,
            'overallScore': data['overallScore'],
            'playerScore': data['playerScore'],
            'strengthScore': data['strengthScore'],
            'playerWeight': data['playerWeight'],
            'strengthWeight': data['strengthWeight'],
            'timestamp': datetime.now().isoformat()
        }

        # JSON 파일로 저장
        ensure_overall_scores_dir()
        file_path = os.path.join(OVERALL_SCORES_DIR, f"{team_name}.json")

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(score_data, f, indent=2, ensure_ascii=False)

        logger.info(f"✅ Saved overall score for {team_name}: {data['overallScore']:.1f}/100")

        return jsonify({
            'success': True,
            'team': team_name,
            'data': score_data
        })

    except (ValidationError, NotFoundError):
        raise
    except Exception as e:
        logger.error(f"Error saving overall score: {str(e)}", exc_info=True)
        raise APIError(f"Failed to save overall score: {str(e)}", status_code=500)


@app.route('/api/teams/<team_name>/overall_score', methods=['GET'])
def get_team_overall_score(team_name):
    """
    팀 종합 점수 조회

    Returns: {
        "team_name": "Liverpool",
        "overallScore": 85.5,
        "playerScore": 90.0,
        "strengthScore": 80.0,
        "playerWeight": 60,
        "strengthWeight": 40,
        "timestamp": "2025-01-10T12:00:00"
    }
    """
    try:
        file_path = os.path.join(OVERALL_SCORES_DIR, f"{team_name}.json")

        if not os.path.exists(file_path):
            return jsonify({
                'success': False,
                'message': f"No overall score found for {team_name}"
            }), 404

        with open(file_path, 'r', encoding='utf-8') as f:
            score_data = json.load(f)

        return jsonify({
            'success': True,
            'data': score_data
        })

    except Exception as e:
        logger.error(f"Error fetching overall score: {str(e)}", exc_info=True)
        raise APIError(f"Failed to fetch overall score: {str(e)}", status_code=500)


@app.route('/api/teams/overall_scores', methods=['GET'])
def get_all_overall_scores():
    """
    모든 팀의 종합 점수 조회

    Returns: {
        "Liverpool": {...},
        "Man City": {...},
        ...
    }
    """
    try:
        ensure_overall_scores_dir()
        all_scores = {}

        for filename in os.listdir(OVERALL_SCORES_DIR):
            if filename.endswith('.json'):
                team_name = filename[:-5]  # .json 제거
                file_path = os.path.join(OVERALL_SCORES_DIR, filename)

                with open(file_path, 'r', encoding='utf-8') as f:
                    score_data = json.load(f)
                    all_scores[team_name] = score_data

        return jsonify({
            'success': True,
            'count': len(all_scores),
            'scores': all_scores
        })

    except Exception as e:
        logger.error(f"Error fetching all overall scores: {str(e)}", exc_info=True)
        raise APIError(f"Failed to fetch overall scores: {str(e)}", status_code=500)


@app.route('/api/ratings/<int:player_id>', methods=['GET'])
def get_player_ratings(player_id):
    """
    특정 선수의 능력치 조회
    """
    try:
        user_id = request.args.get('user_id', 'default')
        session = get_player_session(DB_PATH)

        # 선수 정보 조회
        player = session.query(Player).filter_by(id=player_id).first()
        if not player:
            session.close()
            raise NotFoundError(f"Player with ID {player_id} not found")

        # 능력치 조회
        ratings = session.query(PlayerRating).filter_by(
            player_id=player_id,
            user_id=user_id
        ).all()

        ratings_dict = {}
        for rating in ratings:
            ratings_dict[rating.attribute_name] = {
                'rating': rating.rating,
                'notes': rating.notes,
                'updated_at': rating.updated_at.isoformat() if rating.updated_at else None
            }

        session.close()

        return jsonify({
            'player_id': player_id,
            'player_name': player.name,
            'position': player.position,
            'ratings': ratings_dict
        })

    except NotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error fetching ratings: {str(e)}", exc_info=True)
        raise APIError(f"Failed to fetch ratings: {str(e)}", status_code=500)


@app.route('/api/ratings', methods=['POST'])
def save_player_ratings():
    """
    선수 능력치 저장 또는 업데이트

    Body: {
        "player_id": 123,
        "user_id": "default",
        "ratings": {
            "tackling": 4.5,
            "passing": 3.75,
            ...
        }
    }
    """
    try:
        data = request.json or {}
        player_id = data.get('player_id')
        user_id = data.get('user_id', 'default')
        ratings = data.get('ratings', {})

        if not player_id:
            raise ValidationError("Missing required parameter: player_id")

        if not ratings:
            raise ValidationError("Missing ratings data")

        session = get_player_session(DB_PATH)

        # 선수 존재 확인
        player = session.query(Player).filter_by(id=player_id).first()
        if not player:
            session.close()
            raise NotFoundError(f"Player with ID {player_id} not found")

        # 각 능력치 저장/업데이트
        saved_count = 0
        for attribute_name, rating_value in ratings.items():
            # _comment와 _subPosition은 문자열로 notes 컬럼에 저장 (메타데이터)
            if attribute_name in ['_comment', '_subPosition']:
                # notes 컬럼에 문자열 값 저장 (rating은 0으로 설정)
                existing = session.query(PlayerRating).filter_by(
                    player_id=player_id,
                    user_id=user_id,
                    attribute_name=attribute_name
                ).first()

                string_value = str(rating_value) if not isinstance(rating_value, str) else rating_value

                if existing:
                    existing.rating = 0  # Placeholder
                    existing.notes = string_value
                    existing.updated_at = datetime.now()
                else:
                    new_rating = PlayerRating(
                        player_id=player_id,
                        user_id=user_id,
                        attribute_name=attribute_name,
                        rating=0,  # Placeholder
                        notes=string_value
                    )
                    session.add(new_rating)
                saved_count += 1
                continue

            # 다른 특수 필드 (_, 로 시작)는 건너뛰기
            if attribute_name.startswith('_'):
                continue

            # 값 검증 (0.0 ~ 5.0, 0.25 단위)
            if not isinstance(rating_value, (int, float)):
                continue
            if rating_value < 0.0 or rating_value > 5.0:
                continue
            # 0.25 단위 체크
            if round(rating_value * 4) != rating_value * 4:
                continue

            # 기존 레코드 확인
            existing = session.query(PlayerRating).filter_by(
                player_id=player_id,
                user_id=user_id,
                attribute_name=attribute_name
            ).first()

            if existing:
                # 업데이트
                existing.rating = rating_value
                existing.updated_at = datetime.now()
            else:
                # 신규 생성
                new_rating = PlayerRating(
                    player_id=player_id,
                    user_id=user_id,
                    attribute_name=attribute_name,
                    rating=rating_value
                )
                session.add(new_rating)

            saved_count += 1

        session.commit()
        session.close()

        logger.info(f"✅ Saved {saved_count} ratings for player {player_id}")

        return jsonify({
            'success': True,
            'player_id': player_id,
            'saved_count': saved_count
        })

    except (ValidationError, NotFoundError):
        raise
    except Exception as e:
        logger.error(f"Error saving ratings: {str(e)}", exc_info=True)
        raise APIError(f"Failed to save ratings: {str(e)}", status_code=500)


@app.route('/api/ratings/<int:player_id>/<attribute_name>', methods=['PUT'])
def update_single_rating(player_id, attribute_name):
    """
    단일 능력치 업데이트

    Body: {
        "rating": 4.5,
        "notes": "Optional notes",
        "user_id": "default"
    }
    """
    try:
        data = request.json or {}
        rating_value = data.get('rating')
        notes = data.get('notes', '')
        user_id = data.get('user_id', 'default')

        if rating_value is None:
            raise ValidationError("Missing required parameter: rating")

        # 값 검증
        if rating_value < 0.0 or rating_value > 5.0:
            raise ValidationError("Rating must be between 0.0 and 5.0")

        session = get_player_session(DB_PATH)

        # 기존 레코드 확인
        existing = session.query(PlayerRating).filter_by(
            player_id=player_id,
            user_id=user_id,
            attribute_name=attribute_name
        ).first()

        if existing:
            existing.rating = rating_value
            existing.notes = notes
            existing.updated_at = datetime.now()
        else:
            new_rating = PlayerRating(
                player_id=player_id,
                user_id=user_id,
                attribute_name=attribute_name,
                rating=rating_value,
                notes=notes
            )
            session.add(new_rating)

        session.commit()
        session.close()

        return jsonify({
            'success': True,
            'player_id': player_id,
            'attribute': attribute_name,
            'rating': rating_value
        })

    except (ValidationError, NotFoundError):
        raise
    except Exception as e:
        logger.error(f"Error updating rating: {str(e)}", exc_info=True)
        raise APIError(f"Failed to update rating: {str(e)}", status_code=500)


# ============================================================================
# EPL 공식 데이터 API (Fantasy Premier League)
# ============================================================================

@app.route('/api/epl/standings', methods=['GET'])
@cache.cached(timeout=1800)  # 30분 캐시
def get_epl_standings():
    """
    EPL 리그 순위표 가져오기
    """
    try:
        # 강등팀 필터링 (2024-25 시즌 강등 → 2025-26 시즌 Championship)
        RELEGATED_TEAMS = ['Leicester City', 'Ipswich Town', 'Southampton']

        # Bootstrap 데이터와 Fixtures 데이터 가져오기
        fantasy_data = fetch_fantasy_data()
        fixtures_response = requests.get('https://fantasy.premierleague.com/api/fixtures/', timeout=10)
        fixtures_response.raise_for_status()
        fixtures = fixtures_response.json()

        teams = fantasy_data.get('teams', [])

        # 팀별 통계 계산 (EPL 팀만)
        standings = {}
        for team in teams:
            # 강등팀 제외
            if team['name'] in RELEGATED_TEAMS:
                continue

            team_id = team['id']
            standings[team_id] = {
                'id': team_id,
                'name': team['name'],
                'short_name': team['short_name'],
                'played': 0,
                'won': 0,
                'drawn': 0,
                'lost': 0,
                'goals_for': 0,
                'goals_against': 0,
                'goal_difference': 0,
                'points': 0,
                'position': team.get('position', 0)
            }

        # Fixtures에서 완료된 경기만 처리
        for fixture in fixtures:
            if fixture.get('finished') and fixture.get('team_h_score') is not None:
                home_id = fixture['team_h']
                away_id = fixture['team_a']
                home_score = fixture['team_h_score']
                away_score = fixture['team_a_score']

                # 홈 팀 통계
                if home_id in standings:
                    standings[home_id]['played'] += 1
                    standings[home_id]['goals_for'] += home_score
                    standings[home_id]['goals_against'] += away_score

                    if home_score > away_score:
                        standings[home_id]['won'] += 1
                        standings[home_id]['points'] += 3
                    elif home_score == away_score:
                        standings[home_id]['drawn'] += 1
                        standings[home_id]['points'] += 1
                    else:
                        standings[home_id]['lost'] += 1

                # 원정 팀 통계
                if away_id in standings:
                    standings[away_id]['played'] += 1
                    standings[away_id]['goals_for'] += away_score
                    standings[away_id]['goals_against'] += home_score

                    if away_score > home_score:
                        standings[away_id]['won'] += 1
                        standings[away_id]['points'] += 3
                    elif away_score == home_score:
                        standings[away_id]['drawn'] += 1
                        standings[away_id]['points'] += 1
                    else:
                        standings[away_id]['lost'] += 1

        # 득실차 계산 및 정렬
        standings_list = list(standings.values())
        for team in standings_list:
            team['goal_difference'] = team['goals_for'] - team['goals_against']

        # 승점 > 득실차 > 득점 순으로 정렬
        standings_list.sort(key=lambda x: (x['points'], x['goal_difference'], x['goals_for']), reverse=True)

        # 순위 업데이트
        for idx, team in enumerate(standings_list):
            team['position'] = idx + 1

        return jsonify({'standings': standings_list})

    except Exception as e:
        logger.error(f"Error fetching standings: {str(e)}", exc_info=True)
        raise APIError(f"Failed to fetch standings: {str(e)}", status_code=500)


@app.route('/api/epl/fixtures', methods=['GET'])
@cache.cached(timeout=600, query_string=True)  # 10분 캐시
def get_epl_fixtures():
    """
    EPL 경기 일정 및 결과 가져오기
    Query parameters:
    - event: 특정 게임위크 (옵션)
    - team: 특정 팀 ID (옵션)
    """
    try:
        event_id = request.args.get('event')
        team_id = request.args.get('team')

        # Fixtures 및 Bootstrap 데이터 가져오기
        fixtures_response = requests.get('https://fantasy.premierleague.com/api/fixtures/', timeout=10)
        fixtures_response.raise_for_status()
        fixtures = fixtures_response.json()

        fantasy_data = fetch_fantasy_data()
        teams_dict = {team['id']: team for team in fantasy_data.get('teams', [])}

        # 필터링
        filtered_fixtures = fixtures
        if event_id:
            filtered_fixtures = [f for f in filtered_fixtures if f.get('event') == int(event_id)]
        if team_id:
            team_id = int(team_id)
            filtered_fixtures = [f for f in filtered_fixtures if f.get('team_h') == team_id or f.get('team_a') == team_id]

        # 팀 이름 추가
        enriched_fixtures = []
        for fixture in filtered_fixtures:
            enriched = fixture.copy()
            home_team = teams_dict.get(fixture['team_h'], {})
            away_team = teams_dict.get(fixture['team_a'], {})

            enriched['team_h_name'] = home_team.get('name', 'Unknown')
            enriched['team_h_short'] = home_team.get('short_name', 'UNK')
            enriched['team_a_name'] = away_team.get('name', 'Unknown')
            enriched['team_a_short'] = away_team.get('short_name', 'UNK')

            enriched_fixtures.append(enriched)

        return jsonify({'fixtures': enriched_fixtures})

    except Exception as e:
        logger.error(f"Error fetching fixtures: {str(e)}", exc_info=True)
        raise APIError(f"Failed to fetch fixtures: {str(e)}", status_code=500)


@app.route('/api/epl/leaderboard', methods=['GET'])
@cache.cached(timeout=1800)  # 30분 캐시
def get_epl_leaderboard():
    """
    EPL 리더보드 (득점왕, 도움왕, 클린시트 등)
    SQUAD_DATA와 매핑하여 데이터 정합성 보장
    """
    try:
        # 강등팀 필터링 (2024-25 시즌 강등 → 2025-26 시즌 Championship)
        RELEGATED_TEAMS = ['Leicester City', 'Ipswich Town', 'Southampton']

        fantasy_data = fetch_fantasy_data()
        players = fantasy_data.get('elements', [])
        teams_dict = {team['id']: team for team in fantasy_data.get('teams', [])}

        # 선수 데이터 가공 (EPL 팀만 + SQUAD_DATA 매핑)
        enriched_players = []
        mapped_count = 0
        unmapped_count = 0

        for player in players:
            team = teams_dict.get(player['team'], {})
            team_name = team.get('name', 'Unknown')

            # 강등팀 제외
            if team_name in RELEGATED_TEAMS:
                continue

            # SQUAD_DATA와 매핑
            squad_player = map_fpl_player_to_squad(player, team_name)

            if squad_player:
                # SQUAD_DATA 선수 정보 사용 (데이터 정합성 보장)
                mapped_count += 1
                enriched_players.append({
                    'id': squad_player['id'],  # SQUAD_DATA ID 사용
                    'code': player.get('code'),  # 선수 사진 URL용 코드 (FPL)
                    'name': squad_player['name'],  # SQUAD_DATA 이름 사용
                    'team': team_name,
                    'team_short': team.get('short_name', 'UNK'),
                    'position': squad_player['position'],  # SQUAD_DATA position 사용
                    'goals': player.get('goals_scored', 0),  # FPL 통계
                    'assists': player.get('assists', 0),  # FPL 통계
                    'clean_sheets': player.get('clean_sheets', 0),  # FPL 통계
                    'total_points': player.get('total_points', 0),  # FPL 통계
                    'form': float(player.get('form', 0)),  # FPL 통계
                    'minutes': player.get('minutes', 0)  # FPL 통계
                })
            else:
                # 매핑 실패 시 FPL 데이터 그대로 사용 (fallback)
                unmapped_count += 1
                player_full_name = f"{player['first_name']} {player['second_name']}"
                enriched_players.append({
                    'id': player['id'],
                    'code': player.get('code'),
                    'name': player['web_name'],
                    'team': team_name,
                    'team_short': team.get('short_name', 'UNK'),
                    'position': ['GK', 'DEF', 'MID', 'FWD'][player['element_type'] - 1],
                    'goals': player.get('goals_scored', 0),
                    'assists': player.get('assists', 0),
                    'clean_sheets': player.get('clean_sheets', 0),
                    'total_points': player.get('total_points', 0),
                    'form': float(player.get('form', 0)),
                    'minutes': player.get('minutes', 0)
                })

        logger.info(f"📊 리더보드 매핑 결과: 성공 {mapped_count}명, 실패 {unmapped_count}명")

        # 리더보드 생성
        leaderboard = {
            'top_scorers': sorted([p for p in enriched_players if p['goals'] > 0],
                                 key=lambda x: x['goals'], reverse=True)[:20],
            'top_assists': sorted([p for p in enriched_players if p['assists'] > 0],
                                 key=lambda x: x['assists'], reverse=True)[:20],
            'top_clean_sheets': sorted([p for p in enriched_players if p['clean_sheets'] > 0],
                                      key=lambda x: x['clean_sheets'], reverse=True)[:20],
            'top_points': sorted(enriched_players,
                               key=lambda x: x['total_points'], reverse=True)[:20]
        }

        return jsonify(leaderboard)

    except Exception as e:
        logger.error(f"Error fetching leaderboard: {str(e)}", exc_info=True)
        raise APIError(f"Failed to fetch leaderboard: {str(e)}", status_code=500)


# ============================================================
# Odds & Match Predictions Endpoints
# ============================================================

@app.route('/api/odds/live', methods=['GET'])
def get_live_odds():
    """
    실시간 EPL 배당률

    Query Params:
        - use_demo: true/false (API 키 없을 때 데모 데이터)

    Returns:
        List[Dict]: 경기별 배당률
    """
    try:
        use_demo = request.args.get('use_demo', 'false').lower() == 'true'
        api_key = os.getenv('ODDS_API_KEY')

        if not api_key or use_demo:
            logger.info("Using demo odds data")
            from odds_collection.odds_api_client import get_demo_odds
            raw_data = get_demo_odds()
        else:
            logger.info("Fetching live odds from The Odds API")
            raw_data_api = odds_client.get_epl_odds()
            raw_data = odds_client.parse_odds_data(raw_data_api)

        return jsonify({
            'success': True,
            'count': len(raw_data),
            'matches': raw_data,
            'source': 'demo' if (not api_key or use_demo) else 'live_api',
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error fetching live odds: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/value-bets', methods=['GET'])
def get_value_bets():
    """
    모든 경기의 Value Bet 탐지

    Query Params:
        - min_edge: 최소 edge (default: 0.02)
        - min_confidence: 최소 신뢰도 (default: 0.65)
        - use_demo: true/false

    Returns:
        List[Dict]: Value Bet 목록
    """
    try:
        min_edge = float(request.args.get('min_edge', 0.02))
        min_confidence = float(request.args.get('min_confidence', 0.65))
        use_demo = request.args.get('use_demo', 'false').lower() == 'true'

        # Value Detector 재설정
        detector = ValueDetector(min_edge=min_edge, min_confidence=min_confidence)

        # 배당률 가져오기
        if use_demo:
            from odds_collection.odds_api_client import get_demo_odds
            all_matches = get_demo_odds()
        else:
            raw_data = odds_client.get_epl_odds()
            all_matches = odds_client.parse_odds_data(raw_data)

        # 모든 경기 분석
        all_value_bets = []

        for match in all_matches:
            analysis = odds_aggregator.analyze_match_odds(match)
            analysis['bookmakers_raw'] = match['bookmakers']

            value_bets = detector.detect_value_bets(analysis)
            all_value_bets.extend(value_bets)

        # 요약 통계
        summary = detector.summarize_value_bets(all_value_bets)

        return jsonify({
            'success': True,
            'value_bets': all_value_bets,
            'summary': summary,
            'criteria': {
                'min_edge': min_edge,
                'min_confidence': min_confidence
            },
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error detecting value bets: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/match-predictions', methods=['GET'])
def get_match_predictions():
    """
    배당률 기반 경기 결과 예측
    - 승/무/패 확률
    - 예상 스코어 (Poisson distribution)
    - 가장 가능성 높은 결과

    Query Params:
        - use_demo: true/false
    """
    try:
        use_demo = request.args.get('use_demo', 'true').lower() == 'true'

        # 1. 배당률 데이터 가져오기
        if use_demo:
            from odds_collection.odds_api_client import get_demo_odds
            all_matches = get_demo_odds()
        else:
            raw_data = odds_client.get_epl_odds()
            all_matches = odds_client.parse_odds_data(raw_data)

        # 2. FPL API에서 라운드 정보 가져오기
        try:
            bootstrap_response = requests.get('https://fantasy.premierleague.com/api/bootstrap-static/', timeout=10)
            bootstrap_response.raise_for_status()
            bootstrap_data = bootstrap_response.json()

            fixtures_response = requests.get('https://fantasy.premierleague.com/api/fixtures/', timeout=10)
            fixtures_response.raise_for_status()
            fixtures_data = fixtures_response.json()

            # 팀 ID -> 팀 이름 매핑
            teams = {team['id']: team['name'] for team in bootstrap_data.get('teams', [])}

            # 현재 라운드 찾기
            events = bootstrap_data.get('events', [])
            current_event = next((e for e in events if e.get('is_current', False)), None)
            next_event = next((e for e in events if e.get('is_next', False)), None)
            current_round = (next_event or current_event or {}).get('id', 1)

            # 팀 이름으로 라운드 매핑 생성 (미래 경기만)
            round_mapping = {}
            for fixture in fixtures_data:
                if not fixture.get('finished', False):
                    home_team = teams.get(fixture.get('team_h'))
                    away_team = teams.get(fixture.get('team_a'))
                    event_round = fixture.get('event', current_round)

                    if home_team and away_team:
                        # 팀 이름 정규화
                        key = f"{home_team}_{away_team}"
                        round_mapping[key] = event_round

            logger.info(f"✅ Loaded round info for {len(round_mapping)} upcoming matches (Current round: {current_round})")
        except Exception as e:
            logger.warning(f"⚠️ Failed to load FPL round info: {e}")
            round_mapping = {}
            current_round = None

        # 3. 모든 경기 예측
        predictions = match_predictor.predict_all_matches(all_matches)

        # 4. 예측 데이터에 라운드 정보 추가
        for pred in predictions:
            home_team = pred.get('home_team', '')
            away_team = pred.get('away_team', '')

            # 팀 이름 매칭 시도 (다양한 변형 고려)
            match_key = f"{home_team}_{away_team}"

            # 직접 매칭
            if match_key in round_mapping:
                pred['event'] = round_mapping[match_key]
            else:
                # 부분 매칭 시도 (예: "Man Utd" vs "Manchester United")
                matched_round = None
                for key, round_num in round_mapping.items():
                    key_home, key_away = key.split('_', 1)
                    if (home_team in key_home or key_home in home_team) and \
                       (away_team in key_away or key_away in away_team):
                        matched_round = round_num
                        break

                if matched_round:
                    pred['event'] = matched_round
                else:
                    pred['event'] = current_round

        logger.info(f"✅ Generated {len(predictions)} match predictions with round info")

        # 3. 방법론 가이드
        methodology_guide = {
            'title': 'Sharp Vision AI',
            'description': '세계에서 가장 정확한 Sharp 북메이커(Pinnacle, Betfair Exchange 등)의 배당률을 실시간으로 추출하고 분석하여 '
                          '경기 결과를 예측합니다. Sharp 북메이커는 전문 베터를 허용하며 마진이 낮아(2-3%) 가장 정확한 배당률을 제공합니다. '
                          '연구 결과에 따르면 Sharp 북메이커 합의 예측의 정확도는 약 60%로, 일반 북메이커 평균(57%)보다 높습니다. '
                          '본 시스템은 이러한 Sharp 북메이커의 배당률 데이터를 기반으로 경기 결과를 역추산하는 AI 알고리즘을 구현하였습니다.',
            'steps': [
                {
                    'step': 1,
                    'name': 'Sharp 북메이커 필터링',
                    'formula': 'Bookmakers ∈ {Pinnacle, Betfair, Smarkets, ...}',
                    'description': 'Sharp 북메이커만 선별하여 사용합니다 (Pinnacle, Betfair Exchange, Smarkets, Betclic, Marathonbet).'
                },
                {
                    'step': 2,
                    'name': '암시 확률 계산 (Implied Probability)',
                    'formula': 'P = 1 / 배당률',
                    'description': '각 Sharp 북메이커의 배당률을 확률로 변환합니다.'
                },
                {
                    'step': 3,
                    'name': '합의 확률 (Consensus Probability)',
                    'formula': 'P_consensus = Σ(P_i) / N',
                    'description': 'Sharp 북메이커의 확률 평균을 구하고 마진을 제거하여 실제 확률을 추정합니다.'
                },
                {
                    'step': 4,
                    'name': '예상 득점 계산',
                    'formula': 'E[Total] = f(Over/Under 배당률) → λ_home, λ_away',
                    'description': '언더/오버 배당률로 총 득점 기댓값을 계산하고, 승/무/패 확률로 각 팀에 분배합니다.'
                },
                {
                    'step': 5,
                    'name': 'Poisson Distribution',
                    'formula': 'P(X=k) = (λ^k × e^(-λ)) / k!',
                    'description': '예상 득점을 기반으로 Poisson 분포를 사용하여 모든 가능한 스코어의 확률을 계산합니다.'
                }
            ],
            'data_sources': [
                'The Odds API - Sharp 북메이커 실시간 배당률',
                'Sharp 북메이커: Pinnacle (가장 효율적), Betfair Exchange (시장가), Smarkets, Betclic, Marathonbet',
                'US 북메이커: 언더/오버(Totals) 마켓 데이터 제공'
            ],
            'confidence_levels': {
                'high': '65% 이상 - 높은 신뢰도 (명확한 경기)',
                'medium': '55-65% - 중간 신뢰도 (일반적인 경기)',
                'low': '55% 미만 - 낮은 신뢰도 (불확실한 경기)'
            }
        }

        return jsonify({
            'success': True,
            'predictions': predictions,
            'total_matches': len(predictions),
            'current_round': current_round,
            'methodology': methodology_guide,
            'source': 'demo' if use_demo else 'live_api',
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error generating match predictions: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/dashboard', methods=['GET'])
def get_dashboard_data():
    """
    통합 대시보드 데이터
    - 실시간 배당률
    - Value Bets

    Query Params:
        - use_demo: true/false
    """
    try:
        use_demo = request.args.get('use_demo', 'true').lower() == 'true'

        # 1. 배당률 가져오기
        if use_demo:
            from odds_collection.odds_api_client import get_demo_odds
            all_matches = get_demo_odds()
        else:
            raw_data = odds_client.get_epl_odds()
            all_matches = odds_client.parse_odds_data(raw_data)

        # 2. 모든 경기 분석
        analyzed_matches = []
        for match in all_matches:
            analysis = odds_aggregator.analyze_match_odds(match)
            analysis['match_id'] = match.get('match_id')  # match_id 추가
            analysis['bookmakers_raw'] = match['bookmakers']
            analyzed_matches.append(analysis)

        # 3. Value Bets 탐지
        all_value_bets = []
        for analysis in analyzed_matches:
            value_bets = value_detector.detect_value_bets(analysis)
            all_value_bets.extend(value_bets)

        value_summary = value_detector.summarize_value_bets(all_value_bets)

        return jsonify({
            'success': True,
            'matches': analyzed_matches,
            'value_bets': {
                'opportunities': all_value_bets,
                'summary': value_summary
            },
            'source': 'demo' if use_demo else 'live_api',
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error generating dashboard: {e}")
        return jsonify({'error': str(e)}), 500


# ============================================================
# V3 AI Simulation System Integration
# ============================================================

v3_routes_registered = []

# Import and register Auth routes (core feature)
try:
    from api.v1.auth_routes import register_auth_routes
    register_auth_routes(app)
    v3_routes_registered.append("Auth")
    logger.info("✅ V3 Auth routes registered")
except Exception as e:
    logger.warning(f"⚠️ V3 Auth routes not available: {e}")

# Import and register Simulation routes (core feature)
try:
    from api.v1.simulation_routes import register_simulation_routes
    register_simulation_routes(app)
    v3_routes_registered.append("Simulation")
    logger.info("✅ V3 Simulation routes registered")
except Exception as e:
    logger.warning(f"⚠️ V3 Simulation routes not available: {e}")

# Import and register Payment routes (optional - requires Stripe config)
try:
    from api.v1.payment_routes import payment_bp
    app.register_blueprint(payment_bp)
    v3_routes_registered.append("Payment")
    logger.info("✅ V3 Payment routes registered")
except Exception as e:
    logger.warning(f"⚠️ V3 Payment routes not available (Stripe not configured): {e}")

# Import and register AI Simulation routes (Haiku-based Simple AI)
try:
    from api.ai_simulation_routes import ai_simulation_bp
    app.register_blueprint(ai_simulation_bp)
    v3_routes_registered.append("AI_Simulation")
    logger.info("✅ AI Simulation routes registered (Claude Haiku)")
except Exception as e:
    logger.warning(f"⚠️ AI Simulation routes not available: {e}")

if v3_routes_registered:
    logger.info(f"🚀 V3 System activated: {', '.join(v3_routes_registered)}")
else:
    logger.info("ℹ️ V3 System not activated - using legacy routes only")


# ============================================================
# React SPA Support - Catch all routes
# ============================================================

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_react(path):
    """
    React SPA 라우팅 지원
    - API 요청이 아닌 경우 React index.html 제공
    """
    # API 경로는 무시 (이미 정의된 API 엔드포인트로 라우팅됨)
    if path.startswith('api/'):
        return jsonify({
            'error': {
                'code': 'NOT_FOUND',
                'message': 'The requested API endpoint was not found',
                'status': 404
            }
        }), 404

    # 정적 파일 요청 (js, css, images 등)
    if path and os.path.exists(os.path.join(app.static_folder, path)):
        return app.send_static_file(path)

    # React index.html 제공 (클라이언트 사이드 라우팅)
    if os.path.exists(os.path.join(app.static_folder, 'index.html')):
        return app.send_static_file('index.html')

    # 빌드 파일이 없는 경우
    return jsonify({
        'error': 'React build not found',
        'message': 'Please run `npm run build` in the frontend directory'
    }), 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
