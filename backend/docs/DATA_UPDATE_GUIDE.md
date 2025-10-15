# 🔄 EPL Squad Data Update Guide

## 문제점 요약

기존 `squad_data.py` 파일이 2025년 10월 2일에 생성된 후 업데이트되지 않아:
- ❌ 잘못된 선수 정보 (이적하지 않은 선수 포함)
- ❌ 등번호 오류
- ❌ 나이 정보 누락 (대부분 0)
- ❌ 주전/벤치 구분 없음

## ✅ 해결 방법

Fantasy Premier League API를 사용하여 **실시간 데이터**로 자동 업데이트합니다.

---

## 🚀 즉시 실행 (방법 1 - 추천)

터미널에서 다음 명령어를 실행하세요:

```bash
cd /Users/pukaworks/Desktop/soccer-predictor/backend
chmod +x update_data.sh
./update_data.sh
```

완료!

---

## 🔧 수동 실행 (방법 2)

### 1단계: 스크립트 직접 실행

```bash
cd /Users/pukaworks/Desktop/soccer-predictor/backend
source venv/bin/activate
python3 scripts/update_squad_from_fpl.py
```

### 2단계: 서버 재시작

```bash
# 기존 서버 종료 (Ctrl+C)
python3 api/app.py
```

---

## 🌐 API로 업데이트 (방법 3)

서버가 실행 중일 때:

```bash
curl -X POST http://localhost:5001/api/admin/update-squad-data
```

응답 예시:
```json
{
  "success": true,
  "message": "Squad data updated successfully",
  "stats": {
    "teams": 17,
    "total_players": 531,
    "total_starters": 187,
    "updated_at": "2025-10-05T..."
  }
}
```

---

## 📊 업데이트 후 확인

### 팀 목록 확인
```bash
curl http://localhost:5001/api/teams
```

### 특정 팀 선수 확인
```bash
curl http://localhost:5001/api/squad/Arsenal
```

응답에서 확인할 사항:
- ✅ `is_starter`: 주전 여부
- ✅ `age`: 실제 나이
- ✅ `number`: 정확한 등번호
- ✅ `stats`: 출전 기록, 골, 도움

---

## 🔁 자동 업데이트 설정 (선택사항)

매일 자동으로 업데이트하려면:

### macOS/Linux - Cron 사용

```bash
crontab -e
```

다음 줄 추가:
```
0 3 * * * cd /Users/pukaworks/Desktop/soccer-predictor/backend && ./update_data.sh >> /tmp/squad_update.log 2>&1
```

매일 새벽 3시에 자동 업데이트됩니다.

---

## 📝 업데이트 내역

### Before (기존)
```python
'Arsenal': [
    {
        'name': 'Martín Zubimendi',  # ❌ Real Sociedad 선수
        'number': 3,                   # ❌ 잘못된 등번호
        'age': 0,                      # ❌ 정보 없음
    }
]
```

### After (업데이트 후)
```python
'Arsenal': [
    {
        'id': 45,
        'name': 'Bukayo Saka',        # ✅ 실제 Arsenal 선수
        'number': 7,                   # ✅ 정확한 등번호
        'age': 23,                     # ✅ 실제 나이
        'is_starter': True,            # ✅ 주전 판단
        'stats': {
            'appearances': 10,
            'goals': 3,
            'assists': 7,
            ...
        }
    }
]
```

---

## 🆘 문제 해결

### "No such file or directory" 오류
```bash
cd /Users/pukaworks/Desktop/soccer-predictor/backend
ls -la update_data.sh  # 파일 확인
chmod +x update_data.sh # 실행 권한 부여
```

### "ModuleNotFoundError" 오류
```bash
source venv/bin/activate
pip install requests flask flask-cors
```

### API 연결 실패
- 인터넷 연결 확인
- Fantasy Premier League 사이트 접속 가능 여부 확인

---

## 📚 추가 정보

- **데이터 소스**: https://fantasy.premierleague.com/api/bootstrap-static/
- **업데이트 주기**: 필요시 또는 매주 1회 권장
- **파일 위치**: `/backend/data/squad_data.py`

---

## 💡 팁

1. **시즌 초반**: 이적 시장이 활발하므로 주 2-3회 업데이트
2. **시즌 중반**: 주 1회 업데이트로 충분
3. **부상 정보**: Fantasy API는 실시간 출전 정보 반영

---

질문이나 문제가 있으면 로그를 확인하세요:
```bash
tail -f /tmp/squad_update.log
```
