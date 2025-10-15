# Phase 1 Implementation Plan: Physics-Based Simulation Foundation
## Soccer Predictor v3.0 → v4.0 Physics Engine Upgrade

**Created**: 2025-10-10
**Duration**: 2 weeks (Week 1-2)
**Status**: Ready to Start

---

## 🎯 Executive Summary

This document outlines the concrete implementation plan for **Phase 1** of upgrading the Soccer Predictor from a simple LLM-based predictor to a full **Physics-Guided LLM Football Simulation System**.

### Current State (v3.0)
- ✅ Claude Haiku LLM predictor (simple predictions)
- ✅ PostgreSQL database (users, subscriptions, matches)
- ✅ FastAPI REST API
- ✅ React frontend with tactical ability framework
- ❌ **NO physics engine**
- ❌ **NO player-level simulation**
- ❌ **NO agent-based modeling**

### Target State (Phase 1 Complete)
- ✅ Extended database schema (players, teams, tactical profiles)
- ✅ Player physics state models (position, velocity, acceleration)
- ✅ Basic physics engine core (Newton's equations)
- ✅ Ball physics engine (gravity, drag, Magnus effect)
- ✅ FastAPI endpoints for physics simulation
- ✅ Unit tests for physics accuracy

---

## 📊 Gap Analysis: Current vs Planned

| Component | Current Status | Target (Phase 1) | Gap |
|-----------|---------------|------------------|-----|
| **Database Schema** | Basic (users, matches) | Extended (players, teams, physics state) | 40% → 70% |
| **Physics Engine** | None (0%) | Basic Newton + Ball physics (50%) | 0% → 50% |
| **Player Models** | None | Position-specific attributes | 0% → 100% |
| **Team Models** | Frontend only (localStorage) | PostgreSQL with tactical profiles | 30% → 100% |
| **Simulation** | LLM-only prediction | Physics + LLM hybrid | 15% → 40% |
| **API Design** | Simple REST | Extended with physics endpoints | 60% → 80% |

---

## 🗓️ Week-by-Week Plan

### **Week 1: Database & Data Models** (Days 1-7)

#### Day 1-2: Database Schema Extension
**Files to Create:**
- `backend/database/schema_v4.sql` - Extended schema with player/team tables
- `backend/database/migrations/001_add_physics_tables.sql` - Migration script

**Schema Changes:**
```sql
-- Players table with position-specific attributes
CREATE TABLE players (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID REFERENCES teams(id),
    name VARCHAR(100) NOT NULL,
    position VARCHAR(10) NOT NULL, -- GK, CB, FB, DM, CM, CAM, WG, ST
    squad_number INTEGER,

    -- Physical attributes (0-100)
    pace DECIMAL(5,2),
    acceleration DECIMAL(5,2),
    stamina DECIMAL(5,2),
    strength DECIMAL(5,2),
    agility DECIMAL(5,2),

    -- Technical attributes (position-specific, stored as JSONB)
    technical_attributes JSONB NOT NULL,

    -- Overall rating
    overall_rating DECIMAL(5,2),

    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    injury_status VARCHAR(20),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Teams table with tactical profiles
CREATE TABLE teams (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    short_name VARCHAR(20),

    -- Tactical profile (5 categories from existing framework)
    tactical_organization JSONB NOT NULL,
    attacking_efficiency JSONB NOT NULL,
    defensive_stability JSONB NOT NULL,
    physicality_stamina JSONB NOT NULL,
    psychological_factors JSONB NOT NULL,

    -- Overall team rating
    overall_rating DECIMAL(5,2),

    -- Formation
    default_formation VARCHAR(10), -- e.g., "4-3-3"

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Match physics states (for real-time simulation)
CREATE TABLE match_physics_states (
    id BIGSERIAL PRIMARY KEY,
    match_id VARCHAR(100) REFERENCES matches(id),
    simulation_id UUID NOT NULL,
    tick INTEGER NOT NULL, -- 0.1s intervals

    -- Ball state
    ball_position JSONB NOT NULL, -- [x, y, z] in meters
    ball_velocity JSONB NOT NULL, -- [vx, vy, vz] m/s
    ball_spin JSONB, -- [ωx, ωy, ωz] rad/s

    -- Player states (22 players)
    player_states JSONB NOT NULL, -- Array of player state objects

    -- Game state
    game_time DECIMAL(5,2), -- Seconds
    home_score INTEGER DEFAULT 0,
    away_score INTEGER DEFAULT 0,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_match_physics_sim ON match_physics_states(simulation_id);
CREATE INDEX idx_match_physics_tick ON match_physics_states(simulation_id, tick);
```

#### Day 3-4: Python Data Models (SQLAlchemy ORM)
**Files to Create:**
- `backend/models/player.py` - Player model with position-specific attributes
- `backend/models/team.py` - Team model with tactical profiles
- `backend/models/physics_state.py` - Physics state models

**Example: `backend/models/player.py`**
```python
from sqlalchemy import Column, Integer, String, DECIMAL, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from backend.database.connection import Base

class Player(Base):
    __tablename__ = 'players'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(UUID(as_uuid=True), ForeignKey('teams.id'))
    name = Column(String(100), nullable=False)
    position = Column(String(10), nullable=False)  # GK, CB, FB, DM, CM, CAM, WG, ST
    squad_number = Column(Integer)

    # Physical attributes (0-100 scale)
    pace = Column(DECIMAL(5, 2))
    acceleration = Column(DECIMAL(5, 2))
    stamina = Column(DECIMAL(5, 2))
    strength = Column(DECIMAL(5, 2))
    agility = Column(DECIMAL(5, 2))

    # Technical attributes (position-specific)
    technical_attributes = Column(JSONB, nullable=False)

    # Overall rating
    overall_rating = Column(DECIMAL(5, 2))

    # Status
    is_active = Column(Boolean, default=True)
    injury_status = Column(String(20))

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    team = relationship("Team", back_populates="players")

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': str(self.id),
            'team_id': str(self.team_id) if self.team_id else None,
            'name': self.name,
            'position': self.position,
            'squad_number': self.squad_number,
            'pace': float(self.pace) if self.pace else None,
            'acceleration': float(self.acceleration) if self.acceleration else None,
            'stamina': float(self.stamina) if self.stamina else None,
            'strength': float(self.strength) if self.strength else None,
            'agility': float(self.agility) if self.agility else None,
            'technical_attributes': self.technical_attributes,
            'overall_rating': float(self.overall_rating) if self.overall_rating else None,
            'is_active': self.is_active,
            'injury_status': self.injury_status
        }

    @classmethod
    def get_position_specific_attributes(cls, position: str) -> list:
        """Get required attributes for a position"""
        attributes_map = {
            'GK': ['reflexes', 'positioning', 'handling', 'diving', 'kicking', 'command_area'],
            'CB': ['tackling', 'marking', 'heading', 'positioning', 'passing', 'composure'],
            'FB': ['tackling', 'marking', 'crossing', 'stamina', 'positioning', 'pace'],
            'DM': ['tackling', 'interceptions', 'passing', 'vision', 'positioning', 'stamina'],
            'CM': ['passing', 'vision', 'dribbling', 'stamina', 'tackling', 'long_shots'],
            'CAM': ['passing', 'vision', 'dribbling', 'shooting', 'creativity', 'weak_foot'],
            'WG': ['pace', 'dribbling', 'crossing', 'shooting', 'stamina', 'weak_foot'],
            'ST': ['shooting', 'finishing', 'positioning', 'heading', 'dribbling', 'pace']
        }
        return attributes_map.get(position, [])
```

#### Day 5-7: Migration Scripts & Data Import
**Tasks:**
1. Create migration script to preserve existing data
2. Import EPL player data (from FPL API or manual JSON)
3. Import team tactical profiles (from existing localStorage)
4. Validate data integrity

**Files to Create:**
- `backend/scripts/migrate_v3_to_v4.py` - Migration script
- `backend/scripts/import_epl_players.py` - Player data import
- `backend/scripts/import_team_tactics.py` - Team tactical profile import

---

### **Week 2: Physics Engine Core** (Days 8-14)

#### Day 8-9: Player Physics Engine
**Files to Create:**
- `backend/physics/__init__.py`
- `backend/physics/player_physics.py` - Player movement with Newton's equations
- `backend/physics/constants.py` - Physical constants

**Example: `backend/physics/player_physics.py`**
```python
"""
Player Physics Engine
Simulates player movement using Newton's equations of motion
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, Tuple

# Physical constants
DT = 0.1  # Time step (seconds)
DRAG_COEFFICIENT = 0.3  # Air resistance factor
FIELD_LENGTH = 105.0  # meters
FIELD_WIDTH = 68.0  # meters

@dataclass
class PlayerState:
    """Player physics state at a given moment"""
    player_id: str
    position: np.ndarray  # [x, y] in meters (origin at center)
    velocity: np.ndarray  # [vx, vy] in m/s
    acceleration: np.ndarray  # [ax, ay] in m/s²
    stamina: float  # 0-100
    is_moving: bool = False

    def to_dict(self):
        return {
            'player_id': self.player_id,
            'position': self.position.tolist(),
            'velocity': self.velocity.tolist(),
            'acceleration': self.acceleration.tolist(),
            'stamina': self.stamina,
            'is_moving': self.is_moving
        }

class PlayerPhysicsEngine:
    """
    Physics engine for player movement

    Uses:
    - Newton's Second Law: F = ma
    - Velocity Verlet integration for numerical stability
    - Drag force: F_drag = -b*v (linear approximation)
    """

    def __init__(self):
        self.dt = DT
        self.drag_coef = DRAG_COEFFICIENT

    def update_player_state(
        self,
        player_state: PlayerState,
        player_attributes: Dict,
        target_velocity: np.ndarray,
        dt: float = None
    ) -> PlayerState:
        """
        Update player state for one time step

        Args:
            player_state: Current player state
            player_attributes: Player's physical attributes (pace, acceleration, etc.)
            target_velocity: Desired velocity from agent decision
            dt: Time step (default: 0.1s)

        Returns:
            Updated PlayerState
        """
        if dt is None:
            dt = self.dt

        # Extract attributes
        max_speed = player_attributes.get('pace', 70) / 10.0  # m/s (70 pace = 7 m/s)
        max_accel = player_attributes.get('acceleration', 70) / 10.0  # m/s²
        stamina = player_state.stamina

        # Stamina factor (affects max speed and acceleration)
        stamina_factor = max(0.5, stamina / 100.0)
        effective_max_speed = max_speed * stamina_factor
        effective_max_accel = max_accel * stamina_factor

        # Calculate desired acceleration (to reach target velocity)
        velocity_error = target_velocity - player_state.velocity
        desired_accel = velocity_error / dt

        # Limit acceleration
        accel_magnitude = np.linalg.norm(desired_accel)
        if accel_magnitude > effective_max_accel:
            desired_accel = desired_accel * (effective_max_accel / accel_magnitude)

        # Apply forces
        # F_total = F_drive - F_drag
        # F_drive = m * desired_accel (mass = 1 for simplicity)
        # F_drag = -b * v
        drag_force = -self.drag_coef * player_state.velocity
        total_accel = desired_accel + drag_force

        # Velocity Verlet integration (more stable than Euler)
        new_position = player_state.position + player_state.velocity * dt + 0.5 * total_accel * dt**2
        new_velocity = player_state.velocity + total_accel * dt

        # Limit velocity to max speed
        velocity_magnitude = np.linalg.norm(new_velocity)
        if velocity_magnitude > effective_max_speed:
            new_velocity = new_velocity * (effective_max_speed / velocity_magnitude)

        # Update stamina (depletes with movement)
        speed = np.linalg.norm(new_velocity)
        stamina_drain = 0.01 * speed * dt * (100 / player_attributes.get('stamina', 70))
        new_stamina = max(0, player_state.stamina - stamina_drain)

        # Boundary check (keep on field)
        new_position[0] = np.clip(new_position[0], -FIELD_LENGTH/2, FIELD_LENGTH/2)
        new_position[1] = np.clip(new_position[1], -FIELD_WIDTH/2, FIELD_WIDTH/2)

        return PlayerState(
            player_id=player_state.player_id,
            position=new_position,
            velocity=new_velocity,
            acceleration=total_accel,
            stamina=new_stamina,
            is_moving=velocity_magnitude > 0.1
        )

    def calculate_time_to_ball(
        self,
        player_state: PlayerState,
        ball_position: np.ndarray,
        player_attributes: Dict
    ) -> float:
        """
        Calculate time for player to reach ball

        Uses kinematic equation: t = sqrt(2*d/a) for constant acceleration
        """
        distance = np.linalg.norm(ball_position - player_state.position)
        max_accel = player_attributes.get('acceleration', 70) / 10.0

        # Simple estimation (ignores current velocity)
        time_to_ball = np.sqrt(2 * distance / max_accel)
        return time_to_ball
```

#### Day 10-11: Ball Physics Engine
**Files to Create:**
- `backend/physics/ball_physics.py` - Ball trajectory with Magnus effect

**Example: `backend/physics/ball_physics.py`**
```python
"""
Ball Physics Engine
3D ball trajectory with gravity, drag, and Magnus effect (spin)
"""

import numpy as np
from dataclasses import dataclass
from typing import Tuple

# Ball physical constants
BALL_MASS = 0.43  # kg (FIFA standard)
BALL_RADIUS = 0.11  # meters (FIFA standard)
BALL_AREA = np.pi * BALL_RADIUS**2
AIR_DENSITY = 1.225  # kg/m³ (sea level)
DRAG_COEFFICIENT = 0.25  # Typical for football
MAGNUS_COEFFICIENT = 0.25  # Lift coefficient for spinning ball
GRAVITY = 9.81  # m/s²

@dataclass
class BallState:
    """Ball physics state"""
    position: np.ndarray  # [x, y, z] in meters
    velocity: np.ndarray  # [vx, vy, vz] in m/s
    spin: np.ndarray  # [ωx, ωy, ωz] in rad/s

    def to_dict(self):
        return {
            'position': self.position.tolist(),
            'velocity': self.velocity.tolist(),
            'spin': self.spin.tolist(),
            'speed': float(np.linalg.norm(self.velocity))
        }

class BallPhysicsEngine:
    """
    3D ball physics with Magnus effect

    Forces:
    1. Gravity: F_g = -mg
    2. Drag: F_d = -0.5 * ρ * Cd * A * |v| * v
    3. Magnus (spin): F_m = 0.5 * ρ * Cl * A * (ω × v)
    """

    def __init__(self):
        self.mass = BALL_MASS
        self.radius = BALL_RADIUS
        self.area = BALL_AREA
        self.rho = AIR_DENSITY
        self.Cd = DRAG_COEFFICIENT
        self.Cl = MAGNUS_COEFFICIENT
        self.g = GRAVITY

    def update_ball_state(
        self,
        ball_state: BallState,
        dt: float = 0.1
    ) -> BallState:
        """
        Update ball state for one time step

        Uses Velocity Verlet integration
        """
        pos = ball_state.position
        vel = ball_state.velocity
        spin = ball_state.spin

        # Calculate forces
        F_gravity = np.array([0, 0, -self.mass * self.g])

        # Drag force: F_d = -0.5 * ρ * Cd * A * |v| * v
        speed = np.linalg.norm(vel)
        if speed > 0.01:
            F_drag = -0.5 * self.rho * self.Cd * self.area * speed * vel
        else:
            F_drag = np.zeros(3)

        # Magnus force: F_m = 0.5 * ρ * Cl * A * (ω × v)
        if speed > 0.01 and np.linalg.norm(spin) > 0.1:
            F_magnus = 0.5 * self.rho * self.Cl * self.area * np.cross(spin, vel)
        else:
            F_magnus = np.zeros(3)

        # Total force
        F_total = F_gravity + F_drag + F_magnus

        # Acceleration: a = F/m
        accel = F_total / self.mass

        # Velocity Verlet integration
        new_position = pos + vel * dt + 0.5 * accel * dt**2
        new_velocity = vel + accel * dt

        # Ground collision detection (z = 0)
        if new_position[2] <= 0 and new_velocity[2] < 0:
            # Bounce with energy loss (coefficient of restitution = 0.6)
            new_position[2] = 0
            new_velocity[2] = -0.6 * new_velocity[2]
            # Spin decay on bounce
            new_spin = spin * 0.7
        else:
            new_spin = spin * 0.99  # Spin decay in air

        return BallState(
            position=new_position,
            velocity=new_velocity,
            spin=new_spin
        )

    def simulate_shot(
        self,
        initial_position: np.ndarray,
        initial_velocity: np.ndarray,
        initial_spin: np.ndarray = None,
        max_time: float = 5.0,
        dt: float = 0.01
    ) -> Tuple[BallState, list]:
        """
        Simulate complete ball trajectory

        Returns:
            (final_state, trajectory_list)
        """
        if initial_spin is None:
            initial_spin = np.zeros(3)

        ball_state = BallState(initial_position, initial_velocity, initial_spin)
        trajectory = [ball_state.to_dict()]

        t = 0
        while t < max_time:
            ball_state = self.update_ball_state(ball_state, dt)
            trajectory.append(ball_state.to_dict())

            # Stop if ball has stopped moving
            if np.linalg.norm(ball_state.velocity) < 0.1 and ball_state.position[2] <= 0.01:
                break

            t += dt

        return ball_state, trajectory

    def will_score(
        self,
        initial_position: np.ndarray,
        initial_velocity: np.ndarray,
        goal_position: np.ndarray = None,
        goal_width: float = 7.32,
        goal_height: float = 2.44
    ) -> Tuple[bool, float]:
        """
        Determine if shot will score

        Returns:
            (is_goal, time_to_goal)
        """
        if goal_position is None:
            goal_position = np.array([52.5, 0, 0])  # Standard goal position

        final_state, trajectory = self.simulate_shot(initial_position, initial_velocity)

        # Check if ball crossed goal line within goal dimensions
        for i, state in enumerate(trajectory):
            pos = np.array(state['position'])

            # Check x coordinate (goal line)
            if abs(pos[0] - goal_position[0]) < 0.1:
                # Check y coordinate (width)
                if abs(pos[1]) < goal_width / 2:
                    # Check z coordinate (height)
                    if 0 < pos[2] < goal_height:
                        time_to_goal = i * 0.01
                        return True, time_to_goal

        return False, 0.0
```

#### Day 12-13: Integration & Testing
**Tasks:**
1. Create FastAPI endpoints for physics simulation
2. Write unit tests for physics accuracy
3. Create validation suite against real EPL data

**Files to Create:**
- `backend/api/physics_endpoints.py` - API routes
- `backend/tests/test_player_physics.py` - Unit tests
- `backend/tests/test_ball_physics.py` - Ball physics tests

**Example Test:**
```python
# backend/tests/test_player_physics.py
import pytest
import numpy as np
from backend.physics.player_physics import PlayerPhysicsEngine, PlayerState

def test_player_acceleration():
    """Test that player accelerates correctly"""
    engine = PlayerPhysicsEngine()

    # Create player at rest
    player_state = PlayerState(
        player_id="test_player",
        position=np.array([0.0, 0.0]),
        velocity=np.array([0.0, 0.0]),
        acceleration=np.array([0.0, 0.0]),
        stamina=100.0
    )

    # Player attributes (pace=80, acceleration=80)
    player_attrs = {
        'pace': 80,
        'acceleration': 80,
        'stamina': 80
    }

    # Target velocity: 5 m/s forward
    target_velocity = np.array([5.0, 0.0])

    # Update for 1 second (10 steps)
    for _ in range(10):
        player_state = engine.update_player_state(
            player_state,
            player_attrs,
            target_velocity,
            dt=0.1
        )

    # Check that player is moving forward
    assert player_state.velocity[0] > 3.0
    assert player_state.position[0] > 0
    assert player_state.stamina < 100.0  # Stamina should decrease

def test_player_max_speed():
    """Test that player doesn't exceed max speed"""
    engine = PlayerPhysicsEngine()

    player_state = PlayerState(
        player_id="test_player",
        position=np.array([0.0, 0.0]),
        velocity=np.array([0.0, 0.0]),
        acceleration=np.array([0.0, 0.0]),
        stamina=100.0
    )

    player_attrs = {'pace': 70, 'acceleration': 70, 'stamina': 80}
    max_expected_speed = 7.0  # pace=70 → 7 m/s

    # Try to accelerate to very high speed
    target_velocity = np.array([20.0, 0.0])

    for _ in range(100):  # Many iterations
        player_state = engine.update_player_state(
            player_state,
            player_attrs,
            target_velocity,
            dt=0.1
        )

    # Speed should be capped at max_speed
    actual_speed = np.linalg.norm(player_state.velocity)
    assert actual_speed <= max_expected_speed * 1.1  # 10% tolerance

def test_ball_gravity():
    """Test that ball falls correctly under gravity"""
    from backend.physics.ball_physics import BallPhysicsEngine, BallState

    engine = BallPhysicsEngine()

    # Ball at 10m height, no horizontal velocity
    ball_state = BallState(
        position=np.array([0.0, 0.0, 10.0]),
        velocity=np.array([0.0, 0.0, 0.0]),
        spin=np.array([0.0, 0.0, 0.0])
    )

    # Simulate for 1.5 seconds (should hit ground)
    for _ in range(15):
        ball_state = engine.update_ball_state(ball_state, dt=0.1)

    # Ball should have fallen to ground
    assert ball_state.position[2] <= 0.1  # Close to ground

def test_ball_magnus_effect():
    """Test that spinning ball curves"""
    from backend.physics.ball_physics import BallPhysicsEngine, BallState

    engine = BallPhysicsEngine()

    # Ball with right-to-left spin (backspin around y-axis)
    ball_state = BallState(
        position=np.array([0.0, 0.0, 1.0]),
        velocity=np.array([20.0, 0.0, 0.0]),  # 20 m/s forward
        spin=np.array([0.0, 100.0, 0.0])  # 100 rad/s backspin
    )

    initial_y = ball_state.position[1]

    # Simulate for 1 second
    for _ in range(10):
        ball_state = engine.update_ball_state(ball_state, dt=0.1)

    # Ball should curve sideways due to Magnus effect
    assert abs(ball_state.position[1] - initial_y) > 0.5  # At least 0.5m deviation
```

#### Day 14: Documentation & Review
**Tasks:**
1. Write Phase 1 completion report
2. Document API endpoints
3. Code review and cleanup

---

## 🎯 Success Criteria (Phase 1)

### Functional Requirements
- [ ] Database schema extended with player/team/physics tables
- [ ] Migration from v3 to v4 preserves all existing data
- [ ] Player physics engine passes all unit tests
- [ ] Ball physics engine simulates realistic trajectories
- [ ] FastAPI endpoints return physics simulation results
- [ ] Physics accuracy validated against EPL data (±10%)

### Performance Requirements
- [ ] Player state update: < 1ms per player
- [ ] Ball state update: < 0.5ms
- [ ] Database queries: < 50ms for player/team data
- [ ] API response time: < 100ms for non-simulation endpoints

### Code Quality
- [ ] Test coverage > 80% for physics modules
- [ ] All code follows PEP 8 style guide
- [ ] Type hints for all public functions
- [ ] Documentation strings for all classes/functions

---

## 🚀 Next Steps (Phase 2)

After Phase 1 completion, Phase 2 will implement:
1. **Agent-Based Model**: 22 POMDP agents with position-specific behavior
2. **LLM Integration**: Tactical instruction parser
3. **Match Simulation Loop**: Complete 90-minute simulation
4. **Psychology Model**: Mental state simulation

**Estimated Timeline**: Week 3-6 (4 weeks)

---

## 📝 Notes

### Key Design Decisions
1. **Velocity Verlet Integration**: Chosen for numerical stability over Euler method
2. **Position-Specific Attributes**: Stored as JSONB for flexibility
3. **Time Step**: 0.1s (10 FPS) balances accuracy and performance
4. **Coordinate System**: Origin at field center, x=length, y=width, z=height

### Assumptions
- Player mass = 1 (normalized)
- Drag coefficient = 0.3 (empirical value)
- EPL average player pace = 70 → 7 m/s top speed
- Field dimensions: 105m × 68m (standard EPL)

### Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| Physics too slow | High | Profile code, optimize NumPy operations |
| Data migration fails | High | Extensive testing, backup procedures |
| Physics inaccurate | Medium | Validate against real EPL tracking data |
| Database schema changes break existing features | Medium | Thorough integration testing |

---

**Document Owner**: Claude Code
**Last Updated**: 2025-10-10
**Status**: Ready for Implementation ✅
