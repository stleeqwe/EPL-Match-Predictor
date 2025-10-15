# 전술 프레임워크 아키텍처 설계

## 📐 아키텍처 개요

### 설계 원칙

**Clean Architecture / Hexagonal Architecture 기반**

```
┌─────────────────────────────────────────────────────────┐
│                  Interfaces Layer                        │
│  (API, CLI, Web) - 외부 세계와의 인터페이스              │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│              Application Layer                           │
│  (Use Cases, Services) - 비즈니스 로직 조율              │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│                Domain Layer                              │
│  (Entities, Value Objects) - 핵심 비즈니스 규칙          │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│            Infrastructure Layer                          │
│  (Data Access, External APIs) - 외부 의존성              │
└─────────────────────────────────────────────────────────┘
```

### 핵심 개념

1. **의존성 방향**: 외부 → 내부 (Domain이 가장 안정적)
2. **인터페이스 기반**: 구현이 아닌 인터페이스에 의존
3. **테스트 가능성**: 각 레이어 독립적으로 테스트 가능
4. **확장성**: 새로운 기능 추가 시 기존 코드 수정 최소화

---

## 🏗️ 디렉토리 구조 (개선안)

### 현재 구조의 문제점

```
tactics/
├── core/              # 역할이 불명확
├── analyzer/          # 비즈니스 로직이 여기저기 분산
├── models/            # 데이터 모델만? 도메인 모델?
├── integration.py     # 단일 파일, 확장 어려움
```

### 개선된 구조

```
tactics/
│
├── domain/                          # 도메인 레이어 (핵심)
│   ├── __init__.py
│   ├── entities/                    # 엔티티 (비즈니스 객체)
│   │   ├── __init__.py
│   │   ├── formation.py            # Formation 엔티티
│   │   ├── team.py                 # Team 엔티티
│   │   ├── player.py               # Player 엔티티
│   │   └── match.py                # Match 엔티티
│   │
│   ├── value_objects/               # 값 객체 (불변)
│   │   ├── __init__.py
│   │   ├── blocking_rate.py        # 차단률 값 객체
│   │   ├── tactical_parameters.py  # 전술 파라미터
│   │   ├── position.py             # 포지션
│   │   └── goal_category.py        # 득점 경로
│   │
│   ├── repositories/                # 레포지토리 인터페이스
│   │   ├── __init__.py
│   │   ├── formation_repository.py
│   │   ├── team_repository.py
│   │   └── match_repository.py
│   │
│   └── exceptions.py                # 도메인 예외
│
├── application/                     # 애플리케이션 레이어
│   ├── __init__.py
│   ├── use_cases/                   # 유즈케이스 (비즈니스 로직)
│   │   ├── __init__.py
│   │   ├── analyze_formation.py    # 포메이션 분석
│   │   ├── calculate_blocking_rate.py
│   │   ├── recommend_formation.py
│   │   ├── analyze_match.py
│   │   └── classify_goal.py
│   │
│   ├── services/                    # 애플리케이션 서비스
│   │   ├── __init__.py
│   │   ├── tactical_analyzer.py
│   │   ├── formation_optimizer.py
│   │   └── match_predictor.py
│   │
│   └── dto/                         # 데이터 전송 객체
│       ├── __init__.py
│       ├── formation_dto.py
│       ├── match_analysis_dto.py
│       └── recommendation_dto.py
│
├── infrastructure/                  # 인프라 레이어
│   ├── __init__.py
│   ├── persistence/                 # 데이터 영속성
│   │   ├── __init__.py
│   │   ├── json_formation_repository.py
│   │   ├── database_team_repository.py
│   │   └── cache_manager.py
│   │
│   ├── external/                    # 외부 API 연동
│   │   ├── __init__.py
│   │   ├── fbref_client.py
│   │   ├── understat_client.py
│   │   └── fpl_client.py
│   │
│   └── mappers/                     # 데이터 매퍼
│       ├── __init__.py
│       ├── formation_mapper.py
│       └── player_mapper.py
│
├── interfaces/                      # 인터페이스 레이어
│   ├── __init__.py
│   ├── api/                         # REST API
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── formations.py
│   │   │   ├── analysis.py
│   │   │   └── recommendations.py
│   │   ├── schemas/                 # Pydantic 스키마
│   │   │   ├── formation_schema.py
│   │   │   └── analysis_schema.py
│   │   └── dependencies.py          # DI 설정
│   │
│   ├── cli/                         # CLI 인터페이스
│   │   ├── __init__.py
│   │   └── commands.py
│   │
│   └── web/                         # 웹 대시보드 (선택)
│       └── __init__.py
│
├── config/                          # 설정 관리
│   ├── __init__.py
│   ├── settings.py                  # 전역 설정
│   ├── constants.py                 # 상수
│   └── logging_config.py            # 로깅 설정
│
├── shared/                          # 공유 유틸리티
│   ├── __init__.py
│   ├── decorators.py                # 데코레이터
│   ├── validators.py                # 검증 로직
│   └── types.py                     # 커스텀 타입
│
├── tests/                           # 테스트
│   ├── unit/                        # 단위 테스트
│   │   ├── domain/
│   │   ├── application/
│   │   └── infrastructure/
│   ├── integration/                 # 통합 테스트
│   └── e2e/                         # E2E 테스트
│
├── data/                            # 데이터 파일
│   └── formations.json
│
├── __init__.py
├── __main__.py                      # CLI 엔트리포인트
└── container.py                     # DI 컨테이너
```

---

## 📦 레이어별 상세 설계

### 1. Domain Layer (도메인 레이어)

**역할**: 핵심 비즈니스 규칙, 외부 의존성 없음

#### Entities (엔티티)

```python
# domain/entities/formation.py

from dataclasses import dataclass
from typing import Dict, List
from ..value_objects.blocking_rate import BlockingRate
from ..value_objects.position import Position

@dataclass
class Formation:
    """
    포메이션 엔티티

    비즈니스 규칙:
    - 포메이션은 고유한 식별자를 가진다
    - 11개 포지션을 가진다
    - 각 득점 경로에 대한 차단률을 가진다
    """
    id: str                                # "4-3-3"
    name: str                              # "4-3-3 하이 프레싱"
    positions: List[Position]              # 11개 포지션
    blocking_rates: Dict[str, BlockingRate]  # 득점 경로별 차단률

    def get_blocking_rate(self, goal_category: str) -> BlockingRate:
        """특정 득점 경로에 대한 차단률 조회"""
        if goal_category not in self.blocking_rates:
            raise ValueError(f"Unknown goal category: {goal_category}")
        return self.blocking_rates[goal_category]

    def calculate_overall_defense_rating(self, weights: Dict[str, float]) -> float:
        """가중치 기반 종합 수비력 계산"""
        total_score = 0.0
        total_weight = sum(weights.values())

        for category, weight in weights.items():
            rate = self.get_blocking_rate(category)
            total_score += rate.value * (weight / total_weight)

        return total_score
```

#### Value Objects (값 객체)

```python
# domain/value_objects/blocking_rate.py

from dataclasses import dataclass

@dataclass(frozen=True)
class BlockingRate:
    """
    차단률 값 객체

    불변 객체로 0-100 범위의 값을 가진다
    """
    value: float

    def __post_init__(self):
        if not 0 <= self.value <= 100:
            raise ValueError(f"Blocking rate must be 0-100, got {self.value}")

    def apply_coefficient(self, coefficient: float) -> 'BlockingRate':
        """계수 적용하여 새로운 차단률 반환"""
        new_value = min(100, max(0, self.value * coefficient))
        return BlockingRate(new_value)

    def __str__(self) -> str:
        return f"{self.value:.1f}%"
```

```python
# domain/value_objects/tactical_parameters.py

from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class TacticalCoefficients:
    """
    전술 계수 값 객체

    모든 계수를 하나의 객체로 관리
    """
    team_ability: float = 1.0      # 0.80-1.20
    fatigue: float = 1.0           # 0.80-1.00
    psychology: float = 1.0        # 0.88-1.05
    weather: float = 1.0           # 0.90-1.00
    situation: float = 1.0         # 0.85-1.05

    def __post_init__(self):
        self._validate()

    def _validate(self):
        """범위 검증"""
        if not 0.80 <= self.team_ability <= 1.20:
            raise ValueError("team_ability must be 0.80-1.20")
        if not 0.80 <= self.fatigue <= 1.00:
            raise ValueError("fatigue must be 0.80-1.00")
        # ... 기타 검증

    def combined(self) -> float:
        """통합 계수 계산"""
        return (
            self.team_ability *
            self.fatigue *
            self.psychology *
            self.weather *
            self.situation
        )
```

#### Repository Interfaces (레포지토리 인터페이스)

```python
# domain/repositories/formation_repository.py

from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities.formation import Formation

class IFormationRepository(ABC):
    """포메이션 레포지토리 인터페이스"""

    @abstractmethod
    def find_by_id(self, formation_id: str) -> Optional[Formation]:
        """ID로 포메이션 조회"""
        pass

    @abstractmethod
    def find_all(self) -> List[Formation]:
        """모든 포메이션 조회"""
        pass

    @abstractmethod
    def save(self, formation: Formation) -> None:
        """포메이션 저장"""
        pass
```

---

### 2. Application Layer (애플리케이션 레이어)

**역할**: 유즈케이스 구현, 도메인 객체 조율

#### Use Cases

```python
# application/use_cases/calculate_blocking_rate.py

from dataclasses import dataclass
from typing import Dict, Any
from ...domain.repositories.formation_repository import IFormationRepository
from ...domain.value_objects.blocking_rate import BlockingRate
from ...domain.value_objects.tactical_parameters import TacticalCoefficients
from ...domain.exceptions import FormationNotFoundError

@dataclass
class CalculateBlockingRateRequest:
    """요청 DTO"""
    formation_id: str
    goal_category: str
    coefficients: TacticalCoefficients

@dataclass
class CalculateBlockingRateResponse:
    """응답 DTO"""
    formation_id: str
    goal_category: str
    base_rate: float
    predicted_rate: float
    combined_coefficient: float

class CalculateBlockingRateUseCase:
    """차단률 계산 유즈케이스"""

    def __init__(self, formation_repository: IFormationRepository):
        self._formation_repository = formation_repository

    def execute(self, request: CalculateBlockingRateRequest) -> CalculateBlockingRateResponse:
        """
        차단률 계산 실행

        비즈니스 플로우:
        1. 포메이션 조회
        2. 기본 차단률 가져오기
        3. 계수 적용
        4. 결과 반환
        """
        # 1. 포메이션 조회
        formation = self._formation_repository.find_by_id(request.formation_id)
        if not formation:
            raise FormationNotFoundError(f"Formation {request.formation_id} not found")

        # 2. 기본 차단률
        base_blocking_rate = formation.get_blocking_rate(request.goal_category)

        # 3. 계수 적용
        predicted_blocking_rate = base_blocking_rate.apply_coefficient(
            request.coefficients.combined()
        )

        # 4. 응답 생성
        return CalculateBlockingRateResponse(
            formation_id=request.formation_id,
            goal_category=request.goal_category,
            base_rate=base_blocking_rate.value,
            predicted_rate=predicted_blocking_rate.value,
            combined_coefficient=request.coefficients.combined()
        )
```

```python
# application/use_cases/recommend_formation.py

from dataclasses import dataclass
from typing import Dict, List
from ...domain.repositories.formation_repository import IFormationRepository
from ...domain.value_objects.tactical_parameters import TacticalCoefficients

@dataclass
class FormationRecommendation:
    formation_id: str
    formation_name: str
    overall_score: float
    category_scores: Dict[str, float]

@dataclass
class RecommendFormationRequest:
    opponent_attack_style: Dict[str, float]  # {category: frequency}
    coefficients: TacticalCoefficients

class RecommendFormationUseCase:
    """포메이션 추천 유즈케이스"""

    def __init__(self, formation_repository: IFormationRepository):
        self._formation_repository = formation_repository

    def execute(self, request: RecommendFormationRequest) -> List[FormationRecommendation]:
        """
        최적 포메이션 추천

        알고리즘:
        1. 모든 포메이션 조회
        2. 각 포메이션에 대해 가중 평균 차단률 계산
        3. 점수순 정렬
        4. 추천 리스트 반환
        """
        formations = self._formation_repository.find_all()
        recommendations = []

        for formation in formations:
            # 가중 평균 계산
            overall_score = formation.calculate_overall_defense_rating(
                request.opponent_attack_style
            )

            # 계수 적용
            overall_score *= request.coefficients.combined()
            overall_score = min(100, max(0, overall_score))

            # 카테고리별 점수
            category_scores = {}
            for category, weight in request.opponent_attack_style.items():
                rate = formation.get_blocking_rate(category)
                adjusted = rate.apply_coefficient(request.coefficients.combined())
                category_scores[category] = adjusted.value

            recommendations.append(FormationRecommendation(
                formation_id=formation.id,
                formation_name=formation.name,
                overall_score=overall_score,
                category_scores=category_scores
            ))

        # 점수순 정렬
        recommendations.sort(key=lambda r: r.overall_score, reverse=True)
        return recommendations
```

---

### 3. Infrastructure Layer (인프라 레이어)

**역할**: 외부 시스템과의 통신, 데이터 영속성

#### Repository Implementations

```python
# infrastructure/persistence/json_formation_repository.py

import json
from pathlib import Path
from typing import List, Optional, Dict
from ...domain.repositories.formation_repository import IFormationRepository
from ...domain.entities.formation import Formation
from ...infrastructure.mappers.formation_mapper import FormationMapper

class JsonFormationRepository(IFormationRepository):
    """JSON 파일 기반 포메이션 레포지토리"""

    def __init__(self, data_path: Path, cache_enabled: bool = True):
        self._data_path = data_path
        self._cache_enabled = cache_enabled
        self._cache: Optional[Dict[str, Formation]] = None
        self._mapper = FormationMapper()

    def find_by_id(self, formation_id: str) -> Optional[Formation]:
        """ID로 포메이션 조회"""
        formations = self._load_formations()
        return formations.get(formation_id)

    def find_all(self) -> List[Formation]:
        """모든 포메이션 조회"""
        formations = self._load_formations()
        return list(formations.values())

    def save(self, formation: Formation) -> None:
        """포메이션 저장"""
        # JSON 파일에 저장 (실제 구현)
        # 캐시 무효화
        self._cache = None

    def _load_formations(self) -> Dict[str, Formation]:
        """포메이션 로드 (캐싱 지원)"""
        if self._cache_enabled and self._cache is not None:
            return self._cache

        with open(self._data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        formations = {}
        for formation_id, formation_data in data['formations'].items():
            formation = self._mapper.to_entity(formation_id, formation_data)
            formations[formation_id] = formation

        if self._cache_enabled:
            self._cache = formations

        return formations
```

#### Mappers

```python
# infrastructure/mappers/formation_mapper.py

from typing import Dict, Any
from ...domain.entities.formation import Formation
from ...domain.value_objects.blocking_rate import BlockingRate
from ...domain.value_objects.position import Position

class FormationMapper:
    """포메이션 데이터 매퍼"""

    def to_entity(self, formation_id: str, data: Dict[str, Any]) -> Formation:
        """JSON 데이터 → 도메인 엔티티"""

        # 포지션 매핑
        positions = [
            Position(
                role=pos_data['role'],
                x=pos_data['x'],
                y=pos_data['y']
            )
            for pos_data in data['positions'].values()
        ]

        # 차단률 매핑
        blocking_rates = {
            category: BlockingRate(rate)
            for category, rate in data['blocking_rates'].items()
        }

        return Formation(
            id=formation_id,
            name=data['name_kr'],
            positions=positions,
            blocking_rates=blocking_rates
        )

    def to_dict(self, formation: Formation) -> Dict[str, Any]:
        """도메인 엔티티 → JSON 데이터"""
        return {
            'id': formation.id,
            'name_kr': formation.name,
            'positions': {
                i: {'role': p.role, 'x': p.x, 'y': p.y}
                for i, p in enumerate(formation.positions)
            },
            'blocking_rates': {
                category: rate.value
                for category, rate in formation.blocking_rates.items()
            }
        }
```

---

### 4. Interfaces Layer (인터페이스 레이어)

**역할**: 외부 요청 처리, API 제공

#### REST API

```python
# interfaces/api/routes/analysis.py

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict
from ....application.use_cases.calculate_blocking_rate import (
    CalculateBlockingRateUseCase,
    CalculateBlockingRateRequest,
    CalculateBlockingRateResponse
)
from ....domain.value_objects.tactical_parameters import TacticalCoefficients
from ..schemas.analysis_schema import (
    BlockingRateRequest,
    BlockingRateResponse
)
from ..dependencies import get_blocking_rate_use_case

router = APIRouter(prefix="/analysis", tags=["analysis"])

@router.post("/blocking-rate", response_model=BlockingRateResponse)
async def calculate_blocking_rate(
    request: BlockingRateRequest,
    use_case: CalculateBlockingRateUseCase = Depends(get_blocking_rate_use_case)
) -> BlockingRateResponse:
    """
    차단률 계산 API

    Args:
        request: 차단률 계산 요청

    Returns:
        계산된 차단률
    """
    try:
        # 요청 변환
        coefficients = TacticalCoefficients(
            team_ability=request.team_ability,
            fatigue=request.fatigue,
            psychology=request.psychology
        )

        use_case_request = CalculateBlockingRateRequest(
            formation_id=request.formation_id,
            goal_category=request.goal_category,
            coefficients=coefficients
        )

        # 유즈케이스 실행
        result = use_case.execute(use_case_request)

        # 응답 변환
        return BlockingRateResponse(
            formation_id=result.formation_id,
            goal_category=result.goal_category,
            base_rate=result.base_rate,
            predicted_rate=result.predicted_rate,
            combined_coefficient=result.combined_coefficient
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")
```

---

### 5. Configuration & DI (설정 및 의존성 주입)

```python
# container.py

from dependency_injector import containers, providers
from pathlib import Path

from .domain.repositories.formation_repository import IFormationRepository
from .infrastructure.persistence.json_formation_repository import JsonFormationRepository
from .application.use_cases.calculate_blocking_rate import CalculateBlockingRateUseCase
from .application.use_cases.recommend_formation import RecommendFormationUseCase
from .config.settings import Settings

class Container(containers.DeclarativeContainer):
    """DI 컨테이너"""

    # 설정
    config = providers.Configuration()

    # 레포지토리
    formation_repository = providers.Singleton(
        JsonFormationRepository,
        data_path=Path(__file__).parent / "data" / "formations.json",
        cache_enabled=config.cache_enabled
    )

    # 유즈케이스
    calculate_blocking_rate_use_case = providers.Factory(
        CalculateBlockingRateUseCase,
        formation_repository=formation_repository
    )

    recommend_formation_use_case = providers.Factory(
        RecommendFormationUseCase,
        formation_repository=formation_repository
    )
```

```python
# config/settings.py

from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """전역 설정"""

    # 애플리케이션
    app_name: str = "Tactical Framework"
    version: str = "2.0.0"
    debug: bool = False

    # 캐싱
    cache_enabled: bool = True
    cache_ttl: int = 3600  # seconds

    # 로깅
    log_level: str = "INFO"
    log_format: str = "json"

    # 데이터
    data_dir: str = "./data"

    # 외부 API
    fbref_api_key: Optional[str] = None
    understat_api_key: Optional[str] = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
```

---

## 🎯 핵심 설계 원칙

### 1. 의존성 역전 원칙 (DIP)

```
❌ 나쁜 예 (직접 의존)
UseCase → JsonRepository (구현체)

✅ 좋은 예 (인터페이스 의존)
UseCase → IRepository (인터페이스) ← JsonRepository
```

### 2. 단일 책임 원칙 (SRP)

각 클래스는 하나의 책임만:
- `Formation`: 포메이션 비즈니스 규칙
- `FormationRepository`: 포메이션 데이터 접근
- `CalculateBlockingRateUseCase`: 차단률 계산 플로우
- `FormationMapper`: 데이터 변환

### 3. 개방-폐쇄 원칙 (OCP)

확장에는 열려있고, 수정에는 닫혀있음:
```python
# 새로운 데이터 소스 추가 시
class DatabaseFormationRepository(IFormationRepository):
    # 기존 코드 수정 없이 새로운 구현체 추가
    pass
```

### 4. 인터페이스 분리 원칙 (ISP)

작고 명확한 인터페이스:
```python
# ❌ 거대한 인터페이스
class ITacticalService:
    def analyze_formation(...)
    def calculate_blocking(...)
    def recommend(...)
    def classify_goal(...)  # 너무 많음!

# ✅ 분리된 인터페이스
class IFormationAnalyzer: ...
class IBlockingCalculator: ...
class IFormationRecommender: ...
```

---

## 🔒 에러 핸들링 전략

### 도메인 예외

```python
# domain/exceptions.py

class TacticalFrameworkException(Exception):
    """기본 예외"""
    pass

class FormationNotFoundError(TacticalFrameworkException):
    """포메이션을 찾을 수 없음"""
    pass

class InvalidBlockingRateError(TacticalFrameworkException):
    """차단률 값이 유효하지 않음"""
    pass

class InvalidCoefficientError(TacticalFrameworkException):
    """계수 값이 유효 범위를 벗어남"""
    pass
```

### 에러 핸들러

```python
# interfaces/api/error_handlers.py

from fastapi import Request
from fastapi.responses import JSONResponse
from ...domain.exceptions import (
    TacticalFrameworkException,
    FormationNotFoundError
)

async def tactical_framework_exception_handler(
    request: Request,
    exc: TacticalFrameworkException
) -> JSONResponse:
    """도메인 예외 핸들러"""
    return JSONResponse(
        status_code=400,
        content={
            "error": exc.__class__.__name__,
            "message": str(exc),
            "path": request.url.path
        }
    )
```

---

## 📊 로깅 전략

```python
# shared/logging.py

import logging
import structlog
from typing import Any, Dict

def setup_logging(log_level: str = "INFO", log_format: str = "json"):
    """구조화된 로깅 설정"""

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer() if log_format == "json"
            else structlog.dev.ConsoleRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

# 사용 예
logger = structlog.get_logger()

logger.info(
    "blocking_rate_calculated",
    formation="4-3-3",
    goal_category="central_penetration",
    predicted_rate=85.2,
    user_id="user_123"
)
```

---

## 🧪 테스트 전략

### 단위 테스트

```python
# tests/unit/domain/entities/test_formation.py

import pytest
from tactics.domain.entities.formation import Formation
from tactics.domain.value_objects.blocking_rate import BlockingRate

class TestFormation:
    """Formation 엔티티 테스트"""

    def test_get_blocking_rate_success(self):
        # Given
        formation = Formation(
            id="4-3-3",
            name="4-3-3 하이 프레싱",
            positions=[],
            blocking_rates={
                "central_penetration": BlockingRate(85.0)
            }
        )

        # When
        rate = formation.get_blocking_rate("central_penetration")

        # Then
        assert rate.value == 85.0

    def test_get_blocking_rate_invalid_category(self):
        # Given
        formation = Formation(
            id="4-3-3",
            name="4-3-3",
            positions=[],
            blocking_rates={}
        )

        # When/Then
        with pytest.raises(ValueError):
            formation.get_blocking_rate("invalid_category")
```

### 통합 테스트

```python
# tests/integration/test_calculate_blocking_rate.py

import pytest
from pathlib import Path
from tactics.container import Container
from tactics.application.use_cases.calculate_blocking_rate import (
    CalculateBlockingRateRequest
)
from tactics.domain.value_objects.tactical_parameters import TacticalCoefficients

class TestCalculateBlockingRateIntegration:
    """차단률 계산 통합 테스트"""

    @pytest.fixture
    def container(self):
        container = Container()
        container.config.from_dict({
            "cache_enabled": False,
            "data_dir": str(Path(__file__).parent.parent.parent / "data")
        })
        return container

    def test_calculate_blocking_rate_full_flow(self, container):
        # Given
        use_case = container.calculate_blocking_rate_use_case()
        request = CalculateBlockingRateRequest(
            formation_id="4-3-3",
            goal_category="central_penetration",
            coefficients=TacticalCoefficients(team_ability=1.10)
        )

        # When
        response = use_case.execute(request)

        # Then
        assert response.formation_id == "4-3-3"
        assert response.base_rate == 85.0
        assert response.predicted_rate == 93.5  # 85 * 1.10
```

---

## 🚀 마이그레이션 계획

### Phase 1: 기반 구조 (Week 1)
- [ ] 새 디렉토리 구조 생성
- [ ] Domain Layer 구현
  - [ ] Entities
  - [ ] Value Objects
  - [ ] Repository Interfaces
- [ ] 기본 테스트 작성

### Phase 2: Application Layer (Week 2)
- [ ] Use Cases 구현
- [ ] Application Services
- [ ] DTOs
- [ ] 단위 테스트

### Phase 3: Infrastructure Layer (Week 2-3)
- [ ] Repository 구현체
- [ ] Mappers
- [ ] 캐싱
- [ ] 통합 테스트

### Phase 4: Interfaces Layer (Week 3)
- [ ] REST API
- [ ] CLI
- [ ] DI 컨테이너
- [ ] E2E 테스트

### Phase 5: 기존 코드 마이그레이션 (Week 4)
- [ ] 기존 코드 점진적 마이그레이션
- [ ] 하위 호환성 유지
- [ ] 문서화 업데이트

---

## 📚 참고 자료

- Clean Architecture (Robert C. Martin)
- Domain-Driven Design (Eric Evans)
- Hexagonal Architecture (Alistair Cockburn)
- SOLID Principles

---

## ✅ 기대 효과

1. **유지보수성 향상**: 관심사 분리로 코드 이해 용이
2. **테스트 용이성**: 각 레이어 독립적으로 테스트
3. **확장성**: 새 기능 추가 시 기존 코드 수정 최소화
4. **재사용성**: 도메인 로직을 다양한 인터페이스에서 재사용
5. **팀 협업**: 명확한 경계로 병렬 작업 가능
