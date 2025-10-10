# Agent Behavior System Design
## Haiku-Optimized with Upgrade Path

**Date**: 2025-10-10
**Version**: 1.0 MVP (Cost-Optimized)
**Model**: Claude Haiku (현재) → Sonnet/Opus (향후 업그레이드)

---

## 🎯 Design Philosophy

### Cost-First Approach
**현재 상황**: Haiku 모델 사용 중 (비용 절감)
**설계 원칙**:
1. **80/20 Rule**: 80%는 Rule-based, 20%만 LLM 사용
2. **Caching-First**: 동일 상황은 캐시에서 재사용
3. **Upgrade-Ready**: 나중에 Sonnet/Opus로 쉽게 교체

### Hybrid Architecture
```
┌─────────────────────────────────────────┐
│         Agent Decision System           │
├─────────────────────────────────────────┤
│  Layer 1: Rule-Based (FREE, 80%)        │
│  - Basic movements                      │
│  - Simple decisions (shoot if close)    │
│  - Position-specific behaviors          │
├─────────────────────────────────────────┤
│  Layer 2: Haiku LLM (CHEAP, 20%)        │
│  - Complex tactical decisions           │
│  - Opponent analysis                    │
│  - Strategic planning                   │
├─────────────────────────────────────────┤
│  Layer 3: Cache (INSTANT, 50% hits)     │
│  - Store recent decisions               │
│  - Reuse similar situations             │
└─────────────────────────────────────────┘
```

---

## 💰 Cost Analysis

### Current (Haiku Only)
| Component | API Calls | Cost per Match | Notes |
|-----------|-----------|----------------|-------|
| **Rule-based** | 0 | $0 | 80% of decisions |
| **Haiku calls** | ~50 | $0.20 | Complex decisions only |
| **Cache hits** | 0 | $0 | 50% of LLM needs |
| **Total** | 25 | **$0.10** | Very cheap! |

### Future (Sonnet PRO)
| Component | API Calls | Cost per Match | Notes |
|-----------|-----------|----------------|-------|
| **Rule-based** | 0 | $0 | Still 80% |
| **Sonnet calls** | ~50 | $4.00 | Better decisions |
| **Cache hits** | 0 | $0 | 50% cache |
| **Total** | 25 | **$2.00** | 20x increase, but worth it |

**Conclusion**: Haiku MVP로 검증 → PRO tier에서 Sonnet 제공

---

## 🏗️ System Architecture

### 3-Layer Design

#### Layer 1: SimpleAgent (Rule-Based) 🆓
**Purpose**: Handle 80% of decisions without LLM
**Cost**: $0
**Speed**: < 0.1ms

```python
class SimpleAgent:
    """
    Rule-based agent for basic decisions
    No LLM calls - purely algorithmic
    """

    def decide_action(self, game_state, player_state):
        # Rule-based decision tree
        if self.has_ball(player_state):
            if self.in_shooting_range():
                return Action.SHOOT
            if self.has_open_teammate():
                return Action.PASS
            return Action.DRIBBLE
        else:
            if self.is_closest_to_ball():
                return Action.CHASE_BALL
            return Action.MOVE_TO_POSITION
```

**Handles**:
- ✅ Chase ball (if closest)
- ✅ Shoot (if in range < 20m)
- ✅ Pass (if teammate open)
- ✅ Return to formation position
- ✅ Mark opponent (defender)
- ✅ Save shot (goalkeeper)

---

#### Layer 2: TacticalDecisionMaker (Haiku) 💵
**Purpose**: Handle 20% complex decisions with LLM
**Cost**: $0.004 per call (Haiku)
**Speed**: ~3 seconds

```python
class TacticalDecisionMaker:
    """
    Uses Claude Haiku for complex tactical decisions

    Only called when:
    - Multiple good options available
    - Opponent pattern unclear
    - Strategic planning needed
    """

    def should_use_llm(self, situation):
        # Only use LLM if truly needed
        if situation.is_simple():
            return False  # Use rule-based

        if situation.in_cache():
            return False  # Use cache

        return True  # Call Haiku

    async def get_tactical_decision(self, situation):
        if not self.should_use_llm(situation):
            return None  # Fall back to rules

        # Call Haiku
        prompt = self._build_prompt(situation)
        response = await haiku_client.generate(
            prompt=prompt,
            max_tokens=200,  # Keep it short!
            temperature=0.7
        )

        return self._parse_response(response)
```

**Handles**:
- 🧠 Complex passing options (3+ teammates open)
- 🧠 Opponent weakness exploitation
- 🧠 Strategic positioning adjustments
- 🧠 Counter-attack vs possession decision
- 🧠 Set-piece tactics

---

#### Layer 3: DecisionCache (Instant) ⚡
**Purpose**: Avoid repeat LLM calls
**Cost**: $0
**Speed**: < 1ms

```python
class DecisionCache:
    """
    Cache recent LLM decisions

    Cache key: situation_hash (position, ball location, score, time)
    Cache duration: 10 seconds (situations change)
    """

    def get(self, situation):
        key = self._hash_situation(situation)
        cached = self.cache.get(key)

        if cached and not cached.is_expired():
            self.cache_hits += 1
            return cached.decision

        self.cache_misses += 1
        return None

    def put(self, situation, decision):
        key = self._hash_situation(situation)
        self.cache[key] = CachedDecision(
            decision=decision,
            expires_at=time.now() + 10  # 10 seconds
        )
```

**Benefits**:
- ⚡ 50% cache hit rate expected
- 💰 Cuts LLM costs in half
- 🚀 Instant decisions

---

## 🎮 Position-Specific Behaviors

### Rule-Based (No LLM)

#### Goalkeeper (GK)
```python
def gk_decide(self, state):
    if ball_in_penalty_area():
        if can_catch_ball():
            return Action.CATCH
        return Action.SAVE

    if ball_far_from_goal():
        return Action.STAY_ON_LINE

    return Action.POSITION_FOR_SHOT
```

#### Center Back (CB)
```python
def cb_decide(self, state):
    if opponent_in_area():
        return Action.MARK_OPPONENT

    if ball_near():
        return Action.CLEAR_BALL

    return Action.HOLD_DEFENSIVE_LINE
```

#### Striker (ST)
```python
def st_decide(self, state):
    if has_ball():
        if in_shooting_range():
            return Action.SHOOT
        return Action.DRIBBLE_FORWARD

    if ball_in_attacking_third():
        return Action.MAKE_RUN

    return Action.HOLD_UP_PLAY
```

**8 positions × ~5 rules each = 40 total rules (covers 80% of decisions)**

---

## 🧠 When to Use Haiku (20% Cases)

### Trigger Conditions

#### 1. Complex Passing Decision
```python
if len(open_teammates) >= 3:
    # Too many options - ask Haiku
    decision = await haiku.decide_best_pass(
        teammates=open_teammates,
        opponent_positions=opponents
    )
```

#### 2. Strategic Adjustment
```python
if losing_by_2_goals and time_remaining < 20:
    # Need tactical change - ask Haiku
    adjustment = await haiku.suggest_tactical_change(
        current_formation="4-3-3",
        losing=True,
        time_left=18
    )
```

#### 3. Opponent Pattern Recognition
```python
if opponent_scored_3_times_from_same_pattern():
    # Need counter-strategy - ask Haiku
    counter = await haiku.analyze_opponent_pattern(
        recent_goals=opponent_goals
    )
```

**Estimated**: ~50 Haiku calls per 90-min match (cache reduces to ~25)

---

## 📊 Decision Flow

```
New Situation
    ↓
Is it simple? (80%) ───YES──→ Rule-Based Decision → Execute
    ↓ NO
    ↓
In cache? (50% of complex) ───YES──→ Cached Decision → Execute
    ↓ NO
    ↓
Call Haiku (10% total) ────────────→ LLM Decision → Cache → Execute
```

**Result**:
- 80% = Free (rules)
- 10% = Free (cache)
- 10% = Haiku ($0.004 each)

**Total**: ~25 Haiku calls × $0.004 = **$0.10 per match**

---

## 🔄 Upgrade Path (Future)

### BASIC Tier (Current)
```python
# config.py
AGENT_CONFIG = {
    'tier': 'BASIC',
    'llm_model': 'claude-haiku',
    'llm_calls_per_match': 25,
    'cost_per_match': 0.10,
    'decision_quality': 'Good'
}
```

### PRO Tier (Future)
```python
# config.py
AGENT_CONFIG = {
    'tier': 'PRO',
    'llm_model': 'claude-sonnet',  # Just change this!
    'llm_calls_per_match': 25,  # Same number
    'cost_per_match': 2.00,  # 20x, but much better
    'decision_quality': 'Excellent'
}
```

**No code changes needed** - just config update!

---

## 🗂️ File Structure

```
backend/
├── agents/
│   ├── __init__.py
│   ├── simple_agent.py         # Rule-based (Layer 1)
│   ├── position_behaviors.py   # GK, CB, ST, etc.
│   ├── tactical_ai.py          # Haiku integration (Layer 2)
│   ├── decision_cache.py       # Caching (Layer 3)
│   └── actions.py              # Action enum
├── simulation/
│   ├── match_engine.py         # Main loop
│   ├── game_state.py           # Current state
│   └── event_detector.py       # Goal, shot, pass detection
└── ai/
    ├── simple_predictor.py     # Existing Haiku predictor
    └── claude_client.py        # Existing Claude client
```

---

## 🎯 Implementation Plan (Day 3-4)

### Day 3 Morning: Core Agent System
- [x] Design document (this file)
- [ ] `actions.py` - Action enum (SHOOT, PASS, etc.)
- [ ] `simple_agent.py` - Rule-based decision tree
- [ ] `position_behaviors.py` - 8 position behaviors

### Day 3 Afternoon: Haiku Integration
- [ ] `tactical_ai.py` - Haiku wrapper
- [ ] `decision_cache.py` - Caching system
- [ ] Test: Single agent makes decisions

### Day 4 Morning: Integration
- [ ] Connect agents to physics engine
- [ ] Test: 22 agents on field
- [ ] Test: Agents chase ball, shoot, pass

### Day 4 Afternoon: Refinement
- [ ] Tune decision thresholds
- [ ] Add missing behaviors
- [ ] Performance optimization

---

## 🧪 Testing Strategy

### Unit Tests
```python
def test_agent_shoots_when_in_range():
    agent = SimpleAgent(position='ST')
    state = GameState(
        player_position=(40, 0),  # 12m from goal
        ball_position=(40, 0),
        has_ball=True
    )

    action = agent.decide(state)
    assert action == Action.SHOOT

def test_agent_uses_cache():
    cache = DecisionCache()
    situation = create_test_situation()

    # First call - miss
    decision1 = cache.get(situation)
    assert decision1 is None

    # Store decision
    cache.put(situation, Action.PASS)

    # Second call - hit
    decision2 = cache.get(situation)
    assert decision2 == Action.PASS
```

### Integration Test
```python
def test_full_agent_system():
    # Create 22 agents
    agents = create_team_agents()

    # Simulate 10 seconds (100 ticks)
    for tick in range(100):
        for agent in agents:
            action = agent.decide(game_state)
            execute_action(agent, action)

    # Verify
    assert no_crashes
    assert ball_moved
    assert agents_made_decisions
```

---

## 💡 Haiku Prompt Design (Cost-Optimized)

### Keep Prompts SHORT
```python
# BAD: Long prompt = high cost
prompt = f"""
You are an expert football analyst with 20 years of experience...
(500 tokens of context)
What should player {name} do?
"""

# GOOD: Concise prompt = low cost
prompt = f"""
Player at ({x},{y}), ball at ({bx},{by})
3 open teammates: A(45,10), B(40,-5), C(35,0)
Best pass target?
"""
# Only ~30 tokens!
```

### Limit Response Length
```python
response = await haiku.generate(
    prompt=prompt,
    max_tokens=50,  # Short response only!
    temperature=0.7
)
```

**Result**: ~80 tokens total (prompt + response) × $0.25/1M = **$0.00002 per call** ✅

---

## 📈 Success Metrics

| Metric | Target | How to Measure |
|--------|--------|----------------|
| **Cost** | < $0.20/match | Track API calls |
| **Cache Hit Rate** | > 40% | cache_hits / total_requests |
| **Decision Speed** | < 10ms avg | Time per decide() call |
| **LLM Usage** | < 20% | llm_calls / total_decisions |
| **Realistic Behavior** | Looks like football | Visual inspection |

---

## 🚀 Future Enhancements

### Phase 2 (Sonnet Upgrade)
- Switch to Sonnet for PRO tier
- Better tactical decisions
- Opponent modeling
- Team coordination

### Phase 3 (Advanced)
- Multi-agent communication
- Formation adjustments
- Player personality traits
- Fatigue-based decisions

---

## 📝 Notes

### Why This Design Works
1. **Cost-Effective**: 90% free (rules + cache)
2. **Fast**: Most decisions instant
3. **Scalable**: Easy to add Sonnet later
4. **Practical**: Works with current Haiku setup

### Key Decisions
- Rule-based first (80/20 rule)
- Haiku for complex only
- Cache aggressively
- Tier system for future

---

**Status**: 📝 Design Complete - Ready to Implement
**Next**: Create `simple_agent.py` with rule-based decisions
**Timeline**: Day 3-4 (2 days)

---

*Document Version: 1.0*
*Created: 2025-10-10*
*Model: Haiku (upgradable to Sonnet)*
