"""
CatBoost 모델 구현
범주형 변수에 강한 Gradient Boosting 알고리즘
"""

import numpy as np
import pandas as pd
from catboost import CatBoostClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FootballCatBoostModel:
    """
    CatBoost 기반 축구 경기 결과 예측 모델

    특징:
    - 범주형 변수 자동 처리 (팀명, 포지션 등)
    - GPU 가속 지원
    - Overfitting 방지 내장
    - Feature importance 분석
    """

    def __init__(self, use_gpu=False):
        """
        Args:
            use_gpu: GPU 사용 여부 (기본값 False)
        """
        self.model = CatBoostClassifier(
            iterations=500,
            learning_rate=0.03,
            depth=6,
            loss_function='MultiClass',
            eval_metric='MultiClass',
            task_type='GPU' if use_gpu else 'CPU',
            random_seed=42,
            verbose=False,
            early_stopping_rounds=50
        )

        self.label_encoder = LabelEncoder()
        self.feature_names = []
        self.categorical_features = []

    def prepare_features(self, match_data: pd.DataFrame) -> pd.DataFrame:
        """
        경기 데이터에서 피처 추출

        Args:
            match_data: 경기 데이터 DataFrame
                필수 컬럼: home_team, away_team, home_score, away_score
                선택 컬럼: home_xg, away_xg, home_possession, away_possession 등

        Returns:
            피처 DataFrame
        """
        features = pd.DataFrame()

        # 범주형 피처
        features['home_team'] = match_data['home_team']
        features['away_team'] = match_data['away_team']

        # 수치형 피처
        if 'home_xg' in match_data.columns:
            features['home_xg'] = match_data['home_xg'].fillna(0)
            features['away_xg'] = match_data['away_xg'].fillna(0)

        if 'home_possession' in match_data.columns:
            features['home_possession'] = match_data['home_possession'].fillna(50)
            features['away_possession'] = match_data['away_possession'].fillna(50)

        if 'home_shots' in match_data.columns:
            features['home_shots'] = match_data['home_shots'].fillna(0)
            features['away_shots'] = match_data['away_shots'].fillna(0)

        if 'home_shots_on_target' in match_data.columns:
            features['home_shots_on_target'] = match_data['home_shots_on_target'].fillna(0)
            features['away_shots_on_target'] = match_data['away_shots_on_target'].fillna(0)

        # 파생 피처
        if 'home_xg' in features.columns and 'away_xg' in features.columns:
            features['xg_diff'] = features['home_xg'] - features['away_xg']

        if 'home_possession' in features.columns:
            features['possession_diff'] = features['home_possession'] - features['away_possession']

        # 범주형 피처 리스트
        self.categorical_features = ['home_team', 'away_team']

        return features

    def prepare_labels(self, match_data: pd.DataFrame) -> np.ndarray:
        """
        경기 결과 레이블 생성

        Args:
            match_data: 경기 데이터 (home_score, away_score 필요)

        Returns:
            레이블 배열 (0: 원정승, 1: 무승부, 2: 홈승)
        """
        labels = []

        for _, row in match_data.iterrows():
            home_score = row['home_score']
            away_score = row['away_score']

            if home_score > away_score:
                labels.append('home_win')
            elif home_score < away_score:
                labels.append('away_win')
            else:
                labels.append('draw')

        # 레이블 인코딩
        encoded_labels = self.label_encoder.fit_transform(labels)

        return encoded_labels

    def fit(self, match_data: pd.DataFrame, validation_split=0.2):
        """
        모델 학습

        Args:
            match_data: 경기 데이터 DataFrame
            validation_split: 검증 데이터 비율
        """
        logger.info("Preparing features and labels...")

        # 피처 및 레이블 준비
        X = self.prepare_features(match_data)
        y = self.prepare_labels(match_data)

        self.feature_names = X.columns.tolist()

        # Train/Validation split
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=validation_split, random_state=42, stratify=y
        )

        logger.info(f"Training samples: {len(X_train)}, Validation samples: {len(X_val)}")
        logger.info(f"Categorical features: {self.categorical_features}")

        # 모델 학습
        self.model.fit(
            X_train,
            y_train,
            cat_features=self.categorical_features,
            eval_set=(X_val, y_val),
            verbose=False
        )

        # 학습 결과
        best_score = self.model.get_best_score()
        logger.info(f"Best validation score: {best_score}")

        # Feature importance
        feature_importance = self.model.get_feature_importance()
        importance_df = pd.DataFrame({
            'feature': self.feature_names,
            'importance': feature_importance
        }).sort_values('importance', ascending=False)

        logger.info("\nTop 10 Feature Importance:")
        logger.info(importance_df.head(10).to_string(index=False))

    def predict(self, home_team: str, away_team: str, **kwargs) -> dict:
        """
        경기 결과 예측

        Args:
            home_team: 홈팀 이름
            away_team: 원정팀 이름
            **kwargs: 추가 피처 (home_xg, away_xg, home_possession 등)

        Returns:
            예측 결과 딕셔너리
        """
        # 입력 데이터 준비
        input_data = pd.DataFrame([{
            'home_team': home_team,
            'away_team': away_team,
            **kwargs
        }])

        # 피처 추출
        X = self.prepare_features(input_data)

        # 예측
        probabilities = self.model.predict_proba(X)[0]

        # 레이블별 확률 매핑
        label_to_prob = {}
        for label, prob in zip(self.label_encoder.classes_, probabilities):
            label_to_prob[label] = float(prob * 100)

        return {
            'home_win': label_to_prob.get('home_win', 0.0),
            'draw': label_to_prob.get('draw', 0.0),
            'away_win': label_to_prob.get('away_win', 0.0),
            'model_type': 'catboost'
        }

    def get_feature_importance(self) -> pd.DataFrame:
        """
        피처 중요도 반환

        Returns:
            피처 중요도 DataFrame
        """
        importance = self.model.get_feature_importance()

        return pd.DataFrame({
            'feature': self.feature_names,
            'importance': importance
        }).sort_values('importance', ascending=False)

    def save_model(self, filepath: str):
        """모델 저장"""
        self.model.save_model(filepath)
        logger.info(f"Model saved to {filepath}")

    def load_model(self, filepath: str):
        """모델 로드"""
        self.model.load_model(filepath)
        logger.info(f"Model loaded from {filepath}")


if __name__ == "__main__":
    # 테스트
    logger.info("=" * 60)
    logger.info("CatBoost Model Test")
    logger.info("=" * 60)

    # 더미 데이터 생성
    np.random.seed(42)

    teams = ['Man City', 'Arsenal', 'Liverpool', 'Chelsea', 'Tottenham',
             'Man United', 'Newcastle', 'Brighton', 'Aston Villa', 'West Ham']

    n_matches = 200

    match_data = pd.DataFrame({
        'home_team': np.random.choice(teams, n_matches),
        'away_team': np.random.choice(teams, n_matches),
        'home_score': np.random.randint(0, 5, n_matches),
        'away_score': np.random.randint(0, 5, n_matches),
        'home_xg': np.random.uniform(0.5, 3.0, n_matches),
        'away_xg': np.random.uniform(0.5, 3.0, n_matches),
        'home_possession': np.random.uniform(35, 65, n_matches),
        'away_possession': np.random.uniform(35, 65, n_matches),
        'home_shots': np.random.randint(5, 20, n_matches),
        'away_shots': np.random.randint(5, 20, n_matches)
    })

    # 같은 팀끼리 경기 제거
    match_data = match_data[match_data['home_team'] != match_data['away_team']].reset_index(drop=True)

    logger.info(f"\nTotal matches: {len(match_data)}")

    # 모델 학습
    model = FootballCatBoostModel(use_gpu=False)
    model.fit(match_data, validation_split=0.2)

    # 예측 테스트
    logger.info("\n" + "=" * 60)
    logger.info("Prediction Test: Man City vs Arsenal")
    logger.info("=" * 60)

    prediction = model.predict(
        home_team='Man City',
        away_team='Arsenal',
        home_xg=2.1,
        away_xg=1.3,
        home_possession=58,
        away_possession=42,
        home_shots=15,
        away_shots=10
    )

    logger.info(f"Home Win: {prediction['home_win']:.1f}%")
    logger.info(f"Draw: {prediction['draw']:.1f}%")
    logger.info(f"Away Win: {prediction['away_win']:.1f}%")

    # Feature Importance
    logger.info("\n" + "=" * 60)
    logger.info("Feature Importance")
    logger.info("=" * 60)
    logger.info(model.get_feature_importance().to_string(index=False))
