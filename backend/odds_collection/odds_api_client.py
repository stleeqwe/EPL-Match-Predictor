"""
The Odds API Client
공식 API: https://the-odds-api.com/

무료 티어:
- 월 500 requests
- 실시간 배당률 데이터
- 주요 북메이커: Bet365, Pinnacle, Betfair, William Hill 등
"""

import requests
import os
from typing import Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class OddsAPIClient:
    """The Odds API 클라이언트"""
    
    BASE_URL = "https://api.the-odds-api.com/v4"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Args:
            api_key: The Odds API 키 (환경 변수 ODDS_API_KEY에서 자동 로드)
        """
        self.api_key = api_key or os.getenv('ODDS_API_KEY')
        if not self.api_key:
            logger.warning("ODDS_API_KEY not found. Using demo mode.")
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Soccer-Predictor/1.0'
        })
    
    def get_sports(self) -> List[Dict]:
        """
        사용 가능한 스포츠 목록
        
        Returns:
            List[Dict]: 스포츠 정보
        """
        endpoint = f"{self.BASE_URL}/sports"
        params = {'apiKey': self.api_key}
        
        try:
            response = self.session.get(endpoint, params=params, timeout=10)
            response.raise_for_status()
            
            sports = response.json()
            logger.info(f"Fetched {len(sports)} sports")
            return sports
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch sports: {e}")
            return []
    
    def get_epl_odds(
        self,
        regions: str = 'us,uk,eu',  # US for totals, UK/EU for all major bookmakers including Pinnacle
        markets: str = 'h2h,totals',
        oddsFormat: str = 'decimal'
    ) -> List[Dict]:
        """
        EPL 배당률 가져오기
        
        Args:
            regions: 지역 (uk, us, eu, au)
            markets: 마켓 타입 (h2h=승무패, spreads=핸디캡, totals=오버언더)
            oddsFormat: 배당률 형식 (decimal, american)
        
        Returns:
            List[Dict]: 경기별 배당률 데이터
            
        Example:
            [
                {
                    'id': 'abc123',
                    'sport_key': 'soccer_epl',
                    'commence_time': '2025-10-05T14:00:00Z',
                    'home_team': 'Manchester City',
                    'away_team': 'Liverpool',
                    'bookmakers': [
                        {
                            'key': 'bet365',
                            'title': 'Bet365',
                            'markets': [
                                {
                                    'key': 'h2h',
                                    'outcomes': [
                                        {'name': 'Manchester City', 'price': 1.80},
                                        {'name': 'Draw', 'price': 3.50},
                                        {'name': 'Liverpool', 'price': 4.20}
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        """
        endpoint = f"{self.BASE_URL}/sports/soccer_epl/odds"
        params = {
            'apiKey': self.api_key,
            'regions': regions,
            'markets': markets,
            'oddsFormat': oddsFormat
        }
        
        try:
            response = self.session.get(endpoint, params=params, timeout=15)
            response.raise_for_status()
            
            # API 사용량 확인 (헤더에 포함됨)
            remaining = response.headers.get('x-requests-remaining')
            used = response.headers.get('x-requests-used')
            
            if remaining:
                logger.info(f"API requests: {used} used, {remaining} remaining")
            
            odds_data = response.json()
            logger.info(f"Fetched odds for {len(odds_data)} EPL matches")
            
            return odds_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch EPL odds: {e}")
            return []
    
    def get_match_odds(self, event_id: str) -> Optional[Dict]:
        """
        특정 경기의 배당률 가져오기
        
        Args:
            event_id: 경기 ID
        
        Returns:
            Dict: 경기 배당률 데이터
        """
        endpoint = f"{self.BASE_URL}/sports/soccer_epl/events/{event_id}/odds"
        params = {
            'apiKey': self.api_key,
            'regions': 'uk',
            'markets': 'h2h',
            'oddsFormat': 'decimal'
        }
        
        try:
            response = self.session.get(endpoint, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch match odds for {event_id}: {e}")
            return None
    
    def parse_odds_data(self, raw_data: List[Dict]) -> List[Dict]:
        """
        API 응답을 표준 포맷으로 변환
        
        Args:
            raw_data: The Odds API 원본 응답
        
        Returns:
            List[Dict]: 정규화된 배당률 데이터
        """
        parsed_matches = []
        
        for match in raw_data:
            try:
                match_data = {
                    'match_id': match['id'],
                    'id': match['id'],  # Include 'id' for MatchPredictor
                    'commence_time': datetime.fromisoformat(
                        match['commence_time'].replace('Z', '+00:00')
                    ),
                    'home_team': match['home_team'],
                    'away_team': match['away_team'],
                    'bookmakers': {},
                    'bookmakers_raw': match.get('bookmakers', [])  # Raw data for totals extraction
                }

                # 북메이커별 배당률 추출
                for bookmaker in match.get('bookmakers', []):
                    bookie_key = bookmaker['key']

                    for market in bookmaker.get('markets', []):
                        if market['key'] == 'h2h':
                            outcomes = market['outcomes']

                            # 홈/무/원정 매칭
                            odds_dict = {}
                            for outcome in outcomes:
                                if outcome['name'] == match['home_team']:
                                    odds_dict['home'] = outcome['price']
                                elif outcome['name'] == match['away_team']:
                                    odds_dict['away'] = outcome['price']
                                elif outcome['name'] == 'Draw':
                                    odds_dict['draw'] = outcome['price']

                            match_data['bookmakers'][bookie_key] = odds_dict

                parsed_matches.append(match_data)
                
            except Exception as e:
                logger.error(f"Error parsing match data: {e}")
                continue
        
        return parsed_matches
    
    def get_historical_odds(
        self,
        sport: str = 'soccer_epl',
        date: str = None
    ) -> List[Dict]:
        """
        과거 배당률 데이터 (Historical Odds API - 유료)
        
        Args:
            sport: 스포츠 키
            date: 날짜 (YYYY-MM-DD)
        
        Returns:
            List[Dict]: 과거 배당률
        """
        # 참고: Historical API는 별도 구독 필요
        logger.warning("Historical odds API requires paid subscription")
        return []


# ============================================================
# 데모/테스트용 Mock 데이터
# ============================================================

def get_demo_odds() -> List[Dict]:
    """
    API 키 없이 테스트용 더미 데이터
    실제 EPL 경기 기준
    """
    return [
        {
            'match_id': 'demo_001',
            'commence_time': datetime(2025, 10, 5, 15, 0),
            'home_team': 'Manchester City',
            'away_team': 'Liverpool',
            'bookmakers': {
                'bet365': {'home': 1.80, 'draw': 3.50, 'away': 4.20},
                'pinnacle': {'home': 1.75, 'draw': 3.60, 'away': 4.50},
                'betfair': {'home': 1.82, 'draw': 3.45, 'away': 4.10},
                'williamhill': {'home': 1.78, 'draw': 3.55, 'away': 4.30}
            }
        },
        {
            'match_id': 'demo_002',
            'commence_time': datetime(2025, 10, 5, 17, 30),
            'home_team': 'Arsenal',
            'away_team': 'Chelsea',
            'bookmakers': {
                'bet365': {'home': 2.10, 'draw': 3.40, 'away': 3.30},
                'pinnacle': {'home': 2.05, 'draw': 3.50, 'away': 3.40},
                'betfair': {'home': 2.12, 'draw': 3.35, 'away': 3.25},
                'williamhill': {'home': 2.08, 'draw': 3.45, 'away': 3.35}
            }
        },
        {
            'match_id': 'demo_003',
            'commence_time': datetime(2025, 10, 6, 14, 0),
            'home_team': 'Tottenham',
            'away_team': 'Manchester United',
            'bookmakers': {
                'bet365': {'home': 2.30, 'draw': 3.30, 'away': 3.00},
                'pinnacle': {'home': 2.25, 'draw': 3.40, 'away': 3.10},
                'betfair': {'home': 2.32, 'draw': 3.25, 'away': 2.95},
                'williamhill': {'home': 2.28, 'draw': 3.35, 'away': 3.05}
            }
        }
    ]


# ============================================================
# CLI 테스트
# ============================================================

if __name__ == "__main__":
    import sys
    
    # API 키 확인
    api_key = os.getenv('ODDS_API_KEY')
    
    if not api_key:
        print("=" * 60)
        print("⚠️  ODDS_API_KEY not found in environment variables")
        print("=" * 60)
        print("\nTo get a free API key:")
        print("1. Visit: https://the-odds-api.com/")
        print("2. Sign up for free tier (500 requests/month)")
        print("3. Copy your API key")
        print("4. Set environment variable:")
        print("   export ODDS_API_KEY='your_key_here'")
        print("\nUsing demo data instead...\n")
        
        # 데모 데이터 표시
        demo_data = get_demo_odds()
        for match in demo_data:
            print(f"\n📅 {match['home_team']} vs {match['away_team']}")
            print(f"   Time: {match['commence_time']}")
            print(f"   Bookmakers:")
            for bookie, odds in match['bookmakers'].items():
                print(f"     {bookie:12s}: Home {odds['home']:.2f} | "
                      f"Draw {odds['draw']:.2f} | Away {odds['away']:.2f}")
        
        sys.exit(0)
    
    # 실제 API 테스트
    print("=" * 60)
    print("Testing The Odds API")
    print("=" * 60)
    
    client = OddsAPIClient(api_key)
    
    # 1. 사용 가능한 스포츠 조회
    print("\n1. Fetching available sports...")
    sports = client.get_sports()
    soccer_sports = [s for s in sports if 'soccer' in s.get('key', '')]
    print(f"   Found {len(soccer_sports)} soccer leagues:")
    for sport in soccer_sports[:5]:
        print(f"     - {sport['title']} ({sport['key']})")
    
    # 2. EPL 배당률 조회
    print("\n2. Fetching EPL odds...")
    epl_odds = client.get_epl_odds()
    
    if epl_odds:
        parsed = client.parse_odds_data(epl_odds)
        print(f"   Found {len(parsed)} upcoming EPL matches:\n")
        
        for match in parsed[:3]:
            print(f"   📅 {match['home_team']} vs {match['away_team']}")
            print(f"      Time: {match['commence_time']}")
            print(f"      Bookmakers: {len(match['bookmakers'])}")
            
            # 최고/최저 배당률 표시
            if match['bookmakers']:
                all_home_odds = [b['home'] for b in match['bookmakers'].values() if 'home' in b]
                if all_home_odds:
                    best_home = max(all_home_odds)
                    worst_home = min(all_home_odds)
                    print(f"      Home odds range: {worst_home:.2f} - {best_home:.2f}")
            print()
    else:
        print("   No odds data available")
    
    print("=" * 60)
    print("✅ Test Complete!")
    print("=" * 60)
