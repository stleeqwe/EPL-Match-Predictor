# Week 6 상세 실행 계획: Iterative Loop Orchestrator

**기간**: Day 25-28 (4일)
**목표**: Phase 1-7 반복 루프 통합 및 수렴 로직 구현
**상태**: 🚀 시작

---

## 📋 목표 및 범위

### 핵심 목표
1. **Convergence Judge**: 5가지 기준으로 시뮬레이션 수렴 판단
2. **AI Integration Layer**: Prompt를 실제 AI Client와 연결
3. **Match Simulator V3**: 전체 Phase 1-7 통합 오케스트레이터
4. **통합 테스트**: Mock AI 응답으로 전체 플로우 검증

### 산출물
- `simulation/v3/convergence_judge.py` (~200줄)
- `simulation/v3/ai_integration.py` (~300줄)
- `simulation/v3/match_simulator_v3.py` (~400줄)
- `simulation/v3/test_integration.py` (~300줄)

**총 예상**: ~1,200줄

---

## 🏗️ 아키텍처 설계

### 전체 플로우
```
┌─────────────────────────────────────────────────────┐
│            Match Simulator V3                       │
│         (Orchestrator - 전체 플로우 관리)            │
└──────────────────┬──────────────────────────────────┘
                   │
                   ↓
        ┌──────────────────────┐
        │   Phase 1: AI 시나리오 생성   │
        │   (AI Integration Layer)     │
        └──────────┬───────────────────┘
                   ↓
        ┌──────────────────────┐
        │   Phase 2: Statistical    │
        │   Engine 시뮬레이션        │
        └──────────┬───────────┘
                   ↓
        ┌──────────────────────┐
        │   Phase 3: AI 분석/조정    │
        │   (AI Integration Layer)  │
        └──────────┬───────────┘
                   ↓
        ┌──────────────────────┐
        │   Phase 4: 수렴 판단       │
        │   (Convergence Judge)     │
        └──────────┬───────────┘
                   │
         수렴? ────┤
                   │ No (조정 필요)
                   ↓
        ┌──────────────────────┐
        │   Phase 5: 시나리오 조정   │
        │   (AI adjusted_scenario)  │
        └──────────┬───────────┘
                   │
                   ↓ (반복)
            Phase 2로 돌아가기
                   │
         Yes (수렴 완료)
                   ↓
        ┌──────────────────────┐
        │   Phase 7: 최종 리포트    │
        │   (AI Integration Layer)  │
        └──────────┬───────────┘
                   ↓
            MatchResult 반환
```

---

## 📅 일정 및 작업 분해

### Day 25: Convergence Judge 구현

**목표**: 시뮬레이션 수렴 여부를 5가지 기준으로 판단

**작업 항목**:

1. **convergence_judge.py 구현**
   ```python
   class ConvergenceJudge:
       """
       수렴 판단기

       5가지 기준:
       1. 서사 일치율 (narrative_adherence >= 0.6) - 가중치 40%
       2. AI 수렴 신호 (status == CONVERGED) - 가중치 30%
       3. 반복 횟수 (>= max_iterations) - 가중치 15%
       4. 득점 차이 안정 (이전 vs 현재) - 가중치 10%
       5. 슛 차이 안정 (이전 vs 현재) - 가중치 5%
       """

       def __init__(self,
                    adherence_threshold: float = 0.6,
                    max_iterations: int = 5,
                    score_stability_threshold: int = 1,
                    shot_stability_threshold: int = 3):
           ...

       def is_converged(self,
                       analysis: AnalysisResult,
                       current_result: SimulationResult,
                       previous_result: Optional[SimulationResult],
                       iteration: int) -> Tuple[bool, Dict[str, Any]]:
           """
           수렴 판단

           Returns:
               (is_converged, convergence_info)
           """
           scores = {
               'adherence': self._score_adherence(current_result),
               'ai_signal': self._score_ai_signal(analysis),
               'iterations': self._score_iterations(iteration),
               'score_stability': self._score_stability(
                   current_result, previous_result, 'score'
               ),
               'shot_stability': self._score_stability(
                   current_result, previous_result, 'shots'
               ),
           }

           weighted_score = (
               scores['adherence'] * 0.40 +
               scores['ai_signal'] * 0.30 +
               scores['iterations'] * 0.15 +
               scores['score_stability'] * 0.10 +
               scores['shot_stability'] * 0.05
           )

           is_converged = weighted_score >= 0.7  # 70% 이상

           return is_converged, {
               'weighted_score': weighted_score,
               'scores': scores,
               'reason': self._get_convergence_reason(scores)
           }
   ```

2. **단위 테스트**
   - 각 기준별 점수 계산 테스트
   - 가중 평균 계산 테스트
   - 경계값 테스트

**검증 기준**:
- [ ] 5개 기준 모두 구현
- [ ] 가중 평균 70% 이상 시 수렴
- [ ] 단위 테스트 통과

---

### Day 26: AI Integration Layer 구현

**목표**: Prompt를 실제 AI Client와 연결

**작업 항목**:

1. **ai_integration.py 구현**
   ```python
   class AIIntegrationLayer:
       """
       AI Integration Layer

       Prompt → AI Client → 파싱 → 데이터 모델 변환
       """

       def __init__(self, ai_client, provider: str = 'claude'):
           self.ai_client = ai_client  # ClaudeClient or QwenClient
           self.provider = provider

       def generate_scenario(self, match_input: MatchInput) -> Scenario:
           """
           Phase 1: 시나리오 생성
           """
           # 1. Prompt 생성
           from ai.prompts.phase1_scenario import generate_phase1_prompt
           system_prompt, user_prompt = generate_phase1_prompt(match_input)

           # 2. AI 호출
           success, response, usage, error = self.ai_client.generate(
               prompt=user_prompt,
               system_prompt=system_prompt,
               tier='BASIC'
           )

           if not success:
               raise AIClientError(f"Phase 1 실패: {error}")

           # 3. JSON 파싱
           scenario_dict = self._parse_json(response)

           # 4. Scenario 객체 생성
           scenario = self._dict_to_scenario(scenario_dict)

           return scenario

       def analyze_result(self,
                         original_scenario: Scenario,
                         simulation_result: SimulationResult,
                         iteration: int) -> AnalysisResult:
           """
           Phase 3: 결과 분석
           """
           # 1. Prompt 생성
           from ai.prompts.phase3_analysis import generate_phase3_prompt
           system_prompt, user_prompt = generate_phase3_prompt(
               original_scenario,
               simulation_result,
               iteration
           )

           # 2. AI 호출
           success, response, usage, error = self.ai_client.generate(
               prompt=user_prompt,
               system_prompt=system_prompt,
               tier='BASIC'
           )

           if not success:
               raise AIClientError(f"Phase 3 실패: {error}")

           # 3. JSON 파싱
           analysis_dict = self._parse_json(response)

           # 4. AnalysisResult 객체 생성
           result = self._dict_to_analysis_result(analysis_dict)

           return result

       def generate_report(self,
                          match_input: MatchInput,
                          final_result: SimulationResult) -> str:
           """
           Phase 7: 최종 리포트
           """
           # 1. Prompt 생성
           from ai.prompts.phase7_report import generate_phase7_prompt
           system_prompt, user_prompt = generate_phase7_prompt(
               match_input,
               final_result
           )

           # 2. AI 호출
           success, response, usage, error = self.ai_client.generate(
               prompt=user_prompt,
               system_prompt=system_prompt,
               tier='BASIC'
           )

           if not success:
               raise AIClientError(f"Phase 7 실패: {error}")

           # 3. 마크다운 반환 (파싱 불필요)
           return response
   ```

2. **Mock AI Client 구현** (테스트용)
   ```python
   class MockAIClient:
       """테스트용 Mock AI Client"""

       def generate(self, prompt, system_prompt=None, tier='BASIC'):
           # Phase 1 응답 Mock
           if 'scenario' in prompt.lower():
               return True, MOCK_SCENARIO_JSON, {}, None

           # Phase 3 응답 Mock
           elif 'analysis' in prompt.lower():
               return True, MOCK_ANALYSIS_JSON, {}, None

           # Phase 7 응답 Mock
           elif 'report' in prompt.lower():
               return True, MOCK_REPORT_MARKDOWN, {}, None
   ```

**검증 기준**:
- [ ] 3개 Phase 모두 구현
- [ ] Mock AI로 테스트 통과
- [ ] 에러 핸들링 완료

---

### Day 27: Match Simulator V3 Orchestrator 구현

**목표**: 전체 Phase 1-7 통합

**작업 항목**:

1. **match_simulator_v3.py 구현**
   ```python
   class MatchSimulatorV3:
       """
       Match Simulator V3

       Phase 1-7 통합 오케스트레이터
       """

       def __init__(self,
                   statistical_engine: StatisticalMatchEngine,
                   ai_integration: AIIntegrationLayer,
                   convergence_judge: ConvergenceJudge,
                   max_iterations: int = 5):
           self.engine = statistical_engine
           self.ai = ai_integration
           self.judge = convergence_judge
           self.max_iterations = max_iterations

       def simulate_match(self, match_input: MatchInput) -> Dict[str, Any]:
           """
           전체 시뮬레이션 실행

           Returns:
               {
                   'final_result': SimulationResult,
                   'final_report': str (markdown),
                   'convergence_info': Dict,
                   'iterations': int,
                   'scenario_history': List[Scenario]
               }
           """
           print(f"\n{'='*60}")
           print(f"Match Simulator V3: {match_input.home_team.name} vs {match_input.away_team.name}")
           print(f"{'='*60}\n")

           # Phase 1: AI 시나리오 생성
           print("Phase 1: AI 시나리오 생성...")
           scenario = self.ai.generate_scenario(match_input)
           print(f"  ✅ 시나리오 생성 완료: {len(scenario.events)}개 이벤트")

           scenario_history = [scenario]
           previous_result = None

           # Phase 2-6: 반복 루프
           for iteration in range(1, self.max_iterations + 1):
               print(f"\n--- Iteration {iteration}/{self.max_iterations} ---")

               # Phase 2: Statistical Engine 시뮬레이션
               print("Phase 2: Statistical Engine 시뮬레이션...")
               guide = ScenarioGuide(scenario.to_dict())
               result = self.engine.simulate_match(
                   self._to_team_info(match_input.home_team),
                   self._to_team_info(match_input.away_team),
                   guide
               )
               print(f"  최종 스코어: {result.final_score['home']}-{result.final_score['away']}")
               print(f"  서사 일치율: {result.narrative_adherence:.0%}")

               # Phase 3: AI 분석
               print("Phase 3: AI 분석/조정...")
               analysis = self.ai.analyze_result(scenario, result, iteration)
               print(f"  AI 상태: {analysis.status.value}")

               # Phase 4: 수렴 판단
               print("Phase 4: 수렴 판단...")
               is_converged, conv_info = self.judge.is_converged(
                   analysis, result, previous_result, iteration
               )
               print(f"  수렴 점수: {conv_info['weighted_score']:.2f}")
               print(f"  수렴 여부: {'✅ Yes' if is_converged else '❌ No'}")

               if is_converged:
                   # 수렴 완료 → Phase 7로
                   print(f"\n수렴 완료! (Iteration {iteration})")
                   final_result = result
                   break

               # Phase 5: 시나리오 조정
               if analysis.adjusted_scenario:
                   print("Phase 5: 시나리오 조정...")
                   scenario = analysis.adjusted_scenario
                   scenario_history.append(scenario)
                   print(f"  시나리오 조정 완료")
               else:
                   print("  조정된 시나리오 없음, 현재 시나리오 유지")

               previous_result = result

               # Phase 6: 다음 반복으로
               if iteration == self.max_iterations:
                   print(f"\n최대 반복 {self.max_iterations}회 도달")
                   final_result = result

           # Phase 7: 최종 리포트
           print("\nPhase 7: 최종 리포트 생성...")
           final_report = self.ai.generate_report(match_input, final_result)
           print(f"  ✅ 리포트 생성 완료 ({len(final_report)} 문자)")

           print(f"\n{'='*60}")
           print(f"시뮬레이션 완료!")
           print(f"{'='*60}\n")

           return {
               'final_result': final_result,
               'final_report': final_report,
               'convergence_info': conv_info,
               'iterations': iteration,
               'scenario_history': scenario_history,
           }
   ```

2. **헬퍼 메서드**
   - `_to_team_info()`: MatchInput → TeamInfo 변환
   - 로깅 및 진행 상황 표시

**검증 기준**:
- [ ] 전체 플로우 실행 가능
- [ ] 반복 루프 작동
- [ ] 수렴 시 조기 종료

---

### Day 28: 통합 테스트

**목표**: Mock AI로 전체 플로우 검증

**작업 항목**:

1. **test_integration.py 구현**
   ```python
   def test_full_flow_mock():
       """전체 플로우 통합 테스트 (Mock AI)"""
       print("=== Match Simulator V3 통합 테스트 ===\n")

       # 1. 컴포넌트 생성
       engine = StatisticalMatchEngine(seed=42)
       mock_ai = MockAIClient()
       ai_integration = AIIntegrationLayer(mock_ai)
       judge = ConvergenceJudge()

       simulator = MatchSimulatorV3(
           statistical_engine=engine,
           ai_integration=ai_integration,
           convergence_judge=judge,
           max_iterations=3
       )

       # 2. 테스트 경기 입력
       match_input = create_test_match_input()

       # 3. 시뮬레이션 실행
       result = simulator.simulate_match(match_input)

       # 4. 검증
       assert result['final_result'] is not None
       assert result['final_report'] is not None
       assert result['iterations'] >= 1
       assert len(result['scenario_history']) >= 1

       print("✅ 전체 플로우 통합 테스트 통과!")
   ```

2. **엣지 케이스 테스트**
   - 1회 반복으로 수렴
   - 최대 반복 도달
   - AI 에러 핸들링

**검증 기준**:
- [ ] Mock AI로 전체 플로우 실행
- [ ] 모든 Phase 순차 실행
- [ ] 엣지 케이스 테스트 통과

---

## ✅ Week 6 검증 기준

### 기능 검증
- [ ] Convergence Judge 5개 기준 작동
- [ ] AI Integration Layer 3개 Phase 연결
- [ ] Match Simulator V3 전체 플로우 실행
- [ ] Mock AI로 통합 테스트 통과
- [ ] 수렴 시 조기 종료 확인
- [ ] 최대 반복 시 강제 종료 확인

### 코드 품질
- [ ] 모든 클래스에 docstring
- [ ] Type hints 100%
- [ ] 에러 핸들링 완료
- [ ] 로깅 및 진행 상황 표시

---

## 🎯 성공 지표

### 정량 지표
- 코드 라인: ~1,200줄
- 통합 테스트: > 5개
- 테스트 통과율: 100%
- Mock AI 시뮬레이션 < 5초

### 정성 지표
- 전체 플로우가 명확하게 작동
- 로그가 각 Phase 진행 상황을 명확히 표시
- 에러 발생 시 의미 있는 메시지
- 코드가 확장 가능 (다른 AI Provider 추가 용이)

---

## 🚧 리스크 및 완화 전략

### 리스크 1: AI API 키 필요
**문제**: 실제 테스트는 API 키 필요
**완화**: Mock AI Client로 개발 및 테스트, 실제 API는 선택사항

### 리스크 2: 수렴 기준 튜닝
**문제**: 가중치(40%, 30%, ...)가 최적이 아닐 수 있음
**완화**: 설정 가능한 파라미터로 구현, 추후 실험으로 조정

### 리스크 3: 반복 시간
**문제**: 5회 반복 시 시간 오래 걸릴 수 있음
**완화**: 조기 수렴 로직으로 평균 2-3회 반복, 병렬화 고려

---

**계획 수립 완료 - Day 25 구현 시작** 🚀
