"""
Simulation v2.0 - AI-Guided Iterative Refinement (Accurate Implementation)

정확히 설계 문서대로 구현:
EPL_AI_Simulation_System_Design_v2.md

핵심 특징:
- 분 단위(90분) 이벤트 기반 시뮬레이션
- 5-7개 다중 시나리오 생성
- 이벤트 시퀀스 (minute_range + probability_boost)
- 서사 일치율 직접 계산
- 7단계 파이프라인
"""

__version__ = '2.0.0-accurate'

# Export core components
from .scenario import Scenario, ScenarioEvent, EventType, create_example_scenario
from .scenario_guide import ScenarioGuide
from .event_simulation_engine import (
    EventBasedSimulationEngine,
    EventProbabilityCalculator,
    EventSampler,
    MatchParameters,
    MatchContext,
    create_match_parameters,
    EPL_BASELINE
)

__all__ = [
    # Data structures
    'Scenario',
    'ScenarioEvent',
    'EventType',
    'create_example_scenario',

    # Scenario guide
    'ScenarioGuide',

    # Simulation engine
    'EventBasedSimulationEngine',
    'EventProbabilityCalculator',
    'EventSampler',
    'MatchParameters',
    'MatchContext',
    'create_match_parameters',
    'EPL_BASELINE',
]
