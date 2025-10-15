"""
전술 스타일 파라미터

수비/공격/전환 전술 파라미터 정의 및 관리
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class DefensiveParameters:
    """수비 전술 파라미터"""

    pressing_intensity: int = 5  # 압박 강도 (1-10)
    defensive_line: int = 5  # 수비 라인 높이 (1-10: 1=낮음, 10=높음)
    defensive_width: int = 5  # 수비 폭 (1-10: 1=좁음, 10=넓음)
    compactness: int = 5  # 밀집도 (1-10: 1=느슨함, 10=밀집)
    line_distance: float = 12.0  # 라인 간 거리 (m)

    def __post_init__(self):
        """유효성 검사"""
        self._validate_range('pressing_intensity', 1, 10)
        self._validate_range('defensive_line', 1, 10)
        self._validate_range('defensive_width', 1, 10)
        self._validate_range('compactness', 1, 10)

        if not (8.0 <= self.line_distance <= 20.0):
            raise ValueError("line_distance must be between 8.0 and 20.0")

    def _validate_range(self, param_name: str, min_val: int, max_val: int):
        value = getattr(self, param_name)
        if not (min_val <= value <= max_val):
            raise ValueError(f"{param_name} must be between {min_val} and {max_val}")

    def to_dict(self) -> Dict:
        return {
            'pressing_intensity': self.pressing_intensity,
            'defensive_line': self.defensive_line,
            'defensive_width': self.defensive_width,
            'compactness': self.compactness,
            'line_distance': self.line_distance
        }


@dataclass
class OffensiveParameters:
    """공격 전술 파라미터"""

    tempo: int = 5  # 템포 (1-10: 1=느림, 10=빠름)
    buildup_style: str = "balanced"  # short_passing, direct, balanced
    width: int = 5  # 공격 폭 (1-10: 1=중앙 집중, 10=측면 활용)
    creativity: int = 5  # 창의성 (1-10: 1=구조적, 10=자유로움)
    passing_directness: int = 5  # 패스 직접성 (1-10)

    def __post_init__(self):
        """유효성 검사"""
        valid_styles = ["short_passing", "direct", "balanced", "mixed"]
        if self.buildup_style not in valid_styles:
            raise ValueError(f"buildup_style must be one of {valid_styles}")

        self._validate_range('tempo', 1, 10)
        self._validate_range('width', 1, 10)
        self._validate_range('creativity', 1, 10)
        self._validate_range('passing_directness', 1, 10)

    def _validate_range(self, param_name: str, min_val: int, max_val: int):
        value = getattr(self, param_name)
        if not (min_val <= value <= max_val):
            raise ValueError(f"{param_name} must be between {min_val} and {max_val}")

    def to_dict(self) -> Dict:
        return {
            'tempo': self.tempo,
            'buildup_style': self.buildup_style,
            'width': self.width,
            'creativity': self.creativity,
            'passing_directness': self.passing_directness
        }


@dataclass
class TransitionParameters:
    """전환 전술 파라미터"""

    counter_press: int = 5  # 압박 후 전환 (1-10)
    counter_speed: int = 5  # 역습 속도 (1-10)
    transition_time: float = 3.5  # 평균 전환 시간 (초)
    recovery_speed: int = 5  # 복귀 속도 (1-10)

    def __post_init__(self):
        """유효성 검사"""
        self._validate_range('counter_press', 1, 10)
        self._validate_range('counter_speed', 1, 10)
        self._validate_range('recovery_speed', 1, 10)

        if not (1.0 <= self.transition_time <= 10.0):
            raise ValueError("transition_time must be between 1.0 and 10.0")

    def _validate_range(self, param_name: str, min_val: int, max_val: int):
        value = getattr(self, param_name)
        if not (min_val <= value <= max_val):
            raise ValueError(f"{param_name} must be between {min_val} and {max_val}")

    def to_dict(self) -> Dict:
        return {
            'counter_press': self.counter_press,
            'counter_speed': self.counter_speed,
            'transition_time': self.transition_time,
            'recovery_speed': self.recovery_speed
        }


@dataclass
class TacticalStyle:
    """통합 전술 스타일"""

    name: str
    defensive: DefensiveParameters = field(default_factory=DefensiveParameters)
    offensive: OffensiveParameters = field(default_factory=OffensiveParameters)
    transition: TransitionParameters = field(default_factory=TransitionParameters)
    description: str = ""

    def to_dict(self) -> Dict:
        """딕셔너리로 변환"""
        return {
            'name': self.name,
            'description': self.description,
            'defensive': self.defensive.to_dict(),
            'offensive': self.offensive.to_dict(),
            'transition': self.transition.to_dict()
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'TacticalStyle':
        """딕셔너리로부터 생성"""
        return cls(
            name=data['name'],
            description=data.get('description', ''),
            defensive=DefensiveParameters(**data.get('defensive', {})),
            offensive=OffensiveParameters(**data.get('offensive', {})),
            transition=TransitionParameters(**data.get('transition', {}))
        )

    @classmethod
    def from_formation(cls, formation_name: str, formation_data: Dict) -> 'TacticalStyle':
        """
        포메이션 데이터로부터 전술 스타일 생성

        Args:
            formation_name: 포메이션 이름
            formation_data: formations.json의 포메이션 데이터

        Returns:
            TacticalStyle 인스턴스
        """
        tactics = formation_data.get('default_tactics', {})

        defensive = DefensiveParameters(
            pressing_intensity=tactics.get('pressing_intensity', 5),
            defensive_line=tactics.get('defensive_line', 5),
            defensive_width=tactics.get('defensive_width', 5),
            compactness=tactics.get('compactness', 5),
            line_distance=12.0  # 기본값
        )

        offensive = OffensiveParameters(
            tempo=tactics.get('tempo', 5),
            buildup_style=tactics.get('buildup_style', 'balanced'),
            width=tactics.get('width', 5),
            creativity=tactics.get('creativity', 5),
            passing_directness=5  # 기본값
        )

        transition = TransitionParameters(
            counter_press=tactics.get('counter_press', 5),
            counter_speed=5,  # 기본값
            transition_time=3.5,  # 기본값
            recovery_speed=5  # 기본값
        )

        return cls(
            name=formation_name,
            description=formation_data.get('philosophy', ''),
            defensive=defensive,
            offensive=offensive,
            transition=transition
        )


class TacticalPresets:
    """유명 전술 프리셋"""

    @staticmethod
    def get_tiki_taka() -> TacticalStyle:
        """티키타카 (Barcelona 2008-2012, Spain 2008-2012)"""
        return TacticalStyle(
            name="Tiki-Taka",
            description="숏패스 기반 점유율 축구, 높은 압박",
            defensive=DefensiveParameters(
                pressing_intensity=9,
                defensive_line=8,
                defensive_width=9,
                compactness=8,
                line_distance=10.0
            ),
            offensive=OffensiveParameters(
                tempo=7,
                buildup_style="short_passing",
                width=9,
                creativity=8,
                passing_directness=3
            ),
            transition=TransitionParameters(
                counter_press=10,
                counter_speed=6,
                transition_time=2.0,
                recovery_speed=8
            )
        )

    @staticmethod
    def get_gegenpressing() -> TacticalStyle:
        """게겐프레싱 (Liverpool Klopp, Dortmund Klopp)"""
        return TacticalStyle(
            name="Gegenpressing",
            description="볼 상실 즉시 강력한 압박, 빠른 전환",
            defensive=DefensiveParameters(
                pressing_intensity=10,
                defensive_line=7,
                defensive_width=8,
                compactness=7,
                line_distance=11.0
            ),
            offensive=OffensiveParameters(
                tempo=9,
                buildup_style="direct",
                width=8,
                creativity=7,
                passing_directness=7
            ),
            transition=TransitionParameters(
                counter_press=10,
                counter_speed=10,
                transition_time=1.5,
                recovery_speed=9
            )
        )

    @staticmethod
    def get_catenaccio() -> TacticalStyle:
        """카테나치오 (Atletico Madrid Simeone)"""
        return TacticalStyle(
            name="Catenaccio",
            description="극단적 수비 중심, 로우 블록, 역습",
            defensive=DefensiveParameters(
                pressing_intensity=3,
                defensive_line=2,
                defensive_width=5,
                compactness=10,
                line_distance=8.0
            ),
            offensive=OffensiveParameters(
                tempo=4,
                buildup_style="direct",
                width=4,
                creativity=5,
                passing_directness=8
            ),
            transition=TransitionParameters(
                counter_press=4,
                counter_speed=9,
                transition_time=4.5,
                recovery_speed=6
            )
        )

    @staticmethod
    def get_total_football() -> TacticalStyle:
        """토탈 풋볼 (Ajax, Netherlands)"""
        return TacticalStyle(
            name="Total Football",
            description="유동적 포지션 변화, 전방위 압박",
            defensive=DefensiveParameters(
                pressing_intensity=9,
                defensive_line=9,
                defensive_width=8,
                compactness=7,
                line_distance=12.0
            ),
            offensive=OffensiveParameters(
                tempo=8,
                buildup_style="short_passing",
                width=8,
                creativity=10,
                passing_directness=5
            ),
            transition=TransitionParameters(
                counter_press=9,
                counter_speed=8,
                transition_time=2.5,
                recovery_speed=9
            )
        )

    @staticmethod
    def list_presets() -> List[str]:
        """사용 가능한 프리셋 목록"""
        return [
            "Tiki-Taka",
            "Gegenpressing",
            "Catenaccio",
            "Total Football"
        ]


# 사용 예시
if __name__ == "__main__":
    # 커스텀 전술 생성
    print("=== 커스텀 전술 스타일 ===")
    custom_tactics = TacticalStyle(
        name="Custom High Press",
        description="맞춤형 하이 프레스 전술",
        defensive=DefensiveParameters(
            pressing_intensity=8,
            defensive_line=7,
            defensive_width=7,
            compactness=7
        ),
        offensive=OffensiveParameters(
            tempo=8,
            buildup_style="balanced",
            width=7,
            creativity=7
        ),
        transition=TransitionParameters(
            counter_press=8,
            counter_speed=7,
            transition_time=3.0,
            recovery_speed=7
        )
    )

    print(f"이름: {custom_tactics.name}")
    print(f"설명: {custom_tactics.description}")
    print(f"압박 강도: {custom_tactics.defensive.pressing_intensity}/10")
    print(f"템포: {custom_tactics.offensive.tempo}/10")

    # 프리셋 사용
    print("\n=== 티키타카 프리셋 ===")
    tiki_taka = TacticalPresets.get_tiki_taka()
    print(f"이름: {tiki_taka.name}")
    print(f"압박 강도: {tiki_taka.defensive.pressing_intensity}/10")
    print(f"수비 라인: {tiki_taka.defensive.defensive_line}/10")
    print(f"빌드업 스타일: {tiki_taka.offensive.buildup_style}")
    print(f"전환 시간: {tiki_taka.transition.transition_time}초")

    # 딕셔너리 변환
    print("\n=== 딕셔너리 변환 ===")
    tactics_dict = tiki_taka.to_dict()
    print(tactics_dict)
