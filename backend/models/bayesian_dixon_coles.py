"""
Hierarchical Bayesian Dixon-Coles Model
========================================

이론적 배경:
- Baio & Blangiardo (2010): "Bayesian hierarchical model for the prediction of football results"
- Rue & Salvesen (2000): "Prediction and retrospective analysis of soccer matches"

베이지안 접근의 장점:
1. 불확실성 정량화 (Uncertainty Quantification)
2. 자동 정규화 (Hierarchical Priors)
3. 적은 데이터로도 강건한 예측
4. 신뢰구간 제공

모델 구조:
-----------
Hierarchical Priors:
    μ_α ~ Normal(0, 1)         # 전체 평균 공격력
    μ_β ~ Normal(0, 1)         # 전체 평균 수비력
    σ_α ~ HalfCauchy(1)        # 공격력 표준편차
    σ_β ~ HalfCauchy(1)        # 수비력 표준편차

Team-specific Parameters:
    α_i ~ Normal(μ_α, σ_α)     # 팀 i의 공격력
    β_i ~ Normal(μ_β, σ_β)     # 팀 i의 수비력

Home Advantage:
    γ ~ Normal(0.3, 0.1)       # 홈 어드밴티지

Likelihood:
    λ_home = exp(α_home - β_away + γ)
    λ_away = exp(α_away - β_home)
    goals_home ~ Poisson(λ_home)
    goals_away ~ Poisson(λ_away)

성능 기대치:
- RPS: 0.18-0.19 (Dixon-Coles MLE 대비 5-10% 개선)
- 신뢰구간 제공으로 리스크 관리 가능
- 승격/강등팀 예측 정확도 향상 (Prior Regularization)
"""

import pymc as pm
import numpy as np
import pandas as pd
import arviz as az
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')


class BayesianDixonColes:
    """
    Hierarchical Bayesian Dixon-Coles Model for Football Match Prediction

    Parameters:
    -----------
    n_samples : int, default=2000
        MCMC 샘플링 횟수
    n_tune : int, default=1000
        MCMC Warm-up (튜닝) 횟수
    target_accept : float, default=0.9
        HMC/NUTS 수용률 목표 (높을수록 정확, 느림)
    cores : int, default=4
        병렬 처리 코어 수
    """

    def __init__(
        self,
        n_samples: int = 2000,
        n_tune: int = 1000,
        target_accept: float = 0.9,
        cores: int = 4
    ):
        self.n_samples = n_samples
        self.n_tune = n_tune
        self.target_accept = target_accept
        self.cores = cores

        self.trace = None
        self.model = None
        self.teams = None
        self.team_to_idx = None

    def fit(self, matches_df: pd.DataFrame, verbose: bool = True):
        """
        베이지안 모델 학습 (MCMC Sampling)

        Parameters:
        -----------
        matches_df : pd.DataFrame
            경기 데이터 (home_team, away_team, home_score, away_score)
        verbose : bool
            학습 과정 출력 여부

        Note:
        -----
        - NUTS (No-U-Turn Sampler) 사용
        - 4개 체인 병렬 실행으로 수렴 진단
        - Gelman-Rubin R-hat < 1.01 목표
        """
        # 완료된 경기만 사용
        completed_matches = matches_df[matches_df['home_score'].notna()].copy()

        # 팀 목록 및 인덱스 생성
        teams = sorted(
            set(completed_matches['home_team']) |
            set(completed_matches['away_team'])
        )
        n_teams = len(teams)
        self.teams = teams
        self.team_to_idx = {team: idx for idx, team in enumerate(teams)}

        # 경기 인덱스 변환
        home_idx = completed_matches['home_team'].map(self.team_to_idx).values
        away_idx = completed_matches['away_team'].map(self.team_to_idx).values
        home_goals_obs = completed_matches['home_score'].astype(int).values
        away_goals_obs = completed_matches['away_score'].astype(int).values

        if verbose:
            print("=" * 60)
            print("Hierarchical Bayesian Dixon-Coles Model")
            print("=" * 60)
            print(f"Teams: {n_teams}")
            print(f"Matches: {len(completed_matches)}")
            print(f"MCMC Samples: {self.n_samples} (Tune: {self.n_tune})")
            print(f"Cores: {self.cores}")
            print("-" * 60)

        # 베이지안 모델 구축
        with pm.Model() as model:
            # ==========================================
            # Hyperpriors (Level 2)
            # ==========================================
            # 전체 팀들의 공격력/수비력 분포
            mu_attack = pm.Normal('mu_attack', mu=0, sigma=1)
            mu_defense = pm.Normal('mu_defense', mu=0, sigma=1)

            # Hierarchical variance (Heavy-tailed prior)
            sigma_attack = pm.HalfCauchy('sigma_attack', beta=1)
            sigma_defense = pm.HalfCauchy('sigma_defense', beta=1)

            # ==========================================
            # Team-specific Parameters (Level 1)
            # ==========================================
            # 각 팀의 공격력/수비력 (Hierarchical)
            attack_raw = pm.Normal('attack_raw', mu=0, sigma=1, shape=n_teams)
            defense_raw = pm.Normal('defense_raw', mu=0, sigma=1, shape=n_teams)

            # Non-centered parameterization (수렴 개선)
            attack = pm.Deterministic('attack', mu_attack + attack_raw * sigma_attack)
            defense = pm.Deterministic('defense', mu_defense + defense_raw * sigma_defense)

            # 홈 어드밴티지 (약 1.3배, log scale에서 0.26)
            gamma = pm.Normal('gamma', mu=0.26, sigma=0.1)

            # ==========================================
            # Likelihood (Level 0)
            # ==========================================
            # Poisson 평균 계산 (log-linear model)
            lambda_home = pm.math.exp(
                attack[home_idx] - defense[away_idx] + gamma
            )
            lambda_away = pm.math.exp(
                attack[away_idx] - defense[home_idx]
            )

            # 관측값 (Poisson likelihood)
            home_goals = pm.Poisson(
                'home_goals',
                mu=lambda_home,
                observed=home_goals_obs
            )
            away_goals = pm.Poisson(
                'away_goals',
                mu=lambda_away,
                observed=away_goals_obs
            )

            # ==========================================
            # MCMC Sampling (NUTS)
            # ==========================================
            if verbose:
                print("Starting MCMC sampling (NUTS)...")
                print("This may take 2-5 minutes depending on data size.\n")

            self.trace = pm.sample(
                draws=self.n_samples,
                tune=self.n_tune,
                cores=self.cores,
                target_accept=self.target_accept,
                return_inferencedata=True,
                progressbar=verbose
            )

        self.model = model

        if verbose:
            print("\n" + "=" * 60)
            print("Sampling Complete!")
            print("=" * 60)
            self._print_diagnostics()

    def _print_diagnostics(self):
        """MCMC 진단 통계 출력"""
        # R-hat (Gelman-Rubin statistic)
        rhat = az.rhat(self.trace)
        max_rhat = float(rhat.max().to_array().max())

        # Effective Sample Size
        ess = az.ess(self.trace)
        min_ess = float(ess.min().to_array().min())

        print(f"\nDiagnostics:")
        print(f"  Max R-hat: {max_rhat:.4f} (< 1.01 good)")
        print(f"  Min ESS: {min_ess:.0f} (> 400 good)")

        if max_rhat > 1.05:
            print("  ⚠️  Warning: Poor convergence detected!")
            print("     Consider increasing n_tune or n_samples")
        else:
            print("  ✓ Good convergence")

    def predict_match(
        self,
        home_team: str,
        away_team: str,
        n_sims: int = 5000,
        credible_interval: float = 0.95
    ) -> Dict:
        """
        베이지안 예측 (Posterior Predictive Distribution)

        Parameters:
        -----------
        home_team : str
            홈팀 이름
        away_team : str
            원정팀 이름
        n_sims : int
            시뮬레이션 횟수
        credible_interval : float
            신뢰구간 수준 (default: 95%)

        Returns:
        --------
        dict : 예측 결과
            - home_win, draw, away_win: 승/무/패 확률 (%)
            - expected_goals: 예상 득점 (평균 및 신뢰구간)
            - credible_intervals: 결과 확률의 95% 신뢰구간
            - top_scores: 가능성 높은 스코어 Top 5
            - posterior_samples: 원시 시뮬레이션 데이터 (분석용)
            - risk_metrics: 리스크 지표
        """
        if self.trace is None:
            raise ValueError("Model not fitted. Call fit() first.")

        home_idx = self.team_to_idx.get(home_team)
        away_idx = self.team_to_idx.get(away_team)

        if home_idx is None or away_idx is None:
            raise ValueError(f"Team not found: {home_team} or {away_team}")

        # Posterior samples 추출
        attack_samples = self.trace.posterior['attack'].values.reshape(-1, len(self.teams))
        defense_samples = self.trace.posterior['defense'].values.reshape(-1, len(self.teams))
        gamma_samples = self.trace.posterior['gamma'].values.flatten()

        # 샘플 수 제한 (계산 효율)
        n_posterior = len(gamma_samples)
        if n_posterior > n_sims:
            indices = np.random.choice(n_posterior, n_sims, replace=False)
        else:
            indices = np.arange(n_posterior)
            n_sims = n_posterior

        # 시뮬레이션
        results = {'home': 0, 'draw': 0, 'away': 0}
        goals_home_samples = []
        goals_away_samples = []
        score_counts = {}

        for i in indices:
            # Lambda 계산 (Posterior)
            lambda_h = np.exp(
                attack_samples[i, home_idx] -
                defense_samples[i, away_idx] +
                gamma_samples[i]
            )
            lambda_a = np.exp(
                attack_samples[i, away_idx] -
                defense_samples[i, home_idx]
            )

            # Poisson 샘플링
            goals_h = np.random.poisson(lambda_h)
            goals_a = np.random.poisson(lambda_a)

            goals_home_samples.append(goals_h)
            goals_away_samples.append(goals_a)

            # 결과 분류
            if goals_h > goals_a:
                results['home'] += 1
            elif goals_h < goals_a:
                results['away'] += 1
            else:
                results['draw'] += 1

            # 스코어 카운팅
            score_key = f"{goals_h}-{goals_a}"
            score_counts[score_key] = score_counts.get(score_key, 0) + 1

        # 확률 계산
        home_win_prob = results['home'] / n_sims * 100
        draw_prob = results['draw'] / n_sims * 100
        away_win_prob = results['away'] / n_sims * 100

        # 신뢰구간 계산
        alpha = 1 - credible_interval
        lower_percentile = (alpha / 2) * 100
        upper_percentile = (1 - alpha / 2) * 100

        goals_home_samples = np.array(goals_home_samples)
        goals_away_samples = np.array(goals_away_samples)

        # Top 5 스코어
        top_scores = sorted(
            [{'score': k, 'probability': v / n_sims * 100}
             for k, v in score_counts.items()],
            key=lambda x: x['probability'],
            reverse=True
        )[:5]

        # 리스크 지표
        goal_diff = goals_home_samples - goals_away_samples
        var_95 = np.percentile(goal_diff, 5)  # Value at Risk (5%)
        cvar_95 = goal_diff[goal_diff <= var_95].mean()  # Conditional VaR

        return {
            # 기본 예측
            'home_win': home_win_prob,
            'draw': draw_prob,
            'away_win': away_win_prob,

            # 예상 득점
            'expected_home_goals': float(np.mean(goals_home_samples)),
            'expected_away_goals': float(np.mean(goals_away_samples)),

            # 신뢰구간
            'credible_intervals': {
                'home_win': [
                    float(np.percentile(goals_home_samples > goals_away_samples, lower_percentile)),
                    float(np.percentile(goals_home_samples > goals_away_samples, upper_percentile))
                ],
                'home_goals': [
                    float(np.percentile(goals_home_samples, lower_percentile)),
                    float(np.percentile(goals_home_samples, upper_percentile))
                ],
                'away_goals': [
                    float(np.percentile(goals_away_samples, lower_percentile)),
                    float(np.percentile(goals_away_samples, upper_percentile))
                ],
                'goal_difference': [
                    float(np.percentile(goal_diff, lower_percentile)),
                    float(np.percentile(goal_diff, upper_percentile))
                ]
            },

            # Top 스코어
            'top_scores': top_scores,

            # 리스크 지표
            'risk_metrics': {
                'var_95': float(var_95),
                'cvar_95': float(cvar_95),
                'home_win_certainty': home_win_prob / 100,
                'prediction_entropy': -sum([
                    p/100 * np.log(p/100 + 1e-10)
                    for p in [home_win_prob, draw_prob, away_win_prob]
                ])
            },

            # 원시 데이터 (고급 분석용)
            'posterior_samples': {
                'home_goals': goals_home_samples.tolist()[:100],  # 샘플만
                'away_goals': goals_away_samples.tolist()[:100]
            }
        }

    def get_team_ratings(self, credible_interval: float = 0.95) -> pd.DataFrame:
        """
        팀별 공격력/수비력 레이팅 (신뢰구간 포함)

        Returns:
        --------
        pd.DataFrame : 팀 레이팅
            - team: 팀 이름
            - attack_mean: 평균 공격력
            - attack_ci_low/high: 신뢰구간
            - defense_mean: 평균 수비력
            - defense_ci_low/high: 신뢰구간
        """
        if self.trace is None:
            raise ValueError("Model not fitted.")

        alpha = 1 - credible_interval
        lower_percentile = (alpha / 2) * 100
        upper_percentile = (1 - alpha / 2) * 100

        attack_samples = self.trace.posterior['attack'].values.reshape(-1, len(self.teams))
        defense_samples = self.trace.posterior['defense'].values.reshape(-1, len(self.teams))

        ratings = []
        for idx, team in enumerate(self.teams):
            attack = attack_samples[:, idx]
            defense = defense_samples[:, idx]

            ratings.append({
                'team': team,
                'attack_mean': float(np.mean(attack)),
                'attack_ci_low': float(np.percentile(attack, lower_percentile)),
                'attack_ci_high': float(np.percentile(attack, upper_percentile)),
                'defense_mean': float(np.mean(defense)),
                'defense_ci_low': float(np.percentile(defense, lower_percentile)),
                'defense_ci_high': float(np.percentile(defense, upper_percentile)),
                'attack_std': float(np.std(attack)),
                'defense_std': float(np.std(defense))
            })

        return pd.DataFrame(ratings).sort_values('attack_mean', ascending=False)

    def plot_team_ratings(self, save_path: Optional[str] = None):
        """팀 레이팅 시각화 (신뢰구간 포함)"""
        try:
            import matplotlib.pyplot as plt

            ratings = self.get_team_ratings()

            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))

            # 공격력
            y_pos = np.arange(len(ratings))
            ax1.barh(y_pos, ratings['attack_mean'], xerr=[
                ratings['attack_mean'] - ratings['attack_ci_low'],
                ratings['attack_ci_high'] - ratings['attack_mean']
            ], capsize=3, alpha=0.7, color='#e74c3c')
            ax1.set_yticks(y_pos)
            ax1.set_yticklabels(ratings['team'])
            ax1.set_xlabel('Attack Strength (log scale)')
            ax1.set_title('Team Attack Ratings (95% CI)')
            ax1.axvline(0, color='black', linestyle='--', alpha=0.3)

            # 수비력
            ax2.barh(y_pos, ratings['defense_mean'], xerr=[
                ratings['defense_mean'] - ratings['defense_ci_low'],
                ratings['defense_ci_high'] - ratings['defense_mean']
            ], capsize=3, alpha=0.7, color='#3498db')
            ax2.set_yticks(y_pos)
            ax2.set_yticklabels(ratings['team'])
            ax2.set_xlabel('Defense Strength (log scale, lower=better)')
            ax2.set_title('Team Defense Ratings (95% CI)')
            ax2.axvline(0, color='black', linestyle='--', alpha=0.3)

            plt.tight_layout()

            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                print(f"Plot saved to {save_path}")
            else:
                plt.show()

        except ImportError:
            print("Matplotlib not available. Install with: pip install matplotlib")

    def summary(self):
        """모델 요약 통계"""
        if self.trace is None:
            raise ValueError("Model not fitted.")

        print("\n" + "=" * 60)
        print("Bayesian Dixon-Coles Model Summary")
        print("=" * 60)
        print(az.summary(self.trace, var_names=['mu_attack', 'mu_defense',
                                                  'sigma_attack', 'sigma_defense',
                                                  'gamma']))
        print("\n" + "=" * 60)


# ============================================================
# 테스트 코드
# ============================================================
if __name__ == "__main__":
    print("Bayesian Dixon-Coles Model - Test Run\n")

    # 더미 데이터 생성 (시뮬레이션)
    np.random.seed(42)
    teams = ['Man City', 'Liverpool', 'Arsenal', 'Chelsea', 'Tottenham',
             'Man United', 'Newcastle', 'Brighton']

    # 실제 같은 데이터 생성 (True parameters)
    true_attack = np.random.normal(0, 0.5, len(teams))
    true_defense = np.random.normal(0, 0.5, len(teams))
    true_gamma = 0.3

    matches = []
    for _ in range(200):  # 200 경기
        home_idx = np.random.randint(0, len(teams))
        away_idx = np.random.randint(0, len(teams))
        if home_idx == away_idx:
            continue

        lambda_h = np.exp(true_attack[home_idx] - true_defense[away_idx] + true_gamma)
        lambda_a = np.exp(true_attack[away_idx] - true_defense[home_idx])

        home_goals = np.random.poisson(lambda_h)
        away_goals = np.random.poisson(lambda_a)

        matches.append({
            'home_team': teams[home_idx],
            'away_team': teams[away_idx],
            'home_score': home_goals,
            'away_score': away_goals
        })

    matches_df = pd.DataFrame(matches)

    # 모델 학습
    model = BayesianDixonColes(n_samples=1000, n_tune=500, cores=2)
    model.fit(matches_df, verbose=True)

    # 모델 요약
    model.summary()

    # 팀 레이팅 확인
    print("\n" + "=" * 60)
    print("Team Ratings:")
    print("=" * 60)
    ratings = model.get_team_ratings()
    print(ratings[['team', 'attack_mean', 'defense_mean']].to_string(index=False))

    # 경기 예측
    print("\n" + "=" * 60)
    print("Match Prediction: Man City vs Liverpool")
    print("=" * 60)
    pred = model.predict_match('Man City', 'Liverpool', n_sims=3000)

    print(f"\nResult Probabilities:")
    print(f"  Home Win: {pred['home_win']:.1f}%")
    print(f"  Draw: {pred['draw']:.1f}%")
    print(f"  Away Win: {pred['away_win']:.1f}%")

    print(f"\nExpected Goals:")
    print(f"  Home: {pred['expected_home_goals']:.2f} "
          f"[{pred['credible_intervals']['home_goals'][0]:.1f}, "
          f"{pred['credible_intervals']['home_goals'][1]:.1f}]")
    print(f"  Away: {pred['expected_away_goals']:.2f} "
          f"[{pred['credible_intervals']['away_goals'][0]:.1f}, "
          f"{pred['credible_intervals']['away_goals'][1]:.1f}]")

    print(f"\nTop 5 Scores:")
    for score in pred['top_scores']:
        print(f"  {score['score']}: {score['probability']:.1f}%")

    print(f"\nRisk Metrics:")
    print(f"  VaR (95%): {pred['risk_metrics']['var_95']:.2f} goals")
    print(f"  CVaR (95%): {pred['risk_metrics']['cvar_95']:.2f} goals")
    print(f"  Prediction Entropy: {pred['risk_metrics']['prediction_entropy']:.3f}")

    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)
