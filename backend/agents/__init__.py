# -*- coding: utf-8 -*-
"""
Agent Behavior System
Hybrid architecture: Rule-based (80%) + Haiku LLM (20%)

Components:
- actions: Action definitions and helpers
- simple_agent: Rule-based decision tree (80% coverage)
- position_behaviors: Position-specific behaviors (GK, CB, FB, DM, CM, CAM, WG, ST)
- tactical_ai: Haiku LLM integration (20% complex decisions)
- decision_cache: Caching to reduce LLM calls by 50%
"""

from .actions import Action, ActionType, calculate_shot_direction, calculate_pass_power, is_in_shooting_range
from .simple_agent import SimpleAgent, PlayerGameState, GameContext
from .position_behaviors import PositionBehaviors, get_position_action
from .tactical_ai import TacticalDecisionMaker, TacticalDecision, create_tactical_ai
from .decision_cache import DecisionCache, CachedDecision, create_situation_dict

__all__ = [
    # Actions
    'Action',
    'ActionType',
    'calculate_shot_direction',
    'calculate_pass_power',
    'is_in_shooting_range',

    # Simple Agent
    'SimpleAgent',
    'PlayerGameState',
    'GameContext',

    # Position Behaviors
    'PositionBehaviors',
    'get_position_action',

    # Tactical AI
    'TacticalDecisionMaker',
    'TacticalDecision',
    'create_tactical_ai',

    # Decision Cache
    'DecisionCache',
    'CachedDecision',
    'create_situation_dict'
]
