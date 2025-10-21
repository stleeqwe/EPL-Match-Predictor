"""
Enriched Match Simulation Service
Complete workflow orchestration for AI-powered match predictions using enriched domain data.

Phase 3 E2E Integration:
- Load enriched domain data (20 teams)
- Call AI Client for predictions
- Format responses for frontend consumption
"""

import logging
from typing import Dict, Optional, Tuple
from datetime import datetime
import queue
import threading

from services.enriched_data_loader import EnrichedDomainDataLoader
from ai.ai_factory import get_ai_client
from simulation.v2.simulation_pipeline import get_pipeline, PipelineConfig
from utils.simulation_events import SimulationEvent
import time

logger = logging.getLogger(__name__)


class EnrichedSimulationService:
    """
    Orchestrate enriched match simulation workflow.

    Features:
    - Load enriched domain data for both teams
    - Validate data completeness
    - Call AI Client with full context
    - Format predictions for frontend display
    - Error handling and logging
    """

    def __init__(self):
        """Initialize enriched simulation service."""
        self.loader = EnrichedDomainDataLoader()
        self.client = get_ai_client()  # Uses AI_PROVIDER from .env
        logger.info(f"EnrichedSimulationService initialized with AI client: {self.client.get_model_info()['provider']}")

    def simulate_match_enriched(
        self,
        home_team: str,
        away_team: str,
        match_context: Optional[Dict] = None
    ) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Run enriched match simulation with full domain data.

        Args:
            home_team: Home team name (e.g., "Arsenal")
            away_team: Away team name (e.g., "Liverpool")
            match_context: Optional match context
                {
                    'venue': 'Emirates Stadium',
                    'competition': 'Premier League',
                    'importance': 'top_clash',
                    'weather': 'Clear'
                }

        Returns:
            Tuple of (success, result_dict, error_message)

            result_dict format:
            {
                'success': True,
                'prediction': {
                    'home_win_probability': 0.40,
                    'draw_probability': 0.30,
                    'away_win_probability': 0.30,
                    'predicted_score': '2-1',
                    'confidence': 'medium',
                    'expected_goals': {'home': 1.8, 'away': 1.2}
                },
                'analysis': {
                    'key_factors': [...],
                    'home_team_strengths': [...],
                    'away_team_strengths': [...],
                    'tactical_insight': '...'
                },
                'summary': '...',
                'teams': {
                    'home': {'name': '...', 'formation': '...'},
                    'away': {'name': '...', 'formation': '...'}
                },
                'usage': {
                    'total_tokens': 1512,
                    'processing_time': 72.3
                },
                'timestamp': '2025-10-16T...'
            }
        """
        logger.info(f"Enriched simulation starting: {home_team} vs {away_team}")

        # Set default match context
        if match_context is None:
            match_context = {}

        # Validate AI availability
        is_healthy, health_error = self.client.health_check()
        if not is_healthy:
            error_msg = f"AI not available: {health_error}"
            logger.error(error_msg)
            return False, None, error_msg

        # Step 1: Load home team data
        try:
            logger.info(f"Loading enriched data for {home_team}...")
            home_team_data = self.loader.load_team_data(home_team)
            logger.info(f"✓ {home_team} data loaded: {len(home_team_data.lineup)} players")
        except FileNotFoundError as e:
            error_msg = f"Home team '{home_team}' not found: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
        except ValueError as e:
            error_msg = f"Home team '{home_team}' data incomplete: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
        except Exception as e:
            error_msg = f"Failed to load home team '{home_team}': {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg

        # Step 2: Load away team data
        try:
            logger.info(f"Loading enriched data for {away_team}...")
            away_team_data = self.loader.load_team_data(away_team)
            logger.info(f"✓ {away_team} data loaded: {len(away_team_data.lineup)} players")
        except FileNotFoundError as e:
            error_msg = f"Away team '{away_team}' not found: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
        except ValueError as e:
            error_msg = f"Away team '{away_team}' data incomplete: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
        except Exception as e:
            error_msg = f"Failed to load away team '{away_team}': {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg

        # Step 3: Run V2 Pipeline (Phase 1-7)
        logger.info(f"Running V2 Pipeline with Enriched Domain Data...")
        start_time = datetime.utcnow()

        # Get pipeline
        pipeline = get_pipeline(config=PipelineConfig(
            max_iterations=5,
            initial_runs=100,
            final_runs=3000,
            convergence_threshold=0.85
        ))

        # Run enriched pipeline
        success, pipeline_result, error = pipeline.run_enriched(
            home_team=home_team_data,
            away_team=away_team_data,
            match_context=match_context
        )

        processing_time = (datetime.utcnow() - start_time).total_seconds()

        if not success:
            error_msg = f"Pipeline failed: {error}"
            logger.error(error_msg)
            return False, None, error_msg

        logger.info(f"✓ Pipeline complete ({processing_time:.1f}s)")

        # Step 4: Format response
        report = pipeline_result['report']
        prediction = report['prediction']

        result = {
            'success': True,
            'prediction': prediction['win_probabilities'],  # {home, draw, away}
            'predicted_score': f"{prediction['expected_goals']['home']:.0f}-{prediction['expected_goals']['away']:.0f}",
            'expected_goals': prediction['expected_goals'],
            'confidence': 'high' if pipeline_result['converged'] else 'medium',
            'analysis': {
                'key_factors': [],  # Can extract from scenarios
                'dominant_scenario': report['dominant_scenario'],
                'all_scenarios': report['all_scenarios'],
                'tactical_insight': f"Simulation converged after {pipeline_result['iterations']} iterations."
            },
            'summary': f"{home_team} vs {away_team}: {report['dominant_scenario']['name']}",
            'teams': {
                'home': {
                    'name': home_team_data.name,
                    'formation': home_team_data.formation
                },
                'away': {
                    'name': away_team_data.name,
                    'formation': away_team_data.formation
                }
            },
            'pipeline_metadata': {
                'converged': pipeline_result['converged'],
                'iterations': pipeline_result['iterations'],
                'total_simulations': pipeline_result['metadata']['total_simulations'],
                'scenarios_count': len(pipeline_result['scenarios'])
            },
            'usage': {
                'total_tokens': 0,  # Pipeline doesn't track tokens (multiple AI calls)
                'processing_time': processing_time,
                'cost_usd': 0.0  # Local = 0
            },
            'match_context': match_context,
            'timestamp': datetime.utcnow().isoformat()
        }

        logger.info(f"Enriched simulation successful: {home_team} vs {away_team}")
        return True, result, None

    def simulate_with_progress_v2(
        self,
        home_team: str,
        away_team: str,
        match_context: Optional[Dict] = None
    ):
        """
        Run V2 Pipeline simulation with real-time SSE progress updates.

        NEW: Uses V2 Pipeline (Phase 1-7) with multi-scenario simulation

        Args:
            home_team: Home team name
            away_team: Away team name
            match_context: Optional match context

        Yields:
            SimulationEvent objects for SSE streaming
        """
        start_time = time.time()
        last_heartbeat = time.time()
        HEARTBEAT_INTERVAL = 15  # Send heartbeat every 15 seconds

        try:
            # Set default match context
            if match_context is None:
                match_context = {}

            # Event 1: Started
            yield SimulationEvent.started(home_team, away_team, match_context)

            # Event 2-3: Load home team
            yield SimulationEvent.loading_home_team(home_team)

            try:
                home_team_data = self.loader.load_team_data(home_team)
                yield SimulationEvent.home_team_loaded(
                    home_team,
                    len(home_team_data.lineup),
                    home_team_data.formation
                )
            except Exception as e:
                yield SimulationEvent.error(
                    f"Failed to load home team: {str(e)}",
                    stage='data_loading'
                )
                return

            # Event 4-5: Load away team
            yield SimulationEvent.loading_away_team(away_team)

            try:
                away_team_data = self.loader.load_team_data(away_team)
                yield SimulationEvent.away_team_loaded(
                    away_team,
                    len(away_team_data.lineup),
                    away_team_data.formation
                )
            except Exception as e:
                yield SimulationEvent.error(
                    f"Failed to load away team: {str(e)}",
                    stage='data_loading'
                )
                return

            # Event 6: V2 Pipeline Starting
            yield SimulationEvent(
                event_type='v2_pipeline_starting',
                data={
                    'message': 'Starting V2 Pipeline with multi-scenario simulation',
                    'engine': 'V2 Pipeline',
                    'phases': 7
                }
            )

            # Get pipeline
            from simulation.v2.simulation_pipeline import get_pipeline, PipelineConfig
            pipeline = get_pipeline(config=PipelineConfig(
                max_iterations=5,
                initial_runs=100,
                final_runs=3000,
                convergence_threshold=0.85
            ))

            # Storage for pipeline events
            pipeline_result = None
            pipeline_error = None

            # Event callback function
            def pipeline_event_callback(event_type: str, data: dict):
                # Convert pipeline events to SSE events
                yield SimulationEvent(
                    event_type=event_type,
                    data=data
                )

            # Run V2 Pipeline with real-time event streaming using queue
            try:
                # Create event queue for thread-safe communication
                event_queue = queue.Queue()
                pipeline_result = {'success': False, 'result': None, 'error': None}

                def collect_events_to_queue(event_type: str, data: dict):
                    """Callback that puts events into queue"""
                    event = SimulationEvent(event_type=event_type, data=data)
                    event_queue.put(event)

                def run_pipeline_in_thread():
                    """Run pipeline in separate thread"""
                    try:
                        success, result, error = pipeline.run_enriched(
                            home_team=home_team_data,
                            away_team=away_team_data,
                            match_context=match_context,
                            event_callback=collect_events_to_queue
                        )
                        pipeline_result['success'] = success
                        pipeline_result['result'] = result
                        pipeline_result['error'] = error
                    except Exception as e:
                        logger.error(f"Pipeline thread error: {str(e)}")
                        pipeline_result['success'] = False
                        pipeline_result['error'] = str(e)
                    finally:
                        # Signal completion with None
                        event_queue.put(None)

                # Start pipeline in separate thread
                pipeline_thread = threading.Thread(target=run_pipeline_in_thread)
                pipeline_thread.daemon = True
                pipeline_thread.start()

                # Yield events as they arrive from queue
                while True:
                    try:
                        # Check for heartbeat
                        if time.time() - last_heartbeat > HEARTBEAT_INTERVAL:
                            yield SimulationEvent(
                                event_type='heartbeat',
                                data={
                                    'message': 'Connection keepalive',
                                    'elapsed': round(time.time() - start_time, 1)
                                }
                            )
                            last_heartbeat = time.time()

                        # Get event from queue (timeout 0.5s to check heartbeat)
                        event = event_queue.get(timeout=0.5)

                        # None signals completion
                        if event is None:
                            break

                        # Yield the event
                        yield event

                    except queue.Empty:
                        # No event yet, continue (allows heartbeat check)
                        continue

                # Wait for thread to complete
                pipeline_thread.join(timeout=10)

                # Check pipeline result
                if not pipeline_result['success']:
                    yield SimulationEvent.error(
                        f"Pipeline failed: {pipeline_result['error']}",
                        stage='v2_pipeline'
                    )
                    return

            except Exception as e:
                logger.error(f"V2 Pipeline error: {str(e)}")
                yield SimulationEvent.error(
                    f"Pipeline execution error: {str(e)}",
                    stage='v2_pipeline'
                )
                return

            # Build final result from pipeline output
            processing_time = time.time() - start_time
            result_data = pipeline_result['result']  # Get result from pipeline_result dict
            report = result_data['report']
            prediction = report['prediction']

            final_result = {
                'success': True,
                'prediction': prediction['win_probabilities'],  # {home, draw, away}
                'predicted_score': f"{prediction['expected_goals']['home']:.0f}-{prediction['expected_goals']['away']:.0f}",
                'expected_goals': prediction['expected_goals'],
                'confidence': 'high' if pipeline_result['converged'] else 'medium',
                'analysis': {
                    'key_factors': [],
                    'dominant_scenario': report['dominant_scenario'],
                    'all_scenarios': report['all_scenarios'],
                    'tactical_insight': f"Simulation converged after {pipeline_result['iterations']} iterations."
                },
                'summary': f"{home_team} vs {away_team}: {report['dominant_scenario']['name']}",
                'teams': {
                    'home': {
                        'name': home_team_data.name,
                        'formation': home_team_data.formation
                    },
                    'away': {
                        'name': away_team_data.name,
                        'formation': away_team_data.formation
                    }
                },
                'pipeline_metadata': {
                    'converged': result_data['converged'],
                    'iterations': result_data['iterations'],
                    'total_simulations': result_data['metadata']['total_simulations'],
                    'scenarios_count': len(result_data['scenarios'])
                },
                'usage': {
                    'total_tokens': 0,  # V2 Pipeline doesn't track tokens
                    'processing_time': processing_time,
                    'cost_usd': 0.0
                },
                'match_context': match_context,
                'timestamp': datetime.utcnow().isoformat()
            }

            # Event: Completed
            total_time = time.time() - start_time
            yield SimulationEvent.completed(final_result, total_time)

        except Exception as e:
            logger.error(f"Unexpected error in simulate_with_progress_v2: {str(e)}")
            yield SimulationEvent.error(
                f"Unexpected error: {str(e)}",
                stage='unknown'
            )

    def simulate_with_progress(
        self,
        home_team: str,
        away_team: str,
        match_context: Optional[Dict] = None
    ):
        """
        Run enriched match simulation with real-time progress updates (SSE generator).

        ⚠️ LEGACY VERSION: Uses single AI call (OLD)
        ⚠️ For V2 Pipeline with SSE, use simulate_with_progress_v2() instead

        ⚠️ P0 FIX APPLIED:
        - ✅ Added: Heartbeat events every 15 seconds (prevents timeout)

        Args:
            home_team: Home team name
            away_team: Away team name
            match_context: Optional match context

        Yields:
            SimulationEvent objects for SSE streaming
        """
        start_time = time.time()
        last_heartbeat = time.time()
        HEARTBEAT_INTERVAL = 15  # ✅ P0 FIX #2: Send heartbeat every 15 seconds

        try:
            # Set default match context
            if match_context is None:
                match_context = {}

            # Event 1: Started
            yield SimulationEvent.started(home_team, away_team, match_context)

            # Event 2: Check AI health
            is_healthy, health_error = self.client.health_check()
            if not is_healthy:
                yield SimulationEvent.error(
                    f"AI not available: {health_error}",
                    stage='initialization'
                )
                return

            # Event 3: Load home team
            yield SimulationEvent.loading_home_team(home_team)

            try:
                home_team_data = self.loader.load_team_data(home_team)
                yield SimulationEvent.home_team_loaded(
                    home_team,
                    len(home_team_data.lineup),
                    home_team_data.formation
                )
            except Exception as e:
                yield SimulationEvent.error(
                    f"Failed to load home team: {str(e)}",
                    stage='data_loading'
                )
                return

            # Event 4: Load away team
            yield SimulationEvent.loading_away_team(away_team)

            try:
                away_team_data = self.loader.load_team_data(away_team)
                yield SimulationEvent.away_team_loaded(
                    away_team,
                    len(away_team_data.lineup),
                    away_team_data.formation
                )
            except Exception as e:
                yield SimulationEvent.error(
                    f"Failed to load away team: {str(e)}",
                    stage='data_loading'
                )
                return

            # Event 5: Build prompt
            yield SimulationEvent.building_prompt()

            # Generate prompts (to measure length)
            system_prompt = self.client._build_enriched_system_prompt()
            user_prompt = self.client._build_enriched_match_prompt(
                home_team=home_team_data,
                away_team=away_team_data,
                match_context=match_context
            )
            prompt_length = len(system_prompt) + len(user_prompt)

            yield SimulationEvent.prompt_ready(prompt_length)

            # Event 6: Start AI Simulation with Streaming
            model_info = self.client.get_model_info()
            yield SimulationEvent(
                event_type='ai_simulation_started',
                data={
                    'message': 'Starting AI-driven simulation with enriched domain data',
                    'engine': f"{model_info['provider']} AI Client",
                    'model': model_info['model']
                }
            )

            # Run AI streaming simulation
            result = None
            try:
                # Track progress
                token_count = 0
                match_events_count = 0

                for ai_event in self.client.simulate_match_enriched_stream(
                    home_team=home_team_data,
                    away_team=away_team_data,
                    match_context=match_context
                ):
                    # Heartbeat check
                    if time.time() - last_heartbeat > HEARTBEAT_INTERVAL:
                        yield SimulationEvent(
                            event_type='heartbeat',
                            data={
                                'message': 'Connection keepalive',
                                'elapsed': round(time.time() - start_time, 1),
                                'stage': 'ai_simulation',
                                'tokens_generated': token_count,
                                'match_events': match_events_count
                            }
                        )
                        last_heartbeat = time.time()

                    # Process AI streaming events
                    event_type = ai_event.get('type')

                    if event_type == 'token_progress':
                        # Token generation progress
                        token_count = ai_event.get('tokens_generated', 0)
                        yield SimulationEvent(
                            event_type='token_progress',
                            data={
                                'tokens_generated': token_count,
                                'estimated_total': ai_event.get('estimated_total', 2500),
                                'message': f"Generating simulation... ({token_count} tokens)"
                            }
                        )

                    elif event_type == 'match_event':
                        # Real AI-generated match event
                        match_events_count += 1
                        event_data = ai_event.get('event', {})
                        minute = event_data.get('minute', 0)
                        evt_type = event_data.get('event_type', 'event')
                        description = event_data.get('description', '')

                        # Stream the match event
                        yield SimulationEvent.match_event(
                            minute=minute,
                            event_type=evt_type,
                            description=description
                        )

                    elif event_type == 'final_prediction':
                        # AI simulation complete with final prediction
                        prediction_data = ai_event.get('prediction', {})
                        tokens_generated = ai_event.get('tokens_generated', token_count)

                        # Build final result
                        result = {
                            'success': True,
                            'prediction': prediction_data.get('prediction', {}),
                            'analysis': prediction_data.get('analysis', {}),
                            'summary': prediction_data.get('summary', ''),
                            'teams': {
                                'home': {
                                    'name': home_team_data.name,
                                    'formation': home_team_data.formation
                                },
                                'away': {
                                    'name': away_team_data.name,
                                    'formation': away_team_data.formation
                                }
                            },
                            'usage': {
                                'total_tokens': tokens_generated,
                                'input_tokens': tokens_generated // 3,  # Rough estimate
                                'output_tokens': tokens_generated * 2 // 3,  # Rough estimate
                                'processing_time': time.time() - start_time,
                                'cost_usd': 0.0  # Cost tracking not implemented
                            },
                            'match_context': match_context,
                            'timestamp': datetime.utcnow().isoformat(),
                            'metadata': prediction_data.get('metadata', {}),
                            'match_events_count': match_events_count
                        }

                        yield SimulationEvent(
                            event_type='ai_simulation_complete',
                            data={
                                'message': 'AI simulation complete',
                                'tokens_generated': tokens_generated,
                                'match_events': match_events_count
                            }
                        )

                    elif event_type == 'error':
                        # AI error
                        error_msg = ai_event.get('error', 'Unknown AI error')
                        logger.error(f"AI simulation error: {error_msg}")
                        yield SimulationEvent.error(
                            f"AI simulation failed: {error_msg}",
                            stage='ai_simulation'
                        )
                        return

            except Exception as e:
                logger.error(f"AI simulation error: {str(e)}")
                yield SimulationEvent.error(
                    f"AI simulation failed: {str(e)}",
                    stage='ai_simulation'
                )
                return

            # Verify result
            if result is None:
                yield SimulationEvent.error(
                    "AI simulation did not return final prediction",
                    stage='ai_simulation'
                )
                return

            # Event 7: Parsing complete
            yield SimulationEvent.result_parsed()

            # Event 8: Completed
            total_time = time.time() - start_time
            yield SimulationEvent.completed(result, total_time)

        except Exception as e:
            logger.error(f"Unexpected error in simulate_with_progress: {str(e)}")
            yield SimulationEvent.error(
                f"Unexpected error: {str(e)}",
                stage='unknown'
            )

    def check_team_readiness(self, team_name: str) -> Tuple[bool, Dict]:
        """
        Check if team data is ready for enriched simulation.

        Args:
            team_name: Team name to check

        Returns:
            Tuple of (ready: bool, details: dict)

            details format:
            {
                'ready': True/False,
                'team_name': '...',
                'completed': {
                    'lineup': True/False,
                    'formation': True/False,
                    'tactics': True/False,
                    'ratings': True/False,
                    'commentary': True/False
                },
                'missing': ['lineup', 'formation', ...],
                'player_count': 11,
                'formation': '4-3-3'
            }
        """
        try:
            team_data = self.loader.load_team_data(team_name)

            # Check completeness
            completed = {
                'lineup': len(team_data.lineup) == 11,
                'formation': bool(team_data.formation),
                'tactics': team_data.tactics is not None,
                'ratings': len(team_data.lineup) > 0 and all(
                    player.ratings for player in team_data.lineup.values()
                ),
                'commentary': team_data.team_strategy_commentary is not None
            }

            missing = [key for key, value in completed.items() if not value]
            ready = len(missing) == 0

            details = {
                'ready': ready,
                'team_name': team_name,
                'completed': completed,
                'missing': missing,
                'player_count': len(team_data.lineup),
                'formation': team_data.formation
            }

            return ready, details

        except FileNotFoundError:
            return False, {
                'ready': False,
                'team_name': team_name,
                'error': 'Team not found',
                'completed': {},
                'missing': ['all_data']
            }
        except Exception as e:
            return False, {
                'ready': False,
                'team_name': team_name,
                'error': str(e),
                'completed': {},
                'missing': ['unknown']
            }


# Global service instance
_enriched_simulation_service = None


def get_enriched_simulation_service() -> EnrichedSimulationService:
    """
    Get global enriched simulation service instance (singleton).

    Returns:
        EnrichedSimulationService instance
    """
    global _enriched_simulation_service

    if _enriched_simulation_service is None:
        _enriched_simulation_service = EnrichedSimulationService()

    return _enriched_simulation_service


def reset_enriched_simulation_service():
    """Reset global service instance (useful for testing)."""
    global _enriched_simulation_service
    _enriched_simulation_service = None
