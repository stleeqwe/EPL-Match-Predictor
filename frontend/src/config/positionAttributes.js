/**
 * 포지션별 능력치 설정 및 가중치
 * 각 포지션마다 고유한 능력치 항목과 가중치를 정의
 */

export const POSITION_ATTRIBUTES = {
  'GK': {
    name: '골키퍼',
    name_en: 'Goalkeeper',
    attributes: [
      { key: 'reflexes', label: '반응속도', weight: 0.17, description: '순간적인 슛에 대한 반사신경과 빠른 대응 능력' },
      { key: 'positioning', label: '포지셔닝', weight: 0.17, description: '골문을 지키기 위한 최적의 위치 선정 능력' },
      { key: 'handling', label: '핸들링', weight: 0.15, description: '볼을 안정적으로 캐치하고 잡아내는 기술' },
      { key: 'one_on_one', label: '1:1 대응', weight: 0.14, description: '공격수와의 일대일 상황에서 골을 막아내는 능력' },
      { key: 'aerial_control', label: '공중볼 지배력', weight: 0.12, description: '크로스나 높은 볼을 안전하게 처리하는 능력' },
      { key: 'buildup', label: '빌드업 능력', weight: 0.13, description: '발로 공격을 시작하는 패스 및 연결 플레이 능력' },
      { key: 'leadership_communication', label: '리더십&의사소통', weight: 0.07, description: '수비진을 지휘하고 조율하는 커뮤니케이션 능력' },
      { key: 'long_kick', label: '롱볼 킥력', weight: 0.05, description: '정확하고 먼 거리의 킥을 구사하는 능력' }
    ]
  },
  'CB': {
    name: '센터백',
    name_en: 'Center Back',
    attributes: [
      { key: 'positioning_reading', label: '포지셔닝 & 공간 읽기', weight: 0.15, description: '위험 상황을 미리 파악하고 적절한 위치를 선점하는 능력' },
      { key: 'composure_judgement', label: '침착성 & 판단력', weight: 0.12, description: '압박 상황에서도 냉정하게 최선의 선택을 하는 능력' },
      { key: 'interception', label: '인터셉트', weight: 0.10, description: '상대의 패스를 예측하고 가로채는 능력' },
      { key: 'aerial_duel', label: '공중볼 경합', weight: 0.09, description: '공중볼 상황에서 우위를 점하는 능력' },
      { key: 'tackle_marking', label: '태클 & 마킹', weight: 0.11, description: '공격수를 밀착 마크하고 정확한 태클로 볼을 뺏는 능력' },
      { key: 'speed', label: '스피드', weight: 0.10, description: '빠른 공격수를 따라잡을 수 있는 주력' },
      { key: 'passing', label: '패스 능력', weight: 0.13, description: '정확한 패스로 공격을 전개하는 능력' },
      { key: 'physical_jumping', label: '피지컬 & 점프력', weight: 0.08, description: '몸싸움과 높이 점프하는 신체 능력' },
      { key: 'buildup_contribution', label: '빌드업 기여도', weight: 0.10, description: '수비에서 공격으로 전환하는 플레이 참여도' },
      { key: 'leadership', label: '리더십', weight: 0.02, description: '수비라인을 이끌고 동료를 독려하는 능력' }
    ]
  },
  'FB': {
    name: '풀백',
    name_en: 'Fullback/Wingback',
    attributes: [
      { key: 'stamina', label: '지구력', weight: 0.16, description: '90분 내내 공수를 오가는 체력' },
      { key: 'speed', label: '스피드', weight: 0.15, description: '측면을 빠르게 장악하는 주력' },
      { key: 'defensive_positioning', label: '수비 포지셔닝', weight: 0.12, description: '수비 시 적절한 위치를 유지하는 능력' },
      { key: 'one_on_one_tackle', label: '1:1 수비 & 태클', weight: 0.13, description: '측면 공격수를 개인 대응하고 볼을 뺏는 능력' },
      { key: 'overlapping', label: '오버래핑', weight: 0.11, description: '윙어를 추월하며 공격 폭을 넓히는 플레이' },
      { key: 'crossing_accuracy', label: '크로스 정확도', weight: 0.11, description: '정확한 크로스로 득점 찬스를 만드는 능력' },
      { key: 'covering', label: '백업 커버링', weight: 0.09, description: '동료 수비수를 지원하고 공간을 메우는 능력' },
      { key: 'agility', label: '민첩성', weight: 0.07, description: '빠른 방향 전환과 몸놀림' },
      { key: 'press_resistance', label: '압박 저항력', weight: 0.04, description: '압박 속에서도 안정적으로 볼을 지키는 능력' },
      { key: 'long_shot', label: '중거리 슈팅', weight: 0.02, description: '골문 밖에서 슈팅으로 위협하는 능력' }
    ]
  },
  'DM': {
    name: '수비형 미드필더',
    name_en: 'Defensive Midfielder',
    attributes: [
      { key: 'positioning', label: '포지셔닝', weight: 0.12, description: '수비진 앞에서 위험 지역을 선점하는 능력' },
      { key: 'ball_winning', label: '볼 차단 & 회수', weight: 0.12, description: '상대의 공격을 차단하고 볼을 되찾는 능력' },
      { key: 'pass_accuracy', label: '패스 정확도', weight: 0.10, description: '안정적이고 정확한 패스 능력' },
      { key: 'composure_press_resistance', label: '침착성 & 압박 해소', weight: 0.12, description: '압박 속에서도 침착하게 볼을 처리하는 능력' },
      { key: 'backline_protection', label: '백라인 보호', weight: 0.10, description: '수비수들 앞에서 방패 역할을 하는 능력' },
      { key: 'pressing_transition_blocking', label: '공간 압박 & 전환 차단', weight: 0.10, description: '상대의 역습 전환을 막고 압박하는 능력' },
      { key: 'progressive_play', label: '공격 전개', weight: 0.09, description: '수비에서 공격으로 연결하는 플레이 능력' },
      { key: 'tempo_control', label: '템포 조절', weight: 0.07, description: '경기 흐름을 읽고 템포를 조절하는 능력' },
      { key: 'stamina', label: '지구력', weight: 0.06, description: '중원을 넓게 커버할 수 있는 체력' },
      { key: 'physicality_mobility', label: '피지컬 & 기동력', weight: 0.10, description: '몸싸움과 넓은 범위를 움직이는 능력' },
      { key: 'leadership', label: '리더십', weight: 0.02, description: '팀을 조율하고 이끄는 능력' }
    ]
  },
  'CM': {
    name: '중앙 미드필더',
    name_en: 'Central Midfielder',
    attributes: [
      { key: 'stamina', label: '지구력', weight: 0.11, description: '공수를 오가며 중원을 지배하는 체력' },
      { key: 'ball_possession_circulation', label: '볼 소유 & 순환', weight: 0.11, description: '볼을 안정적으로 소유하고 순환시키는 능력' },
      { key: 'pass_accuracy_vision', label: '패스 정확도 & 시야', weight: 0.13, description: '넓은 시야로 정확한 패스를 연결하는 능력' },
      { key: 'transition', label: '전환 플레이', weight: 0.10, description: '수비에서 공격, 공격에서 수비로 빠르게 전환하는 능력' },
      { key: 'dribbling_press_resistance', label: '드리블 & 탈압박', weight: 0.10, description: '드리블로 압박을 벗어나는 능력' },
      { key: 'space_creation', label: '공간 창출/침투', weight: 0.09, description: '움직임으로 공간을 만들고 침투하는 능력' },
      { key: 'defensive_contribution', label: '수비 가담', weight: 0.09, description: '수비에 적극적으로 참여하는 능력' },
      { key: 'ball_retention', label: '볼 키핑', weight: 0.07, description: '압박 속에서 볼을 지켜내는 능력' },
      { key: 'long_shot', label: '중거리 슈팅', weight: 0.06, description: '중거리에서 골을 노리는 슈팅 능력' },
      { key: 'agility_acceleration', label: '민첩성 & 가속력', weight: 0.09, description: '빠른 움직임과 순간 가속 능력' },
      { key: 'physicality', label: '피지컬', weight: 0.05, description: '중원에서의 몸싸움 능력' }
    ]
  },
  'CAM': {
    name: '공격형 미드필더',
    name_en: 'Attacking Midfielder',
    attributes: [
      { key: 'creativity', label: '창의성', weight: 0.13, description: '예측 불가능한 플레이로 수비를 무너뜨리는 능력' },
      { key: 'vision_killpass', label: '시야 & 킬패스', weight: 0.12, description: '수비 뒷공간을 꿰뚫는 결정적 패스 능력' },
      { key: 'dribbling', label: '드리블 돌파', weight: 0.11, description: '좁은 공간에서 수비수를 제치는 드리블 능력' },
      { key: 'decision_making', label: '결정적 순간 판단', weight: 0.11, description: '득점 찬스에서 최선의 선택을 하는 능력' },
      { key: 'penetration', label: '공간 침투', weight: 0.10, description: '수비 뒷공간으로 침투하는 움직임' },
      { key: 'shooting_finishing', label: '슈팅 & 마무리', weight: 0.11, description: '직접 골을 넣는 슈팅과 마무리 능력' },
      { key: 'one_touch_pass', label: '원터치 패스', weight: 0.08, description: '빠른 원터치로 연결하는 패스 능력' },
      { key: 'pass_and_move', label: '패스 & 무브', weight: 0.07, description: '패스 후 공간으로 이동하는 플레이' },
      { key: 'acceleration', label: '가속력', weight: 0.07, description: '순간적인 스피드를 내는 능력' },
      { key: 'agility', label: '민첩성', weight: 0.06, description: '좁은 공간에서의 빠른 몸놀림' },
      { key: 'set_piece', label: '세트피스', weight: 0.04, description: '프리킥과 코너킥 키커 능력' }
    ]
  },
  'WG': {
    name: '윙어',
    name_en: 'Winger',
    attributes: [
      { key: 'speed_dribbling', label: '스피드 드리블', weight: 0.12, description: '빠른 속도로 측면을 돌파하는 드리블 능력' },
      { key: 'one_on_one_beating', label: '1:1 제치기', weight: 0.11, description: '수비수를 일대일로 제치는 능력' },
      { key: 'speed', label: '스피드', weight: 0.10, description: '최고 속도로 질주하는 능력' },
      { key: 'acceleration', label: '가속력', weight: 0.09, description: '순간적으로 속도를 내는 능력' },
      { key: 'crossing_accuracy', label: '크로스 정확도', weight: 0.10, description: '박스 안으로 정확한 크로스를 넣는 능력' },
      { key: 'shooting_accuracy', label: '슈팅 정확도', weight: 0.09, description: '골문을 정확하게 노리는 슈팅 능력' },
      { key: 'agility_direction_change', label: '민첩성 & 방향 전환', weight: 0.10, description: '빠르게 방향을 바꾸는 민첩성' },
      { key: 'cutting_in', label: '컷인 무브', weight: 0.08, description: '측면에서 중앙으로 파고드는 움직임' },
      { key: 'creativity', label: '창의성', weight: 0.06, description: '독창적인 플레이로 찬스를 만드는 능력' },
      { key: 'defensive_contribution', label: '수비 가담 & 압박', weight: 0.07, description: '수비 시 압박과 가담 능력' },
      { key: 'cutback_pass', label: '컷백 패스', weight: 0.04, description: '골문 앞으로 되돌리는 패스 능력' },
      { key: 'link_up_play', label: '연계 플레이', weight: 0.04, description: '동료와의 호흡을 맞추는 연계 능력' }
    ]
  },
  'ST': {
    name: '스트라이커',
    name_en: 'Striker',
    attributes: [
      { key: 'finishing', label: '골 결정력', weight: 0.15, description: '결정적 찬스를 골로 연결하는 마무리 능력' },
      { key: 'shot_power', label: '슈팅 정확도 & 파워', weight: 0.14, description: '정확하고 강력한 슈팅을 구사하는 능력' },
      { key: 'composure', label: '침착성', weight: 0.12, description: '골 앞에서 침착하게 마무리하는 능력' },
      { key: 'off_ball_movement', label: '오프더볼 무브먼트', weight: 0.13, description: '볼 없이 공간을 찾아 움직이는 능력' },
      { key: 'hold_up_play', label: '홀딩 & 연결', weight: 0.11, description: '볼을 지키고 동료와 연결하는 포스트 플레이' },
      { key: 'heading', label: '헤딩 득점력', weight: 0.09, description: '공중볼을 헤딩으로 골로 연결하는 능력' },
      { key: 'acceleration', label: '가속력', weight: 0.08, description: '수비 뒷공간으로 빠르게 침투하는 순발력' },
      { key: 'physicality_balance', label: '피지컬 & 밸런스', weight: 0.11, description: '수비수와의 몸싸움과 균형 유지 능력' },
      { key: 'jumping', label: '점프력', weight: 0.07, description: '높이 점프하여 공중볼을 경합하는 능력' }
    ]
  }
};

/**
 * 기존 4개 포지션을 세부 포지션으로 매핑
 */
export const POSITION_MAPPING = {
  'GK': ['GK'],
  'DF': ['CB', 'FB'],
  'MF': ['DM', 'CM', 'CAM'],
  'FW': ['WG', 'ST']
};

/**
 * 세부 포지션의 기본값 (선수의 일반 포지션에서)
 */
export const DEFAULT_SUB_POSITION = {
  'GK': 'GK',
  'DF': 'CB',
  'MF': 'CM',
  'FW': 'ST'
};

/**
 * 가중 평균 계산
 * @param {Object} ratings - { attribute_key: rating_value, ... }
 * @param {String} position - 세부 포지션 (GK, CB, FB, DM, CM, CAM, WG, ST)
 * @returns {Number|null} - 가중 평균 값 (0.0-5.0) 또는 null
 */
export const calculateWeightedAverage = (ratings, position) => {
  if (!ratings || !position || !POSITION_ATTRIBUTES[position]) {
    return null;
  }

  const attributes = POSITION_ATTRIBUTES[position].attributes;
  let totalWeight = 0;
  let weightedSum = 0;

  attributes.forEach(attr => {
    const ratingValue = ratings[attr.key];
    if (typeof ratingValue === 'number' && ratingValue >= 0 && ratingValue <= 5) {
      weightedSum += ratingValue * attr.weight;
      totalWeight += attr.weight;
    }
  });

  if (totalWeight === 0) return null;

  return weightedSum / totalWeight;
};

/**
 * 모든 포지션 목록 가져오기
 */
export const getAllPositions = () => {
  return Object.keys(POSITION_ATTRIBUTES);
};

/**
 * 일반 포지션에서 사용 가능한 세부 포지션 목록
 */
export const getSubPositions = (generalPosition) => {
  // 이미 세부 포지션인 경우
  if (POSITION_ATTRIBUTES[generalPosition]) {
    // 해당 세부 포지션이 속한 일반 포지션 찾기
    for (const [, subs] of Object.entries(POSITION_MAPPING)) {
      if (subs.includes(generalPosition)) {
        return subs;
      }
    }
    return [generalPosition]; // 매핑을 못 찾으면 자기 자신만 반환
  }

  // 일반 포지션인 경우
  return POSITION_MAPPING[generalPosition] || [];
};
