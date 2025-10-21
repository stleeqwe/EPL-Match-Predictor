"""
AI Simulation API Routes
Flask endpoints for Claude-powered match predictions
"""

from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.simple_predictor import SimpleAIPredictor

# Create blueprint
ai_simulation_bp = Blueprint('ai_simulation', __name__)

# Initialize predictor (lazy loading)
_predictor = None


def get_predictor():
    """Get or create predictor instance"""
    global _predictor
    if _predictor is None:
        _predictor = SimpleAIPredictor()
    return _predictor


@ai_simulation_bp.route('/api/ai-simulation/predict', methods=['POST', 'OPTIONS'])
@cross_origin()
def ai_predict():
    """
    AI-powered match prediction endpoint

    Request Body:
    {
        "home_team": "Liverpool",
        "away_team": "Manchester United",
        "user_evaluation": {
            "home_overall": 85.5,
            "home_player_score": 88.0,
            "home_strength_score": 82.0,
            "home_comments": "Strong attacking team...",
            "away_overall": 78.2,
            "away_player_score": 76.0,
            "away_strength_score": 80.5,
            "away_comments": "Solid defensive setup..."
        },
        "sharp_odds": {  // Optional
            "home": 1.85,
            "draw": 3.40,
            "away": 4.20
        },
        "recent_form": {  // Optional
            "home_form": "W-W-D-W-W",
            "away_form": "L-D-W-L-D"
        }
    }

    Response:
    {
        "success": true,
        "predicted_score": "2-1",
        "probabilities": {
            "home_win": 0.45,
            "draw": 0.28,
            "away_win": 0.27
        },
        "confidence": "medium",
        "confidence_score": 62,
        "reasoning": "...",
        "key_factors": ["...", "...", "..."],
        "expected_goals": {
            "home": 1.8,
            "away": 1.2
        },
        "metadata": {
            "model": "claude-3-haiku-20240307",
            "tokens_used": {...},
            "cost_usd": 0.000449
        }
    }
    """

    if request.method == 'OPTIONS':
        return '', 200

    try:
        # Get request data
        data = request.get_json()

        # Validate required fields
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400

        home_team = data.get('home_team')
        away_team = data.get('away_team')
        user_evaluation = data.get('user_evaluation', {})

        if not home_team or not away_team:
            return jsonify({
                'success': False,
                'error': 'home_team and away_team are required'
            }), 400

        if not user_evaluation:
            return jsonify({
                'success': False,
                'error': 'user_evaluation is required'
            }), 400

        # Optional fields
        sharp_odds = data.get('sharp_odds')
        recent_form = data.get('recent_form')

        # Get predictor
        predictor = get_predictor()

        # Make prediction
        result = predictor.predict(
            home_team=home_team,
            away_team=away_team,
            user_evaluation=user_evaluation,
            sharp_odds=sharp_odds,
            recent_form=recent_form
        )

        # Check if prediction was successful
        if not result.get('success', True):
            return jsonify(result), 500

        return jsonify(result), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@ai_simulation_bp.route('/api/ai-simulation/health', methods=['GET'])
@cross_origin()
def health_check():
    """Health check endpoint"""

    try:
        predictor = get_predictor()

        return jsonify({
            'status': 'healthy',
            'model': predictor.model,
            'api_key_set': bool(predictor.api_key)
        }), 200

    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500


@ai_simulation_bp.route('/api/ai-simulation/info', methods=['GET'])
@cross_origin()
def get_info():
    """Get AI simulation information"""

    return jsonify({
        'model': 'claude-3-haiku-20240307',
        'model_name': 'Claude 3 Haiku',
        'capabilities': {
            'speed': 'Fast (3-5 seconds)',
            'cost': 'Very Low ($0.004 per prediction)',
            'accuracy': 'Basic to Good',
            'best_for': ['Quick predictions', 'Basic analysis', 'Cost-effective scenarios']
        },
        'limitations': {
            'complex_reasoning': 'Limited',
            'tactical_depth': 'Basic',
            'multi_agent': 'Not supported'
        },
        'pricing': {
            'input_tokens': '$0.25 per 1M tokens',
            'output_tokens': '$1.25 per 1M tokens',
            'avg_cost_per_prediction': '$0.004'
        },
        'future_upgrades': {
            'when_sonnet_available': {
                'model': 'claude-3-5-sonnet',
                'improvements': ['Better reasoning', 'Tactical depth', 'Higher accuracy'],
                'cost': '$0.08 per prediction (20x higher)'
            },
            'when_opus_available': {
                'model': 'claude-3-opus',
                'improvements': ['Expert-level analysis', 'Multi-agent support', 'Deep reasoning'],
                'cost': '$0.29 per prediction (70x higher)'
            }
        }
    }), 200
