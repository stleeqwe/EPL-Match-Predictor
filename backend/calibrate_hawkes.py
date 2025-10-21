"""
Hawkes Process Parameter Calibration
실제 EPL 경기 데이터를 사용하여 Hawkes parameters (μ, α, β) 최적화

Method: Maximum Likelihood Estimation (MLE)
- Negative log-likelihood를 최소화
- scipy.optimize.minimize 사용
"""

import sys
import os
import numpy as np
from typing import List, Tuple, Dict
from scipy.optimize import minimize

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)


# ==========================================================================
# Data Models
# ==========================================================================

class MatchData:
    """단일 경기 데이터"""
    def __init__(
        self,
        match_id: str,
        home_team: str,
        away_team: str,
        home_goals: int,
        away_goals: int,
        goal_times: List[Tuple[int, str]]  # [(minute, 'home'/'away'), ...]
    ):
        self.match_id = match_id
        self.home_team = home_team
        self.away_team = away_team
        self.home_goals = home_goals
        self.away_goals = away_goals
        self.goal_times = sorted(goal_times)  # Sort by time


# ==========================================================================
# Hawkes Negative Log-Likelihood
# ==========================================================================

def hawkes_log_likelihood(
    params: np.ndarray,
    goal_times: List[int],
    total_minutes: int = 90
) -> float:
    """
    Hawkes Process의 log-likelihood 계산

    Formula:
    log L = Σ log(λ(ti)) - ∫ λ(t) dt

    Args:
        params: [μ, α, β]
        goal_times: 득점 시각 리스트
        total_minutes: 경기 시간

    Returns:
        Log-likelihood (positive value, higher is better)
    """
    mu, alpha, beta = params

    # Parameter constraints
    if mu <= 0 or alpha <= 0 or beta <= 0:
        return -1e10  # Invalid

    if alpha >= 1.0:  # Stability condition
        return -1e10

    # Term 1: Σ log(λ(ti))
    log_intensity_sum = 0.0
    for i, ti in enumerate(goal_times):
        # λ(ti) = μ + Σ α·e^(-β(ti-tj)) for all tj < ti
        intensity = mu
        for tj in goal_times[:i]:
            time_diff = ti - tj
            if time_diff > 0:
                intensity += alpha * np.exp(-beta * time_diff)

        if intensity <= 0:
            return -1e10

        log_intensity_sum += np.log(intensity)

    # Term 2: ∫ λ(t) dt from 0 to T
    # ∫ λ(t) dt = μ·T + Σ (α/β)·(1 - e^(-β(T-ti)))
    integral = mu * total_minutes
    for ti in goal_times:
        integral += (alpha / beta) * (1 - np.exp(-beta * (total_minutes - ti)))

    log_likelihood = log_intensity_sum - integral
    return log_likelihood


def negative_log_likelihood(params: np.ndarray, matches: List[MatchData]) -> float:
    """
    Multiple matches에 대한 negative log-likelihood

    Args:
        params: [μ, α, β]
        matches: 경기 데이터 리스트

    Returns:
        Negative log-likelihood (minimize this)
    """
    total_nll = 0.0

    for match in matches:
        # 각 팀별로 분리해서 계산
        home_goal_times = [t for t, team in match.goal_times if team == 'home']
        away_goal_times = [t for t, team in match.goal_times if team == 'away']

        # Home team log-likelihood
        if len(home_goal_times) > 0:
            ll_home = hawkes_log_likelihood(params, home_goal_times)
            total_nll -= ll_home

        # Away team log-likelihood
        if len(away_goal_times) > 0:
            ll_away = hawkes_log_likelihood(params, away_goal_times)
            total_nll -= ll_away

    return total_nll


# ==========================================================================
# Calibration Functions
# ==========================================================================

def calibrate_hawkes_parameters(
    matches: List[MatchData],
    initial_guess: Tuple[float, float, float] = (0.03, 0.1, 0.3)
) -> Dict:
    """
    Hawkes parameters를 실제 데이터로 calibration

    Args:
        matches: 경기 데이터 리스트
        initial_guess: 초기값 (μ, α, β)

    Returns:
        {
            'mu': float,
            'alpha': float,
            'beta': float,
            'success': bool,
            'nll': float,
            'n_matches': int
        }
    """
    print(f"📊 Calibrating Hawkes parameters...")
    print(f"  Matches: {len(matches)}")
    print(f"  Initial guess: μ={initial_guess[0]:.4f}, α={initial_guess[1]:.4f}, β={initial_guess[2]:.4f}")

    # Bounds: μ ∈ (0.01, 0.1), α ∈ (0.01, 0.5), β ∈ (0.1, 1.0)
    bounds = [(0.01, 0.1), (0.01, 0.5), (0.1, 1.0)]

    # Optimize
    result = minimize(
        negative_log_likelihood,
        x0=initial_guess,
        args=(matches,),
        method='L-BFGS-B',
        bounds=bounds
    )

    mu_opt, alpha_opt, beta_opt = result.x

    print(f"\n✅ Calibration {'successful' if result.success else 'FAILED'}!")
    print(f"  Optimized parameters:")
    print(f"    μ (baseline):   {mu_opt:.4f} → {mu_opt * 90:.2f} goals/90min")
    print(f"    α (excitement): {alpha_opt:.4f}")
    print(f"    β (decay):      {beta_opt:.4f} → half-life {np.log(2)/beta_opt:.2f} min")
    print(f"  Negative log-likelihood: {result.fun:.2f}")

    return {
        'mu': mu_opt,
        'alpha': alpha_opt,
        'beta': beta_opt,
        'success': result.success,
        'nll': result.fun,
        'n_matches': len(matches),
        'half_life_minutes': np.log(2) / beta_opt
    }


# ==========================================================================
# Mock Data Generation (EPL 스타일)
# ==========================================================================

def generate_mock_epl_data(n_matches: int = 50, seed: int = 42) -> List[MatchData]:
    """
    EPL 스타일 mock data 생성 (실제 EPL 데이터 대신 사용)

    EPL 특성:
    - 평균 2.8골/경기
    - Momentum 효과 존재
    - High-scoring과 low-scoring 경기 혼합
    """
    np.random.seed(seed)
    matches = []

    teams = [
        'Arsenal', 'Liverpool', 'Man City', 'Chelsea', 'Man Utd',
        'Tottenham', 'Newcastle', 'Brighton', 'Aston Villa', 'West Ham'
    ]

    for i in range(n_matches):
        home_team = np.random.choice(teams)
        away_team = np.random.choice([t for t in teams if t != home_team])

        # Poisson 기반 득점 (EPL 평균 2.8골)
        home_goals = np.random.poisson(1.5)
        away_goals = np.random.poisson(1.3)

        # Goal times 생성 (momentum 효과 반영)
        goal_times = []

        # Home goals
        for _ in range(home_goals):
            if len(goal_times) > 0 and goal_times[-1][1] == 'home':
                # Momentum: 최근 골 근처에 배치 (5분 이내 확률 높음)
                if np.random.random() < 0.4:
                    last_time = goal_times[-1][0]
                    minute = min(89, last_time + np.random.randint(1, 6))
                else:
                    minute = np.random.randint(0, 90)
            else:
                minute = np.random.randint(0, 90)
            goal_times.append((minute, 'home'))

        # Away goals
        for _ in range(away_goals):
            if len(goal_times) > 0 and goal_times[-1][1] == 'away':
                # Momentum
                if np.random.random() < 0.4:
                    last_time = goal_times[-1][0]
                    minute = min(89, last_time + np.random.randint(1, 6))
                else:
                    minute = np.random.randint(0, 90)
            else:
                minute = np.random.randint(0, 90)
            goal_times.append((minute, 'away'))

        # Sort by time
        goal_times.sort()

        match = MatchData(
            match_id=f"EPL_MOCK_{i+1:03d}",
            home_team=home_team,
            away_team=away_team,
            home_goals=home_goals,
            away_goals=away_goals,
            goal_times=goal_times
        )
        matches.append(match)

    return matches


# ==========================================================================
# Validation
# ==========================================================================

def validate_calibration(params: Dict, test_matches: List[MatchData]):
    """
    Calibration 결과를 test set으로 검증

    Args:
        params: Calibrated parameters
        test_matches: Test 경기 데이터
    """
    print(f"\n📈 Validating calibration...")
    print(f"  Test matches: {len(test_matches)}")

    mu, alpha, beta = params['mu'], params['alpha'], params['beta']

    # Test set에 대한 negative log-likelihood
    test_nll = negative_log_likelihood([mu, alpha, beta], test_matches)
    avg_nll = test_nll / len(test_matches)

    print(f"  Test NLL: {test_nll:.2f}")
    print(f"  Avg NLL per match: {avg_nll:.2f}")

    # Baseline (μ만 사용)과 비교
    baseline_nll = negative_log_likelihood([mu, 0.0001, 1.0], test_matches)

    print(f"\n  Comparison:")
    print(f"    Hawkes NLL:   {test_nll:.2f}")
    print(f"    Baseline NLL: {baseline_nll:.2f}")
    print(f"    Improvement:  {baseline_nll - test_nll:.2f}")

    if test_nll < baseline_nll:
        print(f"  ✅ Hawkes model is better than baseline!")
    else:
        print(f"  ⚠️  Hawkes model is not better than baseline")


# ==========================================================================
# Main
# ==========================================================================

def main():
    """Calibration 실행"""
    print("=" * 70)
    print("🔬 Hawkes Process Parameter Calibration")
    print("=" * 70)

    # 1. Mock data 생성 (실제로는 EPL database에서 로드)
    print("\n📦 Generating mock EPL data...")
    all_matches = generate_mock_epl_data(n_matches=100, seed=42)

    # Statistics
    total_goals = sum(m.home_goals + m.away_goals for m in all_matches)
    avg_goals = total_goals / len(all_matches)
    print(f"  Total goals: {total_goals}")
    print(f"  Average goals per match: {avg_goals:.2f}")

    # 2. Train/Test split (80/20)
    split_idx = int(len(all_matches) * 0.8)
    train_matches = all_matches[:split_idx]
    test_matches = all_matches[split_idx:]

    print(f"  Train: {len(train_matches)} matches")
    print(f"  Test:  {len(test_matches)} matches")

    # 3. Calibration
    print(f"\n" + "=" * 70)
    result = calibrate_hawkes_parameters(
        train_matches,
        initial_guess=(0.03, 0.1, 0.3)
    )

    # 4. Validation
    print(f"\n" + "=" * 70)
    validate_calibration(result, test_matches)

    # 5. 결과 저장 (실제로는 config file에 저장)
    print(f"\n" + "=" * 70)
    print(f"💾 Calibrated Parameters:")
    print(f"=" * 70)
    print(f"\nUpdate hawkes_model.py with these values:")
    print(f"""
    def __init__(
        self,
        mu: float = {result['mu']:.4f},    # Calibrated from EPL data
        alpha: float = {result['alpha']:.4f},  # Calibrated from EPL data
        beta: float = {result['beta']:.4f}     # Calibrated from EPL data
    ):
""")

    print(f"\n✅ Calibration complete!")
    print(f"\n📝 Next steps:")
    print(f"   1. Replace mock data with real EPL match data")
    print(f"   2. Update HawkesGoalModel with calibrated parameters")
    print(f"   3. Re-run integration tests to verify")


if __name__ == "__main__":
    main()
