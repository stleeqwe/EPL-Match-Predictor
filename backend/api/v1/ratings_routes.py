"""
Player Ratings API Routes
선수 능력치 AI 자동 생성 API
"""

from flask import Blueprint, request, jsonify
import logging

from services.fpl_player_service import get_fpl_service
from services.ai_rating_generator import get_ai_rating_generator

logger = logging.getLogger(__name__)

ratings_bp = Blueprint('ratings', __name__, url_prefix='/api/v1/ratings')


@ratings_bp.route('/ai-generate', methods=['POST'])
def ai_generate_ratings():
    """
    AI로 선수 능력치 자동 생성

    Request Body:
    {
        "player_id": 123,           # Optional
        "player_name": "Bukayo Saka",
        "position": "WG",            # GK, CB, FB, DM, CM, CAM, WG, ST
        "team": "Arsenal"
    }

    Response:
    {
        "success": true,
        "ratings": {
            "speed_dribbling": 4.25,
            "one_on_one_beating": 4.00,
            ...
        },
        "comment": "절정의 폼을 과시하며...",
        "confidence": 0.85,
        "data_sources": {
            "fpl_stats": {...},
            "ai_model": "gemini-2.5-flash"
        }
    }

    Error Response:
    {
        "success": false,
        "error": "Error message"
    }
    """
    try:
        # 1. Request 검증
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Missing request body'
            }), 400

        player_name = data.get('player_name')
        position = data.get('position')
        team = data.get('team')

        if not player_name or not position:
            return jsonify({
                'success': False,
                'error': 'Missing required fields: player_name, position'
            }), 400

        # 포지션 검증
        valid_positions = ['GK', 'CB', 'FB', 'DM', 'CM', 'CAM', 'WG', 'ST']
        if position not in valid_positions:
            return jsonify({
                'success': False,
                'error': f'Invalid position: {position}. Must be one of {valid_positions}'
            }), 400

        logger.info(f"AI Rating Generation Request: {player_name} ({position}, {team})")

        # 팀 정보 검증
        if not team or team == 'Unknown':
            logger.warning(f"⚠️ Team information missing for {player_name}. FPL matching may be inaccurate.")
            # 계속 진행하지만 경고 로그 남김

        # 2. FPL API에서 선수 스탯 조회
        fpl_service = get_fpl_service()
        fpl_stats = fpl_service.get_player_stats(player_name, team if team != 'Unknown' else None)

        if not fpl_stats:
            logger.warning(f"FPL stats not found for: {player_name} ({team})")
            return jsonify({
                'success': False,
                'error': f'Player not found in FPL API: {player_name}'
            }), 404

        logger.info(f"FPL stats found: {fpl_stats['name']} - {fpl_stats['goals']}G {fpl_stats['assists']}A")
        logger.info(f"   Team: {fpl_stats['team']}, Minutes: {fpl_stats['minutes']}, Form: {fpl_stats['form']}")

        # 출전시간 검증
        if fpl_stats['minutes'] < 100:
            logger.warning(f"⚠️ Low playing time for {player_name}: {fpl_stats['minutes']} minutes. AI rating may be unreliable.")
            # 계속 진행하지만 경고 로그 남김

        # 3. AI로 능력치 생성
        generator = get_ai_rating_generator()

        try:
            result = generator.generate(
                player_name=fpl_stats['name'],  # FPL의 정확한 이름 사용
                position=position,
                team=fpl_stats['team'],
                fpl_stats=fpl_stats
            )
        except ValueError as e:
            logger.error(f"AI generation validation error: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 400
        except RuntimeError as e:
            logger.error(f"AI generation runtime error: {e}")
            return jsonify({
                'success': False,
                'error': 'AI generation failed. Please try again.'
            }), 500

        # 4. 응답 반환
        response = {
            'success': True,
            'ratings': result.ratings,
            'comment': result.comment,
            'confidence': result.confidence,
            'data_sources': {
                'fpl_stats': fpl_stats,
                'ai_model': 'gemini-2.5-flash',
                'position': position
            }
        }

        logger.info(f"✅ AI Rating generated for {player_name}: {len(result.ratings)} attributes, confidence {result.confidence:.1%}")
        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Unexpected error in ai_generate_ratings: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@ratings_bp.route('/positions', methods=['GET'])
def get_positions():
    """
    사용 가능한 포지션 목록 조회

    Response:
    {
        "success": true,
        "positions": [
            {"key": "GK", "name": "골키퍼", "name_en": "Goalkeeper"},
            {"key": "CB", "name": "센터백", "name_en": "Center Back"},
            ...
        ]
    }
    """
    from services.ai_rating_generator import POSITION_ATTRIBUTES

    positions = [
        {
            'key': key,
            'name': data['name'],
            'name_en': data['name_en'],
            'attribute_count': len(data['attributes'])
        }
        for key, data in POSITION_ATTRIBUTES.items()
    ]

    return jsonify({
        'success': True,
        'positions': positions
    }), 200


def register_ratings_routes(app):
    """Register ratings routes with Flask app"""
    app.register_blueprint(ratings_bp)
    logger.info("✅ Ratings API routes registered")
