"""
Tactics Domain Exceptions

전술 세그먼트 도메인 계층의 예외 정의
Shared Kernel의 기본 예외를 확장
"""

import sys
from pathlib import Path

# Shared Kernel import - add backend to path
backend_path = Path(__file__).parent.parent.parent.parent
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from shared.domain.exceptions import (
    DomainException,
    EntityNotFoundException,
    ValidationError,
    BusinessRuleViolation,
)


class TacticsDomainException(DomainException):
    """전술 도메인 기본 예외"""
    pass


# Entity Exceptions
class FormationNotFoundException(EntityNotFoundException):
    """포메이션을 찾을 수 없음"""
    def __init__(self, formation_id: str):
        super().__init__("Formation", formation_id)


class TacticalStyleNotFoundException(EntityNotFoundException):
    """전술 스타일을 찾을 수 없음"""
    def __init__(self, style_id: str):
        super().__init__("TacticalStyle", style_id)


# Validation Exceptions
class InvalidBlockingRateError(ValidationError):
    """유효하지 않은 차단률"""
    def __init__(self, value: float, reason: str = ""):
        message = f"Invalid blocking rate: {value}"
        if reason:
            message += f" - {reason}"
        super().__init__(message)


class InvalidFormationShapeError(ValidationError):
    """유효하지 않은 포메이션 형태"""
    def __init__(self, shape: str, reason: str = ""):
        message = f"Invalid formation shape: {shape}"
        if reason:
            message += f" - {reason}"
        super().__init__(message)


class InvalidCoefficientError(ValidationError):
    """유효하지 않은 계수"""
    def __init__(self, coefficient_name: str, value: float, valid_range: tuple):
        message = (
            f"Invalid {coefficient_name}: {value}. "
            f"Must be between {valid_range[0]} and {valid_range[1]}"
        )
        super().__init__(message)


class InvalidFieldCoordinatesError(ValidationError):
    """유효하지 않은 필드 좌표"""
    def __init__(self, x: float, y: float, reason: str = ""):
        message = f"Invalid field coordinates: ({x}, {y})"
        if reason:
            message += f" - {reason}"
        super().__init__(message)


class MissingGoalCategoryError(ValidationError):
    """필수 골 카테고리 누락"""
    def __init__(self, missing_categories: set):
        categories_str = ", ".join(sorted(missing_categories))
        message = f"Missing required goal categories: {categories_str}"
        super().__init__(message)


# Business Rule Violations
class FormationPlayerCountViolation(BusinessRuleViolation):
    """포메이션 선수 수 규칙 위반"""
    def __init__(self, actual_count: int, expected_count: int = 11):
        message = (
            f"Formation must have {expected_count} players "
            f"(1 GK + 10 field players), got {actual_count}"
        )
        super().__init__(message)


class GoalkeeperRequiredViolation(BusinessRuleViolation):
    """골키퍼 필수 규칙 위반"""
    def __init__(self):
        super().__init__("Formation must have exactly one goalkeeper")


class FormationIntegrityViolation(BusinessRuleViolation):
    """포메이션 무결성 규칙 위반"""
    def __init__(self, reason: str):
        super().__init__(f"Formation integrity violation: {reason}")


class TacticalMatchupViolation(BusinessRuleViolation):
    """전술 매칭 규칙 위반"""
    def __init__(self, reason: str):
        super().__init__(f"Tactical matchup violation: {reason}")


# Repository Exceptions
class RepositoryError(TacticsDomainException):
    """저장소 오류"""
    pass


class FormationAlreadyExistsError(RepositoryError):
    """포메이션이 이미 존재함"""
    def __init__(self, formation_id: str):
        super().__init__(f"Formation '{formation_id}' already exists")


class FormationPersistenceError(RepositoryError):
    """포메이션 저장 오류"""
    def __init__(self, formation_id: str, reason: str = ""):
        message = f"Failed to persist formation '{formation_id}'"
        if reason:
            message += f": {reason}"
        super().__init__(message)


class FormationDataCorruptedError(RepositoryError):
    """포메이션 데이터 손상"""
    def __init__(self, formation_id: str, reason: str = ""):
        message = f"Formation data corrupted for '{formation_id}'"
        if reason:
            message += f": {reason}"
        super().__init__(message)


# Calculation Exceptions
class TacticalCalculationError(TacticsDomainException):
    """전술 계산 오류"""
    pass


class BlockingRateCalculationError(TacticalCalculationError):
    """차단률 계산 오류"""
    def __init__(self, reason: str):
        super().__init__(f"Failed to calculate blocking rate: {reason}")


class FormationEffectivenessCalculationError(TacticalCalculationError):
    """포메이션 효과성 계산 오류"""
    def __init__(self, formation_id: str, reason: str):
        super().__init__(
            f"Failed to calculate formation effectiveness for '{formation_id}': {reason}"
        )


# Configuration Exceptions
class InvalidTacticalConfigurationError(TacticsDomainException):
    """유효하지 않은 전술 설정"""
    def __init__(self, reason: str):
        super().__init__(f"Invalid tactical configuration: {reason}")
