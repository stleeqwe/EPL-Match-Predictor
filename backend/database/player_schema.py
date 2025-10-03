"""
선수 분석 플랫폼을 위한 데이터베이스 스키마
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

Base = declarative_base()


class Team(Base):
    """EPL 팀 정보"""
    __tablename__ = 'teams'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)  # Arsenal, Liverpool 등
    short_name = Column(String)  # ARS, LIV 등
    stadium = Column(String)
    manager = Column(String)
    founded = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    players = relationship("Player", back_populates="team", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Team(name='{self.name}')>"


class Player(Base):
    """선수 정보"""
    __tablename__ = 'players'

    id = Column(Integer, primary_key=True)
    team_id = Column(Integer, ForeignKey('teams.id'), nullable=False)
    name = Column(String, nullable=False)
    position = Column(String, nullable=False)  # GK, DF, MF, FW
    detailed_position = Column(String)  # CB, CM, ST 등
    number = Column(Integer)  # 등번호
    age = Column(Integer)
    nationality = Column(String)  # 국적 코드 (gb, br, es 등)
    height = Column(String)  # 키 (cm)
    foot = Column(String)  # 주발 (left/right/both)
    market_value = Column(String)  # 시장 가치
    contract_until = Column(String)  # 계약 만료일
    appearances = Column(Integer, default=0)  # 출전 경기 수
    goals = Column(Integer, default=0)  # 득점
    assists = Column(Integer, default=0)  # 어시스트
    photo_url = Column(String)  # 프로필 사진 URL
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    team = relationship("Team", back_populates="players")
    ratings = relationship("PlayerRating", back_populates="player", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Player(name='{self.name}', team='{self.team.name if self.team else None}', position='{self.position}')>"


class PlayerRating(Base):
    """선수 능력치 평가"""
    __tablename__ = 'player_ratings'

    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey('players.id'), nullable=False)
    user_id = Column(String, default='default', nullable=False)  # 여러 사용자 지원
    attribute_name = Column(String, nullable=False)  # reflexes, tackling, passing 등
    rating = Column(Float, nullable=False)  # 0.0 ~ 5.0
    notes = Column(String)  # 메모
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    player = relationship("Player", back_populates="ratings")

    # 제약조건: 한 선수의 같은 능력치는 사용자당 하나만
    __table_args__ = (
        UniqueConstraint('player_id', 'user_id', 'attribute_name', name='uix_player_user_attribute'),
    )

    def __repr__(self):
        return f"<PlayerRating(player_id={self.player_id}, attribute='{self.attribute_name}', rating={self.rating})>"


class PositionAttribute(Base):
    """포지션별 능력치 템플릿"""
    __tablename__ = 'position_attributes'

    id = Column(Integer, primary_key=True)
    position = Column(String, nullable=False)  # GK, DF, MF, FW
    attribute_name = Column(String, nullable=False)  # reflexes, tackling 등
    attribute_name_ko = Column(String)  # 한글 표시명
    attribute_name_en = Column(String)  # 영문 표시명
    display_order = Column(Integer, default=0)  # 표시 순서
    created_at = Column(DateTime, default=datetime.utcnow)

    # 제약조건: 포지션과 능력치 조합은 유일
    __table_args__ = (
        UniqueConstraint('position', 'attribute_name', name='uix_position_attribute'),
    )

    def __repr__(self):
        return f"<PositionAttribute(position='{self.position}', attribute='{self.attribute_name}')>"


# 데이터베이스 초기화 함수
def init_player_db(db_path='player_analysis.db'):
    """데이터베이스 초기화"""
    engine = create_engine(f'sqlite:///{db_path}', echo=False)
    Base.metadata.create_all(engine)
    return engine


def get_player_session(db_path='player_analysis.db'):
    """세션 생성"""
    engine = create_engine(f'sqlite:///{db_path}', echo=False)
    Session = sessionmaker(bind=engine)
    return Session()


def init_position_attributes(session):
    """포지션별 능력치 템플릿 초기화"""

    # 기존 데이터 삭제
    session.query(PositionAttribute).delete()

    attributes = [
        # 골키퍼
        ('GK', 'reflexes', '반응속도', 'Reflexes', 1),
        ('GK', 'positioning', '포지셔닝', 'Positioning', 2),
        ('GK', 'handling', '핸들링', 'Handling', 3),
        ('GK', 'kicking', '발재간', 'Kicking', 4),
        ('GK', 'aerial', '공중볼 처리', 'Aerial', 5),
        ('GK', 'one_on_one', '1:1 대응', 'One-on-One', 6),

        # 수비수
        ('DF', 'tackling', '태클', 'Tackling', 1),
        ('DF', 'marking', '마크', 'Marking', 2),
        ('DF', 'positioning', '포지셔닝', 'Positioning', 3),
        ('DF', 'heading', '헤더', 'Heading', 4),
        ('DF', 'physicality', '피지컬', 'Physicality', 5),
        ('DF', 'speed', '스피드', 'Speed', 6),
        ('DF', 'passing', '패스', 'Passing', 7),

        # 미드필더
        ('MF', 'passing', '패스', 'Passing', 1),
        ('MF', 'vision', '비전', 'Vision', 2),
        ('MF', 'dribbling', '드리블', 'Dribbling', 3),
        ('MF', 'shooting', '슈팅', 'Shooting', 4),
        ('MF', 'tackling', '태클', 'Tackling', 5),
        ('MF', 'stamina', '체력', 'Stamina', 6),
        ('MF', 'creativity', '창조력', 'Creativity', 7),

        # 공격수
        ('FW', 'finishing', '슈팅', 'Finishing', 1),
        ('FW', 'positioning', '위치선정', 'Positioning', 2),
        ('FW', 'dribbling', '드리블', 'Dribbling', 3),
        ('FW', 'pace', '스피드', 'Pace', 4),
        ('FW', 'physicality', '피지컬', 'Physicality', 5),
        ('FW', 'heading', '헤더', 'Heading', 6),
        ('FW', 'first_touch', '퍼스트터치', 'First Touch', 7),
    ]

    for pos, attr, ko, en, order in attributes:
        position_attr = PositionAttribute(
            position=pos,
            attribute_name=attr,
            attribute_name_ko=ko,
            attribute_name_en=en,
            display_order=order
        )
        session.add(position_attr)

    session.commit()


if __name__ == '__main__':
    # 테스트 - 데이터베이스 생성
    print("Creating database...")
    engine = init_player_db('test_player_analysis.db')
    session = get_player_session('test_player_analysis.db')

    print("Initializing position attributes...")
    init_position_attributes(session)

    print("Testing queries...")
    # 포지션 능력치 조회
    gk_attrs = session.query(PositionAttribute).filter_by(position='GK').all()
    print(f"GK attributes: {len(gk_attrs)}")
    for attr in gk_attrs:
        print(f"  - {attr.attribute_name_ko} ({attr.attribute_name})")

    session.close()
    print("✅ Database schema created successfully!")
