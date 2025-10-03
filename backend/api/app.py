"""
Flask API 서버
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_caching import Cache
import sys
import os
import logging

# 부모 디렉토리를 path에 추가
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from models import DixonColesModel, EnsemblePredictor, FeatureEngineer
from models.hybrid_predictor import HybridPredictor
from models.personal_predictor import PersonalPredictor
from data_collection import FBrefScraper, UnderstatScraper
from database.schema import Match, init_db, get_session
import pandas as pd

app = Flask(__name__)
CORS(app)  # React에서 접근 가능하도록

# 로깅 설정 - stdout으로 모든 로그 출력
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


# ==================== Error Handlers ====================

class APIError(Exception):
    """Base API Error"""
    status_code = 500

    def __init__(self, message, status_code=None, payload=None):
        super().__init__()
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['error'] = {
            'code': self.__class__.__name__,
            'message': self.message,
            'status': self.status_code
        }
        return rv


class ValidationError(APIError):
    """Validation Error - 400"""
    status_code = 400


class NotFoundError(APIError):
    """Resource Not Found - 404"""
    status_code = 404


@app.errorhandler(APIError)
def handle_api_error(error):
    """Handle custom API errors"""
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.errorhandler(404)
def handle_404(error):
    """Handle 404 errors"""
    return jsonify({
        'error': {
            'code': 'NOT_FOUND',
            'message': 'The requested resource was not found',
            'status': 404
        }
    }), 404


@app.errorhandler(500)
def handle_500(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {str(error)}", exc_info=True)
    return jsonify({
        'error': {
            'code': 'INTERNAL_SERVER_ERROR',
            'message': 'An internal server error occurred',
            'status': 500
        }
    }), 500


@app.errorhandler(Exception)
def handle_exception(error):
    """Handle all uncaught exceptions"""
    logger.error(f"Unhandled exception: {str(error)}", exc_info=True)
    return jsonify({
        'error': {
            'code': 'UNHANDLED_EXCEPTION',
            'message': str(error),
            'status': 500
        }
    }), 500

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

# 베이지안 모델 캐시 (메모리에 학습된 모델 보관)
bayesian_model_cache = None
dixon_coles_model = None

# 허용 시즌 설정 (최근 5경기 + 이번시즌 + 지난시즌)
ALLOWED_SEASONS = ['2023-2024', '2024-2025']

# 실제 데이터 로드 및 모델 초기화
print("=" * 60)
print("Initializing API with REAL trained models")
print("=" * 60)

try:
    import pickle
    from models.bayesian_dixon_coles_simplified import SimplifiedBayesianDixonColes

    # Load pre-trained models from cache
    model_dir = os.path.join(os.path.dirname(__file__), '..', 'model_cache')

    print("\nLoading pre-trained models from cache...")

    # Load Bayesian model
    bayesian_path = os.path.join(model_dir, 'bayesian_model_real.pkl')
    with open(bayesian_path, 'rb') as f:
        bayesian_model_cache = pickle.load(f)
    print(f"✓ Bayesian Dixon-Coles loaded: {bayesian_path}")

    # Load Dixon-Coles model
    dixon_path = os.path.join(model_dir, 'dixon_coles_real.pkl')
    with open(dixon_path, 'rb') as f:
        dixon_coles_model = pickle.load(f)
    print(f"✓ Dixon-Coles (MLE) loaded: {dixon_path}")

    # Update ensemble with trained model
    ensemble.dixon_coles = dixon_coles_model

    # Load historical data from CSV for features
    csv_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'epl_real_understat.csv')
    historical_matches = pd.read_csv(csv_path)
    historical_matches['date'] = pd.to_datetime(historical_matches['date'])

    print(f"\n✓ Loaded {len(historical_matches)} historical matches")
    print(f"  Date range: {historical_matches['date'].min().date()} to {historical_matches['date'].max().date()}")
    print(f"  Teams: {historical_matches['home_team'].nunique()}")

    # Calculate features
    feature_engineer.calculate_pi_ratings(historical_matches)

    # Initialize hybrid predictor (xgboost optional)
    try:
        xgboost_model = ensemble.xgboost if hasattr(ensemble, 'xgboost') else None
        hybrid_predictor = HybridPredictor(dixon_coles_model, xgboost_model)
    except Exception as e:
        print(f"Warning: HybridPredictor initialization failed: {e}")
        hybrid_predictor = None

    print("\n" + "=" * 60)
    print("✅ API READY with REAL trained models!")
    print("=" * 60)

except Exception as e:
    print(f"\n❌ Error loading real models: {e}")
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
    try:
        xgboost_model = ensemble.xgboost if hasattr(ensemble, 'xgboost') else None
        hybrid_predictor = HybridPredictor(ensemble.dixon_coles, xgboost_model)
    except:
        hybrid_predictor = None
    historical_matches = DUMMY_MATCHES
    import traceback
    traceback.print_exc()

@app.route('/api/health', methods=['GET'])
def health_check():
    """헬스 체크"""
    return jsonify({'status': 'ok', 'message': 'API is running'})

@app.route('/api/fixtures', methods=['GET'])
@cache.cached(timeout=300, query_string=True)  # 5분 캐싱
def get_fixtures():
    """경기 일정 가져오기"""
    try:
        import numpy as np
        fixtures = fbref_scraper.get_epl_fixtures()

        # NaN을 None으로 변환 (JSON에서 null로 변환됨)
        fixtures_dict = fixtures.to_dict(orient='records')
        for fixture in fixtures_dict:
            for key, value in fixture.items():
                if isinstance(value, float) and np.isnan(value):
                    fixture[key] = None

        return jsonify(fixtures_dict)
    except Exception as e:
        logger.error(f"Error fetching fixtures: {str(e)}", exc_info=True)
        raise APIError(f"Failed to fetch fixtures: {str(e)}", status_code=500)

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
        logger.info("\n" + "="*80)
        logger.info("🔍 DEBUG: /api/predict endpoint called")
        logger.info("="*80)

        data = request.json or {}
        logger.info(f"📥 Incoming request data: {data}")

        # Validate required parameters
        home_team = data.get('home_team')
        away_team = data.get('away_team')

        if not home_team:
            raise ValidationError("Missing required parameter: home_team")
        if not away_team:
            raise ValidationError("Missing required parameter: away_team")

        model_type = data.get('model_type', 'hybrid')
        stats_weight = data.get('stats_weight', 75) / 100
        personal_weight = data.get('personal_weight', 25) / 100
        recent5_weight = data.get('recent5_weight', 50) / 100
        current_season_weight = data.get('current_season_weight', 35) / 100
        last_season_weight = data.get('last_season_weight', 15) / 100
        save_prediction = data.get('save_prediction', False)

        logger.info(f"🏠 Home team: {home_team}")
        logger.info(f"✈️  Away team: {away_team}")
        logger.info(f"🤖 Model type: {model_type}")
        logger.info(f"⚖️  Weights - Stats: {stats_weight}, Personal: {personal_weight}")
        logger.info(f"⏰ Temporal - Recent5: {recent5_weight}, Current: {current_season_weight}, Last: {last_season_weight}")

        # 특징 생성 (시즌 필터 적용)
        logger.info(f"🔧 Creating match features...")
        try:
            features = feature_engineer.create_match_features(
                home_team, away_team, historical_matches,
                allowed_seasons=ALLOWED_SEASONS
            )
            logger.info(f"✅ Features created successfully")
        except Exception as feat_error:
            logger.error(f"❌ ERROR in feature creation: {feat_error}")
            import traceback
            logger.error(traceback.format_exc())
            raise

        logger.info(f"🎯 Starting prediction with model_type: {model_type}")

        if model_type == 'statistical':
            logger.info(f"📊 Using statistical (Dixon-Coles) model")
            logger.info(f"🔍 dixon_coles_model object: {dixon_coles_model}")
            logger.info(f"🔍 Has predict_match method: {hasattr(dixon_coles_model, 'predict_match')}")

            # Use pre-trained Dixon-Coles model (FAST)
            try:
                prediction = dixon_coles_model.predict_match(home_team, away_team)
                logger.info(f"✅ Dixon-Coles prediction successful: {prediction}")
            except Exception as pred_error:
                logger.error(f"❌ ERROR in Dixon-Coles prediction: {pred_error}")
                import traceback
                logger.error(traceback.format_exc())
                raise

            # Add metadata
            prediction['weights_used'] = {
                'recent5': recent5_weight * 100,
                'current_season': current_season_weight * 100,
                'last_season': last_season_weight * 100
            }
        elif model_type == 'personal':
            logger.info(f"👤 Using personal (player ratings) model")
            # 개인 분석 - 선수 능력치 기반
            # 프론트엔드에서 player_ratings 전달 받음
            home_player_ratings = data.get('home_player_ratings', [])
            away_player_ratings = data.get('away_player_ratings', [])
            logger.info(f"🔍 Home player ratings count: {len(home_player_ratings)}")
            logger.info(f"🔍 Away player ratings count: {len(away_player_ratings)}")

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

            try:
                prediction = personal_predictor.predict_match(
                    home_player_ratings,
                    away_player_ratings,
                    home_advantage=1.3
                )
                logger.info(f"✅ Personal prediction successful: {prediction}")
            except Exception as pred_error:
                logger.error(f"❌ ERROR in personal prediction: {pred_error}")
                import traceback
                logger.error(traceback.format_exc())
                raise
        else:
            logger.info(f"🔀 Using hybrid model")
            logger.info(f"🔍 hybrid_predictor object: {hybrid_predictor}")
            # 하이브리드 - 새로운 HybridPredictor 사용
            try:
                prediction = hybrid_predictor.predict(
                    home_team, away_team,
                    stats_weight=stats_weight,
                    ml_weight=personal_weight,
                    features=features
                )
                logger.info(f"✅ Hybrid prediction successful: {prediction}")
            except Exception as pred_error:
                logger.error(f"❌ ERROR in hybrid prediction: {pred_error}")
                import traceback
                logger.error(traceback.format_exc())
                raise

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

        logger.info(f"📤 Final prediction to return: {prediction}")
        logger.info(f"✅ Prediction completed successfully!")
        logger.info("="*80 + "\n")

        return jsonify(prediction)

    except (ValidationError, NotFoundError, APIError):
        # Re-raise custom API errors to be handled by error handlers
        raise
    except Exception as e:
        logger.error(f"\n{'='*80}")
        logger.error(f"❌❌❌ CRITICAL ERROR in /api/predict ❌❌❌")
        logger.error(f"{'='*80}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error message: {str(e)}")
        logger.error(f"\nFull traceback:")
        import traceback
        logger.error(traceback.format_exc())
        logger.error(f"{'='*80}\n")

        # Raise as APIError for consistent error handling
        raise APIError(f"Prediction failed: {str(e)}", status_code=500)

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

@app.route('/api/predict/bayesian', methods=['POST'])
def predict_bayesian():
    """
    베이지안 Dixon-Coles 예측

    Body: {
        "home_team": "Manchester City",
        "away_team": "Liverpool",
        "n_sims": 3000,  // 시뮬레이션 횟수 (default: 3000)
        "credible_interval": 0.95,  // 신뢰구간 수준 (default: 0.95)
        "use_cached": true  // 캐시된 모델 사용 (default: true)
    }

    Returns:
    {
        "home_win": float,  // 승률 (%)
        "draw": float,
        "away_win": float,
        "expected_home_goals": float,  // 예상 득점
        "expected_away_goals": float,
        "credible_intervals": {  // 95% 신뢰구간
            "home_goals": [lower, upper],
            "away_goals": [lower, upper],
            "goal_difference": [lower, upper]
        },
        "top_scores": [{"score": "2-1", "probability": 7.5}, ...],
        "risk_metrics": {
            "var_95": float,  // Value at Risk (5%)
            "cvar_95": float,  // Conditional VaR
            "prediction_entropy": float  // 예측 불확실성 (낮을수록 확신)
        }
    }
    """
    global bayesian_model_cache

    try:
        from models.bayesian_dixon_coles_simplified import SimplifiedBayesianDixonColes

        data = request.json
        home_team = data.get('home_team')
        away_team = data.get('away_team')
        n_sims = data.get('n_sims', 3000)
        credible_interval = data.get('credible_interval', 0.95)
        use_cached = data.get('use_cached', True)

        # 캐시 확인 (학습된 모델 재사용)
        if use_cached and 'bayesian_model_cache' in globals() and bayesian_model_cache is not None:
            model = bayesian_model_cache
            print("Using cached Bayesian model")
        else:
            # 새로 학습
            print("Training new Bayesian Dixon-Coles model...")
            model = SimplifiedBayesianDixonColes(
                n_samples=2000,  # MCMC 샘플 수
                burnin=1000,     # Burn-in
                thin=2           # Thinning
            )

            # 허용된 시즌 데이터로 학습
            model.fit(historical_matches, verbose=False)

            # 캐시 저장 (다음 요청에서 재사용)
            bayesian_model_cache = model
            print("Bayesian model trained and cached")

        # 예측
        prediction = model.predict_match(
            home_team,
            away_team,
            n_sims=n_sims,
            credible_interval=credible_interval
        )

        # 메타데이터 추가
        prediction['model_info'] = {
            'type': 'Bayesian Dixon-Coles (Metropolis-Hastings MCMC)',
            'n_simulations': n_sims,
            'credible_interval': credible_interval * 100,
            'acceptance_rate': model.acceptance_rate * 100,
            'effective_samples': len(model.samples)
        }

        return jsonify(prediction)

    except Exception as e:
        import traceback
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@app.route('/api/bayesian/team-ratings', methods=['GET'])
def get_bayesian_team_ratings():
    """
    베이지안 모델의 팀 레이팅 조회 (신뢰구간 포함)

    Returns:
    [
        {
            "team": "Man City",
            "attack_mean": 0.45,
            "attack_ci_low": 0.32,
            "attack_ci_high": 0.58,
            "defense_mean": -0.12,
            "defense_ci_low": -0.28,
            "defense_ci_high": 0.04
        },
        ...
    ]
    """
    global bayesian_model_cache

    try:
        # 모델 캐시 확인
        if 'bayesian_model_cache' not in globals() or bayesian_model_cache is None:
            # 모델 학습
            from models.bayesian_dixon_coles_simplified import SimplifiedBayesianDixonColes
            model = SimplifiedBayesianDixonColes(n_samples=2000, burnin=1000, thin=2)
            model.fit(historical_matches, verbose=False)
            bayesian_model_cache = model
        else:
            model = bayesian_model_cache

        # 레이팅 가져오기
        ratings_df = model.get_team_ratings(credible_interval=0.95)

        return jsonify(ratings_df.to_dict(orient='records'))

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/bayesian/retrain', methods=['POST'])
def retrain_bayesian_model():
    """
    베이지안 모델 재학습 (데이터 업데이트 후 호출)

    Body: {
        "n_samples": 2000,  // optional
        "burnin": 1000,     // optional
        "thin": 2           // optional
    }
    """
    global bayesian_model_cache

    try:
        from models.bayesian_dixon_coles_simplified import SimplifiedBayesianDixonColes

        data = request.json or {}
        n_samples = data.get('n_samples', 2000)
        burnin = data.get('burnin', 1000)
        thin = data.get('thin', 2)

        print(f"Retraining Bayesian model (samples={n_samples}, burnin={burnin})...")

        model = SimplifiedBayesianDixonColes(
            n_samples=n_samples,
            burnin=burnin,
            thin=thin
        )
        model.fit(historical_matches, verbose=True)

        # 캐시 업데이트
        bayesian_model_cache = model

        return jsonify({
            'success': True,
            'message': 'Bayesian model retrained successfully',
            'model_info': {
                'acceptance_rate': model.acceptance_rate * 100,
                'effective_samples': len(model.samples),
                'n_teams': len(model.teams)
            }
        })

    except Exception as e:
        import traceback
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

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
    print("  POST /api/predict/bayesian          🆕 Bayesian prediction with uncertainty")
    print("  GET  /api/bayesian/team-ratings     🆕 Team ratings with credible intervals")
    print("  POST /api/bayesian/retrain          🆕 Retrain Bayesian model")

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
