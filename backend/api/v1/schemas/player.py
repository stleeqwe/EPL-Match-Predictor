"""
Player API Schemas
선수 관련 요청/응답 스키마
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime

from core.domain.entities.player import Player


class PlayerStatsSchema(BaseModel):
    """선수 통계 스키마"""
    appearances: int = Field(ge=0, description="출전 횟수")
    starts: int = Field(ge=0, description="선발 출전")
    minutes: int = Field(ge=0, description="출전 시간")
    goals: int = Field(ge=0, description="골")
    assists: int = Field(ge=0, description="어시스트")
    clean_sheets: int = Field(default=0, ge=0, description="클린시트")

    @validator('starts')
    def starts_cannot_exceed_appearances(cls, v, values):
        if 'appearances' in values and v > values['appearances']:
            raise ValueError('Starts cannot exceed appearances')
        return v

    class Config:
        schema_extra = {
            "example": {
                "appearances": 15,
                "starts": 12,
                "minutes": 1080,
                "goals": 5,
                "assists": 3,
                "clean_sheets": 6
            }
        }


class PlayerResponse(BaseModel):
    """선수 정보 응답"""
    id: int = Field(description="선수 ID")
    external_id: int = Field(description="외부 API ID")
    name: str = Field(description="선수 이름")
    position: str = Field(description="포지션")
    detailed_position: str = Field(description="상세 포지션")
    team_id: int = Field(description="팀 ID")
    team_name: Optional[str] = Field(None, description="팀 이름")
    age: int = Field(ge=16, le=50, description="나이")
    photo_url: Optional[str] = Field(None, description="사진 URL")
    stats: PlayerStatsSchema = Field(description="통계")
    overall_rating: Optional[float] = Field(None, ge=0, le=5, description="종합 평점")
    form_score: float = Field(ge=0, le=10, description="폼 점수")
    is_starter: bool = Field(description="주전 여부")
    created_at: datetime
    updated_at: Optional[datetime]

    @classmethod
    def from_entity(cls, player: Player, team_name: str = None) -> 'PlayerResponse':
        """엔티티에서 스키마 생성"""
        return cls(
            id=player.id.value,
            external_id=player.external_id,
            name=player.name,
            position=player.position.general.value,
            detailed_position=player.position.detailed.value,
            team_id=player.team_id.value if hasattr(player.team_id, 'value') else player.team_id,
            team_name=team_name,
            age=player.age,
            photo_url=None,  # TODO: photo URL 처리
            stats=PlayerStatsSchema(
                appearances=player.stats.appearances,
                starts=player.stats.starts,
                minutes=player.stats.minutes,
                goals=player.stats.goals,
                assists=player.stats.assists,
                clean_sheets=getattr(player.stats, 'clean_sheets', 0)
            ),
            overall_rating=None,  # TODO: 평점 계산
            form_score=player.get_form_score(),
            is_starter=player.is_regular_starter(),
            created_at=getattr(player, 'created_at', datetime.utcnow()),
            updated_at=getattr(player, 'updated_at', None)
        )

    class Config:
        schema_extra = {
            "example": {
                "id": 123,
                "external_id": 456,
                "name": "Mohamed Salah",
                "position": "FW",
                "detailed_position": "WG",
                "team_id": 1,
                "team_name": "Liverpool",
                "age": 31,
                "photo_url": "https://...",
                "stats": {
                    "appearances": 15,
                    "starts": 14,
                    "minutes": 1260,
                    "goals": 12,
                    "assists": 8,
                    "clean_sheets": 0
                },
                "overall_rating": 4.5,
                "form_score": 9.2,
                "is_starter": True,
                "created_at": "2025-01-01T00:00:00",
                "updated_at": "2025-01-20T10:30:00"
            }
        }


class PlayerListResponse(BaseModel):
    """선수 목록 응답"""
    players: List[PlayerResponse]
    total: int = Field(description="전체 선수 수")
    limit: int = Field(description="페이지 크기")
    offset: int = Field(description="오프셋")

    class Config:
        schema_extra = {
            "example": {
                "players": [],
                "total": 500,
                "limit": 20,
                "offset": 0
            }
        }


class PlayerStatsResponse(BaseModel):
    """선수 통계 응답 (상세)"""
    player_id: int
    player_name: str
    stats: PlayerStatsSchema

    # 추가 통계
    minutes_per_appearance: float
    goals_per_90: float
    assists_per_90: float

    class Config:
        schema_extra = {
            "example": {
                "player_id": 123,
                "player_name": "Mohamed Salah",
                "stats": {
                    "appearances": 15,
                    "starts": 14,
                    "minutes": 1260,
                    "goals": 12,
                    "assists": 8,
                    "clean_sheets": 0
                },
                "minutes_per_appearance": 84.0,
                "goals_per_90": 0.86,
                "assists_per_90": 0.57
            }
        }
