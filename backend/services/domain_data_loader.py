"""
Domain Data Loader
사용자가 입력한 Domain 지식을 로드하여 AI 시뮬레이션에 전달
"""

import os
import json
from typing import Dict, Optional, Any
from dataclasses import dataclass


@dataclass
class TeamDomainData:
    """팀의 모든 Domain 데이터를 담는 컨테이너"""
    team_name: str
    formation: Optional[str] = None
    lineup: Optional[Dict[str, int]] = None  # {position: player_id}
    team_strength: Optional[Dict[str, float]] = None  # 18개 속성
    team_strength_comment: Optional[str] = None
    tactics: Optional[Dict[str, Any]] = None
    overall_score: Optional[Dict[str, float]] = None


class DomainDataLoader:
    """Backend에 저장된 Domain 데이터를 로드"""

    def __init__(self, data_root: str = None):
        """
        Args:
            data_root: 데이터 루트 디렉토리 (기본값: backend/data)
        """
        if data_root is None:
            # 현재 파일에서 backend/data 경로 계산
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.data_root = os.path.join(current_dir, '..', 'data')
        else:
            self.data_root = data_root

        self.formations_dir = os.path.join(self.data_root, 'formations')
        self.lineups_dir = os.path.join(self.data_root, 'lineups')
        self.team_strength_dir = os.path.join(self.data_root, 'team_strength')
        self.tactics_dir = os.path.join(self.data_root, 'tactics')
        self.overall_scores_dir = os.path.join(self.data_root, 'overall_scores')

    def load_formation(self, team_name: str) -> Optional[str]:
        """
        팀의 포메이션 로드

        Returns:
            formation (예: "4-3-3") or None
        """
        file_path = os.path.join(self.formations_dir, f"{team_name}.json")

        if not os.path.exists(file_path):
            return None

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('formation')
        except Exception as e:
            print(f"⚠️ Failed to load formation for {team_name}: {e}")
            return None

    def load_lineup(self, team_name: str) -> Optional[Dict[str, int]]:
        """
        팀의 라인업 로드

        Returns:
            lineup dict {position: player_id} or None
        """
        file_path = os.path.join(self.lineups_dir, f"{team_name}.json")

        if not os.path.exists(file_path):
            return None

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('lineup')
        except Exception as e:
            print(f"⚠️ Failed to load lineup for {team_name}: {e}")
            return None

    def load_team_strength(self, team_name: str) -> Optional[Dict[str, Any]]:
        """
        팀 전력 분석 로드 (18개 속성)

        Returns:
            {
                'ratings': {attr: value, ...},
                'comment': str
            } or None
        """
        file_path = os.path.join(self.team_strength_dir, f"{team_name}.json")

        if not os.path.exists(file_path):
            return None

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {
                    'ratings': data.get('ratings', {}),
                    'comment': data.get('comment', '')
                }
        except Exception as e:
            print(f"⚠️ Failed to load team strength for {team_name}: {e}")
            return None

    def load_tactics(self, team_name: str) -> Optional[Dict[str, Any]]:
        """
        팀 전술 설정 로드

        Returns:
            {
                'defensive': {...},
                'offensive': {...},
                'transition': {...}
            } or None
        """
        file_path = os.path.join(self.tactics_dir, f"{team_name}.json")

        if not os.path.exists(file_path):
            return None

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {
                    'defensive': data.get('defensive', {}),
                    'offensive': data.get('offensive', {}),
                    'transition': data.get('transition', {})
                }
        except Exception as e:
            print(f"⚠️ Failed to load tactics for {team_name}: {e}")
            return None

    def load_overall_score(self, team_name: str) -> Optional[Dict[str, float]]:
        """
        팀 종합 점수 로드

        Returns:
            {
                'overallScore': float,
                'playerScore': float,
                'strengthScore': float,
                'playerWeight': float,
                'strengthWeight': float
            } or None
        """
        file_path = os.path.join(self.overall_scores_dir, f"{team_name}.json")

        if not os.path.exists(file_path):
            return None

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data
        except Exception as e:
            print(f"⚠️ Failed to load overall score for {team_name}: {e}")
            return None

    def load_all(self, team_name: str) -> TeamDomainData:
        """
        팀의 모든 Domain 데이터를 한 번에 로드

        Args:
            team_name: 팀 이름

        Returns:
            TeamDomainData 객체
        """
        formation = self.load_formation(team_name)
        lineup = self.load_lineup(team_name)

        # Team Strength
        team_strength_data = self.load_team_strength(team_name)
        team_strength_ratings = None
        team_strength_comment = None
        if team_strength_data:
            team_strength_ratings = team_strength_data.get('ratings')
            team_strength_comment = team_strength_data.get('comment')

        tactics = self.load_tactics(team_name)
        overall_score = self.load_overall_score(team_name)

        return TeamDomainData(
            team_name=team_name,
            formation=formation,
            lineup=lineup,
            team_strength=team_strength_ratings,
            team_strength_comment=team_strength_comment,
            tactics=tactics,
            overall_score=overall_score
        )

    def get_data_summary(self, team_name: str) -> Dict[str, bool]:
        """
        팀의 데이터 준비 상태 확인

        Returns:
            {
                'formation': bool,
                'lineup': bool,
                'team_strength': bool,
                'tactics': bool,
                'overall_score': bool
            }
        """
        return {
            'formation': self.load_formation(team_name) is not None,
            'lineup': self.load_lineup(team_name) is not None,
            'team_strength': self.load_team_strength(team_name) is not None,
            'tactics': self.load_tactics(team_name) is not None,
            'overall_score': self.load_overall_score(team_name) is not None
        }


# 전역 인스턴스
_loader_instance = None

def get_domain_data_loader() -> DomainDataLoader:
    """싱글톤 패턴으로 DomainDataLoader 인스턴스 반환"""
    global _loader_instance
    if _loader_instance is None:
        _loader_instance = DomainDataLoader()
    return _loader_instance
