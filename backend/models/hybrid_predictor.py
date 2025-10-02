"""
하이브리드 예측 모델
Dixon-Coles + XGBoost 앙상블
"""

import numpy as np
from typing import Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HybridPredictor:
    def __init__(self, dixon_coles_model, xgboost_model=None):
        """
        Args:
            dixon_coles_model: DixonColesModel 인스턴스
            xgboost_model: XGBoostPredictor 인스턴스 (선택)
        """
        self.dixon_coles = dixon_coles_model
        self.xgboost = xgboost_model

    def predict(self, home_team: str, away_team: str,
                stats_weight: float = 0.7,
                ml_weight: float = 0.3,
                features: Dict = None) -> Dict:
        """
        하이브리드 예측

        Args:
            home_team: 홈팀명
            away_team: 원정팀명
            stats_weight: Dixon-Coles 가중치 (0~1)
            ml_weight: XGBoost 가중치 (0~1)
            features: 경기 특징 (XGBoost용)

        Returns:
            dict: 예측 결과
        """
        # 가중치 정규화
        total_weight = stats_weight + ml_weight
        if total_weight > 0:
            stats_weight /= total_weight
            ml_weight /= total_weight
        else:
            stats_weight = 0.7
            ml_weight = 0.3

        # Dixon-Coles 예측
        dc_prediction = self.dixon_coles.predict_match(home_team, away_team)

        logger.info(f"Dixon-Coles prediction: Home {dc_prediction['home_win']:.1f}% / Draw {dc_prediction['draw']:.1f}% / Away {dc_prediction['away_win']:.1f}%")

        # XGBoost가 사용 가능한 경우
        if self.xgboost and self.xgboost.model is not None and features:
            try:
                xgb_prediction = self.xgboost.predict(features)
                logger.info(f"XGBoost prediction: Home {xgb_prediction['home_win']:.1f}% / Draw {xgb_prediction['draw']:.1f}% / Away {xgb_prediction['away_win']:.1f}%")

                # 가중 평균
                hybrid_prediction = {
                    'home_win': dc_prediction['home_win'] * stats_weight + xgb_prediction['home_win'] * ml_weight,
                    'draw': dc_prediction['draw'] * stats_weight + xgb_prediction['draw'] * ml_weight,
                    'away_win': dc_prediction['away_win'] * stats_weight + xgb_prediction['away_win'] * ml_weight,
                    'expected_home_goals': dc_prediction['expected_home_goals'],
                    'expected_away_goals': dc_prediction['expected_away_goals'],
                    'top_scores': dc_prediction.get('top_scores', []),
                    'model_blend': {
                        'dixon_coles_weight': stats_weight * 100,
                        'xgboost_weight': ml_weight * 100
                    }
                }

                logger.info(f"Hybrid prediction: Home {hybrid_prediction['home_win']:.1f}% / Draw {hybrid_prediction['draw']:.1f}% / Away {hybrid_prediction['away_win']:.1f}%")
                return hybrid_prediction

            except Exception as e:
                logger.warning(f"XGBoost prediction failed, using Dixon-Coles only: {e}")

        # XGBoost 사용 불가능한 경우 Dixon-Coles만 사용
        logger.info("Using Dixon-Coles only (XGBoost not available)")
        dc_prediction['model_blend'] = {
            'dixon_coles_weight': 100.0,
            'xgboost_weight': 0.0
        }
        return dc_prediction

    def predict_with_temporal_weights(self, home_team: str, away_team: str,
                                     recent5_weight: float = 0.5,
                                     current_season_weight: float = 0.35,
                                     last_season_weight: float = 0.15) -> Dict:
        """
        시간 가중치를 적용한 예측

        Args:
            home_team: 홈팀명
            away_team: 원정팀명
            recent5_weight: 최근 5경기 가중치
            current_season_weight: 현 시즌 가중치
            last_season_weight: 지난 시즌 가중치

        Returns:
            dict: 예측 결과
        """
        # 현재는 Dixon-Coles의 시간 감쇠(xi)가 자동으로 적용되므로
        # 추가적인 시간 가중치는 메타데이터로만 저장
        prediction = self.dixon_coles.predict_match(home_team, away_team)

        prediction['temporal_weights'] = {
            'recent5': recent5_weight * 100,
            'current_season': current_season_weight * 100,
            'last_season': last_season_weight * 100
        }

        return prediction

    def predict_with_squad_analysis(self, home_team: str, away_team: str,
                                   home_squad_strength: float = 1.0,
                                   away_squad_strength: float = 1.0) -> Dict:
        """
        스쿼드 분석을 반영한 예측

        Args:
            home_team: 홈팀명
            away_team: 원정팀명
            home_squad_strength: 홈팀 전력 계수 (0.5~1.5)
            away_squad_strength: 원정팀 전력 계수 (0.5~1.5)

        Returns:
            dict: 예측 결과
        """
        # 기본 예측
        prediction = self.dixon_coles.predict_match(home_team, away_team)

        # 스쿼드 전력에 따라 예상 득점 조정
        prediction['expected_home_goals'] *= home_squad_strength
        prediction['expected_away_goals'] *= away_squad_strength

        # 승무패 확률 재계산 (간단한 휴리스틱)
        goal_diff = prediction['expected_home_goals'] - prediction['expected_away_goals']

        if goal_diff > 0.5:
            # 홈팀 유리
            prediction['home_win'] += min(10, goal_diff * 5)
            prediction['draw'] -= min(5, goal_diff * 2.5)
            prediction['away_win'] -= min(5, goal_diff * 2.5)
        elif goal_diff < -0.5:
            # 원정팀 유리
            prediction['away_win'] += min(10, abs(goal_diff) * 5)
            prediction['draw'] -= min(5, abs(goal_diff) * 2.5)
            prediction['home_win'] -= min(5, abs(goal_diff) * 2.5)

        # 확률 정규화
        total = prediction['home_win'] + prediction['draw'] + prediction['away_win']
        prediction['home_win'] = (prediction['home_win'] / total) * 100
        prediction['draw'] = (prediction['draw'] / total) * 100
        prediction['away_win'] = (prediction['away_win'] / total) * 100

        prediction['squad_adjustments'] = {
            'home_strength': home_squad_strength,
            'away_strength': away_squad_strength
        }

        return prediction


if __name__ == "__main__":
    # 테스트
    from dixon_coles import DixonColesModel
    import pandas as pd

    # 더미 데이터로 모델 학습
    matches = pd.DataFrame({
        'date': pd.date_range(start='2024-08-01', periods=20, freq='D'),
        'home_team': ['Manchester City', 'Arsenal', 'Liverpool'] * 7,
        'away_team': ['Arsenal', 'Liverpool', 'Manchester City'] * 7,
        'home_score': [2, 1, 2, 1, 2, 3, 2] * 3,
        'away_score': [1, 1, 1, 0, 1, 1, 2] * 3,
    })

    dc_model = DixonColesModel()
    dc_model.fit(matches[:20])

    hybrid = HybridPredictor(dc_model)

    # 예측 테스트
    print("=== Hybrid Prediction Test ===")
    prediction = hybrid.predict('Manchester City', 'Liverpool', stats_weight=0.7, ml_weight=0.3)
    print(f"Home win: {prediction['home_win']:.1f}%")
    print(f"Draw: {prediction['draw']:.1f}%")
    print(f"Away win: {prediction['away_win']:.1f}%")
