#!/usr/bin/env python3
"""
SQLite → PostgreSQL 마이그레이션 스크립트
EPL Match Predictor v2.0

사용법:
    python scripts/migrate_sqlite_to_postgres.py
"""

import sqlite3
import psycopg2
from psycopg2.extras import execute_values
import sys
import os
from datetime import datetime

# 색상 출력
GREEN = '\033[0;32m'
BLUE = '\033[0;34m'
YELLOW = '\033[1;33m'
RED = '\033[0;31m'
NC = '\033[0m'

def log_info(msg):
    print(f"{BLUE}ℹ️  {msg}{NC}")

def log_success(msg):
    print(f"{GREEN}✅ {msg}{NC}")

def log_warning(msg):
    print(f"{YELLOW}⚠️  {msg}{NC}")

def log_error(msg):
    print(f"{RED}❌ {msg}{NC}")


# 데이터베이스 설정
SQLITE_DB_PATH = 'backend/data/epl_data.db'

# PostgreSQL 설정 (로컬 개발용)
PG_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'epl_predictor',
    'user': 'epl_user',
    'password': 'epl_dev_password_123'
}


def check_sqlite_exists():
    """SQLite DB 파일 확인"""
    if not os.path.exists(SQLITE_DB_PATH):
        log_error(f"SQLite database not found: {SQLITE_DB_PATH}")
        return False

    file_size = os.path.getsize(SQLITE_DB_PATH)
    log_info(f"Found SQLite DB: {SQLITE_DB_PATH} ({file_size} bytes)")
    return True


def connect_sqlite():
    """SQLite 연결"""
    try:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        conn.row_factory = sqlite3.Row
        log_success("Connected to SQLite")
        return conn
    except Exception as e:
        log_error(f"Failed to connect to SQLite: {e}")
        sys.exit(1)


def connect_postgres():
    """PostgreSQL 연결"""
    try:
        conn = psycopg2.connect(**PG_CONFIG)
        log_success("Connected to PostgreSQL")
        return conn
    except Exception as e:
        log_error(f"Failed to connect to PostgreSQL: {e}")
        log_warning("Make sure PostgreSQL is running (docker-compose -f docker-compose.dev.yml up -d)")
        sys.exit(1)


def create_postgres_schema(pg_conn):
    """PostgreSQL 스키마 생성"""
    log_info("Creating PostgreSQL schema...")

    cursor = pg_conn.cursor()

    # 기존 테이블 삭제 (개발용)
    cursor.execute("DROP TABLE IF EXISTS player_ratings CASCADE;")
    cursor.execute("DROP TABLE IF EXISTS position_attributes CASCADE;")
    cursor.execute("DROP TABLE IF EXISTS players CASCADE;")
    cursor.execute("DROP TABLE IF EXISTS teams CASCADE;")

    # Teams 테이블
    cursor.execute("""
        CREATE TABLE teams (
            id BIGSERIAL PRIMARY KEY,
            name VARCHAR(255) UNIQUE NOT NULL,
            short_name VARCHAR(50),
            stadium VARCHAR(255),
            manager VARCHAR(255),
            founded INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Players 테이블
    cursor.execute("""
        CREATE TABLE players (
            id BIGSERIAL PRIMARY KEY,
            team_id BIGINT NOT NULL REFERENCES teams(id),
            name VARCHAR(255) NOT NULL,
            position VARCHAR(50) NOT NULL,
            detailed_position VARCHAR(50),
            number INTEGER,
            age INTEGER,
            nationality VARCHAR(50),
            height VARCHAR(50),
            foot VARCHAR(50),
            market_value VARCHAR(100),
            contract_until VARCHAR(50),
            appearances INTEGER DEFAULT 0,
            goals INTEGER DEFAULT 0,
            assists INTEGER DEFAULT 0,
            photo_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # PlayerRatings 테이블 (가장 중요! 사용자 평가 데이터)
    cursor.execute("""
        CREATE TABLE player_ratings (
            id BIGSERIAL PRIMARY KEY,
            player_id BIGINT NOT NULL REFERENCES players(id),
            user_id VARCHAR(255) DEFAULT 'default' NOT NULL,
            attribute_name VARCHAR(100) NOT NULL,
            rating DECIMAL(3, 2) NOT NULL CHECK (rating >= 0 AND rating <= 5),
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (player_id, user_id, attribute_name)
        );
    """)

    # PositionAttributes 테이블
    cursor.execute("""
        CREATE TABLE position_attributes (
            id BIGSERIAL PRIMARY KEY,
            position VARCHAR(10) NOT NULL,
            attribute_name VARCHAR(100) NOT NULL,
            attribute_name_ko VARCHAR(100),
            attribute_name_en VARCHAR(100),
            display_order INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (position, attribute_name)
        );
    """)

    # 인덱스 생성 (성능 최적화)
    cursor.execute("CREATE INDEX idx_players_team_id ON players(team_id);")
    cursor.execute("CREATE INDEX idx_player_ratings_player_id ON player_ratings(player_id);")
    cursor.execute("CREATE INDEX idx_player_ratings_user_id ON player_ratings(user_id);")

    pg_conn.commit()
    log_success("PostgreSQL schema created")


def migrate_table(sqlite_conn, pg_conn, table_name, transform_fn=None):
    """테이블 데이터 마이그레이션"""
    log_info(f"Migrating table: {table_name}")

    # SQLite에서 데이터 읽기
    sqlite_cursor = sqlite_conn.cursor()

    # player_ratings는 유효한 player_id만 마이그레이션
    if table_name == 'player_ratings':
        sqlite_cursor.execute(f"""
            SELECT pr.* FROM {table_name} pr
            WHERE EXISTS (SELECT 1 FROM players p WHERE p.id = pr.player_id)
        """)
    else:
        sqlite_cursor.execute(f"SELECT * FROM {table_name}")

    rows = sqlite_cursor.fetchall()

    if not rows:
        log_warning(f"No data found in {table_name}")
        return 0

    # 컬럼 이름 가져오기
    column_names = [desc[0] for desc in sqlite_cursor.description]

    # PostgreSQL에 삽입
    pg_cursor = pg_conn.cursor()

    # 데이터 변환 (필요 시)
    data_to_insert = []
    for row in rows:
        row_dict = dict(zip(column_names, row))

        # players와 teams 테이블은 ID를 유지 (FK 관계 유지)
        # 다른 테이블은 ID 제거 (SERIAL 자동 생성)
        if table_name not in ['players', 'teams'] and 'id' in row_dict:
            del row_dict['id']

        # 커스텀 변환 함수 적용
        if transform_fn:
            row_dict = transform_fn(row_dict)

        data_to_insert.append(row_dict)

    # Bulk insert
    if data_to_insert:
        columns = data_to_insert[0].keys()
        values = [[row[col] for col in columns] for row in data_to_insert]

        insert_query = f"""
            INSERT INTO {table_name} ({', '.join(columns)})
            VALUES %s
        """

        execute_values(pg_cursor, insert_query, values)
        pg_conn.commit()

    log_success(f"Migrated {len(rows)} rows from {table_name}")
    return len(rows)


def verify_migration(sqlite_conn, pg_conn):
    """마이그레이션 검증"""
    log_info("Verifying migration...")

    tables = ['teams', 'players', 'player_ratings', 'position_attributes']

    for table in tables:
        # SQLite 카운트
        sqlite_cursor = sqlite_conn.cursor()
        sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table}")
        sqlite_count = sqlite_cursor.fetchone()[0]

        # PostgreSQL 카운트
        pg_cursor = pg_conn.cursor()
        pg_cursor.execute(f"SELECT COUNT(*) FROM {table}")
        pg_count = pg_cursor.fetchone()[0]

        if sqlite_count == pg_count:
            log_success(f"{table}: {pg_count} rows ✓")
        else:
            log_error(f"{table}: SQLite={sqlite_count}, PostgreSQL={pg_count} ✗")
            return False

    # 중요: 사용자 평가 데이터 샘플 확인
    pg_cursor = pg_conn.cursor()
    pg_cursor.execute("""
        SELECT pr.user_id, p.name, pr.attribute_name, pr.rating
        FROM player_ratings pr
        JOIN players p ON pr.player_id = p.id
        LIMIT 5
    """)
    sample_ratings = pg_cursor.fetchall()

    if sample_ratings:
        log_info("Sample user ratings:")
        for row in sample_ratings:
            print(f"  - {row[0]}: {row[1]} → {row[2]} = {row[3]}")

    return True


def main():
    """메인 실행"""
    print("""
╔══════════════════════════════════════════════════════════╗
║   SQLite → PostgreSQL Migration Tool                    ║
║   EPL Match Predictor v2.0                              ║
╚══════════════════════════════════════════════════════════╝
    """)

    # 1. SQLite DB 확인
    if not check_sqlite_exists():
        return

    # 2. 연결
    sqlite_conn = connect_sqlite()
    pg_conn = connect_postgres()

    try:
        # 3. PostgreSQL 스키마 생성
        create_postgres_schema(pg_conn)

        # 4. 테이블 마이그레이션
        total_rows = 0
        total_rows += migrate_table(sqlite_conn, pg_conn, 'teams')
        total_rows += migrate_table(sqlite_conn, pg_conn, 'players')
        total_rows += migrate_table(sqlite_conn, pg_conn, 'player_ratings')  # 핵심!
        total_rows += migrate_table(sqlite_conn, pg_conn, 'position_attributes')

        # 5. 검증
        if verify_migration(sqlite_conn, pg_conn):
            log_success(f"Migration completed! Total {total_rows} rows migrated")
            log_info("PostgreSQL connection string:")
            print(f"  postgresql://{PG_CONFIG['user']}:{PG_CONFIG['password']}@{PG_CONFIG['host']}:{PG_CONFIG['port']}/{PG_CONFIG['database']}")
        else:
            log_error("Migration verification failed!")
            sys.exit(1)

    except Exception as e:
        log_error(f"Migration failed: {e}")
        import traceback
        traceback.print_exc()
        pg_conn.rollback()
        sys.exit(1)

    finally:
        sqlite_conn.close()
        pg_conn.close()
        log_info("Database connections closed")


if __name__ == '__main__':
    main()
