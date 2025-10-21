# E2E Integration Plan: EnrichedQwenClient → Frontend
## Frontend-Backend 완전 통합 설계

**Date**: 2025-10-16
**Goal**: EnrichedQwenClient를 Frontend에 연결하여 완전한 E2E 테스트 가능하도록 구축

---

## Phase 1: 현재 상태 분석 (COMPLETED)

### 1.1 Frontend 현황
**File**: `frontend/src/components/MatchSimulator.js`

**현재 동작**:
- 클라이언트 사이드 시뮬레이션만 사용
- `simulateBasic()`, `simulatePro()`, `simulateSuper()` 함수로 간단한 수학 계산
- Backend API 호출 **없음**

**데이터 소스**:
- `teamScores`: Backend에서 `/api/teams/{team}/overall_score` 호출
- `checkSimulationReadiness`: Backend에서 `/api/teams/{team}/simulation-ready` 호출

**문제점**:
- EnrichedQwenClient의 강력한 AI 분석을 사용 안함
- 사용자가 입력한 domain 데이터(선수 평가, 전술, 포메이션)를 활용 안함
- 클라이언트 사이드 랜덤 계산으로는 정확도 낮음

### 1.2 Backend 현황

**API Routes** (`backend/api/v1/simulation_routes.py`):
1. `POST /api/v1/simulation/simulate` - simulation_service → ai_factory → QwenClient (legacy)
2. `POST /api/v1/simulation/predict` - v2.0 MatchSimulator (AI 기반)

**AI Clients**:
1. `QwenClient` (legacy) - 기본 프롬프트, 제한된 데이터
2. `EnrichedQwenClient` (Phase 3) ✅ - Enriched Domain Data 활용, 7-section prompt

**Data**:
- `EnrichedDomainDataLoader` ✅ - 20개 팀 전체 데이터 로드 가능
- 선수별 10-12개 속성, 팀 전술, 포메이션, 라인업

**문제점**:
- EnrichedQwenClient가 API 엔드포인트에 연결 안됨
- Frontend에서 접근할 방법이 없음

### 1.3 Gap Analysis

| Component | Status | Issue |
|-----------|--------|-------|
| EnrichedQwenClient | ✅ Implemented | Not exposed via API |
| EnrichedDomainDataLoader | ✅ Ready | Not used in API routes |
| Frontend | ⚠️ Client-side only | Not calling backend AI |
| API Route | ❌ Missing | No `/enriched` endpoint |
| E2E Flow | ❌ Broken | Frontend → Backend not connected |

---

## Phase 2: E2E 통합 아키텍처 설계

### 2.1 목표 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend                                 │
│  MatchSimulator.js                                               │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ User selects teams                                          │ │
│  │ ↓                                                           │ │
│  │ Click "가상 대결 시작"                                       │ │
│  │ ↓                                                           │ │
│  │ POST /api/v1/simulation/enriched                            │ │
│  │ Body: { home_team, away_team }                              │ │
│  └────────────────────────────────────────────────────────────┘ │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTP Request
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│                     Backend API                                  │
│  simulation_routes.py                                            │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ @simulation_bp.route('/enriched', methods=['POST'])         │ │
│  │ def simulate_match_enriched():                              │ │
│  │   1. Load EnrichedTeamInput for home_team                   │ │
│  │   2. Load EnrichedTeamInput for away_team                   │ │
│  │   3. Call EnrichedQwenClient.simulate_match_enriched()      │ │
│  │   4. Return enriched prediction                             │ │
│  └────────────────────────────────────────────────────────────┘ │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│                EnrichedDomainDataLoader                          │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ load_team_data(team_name)                                   │ │
│  │ → EnrichedTeamInput                                         │ │
│  │   - 11 players (10-12 attrs each)                           │ │
│  │   - Formation (4-3-3, 4-2-3-1, etc)                         │ │
│  │   - Tactics (defensive, offensive, transition)              │ │
│  │   - Derived strengths (attack, defense, midfield)           │ │
│  │   - User commentary (player & team)                         │ │
│  └────────────────────────────────────────────────────────────┘ │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│                   EnrichedQwenClient                             │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ simulate_match_enriched(home_team, away_team)               │ │
│  │ 1. Build 7-section enriched prompt                          │ │
│  │ 2. Call Qwen 2.5 14B (Ollama)                               │ │
│  │ 3. Parse AI response                                        │ │
│  │ 4. Return prediction:                                       │ │
│  │    - probabilities (home/draw/away)                         │ │
│  │    - predicted_score                                        │ │
│  │    - confidence                                             │ │
│  │    - analysis (key_factors, tactical_insight)               │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Data Flow

```
User Input (Frontend)
  ↓
Team Selection: "Arsenal" vs "Liverpool"
  ↓
HTTP POST /api/v1/simulation/enriched
  ↓
Backend: Load Enriched Domain Data
  - Arsenal: 11 players, 4-3-3, tactics, commentary
  - Liverpool: 11 players, 4-3-3, tactics, commentary
  ↓
Backend: EnrichedQwenClient.simulate_match_enriched()
  - Build 7-section prompt (~1500 tokens)
  - Call Qwen AI (60-90s)
  - Parse JSON response
  ↓
Backend: Return prediction
  {
    "success": true,
    "prediction": {
      "home_win_probability": 0.40,
      "draw_probability": 0.30,
      "away_win_probability": 0.30,
      "predicted_score": "1-2",
      "confidence": "medium",
      "expected_goals": {"home": 1.5, "away": 1.8}
    },
    "analysis": {
      "key_factors": [...],
      "tactical_insight": "..."
    }
  }
  ↓
Frontend: Display results
  - Show predicted score
  - Show probabilities
  - Show AI analysis
```

---

## Phase 3: 구현 계획

### 3.1 Backend Implementation

#### Step 3.1.1: Create Enriched Service Layer

**File**: `backend/services/enriched_simulation_service.py` (NEW)

**Purpose**: Orchestrate enriched simulation workflow

**Functions**:
```python
class EnrichedSimulationService:
    def __init__(self):
        self.loader = EnrichedDomainDataLoader()
        self.client = get_enriched_qwen_client()

    def simulate_match_enriched(
        self,
        home_team: str,
        away_team: str,
        match_context: Optional[Dict] = None
    ) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Full enriched simulation workflow:
        1. Load enriched data for both teams
        2. Call EnrichedQwenClient
        3. Format response for frontend
        """

def get_enriched_simulation_service() -> EnrichedSimulationService:
    """Singleton"""
```

#### Step 3.1.2: Add API Endpoint

**File**: `backend/api/v1/simulation_routes.py` (MODIFY)

**New Route**:
```python
@simulation_bp.route('/enriched', methods=['POST'])
def simulate_match_enriched():
    """
    Enriched match simulation using domain data.

    Request Body:
    {
        "home_team": "Arsenal",
        "away_team": "Liverpool",
        "match_context": {  // Optional
            "venue": "Emirates Stadium",
            "competition": "Premier League",
            "importance": "top_clash"
        }
    }

    Response:
    {
        "success": true,
        "prediction": {
            "home_win_probability": 0.40,
            "draw_probability": 0.30,
            "away_win_probability": 0.30,
            "predicted_score": "1-2",
            "confidence": "medium",
            "expected_goals": {"home": 1.5, "away": 1.8}
        },
        "analysis": {
            "key_factors": ["factor1", "factor2", ...],
            "home_team_strengths": [...],
            "away_team_strengths": [...],
            "tactical_insight": "..."
        },
        "summary": "..."
        "usage": {
            "total_tokens": 1500,
            "processing_time": 72.3
        },
        "timestamp": "2025-10-16T..."
    }
    """
```

### 3.2 Frontend Implementation

#### Step 3.2.1: Update API Service

**File**: `frontend/src/services/api.js` (MODIFY)

**Add Function**:
```javascript
export const simulateMatchEnriched = async (homeTeam, awayTeam, matchContext = null) => {
  const response = await fetch('http://localhost:5001/api/v1/simulation/enriched', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      home_team: homeTeam,
      away_team: awayTeam,
      match_context: matchContext
    })
  });

  if (!response.ok) {
    throw new Error(`Enriched simulation failed: ${response.statusText}`);
  }

  return response.json();
};
```

#### Step 3.2.2: Update MatchSimulator Component

**File**: `frontend/src/components/MatchSimulator.js` (MODIFY)

**Changes**:
1. Add toggle to switch between "Client-side" and "AI Engine (Qwen)"
2. Modify `simulateMatch()` function:
   - If AI mode: Call `simulateMatchEnriched()` API
   - If client mode: Keep existing logic
3. Display AI analysis results:
   - Probabilities
   - Key factors
   - Tactical insight

**UI Design**:
```javascript
// Add mode selector
const [simulationMode, setSimulationMode] = useState('ai'); // 'ai' or 'client'

// Modified simulateMatch
const simulateMatch = async () => {
  if (simulationMode === 'ai') {
    // Call backend EnrichedQwenClient
    const result = await simulateMatchEnriched(homeTeam, awayTeam);
    setResult({
      ...result,
      mode: 'ai'
    });
  } else {
    // Existing client-side logic
    // ...
  }
};
```

### 3.3 Error Handling

**Backend Errors**:
1. Team not found → 404
2. Simulation data incomplete → 400 with missing items
3. AI generation failed → 500 with error message
4. Ollama not available → 503

**Frontend Errors**:
1. Network error → Retry logic
2. Server error → Display error message
3. Timeout (>120s) → Show progress indicator

---

## Phase 4: Testing Strategy

### 4.1 Backend Unit Tests

**File**: `backend/test_enriched_service_integration.py` (NEW)

**Tests**:
1. Test EnrichedSimulationService creation
2. Test simulate_match_enriched() with valid teams
3. Test error handling (invalid team, missing data)
4. Test response format validation

### 4.2 Backend API Tests

**File**: `backend/test_enriched_api_endpoint.py` (NEW)

**Tests**:
1. POST /api/v1/simulation/enriched with valid body
2. Test 400 errors (missing fields, invalid teams)
3. Test 503 error (Ollama down)
4. Test response time (<120s)

### 4.3 E2E Tests

**Test Scenarios**:
1. **Happy Path**:
   - User selects Arsenal vs Liverpool
   - Clicks "가상 대결 시작"
   - AI mode selected
   - Backend processes enriched data
   - Frontend displays AI prediction

2. **Client Mode**:
   - User selects basic/pro/super
   - Client-side simulation runs
   - Results displayed (no AI analysis)

3. **Error Cases**:
   - Team data incomplete → Show missing items
   - Ollama not available → Fallback to client mode?
   - Network timeout → Retry prompt

### 4.4 Test Data

**Teams to Test**:
- Arsenal vs Liverpool (Top 4)
- Man City vs Chelsea (Title contenders)
- Fulham vs Brentford (Mid-table)
- Burnley vs Leeds (Bottom)

**Expected Results**:
- All 20 teams should work
- AI predictions should be reasonable
- Response time: 60-90s
- Token usage: ~1500/match

---

## Phase 5: Implementation Order

### Day 1: Backend Core (4-6 hours)

**Priority 1**: Enriched Service Layer
1. Create `services/enriched_simulation_service.py`
2. Implement `EnrichedSimulationService` class
3. Write unit tests
4. Verify with 2-3 team pairs

**Priority 2**: API Endpoint
1. Add `/enriched` route to `simulation_routes.py`
2. Implement request validation
3. Implement error handling
4. Test with curl/Postman

### Day 2: Frontend Integration (3-5 hours)

**Priority 1**: API Service
1. Add `simulateMatchEnriched()` to `api.js`
2. Test API call independently

**Priority 2**: MatchSimulator Update
1. Add simulation mode toggle (AI vs Client)
2. Modify `simulateMatch()` function
3. Add AI results display component
4. Style AI analysis section

### Day 3: E2E Testing & Polish (2-4 hours)

**Priority 1**: E2E Tests
1. Test all 20 teams
2. Test error scenarios
3. Test performance (response time)

**Priority 2**: UX Polish
1. Loading states (60-90s wait)
2. Progress indicators
3. Error messages
4. Success animations

**Priority 3**: Documentation
1. Update README with new flow
2. Add API documentation
3. User guide for AI mode

---

## Phase 6: Success Criteria

### Must-Have (Phase 1)
1. ✅ Backend `/api/v1/simulation/enriched` endpoint working
2. ✅ Frontend can call endpoint and display results
3. ✅ All 20 teams work correctly
4. ✅ AI predictions are reasonable
5. ✅ Error handling works

### Nice-to-Have (Phase 2)
1. ⏸️ Mode toggle (AI vs Client-side)
2. ⏸️ Loading progress indicator
3. ⏸️ Animated AI analysis display
4. ⏸️ Compare AI vs Client results

### Future Enhancements (Phase 3+)
1. ⏸️ Cache AI predictions (1 hour TTL)
2. ⏸️ Batch simulation (multiple matches)
3. ⏸️ Historical comparison (track accuracy)
4. ⏸️ User feedback on predictions

---

## Phase 7: Risk Assessment

### High Risk
1. **Ollama Availability**:
   - Mitigation: Health check, fallback to client mode

2. **Response Time (60-90s)**:
   - Mitigation: Progress indicator, async processing

3. **Token Limit Overflow**:
   - Mitigation: Already tested, ~1500 tokens is safe

### Medium Risk
1. **Team Data Incomplete**:
   - Mitigation: Validation before simulation, clear error messages

2. **Network Timeout**:
   - Mitigation: 120s timeout, retry logic

### Low Risk
1. **Frontend State Management**:
   - Mitigation: Simple useState, no Redux needed

2. **Browser Compatibility**:
   - Mitigation: Standard fetch API, works in all modern browsers

---

## Phase 8: Rollback Plan

### If E2E Integration Fails:
1. Keep existing client-side simulation as default
2. Offer AI mode as "experimental" feature
3. Add toggle to disable AI mode

### If Performance Issues:
1. Increase timeout to 180s
2. Add queue system for multiple requests
3. Cache predictions

### If Data Issues:
1. Validate data before simulation
2. Show clear error messages
3. Guide user to complete missing data

---

## Appendix A: API Contract

### Request
```typescript
POST /api/v1/simulation/enriched

Body: {
  home_team: string;          // Required: Team name (e.g., "Arsenal")
  away_team: string;          // Required: Team name (e.g., "Liverpool")
  match_context?: {           // Optional: Match context
    venue?: string;           // e.g., "Emirates Stadium"
    competition?: string;     // e.g., "Premier League"
    importance?: string;      // e.g., "top_clash", "league_match"
    weather?: string;         // e.g., "Clear", "Rainy"
  }
}
```

### Response (Success)
```typescript
{
  success: true;
  prediction: {
    home_win_probability: number;    // 0.0 - 1.0
    draw_probability: number;        // 0.0 - 1.0
    away_win_probability: number;    // 0.0 - 1.0
    predicted_score: string;         // e.g., "2-1"
    confidence: "low" | "medium" | "high";
    expected_goals: {
      home: number;                  // e.g., 1.8
      away: number;                  // e.g., 1.2
    };
  };
  analysis: {
    key_factors: string[];           // e.g., ["High pressing intensity", ...]
    home_team_strengths: string[];   // e.g., ["Creative midfield", ...]
    away_team_strengths: string[];   // e.g., ["Solid defense", ...]
    tactical_insight: string;        // Paragraph of analysis
  };
  summary: string;                   // Brief summary
  usage: {
    total_tokens: number;            // e.g., 1512
    processing_time: number;         // Seconds, e.g., 72.3
  };
  timestamp: string;                 // ISO 8601
}
```

### Response (Error)
```typescript
{
  success: false;
  error: string;                     // Error message
  message?: string;                  // Detailed error description
  missing_items?: string[];          // If data incomplete
}
```

---

## Appendix B: Frontend Component Structure

```jsx
<MatchSimulator>
  {/* Mode Selector */}
  <ModeToggle
    value={simulationMode}
    onChange={setSimulationMode}
    options={[
      { value: 'ai', label: 'AI Engine (Qwen)', icon: '🤖' },
      { value: 'client', label: 'Client-side', icon: '⚡' }
    ]}
  />

  {/* Team Selection */}
  <TeamSelection
    homeTeam={homeTeam}
    awayTeam={awayTeam}
    onChange={(home, away) => {...}}
  />

  {/* Simulate Button */}
  <Button
    onClick={simulateMatch}
    disabled={!homeTeam || !awayTeam || simulating}
    loading={simulating}
  >
    {simulationMode === 'ai' ? 'AI 예측 시작 (60-90초)' : '빠른 시뮬레이션'}
  </Button>

  {/* Results */}
  {result && (
    <>
      {/* Score Display */}
      <ScoreDisplay result={result} />

      {/* AI Analysis (only if mode === 'ai') */}
      {result.mode === 'ai' && (
        <AIAnalysisPanel
          prediction={result.prediction}
          analysis={result.analysis}
          summary={result.summary}
        />
      )}
    </>
  )}
</MatchSimulator>
```

---

**END OF PLAN**

---

## Summary

This plan provides a complete roadmap for integrating EnrichedQwenClient with the Frontend:

1. **Phase 1**: Analysis (COMPLETED)
2. **Phase 2**: Architecture Design (DOCUMENTED)
3. **Phase 3**: Implementation Plan (DETAILED)
4. **Phase 4**: Testing Strategy (COMPREHENSIVE)
5. **Phase 5**: Execution Order (PRIORITIZED)
6. **Phase 6**: Success Criteria (MEASURABLE)
7. **Phase 7**: Risk Assessment (PROACTIVE)
8. **Phase 8**: Rollback Plan (SAFETY NET)

**Next Step**: Begin Phase 5 Day 1 - Backend Core Implementation

**Estimated Total Time**: 9-15 hours
**Difficulty**: Medium (Well-defined, incremental)
**Risk Level**: Low (All components tested individually)
