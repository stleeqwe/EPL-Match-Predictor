"""
시간 가중치 계산 유틸리티
Time-weighted Dixon-Coles를 위한 지수 감쇠 가중치
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta


def calculate_exponential_decay_weights(match_dates, xi=0.005, reference_date=None):
    """
    경기 날짜에 대한 지수 감쇠 가중치 계산

    Args:
        match_dates: 경기 날짜 리스트 (datetime 또는 pd.Timestamp)
        xi: 감쇠 파라미터 (기본값 0.005, 더 크면 최근 경기에 더 큰 가중치)
        reference_date: 기준 날짜 (기본값: 가장 최근 경기 날짜)

    Returns:
        numpy.array: 각 경기에 대한 가중치 (0~1 사이 값)

    공식:
        φ(t) = exp(-ξ × t)
        여기서 t는 기준 날짜로부터 경과한 일수
    """
    # 날짜를 pandas datetime으로 변환
    if isinstance(match_dates, pd.Series):
        dates = pd.to_datetime(match_dates)
    else:
        dates = pd.to_datetime(match_dates)

    # 기준 날짜 설정 (기본값: 가장 최근 경기)
    if reference_date is None:
        reference_date = dates.max()
    else:
        reference_date = pd.to_datetime(reference_date)

    # 경과 일수 계산 (TimedeltaIndex를 numpy 배열로 변환)
    days_ago = np.array((reference_date - dates).days)

    # 지수 감쇠 가중치 계산
    weights = np.exp(-xi * days_ago)

    return weights


def calculate_linear_decay_weights(match_dates, reference_date=None):
    """
    선형 감쇠 가중치 계산 (대안)

    Args:
        match_dates: 경기 날짜 리스트
        reference_date: 기준 날짜

    Returns:
        numpy.array: 선형 감쇠 가중치
    """
    if isinstance(match_dates, pd.Series):
        dates = pd.to_datetime(match_dates)
    else:
        dates = pd.to_datetime(match_dates)

    if reference_date is None:
        reference_date = dates.max()
    else:
        reference_date = pd.to_datetime(reference_date)

    days_ago = (reference_date - dates).dt.days
    max_days = days_ago.max()

    if max_days == 0:
        return np.ones(len(dates))

    # 선형 감쇠 (0~1 사이 값)
    weights = 1 - (days_ago / max_days)
    weights = np.maximum(weights, 0.1)  # 최소 가중치 0.1

    return weights


def get_optimal_xi(match_data, xi_range=(0.001, 0.01), steps=10):
    """
    최적의 xi 파라미터 찾기 (교차 검증 기반)

    Args:
        match_data: 경기 데이터 DataFrame (date, home_score, away_score 필요)
        xi_range: 탐색할 xi 범위
        steps: 탐색 스텝 수

    Returns:
        float: 최적 xi 값
    """
    from sklearn.model_selection import TimeSeriesSplit

    xi_values = np.linspace(xi_range[0], xi_range[1], steps)
    best_xi = xi_values[0]
    best_score = float('inf')

    tscv = TimeSeriesSplit(n_splits=3)

    for xi in xi_values:
        scores = []

        for train_idx, val_idx in tscv.split(match_data):
            train_data = match_data.iloc[train_idx]
            val_data = match_data.iloc[val_idx]

            # 가중치 계산
            weights = calculate_exponential_decay_weights(
                train_data['date'],
                xi=xi,
                reference_date=train_data['date'].max()
            )

            # 여기서는 간단히 가중치 분산을 평가 지표로 사용
            # 실제로는 Dixon-Coles 모델 성능으로 평가해야 함
            score = np.var(weights)
            scores.append(score)

        avg_score = np.mean(scores)

        if avg_score < best_score:
            best_score = avg_score
            best_xi = xi

    return best_xi


def apply_time_window(match_data, days=730, reference_date=None):
    """
    특정 기간 내의 경기만 필터링

    Args:
        match_data: 경기 데이터 DataFrame
        days: 포함할 과거 일수 (기본값 730일 = 2년)
        reference_date: 기준 날짜

    Returns:
        DataFrame: 필터링된 경기 데이터
    """
    if reference_date is None:
        reference_date = pd.Timestamp.now()
    else:
        reference_date = pd.to_datetime(reference_date)

    cutoff_date = reference_date - timedelta(days=days)

    filtered_data = match_data[
        pd.to_datetime(match_data['date']) >= cutoff_date
    ].copy()

    return filtered_data


if __name__ == "__main__":
    # 테스트 예제
    print("=" * 60)
    print("Time Weighting Utility Test")
    print("=" * 60)

    # 샘플 경기 날짜 생성
    reference = pd.Timestamp('2024-10-02')
    dates = pd.date_range(
        start=reference - timedelta(days=365),
        end=reference,
        freq='7D'  # 매주
    )

    print(f"\n총 경기 수: {len(dates)}")
    print(f"기간: {dates[0].date()} ~ {dates[-1].date()}")

    # 지수 감쇠 가중치 계산
    weights_exp = calculate_exponential_decay_weights(dates, xi=0.005)

    print(f"\n지수 감쇠 가중치 (xi=0.005):")
    print(f"  최소: {weights_exp.min():.4f}")
    print(f"  최대: {weights_exp.max():.4f}")
    print(f"  평균: {weights_exp.mean():.4f}")

    # 최근 5경기 vs 1년 전 5경기 비교
    print(f"\n최근 5경기 평균 가중치: {weights_exp[-5:].mean():.4f}")
    print(f"1년 전 5경기 평균 가중치: {weights_exp[:5].mean():.4f}")
    print(f"가중치 비율: {weights_exp[-5:].mean() / weights_exp[:5].mean():.2f}배")

    # 다양한 xi 값 비교
    print(f"\nxi 파라미터에 따른 최신/최구 가중치 비율:")
    for xi in [0.001, 0.003, 0.005, 0.01, 0.02]:
        w = calculate_exponential_decay_weights(dates, xi=xi)
        ratio = w[-1] / w[0]
        print(f"  xi={xi:.3f}: {ratio:.2f}배")
