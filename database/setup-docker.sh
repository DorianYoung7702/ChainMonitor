#!/bin/bash

# ChainMonitor Database Setup Script for Docker
# 用于在Docker环境中设置数据库和生成测试数据

set -e  # 遇到错误立即退出

echo "======================================"
echo " ChainMonitor Database Setup (Docker)"
echo "======================================"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Docker配置
DB_NAME=chainmonitor
DB_USER=chainmonitor_user
DB_PASSWORD=chainmonitor_pass
DB_HOST=localhost
DB_PORT=5432

echo -e "\n${YELLOW}Configuration:${NC}"
echo "  Database: $DB_NAME"
echo "  User: $DB_USER"
echo "  Host: $DB_HOST (Docker)"
echo "  Port: $DB_PORT"

# 步骤1: 检查Docker是否安装
echo -e "\n${YELLOW}Step 1: Checking Docker installation...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker is not installed. Please install Docker first.${NC}"
    echo "  Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}Docker Compose is not installed. Please install Docker Compose first.${NC}"
    echo "  Visit: https://docs.docker.com/compose/install/"
    exit 1
fi
echo -e "${GREEN}✓ Docker found${NC}"

# 步骤2: 启动Docker容器
echo -e "\n${YELLOW}Step 2: Starting Docker containers...${NC}"
cd ..
if docker compose version &> /dev/null; then
    docker compose up -d postgres
else
    docker-compose up -d postgres
fi

echo -e "${GREEN}✓ Docker containers started${NC}"

# 步骤3: 等待PostgreSQL就绪
echo -e "\n${YELLOW}Step 3: Waiting for PostgreSQL to be ready...${NC}"
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if docker exec chainmonitor-db pg_isready -U $DB_USER -d $DB_NAME &> /dev/null; then
        echo -e "${GREEN}✓ PostgreSQL is ready${NC}"
        break
    fi

    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo -e "${BLUE}Waiting for PostgreSQL... ($RETRY_COUNT/$MAX_RETRIES)${NC}"
    sleep 2
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo -e "${RED}✗ PostgreSQL failed to start${NC}"
    exit 1
fi

# 步骤4: 运行迁移脚本
echo -e "\n${YELLOW}Step 4: Running database migrations...${NC}"
docker exec -i chainmonitor-db psql -U $DB_USER -d $DB_NAME < database/migrations/001_init_schema.sql

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Schema created successfully${NC}"
else
    echo -e "${RED}✗ Schema creation failed${NC}"
    exit 1
fi

# 步骤5: 安装Python依赖
echo -e "\n${YELLOW}Step 5: Installing Python dependencies...${NC}"
cd database
if command -v pip3 &> /dev/null; then
    pip3 install -r requirements.txt
elif command -v pip &> /dev/null; then
    pip install -r requirements.txt
else
    echo -e "${RED}pip is not installed. Please install Python and pip first.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python dependencies installed${NC}"

# 步骤6: 生成测试数据
echo -e "\n${YELLOW}Step 6: Generating test data...${NC}"
read -p "Generate test data? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    export DB_HOST=$DB_HOST
    export DB_PORT=$DB_PORT
    export DB_NAME=$DB_NAME
    export DB_USER=$DB_USER
    export DB_PASSWORD=$DB_PASSWORD

    python3 seeds/generate_test_data.py
    echo -e "${GREEN}✓ Test data generated${NC}"
else
    echo -e "${YELLOW}Skipping test data generation${NC}"
fi

# 步骤7: 创建.env文件
echo -e "\n${YELLOW}Step 7: Creating .env file...${NC}"
cat > .env <<EOF
# ChainMonitor Database Configuration (Docker)
DB_HOST=$DB_HOST
DB_PORT=$DB_PORT
DB_NAME=$DB_NAME
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD
EOF
echo -e "${GREEN}✓ .env file created${NC}"

# 完成
echo -e "\n${GREEN}======================================"
echo "  Setup completed successfully!"
echo "======================================${NC}"

echo -e "\n${YELLOW}Docker containers:${NC}"
echo "  PostgreSQL: localhost:5432"
echo "  pgAdmin: http://localhost:5050"
echo "    Email: admin@chainmonitor.com"
echo "    Password: admin"

echo -e "\n${YELLOW}Next steps:${NC}"
echo "  1. Source the .env file: source .env"
echo "  2. Test the connection: python3 utils/db_helper.py"
echo "  3. Integrate with backend/config.py"
echo ""
echo -e "${YELLOW}Docker commands:${NC}"
echo "  Stop containers: docker-compose stop"
echo "  Start containers: docker-compose start"
echo "  View logs: docker-compose logs -f postgres"
echo "  Restart: docker-compose restart postgres"
echo ""
echo -e "${YELLOW}Connection string:${NC}"
echo "  postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME"
