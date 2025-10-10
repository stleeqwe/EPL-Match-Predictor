# Phase 1 MVP Plan: 2D Physics-Based Simulation
## Soccer Predictor v4.0 - Minimum Viable Product

**Updated**: 2025-10-10
**Duration**: 1 week (7 days) - Fast track to MVP
**Focus**: 2D simulation, core physics, rapid validation

---

## 🎯 MVP Philosophy

**Key Changes from Original Plan:**
1. ✂️ **Remove 3D visualization** - Use simple 2D Canvas/SVG instead
2. ✂️ **Simplify ball physics** - 2D trajectory (still with Magnus effect on 2D plane)
3. ✂️ **Focus on core mechanics** - Player movement + ball trajectory + event detection
4. ✅ **Rapid validation** - Get working simulation in 1 week, not 2

**MVP Success Criteria:**
- Can simulate a 90-minute match in 2D
- Players move realistically based on physics
- Ball trajectory is accurate
- Basic events detected: goals, shots, passes
- Results comparable to current LLM predictor

---

## 📅 Revised 7-Day Sprint

### **Day 1-2: Complete Data Models** (Today)
**Goal**: Finish all SQLAlchemy models

- [x] Player model ✅ DONE
- [ ] Team model with tactical profiles
- [ ] MatchSimulation model
- [ ] Simple data seeding (2-3 test teams)

**Files to Create:**
- `backend/models/team.py`
- `backend/models/match_simulation.py`
- `backend/scripts/seed_test_data.py`

---

### **Day 3-4: 2D Physics Engine**
**Goal**: Working physics simulation (2D only)

#### Player Physics (2D)
- Position: [x, y] on 105m × 68m field
- Velocity: [vx, vy] in m/s
- Newton's equations: F = ma
- Stamina drain

**Simplified from 3D:**
```python
# OLD (3D):
position = [x, y, z]  # 3 dimensions
velocity = [vx, vy, vz]

# NEW (2D):
position = [x, y]  # 2 dimensions only
velocity = [vx, vy]
# z-coordinate only for ball (is it in air or on ground)
```

#### Ball Physics (2D + height)
- Position: [x, y, h] where h = height off ground
- Velocity: [vx, vy, vh]
- Gravity (affects h only)
- Drag force
- **Magnus effect in 2D**: Ball curves left/right on 2D plane

**Key Simplification:**
- No full 3D spin (ωx, ωy, ωz)
- Just single spin value (clockwise/counter-clockwise)
- Still produces realistic curving shots

**Files to Create:**
- `backend/physics/constants.py`
- `backend/physics/player_physics.py` (2D version)
- `backend/physics/ball_physics.py` (2D version)
- `backend/physics/field.py` (2D field boundaries)

---

### **Day 5: Basic Agent Behavior**
**Goal**: Players make simple decisions

**Simplified Agents:**
- Not full POMDP (save for later)
- Simple state machine:
  - `CHASE_BALL`: Move toward ball
  - `MARK_OPPONENT`: Track nearest opponent
  - `MOVE_TO_POSITION`: Return to formation position
  - `SHOOT`: Attempt shot if in range

**Position-Specific Logic:**
```python
# Simplified example:
if position == 'ST':
    if distance_to_ball < 20m and ball_in_attacking_third:
        action = 'SHOOT'
    else:
        action = 'CHASE_BALL'
elif position == 'GK':
    action = 'MOVE_TO_GOAL_LINE'
```

**Files to Create:**
- `backend/agents/simple_agent.py`
- `backend/agents/position_behaviors.py`

---

### **Day 6: Match Simulation Loop**
**Goal**: Complete 90-minute simulation

**Core Loop:**
```python
def simulate_match(home_team, away_team):
    # Initialize 22 players on field
    # Initialize ball at center

    for tick in range(5400):  # 90 min × 60 sec × 10 ticks/sec
        # 1. Each player decides action
        for player in all_players:
            action = player.decide_action(game_state)

        # 2. Update physics
        update_player_positions(dt=0.1)
        update_ball_position(dt=0.1)

        # 3. Detect events
        if ball_in_goal():
            record_goal()

        # 4. Update game state
        update_possession()

    return match_result
```

**Files to Create:**
- `backend/simulation/match_engine.py`
- `backend/simulation/event_detector.py`
- `backend/simulation/game_state.py`

---

### **Day 7: Testing & Validation**
**Goal**: Verify physics accuracy

**Unit Tests:**
- Player accelerates correctly
- Player doesn't exceed max speed
- Ball falls under gravity
- Ball curves with spin
- Goals detected correctly

**Integration Test:**
- Simulate Liverpool vs Man City
- Check final score is realistic (0-5 goals per team)
- Check possession percentage (30-70%)
- Check shot counts (5-20 per team)

**Files to Create:**
- `backend/tests/test_player_physics_2d.py`
- `backend/tests/test_ball_physics_2d.py`
- `backend/tests/test_match_simulation.py`

---

## 🎨 2D Visualization (Simple)

**For MVP, NO Three.js needed. Use simple approaches:**

### Option 1: Server-Side 2D Rendering
```python
import matplotlib.pyplot as plt

def render_match_frame(game_state):
    fig, ax = plt.subplots()
    ax.set_xlim(-52.5, 52.5)
    ax.set_ylim(-34, 34)

    # Draw field
    ax.plot([-52.5, 52.5, 52.5, -52.5, -52.5],
            [-34, -34, 34, 34, -34], 'g-')

    # Draw players
    for player in game_state.home_players:
        ax.plot(player.x, player.y, 'ro')
    for player in game_state.away_players:
        ax.plot(player.x, player.y, 'bo')

    # Draw ball
    ax.plot(game_state.ball.x, game_state.ball.y, 'ko', markersize=10)

    return fig
```

### Option 2: Frontend Canvas 2D
```javascript
// Simple 2D Canvas rendering
function renderField(gameState) {
    const canvas = document.getElementById('field');
    const ctx = canvas.getContext('2d');

    // Draw field
    ctx.fillStyle = '#2d5016';
    ctx.fillRect(0, 0, 1050, 680);  // 105m × 68m scaled

    // Draw players
    gameState.homePlayers.forEach(player => {
        ctx.fillStyle = 'red';
        ctx.fillRect(player.x * 10, player.y * 10, 5, 5);
    });

    // Draw ball
    ctx.fillStyle = 'white';
    ctx.arc(ball.x * 10, ball.y * 10, 3, 0, 2 * Math.PI);
    ctx.fill();
}
```

### Option 3: SVG Animation
```html
<svg width="1050" height="680">
    <rect width="1050" height="680" fill="#2d5016"/>

    <!-- Home players -->
    <circle cx="100" cy="340" r="5" fill="red" />

    <!-- Ball -->
    <circle cx="525" cy="340" r="8" fill="white" />
</svg>
```

**Decision: Use Option 2 (Canvas 2D) for MVP**
- Fast rendering
- Easy to update
- Good enough for validation
- Can upgrade to Three.js later

---

## 📐 Simplified Physics Equations

### 2D Player Movement
```python
# Position update (2D)
new_x = x + vx * dt
new_y = y + vy * dt

# Velocity update (Newton's 2nd law)
ax = (target_vx - vx) / dt
ay = (target_vy - vy) / dt

# Limit acceleration
a_magnitude = sqrt(ax² + ay²)
if a_magnitude > max_accel:
    ax = ax * (max_accel / a_magnitude)
    ay = ay * (max_accel / a_magnitude)

# Apply drag
ax -= drag_coef * vx
ay -= drag_coef * vy

# Update velocity
vx += ax * dt
vy += ay * dt

# Limit speed
v_magnitude = sqrt(vx² + vy²)
if v_magnitude > max_speed:
    vx = vx * (max_speed / v_magnitude)
    vy = vy * (max_speed / v_magnitude)
```

### 2D Ball Trajectory (with height)
```python
# Ball position: (x, y, h) where h = height
# Ball velocity: (vx, vy, vh)

# Horizontal movement (2D plane)
x += vx * dt
y += vy * dt

# Vertical movement (gravity)
h += vh * dt
vh -= g * dt  # g = 9.81 m/s²

# Drag (affects horizontal velocity)
drag_x = -0.5 * rho * Cd * A * vx * |v|
drag_y = -0.5 * rho * Cd * A * vy * |v|

vx += drag_x / mass * dt
vy += drag_y / mass * dt

# Magnus effect (2D curve)
# For spin in 2D (like top-spin or side-spin)
spin_force_x = -spin * vy  # Perpendicular to velocity
spin_force_y = spin * vx

vx += spin_force_x * dt
vy += spin_force_y * dt

# Ground collision
if h <= 0:
    h = 0
    vh = -vh * 0.6  # Bounce with energy loss
    spin *= 0.7  # Spin decay
```

**Key Simplifications:**
- No 3D vector cross products
- Single spin value instead of (ωx, ωy, ωz)
- Still produces realistic curving shots in 2D

---

## 🗂️ Revised File Structure

```
backend/
├── models/
│   ├── __init__.py          ✅ Done
│   ├── player.py            ✅ Done
│   ├── team.py              ⏳ Next
│   └── match_simulation.py  ⏳ Next
├── physics/
│   ├── __init__.py
│   ├── constants.py         (Physical constants)
│   ├── player_physics.py    (2D player movement)
│   ├── ball_physics.py      (2D ball + height)
│   └── field.py             (2D field boundaries)
├── agents/
│   ├── __init__.py
│   ├── simple_agent.py      (Simple state machine)
│   └── position_behaviors.py (ST, GK, CB, etc.)
├── simulation/
│   ├── __init__.py
│   ├── match_engine.py      (Main simulation loop)
│   ├── event_detector.py    (Goals, shots, passes)
│   └── game_state.py        (Current match state)
├── tests/
│   ├── test_player_physics_2d.py
│   ├── test_ball_physics_2d.py
│   └── test_match_simulation.py
└── scripts/
    └── seed_test_data.py    (Create test teams)
```

---

## 🎯 MVP Success Criteria (Revised)

### Functional Requirements
- [x] Database schema with players/teams ✅
- [x] Player model with physics conversion ✅
- [ ] Team model with tactical profiles
- [ ] 2D player physics (Newton's laws)
- [ ] 2D ball physics (gravity + spin)
- [ ] Simple agent decision-making
- [ ] 90-minute match simulation
- [ ] Event detection (goals, shots)
- [ ] Basic 2D visualization

### Performance Requirements
- [ ] Simulate 90 minutes in < 60 seconds
- [ ] Player update: < 1ms per player
- [ ] Ball update: < 0.5ms
- [ ] Total: ~3 seconds for 5,400 ticks

### Accuracy Requirements
- [ ] Goals per match: 1-5 (realistic EPL range)
- [ ] Possession: 30-70% (realistic range)
- [ ] Shots: 5-20 per team (realistic range)
- [ ] Pass accuracy: 60-90% (realistic range)

---

## 📊 Comparison: 3D vs 2D Approach

| Aspect | Original (3D) | MVP (2D) | Benefit |
|--------|---------------|----------|---------|
| **Ball Position** | [x, y, z] | [x, y, h] | Simpler math |
| **Ball Velocity** | [vx, vy, vz] | [vx, vy, vh] | Simpler |
| **Ball Spin** | [ωx, ωy, ωz] | single spin | Much simpler |
| **Magnus Force** | Cross product | Perpendicular 2D | Easy to compute |
| **Visualization** | Three.js WebGL | Canvas 2D | Faster to implement |
| **Development Time** | 14 days | 7 days | **50% faster** |
| **Complexity** | High | Medium | Easier to debug |
| **Upgrade Path** | N/A | Can add 3D later | Flexible |

**Conclusion**: 2D is perfect for MVP. Proves physics concept with 50% less development time.

---

## 🚀 Today's Action Plan (Day 1-2)

### Immediate Tasks (Next 2 hours)
1. ✅ Create Team model (`backend/models/team.py`)
2. ✅ Create MatchSimulation model (`backend/models/match_simulation.py`)
3. ✅ Create physics constants (`backend/physics/constants.py`)
4. ✅ Create 2D player physics engine (`backend/physics/player_physics.py`)
5. ✅ Create 2D ball physics engine (`backend/physics/ball_physics.py`)

### Today's Goal
- All models complete
- Physics engines 50% complete
- Ready to start simulation loop tomorrow

---

## 💡 Key Design Decisions (Updated)

| Decision | Rationale |
|----------|-----------|
| **2D instead of 3D** | MVP speed, easier debugging, good enough for validation |
| **Canvas 2D rendering** | Fast, simple, no WebGL complexity |
| **Simple agent FSM** | Postpone POMDP to Phase 2, get working simulation first |
| **7-day sprint** | Aggressive but achievable, focus on core mechanics |
| **Keep Magnus effect** | Still important for realistic shots, easy in 2D |
| **Height as separate dimension** | Ball still has vertical motion (jumps, lobs) |

---

## 📈 Success Metrics

**MVP Delivered When:**
- [x] All models created (Player ✅, Team ⏳, Match ⏳)
- [ ] Physics engines working (2D movement + ball trajectory)
- [ ] Can simulate 90-minute match
- [ ] Results match reality (1-5 goals, 5-20 shots)
- [ ] 2D visualization shows player/ball movement
- [ ] Unit tests pass (> 80% coverage)

**Timeline**: 7 days from now = **2025-10-17**

---

## 🔄 Migration to 3D (Future)

**When MVP is validated, upgrading to 3D is straightforward:**

```python
# Change from 2D:
position = np.array([x, y])

# To 3D:
position = np.array([x, y, z])

# Add full 3D spin:
spin = np.array([wx, wy, wz])

# Use cross product for Magnus:
F_magnus = np.cross(spin, velocity)
```

**Effort**: ~2-3 days to upgrade from 2D to 3D after MVP is working

---

**Status**: 🚀 Ready to build MVP
**Focus**: Core physics, 2D simulation, rapid validation
**Timeline**: 7 days to working prototype

Let's build! 💪
