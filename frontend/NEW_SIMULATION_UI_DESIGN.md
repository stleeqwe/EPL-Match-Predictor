# New Simulation Dashboard UI/UX Design
**V2 Pipeline Integration - Premium Experience**

---

## 🎯 Design Goals

### Current Issues
1. ❌ **Too Basic**: Simple glassmorphism cards with minimal engagement
2. ❌ **No Pipeline Visualization**: 7 phases not represented
3. ❌ **No Scenario Display**: Multi-scenario concept invisible
4. ❌ **Poor Wait Experience**: 5-6 minutes feels longer than it is
5. ❌ **Lack of Data**: No real-time insights during processing

### Design Objectives
1. ✅ **Premium Feel**: High-end animations and visual effects
2. ✅ **7-Phase Pipeline Visualization**: Clear phase progression
3. ✅ **Scenario Cards**: Real-time scenario generation display
4. ✅ **Convergence Visualization**: Live convergence graph
5. ✅ **Immersive Experience**: Keep user engaged for 5-6 minutes
6. ✅ **Data-Rich**: Real-time statistics and insights

---

## 🎨 New UI Layout

### Layout Structure
```
┌────────────────────────────────────────────────────────────────┐
│ HEADER: Team Matchup + AI Engine Info                         │
│ Arsenal vs Liverpool | Qwen 2.5 14B + V2 Pipeline            │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│ PIPELINE PHASES (Horizontal Stepper with Animations)          │
│                                                                │
│  ①──────▶②──────▶③──────▶④──────▶⑤──────▶⑥──────▶⑦        │
│  Generate  Validate  Refine  Converge  Final   Aggregate Done│
│  Scenarios                             Simulation            │
│                                                                │
│  Current: Phase 3 - Iteration 2/5 (45%)                       │
└────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────┬──────────────────────────┐
│ LEFT PANEL (60%)                    │ RIGHT PANEL (40%)        │
│                                     │                          │
│ ┌─────────────────────────────────┐ │ ┌──────────────────────┐ │
│ │ SCENARIO CARDS (Real-time)      │ │ │ LIVE STATISTICS      │ │
│ │                                 │ │ │                      │ │
│ │ ┌─────────────────────────────┐ │ │ │ ⚡ Current Phase:   │ │
│ │ │ Scenario 1: Arsenal Attack  │ │ │ │    Phase 3          │ │
│ │ │ Probability: 35%            │ │ │ │                      │ │
│ │ │ Status: ✅ Validated        │ │ │ │ 🔄 Iterations:      │ │
│ │ │ Events: 12                  │ │ │ │    2 / 5            │ │
│ │ └─────────────────────────────┘ │ │ │                      │ │
│ │                                 │ │ │ 📊 Simulations:     │ │
│ │ ┌─────────────────────────────┐ │ │ │    1,200 / 18,300   │ │
│ │ │ Scenario 2: Liverpool Press │ │ │ │                      │ │
│ │ │ Probability: 28%            │ │ │ │ ⏱️  Elapsed:        │ │
│ │ │ Status: 🔄 Validating...    │ │ │ │    2m 15s / ~5m     │ │
│ │ │ Events: 8                   │ │ │ └──────────────────────┘ │
│ │ └─────────────────────────────┘ │ │                          │
│ │                                 │ │ ┌──────────────────────┐ │
│ │ ┌─────────────────────────────┐ │ │ │ CONVERGENCE GRAPH    │ │
│ │ │ Scenario 3: Midfield Battle │ │ │ │                      │ │
│ │ │ Probability: 22%            │ │ │ │  1.0 ┤              │ │
│ │ │ Status: ⏳ Pending          │ │ │ │      │    ●         │ │
│ │ │ Events: 0                   │ │ │ │  0.9 ┤   ●●         │ │
│ │ └─────────────────────────────┘ │ │ │      │  ●           │ │
│ │                                 │ │ │  0.8 ┤ ●            │ │
│ │ ... (4-7 scenarios total)       │ │ │      └─┬─┬─┬─┬─┬─  │ │
│ └─────────────────────────────────┘ │ │        1 2 3 4 5    │ │
│                                     │ │     Iteration        │ │
│                                     │ └──────────────────────┘ │
│                                     │                          │
│                                     │ ┌──────────────────────┐ │
│                                     │ │ PHASE TIMELINE       │ │
│                                     │ │                      │ │
│                                     │ │ ✅ Phase 1: 0:45    │ │
│                                     │ │ ✅ Phase 2: 1:20    │ │
│                                     │ │ 🔄 Phase 3: 2:15... │ │
│                                     │ │ ⏳ Phase 4: --:--  │ │
│                                     │ │ ⏳ Phase 5: --:--  │ │
│                                     │ │ ⏳ Phase 6: --:--  │ │
│                                     │ │ ⏳ Phase 7: --:--  │ │
│                                     │ └──────────────────────┘ │
└─────────────────────────────────────┴──────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│ FOOTER: System Status + Technical Info                        │
│ 🖥️  Backend: Connected | 🔋 Resources: Normal | 💾 Cache: OK  │
└────────────────────────────────────────────────────────────────┘
```

---

## 🎨 Visual Design Specifications

### Color Palette
```css
/* Primary (Pipeline Active) */
--pipeline-active: #06b6d4;      /* Cyan 500 */
--pipeline-complete: #10b981;    /* Green 500 */
--pipeline-pending: #64748b;     /* Slate 500 */

/* Scenario Cards */
--scenario-dominant: #f59e0b;    /* Amber 500 */
--scenario-secondary: #8b5cf6;   /* Violet 500 */
--scenario-low: #6b7280;         /* Gray 500 */

/* Status Colors */
--status-validating: #3b82f6;    /* Blue 500 */
--status-converged: #10b981;     /* Green 500 */
--status-pending: #94a3b8;       /* Slate 400 */
--status-error: #ef4444;         /* Red 500 */

/* Background Layers */
--bg-primary: rgba(15, 23, 42, 0.95);      /* Slate 900 */
--bg-secondary: rgba(30, 41, 59, 0.8);     /* Slate 800 */
--bg-accent: rgba(51, 65, 85, 0.6);        /* Slate 700 */
```

### Typography
```css
/* Headers */
--font-header: 'Inter', -apple-system, sans-serif;
--font-weight-header: 700;

/* Body */
--font-body: 'Inter', -apple-system, sans-serif;
--font-weight-body: 400;

/* Monospace (Stats) */
--font-mono: 'JetBrains Mono', 'Fira Code', monospace;
--font-weight-mono: 500;
```

---

## 🎬 Animation Specifications

### 1. Phase Transition Animation
```javascript
// When phase changes (e.g., Phase 2 → Phase 3)
{
  initial: { scale: 0.9, opacity: 0 },
  animate: { scale: 1, opacity: 1 },
  transition: { type: 'spring', stiffness: 300, damping: 20 }
}

// Active phase pulses
{
  animate: {
    scale: [1, 1.05, 1],
    boxShadow: [
      '0 0 0 0 rgba(6, 182, 212, 0)',
      '0 0 0 8px rgba(6, 182, 212, 0.2)',
      '0 0 0 0 rgba(6, 182, 212, 0)'
    ]
  },
  transition: { duration: 2, repeat: Infinity }
}
```

### 2. Scenario Card Entrance
```javascript
// Staggered entrance when scenarios are generated
{
  initial: { x: -100, opacity: 0, rotateY: -15 },
  animate: { x: 0, opacity: 1, rotateY: 0 },
  transition: {
    type: 'spring',
    stiffness: 200,
    damping: 15,
    delay: index * 0.15  // Stagger by 150ms
  }
}
```

### 3. Convergence Graph Animation
```javascript
// New data point appears
{
  initial: { scale: 0, y: -20 },
  animate: { scale: 1, y: 0 },
  transition: { type: 'spring', stiffness: 500 }
}

// Line drawing animation
{
  initial: { pathLength: 0, opacity: 0 },
  animate: { pathLength: 1, opacity: 1 },
  transition: { duration: 0.8, ease: 'easeInOut' }
}
```

### 4. Statistics Counter Animation
```javascript
// Number counting up
function animateValue(start, end, duration) {
  const range = end - start;
  const startTime = Date.now();

  function update() {
    const elapsed = Date.now() - startTime;
    const progress = Math.min(elapsed / duration, 1);
    const current = Math.floor(start + range * easeOutQuad(progress));

    if (progress < 1) {
      requestAnimationFrame(update);
    }
  }

  update();
}
```

---

## 📊 Component Breakdown

### 1. Pipeline Stepper Component
```jsx
<PipelineStepper>
  <PhaseStep
    number={1}
    title="Generate Scenarios"
    status="complete"  // complete | active | pending
    duration="0:45"
  />
  <PhaseStep
    number={2}
    title="Initial Validation"
    status="complete"
    duration="1:20"
  />
  <PhaseStep
    number={3}
    title="Iterative Refinement"
    status="active"
    progress={0.45}  // 45%
    iteration="2/5"
  />
  // ... etc
</PipelineStepper>
```

**Features:**
- Horizontal stepper with connecting lines
- Active phase pulses with glow effect
- Completed phases show checkmark
- Pending phases are grayed out
- Duration displayed under each phase

---

### 2. Scenario Card Component
```jsx
<ScenarioCard
  scenario={{
    name: "Arsenal Attack-Heavy",
    probability: 0.35,
    status: "validated",  // generated | validating | validated | converged
    events: 12,
    keyEvents: [
      "Saka's pace on right wing",
      "Odegaard's creativity",
      "High defensive line"
    ],
    expectedScore: "2-1",
    confidence: 0.82
  }}
  rank={1}  // 1 = dominant scenario
  isAnimating={true}
/>
```

**Visual States:**
1. **Generated** (Gray): Just created, not yet validated
2. **Validating** (Blue, pulsing): Currently running simulations
3. **Validated** (Green): Passed validation
4. **Converged** (Gold): Dominant scenario after convergence

**Card Layout:**
```
┌─────────────────────────────────────┐
│ 🏆 Scenario 1 (Dominant)           │
│                                     │
│ Arsenal Attack-Heavy                │
│                                     │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━ 35%   │
│                                     │
│ ✅ Status: Validated               │
│ ⚽ Expected: 2-1                    │
│ 📊 Events: 12                      │
│ 🎯 Confidence: 82%                 │
│                                     │
│ Key Factors:                        │
│ • Saka's pace on right wing        │
│ • Odegaard's creativity            │
│ • High defensive line vulnerability│
└─────────────────────────────────────┘
```

---

### 3. Convergence Graph Component
```jsx
<ConvergenceGraph
  data={[
    { iteration: 1, confidence: 0.72, variance: 0.15 },
    { iteration: 2, confidence: 0.85, variance: 0.09 },
    { iteration: 3, confidence: 0.91, variance: 0.05 },
    // ...
  ]}
  threshold={0.85}
  currentIteration={3}
/>
```

**Features:**
- Line graph showing confidence over iterations
- Threshold line (0.85) as dashed horizontal line
- Current iteration highlighted
- Smooth animation as new points added
- Variance shown as shaded area
- Convergence achieved indicator

---

### 4. Live Statistics Panel
```jsx
<LiveStats>
  <StatItem
    icon="⚡"
    label="Current Phase"
    value="Phase 3: Iterative Refinement"
    animated={true}
  />
  <StatItem
    icon="🔄"
    label="Iterations"
    value="2 / 5"
    progress={0.4}
  />
  <StatItem
    icon="📊"
    label="Simulations Run"
    value="1,200 / 18,300"
    progress={0.065}
    countUp={true}
  />
  <StatItem
    icon="⏱️"
    label="Elapsed Time"
    value="2m 15s / ~5m 30s"
    estimatedRemaining="3m 15s"
  />
  <StatItem
    icon="🎯"
    label="Confidence"
    value="85%"
    status={confidence >= 0.85 ? 'converged' : 'refining'}
  />
</LiveStats>
```

---

### 5. Phase Timeline Component
```jsx
<PhaseTimeline>
  <TimelineItem phase={1} status="complete" duration="0:45" />
  <TimelineItem phase={2} status="complete" duration="1:20" />
  <TimelineItem phase={3} status="active" elapsed="2:15" />
  <TimelineItem phase={4} status="pending" estimated="1:30" />
  // ...
</PhaseTimeline>
```

**Visual:**
```
✅ Phase 1: Generate Scenarios      [0:45]
✅ Phase 2: Initial Validation      [1:20]
🔄 Phase 3: Iterative Refinement    [2:15...]
⏳ Phase 4: Convergence Check       [~1:30]
⏳ Phase 5: Additional Iterations   [~0:45]
⏳ Phase 6: Final Simulation        [~1:00]
⏳ Phase 7: Result Aggregation      [~0:05]
```

---

## 🎯 User Experience Flow

### Phase 1: Generate Scenarios (0-15%)
**UI Changes:**
- Phase 1 in stepper pulses and glows
- "Generating scenarios..." message
- Empty scenario card slots appear with skeleton loading

**Events Received:**
- `phase1_started`
- `phase1_generating` (progress updates)
- `phase1_complete` (scenario count)

**User Sees:**
- Scenario cards fade in one by one (staggered)
- Each card shows: name, expected probability, status "Generated"

---

### Phase 2: Initial Validation (15-20%)
**UI Changes:**
- Phase 2 in stepper becomes active
- Scenario cards change to "Validating" state (pulsing blue border)
- Simulation counter starts incrementing

**Events Received:**
- `phase2_started`
- `phase2_validating` (progress per scenario)
- `phase2_complete`

**User Sees:**
- Each scenario card shows validation progress
- "Running 100 simulations per scenario..."
- Counter: "600 / 600 simulations complete"

---

### Phase 3-5: Iterative Refinement (20-85%)
**UI Changes:**
- Phase 3 in stepper becomes active
- Iteration counter shows "1/5", "2/5", etc.
- Convergence graph starts building
- Scenario probabilities update after each iteration

**Events Received:**
- `phase3_5_started`
- `iteration_started` (iteration number)
- `iteration_validating` (progress)
- `iteration_complete` (updated probabilities, confidence)
- `convergence_check` (confidence score, converged status)
- `convergence_reached` OR `continue_iteration`

**User Sees:**
- Iteration badge: "Iteration 2/5"
- Convergence graph adds new point
- Scenario probabilities animate to new values
- When converged: "✅ Converged after 3 iterations!" celebration animation

---

### Phase 6: Final High-Resolution Simulation (85-95%)
**UI Changes:**
- Phase 6 in stepper becomes active
- Large progress bar: "Running 18,000 final simulations..."
- Simulation counter rapidly increments

**Events Received:**
- `phase6_started`
- `phase6_progress` (frequent updates)
- `phase6_complete`

**User Sees:**
- Dramatic progress bar filling
- Counter: "15,234 / 18,000"
- "Refining predictions with high-resolution data..."

---

### Phase 7: Result Aggregation (95-100%)
**UI Changes:**
- Phase 7 in stepper becomes active
- "Aggregating results..." message
- Final calculations shown

**Events Received:**
- `phase7_started`
- `phase7_complete`
- `completed` (final result)

**User Sees:**
- Brief aggregation phase
- Completion celebration animation
- Transition to results view

---

## 🎨 Advanced Visual Effects

### 1. Particle System for Completion
```javascript
// When simulation completes
<Particles
  count={50}
  colors={['#06b6d4', '#10b981', '#f59e0b']}
  behavior="burst"
  duration={2000}
/>
```

### 2. Scenario Card Glow Effect
```css
.scenario-card.dominant {
  box-shadow:
    0 0 20px rgba(245, 158, 11, 0.4),
    0 0 40px rgba(245, 158, 11, 0.2),
    inset 0 0 20px rgba(245, 158, 11, 0.1);
  border: 2px solid #f59e0b;
  animation: glow-pulse 2s ease-in-out infinite;
}

@keyframes glow-pulse {
  0%, 100% { box-shadow: 0 0 20px rgba(245, 158, 11, 0.4); }
  50% { box-shadow: 0 0 40px rgba(245, 158, 11, 0.6); }
}
```

### 3. Data Stream Effect
```javascript
// Visualize data flowing between phases
<DataStream
  from={phase2}
  to={phase3}
  particles={20}
  speed={2}
  color="#06b6d4"
/>
```

---

## 📱 Responsive Design

### Desktop (1920x1080+)
- Full layout as shown above
- 2-column layout (60/40 split)
- All visualizations visible

### Tablet (768px - 1919px)
- 2-column layout maintained
- Slightly smaller cards
- Convergence graph simplified

### Mobile (< 768px)
- Single column layout
- Phase stepper becomes vertical
- Scenario cards stack
- Simplified graphs
- Collapsible sections

---

## 🎯 Key Improvements Over Current UI

### Current UI Issues → New Solutions

| Issue | Current | New Solution |
|-------|---------|--------------|
| **No Pipeline Visibility** | Single progress bar | 7-phase stepper with clear progression |
| **No Scenario Display** | Hidden | Real-time scenario cards with details |
| **No Convergence Info** | Not shown | Live convergence graph + confidence score |
| **Basic Animations** | Fade in/out only | Spring animations, particles, glows, data streams |
| **Minimal Data** | Just progress % | 10+ live metrics, counters, timelines |
| **Static Layout** | Fixed cards | Dynamic, responsive, immersive |
| **No Engagement** | Boring wait | Exciting, data-rich, gamified experience |

---

## 🚀 Implementation Priority

### Phase 1 (Core Functionality) - Day 1
1. ✅ Pipeline stepper component
2. ✅ Scenario card component (basic)
3. ✅ Live statistics panel
4. ✅ Backend SSE integration
5. ✅ Basic animations

### Phase 2 (Enhanced Visuals) - Day 2
1. ✅ Convergence graph component
2. ✅ Phase timeline component
3. ✅ Advanced animations (spring, particles)
4. ✅ Responsive layout
5. ✅ Polish and refinements

---

**End of Design Document**
