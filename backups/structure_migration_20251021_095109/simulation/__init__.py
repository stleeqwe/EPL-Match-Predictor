"""
Simulation Module
Statistical match simulation with AI integration

v2.0 정확 구현: simulation.v2
Legacy 구현: simulation.legacy
"""

# Legacy imports for backward compatibility
try:
    from .legacy.statistical_engine import StatisticalMatchEngine
    from .legacy.match_simulator import MatchSimulator, get_match_simulator, reset_match_simulator

    __all__ = [
        'StatisticalMatchEngine',
        'MatchSimulator',
        'get_match_simulator',
        'reset_match_simulator'
    ]
except ImportError:
    # Legacy files not available
    __all__ = []
