#!/bin/bash

# ChainMonitor Quick Start Script
# 一键启动所有服务进行测试

set -e

echo "╔════════════════════════════════════════╗"
echo "║   ChainMonitor Quick Start Script     ║"
echo "╚════════════════════════════════════════╝"

# 颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo ""
echo -e "${YELLOW}This script will:${NC}"
echo "  1. Start PostgreSQL with Docker"
echo "  2. Initialize database and generate test data"
echo "  3. Start frontend development server"
echo ""
read -p "Continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 0
fi

# Step 1: 启动数据库
echo ""
echo -e "${BLUE}[1/3] Starting PostgreSQL...${NC}"
docker-compose up -d postgres
echo -e "${GREEN}✓ PostgreSQL started${NC}"

# Step 2: 设置数据库
echo ""
echo -e "${BLUE}[2/3] Setting up database...${NC}"
cd database

# 等待PostgreSQL就绪
echo "Waiting for PostgreSQL to be ready..."
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if docker exec chainmonitor-db pg_isready -U chainmonitor_user -d chainmonitor &> /dev/null; then
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    sleep 1
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo -e "${RED}✗ PostgreSQL failed to start${NC}"
    exit 1
fi

# 运行迁移
echo "Running migrations..."
docker exec -i chainmonitor-db psql -U chainmonitor_user -d chainmonitor < migrations/001_init_schema.sql > /dev/null 2>&1

# 安装Python依赖
if [ ! -d "venv" ]; then
    echo "Installing Python dependencies..."
    pip3 install -r requirements.txt > /dev/null 2>&1
fi

# 生成测试数据
echo "Generating test data..."
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=chainmonitor
export DB_USER=chainmonitor_user
export DB_PASSWORD=chainmonitor_pass

python3 seeds/generate_test_data.py <<EOF
y
EOF

echo -e "${GREEN}✓ Database setup complete${NC}"

cd ..

# Step 3: 启动前端
echo ""
echo -e "${BLUE}[3/3] Starting frontend...${NC}"
cd frontend

if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

echo ""
echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   All services are ready!              ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}Services:${NC}"
echo "  🗄️  PostgreSQL: localhost:5432"
echo "  🌐 pgAdmin: http://localhost:5050 (if started)"
echo "  🚀 Frontend: http://localhost:3000 (starting...)"
echo ""
echo -e "${YELLOW}Starting frontend server...${NC}"
echo ""

npm run dev
