"""
Flask API 서버
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_caching import Cache
import sys
import os

# 부모 디렉토리를 path에 추가
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from models import DixonColesModel, EnsemblePredictor, FeatureEngineer
from models.hybrid_predictor import HybridPredictor
from models.personal_predictor import PersonalPredictor
from data_collection import FBrefScraper, UnderstatScraper
import pandas as pd

app = Flask(__name__)
CORS(app)  # React에서 접근 가능하도록

# Flask-Caching 설정
cache = Cache(app, config={
    'CACHE_TYPE': 'simple',  # 메모리 기반 캐시
    'CACHE_DEFAULT_TIMEOUT': 300  # 기본 5분
})

# 전역 객체
ensemble = EnsemblePredictor()
feature_engineer = FeatureEngineer()
fbref_scraper = FBrefScraper()
understat_scraper = UnderstatScraper()

# 하이브리드 예측기 (나중에 초기화)
hybrid_predictor = None
personal_predictor = PersonalPredictor()

# 허용 시즌 설정 (최근 5경기 + 이번시즌 + 지난시즌)
ALLOWED_SEASONS = ['2024-2025', '2025-2026']

# 실제 데이터 로드 및 모델 초기화
print("Loading historical match data...")
print(f"Allowed seasons: {ALLOWED_SEASONS}")
try:
    # DB에서 과거 시즌 데이터 로드
    from database.schema import init_db, get_session, Match
    db_path = os.path.join(os.path.dirname(__file__), '..', 'soccer_predictor.db')
    db_url = f'sqlite:///{os.path.abspath(db_path)}'
    engine = init_db(db_url)
    session = get_session(engine)

    # 허용된 시즌의 경기만 로드
    matches = session.query(Match).filter(Match.season.in_(ALLOWED_SEASONS)).all()

    # DataFrame으로 변환 (세션 닫기 전에 데이터 추출)
    historical_matches = pd.DataFrame([{
        'date': m.match_date,
        'season': m.season,
        'home_team': m.home_team.name,
        'away_team': m.away_team.name,
        'home_score': m.home_score,
        'away_score': m.away_score,
        'home_xg': m.home_xg,
        'away_xg': m.away_xg
    } for m in matches])

    session.close()

    print(f"✓ Loaded {len(historical_matches)} matches from seasons: {ALLOWED_SEASONS}")

    # 모델 초기화 (시즌 필터 적용)
    ensemble.dixon_coles.fit(historical_matches, allowed_seasons=ALLOWED_SEASONS)
    feature_engineer.calculate_pi_ratings(historical_matches, allowed_seasons=ALLOWED_SEASONS)

    # 하이브리드 예측기 초기화
    hybrid_predictor = HybridPredictor(ensemble.dixon_coles, ensemble.xgboost)

    print(f"✓ Model initialized with {len(historical_matches)} historical matches")
except Exception as e:
    print(f"Warning: Could not initialize models with real data: {e}")
    print("Using fallback initialization...")
    DUMMY_MATCHES = pd.DataFrame({
        'date': pd.date_range(start='2024-08-01', periods=30, freq='D'),
        'home_team': ['Manchester City', 'Arsenal', 'Liverpool', 'Tottenham', 'Chelsea'] * 6,
        'away_team': ['Arsenal', 'Liverpool', 'Chelsea', 'Manchester City', 'Tottenham'] * 6,
        'home_score': [2, 1, 2, 1, 2, 3, 2, 1, 2, 1] * 3,
        'away_score': [1, 1, 1, 0, 1, 1, 2, 1, 0, 1] * 3,
        'home_xg': [2.3, 1.5, 2.1, 1.8, 2.0] * 6,
        'away_xg': [1.1, 1.4, 1.2, 0.8, 1.3] * 6
    })
    ensemble.dixon_coles.fit(DUMMY_MATCHES)
    feature_engineer.calculate_pi_ratings(DUMMY_MATCHES)
    hybrid_predictor = HybridPredictor(ensemble.dixon_coles, ensemble.xgboost)
    historical_matches = DUMMY_MATCHES

@app.route('/api/health', methods=['GET'])
def health_check():
    """헬스 체크"""
    return jsonify({'status': 'ok', 'message': 'API is running'})

@app.route('/api/fixtures', methods=['GET'])
@cache.cached(timeout=300, query_string=True)  # 5분 캐싱
def get_fixtures():
    """경기 일정 가져오기"""
    try:
        fixtures = fbref_scraper.get_epl_fixtures()
        return jsonify(fixtures.to_dict(orient='records'))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/predict', methods=['POST'])
def predict_match():
    """
    경기 예측
    Body: {
        "home_team": "Manchester City",
        "away_team": "Liverpool",
        "model_type": "hybrid",  // "statistical", "personal", "hybrid"
        "stats_weight": 75,
        "personal_weight": 25,
        "recent5_weight": 50,
        "current_season_weight": 35,
        "last_season_weight": 15,
        "save_prediction": true  // 예측 저장 여부
    }
    """
    try:
        data = request.json
        home_team = data.get('home_team')
        away_team = data.get('away_team')
        model_type = data.get('model_type', 'hybrid')
        stats_weight = data.get('stats_weight', 75) / 100
        personal_weight = data.get('personal_weight', 25) / 100
        recent5_weight = data.get('recent5_weight', 50) / 100
        current_season_weight = data.get('current_season_weight', 35) / 100
        last_season_weight = data.get('last_season_weight', 15) / 100
        save_prediction = data.get('save_prediction', False)

        # 특징 생성 (시즌 필터 적용)
        features = feature_engineer.create_match_features(
            home_team, away_team, historical_matches,
            allowed_seasons=ALLOWED_SEASONS
        )

        if model_type == 'statistical':
            # Dixon-Coles with temporal weighting
            # 각 시간 기간별 데이터로 별도 예측 생성

            # 1. 최근 5경기 예측
            recent_matches = historical_matches.sort_values('date', ascending=False).head(30)  # 최근 30경기에서 각 팀 5경기
            dc_recent = DixonColesModel()
            dc_recent.xi = 0.03  # 최근 경기 강조
            dc_recent.fit(recent_matches, allowed_seasons=ALLOWED_SEASONS)
            pred_recent = dc_recent.predict_match(home_team, away_team)

            # 2. 현재 시즌 예측 (2025-26)
            current_season_matches = historical_matches[historical_matches['season'] == '2025-2026']
            if len(current_season_matches) > 0:
                dc_current = DixonColesModel()
                dc_current.fit(current_season_matches, allowed_seasons=['2025-2026'])
                pred_current = dc_current.predict_match(home_team, away_team)
            else:
                pred_current = pred_recent  # Fallback

            # 3. 지난 시즌 예측 (2024-25)
            last_season_matches = historical_matches[historical_matches['season'] == '2024-2025']
            dc_last = DixonColesModel()
            dc_last.fit(last_season_matches, allowed_seasons=['2024-2025'])
            pred_last = dc_last.predict_match(home_team, away_team)

            # 가중 평균 계산
            prediction = {
                'home_win': (pred_recent['home_win'] * recent5_weight +
                            pred_current['home_win'] * current_season_weight +
                            pred_last['home_win'] * last_season_weight),
                'draw': (pred_recent['draw'] * recent5_weight +
                        pred_current['draw'] * current_season_weight +
                        pred_last['draw'] * last_season_weight),
                'away_win': (pred_recent['away_win'] * recent5_weight +
                            pred_current['away_win'] * current_season_weight +
                            pred_last['away_win'] * last_season_weight),
                'expected_home_goals': (pred_recent['expected_home_goals'] * recent5_weight +
                                       pred_current['expected_home_goals'] * current_season_weight +
                                       pred_last['expected_home_goals'] * last_season_weight),
                'expected_away_goals': (pred_recent['expected_away_goals'] * recent5_weight +
                                       pred_current['expected_away_goals'] * current_season_weight +
                                       pred_last['expected_away_goals'] * last_season_weight),
                'top_scores': pred_recent['top_scores'],  # 최근 경기 기준 스코어 확률
                'weights_used': {
                    'recent5': recent5_weight * 100,
                    'current_season': current_season_weight * 100,
                    'last_season': last_season_weight * 100
                },
                'breakdown': {
                    'recent5': {'home_win': pred_recent['home_win'], 'draw': pred_recent['draw'], 'away_win': pred_recent['away_win']},
                    'current_season': {'home_win': pred_current['home_win'], 'draw': pred_current['draw'], 'away_win': pred_current['away_win']},
                    'last_season': {'home_win': pred_last['home_win'], 'draw': pred_last['draw'], 'away_win': pred_last['away_win']}
                }
            }
        elif model_type == 'personal':
            # 개인 분석 - 선수 능력치 기반
            # 프론트엔드에서 player_ratings 전달 받음
            home_player_ratings = data.get('home_player_ratings', [])
            away_player_ratings = data.get('away_player_ratings', [])

            # 선수 평가 데이터가 없으면 더미 데이터 사용
            if not home_player_ratings or not away_player_ratings:
                # 기본 평균 능력치 (중간 정도 팀)
                home_player_ratings = [
                    {'position': 'ST', 'ratings': {'슈팅': 75, '위치선정': 75, '퍼스트터치': 75, '스피드': 75, '피지컬': 75}},
                    {'position': 'W', 'ratings': {'드리블': 75, '스피드': 75, '크로스': 75, '슈팅': 75, '민첩성': 75}},
                    {'position': 'AM', 'ratings': {'패스': 75, '비전': 75, '드리블': 75, '슈팅': 75, '창조력': 75}},
                    {'position': 'DM', 'ratings': {'태클': 75, '인터셉트': 75, '패스': 75, '체력': 75, '포지셔닝': 75}},
                    {'position': 'CB', 'ratings': {'태클': 75, '마크': 75, '헤더': 75, '포지셔닝': 75, '피지컬': 75}},
                    {'position': 'GK', 'ratings': {'반응속도': 75, '포지셔닝': 75, '핸들링': 75, '발재간': 75, '공중볼': 75}},
                ]
                away_player_ratings = home_player_ratings.copy()

            prediction = personal_predictor.predict_match(
                home_player_ratings,
                away_player_ratings,
                home_advantage=1.3
            )
        else:
            # 하이브리드 - 새로운 HybridPredictor 사용
            prediction = hybrid_predictor.predict(
                home_team, away_team,
                stats_weight=stats_weight,
                ml_weight=personal_weight,
                features=features
            )

            # 시간 가중치 메타데이터 추가
            prediction['temporal_weights'] = {
                'recent5': recent5_weight * 100,
                'current_season': current_season_weight * 100,
                'last_season': last_season_weight * 100
            }

        # 예측 저장 (옵션)
        if save_prediction:
            from utils.db_manager import DatabaseManager
            from database.schema import Team
            db = DatabaseManager()

            # 팀 ID 찾기
            db_path = os.path.join(os.path.dirname(__file__), '..', 'soccer_predictor.db')
            db_url = f'sqlite:///{os.path.abspath(db_path)}'
            engine = init_db(db_url)
            temp_session = get_session(engine)

            home_team_obj = temp_session.query(Team).filter_by(name=home_team).first()
            away_team_obj = temp_session.query(Team).filter_by(name=away_team).first()

            # 경기 찾기 또는 생성 (미래 경기는 ID 없을 수 있음)
            match = temp_session.query(Match).filter_by(
                home_team_id=home_team_obj.id if home_team_obj else None,
                away_team_id=away_team_obj.id if away_team_obj else None,
                status='upcoming'
            ).first()

            match_id = match.id if match else None
            temp_session.close()

            # match_id 없으면 임시 경기 생성 (예측만 저장)
            if not match_id:
                print(f"Warning: No match found for {home_team} vs {away_team}, using dummy match_id=1")
                match_id = 1

            db.save_prediction(
                match_id=match_id,
                home_win_prob=prediction['home_win'],
                draw_prob=prediction['draw'],
                away_win_prob=prediction['away_win'],
                expected_home_goals=prediction['expected_home_goals'],
                expected_away_goals=prediction['expected_away_goals'],
                model_type=model_type,
                stats_weight=stats_weight * 100,
                personal_weight=personal_weight * 100
            )
            db.close()

        return jsonify(prediction)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/predictions/history', methods=['GET'])
def get_predictions_history():
    """예측 히스토리"""
    try:
        from utils.db_manager import DatabaseManager
        db = DatabaseManager()

        limit = request.args.get('limit', 20, type=int)
        history = db.get_predictions_history(limit=limit)

        db.close()
        return jsonify(history)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/predictions/accuracy', methods=['GET'])
def get_prediction_accuracy():
    """예측 정확도"""
    try:
        from utils.db_manager import DatabaseManager
        db = DatabaseManager()

        days = request.args.get('days', 30, type=int)
        accuracy = db.calculate_prediction_accuracy(days=days)

        db.close()
        return jsonify(accuracy)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/player-ratings', methods=['POST'])
def save_player_ratings():
    """선수 능력치 저장"""
    try:
        from utils.db_manager import DatabaseManager
        db = DatabaseManager()

        data = request.json
        player_id = data.get('player_id')
        ratings = data.get('ratings', {})

        for attribute, rating in ratings.items():
            db.save_player_rating(player_id, attribute, rating)

        db.close()
        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/teams', methods=['GET'])
@cache.cached(timeout=3600)  # 1시간 캐싱 (팀 목록은 자주 변경 안됨)
def get_teams():
    """팀 목록"""
    from database.schema import Team, get_session, init_db
    import os

    try:
        db_path = os.path.join(os.path.dirname(__file__), '..', 'soccer_predictor.db')
        db_url = f'sqlite:///{os.path.abspath(db_path)}'
        engine = init_db(db_url)
        session = get_session(engine)

        teams = session.query(Team).filter_by(league='EPL').all()
        team_names = [team.name for team in teams]
        session.close()

        return jsonify(team_names)
    except Exception as e:
        # Fallback to hardcoded list
        teams = [
            'Manchester City', 'Arsenal', 'Liverpool', 'Tottenham', 'Chelsea',
            'Manchester United', 'Newcastle United', 'Brighton', 'Aston Villa', 'Wolverhampton Wanderers',
            'West Ham', 'Brentford', 'Fulham', 'Crystal Palace', 'Everton',
            'Bournemouth', 'Nottingham Forest', 'Leicester', 'Ipswich', 'Southampton'
        ]
        return jsonify(teams)

@app.route('/api/team-stats/<team_name>', methods=['GET'])
@cache.cached(timeout=1800)  # 30분 캐싱
def get_team_stats(team_name):
    """팀 통계"""
    try:
        # Pi-ratings
        ratings = feature_engineer.pi_ratings.get(team_name, {'home': 0.0, 'away': 0.0})

        # 최근 폼
        form = feature_engineer.get_recent_form(team_name, historical_matches, n_matches=5)

        # 홈/원정 통계 (시즌 필터 적용)
        home_stats = feature_engineer.get_home_away_stats(team_name, historical_matches, is_home=True, allowed_seasons=ALLOWED_SEASONS)
        away_stats = feature_engineer.get_home_away_stats(team_name, historical_matches, is_home=False, allowed_seasons=ALLOWED_SEASONS)

        return jsonify({
            'team': team_name,
            'pi_ratings': ratings,
            'recent_form': form,
            'home_stats': home_stats,
            'away_stats': away_stats
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/squad/<team_name>', methods=['GET'])
@cache.cached(timeout=1800)  # 30분 캐싱
def get_squad(team_name):
    """선수 명단"""
    try:
        # 선수 데이터 import
        sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
        from data.squad_data import get_squad as get_squad_data

        squad = get_squad_data(team_name)
        if squad:
            return jsonify(squad)

        # Fallback 더미 데이터
        squads = {
            'Manchester City': [
                {'id': 1, 'name': 'Erling Haaland', 'position': 'ST', 'number': 9, 'age': 24, 'nationality': '🇳🇴'},
                {'id': 2, 'name': 'Phil Foden', 'position': 'W', 'number': 47, 'age': 23, 'nationality': '🏴󠁧󠁢󠁥󠁮󠁧󠁿'},
                {'id': 3, 'name': 'Kevin De Bruyne', 'position': 'AM', 'number': 17, 'age': 32, 'nationality': '🇧🇪'},
            ],
            'Liverpool': [
                {'id': 11, 'name': 'Darwin Nunez', 'position': 'ST', 'number': 9, 'age': 24, 'nationality': '🇺🇾'},
                {'id': 12, 'name': 'Mohamed Salah', 'position': 'W', 'number': 11, 'age': 31, 'nationality': '🇪🇬'},
            ]
        }

        return jsonify(squads.get(team_name, []))
    except Exception as e:
        print(f"Error in get_squad: {e}")
        return jsonify([])

@app.route('/api/standings', methods=['GET'])
@cache.cached(timeout=300, query_string=True)  # 5분 캐싱
def get_standings():
    """리그 순위표 반환"""
    from database.schema import Standings, Team, get_session, init_db
    import os

    season = request.args.get('season', '2024-2025')

    try:
        # DB에서 순위표 조회
        db_path = os.path.join(os.path.dirname(__file__), '..', 'soccer_predictor.db')
        db_url = f'sqlite:///{os.path.abspath(db_path)}'
        engine = init_db(db_url)
        session = get_session(engine)

        standings = session.query(Standings, Team).join(Team).filter(
            Standings.season == season
        ).order_by(Standings.rank).all()

        if standings:
            result = []
            for standing, team in standings:
                result.append({
                    'rank': standing.rank,
                    'team': team.name,
                    'matches_played': standing.matches_played,
                    'wins': standing.wins,
                    'draws': standing.draws,
                    'losses': standing.losses,
                    'goals_for': standing.goals_for,
                    'goals_against': standing.goals_against,
                    'goal_difference': standing.goal_difference,
                    'points': standing.points,
                    'updated_at': standing.updated_at.isoformat() if standing.updated_at else None
                })
            session.close()
            return jsonify(result)

        session.close()

        # DB가 비어있으면 실시간 스크래핑
        standings_df = fbref_scraper.get_league_standings(season=season)

        if not standings_df.empty:
            result = standings_df.to_dict(orient='records')
            return jsonify(result)
        else:
            return jsonify({'error': 'No standings data available'}), 404

    except Exception as e:
        print(f"Error in get_standings: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/predict/catboost', methods=['POST'])
def predict_catboost():
    """CatBoost 모델 예측"""
    try:
        from models.catboost_model import FootballCatBoostModel
        data = request.json
        catboost_model = FootballCatBoostModel(use_gpu=False)
        prediction = catboost_model.predict(
            home_team=data.get('home_team'),
            away_team=data.get('away_team'),
            home_xg=data.get('home_xg', 1.5),
            away_xg=data.get('away_xg', 1.2),
            home_possession=data.get('home_possession', 50),
            away_possession=data.get('away_possession', 50),
            home_shots=data.get('home_shots', 12),
            away_shots=data.get('away_shots', 10)
        )
        return jsonify(prediction)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/expected-threat', methods=['POST'])
def calculate_expected_threat():
    """Expected Threat (xT) 계산"""
    try:
        from features.expected_threat import ExpectedThreatCalculator
        data = request.json
        xt_calc = ExpectedThreatCalculator()
        match_xt = xt_calc.calculate_match_xt_score(
            data.get('home_stats', {}),
            data.get('away_stats', {})
        )
        return jsonify(match_xt)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/evaluate', methods=['POST'])
def evaluate_predictions():
    """예측 평가 메트릭 계산"""
    try:
        from evaluation.metrics import evaluate_predictions as eval_preds
        data = request.json
        metrics = eval_preds(
            data.get('predictions', []),
            data.get('actuals', [])
        )
        return jsonify(metrics)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/predict/ensemble', methods=['POST'])
def predict_ensemble():
    """앙상블 모델 예측"""
    try:
        from models.ensemble import EnsemblePredictor as AdvancedEnsemble
        data = request.json
        model_predictions = {
            'dixon_coles': ensemble.dixon_coles.predict_match(
                data.get('home_team'),
                data.get('away_team')
            )
        }
        ensemble_predictor = AdvancedEnsemble(
            ensemble_method=data.get('ensemble_method', 'weighted_average')
        )
        if data.get('weights'):
            ensemble_predictor.set_weights(data['weights'])
        result = ensemble_predictor.predict(model_predictions)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("Starting Flask API server...")
    print("Available endpoints:")
    print("  GET  /api/health")
    print("  GET  /api/fixtures")
    print("  POST /api/predict")
    print("  GET  /api/teams")
    print("  GET  /api/team-stats/<team_name>")
    print("  GET  /api/squad/<team_name>")
    print("  GET  /api/standings")
    print("  POST /api/predict/catboost")
    print("  POST /api/expected-threat")
    print("  POST /api/evaluate")
    print("  POST /api/predict/ensemble")

    # 스케줄러 시작
    try:
        sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
        from utils.scheduler import get_scheduler
        scheduler = get_scheduler()
        scheduler.start()
        print("\n📅 Auto-scheduler enabled: Daily match updates at 02:00 KST")
    except Exception as e:
        print(f"⚠️  Scheduler not started: {e}")

    app.run(host='0.0.0.0', port=5001, debug=True)
