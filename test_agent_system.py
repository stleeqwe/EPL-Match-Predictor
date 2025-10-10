#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent System Test Suite
Validates all agent components without requiring pytest

Tests:
1. Actions - Creation and serialization
2. Simple Agent - Rule-based decisions
3. Position Behaviors - Position-specific logic
4. Decision Cache - Caching functionality
5. Integration - Full agent system workflow
"""

import sys
import time
import numpy as np
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / 'backend'))

# Import agent components
from agents.actions import (
    Action, ActionType,
    calculate_shot_direction, calculate_pass_power, is_in_shooting_range
)
from agents.simple_agent import SimpleAgent, PlayerGameState, GameContext
from agents.position_behaviors import PositionBehaviors, get_position_action
from agents.decision_cache import DecisionCache, create_situation_dict

from physics.constants import FIELD_X_MIN, FIELD_X_MAX


# =============================================================================
# TEST FIXTURES
# =============================================================================

def create_test_player(
    player_id='test_player',
    position=(0, 0),
    role='CM',
    has_ball=False,
    team_id='home'
):
    """Create test player state"""
    return PlayerGameState(
        player_id=player_id,
        position=np.array(position),
        velocity=np.zeros(2),
        stamina=80.0,
        has_ball=has_ball,
        team_id=team_id,
        role=role,
        attributes={
            'pace': 75,
            'shooting': 70,
            'passing': 80,
            'dribbling': 75,
            'defending': 60,
            'physical': 70
        }
    )


def create_test_context(
    ball_position=(0, 0, 0.5),
    is_attacking_left=False,
    teammates=None,
    opponents=None
):
    """Create test game context"""
    return GameContext(
        ball_position=np.array(ball_position),
        ball_velocity=np.zeros(3),
        teammates=teammates or [],
        opponents=opponents or [],
        score={'home': 0, 'away': 0},
        time_remaining=45.0,
        is_attacking_left=is_attacking_left
    )


# =============================================================================
# TEST 1: ACTIONS
# =============================================================================

def test_action_creation():
    """Test 1: Action creation and serialization"""
    print("\n[Test 1] Action Creation")

    # Test shoot action
    shoot_action = Action.create_shoot(
        target_position=np.array([52.5, 0.0]),
        power=80.0
    )

    assert shoot_action.action_type == ActionType.SHOOT
    assert shoot_action.power == 80.0
    print(f"  Shoot action: {shoot_action.action_type.value}, power={shoot_action.power}")

    # Test pass action
    pass_action = Action.create_pass(
        target_player_id='teammate_1',
        target_position=np.array([10.0, 5.0]),
        power=60.0
    )

    assert pass_action.action_type == ActionType.PASS
    assert pass_action.target_player_id == 'teammate_1'
    print(f"  Pass action: to {pass_action.target_player_id}, power={pass_action.power}")

    # Test serialization
    action_dict = shoot_action.to_dict()
    assert 'action_type' in action_dict
    assert action_dict['action_type'] == 'shoot'
    print(f"  Serialization works: {list(action_dict.keys())}")

    print("  ✓ Action creation and serialization passed")
    return True


def test_action_helpers():
    """Test 2: Action helper functions"""
    print("\n[Test 2] Action Helpers")

    # Test shooting range
    player_pos = np.array([30.0, 0.0])
    goal_pos = np.array([52.5, 0.0])

    in_range, quality = is_in_shooting_range(player_pos, goal_pos)
    print(f"  Distance: {np.linalg.norm(goal_pos - player_pos):.1f}m")
    print(f"  In range: {in_range}, quality: {quality:.2f}")

    assert in_range is True
    assert 0 <= quality <= 1

    # Test pass power calculation
    power_short = calculate_pass_power(10.0, 'short')
    power_medium = calculate_pass_power(20.0, 'medium')
    power_long = calculate_pass_power(40.0, 'long')

    print(f"  Pass power - short(10m): {power_short:.0f}, medium(20m): {power_medium:.0f}, long(40m): {power_long:.0f}")

    assert power_short < power_medium < power_long

    # Test shot direction
    direction = calculate_shot_direction(
        player_position=np.array([0.0, 0.0]),
        goal_position=np.array([52.5, 0.0]),
        accuracy=0.9
    )

    assert np.linalg.norm(direction) > 0.9  # Normalized
    print(f"  Shot direction: {direction}")

    print("  ✓ Action helpers passed")
    return True


# =============================================================================
# TEST 3: SIMPLE AGENT
# =============================================================================

def test_simple_agent_with_ball():
    """Test 3: Simple agent with ball"""
    print("\n[Test 3] Simple Agent - With Ball")

    agent = SimpleAgent()

    # Player with ball near goal
    player = create_test_player(
        position=(40.0, 0.0),
        has_ball=True,
        role='ST'
    )

    context = create_test_context(
        ball_position=(40.0, 0.0, 0.5),
        is_attacking_left=False  # Attacking right goal at x=52.5
    )

    # Agent should decide to shoot (in range, clear path)
    action = agent.decide_action(player, context)

    print(f"  Player at (40, 0), has ball, near goal")
    print(f"  Decision: {action.action_type.value}")

    assert action is not None
    # Should shoot or dribble toward goal
    assert action.action_type in [ActionType.SHOOT, ActionType.DRIBBLE]

    print("  ✓ Simple agent with ball passed")
    return True


def test_simple_agent_without_ball():
    """Test 4: Simple agent without ball"""
    print("\n[Test 4] Simple Agent - Without Ball")

    agent = SimpleAgent()

    # Player without ball, ball nearby
    player = create_test_player(
        position=(0.0, 0.0),
        has_ball=False,
        role='CM'
    )

    context = create_test_context(
        ball_position=(5.0, 5.0, 0.5)
    )

    action = agent.decide_action(player, context)

    print(f"  Player at (0, 0), no ball, ball at (5, 5)")
    print(f"  Decision: {action.action_type.value}")

    assert action is not None
    # Should chase ball or move to position
    assert action.action_type in [ActionType.CHASE_BALL, ActionType.MOVE_TO_POSITION]

    print("  ✓ Simple agent without ball passed")
    return True


def test_simple_agent_passing():
    """Test 5: Simple agent passing decision"""
    print("\n[Test 5] Simple Agent - Passing Decision")

    agent = SimpleAgent()

    # Player with ball and open teammates
    player = create_test_player(
        position=(20.0, 0.0),
        has_ball=True,
        role='CM'
    )

    # Add open teammates
    teammate1 = create_test_player('teammate1', position=(30.0, 5.0), role='ST')
    teammate2 = create_test_player('teammate2', position=(25.0, -5.0), role='WG')

    context = create_test_context(
        ball_position=(20.0, 0.0, 0.5),
        teammates=[teammate1, teammate2],
        is_attacking_left=False
    )

    action = agent.decide_action(player, context)

    print(f"  Player at (20, 0), has ball, 2 teammates open")
    print(f"  Decision: {action.action_type.value}")

    if action.action_type == ActionType.PASS:
        print(f"  Target: {action.target_player_id}")

    # Should pass or shoot or dribble
    assert action.action_type in [ActionType.PASS, ActionType.SHOOT, ActionType.DRIBBLE]

    print("  ✓ Simple agent passing decision passed")
    return True


# =============================================================================
# TEST 6: POSITION BEHAVIORS
# =============================================================================

def test_goalkeeper_behavior():
    """Test 6: Goalkeeper behavior"""
    print("\n[Test 6] Goalkeeper Behavior")

    # Goalkeeper near own goal
    gk = create_test_player(
        player_id='gk',
        position=(-50.0, 0.0),
        role='GK',
        team_id='home'
    )

    # Ball approaching goal
    context = create_test_context(
        ball_position=(-45.0, 0.0, 1.0),
        is_attacking_left=True  # Home team defends left goal
    )

    action = PositionBehaviors.goalkeeper_behavior(gk, context)

    print(f"  GK at (-50, 0), ball at (-45, 0)")
    print(f"  Decision: {action.action_type.value if action else 'None'}")

    assert action is not None

    print("  ✓ Goalkeeper behavior passed")
    return True


def test_striker_behavior():
    """Test 7: Striker behavior"""
    print("\n[Test 7] Striker Behavior")

    # Striker with ball near goal
    striker = create_test_player(
        player_id='st',
        position=(45.0, 0.0),
        role='ST',
        has_ball=True
    )

    context = create_test_context(
        ball_position=(45.0, 0.0, 0.5),
        is_attacking_left=False  # Attacking right goal
    )

    action = PositionBehaviors.striker_behavior(striker, context)

    print(f"  Striker at (45, 0), has ball, near goal")
    print(f"  Decision: {action.action_type.value if action else 'None'}")

    assert action is not None
    # Striker near goal with ball should shoot
    assert action.action_type == ActionType.SHOOT

    print("  ✓ Striker behavior passed")
    return True


def test_position_dispatcher():
    """Test 8: Position action dispatcher"""
    print("\n[Test 8] Position Action Dispatcher")

    # Test for each position
    positions = ['GK', 'CB', 'FB', 'DM', 'CM', 'CAM', 'WG', 'ST']

    for role in positions:
        player = create_test_player(
            position=(0.0, 0.0),
            role=role
        )

        context = create_test_context()

        action = get_position_action(player, context)

        print(f"  {role}: {action.action_type.value if action else 'fallback to SimpleAgent'}")

    print("  ✓ Position dispatcher passed")
    return True


# =============================================================================
# TEST 9: DECISION CACHE
# =============================================================================

def test_decision_cache():
    """Test 9: Decision cache functionality"""
    print("\n[Test 9] Decision Cache")

    cache = DecisionCache(ttl=10.0)

    # Create test situation
    situation = create_situation_dict(
        player_position=(20.0, 5.0),
        ball_position=(20.0, 5.0, 0.5),
        score={'home': 0, 'away': 0},
        decision_type='pass'
    )

    # First call - should miss
    result = cache.get(situation)
    assert result is None
    print(f"  First call: MISS (expected)")

    # Store decision
    test_action = Action.create_pass('teammate1', np.array([30.0, 5.0]), 60.0)
    cache.put(situation, test_action)
    print(f"  Stored decision in cache")

    # Second call - should hit
    result = cache.get(situation)
    assert result is not None
    assert result.target_player_id == 'teammate1'
    print(f"  Second call: HIT (cached)")

    # Check statistics
    stats = cache.get_statistics()
    print(f"  Hit rate: {stats['hit_rate']:.1%}")
    print(f"  Cache size: {stats['current_size']}")

    assert stats['hits'] == 1
    assert stats['misses'] == 1
    assert stats['hit_rate'] == 0.5

    print("  ✓ Decision cache passed")
    return True


def test_cache_expiration():
    """Test 10: Cache expiration"""
    print("\n[Test 10] Cache Expiration")

    cache = DecisionCache(ttl=1.0)  # 1 second TTL

    situation = create_situation_dict(
        player_position=(0.0, 0.0),
        ball_position=(0.0, 0.0, 0.5),
        score={'home': 0, 'away': 0},
        decision_type='move'
    )

    # Store decision
    action = Action.create_idle()
    cache.put(situation, action)

    # Should hit immediately
    result = cache.get(situation)
    assert result is not None
    print(f"  Immediate: HIT")

    # Wait for expiration
    print(f"  Waiting 1.5 seconds for expiration...")
    time.sleep(1.5)

    # Should miss after expiration
    result = cache.get(situation)
    assert result is None
    print(f"  After 1.5s: MISS (expired)")

    print("  ✓ Cache expiration passed")
    return True


def test_cache_lru_eviction():
    """Test 11: Cache LRU eviction"""
    print("\n[Test 11] Cache LRU Eviction")

    cache = DecisionCache(ttl=60.0, max_size=3)

    # Add 4 entries (should evict oldest)
    for i in range(4):
        situation = create_situation_dict(
            player_position=(i, i),
            ball_position=(i, i, 0.5),
            score={'home': 0, 'away': 0},
            decision_type=f'action_{i}'
        )
        cache.put(situation, Action.create_idle())
        print(f"  Added entry {i+1}/4")

    stats = cache.get_statistics()
    print(f"  Cache size: {stats['current_size']} (max: {stats['max_size']})")
    print(f"  Evictions: {stats['evictions']}")

    assert stats['current_size'] == 3
    assert stats['evictions'] == 1

    print("  ✓ Cache LRU eviction passed")
    return True


# =============================================================================
# TEST 12: INTEGRATION
# =============================================================================

def test_full_agent_integration():
    """Test 12: Full agent system integration"""
    print("\n[Test 12] Full Agent Integration")

    # Create agents
    simple_agent = SimpleAgent()
    cache = DecisionCache()

    # Simulate multiple decisions
    num_decisions = 10
    print(f"  Simulating {num_decisions} decisions...")

    for i in range(num_decisions):
        # Create player and context
        player = create_test_player(
            position=(i * 5, 0),
            has_ball=(i % 2 == 0)
        )

        context = create_test_context(
            ball_position=(i * 5, 0, 0.5)
        )

        # Try cache first
        situation = create_situation_dict(
            player_position=tuple(player.position),
            ball_position=tuple(context.ball_position),
            score=context.score,
            decision_type='agent_decision'
        )

        cached = cache.get(situation)

        if cached is None:
            # Use agent
            action = simple_agent.decide_action(player, context)
            cache.put(situation, action)
        else:
            action = cached

        assert action is not None

    # Check cache performance
    stats = cache.get_statistics()
    print(f"  Cache stats:")
    print(f"    Total requests: {stats['total_requests']}")
    print(f"    Hits: {stats['hits']}")
    print(f"    Misses: {stats['misses']}")
    print(f"    Hit rate: {stats['hit_rate']:.1%}")

    print("  ✓ Full agent integration passed")
    return True


# =============================================================================
# PERFORMANCE TEST
# =============================================================================

def test_agent_performance():
    """Test 13: Agent decision performance"""
    print("\n[Test 13] Agent Performance")

    agent = SimpleAgent()

    # Create player and context
    player = create_test_player(position=(20.0, 0.0), has_ball=True)
    teammate1 = create_test_player('t1', position=(30.0, 5.0))
    teammate2 = create_test_player('t2', position=(35.0, -5.0))

    context = create_test_context(
        ball_position=(20.0, 0.0, 0.5),
        teammates=[teammate1, teammate2]
    )

    # Time 1000 decisions
    num_decisions = 1000
    start_time = time.time()

    for i in range(num_decisions):
        action = agent.decide_action(player, context)

    elapsed = time.time() - start_time
    avg_time_ms = (elapsed / num_decisions) * 1000

    print(f"  {num_decisions} decisions in {elapsed:.3f}s")
    print(f"  Average: {avg_time_ms:.3f}ms per decision")
    print(f"  Target: < 1ms ({'✓ PASS' if avg_time_ms < 1.0 else '✗ FAIL'})")

    assert avg_time_ms < 5.0  # Should be < 5ms (very generous)

    print("  ✓ Agent performance passed")
    return True


# =============================================================================
# MAIN TEST RUNNER
# =============================================================================

def run_all_tests():
    """Run all agent system tests"""
    print("=" * 70)
    print("Agent System Test Suite")
    print("=" * 70)

    tests = [
        # Actions
        ("Action Creation", test_action_creation),
        ("Action Helpers", test_action_helpers),

        # Simple Agent
        ("Simple Agent - With Ball", test_simple_agent_with_ball),
        ("Simple Agent - Without Ball", test_simple_agent_without_ball),
        ("Simple Agent - Passing", test_simple_agent_passing),

        # Position Behaviors
        ("Goalkeeper Behavior", test_goalkeeper_behavior),
        ("Striker Behavior", test_striker_behavior),
        ("Position Dispatcher", test_position_dispatcher),

        # Decision Cache
        ("Decision Cache", test_decision_cache),
        ("Cache Expiration", test_cache_expiration),
        ("Cache LRU Eviction", test_cache_lru_eviction),

        # Integration
        ("Full Agent Integration", test_full_agent_integration),

        # Performance
        ("Agent Performance", test_agent_performance)
    ]

    passed = 0
    failed = 0
    start_time = time.time()

    for name, test_func in tests:
        try:
            result = test_func()
            if result:
                passed += 1
        except AssertionError as e:
            print(f"  ✗ FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"  ✗ ERROR: {e}")
            failed += 1

    elapsed = time.time() - start_time

    # Summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    print(f"Total Tests: {len(tests)}")
    print(f"Passed: {passed} ({passed/len(tests)*100:.0f}%)")
    print(f"Failed: {failed}")
    print(f"Execution Time: {elapsed:.3f}s")

    if failed == 0:
        print("\n✓ ALL TESTS PASSED")
        print("=" * 70)
        return True
    else:
        print(f"\n✗ {failed} TEST(S) FAILED")
        print("=" * 70)
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
