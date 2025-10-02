"""
베이지안 모델 진단 및 시각화 도구
====================================

MCMC 수렴 진단, 사후분포 시각화, 예측 검증 도구

주요 기능:
1. Trace Plots: MCMC 체인 수렴 확인
2. Posterior Distributions: 파라미터 사후분포
3. Pair Plots: 파라미터 간 상관관계
4. Predictive Checks: 모델 적합도 검증
5. Credible Intervals: 신뢰구간 시각화
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from typing import Dict, List, Optional
import warnings
warnings.filterwarnings('ignore')


class BayesianDiagnostics:
    """베이지안 모델 진단 클래스"""

    def __init__(self, model):
        """
        Parameters:
        -----------
        model : SimplifiedBayesianDixonColes
            학습된 베이지안 모델
        """
        self.model = model

    def plot_trace(self, params: List[str] = None, save_path: Optional[str] = None):
        """
        Trace Plot: MCMC 샘플링 궤적

        수렴 판단:
        - 트레이스가 안정적으로 보이면 수렴
        - 트렌드가 보이면 수렴 실패
        """
        if self.model.samples is None:
            raise ValueError("Model not fitted")

        if params is None:
            params = ['mu_attack', 'mu_defense', 'sigma_attack', 'sigma_defense', 'gamma']

        n_params = len(params)
        fig, axes = plt.subplots(n_params, 1, figsize=(12, 3 * n_params))

        if n_params == 1:
            axes = [axes]

        for i, param in enumerate(params):
            values = [s[param] for s in self.model.samples]
            axes[i].plot(values, linewidth=0.5, alpha=0.8)
            axes[i].set_ylabel(param)
            axes[i].set_xlabel('Sample')
            axes[i].set_title(f'Trace Plot: {param}')
            axes[i].grid(True, alpha=0.3)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Trace plot saved to {save_path}")
        else:
            plt.show()

    def plot_posterior(self, params: List[str] = None, save_path: Optional[str] = None):
        """
        Posterior Distribution: 사후분포 히스토그램

        해석:
        - 분포의 중심: 파라미터 최적값
        - 분포의 폭: 불확실성
        """
        if self.model.samples is None:
            raise ValueError("Model not fitted")

        if params is None:
            params = ['mu_attack', 'mu_defense', 'sigma_attack', 'sigma_defense', 'gamma']

        n_params = len(params)
        fig, axes = plt.subplots(n_params, 1, figsize=(10, 3 * n_params))

        if n_params == 1:
            axes = [axes]

        for i, param in enumerate(params):
            values = np.array([s[param] for s in self.model.samples])

            axes[i].hist(values, bins=50, density=True, alpha=0.6, color='steelblue', edgecolor='black')

            # 통계량 표시
            mean = np.mean(values)
            median = np.median(values)
            ci_low = np.percentile(values, 2.5)
            ci_high = np.percentile(values, 97.5)

            axes[i].axvline(mean, color='red', linestyle='--', linewidth=2, label=f'Mean: {mean:.3f}')
            axes[i].axvline(median, color='green', linestyle='--', linewidth=2, label=f'Median: {median:.3f}')
            axes[i].axvline(ci_low, color='orange', linestyle=':', linewidth=1.5, label=f'95% CI: [{ci_low:.3f}, {ci_high:.3f}]')
            axes[i].axvline(ci_high, color='orange', linestyle=':', linewidth=1.5)

            axes[i].set_xlabel(param)
            axes[i].set_ylabel('Density')
            axes[i].set_title(f'Posterior Distribution: {param}')
            axes[i].legend()
            axes[i].grid(True, alpha=0.3)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Posterior plot saved to {save_path}")
        else:
            plt.show()

    def plot_team_ratings_comparison(self, save_path: Optional[str] = None):
        """
        팀 레이팅 비교 (공격력 vs 수비력)

        해석:
        - 오른쪽 위: 강팀 (공격력↑, 수비력↓)
        - 왼쪽 아래: 약팀 (공격력↓, 수비력↑)
        """
        ratings_df = self.model.get_team_ratings()

        fig, ax = plt.subplots(figsize=(12, 8))

        # Scatter plot with error bars
        ax.errorbar(
            ratings_df['attack_mean'],
            ratings_df['defense_mean'],
            xerr=[
                ratings_df['attack_mean'] - ratings_df['attack_ci_low'],
                ratings_df['attack_ci_high'] - ratings_df['attack_mean']
            ],
            yerr=[
                ratings_df['defense_mean'] - ratings_df['defense_ci_low'],
                ratings_df['defense_ci_high'] - ratings_df['defense_mean']
            ],
            fmt='o',
            markersize=8,
            capsize=5,
            alpha=0.7
        )

        # 팀 이름 레이블
        for _, row in ratings_df.iterrows():
            ax.annotate(
                row['team'],
                (row['attack_mean'], row['defense_mean']),
                xytext=(5, 5),
                textcoords='offset points',
                fontsize=9,
                alpha=0.8
            )

        ax.axhline(0, color='gray', linestyle='--', alpha=0.5)
        ax.axvline(0, color='gray', linestyle='--', alpha=0.5)

        ax.set_xlabel('Attack Strength (higher = better)', fontsize=12)
        ax.set_ylabel('Defense Strength (lower = better)', fontsize=12)
        ax.set_title('Team Ratings: Attack vs Defense (95% Credible Intervals)', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)

        # Quadrant labels
        ax.text(0.95, 0.95, 'Strong Attack\nStrong Defense', transform=ax.transAxes,
                ha='right', va='top', fontsize=10, alpha=0.5, style='italic')
        ax.text(0.05, 0.05, 'Weak Attack\nWeak Defense', transform=ax.transAxes,
                ha='left', va='bottom', fontsize=10, alpha=0.5, style='italic')

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Team ratings comparison saved to {save_path}")
        else:
            plt.show()

    def plot_prediction_distribution(
        self,
        home_team: str,
        away_team: str,
        n_sims: int = 3000,
        save_path: Optional[str] = None
    ):
        """
        예측 분포 시각화

        1. 득점 분포 히스토그램
        2. 결과 확률 바 차트
        3. 스코어 히트맵
        """
        prediction = self.model.predict_match(home_team, away_team, n_sims=n_sims)

        fig, axes = plt.subplots(2, 2, figsize=(14, 10))

        # 1. 득점 분포
        home_goals = prediction['posterior_samples']['home_goals'][:100]
        away_goals = prediction['posterior_samples']['away_goals'][:100]

        axes[0, 0].hist(home_goals, bins=range(0, 8), alpha=0.6, label=home_team, color='red', edgecolor='black')
        axes[0, 0].hist(away_goals, bins=range(0, 8), alpha=0.6, label=away_team, color='blue', edgecolor='black')
        axes[0, 0].set_xlabel('Goals')
        axes[0, 0].set_ylabel('Frequency')
        axes[0, 0].set_title('Goal Distribution (Posterior Predictive)')
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3)

        # 2. 결과 확률
        results = ['Home Win', 'Draw', 'Away Win']
        probabilities = [
            prediction['home_win'],
            prediction['draw'],
            prediction['away_win']
        ]
        colors = ['#e74c3c', '#95a5a6', '#3498db']

        axes[0, 1].bar(results, probabilities, color=colors, alpha=0.7, edgecolor='black')
        axes[0, 1].set_ylabel('Probability (%)')
        axes[0, 1].set_title('Match Outcome Probabilities')
        axes[0, 1].grid(True, alpha=0.3, axis='y')

        # 확률값 표시
        for i, (result, prob) in enumerate(zip(results, probabilities)):
            axes[0, 1].text(i, prob + 2, f'{prob:.1f}%', ha='center', fontweight='bold')

        # 3. Top 스코어
        top_scores = prediction['top_scores']
        scores = [s['score'] for s in top_scores]
        score_probs = [s['probability'] for s in top_scores]

        axes[1, 0].barh(scores, score_probs, color='green', alpha=0.7, edgecolor='black')
        axes[1, 0].set_xlabel('Probability (%)')
        axes[1, 0].set_ylabel('Score')
        axes[1, 0].set_title('Most Likely Scores')
        axes[1, 0].grid(True, alpha=0.3, axis='x')

        # 4. 리스크 메트릭
        risk_info = f"""
        Expected Goals:
        • Home: {prediction['expected_home_goals']:.2f}
          [{prediction['credible_intervals']['home_goals'][0]:.1f},
           {prediction['credible_intervals']['home_goals'][1]:.1f}]
        • Away: {prediction['expected_away_goals']:.2f}
          [{prediction['credible_intervals']['away_goals'][0]:.1f},
           {prediction['credible_intervals']['away_goals'][1]:.1f}]

        Risk Metrics:
        • VaR (95%): {prediction['risk_metrics']['var_95']:.2f} goals
        • CVaR (95%): {prediction['risk_metrics']['cvar_95']:.2f} goals
        • Entropy: {prediction['risk_metrics']['prediction_entropy']:.3f}
          (lower = more certain)

        Goal Difference (95% CI):
        [{prediction['credible_intervals']['goal_difference'][0]:.1f},
         {prediction['credible_intervals']['goal_difference'][1]:.1f}]
        """

        axes[1, 1].text(0.1, 0.5, risk_info, fontsize=10, verticalalignment='center',
                       family='monospace', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        axes[1, 1].axis('off')
        axes[1, 1].set_title('Risk Metrics & Credible Intervals')

        plt.suptitle(f'{home_team} vs {away_team} - Bayesian Prediction', fontsize=16, fontweight='bold')
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Prediction distribution saved to {save_path}")
        else:
            plt.show()

    def convergence_diagnostics(self) -> Dict:
        """
        수렴 진단 통계

        Returns:
        --------
        dict : 진단 통계
            - effective_sample_size: 유효 샘플 수 (autocorrelation 보정)
            - acceptance_rate: 수용률
            - geweke_z_scores: Geweke 수렴 진단 (|z| < 2 이면 수렴)
        """
        if self.model.samples is None:
            raise ValueError("Model not fitted")

        diagnostics = {
            'acceptance_rate': self.model.acceptance_rate,
            'n_samples': len(self.model.samples),
            'parameters': {}
        }

        # 각 파라미터별 진단
        params = ['mu_attack', 'mu_defense', 'sigma_attack', 'sigma_defense', 'gamma']

        for param in params:
            values = np.array([s[param] for s in self.model.samples])

            # Effective Sample Size (간단한 추정)
            # Autocorrelation 고려 (실제로는 더 정교한 계산 필요)
            autocorr = np.corrcoef(values[:-1], values[1:])[0, 1]
            ess = len(values) / (1 + 2 * autocorr) if autocorr > 0 else len(values)

            # Geweke Z-score (첫 10% vs 마지막 50%)
            first_10 = values[:len(values) // 10]
            last_50 = values[len(values) // 2:]

            z_score = (np.mean(first_10) - np.mean(last_50)) / \
                     np.sqrt(np.var(first_10) / len(first_10) + np.var(last_50) / len(last_50))

            diagnostics['parameters'][param] = {
                'mean': float(np.mean(values)),
                'std': float(np.std(values)),
                'ess': float(ess),
                'geweke_z': float(z_score),
                'converged': abs(z_score) < 2  # |z| < 2 이면 수렴
            }

        return diagnostics

    def print_diagnostics(self):
        """진단 통계 출력"""
        diag = self.convergence_diagnostics()

        print("\n" + "=" * 60)
        print("MCMC Convergence Diagnostics")
        print("=" * 60)
        print(f"\nOverall:")
        print(f"  Acceptance Rate: {diag['acceptance_rate'] * 100:.1f}%")
        print(f"  Total Samples: {diag['n_samples']}")

        print(f"\nParameter-wise:")
        print(f"  {'Parameter':<20} {'Mean':<10} {'ESS':<10} {'Geweke Z':<12} {'Converged'}")
        print("-" * 60)

        for param, stats in diag['parameters'].items():
            status = "✓" if stats['converged'] else "✗"
            print(f"  {param:<20} {stats['mean']:<10.3f} {stats['ess']:<10.0f} "
                  f"{stats['geweke_z']:<12.3f} {status}")

        print("\nInterpretation:")
        print("  • Acceptance Rate: 15-50% is ideal")
        print("  • ESS: Higher is better (>400 recommended)")
        print("  • Geweke Z: |z| < 2 indicates convergence")
        print("=" * 60)


# ============================================================
# 사용 예제
# ============================================================
if __name__ == "__main__":
    from bayesian_dixon_coles_simplified import SimplifiedBayesianDixonColes
    import pandas as pd

    print("Bayesian Diagnostics - Example\n")

    # Dummy data
    np.random.seed(42)
    teams = ['Man City', 'Liverpool', 'Arsenal', 'Chelsea', 'Tottenham']

    matches = []
    for _ in range(100):
        home_idx = np.random.randint(0, len(teams))
        away_idx = np.random.randint(0, len(teams))
        if home_idx == away_idx:
            continue

        home_goals = np.random.poisson(1.5)
        away_goals = np.random.poisson(1.2)

        matches.append({
            'home_team': teams[home_idx],
            'away_team': teams[away_idx],
            'home_score': home_goals,
            'away_score': away_goals
        })

    matches_df = pd.DataFrame(matches)

    # Fit model
    model = SimplifiedBayesianDixonColes(n_samples=1000, burnin=500, thin=2)
    model.fit(matches_df, verbose=False)

    # Diagnostics
    diag = BayesianDiagnostics(model)

    # 1. Convergence diagnostics
    diag.print_diagnostics()

    # 2. Plots (저장만, display 안함)
    print("\nGenerating diagnostic plots...")

    diag.plot_trace(save_path='trace_plot.png')
    diag.plot_posterior(save_path='posterior_plot.png')
    diag.plot_team_ratings_comparison(save_path='team_ratings.png')
    diag.plot_prediction_distribution('Man City', 'Liverpool', save_path='prediction_dist.png')

    print("\nAll plots saved!")
    print("  - trace_plot.png")
    print("  - posterior_plot.png")
    print("  - team_ratings.png")
    print("  - prediction_dist.png")
