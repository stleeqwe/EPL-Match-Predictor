# 가상 시뮬레이션 아키텍처 분석

**분석 일시**: 2025-10-12
**대상**: EPL Match Predictor 물리 기반 경기 시뮬레이터

---

## 📐 현재 아키텍처 개요

### 전체 구조

```
┌─────────────────────────────────────────────────────────────┐
│                     Simulation Layer                         │
│  (GameSimulator - 메인 시뮬레이션 루프)                      │
└────────┬──────────────────────────────────────┬─────────────┘
         │                                       │
         ▼                                       ▼
┌────────────────────────┐           ┌────────────────────────┐
│   Physics Layer        │           │   Agents Layer         │
│  - player_physics      │           │  - simple_agent        │
│  - ball_physics        │           │  - position_behaviors  │
│  - constants           │           │  - tactical_ai         │
└────────────────────────┘           │  - actions             │
                                     └────────────────────────┘
         │                                       │
         ▼                                       ▼
┌─────────────────────────────────────────────────────────────┐
│                  Support Systems                             │
│  - FieldState (96-zone grid)                                │
│  - ActionExecutor (action → physics)                        │
│  - EventDetector (goals, fouls, etc.)                       │
│  - MatchStatistics                                          │
│  - GlobalContext                                            │
│  - DynamicBalancer                                          │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔍 레이어별 상세 분석

### 1. Physics Layer (물리 엔진)

**위치**: `backend/physics/`

#### 구성 요소

**1.1 player_physics.py**
```python
class PlayerPhysicsEngine:
    """
    선수 물리 시뮬레이션

    - 위치, 속도, 가속도 업데이트
    - 스태미나 소모 계산
    - 충돌 감지
    - 물리 법칙 적용 (뉴턴 역학)
    """
```

**1.2 ball_physics.py**
```python
class BallPhysicsEngine:
    """
    공 물리 시뮬레이션

    - 3D 위치 추적
    - 중력, 마찰, 공기 저항
    - 바운스 시뮬레이션
    - 스핀 효과
    """
```

**1.3 constants.py**
```python
# 물리 상수
DT = 0.1  # 시뮬레이션 타임스텝 (0.1초)
TICKS_PER_SECOND = 10
MATCH_DURATION_SECONDS = 5400  # 90분

# 필드 크기
FIELD_LENGTH = 105.0  # 미터
FIELD_WIDTH = 68.0

# 플레이어 상수
PLAYER_CONTROL_RADIUS = 2.0
SHOT_POWER_BASE = 25.0
PASS_POWER_SHORT = 8.0
```

#### 특징
- ✅ **실시간 물리 시뮬레이션**: 0.1초 단위로 정밀 계산
- ✅ **현실적인 물리 법칙**: 중력, 마찰, 공기 저항 모델링
- ✅ **선수 능력치 반영**: pace, shooting, stamina 등

---

### 2. Agents Layer (AI 에이전트)

**위치**: `backend/agents/`

#### 구성 요소

**2.1 simple_agent.py**
```python
class SimpleAgent:
    """
    선수 의사결정 AI

    입력:
    - PlayerGameState (본인 상태)
    - GameContext (팀원, 상대, 공 위치)

    출력:
    - Action (SHOOT, PASS, DRIBBLE, etc.)

    로직:
    - 공 소유 시: 슛/패스/드리블 판단
    - 공 미소유 시: 포지션 복귀/마킹/볼 체이싱
    """
```

**2.2 position_behaviors.py**
```python
def get_position_action(player: PlayerGameState, context: GameContext):
    """
    포지션별 특화 행동

    GK: 골 방어, 슈팅 막기
    CB: 수비 라인 유지, 마킹
    CM: 패스 연결, 지원
    ST: 득점 기회 찾기, 슈팅
    """
```

**2.3 actions.py**
```python
class ActionType(Enum):
    SHOOT = "shoot"
    PASS = "pass"
    DRIBBLE = "dribble"
    TACKLE = "tackle"
    CHASE_BALL = "chase_ball"
    MOVE_TO_POSITION = "move_to_position"
    MARK_OPPONENT = "mark_opponent"
    CLEAR_BALL = "clear_ball"
    SAVE_SHOT = "save_shot"
    IDLE = "idle"
```

#### 특징
- ✅ **포지션 기반 AI**: 각 포지션별 고유한 행동 패턴
- ✅ **컨텍스트 인지**: 팀원, 상대, 공 위치를 고려한 의사결정
- ✅ **동적 밸런싱**: 팀 우위에 따라 능력치 조정

---

### 3. Simulation Layer (시뮬레이션 엔진)

**위치**: `backend/simulation/`

#### 메인 시뮬레이터

**game_simulator.py**
```python
class GameSimulator:
    """
    경기 전체 시뮬레이션 조율

    메인 루프:
    1. 에이전트 의사결정 (모든 선수)
    2. 액션 실행 → 물리 파라미터 변환
    3. 물리 업데이트 (선수 + 공)
    4. 이벤트 감지 (골, 아웃, 파울)
    5. 통계 수집

    90분 = 54,000 ticks (0.1초 간격)
    """
```

**시뮬레이션 플로우**:
```
for each tick (0.1초):
    1. Global Context 업데이트
       ├─ 점유율 계산
       ├─ 경기 단계 (전반/후반)
       └─ Dynamic Balance 계산

    2. 각 선수별:
       ├─ Agent 의사결정
       ├─ Action 실행
       ├─ Physics 업데이트
       └─ Ball interaction

    3. Ball Physics 업데이트

    4. Event Detection
       ├─ Goal
       ├─ Out of bounds
       └─ Fouls (미구현)

    5. Statistics 수집
```

#### 지원 시스템

**3.1 field_state.py - 공간 인식**
```python
class FieldState:
    """
    필드를 96개 존으로 분할 (8×12 그리드)

    기능:
    - 존별 지배율 추적 (home/away/contested)
    - 압박 맵 (pressure map)
    - 패싱 레인 분석
    - 로컬 밀도 계산

    용도:
    - AI가 공간을 인식
    - 전술적 판단 지원
    - 통계 수집
    """
```

**3.2 action_executor.py - 액션 → 물리 변환**
```python
class ActionExecutor:
    """
    고수준 액션을 저수준 물리 파라미터로 변환

    예:
    SHOOT(target, power=80)
      → ball_velocity = [25, 5, 3.75]
      → player_velocity = [2.1, 0.3]

    PASS(target, power=60)
      → ball_velocity = [12, 8, 0.6]
      → pass accuracy 체크
      → 실패 시 방향 오차 추가
    """
```

**3.3 event_detector.py - 이벤트 감지**
```python
class EventDetector:
    """
    경기 이벤트 실시간 감지

    이벤트:
    - GOAL: 공이 골대 안에 들어감
    - THROW_IN: 공이 터치라인 밖으로
    - CORNER: 공이 골라인 밖 (수비팀 마지막 터치)
    - GOAL_KICK: 공이 골라인 밖 (공격팀 마지막 터치)
    """
```

**3.4 match_statistics.py - 통계 수집**
```python
class MatchStatistics:
    """
    경기 통계 추적

    통계:
    - 점유율 (possession)
    - 슈팅 (shots, shots on target)
    - 패스 (passes, pass accuracy)
    - 태클, 파울
    - xG (Expected Goals)
    - 선수별 통계
    """
```

**3.5 global_context.py - 경기 컨텍스트**
```python
class GlobalContext:
    """
    전역 경기 상태 추적

    추적 항목:
    - 점유율 밸런스
    - 경기 단계 (opening, midgame, closing)
    - 압박 강도
    - 템포
    """
```

**3.6 dynamic_balancer.py - 동적 밸런싱**
```python
class DynamicBalancer:
    """
    경기 밸런스 자동 조정

    목적: 한 팀이 지나치게 우위를 점하는 것 방지

    조정 요소:
    - pass_accuracy_multiplier: 패스 정확도
    - speed_multiplier: 이동 속도
    - tackle_range_multiplier: 태클 범위

    예: 홈팀이 70% 점유 중
    → 홈팀 pass accuracy × 0.9
    → 원정팀 speed × 1.1
    """
```

---

## 🎯 아키텍처 특징

### 강점

1. **✅ 물리 기반 정밀 시뮬레이션**
   - 0.1초 간격의 실시간 물리 계산
   - 현실적인 선수/공 움직임

2. **✅ 공간 인식 (Field State)**
   - 96존 그리드로 필드 분할
   - 존 지배율, 압박 맵 추적
   - AI가 공간을 이해하고 활용

3. **✅ 포지션 기반 AI**
   - GK, CB, CM, ST 등 포지션별 고유 행동
   - 컨텍스트 기반 의사결정

4. **✅ 동적 밸런싱**
   - 경기 흐름에 따라 능력치 자동 조정
   - 일방적인 경기 방지

5. **✅ 모듈화된 구조**
   - Physics, Agents, Simulation 레이어 분리
   - 각 컴포넌트 독립적으로 테스트 가능

### 약점

1. **❌ 전술 시스템 부재**
   - 포메이션이 있지만 전술적 효과가 미미
   - 포메이션별 차단률, 공격 스타일 등 없음
   - 감독 지시 시스템 없음

2. **❌ 레이어 경계 불명확**
   - ActionExecutor가 physics와 agents를 모두 참조
   - 의존성 방향이 혼재
   - 테스트 어려움

3. **❌ 에러 핸들링 부족**
   - 예외 처리 최소화
   - 로깅 시스템 없음
   - 디버깅 어려움

4. **❌ 설정 관리 미흡**
   - 하드코딩된 상수 많음
   - 설정 변경 시 코드 수정 필요

5. **❌ 확장성 제한**
   - 새로운 액션 추가 시 여러 파일 수정
   - 전술 시스템 추가가 어려움

---

## 🔗 전술 프레임워크와의 통합 방안

### 현재 문제점

```
[Simulation]                    [Tactics Framework]
     |                                  |
     |                                  |
     ❌ 통합 없음 - 완전히 독립적
```

**시뮬레이션에는 전술이 없고, 전술 프레임워크는 시뮬레이션과 연결되지 않음**

### 통합 아키텍처 제안

```
┌─────────────────────────────────────────────────────────────┐
│                  Application Layer                           │
│  (Match Orchestrator - 경기 전체 조율)                       │
└────────┬──────────────────────────────────────┬─────────────┘
         │                                       │
         ▼                                       ▼
┌────────────────────────┐           ┌────────────────────────┐
│  Simulation Engine     │           │  Tactics Framework     │
│                        │           │                        │
│  - GameSimulator       │◄─────────►│  - Formation System    │
│  - Physics             │  통합     │  - Blocking Rates      │
│  - Agents              │  인터페이스│  - Tactical Params    │
│  - FieldState          │           │  - Recommendations     │
└────────────────────────┘           └────────────────────────┘
```

### 통합 포인트

#### 1. Formation → Simulation

**경로**: Tactics Framework → Simulation

```python
# tactics/domain/entities/formation.py
class Formation:
    def get_player_positions(self) -> Dict[str, Position]:
        """
        포메이션별 선수 초기 위치 제공

        Returns:
            {
                'GK': Position(x=-48, y=0),
                'CB_L': Position(x=-40, y=-8),
                'CB_R': Position(x=-40, y=8),
                ...
            }
        """

# simulation/game_simulator.py
class GameSimulator:
    def initialize_with_formation(
        self,
        home_formation: Formation,
        away_formation: Formation
    ):
        """
        포메이션 기반 선수 배치

        1. 포메이션에서 포지션 정보 가져오기
        2. 선수를 해당 위치에 배치
        3. 포지션별 역할 부여
        """
```

#### 2. Tactical Parameters → Agent Behavior

**경로**: Tactics → Agents

```python
# tactics/domain/value_objects/tactical_parameters.py
@dataclass
class TacticalInstructions:
    """
    감독의 전술 지시

    Attributes:
        pressing_intensity: 1-10 (압박 강도)
        defensive_line: 1-10 (수비 라인 높이)
        tempo: 1-10 (경기 템포)
        width: 1-10 (공격 폭)
        pass_directness: 1-10 (패스 직선성)
    """

# agents/tactical_agent.py
class TacticalAgent:
    """
    전술 지시를 따르는 AI 에이전트

    기존 SimpleAgent를 확장하여 전술 지시 반영
    """
    def __init__(self, tactical_instructions: TacticalInstructions):
        self.instructions = tactical_instructions

    def decide_action(self, state, context):
        # 전술 지시에 따라 행동 조정
        if self.instructions.pressing_intensity >= 8:
            # 하이 프레스 → 공격적 압박
            if distance_to_ball < 10:
                return Action(ActionType.TACKLE)

        if self.instructions.pass_directness >= 7:
            # 직선 패스 선호 → 롱볼
            return Action(ActionType.PASS, power=80)
```

#### 3. Blocking Rates → Simulation Outcome

**경로**: Tactics → Simulation (확률 조정)

```python
# simulation/shot_calculator.py
class ShotCalculator:
    """
    슈팅 성공 확률 계산

    기존: 선수 능력치만 고려
    개선: 포메이션 차단률 반영
    """
    def calculate_shot_success_probability(
        self,
        shooter_ability: float,
        defender_formation: Formation,
        shot_location: Position
    ) -> float:
        # 1. 슛 경로 분류 (central_penetration, cutback, etc.)
        shot_category = self._classify_shot_location(shot_location)

        # 2. 포메이션 차단률 조회
        blocking_rate = defender_formation.get_blocking_rate(shot_category)

        # 3. 기본 성공률 계산
        base_success = shooter_ability * 0.3  # 30% base

        # 4. 차단률 적용
        final_success = base_success * (1 - blocking_rate / 100)

        return final_success
```

#### 4. Match Analysis → Tactics Feedback

**경로**: Simulation → Tactics (피드백 루프)

```python
# integration/match_analyzer.py
class MatchAnalyzer:
    """
    시뮬레이션 결과를 전술적으로 분석

    시뮬레이션 결과 → 전술 프레임워크 검증
    """
    def analyze_match_result(
        self,
        simulation_result: Dict,
        home_formation: Formation,
        away_formation: Formation
    ) -> Dict:
        """
        경기 결과 분석

        Returns:
            {
                'actual_blocking_rates': {...},  # 실제 차단률
                'predicted_blocking_rates': {...},  # 예측 차단률
                'accuracy': 0.85,  # 예측 정확도
                'insights': [...]  # 인사이트
            }
        """
        # 실제 골 분류
        actual_goals = self._classify_goals(simulation_result['events'])

        # 예측 vs 실제 비교
        for category, count in actual_goals.items():
            predicted_rate = home_formation.get_blocking_rate(category)
            actual_rate = self._calculate_actual_blocking_rate(
                count,
                simulation_result['statistics']['shots']
            )

            # 차이 분석
            diff = abs(predicted_rate - actual_rate)
            if diff > 10:
                insights.append(f"{category}: 예측 오차 {diff}%")

        return analysis
```

---

## 🏗️ 통합 아키텍처 설계

### Phase 1: 인터페이스 레이어 구축

```
tactics/
├── interfaces/
│   └── simulation/                    # 시뮬레이션 통합
│       ├── formation_provider.py      # 포메이션 → 시뮬레이션
│       ├── tactical_instructions_adapter.py
│       └── match_analyzer.py          # 시뮬레이션 결과 분석
```

### Phase 2: 시뮬레이션 확장

```
simulation/
├── tactical_integration.py             # 전술 시스템 통합 지점
├── formation_initializer.py            # 포메이션 기반 초기화
└── tactical_shot_calculator.py         # 전술 기반 슛 계산
```

### Phase 3: 공통 도메인 모델

```
shared/
└── domain/
    ├── position.py                     # 공통 Position 타입
    ├── player_role.py                  # 공통 역할 정의
    └── match_events.py                 # 공통 이벤트 타입
```

---

## 📊 통합 시나리오 예시

### 시나리오: Arsenal (4-3-3) vs Man City (4-3-3)

```python
# 1. 전술 설정
arsenal_formation = Formation.load("4-3-3")
arsenal_tactics = TacticalInstructions(
    pressing_intensity=9,
    defensive_line=8,
    tempo=8
)

mancity_formation = Formation.load("4-3-3")
mancity_tactics = TacticalInstructions(
    pressing_intensity=9,
    defensive_line=8,
    tempo=9
)

# 2. 시뮬레이션 초기화
simulator = GameSimulator()
simulator.set_formations(
    home=arsenal_formation,
    away=mancity_formation
)
simulator.set_tactical_instructions(
    home=arsenal_tactics,
    away=mancity_tactics
)

# 3. 경기 실행
result = simulator.simulate_match(
    home_players=arsenal_squad,
    away_players=mancity_squad
)

# 4. 전술 분석
analyzer = MatchAnalyzer()
tactical_analysis = analyzer.analyze(result, arsenal_formation, mancity_formation)

print(f"Arsenal 중앙 침투 차단률: {tactical_analysis['arsenal']['central_penetration']}")
print(f"예측: 85%, 실제: {tactical_analysis['actual']['central_penetration']}%")
```

---

## 🎯 다음 단계 제안

### Option 1: 최소 통합 (1주)
```
목표: 포메이션만 연동

작업:
1. Formation → 선수 초기 위치 매핑
2. 시뮬레이션에 포메이션 설정 인터페이스 추가
3. 테스트: 4-3-3 vs 4-4-2 비교

효과:
- 포메이션이 경기에 실제 영향
- 시각적 차이 확인 가능
```

### Option 2: 전술 파라미터 통합 (2주)
```
목표: 전술 지시까지 반영

작업:
1. TacticalInstructions → Agent 행동 조정
2. 압박 강도, 수비 라인 높이 구현
3. 전술별 경기 스타일 차이 검증

효과:
- 전술이 AI 행동에 영향
- 하이 프레스 vs 로우 블록 차이 명확
```

### Option 3: 완전 통합 (4주)
```
목표: 차단률 검증 및 피드백 루프

작업:
1. 포메이션별 차단률을 시뮬레이션에 반영
2. 슛/패스 성공률 계산 시 전술 고려
3. 시뮬레이션 결과로 차단률 검증
4. 피드백 루프 구축

효과:
- 전술 프레임워크 예측 정확도 검증
- 실제 데이터 기반 개선
- 프로덕션 레벨 완성도
```

---

## 💡 권장 사항

### 1. 단계적 통합 (추천) ⭐

```
Week 1-2: 포메이션 연동
  → 포메이션이 시뮬레이션에서 보이게

Week 3-4: 전술 파라미터
  → 하이 프레스가 실제로 작동하게

Week 5-6: 차단률 검증
  → 전술 프레임워크 예측 vs 시뮬레이션 결과

Week 7-8: 최적화 및 테스트
  → 버그 수정, 성능 개선
```

### 2. 아키텍처 개선 우선

현재 시뮬레이션의 구조적 문제를 먼저 해결:
```
1. Clean Architecture 적용
   - 레이어 분리 명확화
   - 의존성 역전

2. 에러 핸들링
   - 예외 처리 체계화
   - 로깅 시스템 추가

3. 설정 관리
   - 하드코딩 제거
   - Config 파일 분리

4. 테스트
   - 단위 테스트 추가
   - 통합 테스트 자동화
```

그 후 전술 통합

### 3. 인터페이스 우선 설계

통합 전에 인터페이스부터 정의:
```python
# interface 정의
class ITacticalSimulator(ABC):
    @abstractmethod
    def set_formation(self, team: str, formation: Formation): pass

    @abstractmethod
    def set_tactics(self, team: str, tactics: TacticalInstructions): pass

    @abstractmethod
    def simulate_with_tactics(self) -> TacticalMatchResult: pass

# 그 후 구현
class TacticalGameSimulator(GameSimulator, ITacticalSimulator):
    # 기존 GameSimulator를 확장
    ...
```

---

## 📝 요약

### 현재 상태
- ✅ 정밀한 물리 시뮬레이션
- ✅ 공간 인식 (96존)
- ✅ 포지션 기반 AI
- ❌ **전술 시스템 부재**
- ❌ 레이어 경계 불명확
- ❌ 확장성 제한

### 목표 상태
- ✅ 전술 프레임워크 완전 통합
- ✅ 포메이션이 실제 경기에 영향
- ✅ 전술 지시가 AI 행동에 반영
- ✅ 차단률 예측 정확도 검증
- ✅ Clean Architecture 적용
- ✅ 프로덕션 레벨 안정성

### 핵심 과제
**"전술이 실제로 작동하게 만들기"**

현재는 전술 프레임워크와 시뮬레이션이 완전히 분리되어 있어서,
전술 분석 결과가 실제 경기 시뮬레이션에 전혀 반영되지 않음.

통합 후에는:
- 4-3-3 하이 프레스 → 실제로 높은 압박
- 차단률 85% → 시뮬레이션에서도 85% 차단
- 전술 추천 → 실제 경기에서 효과 입증
