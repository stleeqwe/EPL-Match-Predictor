"""
앙상블 모델 (Ensemble Model)
여러 예측 모델의 결과를 결합하여 더 안정적인 예측 생성

지원 모델:
- Dixon-Coles (통계적)
- Random Forest (머신러닝)
- XGBoost (그래디언트 부스팅)
- CatBoost (범주형 변수 특화)

앙상블 방법:
- Weighted Average (가중 평균)
- Stacking (메타 모델)
- Voting (다수결)
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EnsemblePredictor:
    """
    앙상블 예측 모델

    여러 모델의 예측 결과를 결합
    """

    def __init__(self, ensemble_method='weighted_average'):
        """
        Args:
            ensemble_method: 앙상블 방법
                - 'weighted_average': 가중 평균
                - 'simple_average': 단순 평균
                - 'voting': 다수결
        """
        self.ensemble_method = ensemble_method
        self.model_weights = {
            'dixon_coles': 0.3,
            'random_forest': 0.2,
            'xgboost': 0.25,
            'catboost': 0.25
        }

    def set_weights(self, weights: Dict[str, float]):
        """
        모델 가중치 설정

        Args:
            weights: 모델별 가중치 딕셔너리
                {'dixon_coles': 0.3, 'xgboost': 0.4, 'catboost': 0.3}
        """
        # 가중치 정규화 (합 = 1)
        total = sum(weights.values())
        self.model_weights = {k: v/total for k, v in weights.items()}

        logger.info("Updated model weights:")
        for model, weight in self.model_weights.items():
            logger.info(f"  {model}: {weight:.3f}")

    def predict_weighted_average(self, model_predictions: Dict[str, Dict]) -> Dict:
        """
        가중 평균 앙상블

        Args:
            model_predictions: 모델별 예측 결과
                {
                    'dixon_coles': {'home_win': 50, 'draw': 30, 'away_win': 20},
                    'xgboost': {'home_win': 45, 'draw': 35, 'away_win': 20},
                    ...
                }

        Returns:
            dict: 앙상블 예측 결과
        """
        ensemble_result = {
            'home_win': 0.0,
            'draw': 0.0,
            'away_win': 0.0
        }

        total_weight = 0

        for model_name, prediction in model_predictions.items():
            weight = self.model_weights.get(model_name, 0)

            if weight > 0:
                ensemble_result['home_win'] += prediction['home_win'] * weight
                ensemble_result['draw'] += prediction['draw'] * weight
                ensemble_result['away_win'] += prediction['away_win'] * weight
                total_weight += weight

        # 정규화 (가중치 합으로 나눔)
        if total_weight > 0:
            for key in ensemble_result:
                ensemble_result[key] /= total_weight

        return ensemble_result

    def predict_simple_average(self, model_predictions: Dict[str, Dict]) -> Dict:
        """
        단순 평균 앙상블

        Args:
            model_predictions: 모델별 예측 결과

        Returns:
            dict: 앙상블 예측 결과
        """
        ensemble_result = {
            'home_win': 0.0,
            'draw': 0.0,
            'away_win': 0.0
        }

        n_models = len(model_predictions)

        for prediction in model_predictions.values():
            ensemble_result['home_win'] += prediction['home_win']
            ensemble_result['draw'] += prediction['draw']
            ensemble_result['away_win'] += prediction['away_win']

        # 평균
        for key in ensemble_result:
            ensemble_result[key] /= n_models

        return ensemble_result

    def predict_voting(self, model_predictions: Dict[str, Dict]) -> Dict:
        """
        다수결 앙상블

        각 모델의 가장 높은 확률 클래스를 투표

        Args:
            model_predictions: 모델별 예측 결과

        Returns:
            dict: 앙상블 예측 결과
        """
        votes = {
            'home_win': 0,
            'draw': 0,
            'away_win': 0
        }

        for model_name, prediction in model_predictions.items():
            # 가장 높은 확률 클래스 찾기
            predicted_class = max(prediction, key=prediction.get)

            # 투표 (가중치 적용)
            weight = self.model_weights.get(model_name, 1)
            votes[predicted_class] += weight

        # 투표 결과를 확률로 변환
        total_votes = sum(votes.values())

        ensemble_result = {
            key: (vote / total_votes * 100) if total_votes > 0 else 0
            for key, vote in votes.items()
        }

        return ensemble_result

    def predict(self, model_predictions: Dict[str, Dict]) -> Dict:
        """
        앙상블 예측

        Args:
            model_predictions: 모델별 예측 결과

        Returns:
            dict: 앙상블 예측 결과 + 메타 정보
        """
        # 앙상블 방법에 따라 예측
        if self.ensemble_method == 'weighted_average':
            result = self.predict_weighted_average(model_predictions)
        elif self.ensemble_method == 'simple_average':
            result = self.predict_simple_average(model_predictions)
        elif self.ensemble_method == 'voting':
            result = self.predict_voting(model_predictions)
        else:
            raise ValueError(f"Unknown ensemble method: {self.ensemble_method}")

        # 메타 정보 추가
        result['ensemble_method'] = self.ensemble_method
        result['model_count'] = len(model_predictions)
        result['models_used'] = list(model_predictions.keys())

        # 확률 합 = 100% 확인
        total_prob = result['home_win'] + result['draw'] + result['away_win']
        if not (99.9 <= total_prob <= 100.1):
            logger.warning(f"Probability sum: {total_prob}% (expected 100%)")

        # 모델 간 분산 계산 (예측 불확실성 지표)
        home_win_probs = [p['home_win'] for p in model_predictions.values()]
        draw_probs = [p['draw'] for p in model_predictions.values()]
        away_win_probs = [p['away_win'] for p in model_predictions.values()]

        result['uncertainty'] = {
            'home_win_std': float(np.std(home_win_probs)),
            'draw_std': float(np.std(draw_probs)),
            'away_win_std': float(np.std(away_win_probs)),
            'avg_std': float(np.mean([np.std(home_win_probs), np.std(draw_probs), np.std(away_win_probs)]))
        }

        return result

    def optimize_weights(self, predictions_history: List[Dict], actuals: List[str]) -> Dict[str, float]:
        """
        과거 예측 데이터 기반 최적 가중치 학습

        Args:
            predictions_history: 과거 예측 기록
                [
                    {
                        'dixon_coles': {'home_win': 50, ...},
                        'xgboost': {'home_win': 45, ...},
                        ...
                    },
                    ...
                ]
            actuals: 실제 결과 리스트
                ['home_win', 'draw', 'away_win', ...]

        Returns:
            dict: 최적 가중치
        """
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from evaluation.metrics import ranked_probability_score

        # 모델 리스트 추출
        model_names = list(predictions_history[0].keys())

        # 최적화 목표: RPS 최소화
        best_weights = None
        best_rps = float('inf')

        # Grid search for weights
        weight_candidates = np.linspace(0, 1, 11)  # 0.0, 0.1, ..., 1.0

        # 간단한 그리드 서치 (3개 모델 가정)
        for w1 in weight_candidates:
            for w2 in weight_candidates:
                w3 = 1 - w1 - w2
                if w3 < 0:
                    continue

                weights = {
                    model_names[0]: w1,
                    model_names[1]: w2,
                    model_names[2] if len(model_names) > 2 else model_names[0]: w3
                }

                # 앙상블 예측
                ensemble_preds = []
                for pred_dict in predictions_history:
                    ensemble_pred = self.predict_weighted_average(pred_dict)
                    ensemble_preds.append(ensemble_pred)

                # 평가
                try:
                    # 실제 결과를 숫자로 변환
                    result_to_class = {'away_win': 0, 'draw': 1, 'home_win': 2}
                    y_true = np.array([result_to_class[r] for r in actuals])

                    # 예측 확률 배열 생성
                    y_pred = np.array([
                        [p['away_win']/100, p['draw']/100, p['home_win']/100]
                        for p in ensemble_preds
                    ])

                    rps = ranked_probability_score(y_true, y_pred)

                    if rps < best_rps:
                        best_rps = rps
                        best_weights = weights.copy()

                except Exception as e:
                    continue

        if best_weights:
            logger.info(f"Optimized weights (RPS: {best_rps:.4f}):")
            for model, weight in best_weights.items():
                logger.info(f"  {model}: {weight:.3f}")

            self.set_weights(best_weights)

        return best_weights


if __name__ == "__main__":
    # 테스트
    logger.info("=" * 60)
    logger.info("Ensemble Model Test")
    logger.info("=" * 60)

    # 더미 예측 데이터
    model_predictions = {
        'dixon_coles': {
            'home_win': 52.0,
            'draw': 28.0,
            'away_win': 20.0
        },
        'random_forest': {
            'home_win': 48.0,
            'draw': 30.0,
            'away_win': 22.0
        },
        'xgboost': {
            'home_win': 50.0,
            'draw': 29.0,
            'away_win': 21.0
        },
        'catboost': {
            'home_win': 51.0,
            'draw': 27.0,
            'away_win': 22.0
        }
    }

    logger.info("\nIndividual Model Predictions:")
    for model, pred in model_predictions.items():
        logger.info(f"  {model}: H={pred['home_win']:.1f}% D={pred['draw']:.1f}% A={pred['away_win']:.1f}%")

    # 1. Weighted Average Ensemble
    logger.info("\n" + "=" * 60)
    logger.info("1. Weighted Average Ensemble")
    logger.info("=" * 60)

    ensemble_wa = EnsemblePredictor(ensemble_method='weighted_average')
    result_wa = ensemble_wa.predict(model_predictions)

    logger.info(f"Result: H={result_wa['home_win']:.1f}% D={result_wa['draw']:.1f}% A={result_wa['away_win']:.1f}%")
    logger.info(f"Uncertainty: {result_wa['uncertainty']['avg_std']:.2f}%")

    # 2. Simple Average Ensemble
    logger.info("\n" + "=" * 60)
    logger.info("2. Simple Average Ensemble")
    logger.info("=" * 60)

    ensemble_sa = EnsemblePredictor(ensemble_method='simple_average')
    result_sa = ensemble_sa.predict(model_predictions)

    logger.info(f"Result: H={result_sa['home_win']:.1f}% D={result_sa['draw']:.1f}% A={result_sa['away_win']:.1f}%")

    # 3. Voting Ensemble
    logger.info("\n" + "=" * 60)
    logger.info("3. Voting Ensemble")
    logger.info("=" * 60)

    ensemble_v = EnsemblePredictor(ensemble_method='voting')
    result_v = ensemble_v.predict(model_predictions)

    logger.info(f"Result: H={result_v['home_win']:.1f}% D={result_v['draw']:.1f}% A={result_v['away_win']:.1f}%")

    # 4. Custom Weights
    logger.info("\n" + "=" * 60)
    logger.info("4. Custom Weights Ensemble")
    logger.info("=" * 60)

    ensemble_custom = EnsemblePredictor(ensemble_method='weighted_average')
    ensemble_custom.set_weights({
        'dixon_coles': 0.4,  # 통계 모델에 높은 가중치
        'xgboost': 0.3,
        'catboost': 0.3
    })

    result_custom = ensemble_custom.predict(model_predictions)

    logger.info(f"Result: H={result_custom['home_win']:.1f}% D={result_custom['draw']:.1f}% A={result_custom['away_win']:.1f}%")

    # 불확실성 분석
    logger.info("\n" + "=" * 60)
    logger.info("Uncertainty Analysis")
    logger.info("=" * 60)

    uncertainty = result_wa['uncertainty']
    logger.info(f"Home Win Std Dev: {uncertainty['home_win_std']:.2f}%")
    logger.info(f"Draw Std Dev: {uncertainty['draw_std']:.2f}%")
    logger.info(f"Away Win Std Dev: {uncertainty['away_win_std']:.2f}%")
    logger.info(f"Average Std Dev: {uncertainty['avg_std']:.2f}%")

    if uncertainty['avg_std'] < 2:
        logger.info("→ Low uncertainty: Models agree strongly")
    elif uncertainty['avg_std'] < 5:
        logger.info("→ Medium uncertainty: Some disagreement between models")
    else:
        logger.info("→ High uncertainty: Significant disagreement between models")

    logger.info("\n" + "=" * 60)
    logger.info("✅ Ensemble Model Test Complete")
    logger.info("=" * 60)
