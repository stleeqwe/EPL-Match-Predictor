# Architecture Redesign for 95% Balance Target

**Date**: 2025-10-10
**Current**: V11 (60% balanced)
**Target**: 95% balanced matches
**Status**: 🔬 DEEP ANALYSIS & REDESIGN

---

## 🎯 Problem Statement

### Current Performance (V11)
```
Balanced matches: 60% (6/10)
Imbalanced matches: 40% (4/10)
Pattern: 10-90% extreme dominance in failed matches
```

### Target Performance (95%)
```
Balanced matches: 95% (19/20)
Imbalanced matches: 5% (1/20)
Maximum acceptable: 20-80% possession range
```

### Gap Analysis
```
Current failure rate: 40%
Target failure rate: 5%
Required improvement: 8x reduction in failures
```

**This is NOT incremental improvement - requires fundamental architectural change**

---

## 🔬 Root Cause Analysis (Deep Dive)

### Why Do 40% of Matches Still Fail?

#### Observation 1: Initial Randomness Amplification
```
Match Start (t=0):
- Ball randomly placed at ±10m
- Team A closer → gets ball first
- Probability: 50-50

t=30s:
- Team A: 70% possession
- Team B: 30% possession
- Gap emerges

t=5min (end):
- Team A: 90% possession
- Team B: 10% possession
- Gap locked in

WHY? Positive feedback loop not broken by current mechanics
```

#### Observation 2: Lack of Tactical Adaptation
```
Team A (winning possession 80-20):
- Still plays same way
- No defensive adjustment
- No fatigue effects
- Maintains advantage

Team B (losing possession 20-80):
- Still plays same way
- No increased pressing
- No tactical desperation
- Cannot recover

WHY? No team-level intelligence or adaptive strategy
```

#### Observation 3: Individual vs Collective Optimization
```
Current System (Individual):
Player 1: "I see ball → I chase ball"
Player 2: "I see ball → I chase ball"
...
Result: All players chase ball, no positioning

Needed System (Collective):
Player 1: "I'm closest → I press ball carrier"
Player 2: "I cover passing lane to their midfielder"
Player 3: "I block space behind defense"
...
Result: Organized pressing, higher ball recovery
```

#### Observation 4: Space Exploitation Failure
```
Current Decision Making:
if has_ball:
    pass_to_closest_teammate()  # May be marked

Better Decision Making:
if has_ball:
    teammates_in_space = find_teammates_with_space()
    pass_to_player_in_space()  # Safer, progressive

Current: Space-blind
Needed: Space-aware
```

---

## 💡 Core Insight

**The fundamental problem is not individual player behavior but LACK OF TEAM COORDINATION**

Current architecture:
```
11 players × Individual decisions = Chaos without coordination
```

Needed architecture:
```
1 Team Strategy + 11 Coordinated players = Organized team play
```

---

## 🏗️ Proposed Architecture Redesign

### High-Level Structure

```
GameSimulator
│
├─── Physics Layer (unchanged)
│    ├─ PlayerPhysicsEngine
│    └─ BallPhysicsEngine
│
├─── Team Intelligence Layer (NEW)
│    │
│    ├─ GlobalContext
│    │  ├─ Possession tracker (who has ball, for how long)
│    │  ├─ Field zones (defensive/middle/attacking thirds)
│    │  ├─ Possession balance (-1.0 to +1.0)
│    │  └─ Match phase (early/mid/late)
│    │
│    ├─ TeamStrategy (NEW)
│    │  ├─ Tactical state (PRESSING/DEFENDING/POSSESSING/COUNTER)
│    │  ├─ Formation shape (COMPACT/BALANCED/EXPANDED)
│    │  ├─ Pressing intensity (HIGH/MEDIUM/LOW)
│    │  └─ Risk tolerance (SAFE/BALANCED/AGGRESSIVE)
│    │
│    ├─ SpaceAnalyzer (NEW)
│    │  ├─ Zone control map (which team dominates each area)
│    │  ├─ Dangerous spaces (opponent threats)
│    │  ├─ Available spaces (attacking opportunities)
│    │  └─ Passing lanes (open/blocked)
│    │
│    └─ DynamicBalancer (NEW - Critical for 95%)
│       ├─ Possession-based adjustments
│       ├─ Fatigue simulation
│       └─ Rubber-band restoration
│
└─── Player Intelligence Layer (redesigned)
     │
     ├─ TacticalAgent (replaces SimpleAgent)
     │  ├─ Team-aware decisions
     │  ├─ Role-based behavior
     │  └─ Context-sensitive actions
     │
     └─ CoordinatedBehaviors
        ├─ Organized pressing
        ├─ Space occupation
        ├─ Passing lane blocking
        └─ Formation maintenance
```

---

## 🎯 Implementation Strategy (3-Phase Approach)

### Phase 1: Foundation (Target: 80% balance)
**Time: 6-8 hours**
**Goal: Add team-level awareness and dynamic balancing**

#### 1.1 Global Context System
```python
class GlobalContext:
    """Track global match state"""

    def __init__(self):
        self.possession_timer = {'home': 0.0, 'away': 0.0}
        self.possession_balance = 0.0  # -1.0 (away dominant) to +1.0 (home dominant)
        self.ball_zone = 'middle'  # defensive/middle/attacking

    def update(self, dt, ball_position, ball_possessor):
        # Track cumulative possession
        if ball_possessor:
            self.possession_timer[ball_possessor] += dt

        # Calculate balance
        total = self.possession_timer['home'] + self.possession_timer['away']
        if total > 0:
            self.possession_balance = (
                self.possession_timer['home'] - self.possession_timer['away']
            ) / total

        # Determine ball zone
        if ball_position[0] > 35: self.ball_zone = 'attacking_home'
        elif ball_position[0] < -35: self.ball_zone = 'attacking_away'
        else: self.ball_zone = 'middle'
```

#### 1.2 Dynamic Balancer (CRITICAL)
```python
class DynamicBalancer:
    """
    Self-balancing mechanism that prevents runaway possession

    Philosophy:
    - Simulates realistic fatigue/pressure effects
    - Losing team gets "desperation" boost
    - Winning team gets "complacency" penalty
    """

    def calculate_adjustments(self, possession_balance):
        """
        Returns multipliers for various mechanics

        Args:
            possession_balance: -1.0 to 1.0 (negative = away dominant)

        Returns:
            {
                'home_tackle_range': float,
                'away_tackle_range': float,
                'home_pass_accuracy': float,
                'away_pass_accuracy': float,
                'home_interception_chance': float,
                'away_interception_chance': float
            }
        """
        # Extract imbalance magnitude
        imbalance = abs(possession_balance)

        # Determine dominant/losing teams
        if possession_balance > 0:
            dominant_team = 'home'
            losing_team = 'away'
        else:
            dominant_team = 'away'
            losing_team = 'home'

        # No adjustment if balance is acceptable (< 30% difference)
        if imbalance < 0.3:
            return {
                'home_tackle_range': 1.0,
                'away_tackle_range': 1.0,
                'home_pass_accuracy': 1.0,
                'away_pass_accuracy': 1.0,
                'home_interception_chance': 1.0,
                'away_interception_chance': 1.0
            }

        # Calculate adjustment strength (0.0 to 1.0)
        # 30% imbalance = 0.0 adjustment
        # 50% imbalance = 0.5 adjustment (moderate)
        # 70% imbalance = 1.0 adjustment (maximum)
        adjustment_strength = min(1.0, (imbalance - 0.3) / 0.4)

        # Losing team advantages (simulates desperation/increased intensity)
        losing_tackle_range_boost = 1.0 + (0.5 * adjustment_strength)  # Up to +50%
        losing_interception_boost = 1.0 + (0.8 * adjustment_strength)  # Up to +80%

        # Dominant team penalties (simulates fatigue/complacency)
        dominant_pass_accuracy_penalty = 1.0 - (0.25 * adjustment_strength)  # Up to -25%
        dominant_tackle_range_penalty = 1.0 - (0.2 * adjustment_strength)  # Up to -20%

        # Build adjustments dict
        adjustments = {
            'home_tackle_range': 1.0,
            'away_tackle_range': 1.0,
            'home_pass_accuracy': 1.0,
            'away_pass_accuracy': 1.0,
            'home_interception_chance': 1.0,
            'away_interception_chance': 1.0
        }

        # Apply to appropriate teams
        adjustments[f'{losing_team}_tackle_range'] = losing_tackle_range_boost
        adjustments[f'{losing_team}_interception_chance'] = losing_interception_boost
        adjustments[f'{dominant_team}_pass_accuracy'] = dominant_pass_accuracy_penalty
        adjustments[f'{dominant_team}_tackle_range'] = dominant_tackle_range_penalty

        return adjustments
```

#### 1.3 Integration into Game Loop
```python
# In GameSimulator.__init__()
self.global_context = GlobalContext()
self.dynamic_balancer = DynamicBalancer()

# In _simulate_tick()
# 1. Update context
current_possessor = self._determine_ball_possessor(ball_state, player_states)
self.global_context.update(self.config.dt, ball_state.position, current_possessor)

# 2. Get dynamic adjustments
adjustments = self.dynamic_balancer.calculate_adjustments(
    self.global_context.possession_balance
)

# 3. Apply to action execution
# Modify tackle ranges
EFFECTIVE_TACKLE_RADIUS = PLAYER_TACKLE_RADIUS * adjustments[f'{team}_tackle_range']

# Modify pass accuracy in action_executor
pass_accuracy *= adjustments[f'{team}_pass_accuracy']

# Modify interception chances
interception_prob *= adjustments[f'{opposing_team}_interception_chance']
```

**Expected Result**: 70-80% balanced matches

---

### Phase 2: Coordination (Target: 90% balance)
**Time: 5-7 hours**
**Goal: Add space awareness and organized pressing**

#### 2.1 Space Analyzer
```python
class SpaceAnalyzer:
    """
    Analyzes field space using grid-based approach

    Divides field into zones and calculates:
    - Which team controls each zone
    - Where are dangerous spaces (opponents unmarked)
    - Where are available spaces (for passes/runs)
    """

    def __init__(self):
        # Divide field into 12x8 grid (96 zones)
        self.grid_x = 12  # Along length
        self.grid_y = 8   # Along width

        # Each zone: 105m / 12 = 8.75m × 68m / 8 = 8.5m
        self.zone_width = (FIELD_X_MAX - FIELD_X_MIN) / self.grid_x
        self.zone_height = (FIELD_Y_MAX - FIELD_Y_MIN) / self.grid_y

    def analyze_space(self, home_players, away_players, ball_position):
        """
        Returns space control map

        Returns:
            {
                'zone_control': 2D array (12x8) with values:
                    -1.0 = fully away controlled
                     0.0 = neutral
                    +1.0 = fully home controlled
                'dangerous_zones_home': [(x, y), ...],
                'dangerous_zones_away': [(x, y), ...],
                'available_spaces': [(x, y), ...]
            }
        """
        zone_control = np.zeros((self.grid_x, self.grid_y))

        # Calculate each zone's control
        for i in range(self.grid_x):
            for j in range(self.grid_y):
                zone_center = self._get_zone_center(i, j)

                # Find closest player from each team
                home_dist = min(
                    np.linalg.norm(p.position[:2] - zone_center)
                    for p in home_players
                )
                away_dist = min(
                    np.linalg.norm(p.position[:2] - zone_center)
                    for p in away_players
                )

                # Control based on relative distance
                total_dist = home_dist + away_dist
                if total_dist > 0:
                    zone_control[i, j] = (away_dist - home_dist) / total_dist

        # Find dangerous zones (opponent-controlled near our goal)
        dangerous_zones_home = []
        dangerous_zones_away = []

        for i in range(self.grid_x):
            for j in range(self.grid_y):
                zone_center = self._get_zone_center(i, j)

                # Home's dangerous zone: away-controlled in home's defensive third
                if zone_center[0] < -18 and zone_control[i, j] < -0.5:
                    dangerous_zones_home.append((i, j))

                # Away's dangerous zone: home-controlled in away's defensive third
                if zone_center[0] > 18 and zone_control[i, j] > 0.5:
                    dangerous_zones_away.append((i, j))

        # Find available spaces (low player density)
        available_spaces = []
        for i in range(self.grid_x):
            for j in range(self.grid_y):
                zone_center = self._get_zone_center(i, j)

                # Count players in zone
                players_in_zone = 0
                for p in home_players + away_players:
                    if self._point_in_zone(p.position[:2], i, j):
                        players_in_zone += 1

                # Available if < 2 players
                if players_in_zone < 2:
                    available_spaces.append(zone_center)

        return {
            'zone_control': zone_control,
            'dangerous_zones_home': dangerous_zones_home,
            'dangerous_zones_away': dangerous_zones_away,
            'available_spaces': available_spaces
        }
```

#### 2.2 Organized Pressing System
```python
class PressingCoordinator:
    """
    Coordinates team pressing behavior

    When opponent has ball:
    - Assign 1 player to press ball carrier
    - Assign 2-3 players to block passing lanes
    - Others maintain defensive shape
    """

    def assign_pressing_roles(self, team_players, opponents, ball_carrier):
        """
        Returns role assignments for each player

        Returns:
            {
                'player_id': {
                    'role': 'press_ball' | 'block_lane' | 'cover_space',
                    'target': position or player
                }
            }
        """
        roles = {}

        # 1. Find closest player to ball carrier - they press
        distances = [
            (p.player_id, np.linalg.norm(p.position[:2] - ball_carrier.position[:2]))
            for p in team_players
        ]
        distances.sort(key=lambda x: x[1])

        presser_id = distances[0][0]
        roles[presser_id] = {
            'role': 'press_ball',
            'target': ball_carrier.position[:2]
        }

        # 2. Find likely pass targets
        pass_targets = self._predict_pass_targets(
            ball_carrier,
            [opp for opp in opponents if opp.player_id != ball_carrier.player_id]
        )

        # 3. Assign 2-3 players to block lanes to top pass targets
        lane_blockers = distances[1:4]  # Next 3 closest
        for i, (player_id, _) in enumerate(lane_blockers):
            if i < len(pass_targets):
                target = pass_targets[i]
                roles[player_id] = {
                    'role': 'block_lane',
                    'target': target.position[:2]
                }

        # 4. Rest maintain shape
        assigned = set(roles.keys())
        for p in team_players:
            if p.player_id not in assigned:
                roles[p.player_id] = {
                    'role': 'cover_space',
                    'target': self._get_defensive_position(p)
                }

        return roles

    def _predict_pass_targets(self, ball_carrier, teammates):
        """
        Predict most likely pass targets based on:
        - Distance (closer = more likely)
        - Angle (forward = more likely)
        - Openness (unmarked = more likely)
        """
        scored_targets = []

        for teammate in teammates:
            # Distance score (closer = better, up to optimal range)
            distance = np.linalg.norm(
                teammate.position[:2] - ball_carrier.position[:2]
            )
            distance_score = 1.0 if distance < 15 else max(0, 1.0 - (distance - 15) / 25)

            # Forward score (attacking direction = better)
            direction_to_teammate = teammate.position[:2] - ball_carrier.position[:2]
            # Assume ball_carrier attacking toward positive x
            forward_score = max(0, direction_to_teammate[0] / (distance + 0.1))

            # Combined score
            total_score = distance_score * 0.5 + forward_score * 0.5
            scored_targets.append((teammate, total_score))

        # Return top 3
        scored_targets.sort(key=lambda x: x[1], reverse=True)
        return [t[0] for t in scored_targets[:3]]
```

#### 2.3 Space-Aware Positioning
```python
class SpaceAwareAgent:
    """
    Enhanced agent that considers space when making decisions
    """

    def decide_position_without_ball(
        self,
        player_state,
        game_context,
        space_analysis,
        pressing_role
    ):
        """
        Decide where to position when not having ball

        Considers:
        - Pressing role assignment
        - Available spaces
        - Formation position
        """
        # 1. If assigned pressing role, execute it
        if pressing_role['role'] == 'press_ball':
            return Action.create_chase_ball(
                pressing_role['target'],
                speed=100.0
            )

        elif pressing_role['role'] == 'block_lane':
            # Position between ball carrier and pass target
            ball_pos = game_context.ball_position[:2]
            target_pos = pressing_role['target']

            # Optimal blocking position: 60% toward target
            blocking_pos = ball_pos + 0.6 * (target_pos - ball_pos)

            return Action.create_move_to_position(
                blocking_pos,
                speed=80.0
            )

        elif pressing_role['role'] == 'cover_space':
            # Move to cover dangerous space or maintain formation
            dangerous_spaces = space_analysis['dangerous_zones_home']  # or away

            if dangerous_spaces:
                # Cover nearest dangerous space
                nearest_danger = min(
                    dangerous_spaces,
                    key=lambda z: np.linalg.norm(z - player_state.position[:2])
                )
                return Action.create_move_to_position(
                    nearest_danger,
                    speed=70.0
                )
            else:
                # Return to formation position
                formation_pos = self._get_formation_position(player_state)
                return Action.create_move_to_position(
                    formation_pos,
                    speed=60.0
                )
```

**Expected Result**: 85-90% balanced matches

---

### Phase 3: Advanced Tactics (Target: 95% balance)
**Time: 4-6 hours**
**Goal: Add dynamic formation and advanced passing**

#### 3.1 Team Strategy State Machine
```python
class TeamStrategy:
    """
    Manages team-level tactical decisions

    States:
    - HIGH_PRESS: Aggressive pressing when losing possession
    - POSSESSION: Safe passing when ahead
    - COUNTER: Quick transitions
    - LOW_BLOCK: Compact defense
    """

    def __init__(self):
        self.current_state = 'BALANCED'
        self.formation_compactness = 1.0  # 0.7 = compact, 1.3 = expanded

    def update_strategy(self, global_context, space_analysis):
        """
        Determine tactical approach based on game state
        """
        possession_balance = global_context.possession_balance
        ball_zone = global_context.ball_zone

        # If losing possession significantly, press hard
        if abs(possession_balance) > 0.4:
            losing_team = 'home' if possession_balance < 0 else 'away'

            if losing_team == 'home':
                self.home_state = 'HIGH_PRESS'
                self.home_compactness = 0.8  # Slightly compact for pressing
                self.away_state = 'POSSESSION'
                self.away_compactness = 1.2  # Spread out
            else:
                self.away_state = 'HIGH_PRESS'
                self.away_compactness = 0.8
                self.home_state = 'POSSESSION'
                self.home_compactness = 1.2

        else:
            # Balanced possession - play normally
            self.home_state = 'BALANCED'
            self.away_state = 'BALANCED'
            self.home_compactness = 1.0
            self.away_compactness = 1.0

    def get_formation_positions(self, team, base_formation):
        """
        Adjust formation based on compactness
        """
        compactness = (
            self.home_compactness if team == 'home'
            else self.away_compactness
        )

        # Scale inter-player distances
        adjusted_positions = []
        centroid = np.mean([p for p in base_formation], axis=0)

        for pos in base_formation:
            # Vector from centroid to position
            to_pos = pos - centroid
            # Scale by compactness
            adjusted_pos = centroid + to_pos * compactness
            adjusted_positions.append(adjusted_pos)

        return adjusted_positions
```

#### 3.2 Advanced Pass Decision Making
```python
def decide_pass_with_space_awareness(
    player_state,
    teammates,
    opponents,
    space_analysis
):
    """
    Choose pass target considering:
    - Safety (not marked)
    - Progressiveness (toward goal)
    - Space (into available space)
    """
    available_spaces = space_analysis['available_spaces']

    scored_targets = []

    for teammate in teammates:
        # 1. Safety score (distance to nearest opponent)
        nearest_opponent_dist = min(
            np.linalg.norm(teammate.position[:2] - opp.position[:2])
            for opp in opponents
        )
        safety_score = min(1.0, nearest_opponent_dist / 5.0)  # Safe if >5m

        # 2. Progressive score (closer to goal)
        goal_distance_player = np.linalg.norm(
            player_state.position[:2] - goal_position
        )
        goal_distance_teammate = np.linalg.norm(
            teammate.position[:2] - goal_position
        )
        progressive_score = max(
            0,
            (goal_distance_player - goal_distance_teammate) / 20.0
        )

        # 3. Space score (is teammate in available space?)
        in_space = any(
            np.linalg.norm(teammate.position[:2] - space) < 5.0
            for space in available_spaces
        )
        space_score = 1.0 if in_space else 0.3

        # Combined score
        # Weights: safety (40%), progressive (30%), space (30%)
        total_score = (
            safety_score * 0.4 +
            progressive_score * 0.3 +
            space_score * 0.3
        )

        scored_targets.append((teammate, total_score))

    # Choose best target
    if scored_targets:
        scored_targets.sort(key=lambda x: x[1], reverse=True)
        return scored_targets[0][0]

    return None
```

**Expected Result**: 93-96% balanced matches

---

## 📊 Expected Results by Phase

### Phase 1 (Foundation)
```
Time: 6-8 hours
Balanced: 70-80% (14-16 / 20 matches)
Improvement: +10-20% from V11
Key: Dynamic balancing prevents runaway
```

### Phase 2 (Coordination)
```
Time: +5-7 hours (total 11-15h)
Balanced: 85-90% (17-18 / 20 matches)
Improvement: +5-10% from Phase 1
Key: Organized pressing + space awareness
```

### Phase 3 (Advanced)
```
Time: +4-6 hours (total 15-21h)
Balanced: 93-96% (19 / 20 matches)
Improvement: +3-6% from Phase 2
Key: Adaptive tactics + intelligent passing
```

---

## 🎯 Implementation Roadmap

### Week 1: Foundation
- **Day 1-2**: GlobalContext + DynamicBalancer
- **Day 2-3**: Integration + Testing
- **Goal**: 75% balance

### Week 2: Coordination
- **Day 1-2**: SpaceAnalyzer + PressingCoordinator
- **Day 2-3**: SpaceAwareAgent + Integration
- **Goal**: 87% balance

### Week 3: Advanced
- **Day 1**: TeamStrategy state machine
- **Day 2**: Advanced pass logic
- **Day 3**: Testing + tuning
- **Goal**: 95% balance

**Total Timeline: 15-21 hours (3 weeks part-time or 2 days full-time)**

---

## 🔬 Testing Strategy

### Tier 1: Unit Tests (each component)
- GlobalContext tracking accuracy
- DynamicBalancer adjustment ranges
- SpaceAnalyzer zone calculations
- PressingCoordinator role assignments

### Tier 2: Integration Tests (phase completion)
- Phase 1: 20-match test → expect 75%±5%
- Phase 2: 20-match test → expect 87%±3%
- Phase 3: 20-match test → expect 95%±2%

### Tier 3: Stress Tests (edge cases)
- Extreme initial imbalance (90-10 start)
- Very long matches (90 min simulated)
- Mismatched team skills

---

## 🎓 Key Design Principles

### 1. Self-Balancing First
The DynamicBalancer is the **safety net** that prevents catastrophic failures. Even if other systems fail, this ensures decent balance.

### 2. Gradual Complexity
Phase 1 can ship with 75% balance. Phases 2 and 3 are incremental improvements, not all-or-nothing.

### 3. Realistic Modeling
All "artificial" adjustments (DynamicBalancer) model real phenomena:
- Fatigue → lower pass accuracy when dominant
- Desperation → harder pressing when losing
- Momentum → psychological effects

### 4. Testable Components
Each component can be tested independently, reducing debugging time.

---

## ⚠️ Risks & Mitigations

### Risk 1: Dynamic Balancer Too Obvious
**Risk**: Users notice "rubber-banding"
**Mitigation**:
- Only activate at >30% imbalance
- Gradual scaling (not sudden jumps)
- Model as fatigue/pressure (realistic)

### Risk 2: Space Analysis Performance
**Risk**: 96 zones × many calculations = slow
**Mitigation**:
- Update space map every 0.5s (not every tick)
- Use spatial hashing for zone lookups
- Target: <5% performance impact

### Risk 3: Complexity Creep
**Risk**: Over-engineering, hard to maintain
**Mitigation**:
- Ship Phase 1 alone if time constrained
- Keep each component <200 lines
- Extensive documentation

### Risk 4: Unpredictable Emergent Behavior
**Risk**: Complex interactions create new problems
**Mitigation**:
- Comprehensive logging
- Replay capability for debugging
- Gradual rollout with testing

---

## 📈 Success Metrics

### Primary Metric
**95% of matches have 30-70% possession for each team**

### Secondary Metrics
- Average possession: 48-52% (near perfect 50-50)
- Standard deviation: <20% (down from 27%)
- Performance: >60x real-time (maintain playability)
- No systematic bias (home vs away within 3%)

### Qualitative Metrics
- Matches "feel" balanced
- Visible back-and-forth play
- No obvious rubber-banding
- Tactical variety emerges

---

## 💎 Conclusion

**The path to 95% balance requires architectural change, not parameter tuning.**

Current V11 achieves 60% through:
- Individual improvements (pass failure, tackles)

Proposed redesign achieves 95% through:
- **Team intelligence** (GlobalContext, TeamStrategy)
- **Dynamic balancing** (DynamicBalancer)
- **Space awareness** (SpaceAnalyzer)
- **Organized coordination** (PressingCoordinator)

**Estimated effort: 15-21 hours across 3 phases**

**Risk: Medium (new architecture)**
**Reward: High (95% balance = world-class simulation)**

**Recommendation: Proceed with phased implementation, shipping Phase 1 as V12 beta**

---

**Status**: 📋 DESIGN COMPLETE, READY FOR IMPLEMENTATION
**Next Step**: Begin Phase 1 - GlobalContext + DynamicBalancer
**Estimated First Results**: 6-8 hours

