"""
Players API Endpoints
선수 관련 API
"""
from fastapi import APIRouter, Depends, Query, Path, HTTPException
from typing import List, Optional

from api.v1.schemas.player import (
    PlayerResponse,
    PlayerListResponse,
    PlayerStatsResponse
)
from api.v1.dependencies.database import get_db
from core.use_cases.get_player import GetPlayerUseCase, GetPlayerRequest
from shared.exceptions.domain import PlayerNotFoundError
from sqlalchemy.orm import Session

router = APIRouter()


@router.get(
    "/{player_id}",
    response_model=PlayerResponse,
    summary="선수 정보 조회",
    description="선수 ID로 상세 정보를 조회합니다.",
    responses={
        200: {"description": "성공"},
        404: {"description": "선수를 찾을 수 없음"}
    }
)
async def get_player(
    player_id: int = Path(..., gt=0, description="선수 ID"),
    db: Session = Depends(get_db)
) -> PlayerResponse:
    """선수 정보 조회"""
    try:
        # TODO: Repository 구현 후 실제 use case 연결
        # use_case = GetPlayerUseCase(player_repository)
        # request = GetPlayerRequest(player_id=player_id)
        # response = use_case.execute(request)
        # return PlayerResponse.from_entity(response.player)

        # 임시 구현
        raise HTTPException(status_code=501, detail="Not implemented yet")
    except PlayerNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/",
    response_model=PlayerListResponse,
    summary="선수 목록 조회",
    description="필터 조건에 따라 선수 목록을 조회합니다."
)
async def list_players(
    team_id: Optional[int] = Query(None, description="팀 ID"),
    position: Optional[str] = Query(None, description="포지션 (GK/DF/MF/FW)"),
    min_rating: Optional[float] = Query(None, ge=0, le=5, description="최소 평점"),
    limit: int = Query(20, ge=1, le=100, description="페이지 크기"),
    offset: int = Query(0, ge=0, description="오프셋"),
    db: Session = Depends(get_db)
) -> PlayerListResponse:
    """선수 목록 조회"""
    # TODO: 필터링 유스케이스 구현
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.get(
    "/{player_id}/stats",
    response_model=PlayerStatsResponse,
    summary="선수 통계 조회"
)
async def get_player_stats(
    player_id: int = Path(..., gt=0),
    db: Session = Depends(get_db)
) -> PlayerStatsResponse:
    """선수 통계 조회"""
    # TODO: 통계 조회 유스케이스 구현
    raise HTTPException(status_code=501, detail="Not implemented yet")
