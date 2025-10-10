/**
 * Squad Builder Utilities
 * 스쿼드 빌더 전용 헬퍼 함수 모음
 */

/**
 * 포지션 호환성 체크
 * @param {string} playerPosition - 선수 포지션 (GK, CB, FB, etc.)
 * @param {string} targetRole - 목표 역할
 * @returns {boolean} 호환 여부
 */
export const isPositionCompatible = (playerPosition, targetRole) => {
  const compatibility = {
    GK: ['GK'],
    CB: ['CB'],
    FB: ['FB', 'WG'], // 풀백은 윙어 역할 가능
    DM: ['DM', 'CM'], // 수비형 미드필더는 중앙 미드필더 가능
    CM: ['CM', 'DM', 'CAM'], // 중앙 미드필더는 유연함
    CAM: ['CAM', 'CM', 'WG'], // 공격형 미드필더는 측면 가능
    WG: ['WG', 'ST', 'CAM'], // 윙어는 공격수/CAM 가능
    ST: ['ST', 'WG'] // 스트라이커는 윙어 가능
  };

  return compatibility[playerPosition]?.includes(targetRole) || false;
};

/**
 * 선수 평점 계산 (고급 알고리즘)
 * @param {object} player - 선수 객체
 * @returns {number} 평점 (0-5)
 */
export const calculateAdvancedRating = (player) => {
  const {
    is_starter = false,
    age = 25,
    goals = 0,
    assists = 0,
    minutes = 0,
    appearances = 0,
    position
  } = player;

  let baseRating = 3.0;

  // 1. 주전 여부 (+0.5)
  if (is_starter) baseRating += 0.5;

  // 2. 나이 곡선 (피크: 26-29세)
  if (age >= 26 && age <= 29) {
    baseRating += 0.4;
  } else if (age >= 23 && age <= 25) {
    baseRating += 0.25;
  } else if (age >= 30 && age <= 32) {
    baseRating += 0.2;
  } else if (age >= 20 && age <= 22) {
    baseRating += 0.1;
  }

  // 3. 포지션별 통계 가중치
  const positionWeights = {
    ST: { goals: 0.15, assists: 0.08 },
    WG: { goals: 0.12, assists: 0.12 },
    CAM: { goals: 0.10, assists: 0.15 },
    CM: { goals: 0.08, assists: 0.10 },
    DM: { goals: 0.05, assists: 0.08 },
    FB: { goals: 0.08, assists: 0.10 },
    CB: { goals: 0.05, assists: 0.03 },
    GK: { goals: 0.00, assists: 0.00 }
  };

  const weights = positionWeights[position] || { goals: 0.05, assists: 0.05 };
  baseRating += goals * weights.goals;
  baseRating += assists * weights.assists;

  // 4. 출전 시간 보너스
  if (minutes > 1500) baseRating += 0.3;
  else if (minutes > 1000) baseRating += 0.2;
  else if (minutes > 500) baseRating += 0.1;

  // 5. 경기당 기여도
  if (appearances > 0) {
    const contributionPerGame = (goals + assists) / appearances;
    if (contributionPerGame > 1.0) baseRating += 0.25;
    else if (contributionPerGame > 0.5) baseRating += 0.15;
  }

  return Math.min(5.0, Math.max(0.0, baseRating));
};

/**
 * 선수 폼 계산 (최근 컨디션)
 * @param {object} player - 선수 객체
 * @returns {number} 폼 (0-5)
 */
export const calculatePlayerForm = (player) => {
  const {
    goals = 0,
    assists = 0,
    minutes = 0,
    appearances = 0,
    is_starter = false
  } = player;

  let form = 3.5;

  // 최근 출전 시간 기반
  if (minutes > 800) form += 0.5;
  else if (minutes > 500) form += 0.3;
  else if (minutes < 200) form -= 0.5;

  // 최근 기여도
  const recentContribution = (goals + assists) * 0.2;
  form += recentContribution;

  // 주전 여부
  if (is_starter) form += 0.2;

  return Math.min(5.0, Math.max(0.0, form));
};

/**
 * 팀 케미스트리 계산
 * @param {array} starters - 선발 선수 배열
 * @returns {number} 케미스트리 (0-5)
 */
export const calculateTeamChemistry = (starters) => {
  if (!starters || starters.length === 0) return 0;

  let chemistry = 3.0;

  // 1. 평균 폼
  const avgForm = starters.reduce((sum, p) => sum + (p.form || 3.5), 0) / starters.length;
  chemistry += (avgForm - 3.5) * 0.5;

  // 2. 나이 분포 (이상적: 23-32세 골고루)
  const ageGroups = {
    young: starters.filter(p => p.age < 23).length,
    prime: starters.filter(p => p.age >= 23 && p.age <= 29).length,
    veteran: starters.filter(p => p.age >= 30).length
  };

  if (ageGroups.prime >= 6) chemistry += 0.3;
  if (ageGroups.young >= 2 && ageGroups.young <= 4) chemistry += 0.2;
  if (ageGroups.veteran >= 2 && ageGroups.veteran <= 4) chemistry += 0.2;

  // 3. 주전 선수 비율 (높을수록 좋음)
  const startersCount = starters.filter(p => p.is_starter).length;
  const starterRatio = startersCount / starters.length;
  chemistry += starterRatio * 0.5;

  return Math.min(5.0, Math.max(0.0, chemistry));
};

/**
 * 포메이션 밸런스 분석
 * @param {object} formation - 포메이션 객체
 * @param {array} starters - 선발 선수 배열
 * @returns {object} 밸런스 분석 결과
 */
export const analyzeFormationBalance = (formation, starters) => {
  const positionCounts = {
    GK: 0,
    DF: 0, // CB + FB
    MF: 0, // DM + CM + CAM
    FW: 0  // WG + ST
  };

  starters.forEach(player => {
    if (player.position === 'GK') positionCounts.GK++;
    else if (['CB', 'FB'].includes(player.position)) positionCounts.DF++;
    else if (['DM', 'CM', 'CAM'].includes(player.position)) positionCounts.MF++;
    else if (['WG', 'ST'].includes(player.position)) positionCounts.FW++;
  });

  const total = positionCounts.DF + positionCounts.MF + positionCounts.FW;

  return {
    defensive: total > 0 ? (positionCounts.DF / total) * 100 : 0,
    midfield: total > 0 ? (positionCounts.MF / total) * 100 : 0,
    attacking: total > 0 ? (positionCounts.FW / total) * 100 : 0,
    isBalanced: Math.abs(positionCounts.DF - positionCounts.FW) <= 2,
    style: positionCounts.FW > positionCounts.DF + 1 ? 'attacking' : 
           positionCounts.DF > positionCounts.FW + 1 ? 'defensive' : 'balanced'
  };
};

/**
 * 스쿼드 검증
 * @param {object} squad - 스쿼드 객체
 * @param {object} formation - 포메이션 객체
 * @returns {object} 검증 결과
 */
export const validateSquad = (squad, formation) => {
  const errors = [];
  const warnings = [];

  // 1. 필수 포지션 체크
  const requiredPositions = Object.keys(formation.positions);
  const filledPositions = Object.keys(squad.starters);

  const missingPositions = requiredPositions.filter(
    pos => !filledPositions.includes(pos)
  );

  if (missingPositions.length > 0) {
    errors.push(`빈 포지션: ${missingPositions.join(', ')}`);
  }

  // 2. 골키퍼 체크
  const gkCount = Object.entries(squad.starters).filter(([key, _]) => 
    key.startsWith('GK')
  ).length;

  if (gkCount === 0) {
    errors.push('골키퍼가 배치되지 않았습니다');
  } else if (gkCount > 1) {
    errors.push('골키퍼는 1명만 배치 가능합니다');
  }

  // 3. 후보 선수 수 체크
  if (squad.substitutes.length > 7) {
    errors.push('후보 선수는 최대 7명입니다');
  }

  if (squad.substitutes.length < 3) {
    warnings.push('최소 3명의 후보 선수를 배치하세요');
  }

  // 4. 총 선수 수 체크
  const totalPlayers = filledPositions.length + squad.substitutes.length;
  if (totalPlayers < 14) {
    warnings.push('풀 스쿼드는 최소 14명 권장');
  }

  return {
    isValid: errors.length === 0,
    errors,
    warnings
  };
};

/**
 * 스쿼드 익스포트 (JSON)
 * @param {object} squad - 스쿼드 객체
 * @param {string} formation - 포메이션 이름
 * @param {string} teamName - 팀 이름
 * @returns {string} JSON 문자열
 */
export const exportSquad = (squad, formation, teamName) => {
  const exportData = {
    version: '2.0',
    team: teamName,
    formation,
    squad,
    exportedAt: new Date().toISOString(),
    metadata: {
      totalPlayers: Object.keys(squad.starters).length + squad.substitutes.length,
      hasFullLineup: Object.keys(squad.starters).length === 11
    }
  };

  return JSON.stringify(exportData, null, 2);
};

/**
 * 스쿼드 임포트 (JSON)
 * @param {string} jsonString - JSON 문자열
 * @returns {object|null} 스쿼드 객체 또는 null (실패 시)
 */
export const importSquad = (jsonString) => {
  try {
    const data = JSON.parse(jsonString);
    
    // 버전 체크
    if (data.version !== '2.0') {
      console.warn('이전 버전의 스쿼드 데이터입니다');
    }

    // 필수 필드 검증
    if (!data.squad || !data.formation) {
      throw new Error('Invalid squad data');
    }

    return {
      squad: data.squad,
      formation: data.formation,
      team: data.team
    };
  } catch (error) {
    console.error('Failed to import squad:', error);
    return null;
  }
};

/**
 * 포지션 좌표 계산 (커스텀 포메이션용)
 * @param {string} role - 역할 (GK, CB, etc.)
 * @param {number} index - 해당 역할 내 인덱스
 * @param {number} totalInRole - 해당 역할 총 인원
 * @returns {object} {x, y} 좌표
 */
export const calculatePositionCoordinates = (role, index, totalInRole) => {
  const yPositions = {
    GK: 90,
    CB: 75,
    FB: 68,
    DM: 55,
    CM: 45,
    CAM: 30,
    WG: 15,
    ST: 10
  };

  const y = yPositions[role] || 50;

  // X 좌표는 균등 분배
  if (totalInRole === 1) {
    return { x: 50, y };
  } else if (totalInRole === 2) {
    return { x: index === 0 ? 35 : 65, y };
  } else if (totalInRole === 3) {
    return { x: index === 0 ? 25 : index === 1 ? 50 : 75, y };
  } else if (totalInRole === 4) {
    return { x: 15 + (index * 23.3), y };
  } else {
    // 5명 이상
    const spacing = 80 / (totalInRole + 1);
    return { x: 10 + spacing * (index + 1), y };
  }
};

/**
 * 포메이션 추천 (팀 구성에 맞춰)
 * @param {array} players - 선수 배열
 * @returns {string} 추천 포메이션
 */
export const recommendFormation = (players) => {
  const positionCounts = {
    GK: players.filter(p => p.position === 'GK').length,
    CB: players.filter(p => p.position === 'CB').length,
    FB: players.filter(p => p.position === 'FB').length,
    DM: players.filter(p => p.position === 'DM').length,
    CM: players.filter(p => p.position === 'CM').length,
    CAM: players.filter(p => p.position === 'CAM').length,
    WG: players.filter(p => p.position === 'WG').length,
    ST: players.filter(p => p.position === 'ST').length
  };

  // 공격수가 많으면
  if (positionCounts.ST >= 3) return '4-4-2';
  
  // 윙어가 많으면
  if (positionCounts.WG >= 4) return '4-3-3';
  
  // CAM이 많으면
  if (positionCounts.CAM >= 3) return '4-2-3-1';
  
  // 중앙 미드필더가 많으면
  if (positionCounts.CM >= 5) return '3-5-2';
  
  // 센터백이 많으면
  if (positionCounts.CB >= 5) return '3-4-3';
  
  // 기본값
  return '4-3-3';
};

/**
 * 로컬 스토리지 헬퍼
 */
export const squadStorage = {
  save: (teamName, squadData) => {
    const key = `squad_${teamName}`;
    localStorage.setItem(key, JSON.stringify(squadData));
  },
  
  load: (teamName) => {
    const key = `squad_${teamName}`;
    const data = localStorage.getItem(key);
    return data ? JSON.parse(data) : null;
  },
  
  delete: (teamName) => {
    const key = `squad_${teamName}`;
    localStorage.removeItem(key);
  },
  
  list: () => {
    const keys = Object.keys(localStorage).filter(k => k.startsWith('squad_'));
    return keys.map(k => k.replace('squad_', ''));
  }
};

/**
 * 디버그 헬퍼
 */
export const debugSquad = (squad, players) => {
  console.group('🔍 Squad Debug Info');
  
  console.log('Total Starters:', Object.keys(squad.starters).length);
  console.log('Total Substitutes:', squad.substitutes.length);
  
  const starterPlayers = Object.values(squad.starters)
    .map(id => players.find(p => p.id === id))
    .filter(Boolean);
  
  console.log('Starter Positions:', 
    starterPlayers.map(p => `${p.name} (${p.position})`).join(', ')
  );
  
  console.log('Average Rating:', 
    (starterPlayers.reduce((sum, p) => sum + p.rating, 0) / starterPlayers.length).toFixed(2)
  );
  
  console.groupEnd();
};

export default {
  isPositionCompatible,
  calculateAdvancedRating,
  calculatePlayerForm,
  calculateTeamChemistry,
  analyzeFormationBalance,
  validateSquad,
  exportSquad,
  importSquad,
  calculatePositionCoordinates,
  recommendFormation,
  squadStorage,
  debugSquad
};
