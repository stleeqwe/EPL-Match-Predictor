# Prompt Documentation

⚠️ **이 디렉토리는 문서화 전용입니다.**

## 실제 프롬프트 위치

실제로 사용되는 프롬프트는 다음 위치에 있습니다:

### Phase 1 (시나리오 생성)
- **파일**: `backend/simulation/v2/ai_scenario_generator.py`
- **함수**: `AIScenarioGenerator._build_system_prompt()`, `_build_scenario_generation_prompt()`
- **설명**: 5-7개 다중 시나리오 생성

### Phase 3 (분석 및 조정)
- **파일**: `backend/simulation/v2/ai_analyzer.py`
- **함수**: `AIAnalyzer._build_system_prompt()`, `_build_analysis_prompt()`
- **설명**: 시뮬레이션 결과 분석 및 파라미터 조정

### Enriched Match Prediction
- **파일**: `backend/ai/enriched_qwen_client.py`
- **함수**: `EnrichedQwenClient._build_enriched_system_prompt()`, `_build_enriched_match_prompt()`
- **설명**: Enriched Domain Data 기반 매치 예측

---

## 이 디렉토리의 용도

이 디렉토리의 파일들은:
- ✅ 프롬프트 설계 문서
- ✅ 프롬프트 엔지니어링 가이드
- ✅ 예시 및 템플릿

실제 코드에서는 **import되지 않습니다**.

---

## 프롬프트 수정 방법

프롬프트를 수정하려면 위에 명시된 **실제 파일**을 수정하세요.

예시:
```bash
# Phase 1 프롬프트 수정
vim backend/simulation/v2/ai_scenario_generator.py

# Phase 3 프롬프트 수정
vim backend/simulation/v2/ai_analyzer.py
```

---

**Last updated**: 2025-10-17
