# Frontend V2 Pipeline Integration - Complete Analysis

**Date**: 2025-10-17
**Purpose**: Comprehensive mapping of all components, data flows, and requirements for integrating V2 Pipeline with frontend

---

## 📊 Executive Summary

### Current Status
**Frontend does NOT use V2 Pipeline** - it uses the OLD single-AI-call approach via SSE streaming endpoint.

### Critical Discovery
The backend has **TWO DIFFERENT IMPLEMENTATIONS**:

1. ✅ **V2 Pipeline** (`simulate_match_enriched()`) - Phase 1-7 multi-scenario simulation
   - Used by: `/api/v1/simulation/enriched` (non-streaming)
   - Status: ✅ Working, tested, ready

2. ❌ **OLD Version** (`simulate_with_progress()`) - Single AI call
   - Used by: `/api/v1/simulation/enriched/stream` (SSE streaming)
   - Status: ❌ Frontend currently uses THIS endpoint

---

## 🔍 Component Analysis

### 1. Backend Components

#### 1.1 EnrichedSimulationService (`backend/services/enriched_simulation_service.py`)

**Method 1: `simulate_match_enriched()` (Lines 42-214)**
```python
# ✅ V2 PIPELINE INTEGRATION
def simulate_match_enriched(self, home_team: str, away_team: str, match_context: Optional[Dict] = None):
    # Load enriched data
    home_team_data = self.loader.load_team_data(home_team)
    away_team_data = self.loader.load_team_data(away_team)

    # Get V2 Pipeline
    pipeline = get_pipeline(config=PipelineConfig(
        max_iterations=5,
        initial_runs=100,
        final_runs=3000,
        convergence_threshold=0.85
    ))

    # Run V2 Pipeline (Phase 1-7)
    success, pipeline_result, error = pipeline.run_enriched(
        home_team=home_team_data,
        away_team=away_team_data,
        match_context=match_context
    )

    # Return formatted result with pipeline_metadata
    return True, result, None
```

**Features:**
- ✅ Executes Phase 1-7 multi-scenario pipeline
- ✅ Returns `pipeline_metadata` field
- ✅ Convergence-based validation
- ✅ 6 scenarios × (100 validation runs + 3000 final runs)
- ⏱️ Processing time: 5-6 minutes (production)

---

**Method 2: `simulate_with_progress()` (Lines 216-453)**
```python
# ❌ OLD VERSION (STREAMING)
def simulate_with_progress(self, home_team: str, away_team: str, match_context: Optional[Dict] = None):
    # ...
    # Call OLD EnrichedQwenClient
    for ai_event in self.client.simulate_match_enriched_stream(
        home_team=home_team_data,
        away_team=away_team_data,
        match_context=match_context
    ):
        # Process streaming events (token_progress, match_event, final_prediction)
        yield SimulationEvent(...)
```

**Features:**
- ❌ Single AI call (no multi-scenario)
- ❌ No pipeline metadata
- ✅ Real-time SSE streaming
- ✅ Token-by-token progress updates
- ✅ Live match event commentary
- ⏱️ Processing time: ~60-90 seconds

---

#### 1.2 API Endpoints (`backend/api/v1/simulation_routes.py`)

**Endpoint 1: `/api/v1/simulation/enriched` (POST)**
```python
@simulation_bp.route('/enriched', methods=['POST'])
def simulate_match_enriched():
    # Calls: EnrichedSimulationService.simulate_match_enriched()
    # Returns: V2 Pipeline result with pipeline_metadata
```

- ✅ Uses V2 Pipeline
- ❌ No streaming
- Response time: 5-6 minutes

---

**Endpoint 2: `/api/v1/simulation/enriched/stream` (POST)**
```python
@simulation_bp.route('/enriched/stream', methods=['POST'])
def simulate_match_enriched_stream():
    # Returns: SSE stream
    # Calls: EnrichedSimulationService.simulate_with_progress()
    # Generator yields: SimulationEvent objects
```

- ❌ OLD version (single AI call)
- ✅ SSE streaming
- Response time: 60-90 seconds

---

### 2. Frontend Components

#### 2.1 MatchSimulator (`frontend/src/components/MatchSimulator.js`)

**Lines 285-290: AI Model Selection Logic**
```javascript
// Qwen AI Engine 모드인 경우 Real-time Dashboard 표시
if (aiModel === 'qwen') {
  console.log('🤖 Opening Real-time Simulation Dashboard...');
  setShowDashboard(true);  // Opens SimulationDashboard component
  return;
}
```

**Data Flow:**
```
User clicks "시뮬레이션 시작" with aiModel='qwen'
→ simulateMatch() function
→ if (aiModel === 'qwen') → setShowDashboard(true)
→ Renders SimulationDashboard component
```

---

#### 2.2 SimulationDashboard (`frontend/src/components/SimulationDashboard.js`)

**Purpose**: Real-time SSE streaming UI with progress visualization

**Key Code (Lines 38-42):**
```javascript
useEffect(() => {
  if (homeTeam && awayTeam) {
    startSimulation(homeTeam, awayTeam, matchContext);  // ← Calls SSE endpoint
  }
}, [homeTeam, awayTeam, matchContext, startSimulation]);
```

**UI Features:**
- Progress bar (0-100%)
- Real-time event timeline
- Token generation counter
- Live match commentary
- Processing time tracker

---

#### 2.3 useSSESimulation Hook (`frontend/src/hooks/useSSESimulation.js`)

**Lines 40-143: SSE Connection Logic**
```javascript
const startSimulation = useCallback((homeTeam, awayTeam, matchContext = {}) => {
  // POST to SSE endpoint
  fetch(`${API_BASE_URL}/v1/simulation/enriched/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      home_team: homeTeam,
      away_team: awayTeam,
      match_context: matchContext
    })
  }).then(response => {
    // Read SSE stream
    const reader = response.body.getReader();
    // Parse SSE events...
  });
}, [cleanup]);
```

**Event Handling (Lines 148-227):**
```javascript
const handleEvent = (eventType, eventData) => {
  switch (eventType) {
    case 'heartbeat':
      // Silent keepalive
      break;
    case 'match_event':
      // Add to match events list
      setMatchEvents(prev => [...prev, {...}]);
      break;
    case 'completed':
      // Final result
      setResult(eventData.result);
      setStatus('completed');
      break;
    // ... other event types
  }
};
```

**Progress Mapping (Lines 163-186):**
```javascript
const stageProgress = {
  'started': 0,
  'loading_home_team': 10,
  'home_team_loaded': 20,
  'loading_away_team': 25,
  'away_team_loaded': 35,
  'building_prompt': 40,
  'prompt_ready': 45,
  'ai_started': 50,
  'ai_generating': 70,  // Updates with actual AI progress
  'ai_completed': 85,
  'parsing_result': 90,
  'result_parsed': 95,
  'completed': 100
};
```

---

## 📦 Data Format Mapping

### OLD Version Response Format (SSE Streaming)
```json
{
  "success": true,
  "prediction": {
    "home_win_probability": 0.40,
    "draw_probability": 0.30,
    "away_win_probability": 0.30,
    "predicted_score": "2-1",
    "confidence": "medium",
    "expected_goals": {"home": 1.8, "away": 1.2}
  },
  "analysis": {
    "key_factors": ["...", "..."],
    "home_team_strengths": ["...", "..."],
    "away_team_strengths": ["...", "..."],
    "tactical_insight": "..."
  },
  "summary": "...",
  "teams": {
    "home": {"name": "Arsenal", "formation": "4-3-3"},
    "away": {"name": "Liverpool", "formation": "4-3-3"}
  },
  "usage": {
    "total_tokens": 2500,
    "processing_time": 72.3
  },
  "timestamp": "2025-10-17T..."
}
```

### NEW Version Response Format (V2 Pipeline)
```json
{
  "success": true,
  "prediction": {
    "home": 0.40,      // ← KEY CHANGE: home_win_probability → home
    "draw": 0.30,
    "away": 0.30       // ← KEY CHANGE: away_win_probability → away
  },
  "predicted_score": "2-1",
  "expected_goals": {"home": 1.8, "away": 1.2},
  "confidence": "high",
  "analysis": {
    "key_factors": [],  // ← EMPTY (can extract from scenarios)
    "dominant_scenario": {  // ← NEW FIELD
      "name": "Arsenal Attack-Heavy",
      "probability": 0.35,
      "reasoning": "..."
    },
    "all_scenarios": [  // ← NEW FIELD
      {"name": "...", "probability": 0.35, ...},
      {"name": "...", "probability": 0.25, ...},
      // ... 4-6 more scenarios
    ],
    "tactical_insight": "Simulation converged after 3 iterations."
  },
  "summary": "Arsenal vs Liverpool: Arsenal Attack-Heavy",
  "teams": {
    "home": {"name": "Arsenal", "formation": "4-3-3"},
    "away": {"name": "Liverpool", "formation": "4-3-3"}
  },
  "pipeline_metadata": {  // ← NEW SECTION!
    "converged": true,
    "iterations": 3,
    "total_simulations": 18300,  // 5 iterations × 6 scenarios × 100 runs + 6 scenarios × 3000 runs
    "scenarios_count": 6
  },
  "usage": {
    "total_tokens": 0,      // ← Pipeline doesn't track (multiple AI calls)
    "processing_time": 330.5,
    "cost_usd": 0.0
  },
  "match_context": {...},
  "timestamp": "2025-10-17T..."
}
```

### Key Differences Table

| Field | OLD Version | NEW Version (V2) | Notes |
|-------|-------------|------------------|-------|
| `prediction.home` | N/A | ✅ Present | Was `prediction.home_win_probability` |
| `prediction.draw` | N/A | ✅ Present | Was `prediction.draw_probability` |
| `prediction.away` | N/A | ✅ Present | Was `prediction.away_win_probability` |
| `prediction.home_win_probability` | ✅ Present | ❌ Removed | Now just `home` |
| `prediction.draw_probability` | ✅ Present | ❌ Removed | Now just `draw` |
| `prediction.away_win_probability` | ✅ Present | ❌ Removed | Now just `away` |
| `analysis.key_factors` | Populated | Empty array | Can extract from scenarios |
| `analysis.dominant_scenario` | N/A | ✅ NEW | Most probable scenario |
| `analysis.all_scenarios` | N/A | ✅ NEW | All 5-7 scenarios |
| `pipeline_metadata` | N/A | ✅ NEW | Convergence info |
| `usage.total_tokens` | ~2500 | 0 | Pipeline = multiple AI calls |

---

## 🔄 Current Data Flow (OLD Version)

```
┌─────────────────────────────────────────────────────────────────────┐
│ FRONTEND                                                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  MatchSimulator.js (aiModel === 'qwen')                            │
│         │                                                           │
│         ├─► setShowDashboard(true)                                 │
│         │                                                           │
│         ▼                                                           │
│  SimulationDashboard.js                                             │
│         │                                                           │
│         ├─► useSSESimulation()                                      │
│         │         │                                                 │
│         │         └─► startSimulation(homeTeam, awayTeam, context) │
│         │                                                           │
└─────────┼───────────────────────────────────────────────────────────┘
          │
          │ POST /v1/simulation/enriched/stream
          │ (SSE Streaming Endpoint)
          ▼
┌─────────────────────────────────────────────────────────────────────┐
│ BACKEND                                                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  simulation_routes.py                                               │
│    /enriched/stream endpoint                                        │
│         │                                                           │
│         ├─► EnrichedSimulationService.simulate_with_progress()     │
│         │         │                                                 │
│         │         ├─► Load enriched team data                       │
│         │         │                                                 │
│         │         ├─► EnrichedQwenClient.simulate_match_enriched_stream() │
│         │         │         │                                       │
│         │         │         └─► ❌ SINGLE AI CALL (No V2 Pipeline) │
│         │         │                                                 │
│         │         └─► Yield SimulationEvent objects                 │
│         │                                                           │
│         └─► Stream SSE events back to frontend                      │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

⏱️ Processing Time: 60-90 seconds
🎯 Method: Single AI call to Qwen 2.5 14B
📊 Scenarios: 1 (no multi-scenario simulation)
```

---

## 🚀 Target Data Flow (V2 Pipeline)

### Approach A: Non-Streaming (Simple but Poor UX)

```
Frontend                   Backend
   │                          │
   ├─► POST /enriched         │
   │                          ├─► V2 Pipeline (5-6 min)
   │                          │    Phase 1-7...
   │   ⏳ Wait 5-6 min        │
   │   (No progress)          │
   │                          │
   │◄── Response ─────────────┤
   │   (pipeline_metadata)    │
```

**PRO**: Simple implementation (just change endpoint)
**CON**: Poor UX (5-6 min with no feedback)

---

### Approach B: V2 Pipeline with SSE Streaming (RECOMMENDED)

```
┌─────────────────────────────────────────────────────────────────────┐
│ FRONTEND                                                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  SimulationDashboard.js                                             │
│         │                                                           │
│         ├─► useSSESimulation()                                      │
│         │         │                                                 │
│         │         └─► startSimulation() → POST /enriched/stream    │
│         │                                                           │
│         └─► Display Progress:                                       │
│              ├─ Phase 1: Generating scenarios (0-10%)              │
│              ├─ Phase 2-5: Validating (10-85%)                     │
│              ├─ Phase 6: Final simulation (85-95%)                 │
│              └─ Phase 7: Aggregating (95-100%)                     │
│                                                                     │
└─────────┼───────────────────────────────────────────────────────────┘
          │
          │ SSE Stream with V2 Pipeline events
          ▼
┌─────────────────────────────────────────────────────────────────────┐
│ BACKEND (MODIFIED)                                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  EnrichedSimulationService.simulate_with_progress_v2() [NEW!]       │
│         │                                                           │
│         ├─► Load enriched team data                                 │
│         │         │                                                 │
│         │         └─► Yield: loading_home_team, home_team_loaded   │
│         │                                                           │
│         ├─► Get V2 Pipeline                                         │
│         │         │                                                 │
│         │         └─► Yield: phase1_started                         │
│         │                                                           │
│         ├─► Phase 1: Generate Scenarios                             │
│         │         │                                                 │
│         │         └─► Yield: phase1_complete (6 scenarios)          │
│         │                                                           │
│         ├─► Phase 2-5: Iterative Refinement (5 iterations)          │
│         │         │                                                 │
│         │         ├─► Iteration 1 → Yield: iteration_progress (20%)│
│         │         ├─► Iteration 2 → Yield: iteration_progress (40%)│
│         │         ├─► Iteration 3 → Yield: iteration_progress (60%)│
│         │         ├─► Iteration 4 → Yield: iteration_progress (80%)│
│         │         └─► Iteration 5 → Yield: convergence_reached     │
│         │                                                           │
│         ├─► Phase 6: Final High-Resolution Simulation               │
│         │         │                                                 │
│         │         └─► Yield: final_simulation_progress (90%)        │
│         │                                                           │
│         ├─► Phase 7: Aggregate Results                              │
│         │         │                                                 │
│         │         └─► Yield: aggregation_complete                   │
│         │                                                           │
│         └─► Yield: completed (with pipeline_metadata)               │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

⏱️ Processing Time: 5-6 minutes
🎯 Method: V2 Pipeline (Phase 1-7)
📊 Scenarios: 5-7 scenarios with convergence validation
✅ Real-time Progress: Phase-by-phase updates
```

**PRO**: Best UX (real-time progress for 5-6 min task)
**PRO**: Uses V2 Pipeline (multi-scenario, convergence-based)
**CON**: Requires backend modifications (add streaming to pipeline)

---

## 📋 Implementation Requirements

### Option 1: Non-Streaming (Quick Fix)

#### Backend Changes: NONE
- Non-streaming endpoint already works!

#### Frontend Changes:

**1. Update `useSSESimulation.js`**
- Add new function `startSimulationNonStreaming()`
- Use regular `fetch()` instead of SSE stream
- Show loading state during wait

**2. Update `SimulationDashboard.js`**
- Add loading spinner UI
- Remove real-time progress components
- Show "Processing... please wait 5-6 minutes" message

**3. Update response parsing**
- Handle new field names:
  - `prediction.home` instead of `prediction.home_win_probability`
  - `prediction.away` instead of `prediction.away_win_probability`
- Parse new `pipeline_metadata` field
- Display convergence status

**Estimated Effort**: 2-3 hours

---

### Option 2: V2 Pipeline with SSE Streaming (RECOMMENDED)

#### Backend Changes:

**1. Modify `simulation_pipeline.py`**
- Add event callback support to `run_enriched()` method
- Yield events after each phase:
  ```python
  def run_enriched(self, home_team, away_team, match_context, event_callback=None):
      if event_callback:
          event_callback({'phase': 1, 'status': 'started', 'progress': 0})

      # Phase 1: Generate scenarios
      scenarios = enriched_generator.generate_scenarios_enriched(...)
      if event_callback:
          event_callback({'phase': 1, 'status': 'complete', 'scenarios_count': len(scenarios)})

      # Phase 2-5: Iterative refinement
      for iteration in range(max_iterations):
          if event_callback:
              event_callback({
                  'phase': '2-5',
                  'status': 'iteration',
                  'iteration': iteration + 1,
                  'progress': (iteration + 1) / max_iterations
              })
      # ... etc
  ```

**2. Create `simulate_with_progress_v2()` in `enriched_simulation_service.py`**
```python
def simulate_with_progress_v2(self, home_team: str, away_team: str, match_context: Optional[Dict] = None):
    """
    Run V2 Pipeline with SSE streaming progress updates.
    """
    start_time = time.time()

    # Event 1: Started
    yield SimulationEvent.started(home_team, away_team, match_context)

    # Event 2-3: Load teams
    yield SimulationEvent.loading_home_team(home_team)
    home_team_data = self.loader.load_team_data(home_team)
    yield SimulationEvent.home_team_loaded(home_team, len(home_team_data.lineup), home_team_data.formation)

    # ... (similar for away team)

    # Event 4: Phase 1 Start
    yield SimulationEvent(
        event_type='phase1_started',
        data={'message': 'Phase 1: Generating scenarios...', 'progress': 0}
    )

    # Get pipeline with event callback
    pipeline = get_pipeline(...)

    def pipeline_event_handler(event_data):
        # Convert pipeline events to SSE events
        if event_data['phase'] == 1:
            yield SimulationEvent(
                event_type='phase1_progress',
                data={'progress': 10, ...}
            )
        # ... handle other phases

    # Run pipeline with callback
    success, result, error = pipeline.run_enriched(
        home_team=home_team_data,
        away_team=away_team_data,
        match_context=match_context,
        event_callback=pipeline_event_handler
    )

    # Event Final: Completed
    yield SimulationEvent.completed(result, time.time() - start_time)
```

**3. Update `/enriched/stream` endpoint**
```python
@simulation_bp.route('/enriched/stream', methods=['POST'])
def simulate_match_enriched_stream():
    # ...
    def generate():
        # Call NEW simulate_with_progress_v2()
        for event in enriched_service.simulate_with_progress_v2(home_team, away_team, match_context):
            yield event.to_sse_format()

    return Response(stream_with_context(generate()), mimetype='text/event-stream', ...)
```

#### Frontend Changes:

**1. Update `useSSESimulation.js`**
- Add new event types:
  - `phase1_started`, `phase1_complete`
  - `phase2_5_started`, `iteration_progress`, `convergence_reached`
  - `phase6_started`, `final_simulation_progress`
  - `phase7_started`, `aggregation_complete`

**2. Update progress mapping**
```javascript
const stageProgress = {
  'started': 0,
  'loading_home_team': 2,
  'home_team_loaded': 5,
  'loading_away_team': 6,
  'away_team_loaded': 10,
  'phase1_started': 10,
  'phase1_complete': 15,
  'phase2_5_started': 15,
  'iteration_progress': 15 + (progress * 70),  // 15-85%
  'convergence_reached': 85,
  'phase6_started': 85,
  'final_simulation_progress': 85 + (progress * 10),  // 85-95%
  'phase7_started': 95,
  'aggregation_complete': 98,
  'completed': 100
};
```

**3. Update `SimulationDashboard.js`**
- Display current pipeline phase
- Show iteration count (e.g., "Iteration 3/5")
- Display scenarios count
- Show convergence status
- Add `pipeline_metadata` section to results

**4. Update response parsing in `MatchSimulator.js`**
- Handle new field names:
  ```javascript
  const pred = dashboardResult.prediction;
  const homeWinProb = pred.home || pred.home_win_probability;  // Support both
  const drawProb = pred.draw || pred.draw_probability;
  const awayWinProb = pred.away || pred.away_win_probability;
  ```

**5. Add V2 Pipeline info display**
```javascript
{result.pipeline_metadata && (
  <div className="pipeline-info">
    <h4>🔄 V2 Pipeline Status</h4>
    <p>Converged: {result.pipeline_metadata.converged ? 'Yes' : 'No'}</p>
    <p>Iterations: {result.pipeline_metadata.iterations}</p>
    <p>Total Simulations: {result.pipeline_metadata.total_simulations.toLocaleString()}</p>
    <p>Scenarios: {result.pipeline_metadata.scenarios_count}</p>
  </div>
)}
```

**Estimated Effort**: 1-2 days

---

## 🎯 Recommendation

### Recommended Approach: **Option 2 (V2 Pipeline with SSE Streaming)**

**Rationale:**
1. ✅ **Best UX**: Real-time progress for 5-6 minute task
2. ✅ **Full V2 Pipeline**: Multi-scenario, convergence-based simulation
3. ✅ **Future-proof**: Streaming architecture scales for more complex pipelines
4. ✅ **User Engagement**: Live progress reduces perceived wait time
5. ✅ **Transparency**: Shows pipeline phases, builds trust in AI system

**Trade-offs:**
- ⏱️ More implementation time (1-2 days vs 2-3 hours)
- 🔧 Requires pipeline modifications (add event callback support)
- BUT: Superior user experience worth the investment

---

## 📝 Next Steps

1. **User Confirmation**: Get user approval on implementation approach
2. **Backend Implementation**:
   - Add event callback to `SimulationPipeline.run_enriched()`
   - Create `simulate_with_progress_v2()` method
   - Add new SSE event types to `SimulationEvent`
3. **Frontend Implementation**:
   - Update `useSSESimulation` hook
   - Add new progress stages to `SimulationDashboard`
   - Update response parsing in `MatchSimulator`
   - Add V2 Pipeline metadata display
4. **Testing**:
   - E2E test with SSE streaming
   - Verify all 7 phases emit events correctly
   - Test convergence scenarios (early stop vs max iterations)
   - Test frontend UI updates at each phase
5. **Deployment**:
   - Update documentation
   - Add performance metrics logging
   - Monitor real-world usage

---

**End of Analysis**
