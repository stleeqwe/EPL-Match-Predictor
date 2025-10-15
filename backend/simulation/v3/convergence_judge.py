"""
Convergence Judge
시뮬레이션 수렴 판단 로직

5가지 기준으로 반복 루프 종료 여부를 결정합니다:
1. 서사 일치율 (narrative_adherence >= 0.6) - 가중치 40%
2. AI 수렴 신호 (status == CONVERGED) - 가중치 30%
3. 반복 횟수 (>= max_iterations) - 가중치 15%
4. 득점 차이 안정 (이전 vs 현재) - 가중치 10%
5. 슛 차이 안정 (이전 vs 현재) - 가중치 5%
"""

from typing import Dict, Any, Optional, Tuple
import sys
import os

# 경로 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from ai.data_models import AnalysisResult, AnalysisStatus, SimulationResult


class ConvergenceJudge:
    """
    수렴 판단기

    시뮬레이션이 충분히 수렴했는지 5가지 기준으로 판단합니다.
    """

    def __init__(self,
                 adherence_threshold: float = 0.6,
                 max_iterations: int = 5,
                 score_stability_threshold: int = 1,
                 shot_stability_threshold: int = 3,
                 convergence_threshold: float = 0.7):
        """
        Args:
            adherence_threshold: 서사 일치율 목표 (0.0-1.0)
            max_iterations: 최대 반복 횟수
            score_stability_threshold: 득점 차이 안정 기준 (골 수)
            shot_stability_threshold: 슛 차이 안정 기준 (슛 수)
            convergence_threshold: 수렴 판단 가중 점수 임계값 (0.0-1.0)
        """
        self.adherence_threshold = adherence_threshold
        self.max_iterations = max_iterations
        self.score_stability_threshold = score_stability_threshold
        self.shot_stability_threshold = shot_stability_threshold
        self.convergence_threshold = convergence_threshold

    def is_converged(self,
                    analysis: AnalysisResult,
                    current_result: SimulationResult,
                    previous_result: Optional[SimulationResult],
                    iteration: int) -> Tuple[bool, Dict[str, Any]]:
        """
        수렴 판단

        Args:
            analysis: AI 분석 결과
            current_result: 현재 시뮬레이션 결과
            previous_result: 이전 시뮬레이션 결과 (첫 반복이면 None)
            iteration: 현재 반복 횟수

        Returns:
            (is_converged, convergence_info)
            convergence_info: {
                'weighted_score': float,
                'scores': Dict[str, float],
                'reason': str,
                'details': Dict[str, str]
            }
        """
        # 각 기준별 점수 계산 (0.0-1.0)
        scores = {
            'adherence': self._score_adherence(current_result),
            'ai_signal': self._score_ai_signal(analysis),
            'iterations': self._score_iterations(iteration),
            'score_stability': self._score_stability(
                current_result, previous_result, 'score'
            ),
            'shot_stability': self._score_stability(
                current_result, previous_result, 'shots'
            ),
        }

        # 가중 평균 계산
        weighted_score = (
            scores['adherence'] * 0.40 +      # 서사 일치율 40%
            scores['ai_signal'] * 0.30 +      # AI 신호 30%
            scores['iterations'] * 0.15 +     # 반복 횟수 15%
            scores['score_stability'] * 0.10 + # 득점 안정 10%
            scores['shot_stability'] * 0.05    # 슛 안정 5%
        )

        # 수렴 판단 (가중 점수 >= 임계값)
        is_converged = weighted_score >= self.convergence_threshold

        # 상세 정보 생성
        details = {
            'adherence': f"{current_result.narrative_adherence:.0%} (목표: {self.adherence_threshold:.0%})",
            'ai_signal': f"{analysis.status.value}",
            'iterations': f"{iteration}/{self.max_iterations}",
            'score_stability': self._get_stability_detail(current_result, previous_result, 'score'),
            'shot_stability': self._get_stability_detail(current_result, previous_result, 'shots'),
        }

        # 수렴 이유
        reason = self._get_convergence_reason(scores, is_converged)

        return is_converged, {
            'is_converged': is_converged,
            'weighted_score': weighted_score,
            'scores': scores,
            'reason': reason,
            'details': details,
        }

    # ==========================================================================
    # 기준별 점수 계산
    # ==========================================================================

    def _score_adherence(self, result: SimulationResult) -> float:
        """
        서사 일치율 점수

        Args:
            result: 시뮬레이션 결과

        Returns:
            0.0-1.0 점수
        """
        adherence = result.narrative_adherence

        # 목표치 이상이면 1.0
        if adherence >= self.adherence_threshold:
            return 1.0

        # 목표치 미만이면 비율로 계산
        return adherence / self.adherence_threshold

    def _score_ai_signal(self, analysis: AnalysisResult) -> float:
        """
        AI 수렴 신호 점수

        Args:
            analysis: AI 분석 결과

        Returns:
            0.0-1.0 점수
        """
        if analysis.status == AnalysisStatus.CONVERGED:
            return 1.0
        elif analysis.status == AnalysisStatus.MAX_ITERATIONS:
            return 0.8  # 최대 반복 도달도 일종의 수렴
        else:  # NEEDS_ADJUSTMENT
            return 0.0

    def _score_iterations(self, iteration: int) -> float:
        """
        반복 횟수 점수

        Args:
            iteration: 현재 반복 횟수

        Returns:
            0.0-1.0 점수
        """
        # 최대 반복 도달 시 1.0
        if iteration >= self.max_iterations:
            return 1.0

        # 반복 횟수에 비례 (선형)
        return iteration / self.max_iterations

    def _score_stability(self,
                        current_result: SimulationResult,
                        previous_result: Optional[SimulationResult],
                        metric: str) -> float:
        """
        안정성 점수 (득점 또는 슛)

        Args:
            current_result: 현재 결과
            previous_result: 이전 결과
            metric: 'score' 또는 'shots'

        Returns:
            0.0-1.0 점수
        """
        # 첫 반복이면 비교 불가 → 중립 점수
        if previous_result is None:
            return 0.5

        if metric == 'score':
            # 득점 차이
            current_total = current_result.final_score['home'] + current_result.final_score['away']
            previous_total = previous_result.final_score['home'] + previous_result.final_score['away']
            diff = abs(current_total - previous_total)

            threshold = self.score_stability_threshold

        elif metric == 'shots':
            # 슛 차이
            current_shots = current_result.stats.get('home_shots', 0) + current_result.stats.get('away_shots', 0)
            previous_shots = previous_result.stats.get('home_shots', 0) + previous_result.stats.get('away_shots', 0)
            diff = abs(current_shots - previous_shots)

            threshold = self.shot_stability_threshold

        else:
            return 0.5

        # 차이가 임계값 이하면 1.0 (안정적)
        if diff <= threshold:
            return 1.0

        # 차이가 크면 점수 감소 (선형)
        return max(0.0, 1.0 - (diff - threshold) / threshold)

    # ==========================================================================
    # 헬퍼 메서드
    # ==========================================================================

    def _get_stability_detail(self,
                             current_result: SimulationResult,
                             previous_result: Optional[SimulationResult],
                             metric: str) -> str:
        """
        안정성 상세 정보 문자열 생성

        Args:
            current_result: 현재 결과
            previous_result: 이전 결과
            metric: 'score' 또는 'shots'

        Returns:
            상세 정보 문자열
        """
        if previous_result is None:
            return "N/A (첫 반복)"

        if metric == 'score':
            current = current_result.final_score['home'] + current_result.final_score['away']
            previous = previous_result.final_score['home'] + previous_result.final_score['away']
            diff = abs(current - previous)
            return f"이전 {previous}골 → 현재 {current}골 (차이 {diff}골)"

        elif metric == 'shots':
            current = current_result.stats.get('home_shots', 0) + current_result.stats.get('away_shots', 0)
            previous = previous_result.stats.get('home_shots', 0) + previous_result.stats.get('away_shots', 0)
            diff = abs(current - previous)
            return f"이전 {previous}개 → 현재 {current}개 (차이 {diff}개)"

        return "Unknown"

    def _get_convergence_reason(self, scores: Dict[str, float], is_converged: bool) -> str:
        """
        수렴 이유 문자열 생성

        Args:
            scores: 각 기준별 점수
            is_converged: 수렴 여부

        Returns:
            이유 문자열
        """
        if not is_converged:
            # 가장 낮은 점수 찾기
            min_score_key = min(scores, key=scores.get)
            min_score_value = scores[min_score_key]

            reasons_map = {
                'adherence': f"서사 일치율 부족 (점수: {min_score_value:.2f})",
                'ai_signal': f"AI가 조정 필요 신호 (점수: {min_score_value:.2f})",
                'iterations': f"반복 횟수 부족 (점수: {min_score_value:.2f})",
                'score_stability': f"득점 불안정 (점수: {min_score_value:.2f})",
                'shot_stability': f"슛 불안정 (점수: {min_score_value:.2f})",
            }

            return reasons_map.get(min_score_key, "수렴 미달")

        # 수렴 완료
        # 가장 높은 점수 찾기
        max_score_key = max(scores, key=scores.get)
        max_score_value = scores[max_score_key]

        reasons_map = {
            'adherence': f"서사 일치율 목표 달성 (점수: {max_score_value:.2f})",
            'ai_signal': f"AI 수렴 신호 (점수: {max_score_value:.2f})",
            'iterations': f"최대 반복 도달 (점수: {max_score_value:.2f})",
            'score_stability': f"득점 안정 (점수: {max_score_value:.2f})",
            'shot_stability': f"슛 안정 (점수: {max_score_value:.2f})",
        }

        return reasons_map.get(max_score_key, "수렴 완료")


# ==========================================================================
# Testing
# ==========================================================================

def test_convergence_judge():
    """Convergence Judge 테스트"""
    print("=== Convergence Judge 테스트 ===\n")

    judge = ConvergenceJudge()

    # Test 1: 높은 일치율 (수렴)
    print("Test 1: 높은 일치율 (수렴 예상)")

    analysis1 = AnalysisResult(
        status=AnalysisStatus.CONVERGED,
        analysis="서사 일치율 67% 달성"
    )

    result1 = SimulationResult(
        final_score={'home': 2, 'away': 1},
        events=[],
        narrative_adherence=0.67,
        stats={'home_shots': 15, 'away_shots': 12}
    )

    is_converged, info = judge.is_converged(analysis1, result1, None, iteration=2)

    print(f"  서사 일치율: {result1.narrative_adherence:.0%}")
    print(f"  AI 신호: {analysis1.status.value}")
    print(f"  가중 점수: {info['weighted_score']:.2f}")
    print(f"  수렴 여부: {'✅ Yes' if is_converged else '❌ No'}")
    print(f"  이유: {info['reason']}")
    assert is_converged, "높은 일치율은 수렴해야 함"
    print(f"  ✅ Test 1 통과\n")

    # Test 2: 낮은 일치율 (미수렴)
    print("Test 2: 낮은 일치율 (미수렴 예상)")

    analysis2 = AnalysisResult(
        status=AnalysisStatus.NEEDS_ADJUSTMENT,
        analysis="서사 일치율 33%, 조정 필요"
    )

    result2 = SimulationResult(
        final_score={'home': 1, 'away': 1},
        events=[],
        narrative_adherence=0.33,
        stats={'home_shots': 12, 'away_shots': 10}
    )

    is_converged2, info2 = judge.is_converged(analysis2, result2, None, iteration=1)

    print(f"  서사 일치율: {result2.narrative_adherence:.0%}")
    print(f"  AI 신호: {analysis2.status.value}")
    print(f"  가중 점수: {info2['weighted_score']:.2f}")
    print(f"  수렴 여부: {'✅ Yes' if is_converged2 else '❌ No'}")
    print(f"  이유: {info2['reason']}")
    assert not is_converged2, "낮은 일치율은 미수렴이어야 함"
    print(f"  ✅ Test 2 통과\n")

    # Test 3: 최대 반복 도달 (강제 수렴)
    print("Test 3: 최대 반복 도달 (강제 수렴 예상)")

    analysis3 = AnalysisResult(
        status=AnalysisStatus.MAX_ITERATIONS,
        analysis="최대 반복 도달"
    )

    result3 = SimulationResult(
        final_score={'home': 2, 'away': 2},
        events=[],
        narrative_adherence=0.50,  # 목표 미달이지만
        stats={'home_shots': 14, 'away_shots': 13}
    )

    is_converged3, info3 = judge.is_converged(analysis3, result3, None, iteration=5)  # 최대 5회

    print(f"  서사 일치율: {result3.narrative_adherence:.0%}")
    print(f"  반복 횟수: {5}/{judge.max_iterations}")
    print(f"  가중 점수: {info3['weighted_score']:.2f}")
    print(f"  수렴 여부: {'✅ Yes' if is_converged3 else '❌ No'}")
    print(f"  이유: {info3['reason']}")
    assert is_converged3, "최대 반복은 강제 수렴이어야 함"
    print(f"  ✅ Test 3 통과\n")

    # Test 4: 안정성 테스트
    print("Test 4: 안정성 테스트 (이전 결과 비교)")

    previous_result = SimulationResult(
        final_score={'home': 2, 'away': 1},
        events=[],
        narrative_adherence=0.50,
        stats={'home_shots': 14, 'away_shots': 11}
    )

    current_result_stable = SimulationResult(
        final_score={'home': 2, 'away': 1},  # 동일
        events=[],
        narrative_adherence=0.55,
        stats={'home_shots': 15, 'away_shots': 12}  # +2개 (안정)
    )

    analysis4 = AnalysisResult(
        status=AnalysisStatus.NEEDS_ADJUSTMENT,
        analysis="안정성 테스트"
    )

    is_converged4, info4 = judge.is_converged(
        analysis4, current_result_stable, previous_result, iteration=2
    )

    print(f"  득점 안정 점수: {info4['scores']['score_stability']:.2f}")
    print(f"  슛 안정 점수: {info4['scores']['shot_stability']:.2f}")
    print(f"  득점 상세: {info4['details']['score_stability']}")
    print(f"  슛 상세: {info4['details']['shot_stability']}")
    assert info4['scores']['score_stability'] == 1.0, "득점 동일 → 안정 점수 1.0"
    print(f"  ✅ Test 4 통과\n")

    print("=" * 60)
    print("✅ Convergence Judge 모든 테스트 통과!")
    print("=" * 60)


if __name__ == "__main__":
    test_convergence_judge()
