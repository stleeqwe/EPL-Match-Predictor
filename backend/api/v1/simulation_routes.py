"""
AI Simulation API Routes
AI Match Simulation v3.0
"""

from flask import Blueprint, request, jsonify, g
import logging

from services.simulation_service import get_simulation_service
from middleware.auth_middleware import require_auth, require_tier
from middleware.rate_limiter import get_rate_limiter

logger = logging.getLogger(__name__)

simulation_bp = Blueprint('simulation', __name__, url_prefix='/api/v1/simulation')
simulation_service = get_simulation_service()
rate_limiter = get_rate_limiter()


@simulation_bp.route('/simulate', methods=['POST'])
@require_auth
def simulate_match():
    """AI-powered match simulation (tier-based rate limited)."""
    try:
        # Rate limiting
        allowed = rate_limiter.check_limit(g.user_id, g.user_tier, 'simulation')
        if not allowed['allowed']:
            return jsonify({'error': 'Rate limit exceeded', 'reset_at': allowed['reset_at']}), 429

        data = request.get_json()
        home_team = data.get('home_team')
        away_team = data.get('away_team')
        weights = data.get('weights')  # Optional: custom weights

        if not home_team or not away_team:
            return jsonify({'error': 'Missing home_team or away_team'}), 400

        # Validate weights if provided
        if weights:
            if not isinstance(weights, dict):
                return jsonify({'error': 'weights must be a dictionary'}), 400

            # Check required keys
            required_keys = ['user_value', 'odds', 'stats']
            if not all(key in weights for key in required_keys):
                return jsonify({'error': f'weights must contain: {required_keys}'}), 400

            # Check values are numeric and sum to ~1.0
            total = sum(weights.values())
            if not (0.99 <= total <= 1.01):  # Allow small floating point errors
                return jsonify({'error': f'weights must sum to 1.0 (current sum: {total})'}), 400

            # Check values are between 0 and 1
            for key, value in weights.items():
                if not (0 <= value <= 1):
                    return jsonify({'error': f'{key} weight must be between 0 and 1'}), 400

        # Run simulation (with optional weights)
        success, result, error = simulation_service.simulate_match(
            home_team=home_team,
            away_team=away_team,
            user_id=g.user_id,
            tier=g.user_tier,
            weights=weights
        )

        if not success:
            return jsonify({'error': 'Simulation failed', 'message': error}), 500

        return jsonify({
            'success': True,
            'result': result,
            'tier': g.user_tier
        }), 200

    except Exception as e:
        logger.error(f"Simulation error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@simulation_bp.route('/weight-presets', methods=['GET'])
def get_weight_presets():
    """Get available weight presets for data source customization."""
    try:
        presets = [
            {
                'id': 'balanced',
                'name': '밸런스 (기본)',
                'name_en': 'Balanced (Default)',
                'weights': {
                    'user_value': 0.65,
                    'odds': 0.20,
                    'stats': 0.15
                },
                'description': '기본 균형 설정 - 사용자 분석 중심',
                'description_en': 'Default balanced setting - User analysis focused',
                'icon': '⚖️'
            },
            {
                'id': 'analyst',
                'name': '분석가 모드',
                'name_en': 'Analyst Mode',
                'weights': {
                    'user_value': 0.80,
                    'odds': 0.10,
                    'stats': 0.10
                },
                'description': '당신의 전문적 분석을 최우선으로 반영',
                'description_en': 'Prioritize your expert analysis',
                'icon': '🎯'
            },
            {
                'id': 'odds_heavy',
                'name': '배당 중시',
                'name_en': 'Odds Focused',
                'weights': {
                    'user_value': 0.30,
                    'odds': 0.50,
                    'stats': 0.20
                },
                'description': '시장 컨센서스와 배당률 중심 예측',
                'description_en': 'Market consensus and odds-based prediction',
                'icon': '📊'
            },
            {
                'id': 'stats_heavy',
                'name': '통계 중시',
                'name_en': 'Stats Focused',
                'weights': {
                    'user_value': 0.30,
                    'odds': 0.20,
                    'stats': 0.50
                },
                'description': '객관적 데이터와 통계 기반 예측',
                'description_en': 'Objective data and statistics-based prediction',
                'icon': '📈'
            },
            {
                'id': 'hybrid',
                'name': '하이브리드',
                'name_en': 'Hybrid',
                'weights': {
                    'user_value': 0.50,
                    'odds': 0.30,
                    'stats': 0.20
                },
                'description': '주관과 시장 데이터의 균형',
                'description_en': 'Balance between subjective and market data',
                'icon': '🔄'
            }
        ]

        return jsonify({
            'success': True,
            'presets': presets
        }), 200

    except Exception as e:
        logger.error(f"Error fetching weight presets: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


def register_simulation_routes(app):
    """Register simulation routes with Flask app."""
    app.register_blueprint(simulation_bp)
    logger.info("Simulation routes registered")
