"""
Position Type - Shared Enum

모든 세그먼트에서 사용하는 포지션 타입 표준
"""

from enum import Enum


class PositionType(str, Enum):
    """
    표준 포지션 타입

    11가지 주요 포지션
    """
    # 골키퍼
    GK = "goalkeeper"

    # 수비수
    CB = "center_back"         # 중앙 수비수
    LB = "left_back"           # 왼쪽 풀백
    RB = "right_back"          # 오른쪽 풀백
    WB = "wing_back"           # 윙백 (3백 시스템)

    # 미드필더
    DM = "defensive_midfielder"     # 수비형 미드필더
    CM = "central_midfielder"       # 중앙 미드필더
    CAM = "attacking_midfielder"    # 공격형 미드필더
    LM = "left_midfielder"          # 왼쪽 미드필더
    RM = "right_midfielder"         # 오른쪽 미드필더

    # 공격수
    LW = "left_winger"         # 왼쪽 윙어
    RW = "right_winger"        # 오른쪽 윙어
    ST = "striker"             # 스트라이커
    CF = "center_forward"      # 중앙 포워드

    @property
    def is_defender(self) -> bool:
        """수비수 포지션인지"""
        return self in {
            PositionType.CB,
            PositionType.LB,
            PositionType.RB,
            PositionType.WB
        }

    @property
    def is_midfielder(self) -> bool:
        """미드필더 포지션인지"""
        return self in {
            PositionType.DM,
            PositionType.CM,
            PositionType.CAM,
            PositionType.LM,
            PositionType.RM
        }

    @property
    def is_forward(self) -> bool:
        """공격수 포지션인지"""
        return self in {
            PositionType.LW,
            PositionType.RW,
            PositionType.ST,
            PositionType.CF
        }

    @property
    def display_name(self) -> str:
        """표시용 이름"""
        names = {
            PositionType.GK: "골키퍼",
            PositionType.CB: "중앙 수비수",
            PositionType.LB: "왼쪽 풀백",
            PositionType.RB: "오른쪽 풀백",
            PositionType.WB: "윙백",
            PositionType.DM: "수비형 미드필더",
            PositionType.CM: "중앙 미드필더",
            PositionType.CAM: "공격형 미드필더",
            PositionType.LM: "왼쪽 미드필더",
            PositionType.RM: "오른쪽 미드필더",
            PositionType.LW: "왼쪽 윙어",
            PositionType.RW: "오른쪽 윙어",
            PositionType.ST: "스트라이커",
            PositionType.CF: "중앙 포워드",
        }
        return names.get(self, self.value)
