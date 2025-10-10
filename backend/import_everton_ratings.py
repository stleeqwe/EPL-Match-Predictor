"""
에버튼 선수 능력치 데이터 임포트 스크립트
"""

import requests
import json

API_URL = "http://localhost:5001/api"

# 에버튼 팀 코멘트
team_comment = "전체적으로 수비적인 전술. 볼을 전방으로 무리하게 찌르는 공격패스보단 횡으로 안정적으로 돌리면서 상대 헛점을 노리는 전술. 수비와 미들진이 평균적인 수준을 보여주지만 최전방 공격진의 공격력이 떨어짐."

# 에버튼 선수 능력치 (올바른 ID)
everton_ratings = {
    "287": {
        "_name": "Jordan Pickford",
        "_position": "GK",
        "_averageRating": 4.07,
        "reflexes": 4,
        "positioning": 4.5,
        "handling": 4,
        "one_on_one": 4,
        "aerial_control": 3.75,
        "buildup": 3.75,
        "long_kick": 4.5,
        "leadership_communication": 4.25,
        "_subPosition": "GK",
        "_comment": "상위 클럽 수준의 골키퍼. 에버튼의 평범한 수비력을 준수한 수준으로 끌어올리는 동력"
    },
    "291": {
        "_name": "James Tarkowski",
        "_position": "CB",
        "_averageRating": 3.09,
        "positioning_sense": 3.25,
        "composure": 3.75,
        "interception": 2.75,
        "aerial_duel": 3,
        "marking": 2.5,
        "tackling": 3,
        "short_pass": 3,
        "speed": 2.5,
        "press_resistance": 2.5,
        "long_pass": 3.75,
        "progressive_pass_vision": 3.5,
        "physicality": 3.5,
        "jumping": 3.25,
        "leadership": 4.5,
        "_subPosition": "CB",
        "_comment": "중앙수비수 임에도 킥력이 좋아 후방에서 전방으로의 롱킥으로 공격전개 능력이 있음. 발이 느려 속공이나 드리블 좋은 윙어에게 약함. 정적인 수비 상황에서는 안정적일 수 있으나 그 외 탁월한 수비능력을 보여주진 않음."
    },
    "295": {
        "_name": "Michael Keane",
        "_position": "CB",
        "_averageRating": 2.44,
        "positioning_sense": 2.5,
        "composure": 2.5,
        "interception": 2,
        "aerial_duel": 3.5,
        "marking": 2.5,
        "tackling": 2,
        "short_pass": 2.25,
        "speed": 1.5,
        "press_resistance": 2.5,
        "long_pass": 1.75,
        "progressive_pass_vision": 2,
        "physicality": 3.75,
        "jumping": 3.75,
        "leadership": 3,
        "_subPosition": "CB",
        "_comment": "피지컬이 좋아 셋트피스 시 헤딩에 이점이 있음. 피지컬이 좋아 정적인 상황에서의 수비력은 좋으나 역습 및 혼돈스런 상황에서 수비력이 약함."
    },
    "302": {
        "_name": "Idrissa Gueye",
        "_position": "DM",
        "_averageRating": 2.79,
        "positioning": 2.5,
        "ball_winning": 3,
        "pass_accuracy": 3,
        "composure": 3,
        "press_resistance": 2.75,
        "defensive_positioning": 3,
        "pressing": 3,
        "progressive_play": 2.25,
        "tempo_control": 2.25,
        "stamina": 3.5,
        "physicality": 1.75,
        "mobility": 3.5,
        "leadership": 2,
        "_subPosition": "DM"
    },
    "303": {
        "_name": "James Garner",
        "_position": "MF",
        "_averageRating": 2.92,
        "stamina": 3,
        "game_control": 2.75,
        "pass_accuracy": 3.75,
        "transition": 3.25,
        "vision": 3.25,
        "dribbling_press_resistance": 2.75,
        "space_creation": 2.5,
        "defensive_contribution": 2.75,
        "ball_retention": 2.75,
        "long_shot": 2.75,
        "acceleration": 2.5,
        "agility": 2.5,
        "physicality": 2.5,
        "_subPosition": "CM",
        "_comment": "1. 안정적이고 보수적인 스타일로 실수가 적으나 공격력도 적음\n2. 볼을 횡으로만 운반하는 스타일로 결정적인 상황을 만드는데 기여하지 못함\n3. 오른발 킥 감각이 좋아 셋트피스에서 강점을 보임"
    }
}

def save_player_ratings(player_id, ratings_data):
    """선수 능력치 저장"""
    url = f"{API_URL}/ratings"

    # _name, _position, _averageRating 등 메타데이터 제거하고 능력치만 추출
    ratings = {}
    for key, value in ratings_data.items():
        if not key.startswith('_'):
            ratings[key] = value
        elif key in ['_comment', '_subPosition']:
            # _comment와 _subPosition은 메타데이터로 저장
            ratings[key] = value

    payload = {
        "player_id": int(player_id),
        "user_id": "default",
        "ratings": ratings
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        result = response.json()
        print(f"✅ {ratings_data['_name']} (#{player_id}) - {result['saved_count']} ratings saved")
        return True
    except Exception as e:
        print(f"❌ Error saving {ratings_data['_name']} (#{player_id}): {str(e)}")
        return False

def main():
    """메인 함수"""
    print("=" * 60)
    print("에버튼 선수 능력치 임포트")
    print("=" * 60)

    print(f"\n📝 팀 코멘트:\n{team_comment}\n")

    print("=" * 60)
    print("선수 능력치 저장 중...")
    print("=" * 60)

    success_count = 0
    total_count = len(everton_ratings)

    for player_id, ratings_data in everton_ratings.items():
        if save_player_ratings(player_id, ratings_data):
            success_count += 1

    print("\n" + "=" * 60)
    print(f"완료: {success_count}/{total_count} 선수 저장 성공")
    print("=" * 60)

    # 팀 코멘트는 별도로 저장 (향후 구현 예정)
    print(f"\n💡 팀 코멘트는 프론트엔드에서 별도로 관리됩니다.")

if __name__ == '__main__':
    main()
