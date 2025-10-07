# Rating Editor UI/UX Improvements

## 작업 일자
2025-01-XX

## 개요
능력치 평가 화면(RatingEditor)의 High-Tech/Cybernetic 테마 강화 및 사용성 개선 작업

---

## 1. 레이아웃 개선

### 1.1 능력치 본문 영역 세로 높이 증가
**파일**: `frontend/epl-predictor/src/components/RatingEditor.js` (line 523)

**변경 내용**:
```javascript
// Before
max-h-[calc(100vh-28rem)]

// After
max-h-[calc(100vh-20rem)]
```

**효과**: 슬라이더 영역에 약 8rem(128px) 더 많은 공간 확보

---

## 2. 선수 프로필 사진 스캐닝 효과 극대화

### 2.1 강화된 스캔 라인 시스템
**파일**: `frontend/epl-predictor/src/components/RatingEditor.js` (lines 271-313)

**주요 변경사항**:

#### A. 데이터 그리드 오버레이 (사진 뒤)
- **위치**: z-0 (가장 뒤)
- **패턴**: 8px x 8px 그리드
- **색상**: rgba(6, 182, 212, 0.3)
- **애니메이션**: opacity [0 → 0.6 → 0], 4.5초 반복

```javascript
<motion.div
  className="absolute inset-0 pointer-events-none z-0 overflow-hidden rounded-sm"
  style={{
    backgroundImage: `
      linear-gradient(rgba(6, 182, 212, 0.3) 1px, transparent 1px),
      linear-gradient(90deg, rgba(6, 182, 212, 0.3) 1px, transparent 1px)
    `,
    backgroundSize: '8px 8px'
  }}
  animate={{ opacity: [0, 0.6, 0] }}
  transition={{ duration: 4.5, repeat: Infinity, ease: "linear" }}
/>
```

#### B. 스캔 라인 레이어 (사진 위)
- **위치**: z-10
- **두께**: 1.5px (얇고 정밀한 라인)
- **색상**: cyan-400/80 (투명도 80%)
- **글로우**: boxShadow 6px, opacity 0.6
- **상하 글로우**: cyan-400/20, blur 8px
- **속도**: 4.5초 (느린 분석 느낌)

```javascript
{/* Main Bright Line */}
<div
  className="absolute left-0 right-0 h-[1.5px] bg-gradient-to-r from-transparent via-cyan-400/80 to-transparent"
  style={{ boxShadow: '0 0 6px rgba(6, 182, 212, 0.6)' }}
/>

{/* Glow Above */}
<div
  className="absolute left-0 right-0 h-8 -top-8 bg-gradient-to-b from-transparent to-cyan-400/20"
  style={{ filter: 'blur(8px)' }}
/>

{/* Glow Below */}
<div
  className="absolute left-0 right-0 h-8 top-0 bg-gradient-to-t from-transparent to-cyan-400/20"
  style={{ filter: 'blur(8px)' }}
/>
```

#### C. Z-Index 레이어 구조
```
z-20: 코너 브래킷 (Corner Brackets)
z-10: 스캔 라인 (Scan Line)
z-5:  선수 사진 (Photo)
z-0:  데이터 그리드 (Data Grid)
```

### 2.2 제거된 효과들
- ❌ 상하 보조 라인 (Secondary Lines)
- ❌ Scanning Reveal Effect (어두운 영역 reveal)
- 이유: 시각적 복잡도 감소, 메인 스캔 라인에 집중

---

## 3. Tech 테마 강화 - 가중치 뱃지 & Info Circle

### 3.1 가중치 뱃지 (Weight Badge)
**파일**: `frontend/epl-predictor/src/components/RatingSlider.js` (line 249)

**변경 내용**:
```javascript
// Before
<span className="badge text-xs px-2 py-0.5"
  style={{ backgroundColor: 'rgba(50, 10, 80, 0.9)', color: '#FFFFFF' }}>
  {Math.round(weight * 100)}%
</span>

// After
<span className="text-xs px-2 py-0.5 rounded-none bg-slate-900 text-white border border-cyan-500/40 font-mono">
  {Math.round(weight * 100)}%
</span>
```

**개선 사항**:
- ✅ 각진 모서리 (`rounded-none`)
- ✅ 어두운 배경 (`bg-slate-900`)
- ✅ Cyan 테두리 (`border-cyan-500/40`)
- ✅ Monospace 폰트 (`font-mono`)
- ✅ 명확한 흰색 텍스트 (`text-white`)

### 3.2 Info Circle
**파일**: `frontend/epl-predictor/src/components/RatingSlider.js` (lines 255-274)

**변경 내용**:
```javascript
// Icon
<button className="text-cyan-400/60 hover:text-cyan-300 transition-colors">
  <Info className="w-4 h-4" />
</button>

// Tooltip
<motion.div
  className="absolute left-6 -top-2 z-50 bg-slate-900/95 border border-cyan-500/40 p-2 rounded-none text-xs text-cyan-100 whitespace-nowrap backdrop-blur-sm"
>
  {helperText}
</motion.div>
```

**개선 사항**:
- ✅ Cyan 색상 아이콘 (`text-cyan-400/60`)
- ✅ 각진 툴팁 (`rounded-none`)
- ✅ Cyan 테두리 툴팁
- ✅ 어두운 배경 + backdrop blur

---

## 4. 기술적 세부사항

### 4.1 애니메이션 타이밍
| 요소 | Duration | Easing |
|------|----------|--------|
| 스캔 라인 | 4.5초 | linear |
| 데이터 그리드 | 4.5초 | linear |
| 슬라이더 진입 | 0.4초 | easeOut |
| 카운터 | 1.2초 | easeOut |

### 4.2 색상 시스템
| 용도 | 색상 코드 | 사용처 |
|------|-----------|--------|
| Cyan Primary | #06B6D4 | 스캔 라인, 테두리 |
| Cyan Glow | rgba(6, 182, 212, 0.6) | 스캔 라인 glow |
| Slate Dark | #0F172A | 배경, 뱃지 |
| White | #FFFFFF | 텍스트 |

### 4.3 성능 최적화
- `pointer-events-none`: 스캔 효과 레이어에 적용하여 상호작용 방지
- `backdrop-blur-sm`: 최소한의 blur로 성능 유지
- `will-change`: 애니메이션 성능 향상 (필요시 추가 가능)

---

## 5. 사용자 피드백 반영

### 반복 조정 내역
1. **스캔 라인 두께**: 3px → 1.5px
2. **스캔 라인 밝기**: 100% → 80% opacity
3. **스캔 속도**: 3초 → 4.5초
4. **가중치 뱃지 배경**:
   - rgba(50, 10, 80, 0.9)
   - → bg-cyan-500/20
   - → bg-cyan-600/40
   - → bg-cyan-700/60
   - → bg-cyan-900/90
   - → **bg-slate-900** (최종)

---

## 6. 파일 변경 목록

### 수정된 파일
1. **RatingEditor.js** (3개 섹션)
   - Line 523: 능력치 영역 높이
   - Lines 271-313: 스캔 효과 시스템
   - 기타: z-index 조정

2. **RatingSlider.js** (2개 섹션)
   - Line 249: 가중치 뱃지
   - Lines 255-274: Info circle & tooltip

### 추가된 의존성
- 없음 (기존 framer-motion 사용)

---

## 7. 스크린샷 위치 (참고용)

```
선수 프로필 → 능력치 평가 진입
├─ 선수 사진: 스캔 효과 확인
│  ├─ 데이터 그리드 (뒤)
│  ├─ 선수 사진 (중간)
│  └─ 스캔 라인 (앞)
└─ 능력치 슬라이더: 가중치 뱃지 & info circle 확인
```

---

## 8. 향후 개선 가능 사항

### 고려 사항
- [ ] 스캔 라인에 스캔 진행률 표시 추가
- [ ] 데이터 분석 진행률 바 (Progress Bar)
- [ ] 스캔 완료 시 확인 효과 (Checkmark animation)
- [ ] 포지션별 스캔 색상 차별화 (GK, DF, MF, FW)
- [ ] 스캔 중 능력치 값 일시적으로 표시 (hover effect)

### 성능 모니터링
- 스캔 애니메이션이 CPU/GPU 사용량에 미치는 영향 측정
- 저사양 기기에서 테스트 필요

---

## 9. 테스트 체크리스트

- [x] 스캔 효과 시각적 확인
- [x] 데이터 그리드가 사진 뒤에 있는지 확인
- [x] 가중치 뱃지 가독성 확인
- [x] Info circle hover 동작 확인
- [x] 브라우저 캐시 클리어 후 재확인
- [ ] 다양한 브라우저 테스트 (Chrome, Safari, Firefox)
- [ ] 모바일 반응형 테스트
- [ ] 다크모드/라이트모드 호환성

---

## 10. 참고 자료

### 디자인 컨셉
- High-Tech / Cybernetic UI
- Data Analysis / Scanning 시뮬레이션
- WCAG AA 접근성 기준 준수

### 기술 스택
- React 18
- Framer Motion
- Tailwind CSS
- Lucide React Icons

---

**작업 완료일**: 2025-01-XX
**작업자**: Claude Code
**버전**: v1.0
