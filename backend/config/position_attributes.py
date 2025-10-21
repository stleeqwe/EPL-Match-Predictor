"""
포지션별 능력치 설정 및 가중치
각 포지션마다 고유한 능력치 항목과 가중치를 정의
Frontend의 positionAttributes.js와 동일한 로직
"""

POSITION_ATTRIBUTES = {
    'GK': {
        'name': '골키퍼',
        'name_en': 'Goalkeeper',
        'attributes': [
            {'key': 'reflexes', 'label': '반응속도', 'weight': 0.17},
            {'key': 'positioning', 'label': '포지셔닝', 'weight': 0.17},
            {'key': 'handling', 'label': '핸들링', 'weight': 0.15},
            {'key': 'one_on_one', 'label': '1:1 대응', 'weight': 0.14},
            {'key': 'aerial_control', 'label': '공중볼 지배력', 'weight': 0.12},
            {'key': 'buildup', 'label': '빌드업 능력', 'weight': 0.13},
            {'key': 'leadership_communication', 'label': '리더십&의사소통', 'weight': 0.07},
            {'key': 'long_kick', 'label': '롱볼 킥력', 'weight': 0.05}
        ]
    },
    'CB': {
        'name': '센터백',
        'name_en': 'Center Back',
        'attributes': [
            {'key': 'positioning_reading', 'label': '포지셔닝 & 공간 읽기', 'weight': 0.15},
            {'key': 'composure_judgement', 'label': '침착성 & 판단력', 'weight': 0.12},
            {'key': 'interception', 'label': '인터셉트', 'weight': 0.10},
            {'key': 'aerial_duel', 'label': '공중볼 경합', 'weight': 0.09},
            {'key': 'tackle_marking', 'label': '태클 & 마킹', 'weight': 0.11},
            {'key': 'speed', 'label': '스피드', 'weight': 0.10},
            {'key': 'passing', 'label': '패스 능력', 'weight': 0.13},
            {'key': 'physical_jumping', 'label': '피지컬 & 점프력', 'weight': 0.08},
            {'key': 'buildup_contribution', 'label': '빌드업 기여도', 'weight': 0.10},
            {'key': 'leadership', 'label': '리더십', 'weight': 0.02}
        ]
    },
    'FB': {
        'name': '풀백',
        'name_en': 'Fullback/Wingback',
        'attributes': [
            {'key': 'stamina', 'label': '지구력', 'weight': 0.16},
            {'key': 'speed', 'label': '스피드', 'weight': 0.15},
            {'key': 'defensive_positioning', 'label': '수비 포지셔닝', 'weight': 0.12},
            {'key': 'one_on_one_tackle', 'label': '1:1 수비 & 태클', 'weight': 0.13},
            {'key': 'overlapping', 'label': '오버래핑', 'weight': 0.11},
            {'key': 'crossing_accuracy', 'label': '크로스 정확도', 'weight': 0.11},
            {'key': 'covering', 'label': '백업 커버링', 'weight': 0.09},
            {'key': 'agility', 'label': '민첩성', 'weight': 0.07},
            {'key': 'press_resistance', 'label': '압박 저항력', 'weight': 0.04},
            {'key': 'long_shot', 'label': '중거리 슈팅', 'weight': 0.02}
        ]
    },
    'DM': {
        'name': '수비형 미드필더',
        'name_en': 'Defensive Midfielder',
        'attributes': [
            {'key': 'positioning', 'label': '포지셔닝', 'weight': 0.12},
            {'key': 'ball_winning', 'label': '볼 차단 & 회수', 'weight': 0.12},
            {'key': 'pass_accuracy', 'label': '패스 정확도', 'weight': 0.10},
            {'key': 'composure_press_resistance', 'label': '침착성 & 압박 해소', 'weight': 0.12},
            {'key': 'backline_protection', 'label': '백라인 보호', 'weight': 0.10},
            {'key': 'pressing_transition_blocking', 'label': '공간 압박 & 전환 차단', 'weight': 0.10},
            {'key': 'progressive_play', 'label': '공격 전개', 'weight': 0.09},
            {'key': 'tempo_control', 'label': '템포 조절', 'weight': 0.07},
            {'key': 'stamina', 'label': '지구력', 'weight': 0.06},
            {'key': 'physicality_mobility', 'label': '피지컬 & 기동력', 'weight': 0.10},
            {'key': 'leadership', 'label': '리더십', 'weight': 0.02}
        ]
    },
    'CM': {
        'name': '중앙 미드필더',
        'name_en': 'Central Midfielder',
        'attributes': [
            {'key': 'stamina', 'label': '지구력', 'weight': 0.11},
            {'key': 'ball_possession_circulation', 'label': '볼 소유 & 순환', 'weight': 0.11},
            {'key': 'pass_accuracy_vision', 'label': '패스 정확도 & 시야', 'weight': 0.13},
            {'key': 'transition', 'label': '전환 플레이', 'weight': 0.10},
            {'key': 'dribbling_press_resistance', 'label': '드리블 & 탈압박', 'weight': 0.10},
            {'key': 'space_creation', 'label': '공간 창출/침투', 'weight': 0.09},
            {'key': 'defensive_contribution', 'label': '수비 가담', 'weight': 0.09},
            {'key': 'ball_retention', 'label': '볼 키핑', 'weight': 0.07},
            {'key': 'long_shot', 'label': '중거리 슈팅', 'weight': 0.06},
            {'key': 'agility_acceleration', 'label': '민첩성 & 가속력', 'weight': 0.09},
            {'key': 'physicality', 'label': '피지컬', 'weight': 0.05}
        ]
    },
    'CAM': {
        'name': '공격형 미드필더',
        'name_en': 'Attacking Midfielder',
        'attributes': [
            {'key': 'creativity', 'label': '창의성', 'weight': 0.13},
            {'key': 'vision_killpass', 'label': '시야 & 킬패스', 'weight': 0.12},
            {'key': 'dribbling', 'label': '드리블 돌파', 'weight': 0.11},
            {'key': 'decision_making', 'label': '결정적 순간 판단', 'weight': 0.11},
            {'key': 'penetration', 'label': '공간 침투', 'weight': 0.10},
            {'key': 'shooting_finishing', 'label': '슈팅 & 마무리', 'weight': 0.11},
            {'key': 'one_touch_pass', 'label': '원터치 패스', 'weight': 0.08},
            {'key': 'pass_and_move', 'label': '패스 & 무브', 'weight': 0.07},
            {'key': 'acceleration', 'label': '가속력', 'weight': 0.07},
            {'key': 'agility', 'label': '민첩성', 'weight': 0.06},
            {'key': 'set_piece', 'label': '세트피스', 'weight': 0.04}
        ]
    },
    'WG': {
        'name': '윙어',
        'name_en': 'Winger',
        'attributes': [
            {'key': 'speed_dribbling', 'label': '스피드 드리블', 'weight': 0.12},
            {'key': 'one_on_one_beating', 'label': '1:1 제치기', 'weight': 0.11},
            {'key': 'speed', 'label': '스피드', 'weight': 0.10},
            {'key': 'acceleration', 'label': '가속력', 'weight': 0.09},
            {'key': 'crossing_accuracy', 'label': '크로스 정확도', 'weight': 0.10},
            {'key': 'shooting_accuracy', 'label': '슈팅 정확도', 'weight': 0.09},
            {'key': 'agility_direction_change', 'label': '민첩성 & 방향 전환', 'weight': 0.10},
            {'key': 'cutting_in', 'label': '컷인 무브', 'weight': 0.08},
            {'key': 'creativity', 'label': '창의성', 'weight': 0.06},
            {'key': 'defensive_contribution', 'label': '수비 가담 & 압박', 'weight': 0.07},
            {'key': 'cutback_pass', 'label': '컷백 패스', 'weight': 0.04},
            {'key': 'link_up_play', 'label': '연계 플레이', 'weight': 0.04}
        ]
    },
    'ST': {
        'name': '스트라이커',
        'name_en': 'Striker',
        'attributes': [
            {'key': 'finishing', 'label': '골 결정력', 'weight': 0.15},
            {'key': 'shot_power', 'label': '슈팅 정확도 & 파워', 'weight': 0.14},
            {'key': 'composure', 'label': '침착성', 'weight': 0.12},
            {'key': 'off_ball_movement', 'label': '오프더볼 무브먼트', 'weight': 0.13},
            {'key': 'hold_up_play', 'label': '홀딩 & 연결', 'weight': 0.11},
            {'key': 'heading', 'label': '헤딩 득점력', 'weight': 0.09},
            {'key': 'acceleration', 'label': '가속력', 'weight': 0.08},
            {'key': 'physicality_balance', 'label': '피지컬 & 밸런스', 'weight': 0.11},
            {'key': 'jumping', 'label': '점프력', 'weight': 0.07}
        ]
    }
}

# 기존 4개 포지션을 세부 포지션으로 매핑
POSITION_MAPPING = {
    'GK': ['GK'],
    'DF': ['CB', 'FB'],
    'MF': ['DM', 'CM', 'CAM'],
    'FW': ['WG', 'ST']
}

# 세부 포지션의 기본값 (선수의 일반 포지션에서)
DEFAULT_SUB_POSITION = {
    'GK': 'GK',
    'DF': 'CB',
    'MF': 'CM',
    'FW': 'ST'
}


def calculate_weighted_average(ratings, position):
    """
    가중 평균 계산

    Args:
        ratings (dict): {attribute_key: rating_value, ...}
        position (str): 세부 포지션 (GK, CB, FB, DM, CM, CAM, WG, ST)

    Returns:
        float|None: 가중 평균 값 (0.0-5.0) 또는 None
    """
    if not ratings or not position or position not in POSITION_ATTRIBUTES:
        return None

    attributes = POSITION_ATTRIBUTES[position]['attributes']
    total_weight = 0
    weighted_sum = 0

    for attr in attributes:
        rating_value = ratings.get(attr['key'])
        if isinstance(rating_value, (int, float)) and 0 <= rating_value <= 5:
            weighted_sum += rating_value * attr['weight']
            total_weight += attr['weight']

    if total_weight == 0:
        return None

    return weighted_sum / total_weight


def get_sub_position_from_general(general_position):
    """
    일반 포지션에서 기본 세부 포지션 가져오기

    Args:
        general_position (str): GK, DF, MF, FW

    Returns:
        str: 세부 포지션
    """
    return DEFAULT_SUB_POSITION.get(general_position, 'CM')
