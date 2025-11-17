#!/bin/bash

# ChainMonitor Database Setup Script
# 用于快速设置数据库和生成测试数据

set -e  # 遇到错误立即退出

echo "======================================"
echo " ChainMonitor Database Setup"
echo "======================================"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 配置变量
DB_NAME=${DB_NAME:-chainmonitor}
DB_USER=${DB_USER:-chainmonitor_user}
DB_PASSWORD=${DB_PASSWORD:-changeme}
DB_HOST=${DB_HOST:-localhost}
DB_PORT=${DB_PORT:-5432}

echo -e "\n${YELLOW}Configuration:${NC}"
echo "  Database: $DB_NAME"
echo "  User: $DB_USER"
echo "  Host: $DB_HOST"
echo "  Port: $DB_PORT"

# 步骤1: 检查PostgreSQL是否安装
echo -e "\n${YELLOW}Step 1: Checking PostgreSQL installation...${NC}"
if ! command -v psql &> /dev/null; then
    echo -e "${RED}PostgreSQL is not installed. Please install it first.${NC}"
    echo "  Ubuntu/Debian: sudo apt-get install postgresql postgresql-contrib"
    echo "  macOS: brew install postgresql@14"
    exit 1
fi
echo -e "${GREEN}✓ PostgreSQL found${NC}"

# 步骤2: 检查PostgreSQL服务状态
echo -e "\n${YELLOW}Step 2: Checking PostgreSQL service...${NC}"
if ! pg_isready -q; then
    echo -e "${YELLOW}PostgreSQL service is not running. Attempting to start...${NC}"
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo systemctl start postgresql
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        brew services start postgresql@14
    fi
fi
echo -e "${GREEN}✓ PostgreSQL is running${NC}"

# 步骤3: 创建数据库和用户
echo -e "\n${YELLOW}Step 3: Creating database and user...${NC}"
sudo -u postgres psql -v ON_ERROR_STOP=1 <<-EOSQL
    -- 创建用户（如果不存在）
    DO \$\$
    BEGIN
        IF NOT EXISTS (SELECT FROM pg_user WHERE usename = '$DB_USER') THEN
            CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
        END IF;
    END
    \$\$;

    -- 创建数据库（如果不存在）
    SELECT 'CREATE DATABASE $DB_NAME OWNER $DB_USER'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$DB_NAME')\gexec

    -- 授予权限
    GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
EOSQL

echo -e "${GREEN}✓ Database and user created${NC}"

# 步骤4: 运行迁移脚本
echo -e "\n${YELLOW}Step 4: Running database migrations...${NC}"
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f migrations/001_init_schema.sql

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Schema created successfully${NC}"
else
    echo -e "${RED}✗ Schema creation failed${NC}"
    exit 1
fi

# 步骤5: 安装Python依赖
echo -e "\n${YELLOW}Step 5: Installing Python dependencies...${NC}"
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
# ChainMonitor Database Configuration
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

echo -e "\n${YELLOW}Next steps:${NC}"
echo "  1. Source the .env file: source .env"
echo "  2. Test the connection: python3 utils/db_helper.py"
echo "  3. Integrate with backend/config.py"
echo ""
echo -e "${YELLOW}Connection string:${NC}"
echo "  postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME"
