"""
Flask API - Odds-Based Value Betting System
배당률 기반 예측 시스템으로 pivot
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import sys
import os
import logging
from datetime import datetime

# 부모 디렉토리를 path에 추가
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# 새로운 모듈 import
from odds_collection import OddsAPIClient, OddsAggregator
from value_betting import ValueDetector, ArbitrageFinder, KellyCriterion

# 기존 모델 (보조 역할)
from models import DixonColesModel
from models.feature_engineering import FeatureEngineer

app = Flask(__name__)

# CORS 설정 (보안 강화)
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
CORS(app, resources={
    r"/api/*": {
        "origins": ALLOWED_ORIGINS,
        "methods": ["GET", "POST"],
        "allow_headers": ["Content-Type", "X-API-Key"]
    }
})

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# 전역 객체 초기화
odds_client = OddsAPIClient()
odds_aggregator = OddsAggregator()
value_detector = ValueDetector(min_edge=0.02, min_confidence=0.65)
arbitrage_finder = ArbitrageFinder(min_profit=0.005)
kelly_calculator = KellyCriterion(fraction=0.25, max_bet=0.05)

# 기존 모델 (보조)
dixon_coles = DixonColesModel()
feature_engineer = FeatureEngineer()

print("=" * 60)
print("🎯 Odds-Based Value Betting System")
print("=" * 60)
print("✅ API initialized successfully")
print("=" * 60)


# ============================================================
# Health & Status
# ============================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """헬스 체크"""
    return jsonify({
        'status': 'ok',
        'message': 'Odds-Based Value Betting API is running',
        'version': '2.0.0',
        'mode': 'odds_based'
    })


@app.route('/api/status', methods=['GET'])
def get_status():
    """시스템 상태"""
    api_key_configured = bool(os.getenv('ODDS_API_KEY'))
    
    return jsonify({
        'odds_api': {
            'configured': api_key_configured,
            'status': 'active' if api_key_configured else 'demo_mode'
        },
        'modules': {
            'odds_collection': 'active',
            'value_betting': 'active',
            'arbitrage': 'active',
            'kelly_criterion': 'active',
            'dixon_coles': 'auxiliary'  # 보조 역할
        },
        'timestamp': datetime.now().isoformat()
    })


# ============================================================
# Odds Endpoints (Core)
# ============================================================

@app.route('/api/odds/live', methods=['GET'])
def get_live_odds():
    """
    실시간 EPL 배당률
    
    Query Params:
        - use_demo: true/false (API 키 없을 때 데모 데이터)
    
    Returns:
        List[Dict]: 경기별 배당률
    """
    try:
        use_demo = request.args.get('use_demo', 'false').lower() == 'true'
        api_key = os.getenv('ODDS_API_KEY')
        
        if not api_key or use_demo:
            logger.info("Using demo odds data")
            from odds_collection.odds_api_client import get_demo_odds
            raw_data = get_demo_odds()
        else:
            logger.info("Fetching live odds from The Odds API")
            raw_data_api = odds_client.get_epl_odds()
            raw_data = odds_client.parse_odds_data(raw_data_api)
        
        return jsonify({
            'success': True,
            'count': len(raw_data),
            'matches': raw_data,
            'source': 'demo' if (not api_key or use_demo) else 'live_api',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error fetching live odds: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/odds/analyze/<match_id>', methods=['GET'])
def analyze_match_odds(match_id):
    """
    특정 경기 배당률 분석
    
    Args:
        match_id: 경기 ID
    
    Returns:
        Dict: 분석 결과 (overround, consensus, best odds 등)
    """
    try:
        # 실시간 배당률 가져오기
        use_demo = request.args.get('use_demo', 'false').lower() == 'true'
        
        if use_demo:
            from odds_collection.odds_api_client import get_demo_odds
            all_matches = get_demo_odds()
        else:
            raw_data = odds_client.get_epl_odds()
            all_matches = odds_client.parse_odds_data(raw_data)
        
        # match_id로 찾기
        match = next((m for m in all_matches if m['match_id'] == match_id), None)
        
        if not match:
            return jsonify({'error': 'Match not found'}), 404
        
        # 분석 실행
        analysis = odds_aggregator.analyze_match_odds(match)
        
        # bookmakers_raw 추가 (Value Detector에서 필요)
        analysis['bookmakers_raw'] = match['bookmakers']
        
        return jsonify({
            'success': True,
            'analysis': analysis
        })
        
    except Exception as e:
        logger.error(f"Error analyzing match odds: {e}")
        return jsonify({'error': str(e)}), 500


# ============================================================
# Value Betting Endpoints
# ============================================================

@app.route('/api/value-bets', methods=['GET'])
def get_value_bets():
    """
    모든 경기의 Value Bet 탐지
    
    Query Params:
        - min_edge: 최소 edge (default: 0.02)
        - min_confidence: 최소 신뢰도 (default: 0.65)
        - use_demo: true/false
    
    Returns:
        List[Dict]: Value Bet 목록
    """
    try:
        min_edge = float(request.args.get('min_edge', 0.02))
        min_confidence = float(request.args.get('min_confidence', 0.65))
        use_demo = request.args.get('use_demo', 'false').lower() == 'true'
        
        # Value Detector 재설정
        detector = ValueDetector(min_edge=min_edge, min_confidence=min_confidence)
        
        # 배당률 가져오기
        if use_demo:
            from odds_collection.odds_api_client import get_demo_odds
            all_matches = get_demo_odds()
        else:
            raw_data = odds_client.get_epl_odds()
            all_matches = odds_client.parse_odds_data(raw_data)
        
        # 모든 경기 분석
        all_value_bets = []
        
        for match in all_matches:
            analysis = odds_aggregator.analyze_match_odds(match)
            analysis['bookmakers_raw'] = match['bookmakers']
            
            value_bets = detector.detect_value_bets(analysis)
            all_value_bets.extend(value_bets)
        
        # 요약 통계
        summary = detector.summarize_value_bets(all_value_bets)
        
        return jsonify({
            'success': True,
            'value_bets': all_value_bets,
            'summary': summary,
            'criteria': {
                'min_edge': min_edge,
                'min_confidence': min_confidence
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error detecting value bets: {e}")
        return jsonify({'error': str(e)}), 500


# ============================================================
# Arbitrage Endpoints
# ============================================================

@app.route('/api/arbitrage', methods=['GET'])
def get_arbitrage_opportunities():
    """
    아비트라지 기회 탐색
    
    Query Params:
        - min_profit: 최소 수익률 (default: 0.005 = 0.5%)
        - use_demo: true/false
    
    Returns:
        List[Dict]: 아비트라지 기회
    """
    try:
        min_profit = float(request.args.get('min_profit', 0.005))
        use_demo = request.args.get('use_demo', 'false').lower() == 'true'
        
        # Arbitrage Finder 재설정
        finder = ArbitrageFinder(min_profit=min_profit)
        
        # 배당률 가져오기
        if use_demo:
            from odds_collection.odds_api_client import get_demo_odds
            all_matches = get_demo_odds()
        else:
            raw_data = odds_client.get_epl_odds()
            all_matches = odds_client.parse_odds_data(raw_data)
        
        # 모든 경기 분석
        analyzed_matches = []
        for match in all_matches:
            analysis = odds_aggregator.analyze_match_odds(match)
            analyzed_matches.append(analysis)
        
        # 아비트라지 탐색
        opportunities = finder.find_arbitrage_opportunities(analyzed_matches)
        
        return jsonify({
            'success': True,
            'opportunities': opportunities,
            'count': len(opportunities),
            'criteria': {
                'min_profit': min_profit
            },
            'note': 'Arbitrage opportunities are rare and disappear quickly!',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error finding arbitrage: {e}")
        return jsonify({'error': str(e)}), 500


# ============================================================
# Kelly Criterion Endpoints
# ============================================================

@app.route('/api/kelly/calculate', methods=['POST'])
def calculate_kelly():
    """
    Kelly Criterion 계산
    
    Body:
        {
            "win_probability": 0.60,
            "decimal_odds": 2.00,
            "fraction": 0.25,  // optional
            "bankroll": 10000  // optional
        }
    
    Returns:
        Dict: Kelly 베팅 비율 및 금액
    """
    try:
        data = request.json
        
        win_prob = data.get('win_probability')
        odds = data.get('decimal_odds')
        fraction = data.get('fraction', 0.25)
        bankroll = data.get('bankroll', 10000.0)
        
        if not win_prob or not odds:
            return jsonify({'error': 'win_probability and decimal_odds required'}), 400
        
        kelly = KellyCriterion(fraction=fraction, max_bet=0.05)
        kelly_percent = kelly.calculate_kelly(win_prob, odds)
        bet_amount = kelly_percent * bankroll
        
        return jsonify({
            'success': True,
            'kelly_percent': kelly_percent * 100,
            'bet_amount': bet_amount,
            'bankroll': bankroll,
            'edge': (win_prob * odds - 1) * 100,
            'fraction_used': fraction
        })
        
    except Exception as e:
        logger.error(f"Error calculating Kelly: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/kelly/portfolio', methods=['POST'])
def calculate_portfolio_allocation():
    """
    포트폴리오 배분 계산
    
    Body:
        {
            "value_bets": [...],  // Value Detector 결과
            "bankroll": 10000,
            "fraction": 0.25
        }
    
    Returns:
        Dict: 베팅 배분 계획
    """
    try:
        data = request.json
        
        value_bets = data.get('value_bets', [])
        bankroll = data.get('bankroll', 10000.0)
        fraction = data.get('fraction', 0.25)
        
        kelly = KellyCriterion(fraction=fraction, max_bet=0.05)
        allocation = kelly.calculate_bankroll_allocation(value_bets, bankroll)
        
        return jsonify({
            'success': True,
            'allocation': allocation
        })
        
    except Exception as e:
        logger.error(f"Error calculating portfolio: {e}")
        return jsonify({'error': str(e)}), 500


# ============================================================
# Auxiliary: Dixon-Coles (보조)
# ============================================================

@app.route('/api/auxiliary/dixon-coles', methods=['POST'])
def dixon_coles_prediction():
    """
    Dixon-Coles 예측 (보조 역할)
    북메이커 배당률과 비교용
    
    Body:
        {
            "home_team": "Manchester City",
            "away_team": "Liverpool"
        }
    """
    try:
        data = request.json
        home_team = data.get('home_team')
        away_team = data.get('away_team')
        
        if not home_team or not away_team:
            return jsonify({'error': 'home_team and away_team required'}), 400
        
        # Dixon-Coles 예측
        prediction = dixon_coles.predict_match(home_team, away_team)
        
        return jsonify({
            'success': True,
            'prediction': prediction,
            'note': 'This is an auxiliary model. Use bookmaker odds as primary source.',
            'role': 'comparison_only'
        })
        
    except Exception as e:
        logger.error(f"Error in Dixon-Coles prediction: {e}")
        return jsonify({'error': str(e)}), 500


# ============================================================
# Combined Dashboard
# ============================================================

@app.route('/api/dashboard', methods=['GET'])
def get_dashboard_data():
    """
    통합 대시보드 데이터
    - 실시간 배당률
    - Value Bets
    - Arbitrage
    
    Query Params:
        - use_demo: true/false
    """
    try:
        use_demo = request.args.get('use_demo', 'true').lower() == 'true'
        
        # 1. 배당률 가져오기
        if use_demo:
            from odds_collection.odds_api_client import get_demo_odds
            all_matches = get_demo_odds()
        else:
            raw_data = odds_client.get_epl_odds()
            all_matches = odds_client.parse_odds_data(raw_data)
        
        # 2. 모든 경기 분석
        analyzed_matches = []
        for match in all_matches:
            analysis = odds_aggregator.analyze_match_odds(match)
            analysis['bookmakers_raw'] = match['bookmakers']
            analyzed_matches.append(analysis)
        
        # 3. Value Bets 탐지
        all_value_bets = []
        for analysis in analyzed_matches:
            value_bets = value_detector.detect_value_bets(analysis)
            all_value_bets.extend(value_bets)
        
        value_summary = value_detector.summarize_value_bets(all_value_bets)
        
        # 4. Arbitrage 탐색
        arb_opportunities = arbitrage_finder.find_arbitrage_opportunities(analyzed_matches)
        
        return jsonify({
            'success': True,
            'matches': analyzed_matches,
            'value_bets': {
                'opportunities': all_value_bets,
                'summary': value_summary
            },
            'arbitrage': {
                'opportunities': arb_opportunities,
                'count': len(arb_opportunities)
            },
            'source': 'demo' if use_demo else 'live_api',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error generating dashboard: {e}")
        return jsonify({'error': str(e)}), 500


# ============================================================
# Documentation
# ============================================================

@app.route('/api/docs', methods=['GET'])
def get_api_docs():
    """API 문서"""
    return jsonify({
        'api_version': '2.0.0',
        'system': 'Odds-Based Value Betting',
        'endpoints': {
            'health': {
                'GET /api/health': 'Health check'
            },
            'odds': {
                'GET /api/odds/live': 'Get live EPL odds',
                'GET /api/odds/analyze/<match_id>': 'Analyze specific match odds'
            },
            'value_betting': {
                'GET /api/value-bets': 'Detect value betting opportunities',
                'POST /api/kelly/calculate': 'Calculate Kelly Criterion',
                'POST /api/kelly/portfolio': 'Portfolio allocation'
            },
            'arbitrage': {
                'GET /api/arbitrage': 'Find arbitrage opportunities'
            },
            'dashboard': {
                'GET /api/dashboard': 'Combined dashboard data'
            },
            'auxiliary': {
                'POST /api/auxiliary/dixon-coles': 'Dixon-Coles prediction (comparison only)'
            }
        },
        'documentation': 'https://github.com/yourorg/soccer-predictor'
    })


if __name__ == '__main__':
    print("\n🚀 Starting Odds-Based Value Betting API...")
    print("\nAvailable endpoints:")
    print("  GET  /api/health")
    print("  GET  /api/status")
    print("  GET  /api/odds/live")
    print("  GET  /api/odds/analyze/<match_id>")
    print("  GET  /api/value-bets")
    print("  GET  /api/arbitrage")
    print("  POST /api/kelly/calculate")
    print("  POST /api/kelly/portfolio")
    print("  GET  /api/dashboard")
    print("  POST /api/auxiliary/dixon-coles")
    print("\n💡 Tip: Use ?use_demo=true to test without API key")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5001, debug=True)
