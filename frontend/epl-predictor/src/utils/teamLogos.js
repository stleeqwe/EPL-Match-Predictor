/**
 * EPL Team Logos Utility
 * 프리미어리그 팀 엠블럼 매핑 시스템
 */

// EPL 팀별 코드 매핑 (FPL API team code)
// 현재 및 과거 시즌 팀들 포함
const TEAM_CODES = {
  // 현재 시즌 주요 팀들
  'Arsenal': 3,
  'Aston Villa': 7,
  'Bournemouth': 91,
  'AFC Bournemouth': 91,
  'Brentford': 94,
  'Brighton': 36,
  'Brighton and Hove Albion': 36,
  'Burnley': 90,
  'Chelsea': 8,
  'Crystal Palace': 31,
  'Everton': 11,
  'Fulham': 54,
  'Ipswich': 40,
  'Ipswich Town': 40,
  'Leicester': 13,
  'Leicester City': 13,
  'Leeds': 2,
  'Leeds United': 2,
  'Liverpool': 14,
  'Man City': 43,
  'Manchester City': 43,
  'Man Utd': 1,
  'Manchester United': 1,
  'Newcastle': 4,
  'Newcastle United': 4,
  'Nott\'m Forest': 17,
  'Nottingham Forest': 17,
  'Southampton': 20,
  'Spurs': 6,
  'Tottenham': 6,
  'Tottenham Hotspur': 6,
  'Sunderland': 56,
  'Sunderland AFC': 56,
  'West Ham': 21,
  'West Ham United': 21,
  'Wolves': 39,
  'Wolverhampton Wanderers': 39,

  // 과거 시즌 팀들
  'Watford': 57,
  'Norwich': 45,
  'Norwich City': 45,
  'Sheffield United': 49,
  'Sheffield Utd': 49,
  'West Brom': 35,
  'West Bromwich Albion': 35,
  'Luton': 163,
  'Luton Town': 163,
  'Middlesbrough': 25,
  'Stoke': 110,
  'Stoke City': 110,
  'Swansea': 80,
  'Swansea City': 80,
  'Hull': 88,
  'Hull City': 88,
  'Cardiff': 97,
  'Cardiff City': 97,
  'Huddersfield': 38,
  'Huddersfield Town': 38,
  'Burnley FC': 90
};

/**
 * 팀 이름으로 엠블럼 URL 가져오기
 * @param {string} teamName - 팀 이름
 * @param {string} size - 'small' | 'medium' | 'large'
 * @returns {string} 엠블럼 URL
 */
export const getTeamLogo = (teamName, size = 'medium') => {
  const code = TEAM_CODES[teamName];

  if (!code) {
    console.warn(`팀 코드를 찾을 수 없습니다: ${teamName}`);
    return null;
  }

  // 사이즈별 URL 생성
  const sizeMap = {
    'small': '',        // 기본 사이즈
    'medium': '@x2',    // 2배 크기
    'large': '@x3'      // 3배 크기 (존재하지 않을 수 있음)
  };

  const sizeParam = sizeMap[size] || sizeMap.medium;

  return `https://resources.premierleague.com/premierleague/badges/t${code}${sizeParam}.png`;
};

/**
 * 팀 색상 가져오기 (브랜드 컬러)
 * @param {string} teamName - 팀 이름
 * @returns {Object} { primary, secondary }
 */
export const getTeamColors = (teamName) => {
  const colors = {
    'Arsenal': { primary: '#EF0107', secondary: '#FFFFFF' },
    'Aston Villa': { primary: '#95BFE5', secondary: '#670E36' },
    'Bournemouth': { primary: '#DA291C', secondary: '#000000' },
    'Brentford': { primary: '#D20000', secondary: '#FBB800' },
    'Brighton': { primary: '#0057B8', secondary: '#FFCD00' },
    'Burnley': { primary: '#6C1D45', secondary: '#99D6EA' },
    'Chelsea': { primary: '#034694', secondary: '#FFFFFF' },
    'Crystal Palace': { primary: '#1B458F', secondary: '#C4122E' },
    'Everton': { primary: '#003399', secondary: '#FFFFFF' },
    'Fulham': { primary: '#000000', secondary: '#FFFFFF' },
    'Ipswich': { primary: '#0000FF', secondary: '#FFFFFF' },
    'Leicester': { primary: '#003090', secondary: '#FDBE11' },
    'Leeds': { primary: '#FFCD00', secondary: '#1D428A' },
    'Liverpool': { primary: '#C8102E', secondary: '#00B2A9' },
    'Man City': { primary: '#6CABDD', secondary: '#1C2C5B' },
    'Man Utd': { primary: '#DA291C', secondary: '#FBE122' },
    'Newcastle': { primary: '#241F20', secondary: '#FFFFFF' },
    'Nott\'m Forest': { primary: '#DD0000', secondary: '#FFFFFF' },
    'Southampton': { primary: '#D71920', secondary: '#130C0E' },
    'Spurs': { primary: '#132257', secondary: '#FFFFFF' },
    'Sunderland': { primary: '#EB172B', secondary: '#211E1F' },
    'West Ham': { primary: '#7A263A', secondary: '#1BB1E7' },
    'Wolves': { primary: '#FDB913', secondary: '#231F20' },
    // 과거 팀들
    'Watford': { primary: '#FBEE23', secondary: '#ED2127' },
    'Norwich': { primary: '#00A650', secondary: '#FFF200' },
    'Sheffield United': { primary: '#EE2737', secondary: '#000000' },
    'West Brom': { primary: '#122F67', secondary: '#FFFFFF' },
    'Luton': { primary: '#F78F1E', secondary: '#002D62' },
    'Middlesbrough': { primary: '#D6001C', secondary: '#FFFFFF' },
    'Stoke': { primary: '#E03A3E', secondary: '#1B449C' },
    'Swansea': { primary: '#000000', secondary: '#FFFFFF' },
    'Hull': { primary: '#F5A12D', secondary: '#000000' },
    'Cardiff': { primary: '#0070B5', secondary: '#D51007' },
    'Huddersfield': { primary: '#0E63AD', secondary: '#FFFFFF' }
  };

  // 별칭 처리
  const normalizedName = teamName.replace('Manchester City', 'Man City')
                                 .replace('Manchester United', 'Man Utd')
                                 .replace('Tottenham Hotspur', 'Spurs')
                                 .replace('Tottenham', 'Spurs')
                                 .replace('Nottingham Forest', 'Nott\'m Forest')
                                 .replace('West Ham United', 'West Ham')
                                 .replace('Wolverhampton Wanderers', 'Wolves')
                                 .replace('Burnley FC', 'Burnley')
                                 .replace('Leeds United', 'Leeds')
                                 .replace('Leicester City', 'Leicester')
                                 .replace('Ipswich Town', 'Ipswich')
                                 .replace('Brighton and Hove Albion', 'Brighton')
                                 .replace('Newcastle United', 'Newcastle')
                                 .replace('Sunderland AFC', 'Sunderland')
                                 .replace('Norwich City', 'Norwich')
                                 .replace('Sheffield Utd', 'Sheffield United')
                                 .replace('West Bromwich Albion', 'West Brom')
                                 .replace('Luton Town', 'Luton')
                                 .replace('Stoke City', 'Stoke')
                                 .replace('Swansea City', 'Swansea')
                                 .replace('Hull City', 'Hull')
                                 .replace('Cardiff City', 'Cardiff')
                                 .replace('Huddersfield Town', 'Huddersfield');

  return colors[normalizedName] || { primary: '#38003c', secondary: '#00ff85' };
};

/**
 * 팀 약칭 가져오기
 * @param {string} teamName - 팀 이름
 * @returns {string} 3글자 약칭
 */
export const getTeamShortName = (teamName) => {
  const shortNames = {
    'Arsenal': 'ARS',
    'Aston Villa': 'AVL',
    'Bournemouth': 'BOU',
    'Brentford': 'BRE',
    'Brighton': 'BHA',
    'Burnley': 'BUR',
    'Chelsea': 'CHE',
    'Crystal Palace': 'CRY',
    'Everton': 'EVE',
    'Fulham': 'FUL',
    'Ipswich': 'IPS',
    'Leicester': 'LEI',
    'Leeds': 'LEE',
    'Liverpool': 'LIV',
    'Man City': 'MCI',
    'Man Utd': 'MUN',
    'Newcastle': 'NEW',
    'Nott\'m Forest': 'NFO',
    'Southampton': 'SOU',
    'Spurs': 'TOT',
    'Sunderland': 'SUN',
    'West Ham': 'WHU',
    'Wolves': 'WOL',
    // 과거 팀들
    'Watford': 'WAT',
    'Norwich': 'NOR',
    'Sheffield United': 'SHU',
    'West Brom': 'WBA',
    'Luton': 'LUT',
    'Middlesbrough': 'MID',
    'Stoke': 'STK',
    'Swansea': 'SWA',
    'Hull': 'HUL',
    'Cardiff': 'CAR',
    'Huddersfield': 'HUD'
  };

  // 별칭 처리
  const normalizedName = teamName.replace('Manchester City', 'Man City')
                                 .replace('Manchester United', 'Man Utd')
                                 .replace('Tottenham Hotspur', 'Spurs')
                                 .replace('Tottenham', 'Spurs')
                                 .replace('Nottingham Forest', 'Nott\'m Forest')
                                 .replace('West Ham United', 'West Ham')
                                 .replace('Wolverhampton Wanderers', 'Wolves')
                                 .replace('Burnley FC', 'Burnley')
                                 .replace('Leeds United', 'Leeds')
                                 .replace('Leicester City', 'Leicester')
                                 .replace('Ipswich Town', 'Ipswich')
                                 .replace('Brighton and Hove Albion', 'Brighton')
                                 .replace('Newcastle United', 'Newcastle')
                                 .replace('Sunderland AFC', 'Sunderland')
                                 .replace('Norwich City', 'Norwich')
                                 .replace('Sheffield Utd', 'Sheffield United')
                                 .replace('West Bromwich Albion', 'West Brom')
                                 .replace('Luton Town', 'Luton')
                                 .replace('Stoke City', 'Stoke')
                                 .replace('Swansea City', 'Swansea')
                                 .replace('Hull City', 'Hull')
                                 .replace('Cardiff City', 'Cardiff')
                                 .replace('Huddersfield Town', 'Huddersfield');

  return shortNames[normalizedName] || 'UNK';
};

/**
 * 선수 프로필 사진 URL 가져오기
 * @param {number} playerCode - 선수 코드 (FPL API의 code 필드)
 * @param {string} size - 'small' | 'medium' | 'large'
 * @returns {string} 선수 사진 URL
 */
export const getPlayerPhoto = (playerCode, size = 'medium') => {
  if (!playerCode) {
    return null;
  }

  // 사이즈별 해상도
  const sizeMap = {
    'small': '110x140',
    'medium': '250x250',
    'large': '470x470'
  };

  const resolution = sizeMap[size] || sizeMap.medium;

  return `https://resources.premierleague.com/premierleague/photos/players/${resolution}/p${playerCode}.png`;
};

const teamLogos = {
  getTeamLogo,
  getTeamColors,
  getTeamShortName,
  getPlayerPhoto
};

export default teamLogos;
