"""
Ratings API Endpoints
평점 관련 API
"""
from fastapi import APIRouter, Depends, Path, Body, HTTPException
from typing import Dict
from sqlalchemy.orm import Session

from api.v1.schemas.rating import (
    RatingsInput,
    RatingsResponse,
    PlayerRatingsResponse
)
from api.v1.dependencies.database import get_db
from api.v1.dependencies.auth import get_current_user

router = APIRouter()


@router.post(
    "/{player_id}",
    response_model=RatingsResponse,
    summary="선수 평점 저장",
    description="선수의 능력치 평점을 저장합니다.",
    status_code=201
)
async def save_ratings(
    player_id: int = Path(..., gt=0, description="선수 ID"),
    ratings_input: RatingsInput = Body(..., description="평점 데이터"),
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> RatingsResponse:
    """선수 평점 저장"""
    # TODO: SaveRatingsUseCase 구현 및 연결
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.get(
    "/{player_id}",
    response_model=PlayerRatingsResponse,
    summary="선수 평점 조회"
)
async def get_ratings(
    player_id: int = Path(..., gt=0),
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> PlayerRatingsResponse:
    """선수 평점 조회"""
    # TODO: 평점 조회 유스케이스 구현
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.put(
    "/{player_id}/{attribute}",
    response_model=RatingsResponse,
    summary="단일 능력치 업데이트"
)
async def update_single_rating(
    player_id: int = Path(..., gt=0),
    attribute: str = Path(..., description="능력치 이름"),
    value: float = Body(..., ge=0, le=5, description="평점 값"),
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> RatingsResponse:
    """단일 능력치 업데이트"""
    # TODO: 단일 능력치 업데이트 유스케이스 구현
    raise HTTPException(status_code=501, detail="Not implemented yet")
