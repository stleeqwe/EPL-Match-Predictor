"""
Unit Tests for Formation Entity
"""

import pytest
import sys
from pathlib import Path

# Add paths
domain_path = Path(__file__).parent.parent.parent / "domain"
backend_path = Path(__file__).parent.parent.parent.parent.parent
if str(domain_path) not in sys.path:
    sys.path.insert(0, str(domain_path))
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from entities.formation import Formation
import shared.types.identifiers as identifiers
from shared.domain.position_type import PositionType
from shared.domain.field_coordinates import FieldCoordinates

FormationId = identifiers.FormationId


class TestFormationCreation:
    """Formation 생성 테스트"""

    @pytest.fixture
    def valid_blocking_rates(self):
        """유효한 차단률 데이터"""
        return {
            "central_penetration": 70.0,
            "wide_penetration": 65.0,
            "cutback": 60.0,
            "cross": 75.0,
            "throughball": 68.0,
            "longball": 55.0,
            "corner": 80.0,
            "freekick": 72.0,
            "counterattack": 62.0,
            "setpiece": 78.0,
            "individual": 50.0,
            "error": 85.0,
        }

    @pytest.fixture
    def valid_player_positions(self):
        """유효한 선수 포지션 데이터"""
        return {
            PositionType.GK: FieldCoordinates(x=-45.0, y=0.0),
            PositionType.CB: FieldCoordinates(x=-30.0, y=0.0),
            PositionType.LB: FieldCoordinates(x=-30.0, y=-20.0),
            PositionType.RB: FieldCoordinates(x=-30.0, y=20.0),
        }

    def test_create_valid_formation(self, valid_blocking_rates, valid_player_positions):
        """유효한 포메이션 생성"""
        formation = Formation(
            id=FormationId("4-3-3"),
            name="4-3-3 Formation",
            blocking_rates=valid_blocking_rates,
            player_positions=valid_player_positions,
            description="Standard attacking formation"
        )
        assert formation.id == "4-3-3"
        assert formation.name == "4-3-3 Formation"
        assert formation.description == "Standard attacking formation"

    def test_create_formation_without_description(self, valid_blocking_rates, valid_player_positions):
        """설명 없이 포메이션 생성"""
        formation = Formation(
            id=FormationId("4-4-2"),
            name="4-4-2 Formation",
            blocking_rates=valid_blocking_rates,
            player_positions=valid_player_positions
        )
        assert formation.description is None

    def test_create_formation_with_missing_blocking_rates_raises_error(self, valid_player_positions):
        """필수 차단률 누락 시 에러"""
        incomplete_rates = {
            "central_penetration": 70.0,
            "wide_penetration": 65.0,
            # 나머지 누락
        }
        with pytest.raises(ValueError, match="Missing blocking rates"):
            Formation(
                id=FormationId("4-3-3"),
                name="Test",
                blocking_rates=incomplete_rates,
                player_positions=valid_player_positions
            )

    def test_create_formation_with_invalid_blocking_rate_range_raises_error(self, valid_blocking_rates, valid_player_positions):
        """차단률 범위 초과 시 에러"""
        invalid_rates = valid_blocking_rates.copy()
        invalid_rates["central_penetration"] = 150.0  # 범위 초과

        with pytest.raises(ValueError, match="must be between 0 and 100"):
            Formation(
                id=FormationId("4-3-3"),
                name="Test",
                blocking_rates=invalid_rates,
                player_positions=valid_player_positions
            )

    def test_create_formation_without_goalkeeper_raises_error(self, valid_blocking_rates):
        """골키퍼 없는 포지션으로 생성 시 에러"""
        positions_without_gk = {
            PositionType.CB: FieldCoordinates(x=-30.0, y=0.0),
        }
        with pytest.raises(ValueError, match="must have a goalkeeper"):
            Formation(
                id=FormationId("test"),
                name="Test",
                blocking_rates=valid_blocking_rates,
                player_positions=positions_without_gk
            )


class TestFormationBlockingRates:
    """Formation 차단률 관련 테스트"""

    @pytest.fixture
    def formation(self):
        """테스트용 포메이션"""
        return Formation(
            id=FormationId("4-3-3"),
            name="4-3-3",
            blocking_rates={
                "central_penetration": 70.0,
                "wide_penetration": 65.0,
                "cutback": 60.0,
                "cross": 75.0,
                "throughball": 68.0,
                "longball": 55.0,
                "corner": 80.0,
                "freekick": 72.0,
                "counterattack": 62.0,
                "setpiece": 78.0,
                "individual": 50.0,
                "error": 85.0,
            },
            player_positions={PositionType.GK: FieldCoordinates(x=-45.0, y=0.0)}
        )

    def test_get_blocking_rate(self, formation):
        """차단률 조회"""
        rate = formation.get_blocking_rate("central_penetration")
        assert rate == 70.0

    def test_get_blocking_rate_for_unknown_category_raises_error(self, formation):
        """존재하지 않는 카테고리 조회 시 에러"""
        with pytest.raises(KeyError, match="Unknown goal category"):
            formation.get_blocking_rate("unknown_category")

    def test_calculate_overall_defensive_rating(self, formation):
        """전체 수비력 평가"""
        rating = formation.calculate_overall_defensive_rating()
        assert isinstance(rating, float)
        assert 0 <= rating <= 100

    def test_calculate_overall_attacking_vulnerability(self, formation):
        """공격 취약성 평가"""
        vulnerability = formation.calculate_overall_attacking_vulnerability()
        defensive_rating = formation.calculate_overall_defensive_rating()
        assert vulnerability == round(100 - defensive_rating, 2)


class TestFormationStyle:
    """Formation 스타일 판단 테스트"""

    def test_is_defensive_formation(self):
        """수비형 포메이션 판단"""
        formation = Formation(
            id=FormationId("5-3-2"),
            name="5-3-2",
            blocking_rates={
                "central_penetration": 75.0,
                "wide_penetration": 72.0,
                "cutback": 60.0,
                "cross": 75.0,
                "throughball": 68.0,
                "longball": 55.0,
                "corner": 80.0,
                "freekick": 72.0,
                "counterattack": 62.0,
                "setpiece": 78.0,
                "individual": 50.0,
                "error": 85.0,
            },
            player_positions={PositionType.GK: FieldCoordinates(x=-45.0, y=0.0)}
        )
        assert formation.is_defensive_formation() is True
        assert formation.get_formation_style() == "defensive"

    def test_is_attacking_formation(self):
        """공격형 포메이션 판단"""
        formation = Formation(
            id=FormationId("4-3-3"),
            name="4-3-3",
            blocking_rates={
                "central_penetration": 55.0,
                "wide_penetration": 50.0,
                "cutback": 60.0,
                "cross": 75.0,
                "throughball": 68.0,
                "longball": 55.0,
                "corner": 80.0,
                "freekick": 72.0,
                "counterattack": 62.0,
                "setpiece": 78.0,
                "individual": 50.0,
                "error": 85.0,
            },
            player_positions={PositionType.GK: FieldCoordinates(x=-45.0, y=0.0)}
        )
        assert formation.is_attacking_formation() is True
        assert formation.get_formation_style() == "attacking"

    def test_is_balanced_formation(self):
        """균형형 포메이션 판단"""
        formation = Formation(
            id=FormationId("4-4-2"),
            name="4-4-2",
            blocking_rates={
                "central_penetration": 65.0,
                "wide_penetration": 65.0,
                "cutback": 60.0,
                "cross": 75.0,
                "throughball": 68.0,
                "longball": 55.0,
                "corner": 80.0,
                "freekick": 72.0,
                "counterattack": 62.0,
                "setpiece": 78.0,
                "individual": 50.0,
                "error": 85.0,
            },
            player_positions={PositionType.GK: FieldCoordinates(x=-45.0, y=0.0)}
        )
        assert formation.is_balanced_formation() is True
        assert formation.get_formation_style() == "balanced"


class TestFormationPositions:
    """Formation 포지션 관련 테스트"""

    @pytest.fixture
    def formation_with_positions(self):
        """포지션이 있는 포메이션"""
        return Formation(
            id=FormationId("4-3-3"),
            name="4-3-3",
            blocking_rates={
                "central_penetration": 70.0,
                "wide_penetration": 65.0,
                "cutback": 60.0,
                "cross": 75.0,
                "throughball": 68.0,
                "longball": 55.0,
                "corner": 80.0,
                "freekick": 72.0,
                "counterattack": 62.0,
                "setpiece": 78.0,
                "individual": 50.0,
                "error": 85.0,
            },
            player_positions={
                PositionType.GK: FieldCoordinates(x=-45.0, y=0.0),
                PositionType.CB: FieldCoordinates(x=-30.0, y=0.0),
                PositionType.LB: FieldCoordinates(x=-30.0, y=-20.0),
                PositionType.RB: FieldCoordinates(x=-30.0, y=20.0),
                PositionType.CM: FieldCoordinates(x=0.0, y=0.0),
                PositionType.ST: FieldCoordinates(x=30.0, y=0.0),
            }
        )

    def test_get_position_coordinate(self, formation_with_positions):
        """포지션 좌표 조회"""
        gk_pos = formation_with_positions.get_position_coordinate(PositionType.GK)
        assert gk_pos == FieldCoordinates(x=-45.0, y=0.0)

    def test_get_position_coordinate_for_missing_position(self, formation_with_positions):
        """없는 포지션 조회 시 None 반환"""
        pos = formation_with_positions.get_position_coordinate(PositionType.LW)
        assert pos is None


class TestFormationEquality:
    """Formation 동등성 테스트"""

    @pytest.fixture
    def blocking_rates(self):
        return {
            "central_penetration": 70.0,
            "wide_penetration": 65.0,
            "cutback": 60.0,
            "cross": 75.0,
            "throughball": 68.0,
            "longball": 55.0,
            "corner": 80.0,
            "freekick": 72.0,
            "counterattack": 62.0,
            "setpiece": 78.0,
            "individual": 50.0,
            "error": 85.0,
        }

    def test_formations_with_same_id_are_equal(self, blocking_rates):
        """같은 ID의 포메이션은 동등"""
        f1 = Formation(
            id=FormationId("4-3-3"),
            name="Formation 1",
            blocking_rates=blocking_rates,
            player_positions={PositionType.GK: FieldCoordinates(x=-45.0, y=0.0)}
        )
        f2 = Formation(
            id=FormationId("4-3-3"),
            name="Formation 2",  # 이름이 달라도
            blocking_rates=blocking_rates,
            player_positions={PositionType.GK: FieldCoordinates(x=-45.0, y=0.0)}
        )
        assert f1 == f2

    def test_formations_with_different_id_are_not_equal(self, blocking_rates):
        """다른 ID의 포메이션은 동등하지 않음"""
        f1 = Formation(
            id=FormationId("4-3-3"),
            name="Test",
            blocking_rates=blocking_rates,
            player_positions={PositionType.GK: FieldCoordinates(x=-45.0, y=0.0)}
        )
        f2 = Formation(
            id=FormationId("4-4-2"),
            name="Test",
            blocking_rates=blocking_rates,
            player_positions={PositionType.GK: FieldCoordinates(x=-45.0, y=0.0)}
        )
        assert f1 != f2

    def test_formations_are_hashable(self, blocking_rates):
        """포메이션은 해싱 가능 (set, dict 키로 사용 가능)"""
        f1 = Formation(
            id=FormationId("4-3-3"),
            name="Test",
            blocking_rates=blocking_rates,
            player_positions={PositionType.GK: FieldCoordinates(x=-45.0, y=0.0)}
        )
        f2 = Formation(
            id=FormationId("4-4-2"),
            name="Test",
            blocking_rates=blocking_rates,
            player_positions={PositionType.GK: FieldCoordinates(x=-45.0, y=0.0)}
        )

        formation_set = {f1, f2}
        assert len(formation_set) == 2

        formation_dict = {f1: "first", f2: "second"}
        assert formation_dict[f1] == "first"


class TestFormationStringRepresentation:
    """Formation 문자열 표현 테스트"""

    def test_repr_includes_key_information(self):
        """repr에 주요 정보 포함"""
        formation = Formation(
            id=FormationId("4-3-3"),
            name="4-3-3 Attack",
            blocking_rates={
                "central_penetration": 55.0,
                "wide_penetration": 50.0,
                "cutback": 60.0,
                "cross": 75.0,
                "throughball": 68.0,
                "longball": 55.0,
                "corner": 80.0,
                "freekick": 72.0,
                "counterattack": 62.0,
                "setpiece": 78.0,
                "individual": 50.0,
                "error": 85.0,
            },
            player_positions={PositionType.GK: FieldCoordinates(x=-45.0, y=0.0)}
        )

        repr_str = repr(formation)
        assert "Formation" in repr_str
        assert "4-3-3" in repr_str
        assert "style=" in repr_str
        assert "defensive_rating=" in repr_str
