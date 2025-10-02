"""
XGBoost 모델 학습 스크립트
DB에서 과거 경기 데이터를 로드하여 XGBoost 모델 학습
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.schema import Match, Team, init_db, get_session
from models.feature_engineering import FeatureEngineer
from models.xgboost_model import XGBoostPredictor
import pandas as pd
import numpy as np
import logging
import argparse

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class XGBoostTrainer:
    def __init__(self):
        # DB 연결
        db_path = os.path.join(os.path.dirname(__file__), '..', 'soccer_predictor.db')
        db_url = f'sqlite:///{os.path.abspath(db_path)}'
        engine = init_db(db_url)
        self.session = get_session(engine)

        # Feature Engineer
        self.feature_engineer = FeatureEngineer()

        # XGBoost Predictor
        model_path = os.path.join(os.path.dirname(__file__), '..', 'models', 'xgboost_model.pkl')
        self.xgb = XGBoostPredictor(model_path=model_path)

    def load_matches_from_db(self, seasons=None):
        """
        DB에서 완료된 경기 데이터 로드

        Args:
            seasons: 로드할 시즌 리스트 (예: ['2021-2022', '2022-2023'])

        Returns:
            pd.DataFrame: 경기 데이터
        """
        logger.info("Loading matches from database...")

        query = self.session.query(Match).filter(Match.status == 'completed')

        if seasons:
            query = query.filter(Match.season.in_(seasons))

        matches = query.all()

        data = []
        for match in matches:
            home_team = self.session.query(Team).filter_by(id=match.home_team_id).first()
            away_team = self.session.query(Team).filter_by(id=match.away_team_id).first()

            if home_team and away_team and match.home_score is not None and match.away_score is not None:
                data.append({
                    'date': match.match_date,
                    'season': match.season,
                    'home_team': home_team.name,
                    'away_team': away_team.name,
                    'home_score': match.home_score,
                    'away_score': match.away_score,
                    'home_xg': match.home_xg if match.home_xg else match.home_score,
                    'away_xg': match.away_xg if match.away_xg else match.away_score
                })

        df = pd.DataFrame(data)
        logger.info(f"Loaded {len(df)} completed matches")
        return df

    def prepare_training_data(self, matches_df, allowed_seasons=None):
        """
        학습 데이터 준비: Feature Engineering + 라벨 생성

        Args:
            matches_df: 경기 데이터 DataFrame
            allowed_seasons: 학습에 사용할 시즌 리스트

        Returns:
            X (np.ndarray): 특징 데이터
            y (np.ndarray): 라벨 (0=away_win, 1=draw, 2=home_win)
        """
        logger.info("Preparing training data...")

        # Pi-ratings 계산 (시즌 필터 적용)
        self.feature_engineer.calculate_pi_ratings(matches_df, allowed_seasons=allowed_seasons)

        features_list = []
        labels_list = []

        for idx, row in matches_df.iterrows():
            try:
                # 특징 생성 (시즌 필터 적용)
                features = self.feature_engineer.create_match_features(
                    row['home_team'],
                    row['away_team'],
                    matches_df[:idx],  # 이전 경기들만 사용 (미래 정보 누출 방지)
                    allowed_seasons=allowed_seasons
                )

                # 라벨 생성 (0=away_win, 1=draw, 2=home_win)
                if row['home_score'] > row['away_score']:
                    label = 2  # home_win
                elif row['home_score'] < row['away_score']:
                    label = 0  # away_win
                else:
                    label = 1  # draw

                features_list.append(features)
                labels_list.append(label)

            except Exception as e:
                logger.warning(f"Could not create features for match {idx}: {e}")
                continue

        # 특징을 DataFrame으로 변환
        features_df = pd.DataFrame(features_list)

        # NaN 처리
        features_df = features_df.fillna(0)

        logger.info(f"Created {len(features_df)} training samples with {len(features_df.columns)} features")

        # XGBoost 모델을 위한 특징 준비
        X = self.xgb.prepare_features(features_df)
        y = np.array(labels_list)

        logger.info(f"Feature shape: {X.shape}")
        logger.info(f"Label distribution: Home Win={np.sum(y==2)}, Draw={np.sum(y==1)}, Away Win={np.sum(y==0)}")

        return X, y

    def train(self, X, y):
        """
        XGBoost 모델 학습

        Args:
            X: 특징 데이터
            y: 라벨
        """
        logger.info("Training XGBoost model...")

        results = self.xgb.train(X, y, early_stopping_rounds=50)

        if 'error' in results:
            logger.error(f"Training failed: {results['error']}")
            return False

        logger.info(f"Training completed successfully!")
        logger.info(f"Validation Accuracy: {results['accuracy']:.4f}")
        logger.info(f"Validation Log Loss: {results['log_loss']:.4f}")

        # 모델 저장
        self.xgb.save_model()

        return True

    def close(self):
        """세션 종료"""
        self.session.close()


def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(description='Train XGBoost model for match prediction')
    parser.add_argument('--seasons', nargs='+', default=['2024-2025', '2025-2026'],
                        help='Seasons to use for training (default: 2024-2025, 2025-2026)')
    parser.add_argument('--output', default=None, help='Output path for trained model')
    args = parser.parse_args()

    logger.info("="*60)
    logger.info("XGBoost Model Training Pipeline")
    logger.info(f"Training with seasons: {args.seasons}")
    logger.info("="*60)

    trainer = XGBoostTrainer()

    try:
        # 1. DB에서 경기 데이터 로드
        matches_df = trainer.load_matches_from_db(seasons=args.seasons)

        if len(matches_df) == 0:
            logger.error("No match data found in database!")
            logger.error("Please run 'python scripts/collect_historical_data.py' first")
            return

        # 2. 학습 데이터 준비 (시즌 필터 적용)
        X, y = trainer.prepare_training_data(matches_df, allowed_seasons=args.seasons)

        if len(X) < 50:
            logger.warning(f"Only {len(X)} training samples available - this may not be enough for robust training")
            logger.warning("Consider collecting more historical data")

        # 3. 모델 학습
        success = trainer.train(X, y)

        if success:
            logger.info("\n" + "="*60)
            logger.info("✅ XGBoost model training completed successfully!")
            logger.info(f"Model saved to: {trainer.xgb.model_path}")
            logger.info("="*60)
        else:
            logger.error("\n" + "="*60)
            logger.error("❌ XGBoost model training failed!")
            logger.error("="*60)

    except Exception as e:
        logger.error(f"Error during training: {e}")
        raise
    finally:
        trainer.close()


if __name__ == "__main__":
    main()
