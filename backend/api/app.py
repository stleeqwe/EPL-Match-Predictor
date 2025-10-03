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

# 부모 디렉토리를 path에 추가
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from data_collection import FBrefScraper
from data.squad_data import SQUAD_DATA
from database.player_schema import get_player_session, Player, PlayerRating, Team, PositionAttribute
import pandas as pd

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


# ==================== API Endpoints ====================

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
    EPL 전체 팀 목록 가져오기
    """
    try:
        teams = list(SQUAD_DATA.keys())
        return jsonify(sorted(teams))
    except Exception as e:
        logger.error(f"Error fetching teams: {str(e)}", exc_info=True)
        raise APIError(f"Failed to fetch teams: {str(e)}", status_code=500)


@app.route('/api/squad/<team_name>', methods=['GET'])
@cache.cached(timeout=1800, query_string=True)
def get_squad(team_name):
    """
    특정 팀의 선수 명단 가져오기
    """
    try:
        if team_name not in SQUAD_DATA:
            raise NotFoundError(f"Team '{team_name}' not found")

        players = SQUAD_DATA[team_name]
        logger.info(f"📋 Retrieved {len(players)} players for {team_name}")

        return jsonify(players)
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


@app.route('/api/positions', methods=['GET'])
def get_positions():
    """
    포지션 목록 및 포지션별 능력치 카테고리
    """
    positions_config = {
        'GK': {
            'name': '골키퍼',
            'attributes': [
                {'key': 'reflexes', 'name': '반응속도', 'name_en': 'Reflexes'},
                {'key': 'positioning', 'name': '포지셔닝', 'name_en': 'Positioning'},
                {'key': 'handling', 'name': '핸들링', 'name_en': 'Handling'},
                {'key': 'kicking', 'name': '발재간', 'name_en': 'Kicking'},
                {'key': 'aerial', 'name': '공중볼 처리', 'name_en': 'Aerial'},
                {'key': 'one_on_one', 'name': '1:1 대응', 'name_en': 'One-on-One'}
            ]
        },
        'DF': {
            'name': '수비수',
            'attributes': [
                {'key': 'tackling', 'name': '태클', 'name_en': 'Tackling'},
                {'key': 'marking', 'name': '마크', 'name_en': 'Marking'},
                {'key': 'positioning', 'name': '포지셔닝', 'name_en': 'Positioning'},
                {'key': 'heading', 'name': '헤더', 'name_en': 'Heading'},
                {'key': 'physicality', 'name': '피지컬', 'name_en': 'Physicality'},
                {'key': 'speed', 'name': '스피드', 'name_en': 'Speed'},
                {'key': 'passing', 'name': '패스', 'name_en': 'Passing'}
            ]
        },
        'MF': {
            'name': '미드필더',
            'attributes': [
                {'key': 'passing', 'name': '패스', 'name_en': 'Passing'},
                {'key': 'vision', 'name': '비전', 'name_en': 'Vision'},
                {'key': 'dribbling', 'name': '드리블', 'name_en': 'Dribbling'},
                {'key': 'shooting', 'name': '슈팅', 'name_en': 'Shooting'},
                {'key': 'tackling', 'name': '태클', 'name_en': 'Tackling'},
                {'key': 'stamina', 'name': '체력', 'name_en': 'Stamina'},
                {'key': 'creativity', 'name': '창조력', 'name_en': 'Creativity'}
            ]
        },
        'FW': {
            'name': '공격수',
            'attributes': [
                {'key': 'finishing', 'name': '슈팅', 'name_en': 'Finishing'},
                {'key': 'positioning', 'name': '위치선정', 'name_en': 'Positioning'},
                {'key': 'dribbling', 'name': '드리블', 'name_en': 'Dribbling'},
                {'key': 'pace', 'name': '스피드', 'name_en': 'Pace'},
                {'key': 'physicality', 'name': '피지컬', 'name_en': 'Physicality'},
                {'key': 'heading', 'name': '헤더', 'name_en': 'Heading'},
                {'key': 'first_touch', 'name': '퍼스트터치', 'name_en': 'First Touch'}
            ]
        }
    }

    return jsonify(positions_config)


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


@app.route('/api/ratings/<int:player_id>', methods=['GET'])
def get_player_ratings(player_id):
    """
    특정 선수의 능력치 조회
    """
    try:
        user_id = request.args.get('user_id', 'default')
        session = get_player_session()

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

        session = get_player_session()

        # 선수 존재 확인
        player = session.query(Player).filter_by(id=player_id).first()
        if not player:
            session.close()
            raise NotFoundError(f"Player with ID {player_id} not found")

        # 각 능력치 저장/업데이트
        saved_count = 0
        for attribute_name, rating_value in ratings.items():
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

        session = get_player_session()

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


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
