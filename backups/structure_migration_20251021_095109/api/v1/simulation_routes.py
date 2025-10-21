"""
AI Simulation API Routes
AI Match Simulation v3.0
"""

from flask import Blueprint, request, jsonify, g, Response, stream_with_context
import logging

from services.simulation_service import get_simulation_service
from services.enriched_simulation_service import get_enriched_simulation_service
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



@simulation_bp.route('/enriched/check-readiness/<team_name>', methods=['GET'])
def check_team_readiness(team_name):
    """
    Check if team is ready for enriched simulation.

    Response:
    {
        "success": true,
        "ready": true/false,
        "team_name": "Arsenal",
        "completed": {
            "lineup": true,
            "formation": true,
            "tactics": true,
            "ratings": true,
            "commentary": true
        },
        "missing": [],
        "player_count": 11,
        "formation": "4-3-3"
    }
    """
    try:
        enriched_service = get_enriched_simulation_service()
        ready, details = enriched_service.check_team_readiness(team_name)

        return jsonify({
            'success': True,
            **details
        }), 200

    except Exception as e:
        logger.error(f"Check readiness error for {team_name}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to check team readiness',
            'message': str(e)
        }), 500


@simulation_bp.route('/v3/stream', methods=['POST'])
def simulate_match_v3_stream():
    """
    🚀 V3 Pipeline: Real-time SSE streaming simulation

    NEW FEATURES:
    - ✅ NO Templates (dynamic 2-5 scenarios based on match balance)
    - ✅ 100% User Domain Data (11 players, formations, tactics)
    - ✅ Pure Convergence (NO bias detection, NO EPL forcing)
    - ✅ 2.2x Faster (53s vs 120s for V2)
    - ✅ Mathematical Models: Poisson-Rating, Zone Dominance, Key Player
    - ✅ Monte Carlo Validation: 3000 runs per scenario

    Request Body:
    {
        "home_team": "Arsenal",
        "away_team": "Liverpool"
    }

    Response: Server-Sent Events (SSE) Stream

    Event Types:
    - phase1_started: Ensemble calculation started
    - phase1_complete: Ensemble probabilities calculated
    - phase2_started: AI scenario generation started
    - phase2_complete: Scenarios generated
    - phase3_started: Monte Carlo validation started
    - phase3_progress: Validation progress (per scenario)
    - phase3_complete: Validation complete
    - completed: Simulation completed with final result
    - error: Error occurred
    """
    from utils.simulation_events import SimulationEvent
    import json
    import time

    # Optional authentication
    user_id = None
    user_tier = 'BASIC'

    auth_header = request.headers.get('Authorization')
    if auth_header:
        try:
            from middleware.auth_middleware import get_auth_middleware
            middleware = get_auth_middleware()
            is_valid, payload, error = middleware.verify_request()
            if is_valid:
                user_id = payload.get('user_id')
                user_tier = payload.get('tier', 'BASIC')
        except:
            pass

    # Rate limiting (if authenticated)
    if user_id:
        try:
            allowed = rate_limiter.check_limit(user_id, user_tier, 'simulation_v3')
            if not allowed['allowed']:
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'reset_at': allowed['reset_at']
                }), 429
        except Exception as e:
            logger.warning(f"Rate limiter check failed: {str(e)}")

    # Read request body
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'Missing request body'}), 400

        home_team = data.get('home_team')
        away_team = data.get('away_team')

        if not home_team or not away_team:
            return jsonify({'error': 'Missing home_team or away_team'}), 400

        if home_team == away_team:
            return jsonify({'error': 'home_team and away_team cannot be the same'}), 400

    except Exception as e:
        return jsonify({'error': 'Invalid request format', 'message': str(e)}), 400

    def generate():
        """Generator function for SSE streaming"""
        try:
            from services.enriched_data_loader import EnrichedDomainDataLoader
            from simulation.v3.pipeline import SimulationPipelineV3, PipelineConfig

            start_time = time.time()

            user_info = f"user: {user_id}, tier: {user_tier}" if user_id else "unauthenticated"
            logger.info(f"SSE streaming simulation (V3 Pipeline): {home_team} vs {away_team} ({user_info})")

            # Send started event
            yield SimulationEvent.info(
                f"V3 Pipeline started: {home_team} vs {away_team}",
                "started"
            ).to_sse_format()

            # Phase 0: Load team data
            yield SimulationEvent.info("Loading team data...", "loading_teams").to_sse_format()

            loader = EnrichedDomainDataLoader()
            home_data = loader.load_team_data(home_team)
            away_data = loader.load_team_data(away_team)

            yield SimulationEvent.info(
                f"Teams loaded: {home_team} (Attack: {home_data.derived_strengths.attack_strength:.1f}), "
                f"{away_team} (Attack: {away_data.derived_strengths.attack_strength:.1f})",
                "teams_loaded"
            ).to_sse_format()

            # Create pipeline config
            config = PipelineConfig(
                validation_runs=3000,  # Production setting
                log_level="INFO"
            )

            pipeline = SimulationPipelineV3(config=config)

            # ========================================
            # Phase 1: Mathematical Models (Ensemble)
            # ========================================
            yield SimulationEvent.info(
                "Phase 1/4: Running Mathematical Models (Poisson, Zone, Player)...",
                "phase1_started"
            ).to_sse_format()

            ensemble_result = pipeline._run_phase1_ensemble(home_data, away_data)

            yield SimulationEvent.info(
                f"Phase 1 Complete: Ensemble probabilities calculated",
                "phase1_complete",
                {
                    "probabilities": ensemble_result.ensemble_probabilities,
                    "home_win": ensemble_result.ensemble_probabilities['home_win'],
                    "draw": ensemble_result.ensemble_probabilities['draw'],
                    "away_win": ensemble_result.ensemble_probabilities['away_win']
                }
            ).to_sse_format()

            # ========================================
            # Phase 2: AI Scenario Generation
            # ========================================
            yield SimulationEvent.info(
                "Phase 2/4: Generating AI scenarios (NO Templates)...",
                "phase2_started"
            ).to_sse_format()

            generated_scenarios = pipeline._run_phase2_scenarios(home_data, away_data, ensemble_result)

            yield SimulationEvent.info(
                f"Phase 2 Complete: {generated_scenarios.scenario_count} scenarios generated",
                "phase2_complete",
                {
                    "scenario_count": generated_scenarios.scenario_count,
                    "scenarios": [
                        {
                            "id": sc.id,
                            "name": sc.name,
                            "probability": sc.expected_probability
                        }
                        for sc in generated_scenarios.scenarios
                    ]
                }
            ).to_sse_format()

            # ========================================
            # Phase 3: Monte Carlo Validation
            # ========================================
            yield SimulationEvent.info(
                f"Phase 3/4: Running {generated_scenarios.scenario_count * config.validation_runs:,} simulations...",
                "phase3_started",
                {
                    "total_runs": generated_scenarios.scenario_count * config.validation_runs,
                    "runs_per_scenario": config.validation_runs
                }
            ).to_sse_format()

            validation_result = pipeline._run_phase3_validation(
                generated_scenarios.scenarios,
                home_data,
                away_data,
                ensemble_result
            )

            yield SimulationEvent.info(
                f"Phase 3 Complete: {validation_result.total_runs:,} simulations completed",
                "phase3_complete",
                {
                    "total_runs": validation_result.total_runs,
                    "convergence": validation_result.final_probabilities
                }
            ).to_sse_format()

            # Prepare final result
            execution_time = time.time() - start_time

            final_result = {
                "match": {
                    "home_team": home_team,
                    "away_team": away_team
                },
                "probabilities": {
                    "home_win": validation_result.final_probabilities['home_win'],
                    "draw": validation_result.final_probabilities['draw'],
                    "away_win": validation_result.final_probabilities['away_win']
                },
                "scenarios": [
                    {
                        "id": sc.id,
                        "name": sc.name,
                        "expected_probability": sc.expected_probability,
                        "events_count": len(sc.events)
                    }
                    for sc in generated_scenarios.scenarios
                ],
                "validation": {
                    "total_scenarios": validation_result.total_scenarios,
                    "total_runs": validation_result.total_runs,
                    "scenario_results": [
                        {
                            "scenario_id": sr.scenario_id,
                            "scenario_name": sr.scenario_name,
                            "convergence_probability": sr.convergence_probability,
                            "avg_score": sr.avg_score
                        }
                        for sr in validation_result.scenario_results
                    ]
                },
                "execution_time": execution_time,
                "pipeline": "v3",
                "timestamp": time.time()
            }

            # Send completed event
            yield SimulationEvent.success(
                f"V3 Pipeline completed in {execution_time:.1f}s",
                "completed",
                final_result
            ).to_sse_format()

            logger.info(f"SSE stream completed (V3 Pipeline): {home_team} vs {away_team} ({execution_time:.1f}s)")

        except Exception as e:
            logger.error(f"V3 Pipeline error: {str(e)}")
            import traceback
            traceback.print_exc()
            error_event = SimulationEvent.error(f'V3 Pipeline error: {str(e)}', 'pipeline_error')
            yield error_event.to_sse_format()

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization',
            'Access-Control-Allow-Methods': 'POST, OPTIONS'
        }
    )


def register_simulation_routes(app):
    """Register simulation routes with Flask app."""
    app.register_blueprint(simulation_bp)
    logger.info("Simulation routes registered")
