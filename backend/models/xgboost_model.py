"""
XGBoost 예측 모델
"""

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, log_loss, classification_report
from typing import Dict, Tuple
import pickle
import os

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except Exception as e:
    XGBOOST_AVAILABLE = False
    xgb = None
    print(f"Warning: XGBoost not available: {e}")
    print("Install libomp: brew install libomp")

class XGBoostPredictor:
    def __init__(self, model_path='models/xgboost_model.pkl'):
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = []
        self.model_path = model_path

        # 모델이 저장되어 있으면 로드
        if os.path.exists(model_path):
            self.load_model(model_path)

    def prepare_features(self, features_df: pd.DataFrame) -> np.ndarray:
        """특징 준비"""
        self.feature_names = features_df.columns.tolist()
        X = self.scaler.fit_transform(features_df)
        return X

    def train(self, X: np.ndarray, y: np.ndarray, early_stopping_rounds=50):
        """
        모델 학습 (y: 0=away_win, 1=draw, 2=home_win)

        Args:
            X: 특징 데이터
            y: 라벨 (0, 1, 2)
            early_stopping_rounds: Early stopping 라운드

        Returns:
            dict: 학습 결과
        """
        if not XGBOOST_AVAILABLE:
            print("XGBoost not available, skipping training")
            return {'error': 'XGBoost not available'}

        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        # XGBoost 모델 설정
        self.model = xgb.XGBClassifier(
            n_estimators=1000,
            max_depth=8,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            reg_alpha=1.0,
            reg_lambda=1.2,
            min_child_weight=3,
            gamma=0.1,
            random_state=42,
            n_jobs=-1,
            eval_metric='mlogloss'
        )

        # 학습 (XGBoost 2.x API)
        self.model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
            verbose=True
        )

        # 검증 세트 평가
        y_pred = self.model.predict(X_val)
        y_pred_proba = self.model.predict_proba(X_val)

        accuracy = accuracy_score(y_val, y_pred)
        logloss = log_loss(y_val, y_pred_proba)

        print(f"\n=== Training Results ===")
        print(f"Validation Accuracy: {accuracy:.4f}")
        print(f"Validation Log Loss: {logloss:.4f}")
        print(f"\n{classification_report(y_val, y_pred, target_names=['Away Win', 'Draw', 'Home Win'])}")

        # 특징 중요도
        feature_importance = pd.DataFrame({
            'feature': self.feature_names,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)

        print("\n=== Top 10 Feature Importance ===")
        print(feature_importance.head(10).to_string(index=False))

        return {
            'accuracy': accuracy,
            'log_loss': logloss,
            'feature_importance': feature_importance
        }

    def predict(self, features: Dict[str, float]) -> Dict[str, float]:
        """예측"""
        if self.model is None:
            # 더미 예측
            return {
                'home_win': 45.0,
                'draw': 25.0,
                'away_win': 30.0
            }

        # 특징을 올바른 순서로 배열
        X = np.array([[features.get(fname, 0.0) for fname in self.feature_names]])
        X_scaled = self.scaler.transform(X)
        probs = self.model.predict_proba(X_scaled)[0]

        return {
            'away_win': float(probs[0] * 100),
            'draw': float(probs[1] * 100),
            'home_win': float(probs[2] * 100)
        }

    def save_model(self, path=None):
        """모델 저장"""
        if path is None:
            path = self.model_path

        os.makedirs(os.path.dirname(path), exist_ok=True)

        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'feature_names': self.feature_names
        }

        with open(path, 'wb') as f:
            pickle.dump(model_data, f)

        print(f"Model saved to {path}")

    def load_model(self, path=None):
        """모델 로드"""
        if path is None:
            path = self.model_path

        if not os.path.exists(path):
            print(f"Model file not found: {path}")
            return False

        with open(path, 'rb') as f:
            model_data = pickle.load(f)

        self.model = model_data['model']
        self.scaler = model_data['scaler']
        self.feature_names = model_data['feature_names']

        print(f"Model loaded from {path}")
        return True
