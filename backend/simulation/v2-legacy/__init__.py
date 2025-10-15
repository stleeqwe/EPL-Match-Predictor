"""
Simulation v2.0 - AI-Guided Iterative Refinement

v2.0 아키텍처:
AI 파라미터 생성 → 시뮬 100회 → AI 분석/조정 → 재시뮬 → 수렴 체크 → 반복 → 최종 3000회

핵심 컴포넌트:
- AI Parameter Generator: 전술 분석 및 파라미터 생성
- Iterative Engine: 파라미터 기반 시뮬레이션 (100/3000회)
- Bias Detector: 통계적 편향 감지
- Narrative Analyzer: 서사 일치율 분석
- Convergence Judge: 수렴 판정
- Parameter Adjuster: 파라미터 조정
- Match Simulator v2: 전체 워크플로우 조율
"""

from simulation.v2.match_simulator_v2 import MatchSimulatorV2, get_match_simulator_v2
from simulation.v2.ai_parameter_generator import AIParameterGenerator, get_parameter_generator
from simulation.v2.iterative_engine import IterativeSimulationEngine, get_iterative_engine
from simulation.v2.bias_detector import BiasDetector, get_bias_detector
from simulation.v2.narrative_analyzer import NarrativeAnalyzer, get_narrative_analyzer
from simulation.v2.convergence_judge import ConvergenceJudge, get_convergence_judge
from simulation.v2.parameter_adjuster import ParameterAdjuster, get_parameter_adjuster

__version__ = '2.0.0'

__all__ = [
    'MatchSimulatorV2',
    'get_match_simulator_v2',
    'AIParameterGenerator',
    'get_parameter_generator',
    'IterativeSimulationEngine',
    'get_iterative_engine',
    'BiasDetector',
    'get_bias_detector',
    'NarrativeAnalyzer',
    'get_narrative_analyzer',
    'ConvergenceJudge',
    'get_convergence_judge',
    'ParameterAdjuster',
    'get_parameter_adjuster'
]
