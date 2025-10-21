"""
Rating API Schemas
평점 관련 요청/응답 스키마
"""
from pydantic import BaseModel, Field, validator
from typing import Dict, Optional


class RatingsInput(BaseModel):
    """평점 입력 스키마"""
    ratings: Dict[str, float] = Field(..., description="능력치 평점")
    comment: Optional[str] = Field(None, max_length=500, description="코멘트")

    @validator('ratings')
    def validate_ratings(cls, v):
        """평점 검증"""
        if not v:
            raise ValueError("At least one rating is required")

        for attribute, value in v.items():
            # 값 범위 체크
            if not (0.0 <= value <= 5.0):
                raise ValueError(f"{attribute}: Rating must be between 0.0 and 5.0")

            # 0.25 단위 체크
            if round(value / 0.25) * 0.25 != value:
                raise ValueError(f"{attribute}: Rating must be in 0.25 increments")

        return v

    class Config:
        schema_extra = {
            "example": {
                "ratings": {
                    "finishing": 4.75,
                    "shot_power": 4.5,
                    "composure": 4.0,
                    "off_ball_movement": 4.5,
                    "hold_up_play": 3.75,
                    "heading": 3.5
                },
                "comment": "월드클래스 스트라이커"
            }
        }


class RatingsResponse(BaseModel):
    """평점 저장 응답"""
    player_id: int = Field(description="선수 ID")
    overall_rating: float = Field(ge=0, le=5, description="종합 평점")
    saved_count: int = Field(ge=0, description="저장된 능력치 수")

    class Config:
        schema_extra = {
            "example": {
                "player_id": 123,
                "overall_rating": 4.48,
                "saved_count": 9
            }
        }


class AttributeRatingSchema(BaseModel):
    """개별 능력치 평점 스키마"""
    attribute_name: str = Field(description="능력치 이름")
    value: float = Field(ge=0, le=5, description="평점")
    weight: float = Field(ge=0, le=1, description="가중치")
    comment: Optional[str] = Field(None, description="코멘트")


class PlayerRatingsResponse(BaseModel):
    """선수 평점 조회 응답"""
    player_id: int
    player_name: str
    position: str
    detailed_position: str
    ratings: Dict[str, AttributeRatingSchema]
    overall_rating: float = Field(ge=0, le=5)
    comment: Optional[str]
    updated_at: str

    class Config:
        schema_extra = {
            "example": {
                "player_id": 123,
                "player_name": "Mohamed Salah",
                "position": "FW",
                "detailed_position": "ST",
                "ratings": {
                    "finishing": {
                        "attribute_name": "finishing",
                        "value": 4.75,
                        "weight": 0.15,
                        "comment": ""
                    }
                },
                "overall_rating": 4.48,
                "comment": "월드클래스 스트라이커",
                "updated_at": "2025-01-20T10:30:00"
            }
        }
