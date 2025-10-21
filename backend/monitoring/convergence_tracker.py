"""
Convergence Tracker
수렴 패턴 모니터링 및 분석

장기적으로 convergence 패턴을 추적하여:
- 수렴률 분석
- Threshold 튜닝 데이터 축적
- 실패 케이스 분석
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path


class ConvergenceTracker:
    """
    Convergence pattern tracker

    수렴 패턴을 추적하고 분석하여 시뮬레이션 품질 모니터링
    """

    def __init__(self, log_file: Optional[str] = None):
        """
        Args:
            log_file: 로그 파일 경로 (None이면 메모리에만 저장)
        """
        self.convergence_history: List[Dict[str, Any]] = []
        self.log_file = log_file

        # 기존 로그 로드
        if log_file and Path(log_file).exists():
            self._load_from_file()

    def log_convergence(
        self,
        match_id: str,
        match_input: Dict[str, Any],
        convergence_info: Dict[str, Any],
        iterations: int
    ):
        """
        수렴 정보 기록

        Args:
            match_id: 경기 ID
            match_input: 경기 입력 정보 (MatchInput.to_dict())
            convergence_info: 수렴 정보
            iterations: 실제 반복 횟수
        """
        # 전력 차이 계산
        strength_diff = self._calculate_strength_diff(match_input)

        # 스타일 유사도 계산
        style_similarity = self._calculate_style_similarity(match_input)

        # 로그 엔트리 생성
        log_entry = {
            'match_id': match_id,
            'timestamp': datetime.now().isoformat(),
            'home_team': match_input.get('home_team', {}).get('name', 'Unknown'),
            'away_team': match_input.get('away_team', {}).get('name', 'Unknown'),
            'strength_diff': strength_diff,
            'style_similarity': style_similarity,
            'converged': convergence_info.get('is_converged', False),
            'convergence_score': convergence_info.get('weighted_score', 0.0),
            'iterations': iterations,
            'threshold': convergence_info.get('threshold', 0.7),
            'early_stopped': convergence_info.get('early_stopped', False),
            'convergence_fallback': convergence_info.get('convergence_fallback', False),
            'uncertainty': convergence_info.get('uncertainty', 0.0),
        }

        self.convergence_history.append(log_entry)

        # 파일에 저장 (append mode)
        if self.log_file:
            self._append_to_file(log_entry)

    def generate_report(self) -> Dict[str, Any]:
        """
        수렴 패턴 분석 리포트 생성

        Returns:
            분석 리포트 딕셔너리
        """
        if not self.convergence_history:
            return {
                'total_simulations': 0,
                'message': 'No data available'
            }

        # 기본 통계
        total = len(self.convergence_history)
        converged_count = sum(1 for entry in self.convergence_history if entry['converged'])
        early_stopped_count = sum(1 for entry in self.convergence_history if entry['early_stopped'])
        fallback_count = sum(1 for entry in self.convergence_history if entry['convergence_fallback'])

        # 반복 횟수 통계
        iterations_list = [entry['iterations'] for entry in self.convergence_history]
        avg_iterations = sum(iterations_list) / len(iterations_list)

        # 수렴 점수 통계
        scores = [entry['convergence_score'] for entry in self.convergence_history]
        avg_score = sum(scores) / len(scores)

        # 전력 차이별 수렴률
        convergence_by_strength = self._analyze_by_strength_diff()

        # 실패한 경기 목록
        failed_matches = [
            {
                'match_id': entry['match_id'],
                'teams': f"{entry['home_team']} vs {entry['away_team']}",
                'score': entry['convergence_score'],
                'iterations': entry['iterations']
            }
            for entry in self.convergence_history
            if not entry['converged']
        ]

        return {
            'total_simulations': total,
            'overall_convergence_rate': converged_count / total if total > 0 else 0,
            'early_stop_rate': early_stopped_count / total if total > 0 else 0,
            'fallback_rate': fallback_count / total if total > 0 else 0,
            'avg_iterations': avg_iterations,
            'avg_convergence_score': avg_score,
            'convergence_by_strength_diff': convergence_by_strength,
            'failed_matches': failed_matches,
            'recent_10': self.convergence_history[-10:] if len(self.convergence_history) >= 10 else self.convergence_history
        }

    def print_summary(self):
        """요약 리포트 출력"""
        report = self.generate_report()

        if report['total_simulations'] == 0:
            print("No convergence data available.")
            return

        print("\n" + "=" * 70)
        print("📊 Convergence Tracking Summary")
        print("=" * 70)

        print(f"\n총 시뮬레이션: {report['total_simulations']}")
        print(f"수렴률: {report['overall_convergence_rate']:.1%}")
        print(f"Early Stop 비율: {report['early_stop_rate']:.1%}")
        print(f"Fallback 비율: {report['fallback_rate']:.1%}")
        print(f"평균 반복 횟수: {report['avg_iterations']:.1f}")
        print(f"평균 수렴 점수: {report['avg_convergence_score']:.2f}")

        print("\n전력 차이별 수렴률:")
        for range_label, rate in report['convergence_by_strength_diff'].items():
            print(f"  {range_label}: {rate:.1%}")

        if report['failed_matches']:
            print(f"\n실패한 경기 ({len(report['failed_matches'])}개):")
            for match in report['failed_matches'][:5]:  # 최대 5개만 출력
                print(f"  - {match['teams']} (Score: {match['score']:.2f}, Iterations: {match['iterations']})")

        print("\n" + "=" * 70)

    def _calculate_strength_diff(self, match_input: Dict[str, Any]) -> float:
        """전력 차이 계산"""
        home_team = match_input.get('home_team', {})
        away_team = match_input.get('away_team', {})

        home_attack = home_team.get('attack_strength', 75)
        home_defense = home_team.get('defense_strength', 75)
        away_attack = away_team.get('attack_strength', 75)
        away_defense = away_team.get('defense_strength', 75)

        home_strength = (home_attack + home_defense) / 2
        away_strength = (away_attack + away_defense) / 2

        return abs(home_strength - away_strength)

    def _calculate_style_similarity(self, match_input: Dict[str, Any]) -> float:
        """스타일 유사도 계산"""
        home_team = match_input.get('home_team', {})
        away_team = match_input.get('away_team', {})

        home_style = home_team.get('buildup_style', 'mixed').lower()
        away_style = away_team.get('buildup_style', 'mixed').lower()

        style_map = {"direct": 0, "mixed": 0.5, "possession": 1}
        value1 = style_map.get(home_style, 0.5)
        value2 = style_map.get(away_style, 0.5)

        return 1 - abs(value1 - value2)

    def _analyze_by_strength_diff(self) -> Dict[str, float]:
        """전력 차이별 수렴률 분석"""
        ranges = {
            '0-10': (0, 10),
            '10-20': (10, 20),
            '20+': (20, 100)
        }

        results = {}
        for range_label, (min_diff, max_diff) in ranges.items():
            matches_in_range = [
                entry for entry in self.convergence_history
                if min_diff <= entry['strength_diff'] < max_diff
            ]

            if matches_in_range:
                converged_in_range = sum(1 for m in matches_in_range if m['converged'])
                results[range_label] = converged_in_range / len(matches_in_range)
            else:
                results[range_label] = 0.0

        return results

    def _load_from_file(self):
        """파일에서 로그 로드"""
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        entry = json.loads(line)
                        self.convergence_history.append(entry)
        except Exception as e:
            print(f"Warning: Failed to load convergence log: {e}")

    def _append_to_file(self, log_entry: Dict[str, Any]):
        """파일에 로그 추가"""
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
        except Exception as e:
            print(f"Warning: Failed to write convergence log: {e}")


# ==========================================================================
# Testing
# ==========================================================================

def test_convergence_tracker():
    """Convergence Tracker 테스트"""
    print("=== Convergence Tracker 테스트 ===\n")

    tracker = ConvergenceTracker()

    # Test 1: 수렴 성공 케이스
    match_input_1 = {
        'home_team': {
            'name': 'Man City',
            'attack_strength': 95,
            'defense_strength': 90,
            'buildup_style': 'possession'
        },
        'away_team': {
            'name': 'Sheffield',
            'attack_strength': 65,
            'defense_strength': 68,
            'buildup_style': 'direct'
        }
    }

    convergence_info_1 = {
        'is_converged': True,
        'weighted_score': 0.75,
        'early_stopped': True,
        'convergence_fallback': False,
        'uncertainty': 0.25
    }

    tracker.log_convergence(
        match_id='TEST_001',
        match_input=match_input_1,
        convergence_info=convergence_info_1,
        iterations=3
    )

    # Test 2: 수렴 실패 케이스
    match_input_2 = {
        'home_team': {
            'name': 'Arsenal',
            'attack_strength': 88,
            'defense_strength': 85,
            'buildup_style': 'possession'
        },
        'away_team': {
            'name': 'Liverpool',
            'attack_strength': 87,
            'defense_strength': 84,
            'buildup_style': 'possession'
        }
    }

    convergence_info_2 = {
        'is_converged': False,
        'weighted_score': 0.55,
        'early_stopped': False,
        'convergence_fallback': True,
        'uncertainty': 0.45
    }

    tracker.log_convergence(
        match_id='TEST_002',
        match_input=match_input_2,
        convergence_info=convergence_info_2,
        iterations=5
    )

    # Test 3: 리포트 생성
    tracker.print_summary()

    # 검증
    report = tracker.generate_report()
    assert report['total_simulations'] == 2
    assert report['overall_convergence_rate'] == 0.5  # 1/2
    assert report['early_stop_rate'] == 0.5  # 1/2
    assert report['fallback_rate'] == 0.5  # 1/2

    print("\n✅ Convergence Tracker 테스트 통과!")


if __name__ == "__main__":
    test_convergence_tracker()
