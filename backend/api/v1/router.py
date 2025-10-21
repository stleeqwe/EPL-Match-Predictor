"""
API v1 Router
모든 v1 엔드포인트 통합
"""
from fastapi import APIRouter

from api.v1.endpoints import players, ratings

api_router = APIRouter()

# 엔드포인트 등록
api_router.include_router(
    players.router,
    prefix="/players",
    tags=["Players"]
)

api_router.include_router(
    ratings.router,
    prefix="/ratings",
    tags=["Ratings"]
)
