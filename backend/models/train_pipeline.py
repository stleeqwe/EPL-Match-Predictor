"""
모델 학습 파이프라인
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import pandas as pd
import numpy as np
from dixon_coles import DixonColesModel
from xgboost_model import XGBoostPredictor
from feature_engineering import FeatureEngineer

def prepare_training_data(matches_df):
    """
    학습 데이터 준비

    Args:
        matches_df: 경기 데이터

    Returns:
        X, y: 특징과 라벨
    """
    feature_engineer = FeatureEngineer()

    # Pi-ratings 계산
    feature_engineer.calculate_pi_ratings(matches_df)

    X_list = []
    y_list = []

    # 각 경기에 대해 특징 생성
    for idx, match in matches_df.iterrows():
        # 완료된 경기만
        if pd.isna(match['home_score']):
            continue

        home_team = match['home_team']
        away_team = match['away_team']

        # 특징 생성
        features = feature_engineer.create_match_features(
            home_team, away_team, matches_df[:idx]  # 과거 데이터만 사용
        )

        X_list.append(features)

        # 라벨 생성 (0: away_win, 1: draw, 2: home_win)
        if match['home_score'] > match['away_score']:
            y_list.append(2)
        elif match['home_score'] < match['away_score']:
            y_list.append(0)
        else:
            y_list.append(1)

    X = pd.DataFrame(X_list)
    y = np.array(y_list)

    return X, y

def train_models():
    """모든 모델 학습"""
    print("=" * 60)
    print("Starting model training pipeline")
    print("=" * 60)

    # 더미 데이터 생성 (실제로는 DB에서 가져오기)
    matches_df = pd.DataFrame({
        'date': pd.date_range(start='2024-01-01', periods=100, freq='3D'),
        'home_team': np.random.choice(['Manchester City', 'Arsenal', 'Liverpool', 'Tottenham', 'Chelsea'], 100),
        'away_team': np.random.choice(['Manchester City', 'Arsenal', 'Liverpool', 'Tottenham', 'Chelsea'], 100),
        'home_score': np.random.randint(0, 5, 100),
        'away_score': np.random.randint(0, 4, 100),
        'home_xg': np.random.uniform(0.5, 3.5, 100),
        'away_xg': np.random.uniform(0.5, 3.0, 100)
    })

    # 같은 팀끼리 경기하는 경우 제거
    matches_df = matches_df[matches_df['home_team'] != matches_df['away_team']]

    print(f"\nTotal matches: {len(matches_df)}")

    # 1. Dixon-Coles 모델 학습
    print("\n" + "=" * 60)
    print("1. Training Dixon-Coles Model")
    print("=" * 60)

    dc_model = DixonColesModel()
    dc_model.fit(matches_df)

    print("\n=== Dixon-Coles Parameters ===")
    print(f"Home Advantage: {dc_model.home_advantage:.3f}")
    print(f"Rho: {dc_model.rho:.3f}")

    # 2. 특징 준비
    print("\n" + "=" * 60)
    print("2. Preparing Features for XGBoost")
    print("=" * 60)

    X, y = prepare_training_data(matches_df)
    print(f"Features shape: {X.shape}")
    print(f"Labels shape: {y.shape}")
    print(f"\nLabel distribution:")
    print(f"  Away Win: {(y == 0).sum()} ({(y == 0).sum() / len(y) * 100:.1f}%)")
    print(f"  Draw: {(y == 1).sum()} ({(y == 1).sum() / len(y) * 100:.1f}%)")
    print(f"  Home Win: {(y == 2).sum()} ({(y == 2).sum() / len(y) * 100:.1f}%)")

    # 3. XGBoost 모델 학습
    print("\n" + "=" * 60)
    print("3. Training XGBoost Model")
    print("=" * 60)

    xgb_model = XGBoostPredictor(model_path='../models/xgboost_model.pkl')

    # 특징 준비
    X_scaled = xgb_model.prepare_features(X)

    # 학습
    results = xgb_model.train(X_scaled, y)

    # 모델 저장
    if results and 'error' not in results:
        xgb_model.save_model()

    print("\n" + "=" * 60)
    print("Training pipeline completed!")
    print("=" * 60)

    return dc_model, xgb_model

if __name__ == "__main__":
    train_models()
