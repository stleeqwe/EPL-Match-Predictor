"""
평가 메트릭 모듈
축구 경기 결과 예측 모델의 성능 평가

포함 메트릭:
- Ranked Probability Score (RPS): 순위형 확률 평가
- Brier Score: 다중 클래스 확률 정확도
- Log Loss: 확률 예측의 로그 손실
- ROC AUC: 클래스별 분류 성능
"""

import numpy as np
from sklearn.metrics import log_loss, roc_auc_score
from typing import List, Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def ranked_probability_score(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Ranked Probability Score (RPS) 계산

    축구 경기 결과 예측에 적합한 메트릭
    - 완전히 정확한 예측: RPS = 0
    - 완전히 틀린 예측: RPS = 1
    - 홈승/무/원정승은 순서가 있는 범주

    Args:
        y_true: 실제 결과 (0: 원정승, 1: 무승부, 2: 홈승)
        y_pred: 예측 확률 (N x 3 배열, 각 행은 [원정승, 무, 홈승] 확률)

    Returns:
        float: RPS 값 (0~1, 낮을수록 좋음)

    예시:
        실제 결과: 홈승 (클래스 2)
        예측: [0.2, 0.3, 0.5] (원정승 20%, 무 30%, 홈승 50%)

        누적 확률:
        - 실제: [0, 0, 1]
        - 예측: [0.2, 0.5, 1.0]

        RPS = (1/2) * [(0.2-0)^2 + (0.5-0)^2 + (1-1)^2]
            = (1/2) * [0.04 + 0.25 + 0]
            = 0.145
    """
    n_classes = y_pred.shape[1]
    n_samples = len(y_true)

    rps_sum = 0

    for i in range(n_samples):
        # 실제 결과를 one-hot 벡터로 변환
        true_class = int(y_true[i])
        y_true_onehot = np.zeros(n_classes)
        y_true_onehot[true_class] = 1

        # 누적 확률 계산
        cumulative_true = np.cumsum(y_true_onehot)
        cumulative_pred = np.cumsum(y_pred[i])

        # RPS 계산 (누적 확률 차이의 제곱합)
        rps = np.sum((cumulative_pred - cumulative_true) ** 2)
        rps_sum += rps

    # 정규화 (클래스 수 - 1로 나눔)
    rps_avg = rps_sum / (n_samples * (n_classes - 1))

    return rps_avg


def brier_score_multiclass(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    다중 클래스 Brier Score 계산

    확률 예측의 정확도를 측정
    - 완벽한 예측: Brier Score = 0
    - 최악의 예측: Brier Score = 2

    Args:
        y_true: 실제 결과 (0, 1, 2)
        y_pred: 예측 확률 (N x 3 배열)

    Returns:
        float: Brier Score (0~2, 낮을수록 좋음)

    예시:
        실제 결과: 홈승 (클래스 2)
        예측: [0.2, 0.3, 0.5]

        실제 one-hot: [0, 0, 1]
        Brier = (0.2-0)^2 + (0.3-0)^2 + (0.5-1)^2
              = 0.04 + 0.09 + 0.25
              = 0.38
    """
    n_classes = y_pred.shape[1]
    n_samples = len(y_true)

    brier_sum = 0

    for i in range(n_samples):
        # 실제 결과를 one-hot 벡터로 변환
        true_class = int(y_true[i])
        y_true_onehot = np.zeros(n_classes)
        y_true_onehot[true_class] = 1

        # Brier Score = (예측 확률 - 실제 확률)^2의 합
        brier = np.sum((y_pred[i] - y_true_onehot) ** 2)
        brier_sum += brier

    brier_avg = brier_sum / n_samples

    return brier_avg


def calculate_all_metrics(y_true: np.ndarray, y_pred: np.ndarray, class_names: List[str] = None) -> Dict[str, float]:
    """
    모든 평가 메트릭 계산

    Args:
        y_true: 실제 결과 (0, 1, 2)
        y_pred: 예측 확률 (N x 3 배열)
        class_names: 클래스 이름 리스트 (기본값: ['away_win', 'draw', 'home_win'])

    Returns:
        dict: 모든 메트릭 결과
    """
    if class_names is None:
        class_names = ['away_win', 'draw', 'home_win']

    metrics = {}

    # 1. Ranked Probability Score
    rps = ranked_probability_score(y_true, y_pred)
    metrics['rps'] = rps

    # 2. Brier Score
    brier = brier_score_multiclass(y_true, y_pred)
    metrics['brier_score'] = brier

    # 3. Log Loss
    try:
        ll = log_loss(y_true, y_pred, labels=[0, 1, 2])
        metrics['log_loss'] = ll
    except Exception as e:
        logger.warning(f"Log loss calculation failed: {e}")
        metrics['log_loss'] = None

    # 4. Accuracy (가장 높은 확률 클래스)
    y_pred_class = np.argmax(y_pred, axis=1)
    accuracy = np.mean(y_pred_class == y_true)
    metrics['accuracy'] = accuracy

    # 5. 클래스별 정확도
    for i, class_name in enumerate(class_names):
        class_mask = (y_true == i)
        if class_mask.sum() > 0:
            class_accuracy = np.mean(y_pred_class[class_mask] == i)
            metrics[f'accuracy_{class_name}'] = class_accuracy

    return metrics


def evaluate_predictions(predictions: List[Dict], actuals: List[Dict]) -> Dict:
    """
    예측 결과와 실제 결과 비교 평가

    Args:
        predictions: 예측 결과 리스트
            [{'home_win': 50, 'draw': 30, 'away_win': 20}, ...]
        actuals: 실제 결과 리스트
            [{'result': 'home_win'}, ...]

    Returns:
        dict: 평가 메트릭
    """
    n_samples = len(predictions)

    if n_samples != len(actuals):
        raise ValueError("Predictions and actuals must have the same length")

    # 데이터 변환
    y_true = []
    y_pred = []

    result_to_class = {
        'away_win': 0,
        'draw': 1,
        'home_win': 2
    }

    for pred, actual in zip(predictions, actuals):
        # 실제 결과
        actual_result = actual['result']
        y_true.append(result_to_class[actual_result])

        # 예측 확률 (% → 0~1)
        pred_probs = [
            pred.get('away_win', 0) / 100,
            pred.get('draw', 0) / 100,
            pred.get('home_win', 0) / 100
        ]
        y_pred.append(pred_probs)

    y_true = np.array(y_true)
    y_pred = np.array(y_pred)

    # 메트릭 계산
    metrics = calculate_all_metrics(y_true, y_pred)

    return metrics


def compare_models(model_predictions: Dict[str, List], actuals: List[Dict]) -> pd.DataFrame:
    """
    여러 모델의 성능 비교

    Args:
        model_predictions: 모델별 예측 결과
            {'dixon_coles': [...], 'ml': [...], 'ensemble': [...]}
        actuals: 실제 결과

    Returns:
        pd.DataFrame: 모델별 메트릭 비교 표
    """
    import pandas as pd

    results = []

    for model_name, predictions in model_predictions.items():
        metrics = evaluate_predictions(predictions, actuals)
        metrics['model'] = model_name
        results.append(metrics)

    df = pd.DataFrame(results)

    # 모델 컬럼을 첫 번째로 이동
    cols = ['model'] + [col for col in df.columns if col != 'model']
    df = df[cols]

    return df


if __name__ == "__main__":
    # 테스트
    logger.info("=" * 60)
    logger.info("Evaluation Metrics Test")
    logger.info("=" * 60)

    # 더미 데이터 생성
    np.random.seed(42)

    n_samples = 100

    # 실제 결과 (0: 원정승, 1: 무승부, 2: 홈승)
    y_true = np.random.randint(0, 3, n_samples)

    # 예측 확률 (랜덤)
    y_pred_random = np.random.dirichlet([1, 1, 1], n_samples)

    # 예측 확률 (약간 정확한 모델)
    y_pred_good = np.zeros((n_samples, 3))
    for i in range(n_samples):
        true_class = y_true[i]
        # 실제 클래스에 높은 확률 부여
        probs = np.random.dirichlet([1, 1, 1])
        probs[true_class] += 0.5
        probs /= probs.sum()
        y_pred_good[i] = probs

    logger.info("\n" + "=" * 60)
    logger.info("Random Model Evaluation")
    logger.info("=" * 60)
    metrics_random = calculate_all_metrics(y_true, y_pred_random)
    for metric, value in metrics_random.items():
        if value is not None:
            logger.info(f"{metric}: {value:.4f}")

    logger.info("\n" + "=" * 60)
    logger.info("Good Model Evaluation")
    logger.info("=" * 60)
    metrics_good = calculate_all_metrics(y_true, y_pred_good)
    for metric, value in metrics_good.items():
        if value is not None:
            logger.info(f"{metric}: {value:.4f}")

    logger.info("\n" + "=" * 60)
    logger.info("Metric Comparison")
    logger.info("=" * 60)
    logger.info(f"{'Metric':<20} {'Random':<12} {'Good':<12} {'Improvement':<12}")
    logger.info("-" * 60)

    for metric in ['rps', 'brier_score', 'log_loss', 'accuracy']:
        if metrics_random.get(metric) is not None:
            random_val = metrics_random[metric]
            good_val = metrics_good[metric]

            if metric == 'accuracy':
                improvement = good_val - random_val
                logger.info(f"{metric:<20} {random_val:<12.4f} {good_val:<12.4f} {improvement:+.4f}")
            else:
                improvement = random_val - good_val
                logger.info(f"{metric:<20} {random_val:<12.4f} {good_val:<12.4f} {improvement:+.4f}")

    # 실제 예측 데이터 형식 테스트
    logger.info("\n" + "=" * 60)
    logger.info("Real Prediction Format Test")
    logger.info("=" * 60)

    predictions = [
        {'home_win': 50, 'draw': 30, 'away_win': 20},
        {'home_win': 35, 'draw': 35, 'away_win': 30},
        {'home_win': 60, 'draw': 25, 'away_win': 15}
    ]

    actuals = [
        {'result': 'home_win'},
        {'result': 'draw'},
        {'result': 'home_win'}
    ]

    metrics_real = evaluate_predictions(predictions, actuals)

    logger.info("Prediction vs Actual:")
    for i, (pred, actual) in enumerate(zip(predictions, actuals)):
        logger.info(f"  Match {i+1}: {pred} → {actual['result']}")

    logger.info("\nMetrics:")
    for metric, value in metrics_real.items():
        if value is not None:
            logger.info(f"  {metric}: {value:.4f}")

    logger.info("\n" + "=" * 60)
    logger.info("✅ Evaluation Metrics Test Complete")
    logger.info("=" * 60)
