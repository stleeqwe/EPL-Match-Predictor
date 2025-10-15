"""
Tactics Framework - 축구 전술 분석 및 예측 시스템

독립적인 전술 프레임워크 모듈:
- 포메이션별 수비/공격 효율성 분석
- 득점 경로 분류 및 차단률 계산
- EPL 데이터 기반 전술 예측 모델

기존 프로젝트와 독립적으로 구축하되, 통합 인터페이스 제공
"""

__version__ = "1.0.0"
__author__ = "EPL Match Predictor Team"

from .core.formations import FormationSystem
from .models.tactics_model import TacticalSetup
from .analyzer.effectiveness_calculator import EffectivenessCalculator

__all__ = [
    'FormationSystem',
    'TacticalSetup',
    'EffectivenessCalculator'
]
