# 전술 프레임워크 (Tactics Framework)

## 개요

EPL 데이터 기반 축구 전술 분석 및 예측 시스템입니다.

### 주요 기능

1. **포메이션 시스템**
   - 6가지 주요 포메이션 (4-3-3, 4-2-3-1, 4-4-2, 3-5-2, 4-1-4-1, 3-4-3)
   - 포지션별 좌표 및 역할 정의

2. **전술 파라미터**
   - 압박 강도 (1-10)
   - 수비 라인 높이 (1-10)
   - 공격 템포 (1-10)
   - 빌드업 스타일 등

3. **득점 경로 분석**
   - 12가지 득점 경로 분류
   - 빌드업 점진적, 역습, 중앙 침투, 측면 침투, 컷백 등

4. **차단률 계산**
   - 포메이션별 득점 경로 차단 효율
   - EPL 통계 데이터 기반

## 디렉토리 구조

```
tactics/
├── core/                 # 핵심 전술 정의
│   ├── formations.py     # 포메이션 시스템
│   ├── tactical_styles.py # 전술 스타일
│   └── playing_styles.py  # 플레이 스타일
│
├── models/               # 데이터 모델
│   ├── formation_model.py
│   ├── tactics_model.py
│   └── goal_path_model.py
│
├── data/                 # 전술 데이터
│   ├── formations.json
│   ├── tactical_presets.json
│   └── blocking_rates.json
│
├── analyzer/             # 분석 엔진
│   ├── effectiveness_calculator.py
│   ├── matchup_analyzer.py
│   └── goal_path_classifier.py
│
├── api/                  # API 엔드포인트
│   └── tactics_routes.py
│
└── tests/                # 테스트
    └── test_formations.py
```

## 독립성 원칙

이 프레임워크는 기존 프로젝트(`simulation/`, `models/`, `api/`)와 **독립적으로** 작동합니다.

### 통합 인터페이스

나중에 병합 시 사용할 인터페이스:

```python
from tactics.integration import TacticsIntegration

# 선수 능력치에 전술 가중치 적용
adjusted_ratings = TacticsIntegration.apply_tactics_to_player(
    player_data=player,
    tactics=team_tactics
)

# 팀의 전술 적합도 계산
score = TacticsIntegration.calculate_team_tactical_score(
    squad=squad,
    formation="4-3-3",
    tactics=tactical_setup
)
```

## 데이터 소스

- EPL 2017/18 ~ 2024/25 시즌
- FBref (StatsBomb 데이터)
- Understat (xG 데이터)
- 경기 결과 및 득점 경로 분석

## 사용 예시

```python
from tactics import FormationSystem, EffectivenessCalculator

# 포메이션 로드
formation_sys = FormationSystem()
formation_433 = formation_sys.get_formation("4-3-3")

# 차단률 계산
calculator = EffectivenessCalculator()
blocking_rate = calculator.calculate_blocking_rate(
    formation="4-3-3",
    goal_category="central_penetration",
    team_ability=1.12  # 맨시티급
)

print(f"4-3-3 중앙 침투 차단률: {blocking_rate:.1f}%")
```

## Phase별 구현 계획

### Phase 1: 기반 구조 (완료)
- [x] 디렉토리 구조 생성
- [ ] 포메이션 데이터 모델
- [ ] 전술 파라미터 시스템

### Phase 2: 데이터 모델 (진행 중)
- [ ] 득점 경로 분류 시스템
- [ ] 차단률 계산 모델
- [ ] 기본 데이터 (formations.json)

### Phase 3: 분석 엔진
- [ ] 효과성 계산기
- [ ] 전술 매칭 분석
- [ ] 통계 검증

### Phase 4: API 통합
- [ ] 독립 API 엔드포인트
- [ ] 기존 API와 통합
- [ ] 문서화

## 향후 확장

- 실시간 웹 스크래핑 (FBref, Understat)
- 머신러닝 예측 모델
- 대시보드 UI (Streamlit)
- 경기 결과 예측 API

## 라이선스

MIT License
