#!/bin/bash

# ChainMonitor 全栈启动脚本
# 启动所有服务：数据库、API服务器、后端监控、前端

set -e

echo "🚀 ChainMonitor 全栈启动脚本"
echo "================================"

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 检查是否在项目根目录
if [ ! -f "package.json" ] || [ ! -d "backend" ]; then
    echo -e "${RED}❌ 错误：请在项目根目录运行此脚本${NC}"
    exit 1
fi

# 1. 检查Docker是否运行
echo ""
echo "Step 1: 检查Docker..."
if ! docker ps > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker未运行，请先启动Docker${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker已运行${NC}"

# 2. 启动PostgreSQL
echo ""
echo "Step 2: 启动PostgreSQL数据库..."
if docker ps | grep -q chainmonitor-db; then
    echo -e "${YELLOW}⚠️  数据库容器已在运行${NC}"
else
    docker-compose up -d
    echo "等待数据库启动..."
    sleep 5
    echo -e "${GREEN}✅ PostgreSQL已启动${NC}"
fi

# 3. 检查数据库是否已初始化
echo ""
echo "Step 3: 检查数据库schema..."
TABLE_COUNT=$(docker exec chainmonitor-db psql -U chainmonitor_user -d chainmonitor -tAc "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';" 2>/dev/null || echo "0")

if [ "$TABLE_COUNT" -lt "10" ]; then
    echo "初始化数据库schema..."
    docker exec -i chainmonitor-db psql -U chainmonitor_user -d chainmonitor < database/migrations/001_init_schema.sql

    echo "生成测试数据..."
    cd database
    python3 seeds/generate_test_data.py
    cd ..
    echo -e "${GREEN}✅ 数据库已初始化${NC}"
else
    echo -e "${YELLOW}⚠️  数据库已存在 ($TABLE_COUNT 张表)${NC}"
fi

# 4. 启动API服务器（后台）
echo ""
echo "Step 4: 启动API服务器..."
cd backend

# 检查Python依赖
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo "安装Python依赖..."
    pip install -r requirements.txt
fi

# 杀死已存在的API服务器进程
pkill -f "python3.*api_server.py" 2>/dev/null || true

# 启动API服务器
nohup python3 api_server.py > ../logs/api_server.log 2>&1 &
API_PID=$!
echo $API_PID > ../logs/api_server.pid
echo -e "${GREEN}✅ API服务器已启动 (PID: $API_PID)${NC}"
echo "   日志文件: logs/api_server.log"
echo "   API文档: http://localhost:8000/docs"

cd ..

# 等待API服务器启动
echo "等待API服务器启动..."
sleep 3

# 测试API
if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ API服务器健康检查通过${NC}"
else
    echo -e "${YELLOW}⚠️  API服务器可能还在启动中...${NC}"
fi

# 5. 询问是否启动后端监控服务
echo ""
echo "Step 5: 后端监控服务"
echo -e "${YELLOW}注意：后端监控服务需要连接以太坊主网，可能产生RPC调用费用${NC}"
read -p "是否启动后端监控服务？(y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    cd backend

    # 检查环境变量
    if [ -z "$ETH_RPC_URL" ] || [ -z "$CONTRACT_ADDRESS" ]; then
        echo -e "${RED}❌ 错误：请先在.env中配置 ETH_RPC_URL 和 CONTRACT_ADDRESS${NC}"
        echo "   1. 部署智能合约: npm run deploy:sepolia"
        echo "   2. 更新.env文件中的CONTRACT_ADDRESS"
        cd ..
    else
        # 杀死已存在的监控进程
        pkill -f "python3.*monitor.py" 2>/dev/null || true

        # 启动监控服务
        nohup python3 monitor.py > ../logs/monitor.log 2>&1 &
        MONITOR_PID=$!
        echo $MONITOR_PID > ../logs/monitor.pid
        echo -e "${GREEN}✅ 监控服务已启动 (PID: $MONITOR_PID)${NC}"
        echo "   日志文件: logs/monitor.log"
        cd ..
    fi
else
    echo -e "${YELLOW}⏭️  跳过后端监控服务${NC}"
fi

# 6. 启动前端
echo ""
echo "Step 6: 启动前端开发服务器..."
cd frontend

# 检查node_modules
if [ ! -d "node_modules" ]; then
    echo "安装前端依赖..."
    npm install
fi

echo -e "${GREEN}✅ 准备启动前端...${NC}"
echo ""
echo "================================"
echo "🎉 所有服务已启动！"
echo "================================"
echo ""
echo "📊 访问以下地址："
echo "   前端: http://localhost:5173"
echo "   API: http://localhost:8000/docs"
echo "   pgAdmin: http://localhost:5050 (如果启用)"
echo ""
echo "📝 日志文件："
echo "   API服务器: logs/api_server.log"
echo "   监控服务: logs/monitor.log"
echo ""
echo "🛑 停止所有服务："
echo "   ./stop-all-services.sh"
echo ""
echo "================================"
echo ""

# 启动前端（前台运行）
npm run dev
