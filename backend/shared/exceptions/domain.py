"""
Domain Exception Classes
도메인 레벨 예외
"""
from shared.exceptions.base import AppException


class DomainException(AppException):
    """도메인 예외 기본 클래스"""
    pass


class PlayerNotFoundError(DomainException):
    """선수를 찾을 수 없음"""

    def __init__(self, message: str = "Player not found"):
        super().__init__(
            message=message,
            error_code="PLAYER_NOT_FOUND",
            status_code=404
        )


class InvalidRatingError(DomainException):
    """유효하지 않은 평점"""

    def __init__(self, message: str = "Invalid rating"):
        super().__init__(
            message=message,
            error_code="INVALID_RATING",
            status_code=400
        )


class TeamNotFoundError(DomainException):
    """팀을 찾을 수 없음"""

    def __init__(self, message: str = "Team not found"):
        super().__init__(
            message=message,
            error_code="TEAM_NOT_FOUND",
            status_code=404
        )


class MatchNotFoundError(DomainException):
    """경기를 찾을 수 없음"""

    def __init__(self, message: str = "Match not found"):
        super().__init__(
            message=message,
            error_code="MATCH_NOT_FOUND",
            status_code=404
        )


class ValidationError(DomainException):
    """검증 오류"""

    def __init__(self, message: str, details: dict = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=422,
            details=details
        )
