"""
에버튼 선수 능력치 원본 데이터 복구
사용자가 전달한 5명의 선수 능력치와 코멘트를 정확히 저장
"""
import requests
import json

API_URL = "http://localhost:5001/api/ratings"

# 사용자가 전달한 에버튼 팀 분석 원본 데이터
EVERTON_ANALYSIS = {
    "Jordan Pickford": {
        "player_id": 287,
        "ratings": {
            "reflexes": 4,
            "positioning": 4.5,
            "handling": 4,
            "one_on_one": 4,
            "aerial_control": 3.75,
            "long_kick": 4.5,
            "buildup": 3.75,
            "leadership_communication": 4.25,
            "_subPosition": "GK",
            "_comment": "상위 클럽 수준의 골키퍼. 반사신경과 위치 선정이 뛰어나며 발 기술도 준수. 간혹 집중력 저하로 실수가 나오는 것이 아쉬움."
        }
    },
    "James Tarkowski": {
        "player_id": 291,
        "ratings": {
            "tackle": 3.5,
            "positioning_def": 3.5,
            "marking": 3.25,
            "aerial_def": 3.25,
            "strength": 3.25,
            "speed": 2.5,
            "passing_short": 2.75,
            "passing_long": 3,
            "buildup": 2.5,
            "ball_control": 2.5,
            "dribbling": 2,
            "leadership_communication": 3.75,
            "concentration": 3,
            "positioning_off": 2.75,
            "_subPosition": "CB",
            "_comment": "에버튼의 수비 리더. 수비 기본기는 탄탄하지만 빌드업 능력이 부족하고 스피드가 느려 역습에 취약. 나이가 들면서 기량 저하가 보임."
        }
    },
    "Michael Keane": {
        "player_id": 295,
        "ratings": {
            "tackle": 2.75,
            "positioning_def": 2.5,
            "marking": 2.5,
            "aerial_def": 3,
            "strength": 2.75,
            "speed": 2.25,
            "passing_short": 2.25,
            "passing_long": 2.5,
            "buildup": 2,
            "ball_control": 2,
            "dribbling": 1.75,
            "leadership_communication": 2.5,
            "concentration": 2,
            "positioning_off": 2.25,
            "_subPosition": "CB",
            "_comment": "백업 센터백. 모든 면에서 평범하거나 그 이하 수준. 집중력 부족으로 실수가 잦고 공격 가담 능력도 떨어짐. 타코프스키와 함께 뛸 때 더욱 약점이 드러남."
        }
    },
    "Idrissa Gana Gueye": {
        "player_id": 302,
        "ratings": {
            "tackle": 3.5,
            "positioning_def": 3.25,
            "interception": 3.5,
            "strength": 3,
            "stamina": 3.25,
            "speed": 2.75,
            "passing_short": 2.5,
            "passing_long": 2.25,
            "vision": 2,
            "ball_control": 2.5,
            "dribbling": 2.25,
            "work_rate": 3.5,
            "concentration": 3,
            "_subPosition": "DM",
            "_comment": "수비형 미드필더의 교과서. 태클과 인터셉트가 뛰어나지만 나이가 많아 스피드와 빌드업 능력이 부족. 단순한 역할에서는 여전히 리그 평균 이상이지만 복합적인 플레이는 어려움."
        }
    },
    "James Garner": {
        "player_id": 303,
        "ratings": {
            "tackle": 2.75,
            "positioning_def": 2.75,
            "interception": 2.75,
            "passing_short": 3.25,
            "passing_long": 3.5,
            "vision": 3,
            "ball_control": 3,
            "dribbling": 2.75,
            "shot": 2.5,
            "stamina": 3,
            "work_rate": 3.25,
            "creativity": 2.75,
            "concentration": 2.75,
            "_subPosition": "CM",
            "_comment": "젊고 유망한 중앙 미드필더. 패스 능력이 좋고 시야도 넓지만 아직 경험 부족. 수비 기여도가 낮고 결정적인 순간에 임팩트가 부족한 것이 약점."
        }
    }
}


def save_player_ratings(player_name, player_id, ratings):
    """선수 능력치 저장"""
    print(f"\n{'='*60}")
    print(f"저장 중: {player_name} (ID: {player_id})")
    print(f"{'='*60}")

    payload = {
        "player_id": player_id,
        "user_id": "default",
        "ratings": ratings
    }

    try:
        response = requests.post(API_URL, json=payload, timeout=10)

        if response.status_code == 200:
            result = response.json()
            print(f"✅ 성공: {len(ratings)} 개 평가 저장됨")

            # 코멘트 확인
            if "_comment" in ratings:
                print(f"   💬 코멘트: {ratings['_comment'][:50]}...")
            if "_subPosition" in ratings:
                print(f"   📍 세부 포지션: {ratings['_subPosition']}")

            return True
        else:
            print(f"❌ 실패: {response.status_code}")
            print(f"   {response.text}")
            return False

    except Exception as e:
        print(f"❌ 오류: {e}")
        return False


def main():
    print("\n" + "="*60)
    print("에버튼 선수 능력치 복구 시작")
    print("="*60)

    success_count = 0
    total_count = len(EVERTON_ANALYSIS)

    for player_name, data in EVERTON_ANALYSIS.items():
        if save_player_ratings(player_name, data["player_id"], data["ratings"]):
            success_count += 1

    print("\n" + "="*60)
    print(f"완료: {success_count}/{total_count} 명 저장 성공")
    print("="*60)

    if success_count == total_count:
        print("\n✅ 모든 선수 데이터 복구 완료!")
    else:
        print(f"\n⚠️  {total_count - success_count}명 저장 실패")


if __name__ == "__main__":
    main()
