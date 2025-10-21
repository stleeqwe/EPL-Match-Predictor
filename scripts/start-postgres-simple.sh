#!/bin/bash

# 간단한 PostgreSQL 시작 스크립트

set -e

cd "$(dirname "$0")/.."

echo "Starting PostgreSQL..."

# Docker Desktop 실행 확인
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker Desktop is not running"
    echo "Please start Docker Desktop and try again"
    exit 1
fi

# PostgreSQL 시작 (여러 방법 시도)
if command -v docker-compose &> /dev/null; then
    # docker-compose 사용 가능
    docker-compose -f docker-compose.dev.yml up -d postgres
elif docker compose version &> /dev/null; then
    # docker compose 사용 가능
    docker compose -f docker-compose.dev.yml up -d postgres
else
    echo "❌ Neither 'docker compose' nor 'docker-compose' is available"
    exit 1
fi

echo "✅ PostgreSQL started"
echo ""
echo "Connection: postgresql://epl_user:epl_dev_password_123@localhost:5432/epl_predictor"
