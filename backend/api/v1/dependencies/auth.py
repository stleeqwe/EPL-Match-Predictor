"""
Authentication Dependencies
인증 관련 의존성
"""
from fastapi import Header, HTTPException


async def get_current_user(
    authorization: str = Header(None)
) -> str:
    """현재 사용자 ID 반환"""
    # TODO: JWT 토큰 검증 구현
    # 현재는 기본 사용자 반환
    return "default"


async def get_current_user_optional(
    authorization: str = Header(None)
) -> str:
    """현재 사용자 ID 반환 (선택적)"""
    if not authorization:
        return "default"

    # TODO: JWT 토큰 검증 구현
    return "default"
