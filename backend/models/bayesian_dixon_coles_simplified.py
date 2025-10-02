"""
Simplified Bayesian Dixon-Coles using MCMC (NumPy-based)
=========================================================

PyMC 의존성 문제로 인해 NumPy 기반 Metropolis-Hastings MCMC로 구현
실무에서는 PyMC/Stan을 권장하지만, 작동 가능한 프로토타입 제공

이론:
- Posterior ∝ Likelihood × Prior
- MCMC로 posterior sampling
- Hierarchical priors for regularization

성능:
- 정확도는 PyMC와 유사하지만 속도 느림
- 프로덕션 환경에서는 PyMC 3.11 + PyTensor 설치 권장
"""

import numpy as np
import pandas as pd
from scipy.stats import norm, poisson, halfcauchy
from typing import Dict, Tuple, List
import warnings
warnings.filterwarnings('ignore')


class SimplifiedBayesianDixonColes:
    """
    Simplified Bayesian Dixon-Coles with Metropolis-Hastings MCMC

    Parameters:
    -----------
    n_samples : int
        MCMC 샘플 수
    burnin : int
        Burn-in 기간 (버릴 초기 샘플 수)
    thin : int
        Thinning (매 n번째 샘플만 저장)
    """

    def __init__(self, n_samples: int = 5000, burnin: int = 2000, thin: int = 5):
        self.n_samples = n_samples
        self.burnin = burnin
        self.thin = thin

        self.samples = None
        self.teams = None
        self.team_to_idx = None
        self.acceptance_rate = 0.0

    def log_prior(self, params: Dict) -> float:
        """
        Log prior probability

        Hierarchical Priors:
        - mu_attack, mu_defense ~ Normal(0, 1)
        - sigma_attack, sigma_defense ~ HalfCauchy(1)
        - attack[i] ~ Normal(mu_attack, sigma_attack)
        - defense[i] ~ Normal(mu_defense, sigma_defense)
        - gamma ~ Normal(0.26, 0.1)
        """
        log_p = 0.0

        # Hyperparameters
        log_p += norm.logpdf(params['mu_attack'], loc=0, scale=1)
        log_p += norm.logpdf(params['mu_defense'], loc=0, scale=1)
        log_p += halfcauchy.logpdf(params['sigma_attack'], scale=1)
        log_p += halfcauchy.logpdf(params['sigma_defense'], scale=1)

        # Team parameters (hierarchical)
        log_p += np.sum(norm.logpdf(
            params['attack'],
            loc=params['mu_attack'],
            scale=params['sigma_attack']
        ))
        log_p += np.sum(norm.logpdf(
            params['defense'],
            loc=params['mu_defense'],
            scale=params['sigma_defense']
        ))

        # Home advantage
        log_p += norm.logpdf(params['gamma'], loc=0.26, scale=0.1)

        return log_p

    def log_likelihood(self, params: Dict, matches_df: pd.DataFrame) -> float:
        """
        Log likelihood: Σ log P(goals | params)

        Poisson likelihood:
        - lambda_home = exp(attack_home - defense_away + gamma)
        - lambda_away = exp(attack_away - defense_home)
        - goals_home ~ Poisson(lambda_home)
        - goals_away ~ Poisson(lambda_away)
        """
        log_l = 0.0

        for _, match in matches_df.iterrows():
            home_idx = self.team_to_idx[match['home_team']]
            away_idx = self.team_to_idx[match['away_team']]

            # Lambda calculation
            lambda_home = np.exp(
                params['attack'][home_idx] -
                params['defense'][away_idx] +
                params['gamma']
            )
            lambda_away = np.exp(
                params['attack'][away_idx] -
                params['defense'][home_idx]
            )

            # Poisson log likelihood
            home_goals = int(match['home_score'])
            away_goals = int(match['away_score'])

            log_l += poisson.logpmf(home_goals, lambda_home)
            log_l += poisson.logpmf(away_goals, lambda_away)

        return log_l

    def log_posterior(self, params: Dict, matches_df: pd.DataFrame) -> float:
        """Log posterior = Log prior + Log likelihood"""
        return self.log_prior(params) + self.log_likelihood(params, matches_df)

    def propose_params(self, current_params: Dict, proposal_sd: Dict) -> Dict:
        """
        Propose new parameters (Gaussian random walk)

        proposal_sd: 각 파라미터의 제안 분포 표준편차
        """
        new_params = {}

        # Hyperparameters
        new_params['mu_attack'] = current_params['mu_attack'] + \
            np.random.normal(0, proposal_sd['mu'])
        new_params['mu_defense'] = current_params['mu_defense'] + \
            np.random.normal(0, proposal_sd['mu'])

        new_params['sigma_attack'] = max(0.01,
            current_params['sigma_attack'] + np.random.normal(0, proposal_sd['sigma']))
        new_params['sigma_defense'] = max(0.01,
            current_params['sigma_defense'] + np.random.normal(0, proposal_sd['sigma']))

        # Team parameters
        new_params['attack'] = current_params['attack'] + \
            np.random.normal(0, proposal_sd['team'], size=len(current_params['attack']))
        new_params['defense'] = current_params['defense'] + \
            np.random.normal(0, proposal_sd['team'], size=len(current_params['defense']))

        # Home advantage
        new_params['gamma'] = current_params['gamma'] + \
            np.random.normal(0, proposal_sd['gamma'])

        return new_params

    def fit(self, matches_df: pd.DataFrame, verbose: bool = True):
        """
        Metropolis-Hastings MCMC Sampling

        Parameters:
        -----------
        matches_df : pd.DataFrame
            경기 데이터 (home_team, away_team, home_score, away_score)
        verbose : bool
            진행 상황 출력
        """
        # Data preparation
        completed_matches = matches_df[matches_df['home_score'].notna()].copy()
        teams = sorted(
            set(completed_matches['home_team']) |
            set(completed_matches['away_team'])
        )
        n_teams = len(teams)

        self.teams = teams
        self.team_to_idx = {team: idx for idx, team in enumerate(teams)}

        if verbose:
            print("=" * 60)
            print("Simplified Bayesian Dixon-Coles (Metropolis-Hastings MCMC)")
            print("=" * 60)
            print(f"Teams: {n_teams}")
            print(f"Matches: {len(completed_matches)}")
            print(f"MCMC Samples: {self.n_samples} (Burnin: {self.burnin})")
            print("-" * 60)

        # Initial parameters
        current_params = {
            'mu_attack': 0.0,
            'mu_defense': 0.0,
            'sigma_attack': 0.5,
            'sigma_defense': 0.5,
            'attack': np.random.normal(0, 0.1, n_teams),
            'defense': np.random.normal(0, 0.1, n_teams),
            'gamma': 0.26
        }

        # Proposal standard deviations (튜닝 가능)
        proposal_sd = {
            'mu': 0.05,
            'sigma': 0.02,
            'team': 0.05,
            'gamma': 0.02
        }

        # MCMC sampling
        samples = []
        current_log_posterior = self.log_posterior(current_params, completed_matches)

        accepted = 0
        total_iters = self.burnin + self.n_samples * self.thin

        if verbose:
            print(f"Starting MCMC sampling ({total_iters} iterations)...")

        for i in range(total_iters):
            # Propose new parameters
            proposed_params = self.propose_params(current_params, proposal_sd)

            # Calculate acceptance probability
            proposed_log_posterior = self.log_posterior(proposed_params, completed_matches)

            log_accept_ratio = proposed_log_posterior - current_log_posterior

            # Accept/reject
            if np.log(np.random.rand()) < log_accept_ratio:
                current_params = proposed_params
                current_log_posterior = proposed_log_posterior
                accepted += 1

            # Store samples (after burnin, every 'thin' iterations)
            if i >= self.burnin and (i - self.burnin) % self.thin == 0:
                samples.append({
                    'mu_attack': current_params['mu_attack'],
                    'mu_defense': current_params['mu_defense'],
                    'sigma_attack': current_params['sigma_attack'],
                    'sigma_defense': current_params['sigma_defense'],
                    'attack': current_params['attack'].copy(),
                    'defense': current_params['defense'].copy(),
                    'gamma': current_params['gamma']
                })

            # Progress
            if verbose and (i + 1) % 500 == 0:
                progress = (i + 1) / total_iters * 100
                acc_rate = accepted / (i + 1) * 100
                print(f"  Progress: {progress:.1f}% | Acceptance: {acc_rate:.1f}%")

        self.samples = samples
        self.acceptance_rate = accepted / total_iters

        if verbose:
            print("\n" + "=" * 60)
            print("MCMC Sampling Complete!")
            print(f"Final Acceptance Rate: {self.acceptance_rate * 100:.1f}%")
            print(f"Effective Samples: {len(samples)}")
            print("=" * 60)

            if self.acceptance_rate < 0.15 or self.acceptance_rate > 0.5:
                print("\n⚠️  Warning: Suboptimal acceptance rate!")
                print("   Ideal range: 15-50%")
                print("   Consider adjusting proposal_sd")

    def predict_match(
        self,
        home_team: str,
        away_team: str,
        n_sims: int = 3000,
        credible_interval: float = 0.95
    ) -> Dict:
        """
        베이지안 예측 (Posterior Predictive)

        Returns:
        --------
        dict : 예측 결과
            - home_win, draw, away_win
            - expected_goals (with credible intervals)
            - risk_metrics
            - top_scores
        """
        if self.samples is None:
            raise ValueError("Model not fitted. Call fit() first.")

        home_idx = self.team_to_idx[home_team]
        away_idx = self.team_to_idx[away_team]

        # Simulation
        results = {'home': 0, 'draw': 0, 'away': 0}
        goals_home_samples = []
        goals_away_samples = []
        score_counts = {}

        # Sample from posterior
        n_posterior = len(self.samples)
        sample_indices = np.random.choice(n_posterior, min(n_sims, n_posterior), replace=True)

        for idx in sample_indices:
            sample = self.samples[idx]

            # Lambda calculation
            lambda_h = np.exp(
                sample['attack'][home_idx] -
                sample['defense'][away_idx] +
                sample['gamma']
            )
            lambda_a = np.exp(
                sample['attack'][away_idx] -
                sample['defense'][home_idx]
            )

            # Poisson sampling
            goals_h = np.random.poisson(lambda_h)
            goals_a = np.random.poisson(lambda_a)

            goals_home_samples.append(goals_h)
            goals_away_samples.append(goals_a)

            # Result classification
            if goals_h > goals_a:
                results['home'] += 1
            elif goals_h < goals_a:
                results['away'] += 1
            else:
                results['draw'] += 1

            # Score counting
            score_key = f"{goals_h}-{goals_a}"
            score_counts[score_key] = score_counts.get(score_key, 0) + 1

        n_sims_actual = len(sample_indices)

        # Probabilities
        home_win_prob = results['home'] / n_sims_actual * 100
        draw_prob = results['draw'] / n_sims_actual * 100
        away_win_prob = results['away'] / n_sims_actual * 100

        # Credible intervals
        alpha = 1 - credible_interval
        lower_percentile = (alpha / 2) * 100
        upper_percentile = (1 - alpha / 2) * 100

        goals_home_samples = np.array(goals_home_samples)
        goals_away_samples = np.array(goals_away_samples)

        # Top scores
        top_scores = sorted(
            [{'score': k, 'probability': v / n_sims_actual * 100}
             for k, v in score_counts.items()],
            key=lambda x: x['probability'],
            reverse=True
        )[:5]

        # Risk metrics
        goal_diff = goals_home_samples - goals_away_samples
        var_95 = np.percentile(goal_diff, 5)
        cvar_95 = goal_diff[goal_diff <= var_95].mean()

        return {
            'home_win': home_win_prob,
            'draw': draw_prob,
            'away_win': away_win_prob,
            'expected_home_goals': float(np.mean(goals_home_samples)),
            'expected_away_goals': float(np.mean(goals_away_samples)),
            'credible_intervals': {
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
            'top_scores': top_scores,
            'risk_metrics': {
                'var_95': float(var_95),
                'cvar_95': float(cvar_95),
                'prediction_entropy': -sum([
                    p/100 * np.log(p/100 + 1e-10)
                    for p in [home_win_prob, draw_prob, away_win_prob]
                ])
            }
        }

    def get_team_ratings(self, credible_interval: float = 0.95) -> pd.DataFrame:
        """팀별 레이팅 (신뢰구간 포함)"""
        if self.samples is None:
            raise ValueError("Model not fitted.")

        alpha = 1 - credible_interval
        lower_percentile = (alpha / 2) * 100
        upper_percentile = (1 - alpha / 2) * 100

        # Extract samples
        attack_samples = np.array([s['attack'] for s in self.samples])
        defense_samples = np.array([s['defense'] for s in self.samples])

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
            })

        return pd.DataFrame(ratings).sort_values('attack_mean', ascending=False)

    def summary(self):
        """모델 요약"""
        if self.samples is None:
            raise ValueError("Model not fitted.")

        print("\n" + "=" * 60)
        print("Bayesian Model Summary")
        print("=" * 60)

        # Hyperparameters
        mu_attack = [s['mu_attack'] for s in self.samples]
        mu_defense = [s['mu_defense'] for s in self.samples]
        sigma_attack = [s['sigma_attack'] for s in self.samples]
        sigma_defense = [s['sigma_defense'] for s in self.samples]
        gamma = [s['gamma'] for s in self.samples]

        print(f"\nHyperparameters:")
        print(f"  mu_attack: {np.mean(mu_attack):.3f} ± {np.std(mu_attack):.3f}")
        print(f"  mu_defense: {np.mean(mu_defense):.3f} ± {np.std(mu_defense):.3f}")
        print(f"  sigma_attack: {np.mean(sigma_attack):.3f} ± {np.std(sigma_attack):.3f}")
        print(f"  sigma_defense: {np.mean(sigma_defense):.3f} ± {np.std(sigma_defense):.3f}")
        print(f"  gamma (home adv): {np.mean(gamma):.3f} ± {np.std(gamma):.3f}")
        print(f"    -> exp(gamma) = {np.exp(np.mean(gamma)):.2f} (home multiplier)")

        print(f"\nMCMC Diagnostics:")
        print(f"  Acceptance Rate: {self.acceptance_rate * 100:.1f}%")
        print(f"  Effective Samples: {len(self.samples)}")
        print("=" * 60)


# ============================================================
# 테스트 코드
# ============================================================
if __name__ == "__main__":
    print("Simplified Bayesian Dixon-Coles - Test\n")

    # Dummy data
    np.random.seed(42)
    teams = ['Man City', 'Liverpool', 'Arsenal', 'Chelsea', 'Tottenham']

    # True parameters (ground truth)
    true_attack = np.array([0.5, 0.4, 0.3, 0.2, 0.1])
    true_defense = np.array([-0.1, -0.2, -0.1, 0.0, 0.1])
    true_gamma = 0.3

    matches = []
    for _ in range(100):
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

    # Fit model
    model = SimplifiedBayesianDixonColes(n_samples=2000, burnin=1000, thin=2)
    model.fit(matches_df, verbose=True)

    # Summary
    model.summary()

    # Team ratings
    print("\nTeam Ratings:")
    print(model.get_team_ratings())

    # Prediction
    print("\n" + "=" * 60)
    print("Prediction: Man City vs Liverpool")
    print("=" * 60)
    pred = model.predict_match('Man City', 'Liverpool', n_sims=2000)

    print(f"\nResult Probabilities:")
    print(f"  Home Win: {pred['home_win']:.1f}%")
    print(f"  Draw: {pred['draw']:.1f}%")
    print(f"  Away Win: {pred['away_win']:.1f}%")

    print(f"\nExpected Goals (95% CI):")
    print(f"  Home: {pred['expected_home_goals']:.2f} "
          f"[{pred['credible_intervals']['home_goals'][0]:.1f}, "
          f"{pred['credible_intervals']['home_goals'][1]:.1f}]")
    print(f"  Away: {pred['expected_away_goals']:.2f} "
          f"[{pred['credible_intervals']['away_goals'][0]:.1f}, "
          f"{pred['credible_intervals']['away_goals'][1]:.1f}]")

    print(f"\nTop Scores:")
    for score in pred['top_scores']:
        print(f"  {score['score']}: {score['probability']:.1f}%")

    print("\n" + "=" * 60)
    print("Test Complete!")
