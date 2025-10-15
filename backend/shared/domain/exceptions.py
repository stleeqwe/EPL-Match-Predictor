"""
Shared Exceptions

모든 세그먼트에서 사용할 수 있는 공통 예외
"""


class DomainException(Exception):
    """기본 도메인 예외"""
    pass


class EntityNotFoundException(DomainException):
    """엔티티를 찾을 수 없음"""
    def __init__(self, entity_type: str, entity_id: str):
        self.entity_type = entity_type
        self.entity_id = entity_id
        super().__init__(f"{entity_type} with ID '{entity_id}' not found")


class ValidationError(DomainException):
    """검증 실패"""
    pass


class InvalidValueError(ValidationError):
    """유효하지 않은 값"""
    pass


class BusinessRuleViolation(DomainException):
    """비즈니스 규칙 위반"""
    pass
