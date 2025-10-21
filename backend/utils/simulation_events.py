"""
Simulation Event Types for SSE Streaming
실시간 시뮬레이션 진행 상태 이벤트 정의
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional
from datetime import datetime
import json


class SimulationEventType:
    """시뮬레이션 진행 상태 이벤트 타입"""

    # 시작/완료
    STARTED = "started"
    COMPLETED = "completed"
    ERROR = "error"

    # 데이터 로딩
    LOADING_HOME_TEAM = "loading_home_team"
    HOME_TEAM_LOADED = "home_team_loaded"
    LOADING_AWAY_TEAM = "loading_away_team"
    AWAY_TEAM_LOADED = "away_team_loaded"

    # 프롬프트 생성
    BUILDING_PROMPT = "building_prompt"
    PROMPT_READY = "prompt_ready"

    # AI 분석 (Legacy)
    AI_STARTED = "ai_started"
    AI_GENERATING = "ai_generating"  # 토큰 생성 중 (주기적)
    AI_COMPLETED = "ai_completed"

    # 결과 파싱
    PARSING_RESULT = "parsing_result"
    RESULT_PARSED = "result_parsed"

    # 경기 이벤트 (실시간 코멘터리)
    MATCH_EVENT = "match_event"

    # V2 Pipeline Phase Events
    PHASE1_STARTED = "phase1_started"
    PHASE1_COMPLETE = "phase1_complete"
    PHASE1_ERROR = "phase1_error"

    PHASE2_5_STARTED = "phase2_5_started"
    PHASE2_VALIDATING = "phase2_validating"
    PHASE2_COMPLETE = "phase2_complete"

    PHASE3_ANALYZING = "phase3_analyzing"
    PHASE3_COMPLETE = "phase3_complete"
    PHASE3_WARNING = "phase3_warning"

    PHASE4_ADJUSTING = "phase4_adjusting"

    CONVERGENCE_CHECK = "convergence_check"
    CONVERGENCE_REACHED = "convergence_reached"

    ITERATION_STARTED = "iteration_started"
    ITERATION_COMPLETE = "iteration_complete"
    MAX_ITERATIONS_REACHED = "max_iterations_reached"

    PHASE6_STARTED = "phase6_started"
    PHASE6_PROGRESS = "phase6_progress"
    PHASE6_COMPLETE = "phase6_complete"

    PHASE7_STARTED = "phase7_started"
    PHASE7_COMPLETE = "phase7_complete"


@dataclass
class SimulationEvent:
    """시뮬레이션 이벤트 데이터 클래스"""

    event_type: str
    data: Dict[str, Any]
    timestamp: Optional[str] = None

    def __post_init__(self):
        """타임스탬프 자동 설정"""
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()

    def to_sse_format(self) -> str:
        """
        SSE 형식으로 변환

        Returns:
            SSE formatted string: "event: {type}\ndata: {json_data}\n\n"
        """
        json_data = json.dumps({
            'timestamp': self.timestamp,
            **self.data
        }, ensure_ascii=False)

        return f"event: {self.event_type}\ndata: {json_data}\n\n"

    @staticmethod
    def started(home_team: str, away_team: str, match_context: Dict = None) -> 'SimulationEvent':
        """시뮬레이션 시작 이벤트"""
        return SimulationEvent(
            event_type=SimulationEventType.STARTED,
            data={
                'message': f'{home_team} vs {away_team} 시뮬레이션 시작',
                'home_team': home_team,
                'away_team': away_team,
                'match_context': match_context or {}
            }
        )

    @staticmethod
    def loading_home_team(team_name: str) -> 'SimulationEvent':
        """홈팀 데이터 로딩 시작"""
        return SimulationEvent(
            event_type=SimulationEventType.LOADING_HOME_TEAM,
            data={
                'message': f'{team_name} 데이터 로딩 중...',
                'team': team_name,
                'stage': 'data_loading'
            }
        )

    @staticmethod
    def home_team_loaded(team_name: str, player_count: int, formation: str) -> 'SimulationEvent':
        """홈팀 데이터 로딩 완료"""
        return SimulationEvent(
            event_type=SimulationEventType.HOME_TEAM_LOADED,
            data={
                'message': f'{team_name} 데이터 로딩 완료 ({player_count}명, {formation})',
                'team': team_name,
                'player_count': player_count,
                'formation': formation,
                'stage': 'data_loading'
            }
        )

    @staticmethod
    def loading_away_team(team_name: str) -> 'SimulationEvent':
        """원정팀 데이터 로딩 시작"""
        return SimulationEvent(
            event_type=SimulationEventType.LOADING_AWAY_TEAM,
            data={
                'message': f'{team_name} 데이터 로딩 중...',
                'team': team_name,
                'stage': 'data_loading'
            }
        )

    @staticmethod
    def away_team_loaded(team_name: str, player_count: int, formation: str) -> 'SimulationEvent':
        """원정팀 데이터 로딩 완료"""
        return SimulationEvent(
            event_type=SimulationEventType.AWAY_TEAM_LOADED,
            data={
                'message': f'{team_name} 데이터 로딩 완료 ({player_count}명, {formation})',
                'team': team_name,
                'player_count': player_count,
                'formation': formation,
                'stage': 'data_loading'
            }
        )

    @staticmethod
    def building_prompt() -> 'SimulationEvent':
        """프롬프트 생성 시작"""
        return SimulationEvent(
            event_type=SimulationEventType.BUILDING_PROMPT,
            data={
                'message': 'AI 프롬프트 생성 중...',
                'stage': 'prompt_building'
            }
        )

    @staticmethod
    def prompt_ready(prompt_length: int) -> 'SimulationEvent':
        """프롬프트 생성 완료"""
        return SimulationEvent(
            event_type=SimulationEventType.PROMPT_READY,
            data={
                'message': f'AI 프롬프트 준비 완료 ({prompt_length:,} 문자)',
                'prompt_length': prompt_length,
                'stage': 'prompt_building'
            }
        )

    @staticmethod
    def ai_started(model: str) -> 'SimulationEvent':
        """AI 분석 시작"""
        return SimulationEvent(
            event_type=SimulationEventType.AI_STARTED,
            data={
                'message': f'AI 분석 시작 (모델: {model})',
                'model': model,
                'stage': 'ai_analysis'
            }
        )

    @staticmethod
    def ai_generating(tokens_generated: int, estimated_total: int = 2000) -> 'SimulationEvent':
        """AI 토큰 생성 중 (주기적 업데이트)"""
        progress = min(tokens_generated / estimated_total, 1.0) if estimated_total > 0 else 0

        return SimulationEvent(
            event_type=SimulationEventType.AI_GENERATING,
            data={
                'message': f'AI 분석 진행 중... ({tokens_generated:,} / {estimated_total:,} 토큰)',
                'tokens': tokens_generated,
                'estimated_total': estimated_total,
                'progress': round(progress, 3),
                'stage': 'ai_analysis'
            }
        )

    @staticmethod
    def ai_completed(total_tokens: int, processing_time: float) -> 'SimulationEvent':
        """AI 분석 완료"""
        return SimulationEvent(
            event_type=SimulationEventType.AI_COMPLETED,
            data={
                'message': f'AI 분석 완료 ({total_tokens:,} 토큰, {processing_time:.1f}초)',
                'total_tokens': total_tokens,
                'processing_time': processing_time,
                'stage': 'ai_analysis'
            }
        )

    @staticmethod
    def parsing_result() -> 'SimulationEvent':
        """결과 파싱 시작"""
        return SimulationEvent(
            event_type=SimulationEventType.PARSING_RESULT,
            data={
                'message': 'AI 응답 파싱 중...',
                'stage': 'result_parsing'
            }
        )

    @staticmethod
    def result_parsed() -> 'SimulationEvent':
        """결과 파싱 완료"""
        return SimulationEvent(
            event_type=SimulationEventType.RESULT_PARSED,
            data={
                'message': '결과 파싱 완료',
                'stage': 'result_parsing'
            }
        )

    @staticmethod
    def completed(result: Dict[str, Any], total_time: float) -> 'SimulationEvent':
        """시뮬레이션 완료"""
        return SimulationEvent(
            event_type=SimulationEventType.COMPLETED,
            data={
                'message': f'시뮬레이션 완료 (총 {total_time:.1f}초)',
                'total_time': total_time,
                'result': result
            }
        )

    @staticmethod
    def match_event(
        minute: int,
        event_type: str,
        description: str,
        team: Optional[str] = None,
        player: Optional[str] = None
    ) -> 'SimulationEvent':
        """경기 이벤트 (실시간 코멘터리)"""
        return SimulationEvent(
            event_type=SimulationEventType.MATCH_EVENT,
            data={
                'minute': minute,
                'event_type': event_type,  # 'possession', 'shot', 'goal', 'save', 'tackle', etc.
                'description': description,
                'team': team,
                'player': player,
                'stage': 'match_simulation'
            }
        )

    @staticmethod
    def error(error_message: str, stage: str = 'unknown') -> 'SimulationEvent':
        """에러 발생"""
        return SimulationEvent(
            event_type=SimulationEventType.ERROR,
            data={
                'message': f'에러 발생: {error_message}',
                'error': error_message,
                'stage': stage
            }
        )

    @staticmethod
    def info(message: str, stage: str = 'info', data: Dict = None, **kwargs) -> 'SimulationEvent':
        """일반 정보 메시지"""
        event_data = {
            'message': message,
            'stage': stage
        }
        if data:
            event_data.update(data)
        event_data.update(kwargs)
        return SimulationEvent(
            event_type='info',
            data=event_data
        )

    @staticmethod
    def success(message: str, stage: str = 'success', data: Dict = None) -> 'SimulationEvent':
        """성공 메시지"""
        event_data = {
            'message': message,
            'stage': stage
        }
        if data:
            event_data.update(data)
        return SimulationEvent(
            event_type='success',
            data=event_data
        )
