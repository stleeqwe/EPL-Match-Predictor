# 모듈러 시뮬레이션 아키텍처 비전

**설계 철학**: 독립적인 세그먼트 + 통합 이론

---

## 🎯 핵심 개념

### "각 세그먼트는 독립적으로 완벽하게 작동한다"

```
Tactics Segment는 전술만 관리
Player Segment는 선수만 관리
Position Segment는 포지션만 관리

각각은 다른 세그먼트를 알 필요 없음
통합 이론이 이들을 연결
```

---

## 🏗️ 세그먼트 분류

### 1. Tactics Segment (전술)

**책임**: 전술 분석, 포메이션, 차단률

```
backend/segments/tactics/
├── domain/
│   ├── entities/
│   │   ├── formation.py              # Formation 엔티티
│   │   ├── tactical_style.py         # 전술 스타일
│   │   └── blocking_strategy.py      # 차단 전략
│   │
│   ├── value_objects/
│   │   ├── blocking_rate.py          # 차단률
│   │   ├── formation_shape.py        # 포메이션 형태
│   │   └── tactical_parameters.py    # 전술 파라미터
│   │
│   └── repositories/
│       └── formation_repository.py
│
├── application/
│   ├── use_cases/
│   │   ├── analyze_formation.py
│   │   ├── recommend_formation.py
│   │   └── calculate_blocking_rate.py
│   │
│   └── services/
│       └── tactical_analyzer.py
│
├── infrastructure/
│   └── persistence/
│       └── json_formation_repository.py
│
└── __init__.py

# 독립적 사용 가능
from segments.tactics import FormationAnalyzer
analyzer = FormationAnalyzer()
result = analyzer.analyze("4-3-3")
```

**통합 포인트**:
- Formation ID → Position Segment
- Tactical Parameters → Match Segment

---

### 2. Player Segment (선수)

**책임**: 선수 능력치, 컨디션, 성장

```
backend/segments/player/
├── domain/
│   ├── entities/
│   │   ├── player.py                 # Player 엔티티
│   │   ├── physical_attributes.py    # 신체 능력
│   │   ├── technical_attributes.py   # 기술 능력
│   │   └── mental_attributes.py      # 정신력
│   │
│   ├── value_objects/
│   │   ├── stamina.py                # 스태미나
│   │   ├── form.py                   # 폼
│   │   ├── injury_status.py          # 부상 상태
│   │   └── overall_rating.py         # 종합 레이팅
│   │
│   └── repositories/
│       └── player_repository.py
│
├── application/
│   ├── use_cases/
│   │   ├── calculate_player_rating.py
│   │   ├── apply_fatigue.py
│   │   └── check_injury.py
│   │
│   └── services/
│       └── player_evaluator.py
│
└── infrastructure/
    └── persistence/
        └── database_player_repository.py

# 독립적 사용
from segments.player import PlayerEvaluator
evaluator = PlayerEvaluator()
rating = evaluator.calculate_overall(player)
```

**통합 포인트**:
- Player ID → Position Segment
- Player Attributes → Match Segment

---

### 3. Position Segment (포지션)

**책임**: 포지션별 역할, 책임, 위치

```
backend/segments/position/
├── domain/
│   ├── entities/
│   │   ├── position.py               # Position 엔티티
│   │   ├── position_role.py          # 포지션 역할
│   │   └── tactical_responsibility.py # 전술적 책임
│   │
│   ├── value_objects/
│   │   ├── field_coordinates.py      # 필드 좌표
│   │   ├── movement_range.py         # 이동 범위
│   │   ├── zone_coverage.py          # 커버 구역
│   │   └── position_type.py          # GK, CB, CM, etc.
│   │
│   └── repositories/
│       └── position_repository.py
│
├── application/
│   ├── use_cases/
│   │   ├── assign_position.py
│   │   ├── calculate_coverage.py
│   │   └── get_optimal_position.py
│   │
│   └── services/
│       └── position_manager.py
│
└── infrastructure/
    └── persistence/
        └── json_position_repository.py

# 독립적 사용
from segments.position import PositionManager
manager = PositionManager()
optimal_pos = manager.get_optimal_position(
    position_type="CB",
    formation="4-3-3"
)
```

**통합 포인트**:
- Position ID → Tactics Segment (formation)
- Position ID → Player Segment (assignment)

---

### 4. Match Elements Segment (경기 요소)

**책임**: 경기 이벤트, 액션, 규칙

```
backend/segments/match_elements/
├── domain/
│   ├── entities/
│   │   ├── match_event.py            # 경기 이벤트
│   │   ├── action.py                 # 액션 (슛, 패스)
│   │   ├── match_state.py            # 경기 상태
│   │   └── field.py                  # 필드 정보
│   │
│   ├── value_objects/
│   │   ├── score.py                  # 점수
│   │   ├── time.py                   # 경기 시간
│   │   ├── ball_position.py          # 공 위치
│   │   ├── weather.py                # 날씨
│   │   └── event_type.py             # 이벤트 타입
│   │
│   └── repositories/
│       └── match_event_repository.py
│
├── application/
│   ├── use_cases/
│   │   ├── record_event.py
│   │   ├── calculate_xg.py
│   │   └── validate_action.py
│   │
│   └── services/
│       └── match_orchestrator.py
│
└── infrastructure/
    └── persistence/
        └── event_store.py

# 독립적 사용
from segments.match_elements import EventRecorder
recorder = EventRecorder()
recorder.record(ShotEvent(player_id=1, xg=0.45))
```

**통합 포인트**:
- Match Event → Player Segment
- Match Event → Position Segment
- Match Event → Tactics Segment

---

### 5. Physics Segment (물리) - 선택적

**책임**: 물리 시뮬레이션 (필요 시)

```
backend/segments/physics/
├── domain/
│   ├── entities/
│   │   ├── physical_object.py        # 물리 객체
│   │   ├── ball_physics.py           # 공 물리
│   │   └── player_physics.py         # 선수 물리
│   │
│   ├── value_objects/
│   │   ├── velocity.py               # 속도
│   │   ├── acceleration.py           # 가속도
│   │   └── force.py                  # 힘
│   │
│   └── engines/
│       └── physics_engine.py
│
└── application/
    └── services/
        └── physics_calculator.py

# 독립적 사용
from segments.physics import PhysicsEngine
engine = PhysicsEngine()
new_position = engine.calculate_trajectory(ball, force)
```

---

## 🔗 Simulation Integration Theory

### 통합 이론의 역할

**"세그먼트들이 서로 대화하는 방법을 정의"**

```
backend/integration/
├── theory/
│   ├── integration_contracts.py      # 세그먼트 간 계약
│   ├── domain_events.py              # 도메인 이벤트
│   ├── shared_kernel.py              # 공유 커널
│   └── anti_corruption_layer.py      # 부패 방지 레이어
│
├── orchestration/
│   ├── match_simulator.py            # 경기 시뮬레이터
│   ├── event_bus.py                  # 이벤트 버스
│   └── saga_coordinator.py           # 사가 코디네이터
│
└── adapters/
    ├── tactics_adapter.py            # Tactics → Integration
    ├── player_adapter.py             # Player → Integration
    ├── position_adapter.py           # Position → Integration
    └── match_adapter.py              # Match → Integration
```

---

## 📐 통합 패턴

### 1. Domain Events (도메인 이벤트)

**개념**: 세그먼트 간 비동기 통신

```python
# integration/theory/domain_events.py

from dataclasses import dataclass
from datetime import datetime
from typing import Any

@dataclass
class DomainEvent:
    """기본 도메인 이벤트"""
    event_id: str
    event_type: str
    occurred_at: datetime
    payload: Any

# Tactics Segment에서 발행
@dataclass
class FormationChangedEvent(DomainEvent):
    """포메이션 변경 이벤트"""
    team_id: str
    old_formation: str
    new_formation: str
    tactical_changes: dict

# Player Segment에서 구독
class PlayerSegment:
    def on_formation_changed(self, event: FormationChangedEvent):
        """포메이션 변경 시 선수 위치 재조정"""
        for player in self.get_team_players(event.team_id):
            new_position = self.calculate_position(
                player,
                event.new_formation
            )
            player.update_position(new_position)
```

### 2. Shared Kernel (공유 커널)

**개념**: 모든 세그먼트가 공유하는 핵심 개념

```python
# integration/theory/shared_kernel.py

from enum import Enum
from dataclasses import dataclass

class TeamSide(Enum):
    """팀 사이드 (공유)"""
    HOME = "home"
    AWAY = "away"

@dataclass
class FieldCoordinates:
    """필드 좌표 (공유)"""
    x: float  # -52.5 to +52.5
    y: float  # -34.0 to +34.0

    def __post_init__(self):
        if not (-52.5 <= self.x <= 52.5):
            raise ValueError("X out of bounds")
        if not (-34.0 <= self.y <= 34.0):
            raise ValueError("Y out of bounds")

class PositionType(Enum):
    """포지션 타입 (공유)"""
    GK = "goalkeeper"
    CB = "center_back"
    FB = "fullback"
    DM = "defensive_midfielder"
    CM = "central_midfielder"
    CAM = "attacking_midfielder"
    WG = "winger"
    ST = "striker"
```

### 3. Integration Contracts (통합 계약)

**개념**: 세그먼트 간 명시적 계약

```python
# integration/theory/integration_contracts.py

from abc import ABC, abstractmethod
from typing import Protocol

class ITacticsProvider(Protocol):
    """전술 제공자 계약"""

    def get_formation(self, formation_id: str) -> Formation:
        """포메이션 조회"""
        ...

    def get_player_positions(self, formation_id: str) -> dict[str, FieldCoordinates]:
        """포메이션별 선수 위치"""
        ...

    def calculate_blocking_rate(
        self,
        formation_id: str,
        attack_type: str
    ) -> float:
        """차단률 계산"""
        ...

class IPlayerProvider(Protocol):
    """선수 제공자 계약"""

    def get_player(self, player_id: str) -> Player:
        """선수 조회"""
        ...

    def get_player_attributes(self, player_id: str) -> dict:
        """선수 능력치"""
        ...

    def update_stamina(self, player_id: str, stamina: float) -> None:
        """스태미나 업데이트"""
        ...

class IPositionProvider(Protocol):
    """포지션 제공자 계약"""

    def get_position_role(self, position_type: PositionType) -> PositionRole:
        """포지션 역할"""
        ...

    def get_coverage_zone(self, position_type: PositionType) -> list[FieldCoordinates]:
        """커버 구역"""
        ...

class IMatchCoordinator(Protocol):
    """경기 조율자 계약"""

    def record_event(self, event: MatchEvent) -> None:
        """이벤트 기록"""
        ...

    def get_match_state(self) -> MatchState:
        """현재 경기 상태"""
        ...
```

### 4. Anti-Corruption Layer (부패 방지 레이어)

**개념**: 외부 세그먼트의 변경으로부터 보호

```python
# integration/adapters/tactics_adapter.py

class TacticsAdapter:
    """
    Tactics Segment의 Anti-Corruption Layer

    외부에서 Tactics Segment에 접근할 때 이 어댑터를 거침
    내부 구조 변경이 외부에 영향 없음
    """

    def __init__(self, tactics_segment: TacticsSegment):
        self._tactics = tactics_segment

    def get_formation_positions(
        self,
        formation_id: str
    ) -> dict[str, FieldCoordinates]:
        """
        내부 Formation 엔티티 → 표준 좌표로 변환
        """
        formation = self._tactics.get_formation(formation_id)

        # 내부 구조를 표준 인터페이스로 변환
        positions = {}
        for position_data in formation.positions:
            # 내부 Position → 공유 FieldCoordinates
            positions[position_data.role] = FieldCoordinates(
                x=position_data.x,
                y=position_data.y
            )

        return positions

    def calculate_shot_success_probability(
        self,
        formation_id: str,
        shot_location: FieldCoordinates,
        shot_type: str
    ) -> float:
        """
        복잡한 내부 로직을 단순한 인터페이스로 노출
        """
        # 내부 복잡한 계산
        formation = self._tactics.get_formation(formation_id)
        blocking_rate = formation.get_blocking_rate(shot_type)

        # 간단한 결과 반환
        return 1.0 - (blocking_rate / 100.0)
```

---

## 🎮 경기 시뮬레이션 통합

### Match Simulator (통합 오케스트레이터)

```python
# integration/orchestration/match_simulator.py

class MatchSimulator:
    """
    모든 세그먼트를 조율하는 경기 시뮬레이터

    각 세그먼트는 독립적으로 작동
    시뮬레이터는 이들을 조합
    """

    def __init__(
        self,
        tactics_provider: ITacticsProvider,
        player_provider: IPlayerProvider,
        position_provider: IPositionProvider,
        match_coordinator: IMatchCoordinator,
        event_bus: EventBus
    ):
        self.tactics = tactics_provider
        self.players = player_provider
        self.positions = position_provider
        self.match = match_coordinator
        self.events = event_bus

    def simulate_match(
        self,
        home_team: TeamSetup,
        away_team: TeamSetup
    ) -> MatchResult:
        """
        경기 시뮬레이션

        각 세그먼트의 기능을 조합하여 경기 진행
        """
        # 1. 초기화 (Tactics Segment)
        home_positions = self.tactics.get_player_positions(
            home_team.formation_id
        )
        away_positions = self.tactics.get_player_positions(
            away_team.formation_id
        )

        # 2. 선수 배치 (Player + Position Segment)
        for player_id in home_team.player_ids:
            player = self.players.get_player(player_id)
            position = self.positions.get_position_role(player.position_type)

            # 이벤트 발행
            self.events.publish(PlayerPositionedEvent(
                player_id=player_id,
                position=home_positions[player.position_type]
            ))

        # 3. 경기 진행 (Match Elements Segment)
        for tick in range(5400):  # 90분
            # 각 세그먼트에서 데이터 가져오기
            match_state = self.match.get_match_state()

            # 액션 결정 및 실행
            for player_id in home_team.player_ids:
                action = self._decide_action(player_id, match_state)
                result = self._execute_action(action)

                # 결과 기록
                self.match.record_event(result)

        # 4. 결과 반환
        return self._generate_result()

    def _decide_action(self, player_id: str, match_state: MatchState) -> Action:
        """
        액션 결정 (모든 세그먼트 통합)
        """
        # Player Segment: 선수 능력
        player = self.players.get_player(player_id)
        attributes = self.players.get_player_attributes(player_id)

        # Position Segment: 포지션 역할
        role = self.positions.get_position_role(player.position_type)

        # Tactics Segment: 전술 지시
        # (이벤트를 통해 받은 전술 파라미터 사용)

        # 통합 의사결정
        if role.primary_duty == "DEFEND":
            if match_state.ball_distance(player) < 5.0:
                return Action(ActionType.TACKLE)
            else:
                return Action(ActionType.MARK_OPPONENT)

        elif role.primary_duty == "ATTACK":
            if player.has_ball:
                if self._should_shoot(player, match_state):
                    return Action(ActionType.SHOOT)
                else:
                    return Action(ActionType.PASS)

        return Action(ActionType.MOVE_TO_POSITION)

    def _execute_action(self, action: Action) -> ActionResult:
        """
        액션 실행 (세그먼트 간 협력)
        """
        if action.type == ActionType.SHOOT:
            # Tactics: 상대 포메이션 차단률
            blocking_rate = self.tactics.calculate_blocking_rate(
                formation_id=self.opponent_formation,
                attack_type="shot"
            )

            # Player: 슈팅 능력
            shooting_skill = self.players.get_player_attributes(
                action.player_id
            )['shooting']

            # 통합 계산
            success_probability = (
                shooting_skill / 100.0 * (1 - blocking_rate / 100.0)
            )

            # 결과 판정
            if random.random() < success_probability:
                return ActionResult(ActionType.GOAL)
            else:
                return ActionResult(ActionType.SHOT_SAVED)

        # ... 기타 액션
```

---

## 📊 세그먼트 간 통신 흐름

### 예시: 슛 이벤트

```
1. Player Segment: "선수 #10이 슛 시도"
   └─> Event: ShootAttemptEvent

2. Position Segment: "ST 포지션의 슛 위치 확인"
   └─> 슛 위치 = 페널티 박스 중앙

3. Tactics Segment: "상대 4-3-3 포메이션 차단률 조회"
   └─> 중앙 침투 차단률 = 85%

4. Match Elements Segment: "슛 결과 판정"
   └─> 성공 확률 = 선수능력 × (1 - 차단률)
   └─> 판정: 골 실패 (GK 선방)

5. Event Bus: "모든 세그먼트에 결과 통지"
   ├─> Player Segment: 선수 #10 슛 실패 기록
   ├─> Tactics Segment: 포메이션 효과 검증
   └─> Match Elements Segment: 경기 통계 업데이트
```

---

## 🎯 구현 로드맵

### Phase 1: 세그먼트 독립 구축 (2-3주)

**Week 1: Tactics Segment**
```
✓ Domain Layer 완성
✓ Application Layer
✓ Infrastructure Layer
✓ 독립 테스트 (100% 커버리지)
```

**Week 2: Player Segment**
```
✓ Domain Layer
✓ Application Layer
✓ Infrastructure Layer
✓ 독립 테스트
```

**Week 3: Position & Match Elements Segments**
```
✓ Position Segment
✓ Match Elements Segment
✓ 각각 독립 테스트
```

### Phase 2: 통합 이론 수립 (1주)

**Week 4: Integration Theory**
```
✓ Shared Kernel 정의
✓ Domain Events 시스템
✓ Integration Contracts
✓ Anti-Corruption Layers
✓ Event Bus 구현
```

### Phase 3: 통합 및 시뮬레이터 (1-2주)

**Week 5-6: Integration**
```
✓ Match Simulator 구현
✓ Adapters 작성
✓ 통합 테스트
✓ E2E 테스트
✓ 성능 최적화
```

---

## ✅ 장점 요약

### 1. 완전한 독립성
```python
# Tactics Segment만 사용
from segments.tactics import FormationAnalyzer
analyzer = FormationAnalyzer()
result = analyzer.analyze("4-3-3")

# Player Segment만 사용
from segments.player import PlayerEvaluator
evaluator = PlayerEvaluator()
rating = evaluator.calculate_overall(player)

# 통합 사용
from integration import MatchSimulator
simulator = MatchSimulator(tactics, player, position, match)
result = simulator.simulate()
```

### 2. 테스트 용이성
```python
# 각 세그먼트 독립 테스트
def test_tactics_segment():
    analyzer = FormationAnalyzer()
    assert analyzer.analyze("4-3-3").defensive_rating > 80

# 통합 테스트
def test_match_simulation():
    simulator = MatchSimulator(...)
    result = simulator.simulate()
    assert result.home_score >= 0
```

### 3. 확장성
```
새 세그먼트 추가:
1. 새 세그먼트 구현
2. Integration Contract 정의
3. Adapter 작성
4. Event 연결
→ 기존 세그먼트 수정 불필요!
```

### 4. 재사용성
```
Tactics Segment를 다른 프로젝트에 재사용:
- 야구 시뮬레이션
- 농구 시뮬레이션
- 전략 게임

각 세그먼트가 독립적이므로 자유롭게 재사용 가능
```

---

## 🚀 시작 제안

### 1단계: 기존 코드 정리
```bash
# 기존 시뮬레이션 관련 삭제
rm -rf backend/simulation/
rm -rf backend/physics/
rm -rf backend/agents/

# Tactics만 유지
# backend/tactics/ → backend/segments/tactics/로 이동
```

### 2단계: Tactics Segment 2.0 구축
```
이미 작성한 ARCHITECTURE.md 기반
Clean Architecture 완전 적용
독립적으로 완벽하게 작동
```

### 3단계: Player Segment 구축
```
Player Domain 재설계
독립적으로 완성
```

### 4단계: 통합 이론 정의
```
Domain Events
Shared Kernel
Integration Contracts
```

### 5단계: 통합
```
Match Simulator 구현
모든 세그먼트 연결
경기 시뮬레이션 완성
```

---

이 접근이 정답입니다! 🎯

이제 어떻게 진행하시겠습니까?
