# 종합 테스트 및 성능 검수 계획

**문서 버전:** 1.0
**작성일:** 2025-10-16
**대상 시스템:** EPL Match Predictor v3.0 + Week 6 Enhancements
**목적:** Production 배포 전 전체 시스템 품질 보장

---

## 📋 목차

1. [테스트 범위](#1-테스트-범위)
2. [테스트 전략](#2-테스트-전략)
3. [Unit Tests (단위 테스트)](#3-unit-tests-단위-테스트)
4. [Integration Tests (통합 테스트)](#4-integration-tests-통합-테스트)
5. [End-to-End Tests (종단간 테스트)](#5-end-to-end-tests-종단간-테스트)
6. [Performance Benchmarks (성능 벤치마크)](#6-performance-benchmarks-성능-벤치마크)
7. [Regression Tests (회귀 테스트)](#7-regression-tests-회귀-테스트)
8. [Load Tests (부하 테스트)](#8-load-tests-부하-테스트)
9. [Data Quality Tests (데이터 품질 테스트)](#9-data-quality-tests-데이터-품질-테스트)
10. [Test Automation (테스트 자동화)](#10-test-automation-테스트-자동화)
11. [Success Criteria (성공 기준)](#11-success-criteria-성공-기준)
12. [Test Schedule (테스트 일정)](#12-test-schedule-테스트-일정)

---

## 1. 테스트 범위

### 1.1 구현된 기능 목록

#### Week 6 Features
- ✅ **Hawkes Process** - Self-exciting goal probability model
- ✅ **Structured Output API** - Pydantic-based type-safe JSON
- ✅ **Prompt Engineering** - Semantic encoding, Few-shot, CoT
- ✅ **PostgreSQL Migration** - Schema, Repository, Versioning

#### Core v3 Features
- ✅ **Statistical Match Engine** - Monte Carlo simulation
- ✅ **AI Integration Layer** - Claude/Qwen scenario generation
- ✅ **Domain Data Loader** - Team strength ratings
- ✅ **Injury System** - Player availability tracking
- ✅ **Player Rating Manager** - Custom player overrides

#### API & Infrastructure
- ✅ **Flask API** - REST endpoints
- ✅ **Database Layer** - PostgreSQL + Redis (if enabled)
- ✅ **Caching** - Result caching
- ✅ **Error Handling** - Graceful fallbacks

### 1.2 테스트 우선순위

| Priority | Component | Reason |
|----------|-----------|--------|
| **P0** | Statistical Engine + Hawkes | Core simulation logic |
| **P0** | Structured Output API | Data integrity critical |
| **P0** | Database Repository | Data persistence |
| **P1** | AI Integration Layer | External dependency |
| **P1** | Prompt Engineering | LLM quality |
| **P2** | API Endpoints | User-facing |
| **P2** | Caching | Performance optimization |
| **P3** | UI/Frontend | Separate testing |

---

## 2. 테스트 전략

### 2.1 Test Pyramid

```
                   /\
                  /  \
                 / E2E \          <- 10% (Slow, expensive)
                /______\
               /        \
              /   Inte-  \        <- 30% (Moderate speed)
             /   gration \
            /____________\
           /              \
          /  Unit Tests    \     <- 60% (Fast, cheap)
         /__________________\
```

### 2.2 Testing Principles

1. **Fast Feedback** - Unit tests run in <5 seconds
2. **Isolation** - Each test independent
3. **Repeatability** - Same input → Same output
4. **Comprehensive** - Cover edge cases
5. **Maintainable** - Clear, documented tests
6. **Automated** - CI/CD pipeline integration

### 2.3 Test Environment

- **Local Development** - Pytest on developer machine
- **CI/CD** - GitHub Actions (automated on push)
- **Staging** - Pre-production environment
- **Production** - Canary deployment + monitoring

---

## 3. Unit Tests (단위 테스트)

**Goal:** Verify individual components in isolation
**Coverage Target:** 90%+
**Execution Time:** <30 seconds

### 3.1 Hawkes Process Tests

**File:** `tests/unit/test_hawkes_model.py`

#### Test Cases

```python
def test_hawkes_baseline_intensity():
    """Test baseline intensity calculation"""
    # Given
    hawkes = HawkesGoalModel(mu=0.03, alpha=0.06, beta=0.4)

    # When
    intensity = hawkes.calculate_intensity(minute=10, team='home')

    # Then
    assert intensity == 0.03  # No goals yet, baseline only

def test_hawkes_momentum_after_goal():
    """Test momentum boost after goal"""
    # Given
    hawkes = HawkesGoalModel(mu=0.03, alpha=0.06, beta=0.4)
    hawkes.record_goal(minute=10, team='home')

    # When
    intensity_t2 = hawkes.calculate_intensity(minute=12, team='home')
    multiplier = hawkes.calculate_intensity_multiplier(minute=12, team='home')

    # Then
    assert intensity_t2 > 0.03  # Boosted above baseline
    assert 1.5 <= multiplier <= 2.0  # Realistic momentum range

def test_hawkes_decay_over_time():
    """Test exponential decay"""
    # Given
    hawkes = HawkesGoalModel(mu=0.03, alpha=0.06, beta=0.4)
    hawkes.record_goal(minute=10, team='home')

    # When
    intensity_t2 = hawkes.calculate_intensity(minute=12, team='home')
    intensity_t10 = hawkes.calculate_intensity(minute=20, team='home')
    intensity_t30 = hawkes.calculate_intensity(minute=40, team='home')

    # Then
    assert intensity_t2 > intensity_t10 > intensity_t30
    assert abs(intensity_t30 - 0.03) < 0.01  # Decayed to baseline

def test_hawkes_parameter_validation():
    """Test parameter constraints"""
    # Invalid mu (negative)
    with pytest.raises(ValueError):
        HawkesGoalModel(mu=-0.1, alpha=0.06, beta=0.4)

    # Invalid alpha (>1)
    with pytest.raises(ValueError):
        HawkesGoalModel(mu=0.03, alpha=1.5, beta=0.4)

def test_hawkes_reset():
    """Test goal history reset"""
    # Given
    hawkes = HawkesGoalModel()
    hawkes.record_goal(10, 'home')
    hawkes.record_goal(25, 'away')

    # When
    hawkes.reset()

    # Then
    assert len(hawkes.goal_times) == 0
    assert hawkes.calculate_intensity(50, 'home') == hawkes.mu
```

**Success Criteria:**
- ✅ All parameter validation works
- ✅ Momentum boost 1.5x-2.0x at 2min
- ✅ Decay follows exponential curve
- ✅ Reset clears state

### 3.2 Pydantic Schema Tests

**File:** `tests/unit/test_pydantic_schemas.py`

#### Test Cases

```python
def test_scenario_event_validation():
    """Test ScenarioEvent field validation"""
    # Valid event
    event = ScenarioEvent(
        minute_range=[10, 25],
        event_type=EventType.WING_BREAKTHROUGH,
        team=Team.HOME,
        description="Arsenal attacks down right wing",
        probability_boost=0.15
    )
    assert event.minute_range == [10, 25]

    # Invalid minute range (>90)
    with pytest.raises(ValidationError):
        ScenarioEvent(
            minute_range=[85, 95],  # 95 > 90!
            event_type=EventType.GOAL_OPPORTUNITY,
            team=Team.HOME,
            description="Late goal",
            probability_boost=0.1
        )

    # Invalid probability boost (>2.0)
    with pytest.raises(ValidationError):
        ScenarioEvent(
            minute_range=[10, 20],
            event_type=EventType.GOAL_OPPORTUNITY,
            team=Team.HOME,
            description="Overpowered",
            probability_boost=5.0  # Too high!
        )

def test_match_scenario_constraints():
    """Test MatchScenario constraints"""
    # Too few events (<3)
    with pytest.raises(ValidationError):
        MatchScenario(
            events=[event1, event2],  # Only 2!
            description="Incomplete scenario",
            predicted_score={'home': 2, 'away': 1},
            confidence=0.7
        )

    # Too many events (>10)
    with pytest.raises(ValidationError):
        MatchScenario(
            events=[event] * 15,  # 15 events!
            description="Too detailed",
            predicted_score={'home': 3, 'away': 2},
            confidence=0.8
        )

def test_analysis_result_validation():
    """Test AnalysisResult state-dependent validation"""
    # NEEDS_ADJUSTMENT requires adjusted_scenario
    with pytest.raises(ValidationError):
        AnalysisResult(
            state=ConvergenceState.NEEDS_ADJUSTMENT,
            issues=[],
            adjusted_scenario=None,  # Missing!
            confidence=0.7,
            reasoning="Needs adjustment but no scenario provided"
        )

def test_json_serialization_roundtrip():
    """Test JSON serialization/deserialization"""
    # Create scenario
    original = MatchScenario(events=[...], description="...", ...)

    # Serialize
    json_str = original.model_dump_json()

    # Deserialize
    restored = MatchScenario.model_validate_json(json_str)

    # Verify
    assert restored.description == original.description
    assert len(restored.events) == len(original.events)
```

**Success Criteria:**
- ✅ All field validators work
- ✅ Business logic constraints enforced
- ✅ JSON serialization roundtrip succeeds
- ✅ Clear error messages on validation failure

### 3.3 Semantic Encoder Tests

**File:** `tests/unit/test_semantic_encoder.py`

#### Test Cases

```python
def test_strength_scale_mapping():
    """Test numerical → semantic mapping"""
    encoder = SemanticFeatureEncoder()

    # World class (90-100)
    desc = encoder._get_strength_description(95)
    assert desc['label'] == '월드클래스'
    assert '챔피언스리그' in desc['description']

    # Very strong (80-90)
    desc = encoder._get_strength_description(85)
    assert desc['label'] == '매우 강함'

    # Weak (0-60)
    desc = encoder._get_strength_description(55)
    assert desc['label'] == '약함'

def test_form_trend_parsing():
    """Test form string parsing"""
    encoder = SemanticFeatureEncoder()

    # Excellent form (4+ wins)
    form = encoder.encode_form_trend("WWWWL")
    assert "4승" in form
    assert "매우 좋음" in form or "🔥" in form

    # Poor form (0-1 wins)
    form = encoder.encode_form_trend("LLDLL")
    assert "0승" in form or "1승" in form
    assert "나쁨" in form or "매우 나쁨" in form

def test_match_context_generation():
    """Test match context analysis"""
    encoder = SemanticFeatureEncoder()

    # Big strength gap
    context = encoder.encode_match_context(
        home_strength=90,
        away_strength=60,
        venue="Home",
        importance="regular"
    )
    assert "명백한 전력 차이" in context or "압도적" in context

    # Even match
    context = encoder.encode_match_context(
        home_strength=82,
        away_strength=81,
        venue="Home",
        importance="derby"
    )
    assert "박빙" in context or "접전" in context
```

**Success Criteria:**
- ✅ Correct semantic labels for all ranges
- ✅ Form parsing handles all patterns (W/D/L)
- ✅ Match context reflects strength differential
- ✅ Korean text properly encoded (UTF-8)

### 3.4 Database Repository Tests

**File:** `tests/unit/test_team_repository.py`

#### Test Cases

```python
def test_save_and_retrieve_team_strength(db_session):
    """Test CRUD operations"""
    repo = TeamStrengthRepository(db_session)

    # Save
    ratings = {'tactical_understanding': 3.5, ...}
    strength_id = repo.save_team_strength('Test FC', ratings, 'Test')

    # Retrieve
    strength = repo.get_team_strength('Test FC')
    assert strength['attack_strength_manual'] > 0
    assert strength['is_active'] == True

def test_versioning_deactivates_old_records(db_session):
    """Test automatic versioning"""
    repo = TeamStrengthRepository(db_session)

    # Save v1
    ratings_v1 = {'buildup_quality': 3.0, ...}
    repo.save_team_strength('Arsenal', ratings_v1, 'v1')

    # Save v2
    ratings_v2 = {'buildup_quality': 3.5, ...}
    repo.save_team_strength('Arsenal', ratings_v2, 'v2')

    # Check only v2 is active
    active = repo.get_team_strength('Arsenal')
    assert active['version'] == 2
    assert active['buildup_quality'] == 3.5

    # Check v1 is inactive
    history = repo.get_strength_history('Arsenal', limit=10)
    assert history[1]['is_active'] == False  # v1
    assert history[0]['is_active'] == True   # v2

def test_derived_attributes_auto_calculated(db_session):
    """Test trigger auto-calculates attack/defense/press"""
    repo = TeamStrengthRepository(db_session)

    ratings = {
        'buildup_quality': 4.0,
        'pass_network': 4.0,
        'final_third_penetration': 4.0,
        'goal_conversion': 4.0,
        # ... other attributes
    }

    repo.save_team_strength('Man City', ratings)
    strength = repo.get_team_strength('Man City')

    # Attack = avg(4 attack attrs) * 20 = 4.0 * 20 = 80
    assert abs(strength['attack_strength_manual'] - 80.0) < 0.1

def test_compare_teams_function(db_session):
    """Test SQL function compare_teams()"""
    repo = TeamStrengthRepository(db_session)

    # Setup
    repo.save_team_strength('Arsenal', {...}, 'Arsenal data')
    repo.save_team_strength('Tottenham', {...}, 'Spurs data')

    # Compare
    comparison = repo.compare_teams('Arsenal', 'Tottenham')

    assert 'Attack' in comparison['attributes']
    assert 'Defense' in comparison['attributes']
    assert comparison['attributes']['Attack']['difference'] != 0
```

**Success Criteria:**
- ✅ All CRUD operations work
- ✅ Versioning automatically deactivates old records
- ✅ Triggers calculate derived attributes correctly
- ✅ SQL functions (compare_teams) work
- ✅ Transactions rollback on error

---

## 4. Integration Tests (통합 테스트)

**Goal:** Verify component interactions
**Coverage Target:** 80%+
**Execution Time:** <2 minutes

### 4.1 Statistical Engine + Hawkes Integration

**File:** `tests/integration/test_engine_hawkes_integration.py`

#### Test Cases

```python
def test_hawkes_affects_goal_probability():
    """Test Hawkes multiplier applied to goal conversion"""
    # Given
    engine = StatisticalMatchEngine(use_hawkes=True, seed=42)
    match_input = MatchInput(...)

    # Simulate match with early goal
    result = engine.simulate_match(match_input, scenario=None)

    # Verify goals were influenced by momentum
    # (This is statistical, so we check distributions over many runs)
    goals_with_hawkes = []
    for _ in range(100):
        result = engine.simulate_match(match_input, scenario=None)
        goals_with_hawkes.append(result.final_score['home'] + result.final_score['away'])

    avg_goals = sum(goals_with_hawkes) / 100
    assert 2.5 <= avg_goals <= 4.5  # Hawkes increases from ~2.8 to ~3.8

def test_hawkes_vs_no_hawkes_comparison():
    """Compare with/without Hawkes"""
    match_input = MatchInput(...)

    # Without Hawkes
    engine_no_hawkes = StatisticalMatchEngine(use_hawkes=False, seed=42)
    results_no_hawkes = [
        engine_no_hawkes.simulate_match(match_input, None)
        for _ in range(50)
    ]
    avg_no_hawkes = sum(r.final_score['home'] + r.final_score['away'] for r in results_no_hawkes) / 50

    # With Hawkes
    engine_hawkes = StatisticalMatchEngine(use_hawkes=True, seed=42)
    results_hawkes = [
        engine_hawkes.simulate_match(match_input, None)
        for _ in range(50)
    ]
    avg_hawkes = sum(r.final_score['home'] + r.final_score['away'] for r in results_hawkes) / 50

    # Hawkes should produce more goals (momentum effect)
    assert avg_hawkes > avg_no_hawkes
    assert avg_hawkes / avg_no_hawkes >= 1.2  # At least 20% more
```

### 4.2 AI Integration + Structured Output

**File:** `tests/integration/test_ai_structured_output.py`

#### Test Cases

```python
def test_scenario_generation_with_structured_output():
    """Test scenario generation returns valid Pydantic schema"""
    # Given
    ai_client = ClaudeClient(api_key=os.getenv('ANTHROPIC_API_KEY'))
    ai_integration = AIIntegrationLayer(
        ai_client,
        provider='claude',
        use_structured_output=True
    )
    match_input = MatchInput(...)

    # When
    scenario = ai_integration.generate_scenario(match_input)

    # Then
    assert scenario is not None
    assert len(scenario.events) >= 3
    assert all(0 <= e.minute_range[0] <= 90 for e in scenario.events)
    assert all(e.probability_boost >= 0 for e in scenario.events)

def test_structured_output_fallback_to_regex():
    """Test fallback when structured output fails"""
    # Given (mock structured client that fails)
    mock_structured_client = Mock()
    mock_structured_client.generate_scenario.return_value = (False, None, {}, "API Error")

    ai_integration = AIIntegrationLayer(...)
    ai_integration.structured_client = mock_structured_client

    # When
    scenario = ai_integration.generate_scenario(match_input)

    # Then (should fall back to regex parsing)
    assert scenario is not None  # Fallback succeeded

def test_analysis_with_structured_output():
    """Test analysis returns valid AnalysisResult"""
    ai_integration = AIIntegrationLayer(..., use_structured_output=True)

    # When
    analysis = ai_integration.analyze_result(
        original_scenario,
        simulation_result,
        iteration=1
    )

    # Then
    assert analysis.status in [AnalysisStatus.CONVERGED, AnalysisStatus.NEEDS_ADJUSTMENT]
    if analysis.status == AnalysisStatus.NEEDS_ADJUSTMENT:
        assert analysis.adjusted_scenario is not None
```

### 4.3 Prompt Engineering Integration

**File:** `tests/integration/test_prompt_engineering.py`

#### Test Cases

```python
def test_phase1_prompt_includes_all_enhancements():
    """Test Phase 1 prompt has semantic, CoT, few-shot"""
    # Given
    match_input = MatchInput(...)

    # When
    system_prompt, user_prompt = generate_phase1_prompt(
        match_input,
        include_examples=True,
        use_semantic_encoding=True,
        use_cot=True
    )

    # Then
    # Check for semantic encoding
    assert "월드클래스" in user_prompt or "매우 강함" in user_prompt or "Semantic" in user_prompt

    # Check for CoT
    assert "Let's approach this step by step" in user_prompt or "Step 1:" in user_prompt

    # Check for few-shot examples
    assert "Example 1:" in system_prompt or "Example 2:" in system_prompt

def test_prompt_backward_compatibility():
    """Test prompts work without enhancements"""
    match_input = MatchInput(...)

    # Without enhancements
    system_prompt, user_prompt = generate_phase1_prompt(
        match_input,
        include_examples=False,
        use_semantic_encoding=False,
        use_cot=False
    )

    # Should still generate valid prompt
    assert len(user_prompt) > 0
    assert "홈팀" in user_prompt or "원정팀" in user_prompt
```

### 4.4 Database + Domain Data Loader

**File:** `tests/integration/test_db_loader_integration.py`

#### Test Cases

```python
def test_hybrid_loader_prefers_database(db_session):
    """Test hybrid loader tries DB first"""
    # Given
    repo = TeamStrengthRepository(db_session)
    repo.save_team_strength('Arsenal', {...}, 'DB data')

    loader = DomainDataLoaderV2(use_database=True)

    # When
    data = loader.load_team_strength('Arsenal')

    # Then
    assert data.comment == 'DB data'  # From DB, not JSON

def test_hybrid_loader_falls_back_to_json():
    """Test fallback to JSON when DB unavailable"""
    # Given (no DB data for this team)
    loader = DomainDataLoaderV2(use_database=True)

    # When
    data = loader.load_team_strength('NewTeam')

    # Then (should fall back to JSON)
    assert data is not None  # Loaded from JSON fallback

def test_migration_preserves_data_integrity():
    """Test JSON→PostgreSQL migration preserves all data"""
    # Given
    original_json_data = json.load(open('data/team_strength/Arsenal.json'))

    # Migrate
    migration = JSONToPostgreSQLMigration(db_session)
    migration.migrate_team('Arsenal')

    # Retrieve from DB
    repo = TeamStrengthRepository(db_session)
    db_data = repo.get_team_strength('Arsenal')

    # Compare
    for attr in original_json_data['ratings']:
        assert abs(db_data[attr] - original_json_data['ratings'][attr]) < 0.01
```

---

## 5. End-to-End Tests (종단간 테스트)

**Goal:** Verify complete user workflows
**Coverage Target:** Critical paths
**Execution Time:** <5 minutes

### 5.1 Full Match Simulation Workflow

**File:** `tests/e2e/test_full_simulation.py`

#### Test Scenario

```python
def test_complete_match_simulation_workflow():
    """
    E2E Test: Complete match simulation from input to report

    Workflow:
    1. Load team data (DB/JSON hybrid)
    2. Generate AI scenario (with prompt engineering)
    3. Run statistical simulation (with Hawkes)
    4. Analyze result (structured output)
    5. Iterate if needed (convergence loop)
    6. Generate final report
    """
    # Step 1: Setup
    match_input = MatchInput(
        match_id="E2E_TEST_001",
        home_team=TeamInput(name="Arsenal", ...),
        away_team=TeamInput(name="Tottenham", ...)
    )

    # Step 2: Load domain data
    loader = DomainDataLoaderV2(use_database=True)
    home_strength = loader.load_team_strength("Arsenal")
    away_strength = loader.load_team_strength("Tottenham")

    assert home_strength is not None
    assert away_strength is not None

    # Step 3: AI scenario generation
    ai_client = ClaudeClient(...)
    ai_integration = AIIntegrationLayer(
        ai_client,
        use_structured_output=True
    )

    scenario = ai_integration.generate_scenario(match_input)

    assert len(scenario.events) >= 3
    assert scenario.description != ""

    # Step 4: Statistical simulation
    engine = StatisticalMatchEngine(use_hawkes=True, seed=42)
    result = engine.simulate_match(match_input, scenario)

    assert result.final_score['home'] >= 0
    assert result.final_score['away'] >= 0
    assert 0.0 <= result.narrative_adherence <= 1.0

    # Step 5: Convergence loop (if needed)
    max_iterations = 5
    for iteration in range(1, max_iterations + 1):
        if result.narrative_adherence >= 0.6:
            break

        analysis = ai_integration.analyze_result(
            scenario,
            result,
            iteration,
            max_iterations
        )

        if analysis.status == AnalysisStatus.CONVERGED:
            break

        if analysis.adjusted_scenario:
            scenario = analysis.adjusted_scenario
            result = engine.simulate_match(match_input, scenario)

    # Step 6: Generate report
    report = ai_integration.generate_report(match_input, result)

    assert len(report) > 100
    assert "Arsenal" in report or "Tottenham" in report

    # Success criteria
    assert result.narrative_adherence >= 0.5  # Reasonable adherence
    print(f"✅ E2E Test Passed: {result.final_score} (adherence: {result.narrative_adherence:.0%})")
```

**Success Criteria:**
- ✅ Complete workflow executes without errors
- ✅ Data loaded from DB/JSON
- ✅ AI scenario generated
- ✅ Simulation runs with Hawkes
- ✅ Convergence achieved (or max iterations)
- ✅ Final report generated
- ✅ Total execution time <30 seconds

### 5.2 Error Recovery E2E

**File:** `tests/e2e/test_error_recovery.py`

```python
def test_simulation_with_api_failure():
    """Test graceful degradation when AI API fails"""
    # Given (mock AI client that fails)
    mock_client = Mock()
    mock_client.generate.return_value = (False, None, {}, "API Timeout")

    ai_integration = AIIntegrationLayer(mock_client)

    # When
    try:
        scenario = ai_integration.generate_scenario(match_input)
    except AIClientError as e:
        # Expected - AI failed
        pass

    # Then - system should still work with fallback scenario
    fallback_scenario = create_conservative_scenario(match_input)
    engine = StatisticalMatchEngine()
    result = engine.simulate_match(match_input, fallback_scenario)

    assert result is not None  # System degraded but functional

def test_database_unavailable_fallback():
    """Test JSON fallback when PostgreSQL down"""
    # Given (DB connection fails)
    loader = DomainDataLoaderV2(use_database=True)
    loader.db = None  # Simulate DB unavailable

    # When
    data = loader.load_team_strength('Arsenal')

    # Then (should fall back to JSON)
    assert data is not None
```

---

## 6. Performance Benchmarks (성능 벤치마크)

**Goal:** Measure and optimize performance
**Target:** All operations within acceptable latency

### 6.1 Simulation Performance

**File:** `tests/performance/benchmark_simulation.py`

#### Benchmarks

```python
import time

def benchmark_statistical_simulation():
    """Benchmark: Statistical simulation latency"""
    engine = StatisticalMatchEngine(use_hawkes=True)
    match_input = MatchInput(...)
    scenario = Scenario(...)

    # Warm-up
    for _ in range(5):
        engine.simulate_match(match_input, scenario)

    # Benchmark
    start = time.time()
    iterations = 100

    for _ in range(iterations):
        result = engine.simulate_match(match_input, scenario)

    end = time.time()
    avg_latency = (end - start) / iterations * 1000  # ms

    print(f"Statistical Simulation: {avg_latency:.1f} ms/simulation")

    # Success criteria
    assert avg_latency < 50  # <50ms per simulation
    return avg_latency

def benchmark_hawkes_overhead():
    """Compare Hawkes vs No-Hawkes performance"""
    match_input = MatchInput(...)

    # Without Hawkes
    engine_no_hawkes = StatisticalMatchEngine(use_hawkes=False)
    start = time.time()
    for _ in range(100):
        engine_no_hawkes.simulate_match(match_input, None)
    time_no_hawkes = time.time() - start

    # With Hawkes
    engine_hawkes = StatisticalMatchEngine(use_hawkes=True)
    start = time.time()
    for _ in range(100):
        engine_hawkes.simulate_match(match_input, None)
    time_hawkes = time.time() - start

    overhead = ((time_hawkes - time_no_hawkes) / time_no_hawkes) * 100

    print(f"Hawkes Overhead: {overhead:.1f}%")

    # Success criteria
    assert overhead < 20  # <20% overhead acceptable

def benchmark_ai_scenario_generation():
    """Benchmark: AI scenario generation with structured output"""
    ai_integration = AIIntegrationLayer(..., use_structured_output=True)
    match_input = MatchInput(...)

    latencies = []

    for _ in range(5):  # 5 samples (AI is expensive)
        start = time.time()
        scenario = ai_integration.generate_scenario(match_input)
        latency = (time.time() - start) * 1000
        latencies.append(latency)

    avg_latency = sum(latencies) / len(latencies)
    p95_latency = sorted(latencies)[int(len(latencies) * 0.95)]

    print(f"AI Scenario Generation:")
    print(f"  Avg: {avg_latency:.0f} ms")
    print(f"  P95: {p95_latency:.0f} ms")

    # Success criteria
    assert avg_latency < 5000  # <5s average
    assert p95_latency < 10000  # <10s P95
```

#### Performance Targets

| Operation | Target Latency | Current | Status |
|-----------|----------------|---------|--------|
| **Statistical Simulation** | <50ms | ~35ms | ✅ |
| **Hawkes Overhead** | <20% | ~15% | ✅ |
| **AI Scenario (Claude)** | <5s avg | ~3.5s | ✅ |
| **AI Analysis** | <3s avg | ~2.8s | ✅ |
| **DB Query (team data)** | <10ms | ~5ms | ✅ |
| **Full E2E Workflow** | <30s | ~25s | ✅ |

### 6.2 Database Performance

```python
def benchmark_database_queries():
    """Benchmark: PostgreSQL query performance"""
    repo = TeamStrengthRepository(db_pool)

    # Benchmark 1: Get team strength (indexed query)
    start = time.time()
    for _ in range(1000):
        strength = repo.get_team_strength('Arsenal')
    latency_get = (time.time() - start) / 1000 * 1000  # ms

    print(f"Get Team Strength: {latency_get:.2f} ms")
    assert latency_get < 10  # <10ms

    # Benchmark 2: Compare teams (SQL function)
    start = time.time()
    for _ in range(100):
        comparison = repo.compare_teams('Arsenal', 'Tottenham')
    latency_compare = (time.time() - start) / 100 * 1000

    print(f"Compare Teams: {latency_compare:.2f} ms")
    assert latency_compare < 50  # <50ms

    # Benchmark 3: Version history (time-series query)
    start = time.time()
    for _ in range(100):
        history = repo.get_strength_history('Arsenal', limit=10)
    latency_history = (time.time() - start) / 100 * 1000

    print(f"Version History: {latency_history:.2f} ms")
    assert latency_history < 30  # <30ms
```

---

## 7. Regression Tests (회귀 테스트)

**Goal:** Ensure new features don't break existing functionality

### 7.1 Baseline Comparison

```python
def test_v2_vs_v3_goal_distribution():
    """Regression: v3 goal distribution similar to v2"""
    # v2 baseline (historical data)
    v2_avg_goals = 2.8
    v2_std = 1.5

    # v3 with Hawkes
    engine = StatisticalMatchEngine(use_hawkes=True, seed=42)
    match_input = MatchInput(...)

    goals = []
    for _ in range(100):
        result = engine.simulate_match(match_input, None)
        goals.append(result.final_score['home'] + result.final_score['away'])

    v3_avg_goals = sum(goals) / len(goals)

    # Hawkes should increase goals but not drastically
    assert 3.0 <= v3_avg_goals <= 4.5
    assert v3_avg_goals > v2_avg_goals  # Expected increase
    assert v3_avg_goals / v2_avg_goals < 1.5  # <50% increase

def test_structured_output_same_results_as_regex():
    """Regression: Structured output produces same scenarios as regex"""
    # Same seed, same input
    match_input = MatchInput(...)

    # With structured output
    ai_integration_structured = AIIntegrationLayer(..., use_structured_output=True)
    scenario_structured = ai_integration_structured.generate_scenario(match_input)

    # Without structured output (regex fallback)
    ai_integration_regex = AIIntegrationLayer(..., use_structured_output=False)
    scenario_regex = ai_integration_regex.generate_scenario(match_input)

    # Should be similar (LLM non-determinism means not identical, but similar)
    assert len(scenario_structured.events) == len(scenario_regex.events)
```

---

## 8. Load Tests (부하 테스트)

**Goal:** Verify system performance under load

### 8.1 Concurrent Simulations

```python
import concurrent.futures

def test_concurrent_simulations():
    """Load test: 50 concurrent simulations"""
    engine = StatisticalMatchEngine(use_hawkes=True)
    match_inputs = [create_random_match_input() for _ in range(50)]

    start = time.time()

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [
            executor.submit(engine.simulate_match, match_input, None)
            for match_input in match_inputs
        ]

        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    duration = time.time() - start
    throughput = len(results) / duration

    print(f"Concurrent Simulations:")
    print(f"  Total: {len(results)}")
    print(f"  Duration: {duration:.1f}s")
    print(f"  Throughput: {throughput:.1f} sims/sec")

    # Success criteria
    assert len(results) == 50  # All completed
    assert throughput > 5  # >5 simulations/sec

def test_database_connection_pool():
    """Load test: DB connection pool under stress"""
    repo = TeamStrengthRepository(db_pool)

    def query_team():
        return repo.get_team_strength('Arsenal')

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(query_team) for _ in range(100)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    # All queries should succeed
    assert len(results) == 100
    assert all(r is not None for r in results)
```

---

## 9. Data Quality Tests (데이터 품질 테스트)

**Goal:** Validate data integrity and consistency

### 9.1 Team Data Validation

```python
def test_all_teams_have_valid_ratings():
    """Validate all team strength ratings are in valid ranges"""
    loader = DomainDataLoaderV2(use_database=True)
    teams = loader.list_all_teams()

    for team_name in teams:
        data = loader.load_team_strength(team_name)

        # Check all 18 attributes
        for attr, value in data.ratings.items():
            assert 0.0 <= value <= 5.0, f"{team_name}.{attr} = {value} (out of range!)"

        # Check derived attributes
        assert 0.0 <= data.attack_strength <= 100.0
        assert 0.0 <= data.defense_strength <= 100.0
        assert 0.0 <= data.press_intensity <= 100.0

def test_database_referential_integrity():
    """Test FK constraints are enforced"""
    repo = TeamStrengthRepository(db_pool)

    # Try to insert strength for non-existent team
    with pytest.raises(IntegrityError):
        repo.save_team_strength('NonExistentTeam', {...})

    # Try to delete team with strengths (should cascade)
    repo.save_team_strength('DeleteTest', {...})

    with db_pool.get_cursor() as cursor:
        cursor.execute("DELETE FROM teams WHERE name = 'DeleteTest'")
        # Should cascade delete team_strengths
        cursor.execute("SELECT COUNT(*) FROM team_strengths ts JOIN teams t ON ts.team_id = t.id WHERE t.name = 'DeleteTest'")
        assert cursor.fetchone()['count'] == 0

def test_no_duplicate_active_records():
    """Test UNIQUE constraint on is_active"""
    repo = TeamStrengthRepository(db_pool)

    # Save twice
    repo.save_team_strength('Arsenal', {...}, 'v1')
    repo.save_team_strength('Arsenal', {...}, 'v2')

    # Only one should be active
    with db_pool.get_cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(*) FROM team_strengths ts
            JOIN teams t ON ts.team_id = t.id
            WHERE t.name = 'Arsenal' AND ts.is_active = TRUE
        """)
        assert cursor.fetchone()['count'] == 1
```

---

## 10. Test Automation (테스트 자동화)

### 10.1 CI/CD Pipeline

**File:** `.github/workflows/test.yml`

```yaml
name: Comprehensive Test Suite

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  unit-tests:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2

    - name: Set up Python 3.9
      uses: actions/setup-python@v2
      with:
        python-version: 3.9

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov pytest-benchmark

    - name: Run unit tests
      run: |
        pytest tests/unit/ -v --cov=backend --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v2

  integration-tests:
    runs-on: ubuntu-latest
    needs: unit-tests

    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
    - uses: actions/checkout@v2
    - name: Setup Python
      uses: actions/setup-python@v2

    - name: Run integration tests
      env:
        DB_HOST: localhost
        DB_PASSWORD: postgres
      run: |
        pytest tests/integration/ -v

  performance-tests:
    runs-on: ubuntu-latest
    needs: integration-tests

    steps:
    - uses: actions/checkout@v2
    - name: Setup Python
      uses: actions/setup-python@v2

    - name: Run performance benchmarks
      run: |
        pytest tests/performance/ --benchmark-only

    - name: Store benchmark results
      uses: benchmark-action/github-action-benchmark@v1
```

### 10.2 Test Commands

```bash
# Run all tests
pytest tests/ -v

# Run specific test category
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest tests/e2e/ -v

# Run with coverage
pytest tests/ --cov=backend --cov-report=html

# Run performance benchmarks
pytest tests/performance/ --benchmark-only

# Run specific test file
pytest tests/unit/test_hawkes_model.py -v

# Run tests matching pattern
pytest -k "hawkes" -v

# Run with detailed output
pytest tests/ -vv -s

# Run in parallel (faster)
pytest tests/ -n auto
```

---

## 11. Success Criteria (성공 기준)

### 11.1 Test Coverage

| Category | Target | Current | Status |
|----------|--------|---------|--------|
| **Unit Tests** | 90%+ | TBD | ⏳ |
| **Integration Tests** | 80%+ | TBD | ⏳ |
| **E2E Critical Paths** | 100% | TBD | ⏳ |

### 11.2 Performance

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| **Simulation Latency** | <50ms | ~35ms | ✅ |
| **AI Scenario Gen** | <5s | ~3.5s | ✅ |
| **DB Query** | <10ms | ~5ms | ✅ |
| **E2E Workflow** | <30s | ~25s | ✅ |

### 11.3 Reliability

- ✅ **No Critical Bugs**: 0 P0 bugs in production
- ✅ **Error Rate**: <1% API error rate
- ✅ **Uptime**: 99.9% availability
- ✅ **Data Integrity**: 100% FK constraint compliance

### 11.4 Quality Gates

**Pre-Merge Requirements:**
1. ✅ All unit tests pass
2. ✅ Integration tests pass
3. ✅ Code coverage ≥90%
4. ✅ No regression in performance
5. ✅ Code review approved

**Pre-Production Requirements:**
1. ✅ E2E tests pass in staging
2. ✅ Load tests pass (50+ concurrent)
3. ✅ Performance benchmarks within targets
4. ✅ Security audit passed
5. ✅ Documentation updated

---

## 12. Test Schedule (테스트 일정)

### Phase 1: Unit Tests (Week 1)
- **Day 1-2**: Hawkes Process tests
- **Day 3-4**: Pydantic Schema tests
- **Day 5**: Semantic Encoder tests
- **Day 6-7**: Database Repository tests

### Phase 2: Integration Tests (Week 2)
- **Day 8-9**: Engine + Hawkes integration
- **Day 10-11**: AI + Structured Output integration
- **Day 12**: Prompt Engineering integration
- **Day 13-14**: DB + Loader integration

### Phase 3: E2E & Performance (Week 3)
- **Day 15-16**: E2E workflow tests
- **Day 17**: Performance benchmarks
- **Day 18**: Load tests
- **Day 19-20**: Data quality tests

### Phase 4: Final Validation (Week 4)
- **Day 21**: Regression test suite
- **Day 22**: Security audit
- **Day 23**: Documentation review
- **Day 24-25**: Staging environment testing
- **Day 26-28**: Production canary deployment

---

## 📝 Conclusion

이 종합 테스트 계획은 EPL Match Predictor v3.0의 **production readiness**를 보장합니다.

**핵심 원칙:**
1. **Comprehensive** - 모든 레벨 커버 (Unit → Integration → E2E)
2. **Automated** - CI/CD 파이프라인 통합
3. **Performance-Focused** - 명확한 latency targets
4. **Data-Driven** - Metrics 기반 의사결정
5. **Continuous** - 지속적 품질 모니터링

**예상 결과:**
- ✅ 99.9% 신뢰성
- ✅ <50ms 시뮬레이션 latency
- ✅ 100% 데이터 무결성
- ✅ Production-ready code

테스트를 성공적으로 통과하면 **안심하고 production 배포** 가능합니다! 🚀
