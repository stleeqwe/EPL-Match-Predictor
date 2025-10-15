# Fixtures 데이터 테스트

## 1. 백엔드 API 테스트

```bash
curl http://localhost:5001/api/fixtures | python3 -m json.tool | head -50
```

**예상 결과:** 20개 경기 데이터 (JSON 배열)

## 2. 브라우저 콘솔에서 확인할 사항

F12를 눌러 콘솔을 열고 다음을 확인:

### 체크리스트:

- [ ] "Fetching fixtures from API..." 메시지가 표시되는가?
- [ ] "Fixtures received:" 다음에 배열이 표시되는가?
- [ ] "Total fixtures: X" - X가 0보다 큰가?
- [ ] "MatchSelector Debug:" 의 totalFixtures가 0보다 큰가?
- [ ] "Filtered fixtures:" 개수가 0보다 큰가?

### 문제 진단:

**케이스 1: totalFixtures가 0**
→ API 호출 실패 또는 데이터 없음

**케이스 2: totalFixtures > 0, Filtered fixtures = 0**
→ filterGameweek 값 확인 필요
→ gameweek 데이터 형식 불일치

**케이스 3: 에러 메시지**
→ 네트워크 오류 또는 CORS 문제

## 3. 현재 설정

- 백엔드 API: `http://localhost:5001/api/fixtures`
- 프론트엔드: `http://localhost:3000`
- 기본 필터: `filterGameweek = 'all'`

## 4. 일반적인 해결책

### 문제: CORS 오류
```bash
# 백엔드 재시작
cd backend
source venv/bin/activate
python3 -m flask run --host=0.0.0.0 --port=5001
```

### 문제: 캐시 문제
```
브라우저에서:
1. Ctrl + Shift + R (하드 리프레시)
2. 또는 콘솔에서: localStorage.clear()
```

### 문제: fixtures가 빈 배열
```javascript
// 콘솔에서 직접 테스트:
fetch('http://localhost:5001/api/fixtures')
  .then(r => r.json())
  .then(d => console.log('Direct fetch:', d))
```
