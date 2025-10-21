"""
Base Exception Classes
기본 예외 클래스
"""


class AppException(Exception):
    """애플리케이션 기본 예외"""

    def __init__(
        self,
        message: str,
        error_code: str = None,
        status_code: int = 400,
        details: dict = None
    ):
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.status_code = status_code
        self.details = details or {}

        super().__init__(self.message)
