"""
데이터베이스 스키마 정의
SQLite 사용 (나중에 PostgreSQL로 마이그레이션 가능)
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, Date, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime

Base = declarative_base()

class Team(Base):
    """팀 정보"""
    __tablename__ = 'teams'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    short_name = Column(String(50))
    league = Column(String(50))  # EPL, LaLiga 등

    # Relationships
    home_matches = relationship("Match", foreign_keys="Match.home_team_id", back_populates="home_team")
    away_matches = relationship("Match", foreign_keys="Match.away_team_id", back_populates="away_team")
    stats = relationship("TeamStats", back_populates="team")
    players = relationship("Player", back_populates="team")
    standings = relationship("Standings", back_populates="team")

class Match(Base):
    """경기 정보"""
    __tablename__ = 'matches'

    id = Column(Integer, primary_key=True)
    season = Column(String(20))  # 2023-24
    gameweek = Column(Integer)
    match_date = Column(DateTime)

    home_team_id = Column(Integer, ForeignKey('teams.id'))
    away_team_id = Column(Integer, ForeignKey('teams.id'))

    home_score = Column(Integer)
    away_score = Column(Integer)

    # xG 데이터
    home_xg = Column(Float)
    away_xg = Column(Float)

    # 경기 상태
    status = Column(String(20))  # scheduled, completed, postponed

    # Relationships
    home_team = relationship("Team", foreign_keys=[home_team_id], back_populates="home_matches")
    away_team = relationship("Team", foreign_keys=[away_team_id], back_populates="away_matches")
    detailed_stats = relationship("MatchStats", back_populates="match", uselist=False)

class MatchStats(Base):
    """경기 상세 통계"""
    __tablename__ = 'match_stats'

    id = Column(Integer, primary_key=True)
    match_id = Column(Integer, ForeignKey('matches.id'))

    # 홈팀 통계
    home_shots = Column(Integer)
    home_shots_on_target = Column(Integer)
    home_possession = Column(Float)
    home_passes = Column(Integer)
    home_pass_accuracy = Column(Float)
    home_corners = Column(Integer)
    home_fouls = Column(Integer)
    home_yellow_cards = Column(Integer)
    home_red_cards = Column(Integer)

    # 원정팀 통계
    away_shots = Column(Integer)
    away_shots_on_target = Column(Integer)
    away_possession = Column(Float)
    away_passes = Column(Integer)
    away_pass_accuracy = Column(Float)
    away_corners = Column(Integer)
    away_fouls = Column(Integer)
    away_yellow_cards = Column(Integer)
    away_red_cards = Column(Integer)

    # Relationship
    match = relationship("Match", back_populates="detailed_stats")

class TeamStats(Base):
    """팀 시즌 통계 (집계)"""
    __tablename__ = 'team_stats'

    id = Column(Integer, primary_key=True)
    team_id = Column(Integer, ForeignKey('teams.id'))
    season = Column(String(20))

    # 기본 성적
    matches_played = Column(Integer, default=0)
    wins = Column(Integer, default=0)
    draws = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    goals_for = Column(Integer, default=0)
    goals_against = Column(Integer, default=0)
    points = Column(Integer, default=0)

    # xG 집계
    xg_for = Column(Float, default=0.0)
    xg_against = Column(Float, default=0.0)

    # 홈/원정 분리
    home_wins = Column(Integer, default=0)
    home_draws = Column(Integer, default=0)
    home_losses = Column(Integer, default=0)
    away_wins = Column(Integer, default=0)
    away_draws = Column(Integer, default=0)
    away_losses = Column(Integer, default=0)

    # Pi-rating
    pi_rating_home = Column(Float, default=0.0)
    pi_rating_away = Column(Float, default=0.0)

    # Relationship
    team = relationship("Team", back_populates="stats")

class Player(Base):
    """선수 정보"""
    __tablename__ = 'players'

    id = Column(Integer, primary_key=True)
    team_id = Column(Integer, ForeignKey('teams.id'))

    name = Column(String(100), nullable=False)
    position = Column(String(20))  # ST, W, AM, DM, CB, FB, GK
    number = Column(Integer)
    age = Column(Integer)
    nationality = Column(String(50))

    # Relationship
    team = relationship("Team", back_populates="players")
    ratings = relationship("PlayerRating", back_populates="player")

class PlayerRating(Base):
    """선수 능력치 (개인 분석용)"""
    __tablename__ = 'player_ratings'

    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey('players.id'))

    # 능력치 (포지션별로 다름)
    attribute_name = Column(String(50))  # 슈팅, 패스, 드리블 등
    rating = Column(Float)  # -5.0 ~ +5.0

    updated_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    player = relationship("Player", back_populates="ratings")

class Prediction(Base):
    """예측 결과 저장"""
    __tablename__ = 'predictions'

    id = Column(Integer, primary_key=True)
    match_id = Column(Integer, ForeignKey('matches.id'))

    # 예측 확률
    home_win_prob = Column(Float)
    draw_prob = Column(Float)
    away_win_prob = Column(Float)

    # 예상 득점
    expected_home_goals = Column(Float)
    expected_away_goals = Column(Float)

    # 모델 타입
    model_type = Column(String(50))  # dixon-coles, xgboost, hybrid

    # 가중치 (하이브리드용)
    stats_weight = Column(Float)
    personal_weight = Column(Float)

    created_at = Column(DateTime, default=datetime.utcnow)

class Standings(Base):
    """리그 순위표"""
    __tablename__ = 'standings'

    id = Column(Integer, primary_key=True)
    team_id = Column(Integer, ForeignKey('teams.id'), nullable=False)
    season = Column(String(20), nullable=False)  # 2024-2025

    # 순위 정보
    rank = Column(Integer, nullable=False)
    matches_played = Column(Integer, default=0)
    wins = Column(Integer, default=0)
    draws = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    goals_for = Column(Integer, default=0)
    goals_against = Column(Integer, default=0)
    goal_difference = Column(Integer, default=0)
    points = Column(Integer, default=0)

    # 메타 정보
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    team = relationship("Team", back_populates="standings")

def init_db(db_path='sqlite:///soccer_predictor.db'):
    """데이터베이스 초기화"""
    engine = create_engine(db_path, echo=True)
    Base.metadata.create_all(engine)
    return engine

def get_session(engine):
    """세션 생성"""
    Session = sessionmaker(bind=engine)
    return Session()
