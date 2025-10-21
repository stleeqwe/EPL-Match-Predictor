"""
Scenario Generation V3

수학적 모델 기반 시나리오 생성
NO Templates, NO EPL baseline forcing
"""

from .math_based_generator import (
    MathBasedScenarioGenerator,
    GeneratedScenarioResult
)

# Re-export existing scenario data models
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
from simulation.v2.scenario import Scenario, ScenarioEvent, EventType

__all__ = [
    'MathBasedScenarioGenerator',
    'GeneratedScenarioResult',
    'Scenario',
    'ScenarioEvent',
    'EventType',
]
