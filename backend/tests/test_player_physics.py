"""
Unit Tests for Player Physics Engine
Tests individual components of 2D player movement physics
"""

import pytest
import numpy as np
from physics.player_physics import (
    PlayerState,
    PlayerPhysicsEngine,
    create_initial_state,
    calculate_target_velocity
)
from physics.constants import (
    rating_to_speed,
    rating_to_accel,
    stamina_factor,
    FIELD_X_MIN,
    FIELD_X_MAX,
    FIELD_Y_MIN,
    FIELD_Y_MAX
)


class TestPlayerState:
    """Test PlayerState dataclass"""

    def test_create_initial_state(self):
        """Test creating player at rest"""
        player = create_initial_state("test", (10, 20), stamina=80)

        assert player.player_id == "test"
        assert np.allclose(player.position, [10, 20])
        assert np.allclose(player.velocity, [0, 0])
        assert np.allclose(player.acceleration, [0, 0])
        assert player.stamina == 80
        assert player.is_moving == False

    def test_to_dict(self, player_at_rest):
        """Test state serialization to dict"""
        data = player_at_rest.to_dict()

        assert 'player_id' in data
        assert 'position' in data
        assert 'velocity' in data
        assert 'stamina' in data
        assert 'speed' in data
        assert isinstance(data['position'], list)

    def test_from_dict(self, player_at_rest):
        """Test state deserialization from dict"""
        data = player_at_rest.to_dict()
        restored = PlayerState.from_dict(data)

        assert np.allclose(restored.position, player_at_rest.position)
        assert np.allclose(restored.velocity, player_at_rest.velocity)
        assert restored.stamina == player_at_rest.stamina


class TestPlayerPhysicsEngine:
    """Test PlayerPhysicsEngine core functionality"""

    def test_initialization(self):
        """Test engine initialization"""
        engine = PlayerPhysicsEngine(dt=0.1, drag_coef=0.3)

        assert engine.dt == 0.1
        assert engine.drag_coef == 0.3

    def test_player_accelerates_from_rest(self, player_engine, player_at_rest, average_player_attrs):
        """
        Test: Player accelerates from rest

        Given: Player at rest (v=0)
        When: Target velocity = 7 m/s forward
        Then: Player accelerates toward target
        """
        target_vel = np.array([7.0, 0.0])

        # Update for 1 second (10 ticks)
        state = player_at_rest
        for _ in range(10):
            state = player_engine.update_player_state(
                state,
                average_player_attrs,
                target_vel
            )

        # Should be moving forward
        assert state.velocity[0] > 3.0, f"Expected v > 3 m/s, got {state.velocity[0]}"
        assert state.position[0] > 0, "Player should have moved forward"
        assert state.is_moving == True

    def test_player_reaches_max_speed(self, player_engine, player_at_rest, average_player_attrs):
        """
        Test: Player doesn't exceed max speed

        Given: Player with pace=70 (max speed = 7 m/s)
        When: Target velocity = 20 m/s (unrealistic)
        Then: Player speed capped at 7 m/s
        """
        target_vel = np.array([20.0, 0.0])
        max_speed = rating_to_speed(average_player_attrs['pace'])

        # Update for 10 seconds (100 ticks) - should reach max
        state = player_at_rest
        for _ in range(100):
            state = player_engine.update_player_state(
                state,
                average_player_attrs,
                target_vel
            )

        actual_speed = np.linalg.norm(state.velocity)
        assert actual_speed <= max_speed * 1.05, \
            f"Speed {actual_speed:.2f} exceeds max {max_speed:.2f}"

    def test_player_decelerates_to_stop(self, player_engine, player_moving, average_player_attrs):
        """
        Test: Player decelerates when target velocity = 0

        Given: Player moving at 5 m/s
        When: Target velocity = 0
        Then: Player slows down
        """
        initial_speed = np.linalg.norm(player_moving.velocity)
        target_vel = np.zeros(2)

        # Update for 1 second
        state = player_moving
        for _ in range(10):
            state = player_engine.update_player_state(
                state,
                average_player_attrs,
                target_vel
            )

        final_speed = np.linalg.norm(state.velocity)
        assert final_speed < initial_speed, "Player should have slowed down"

    def test_stamina_drains_when_moving(self, player_engine, player_at_rest, average_player_attrs):
        """
        Test: Stamina drains when moving

        Given: Player at full stamina (100)
        When: Player sprints for 60 seconds
        Then: Stamina decreases
        """
        target_vel = np.array([7.0, 0.0])
        initial_stamina = player_at_rest.stamina

        # Run for 60 seconds (600 ticks)
        state = player_at_rest
        for _ in range(600):
            state = player_engine.update_player_state(
                state,
                average_player_attrs,
                target_vel
            )

        assert state.stamina < initial_stamina, \
            f"Stamina should decrease, was {initial_stamina}, now {state.stamina}"
        assert state.stamina >= 0, "Stamina should not go negative"

    def test_stamina_recovers_when_idle(self, player_engine, tired_player, average_player_attrs):
        """
        Test: Stamina recovers when idle

        Given: Tired player (stamina=20)
        When: Player rests (target velocity = 0)
        Then: Stamina increases
        """
        target_vel = np.zeros(2)
        initial_stamina = tired_player.stamina

        # Rest for 30 seconds (300 ticks)
        state = tired_player
        for _ in range(300):
            state = player_engine.update_player_state(
                state,
                average_player_attrs,
                target_vel
            )

        assert state.stamina > initial_stamina, \
            f"Stamina should recover, was {initial_stamina}, now {state.stamina}"
        assert state.stamina <= 100, "Stamina should not exceed 100"

    def test_field_boundaries_x_min(self, player_engine, average_player_attrs):
        """
        Test: Player can't go past left field boundary

        Given: Player near left boundary
        When: Player tries to move left
        Then: Position clamped at boundary
        """
        player = create_initial_state("test", (FIELD_X_MIN + 1, 0), stamina=100)
        target_vel = np.array([-10.0, 0.0])  # Move left

        # Try to cross boundary
        for _ in range(20):
            player = player_engine.update_player_state(
                player,
                average_player_attrs,
                target_vel
            )

        assert player.position[0] >= FIELD_X_MIN, \
            f"Player x={player.position[0]} below minimum {FIELD_X_MIN}"

    def test_field_boundaries_x_max(self, player_engine, average_player_attrs):
        """Test: Player can't go past right field boundary"""
        player = create_initial_state("test", (FIELD_X_MAX - 1, 0), stamina=100)
        target_vel = np.array([10.0, 0.0])  # Move right

        for _ in range(20):
            player = player_engine.update_player_state(
                player,
                average_player_attrs,
                target_vel
            )

        assert player.position[0] <= FIELD_X_MAX, \
            f"Player x={player.position[0]} above maximum {FIELD_X_MAX}"

    def test_field_boundaries_y(self, player_engine, average_player_attrs):
        """Test: Player respects Y boundaries"""
        # Test top boundary
        player = create_initial_state("test", (0, FIELD_Y_MAX - 1), stamina=100)
        target_vel = np.array([0.0, 10.0])

        for _ in range(20):
            player = player_engine.update_player_state(
                player,
                average_player_attrs,
                target_vel
            )

        assert player.position[1] <= FIELD_Y_MAX

    def test_zero_velocity_no_stamina_drain(self, player_engine, player_at_rest, average_player_attrs):
        """
        Test: Standing still doesn't drain stamina

        Given: Player at rest
        When: Target velocity = 0 (standing still)
        Then: Stamina doesn't decrease (might even recover)
        """
        target_vel = np.zeros(2)
        initial_stamina = player_at_rest.stamina

        # Stand still for 10 seconds
        state = player_at_rest
        for _ in range(100):
            state = player_engine.update_player_state(
                state,
                average_player_attrs,
                target_vel
            )

        # Stamina should not decrease (might recover)
        assert state.stamina >= initial_stamina * 0.99, \
            f"Standing still drained stamina: {initial_stamina} ’ {state.stamina}"

    def test_fast_player_beats_slow_player(self, player_engine, fast_player_attrs, slow_player_attrs):
        """
        Test: Fast player reaches target before slow player

        Given: Fast player (pace=90) and slow player (pace=60)
        When: Both sprint toward same target
        Then: Fast player arrives first
        """
        fast_player = create_initial_state("fast", (-10, 0), stamina=100)
        slow_player = create_initial_state("slow", (-10, 0), stamina=100)

        target_pos = np.array([20.0, 0.0])
        fast_target_vel = calculate_target_velocity(
            fast_player.position,
            target_pos,
            rating_to_speed(fast_player_attrs['pace'])
        )
        slow_target_vel = calculate_target_velocity(
            slow_player.position,
            target_pos,
            rating_to_speed(slow_player_attrs['pace'])
        )

        # Run for 3 seconds
        for _ in range(30):
            fast_player = player_engine.update_player_state(
                fast_player,
                fast_player_attrs,
                fast_target_vel
            )
            slow_player = player_engine.update_player_state(
                slow_player,
                slow_player_attrs,
                slow_target_vel
            )

        # Fast player should be closer to target
        fast_distance = np.linalg.norm(fast_player.position - target_pos)
        slow_distance = np.linalg.norm(slow_player.position - target_pos)

        assert fast_distance < slow_distance, \
            f"Fast player ({fast_distance:.1f}m) should be closer than slow player ({slow_distance:.1f}m)"

    def test_tired_player_slower_than_fresh(self, player_engine, average_player_attrs):
        """
        Test: Tired player moves slower than fresh player

        Given: Tired player (stamina=10) and fresh player (stamina=100)
        When: Both try to reach max speed
        Then: Fresh player is faster
        """
        tired = create_initial_state("tired", (0, 0), stamina=10)
        fresh = create_initial_state("fresh", (0, 0), stamina=100)

        target_vel = np.array([7.0, 0.0])

        # Run for 2 seconds
        for _ in range(20):
            tired = player_engine.update_player_state(tired, average_player_attrs, target_vel)
            fresh = player_engine.update_player_state(fresh, average_player_attrs, target_vel)

        tired_speed = np.linalg.norm(tired.velocity)
        fresh_speed = np.linalg.norm(fresh.velocity)

        assert tired_speed < fresh_speed, \
            f"Tired player ({tired_speed:.2f}) should be slower than fresh ({fresh_speed:.2f})"


class TestHelperFunctions:
    """Test helper functions"""

    def test_calculate_target_velocity(self):
        """Test target velocity calculation"""
        current_pos = np.array([0.0, 0.0])
        target_pos = np.array([10.0, 0.0])
        max_speed = 7.0

        target_vel = calculate_target_velocity(current_pos, target_pos, max_speed)

        # Should point toward target
        assert np.allclose(target_vel, [7.0, 0.0], atol=0.1)

    def test_calculate_target_velocity_diagonal(self):
        """Test target velocity for diagonal movement"""
        current_pos = np.array([0.0, 0.0])
        target_pos = np.array([10.0, 10.0])
        max_speed = 7.0

        target_vel = calculate_target_velocity(current_pos, target_pos, max_speed)

        # Should have magnitude = max_speed
        speed = np.linalg.norm(target_vel)
        assert abs(speed - max_speed) < 0.1

    def test_calculate_target_velocity_at_target(self):
        """Test target velocity when already at target"""
        current_pos = np.array([5.0, 5.0])
        target_pos = np.array([5.0, 5.0])
        max_speed = 7.0

        target_vel = calculate_target_velocity(current_pos, target_pos, max_speed)

        # Should be zero (already there)
        assert np.allclose(target_vel, [0.0, 0.0])


class TestPhysicsAccuracy:
    """Test physics equation accuracy"""

    def test_time_to_position_estimation(self, player_engine, player_at_rest, average_player_attrs):
        """Test time-to-position calculation is reasonably accurate"""
        target_pos = np.array([20.0, 0.0])

        # Estimate time
        estimated_time = player_engine.calculate_time_to_position(
            player_at_rest,
            target_pos,
            average_player_attrs
        )

        # Actual simulation
        target_vel = calculate_target_velocity(
            player_at_rest.position,
            target_pos,
            rating_to_speed(average_player_attrs['pace'])
        )

        state = player_at_rest
        actual_time = 0
        while np.linalg.norm(state.position - target_pos) > 0.5:
            state = player_engine.update_player_state(
                state,
                average_player_attrs,
                target_vel
            )
            actual_time += 0.1
            if actual_time > 20:  # Safety limit
                break

        # Estimate should be within 50% of actual
        assert actual_time * 0.5 < estimated_time < actual_time * 2.0, \
            f"Estimated {estimated_time:.1f}s, actual {actual_time:.1f}s"


class TestEdgeCases:
    """Test edge cases and extreme values"""

    def test_zero_stamina_player(self, player_engine, average_player_attrs):
        """Test exhausted player (stamina=0)"""
        player = create_initial_state("exhausted", (0, 0), stamina=0)
        target_vel = np.array([7.0, 0.0])

        # Should still move (just slower)
        state = player
        for _ in range(10):
            state = player_engine.update_player_state(state, average_player_attrs, target_vel)

        # Should be moving (but slowly)
        assert np.linalg.norm(state.velocity) > 0.1
        assert np.linalg.norm(state.velocity) < rating_to_speed(average_player_attrs['pace']) * 0.6

    def test_superhuman_pace(self, player_engine):
        """Test player with pace=100"""
        player = create_initial_state("superhuman", (0, 0), stamina=100)
        attrs = {'pace': 100, 'acceleration': 100, 'stamina': 100}
        target_vel = np.array([10.0, 0.0])

        # Should still work (just very fast)
        state = player
        for _ in range(50):
            state = player_engine.update_player_state(state, attrs, target_vel)

        # Should be moving fast
        assert np.linalg.norm(state.velocity) > 8.0

    def test_very_slow_player(self, player_engine):
        """Test player with pace=10 (very slow)"""
        player = create_initial_state("slow", (0, 0), stamina=100)
        attrs = {'pace': 10, 'acceleration': 10, 'stamina': 70}
        target_vel = np.array([1.0, 0.0])

        # Should still work
        state = player
        for _ in range(50):
            state = player_engine.update_player_state(state, attrs, target_vel)

        # Should be moving (but slowly)
        assert np.linalg.norm(state.velocity) > 0.1
        assert np.linalg.norm(state.velocity) < 1.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
