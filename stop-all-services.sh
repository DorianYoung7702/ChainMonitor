#!/bin/bash

# ChainMonitor 停止所有服务脚本

echo "🛑 停止 ChainMonitor 所有服务..."
echo "================================"

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 1. 停止API服务器
if [ -f "logs/api_server.pid" ]; then
    API_PID=$(cat logs/api_server.pid)
    if kill -0 $API_PID 2>/dev/null; then
        kill $API_PID
        echo -e "${GREEN}✅ API服务器已停止 (PID: $API_PID)${NC}"
    fi
    rm logs/api_server.pid
else
    pkill -f "python3.*api_server.py" 2>/dev/null && echo -e "${GREEN}✅ API服务器已停止${NC}"
fi

# 2. 停止监控服务
if [ -f "logs/monitor.pid" ]; then
    MONITOR_PID=$(cat logs/monitor.pid)
    if kill -0 $MONITOR_PID 2>/dev/null; then
        kill $MONITOR_PID
        echo -e "${GREEN}✅ 监控服务已停止 (PID: $MONITOR_PID)${NC}"
    fi
    rm logs/monitor.pid
else
    pkill -f "python3.*monitor.py" 2>/dev/null && echo -e "${GREEN}✅ 监控服务已停止${NC}"
fi

# 3. 停止前端（如果在后台运行）
pkill -f "vite" 2>/dev/null && echo -e "${GREEN}✅ 前端服务已停止${NC}"

# 4. 停止Docker容器（可选）
read -p "是否停止Docker数据库容器？(y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    docker-compose down
    echo -e "${GREEN}✅ Docker容器已停止${NC}"
else
    echo "保持Docker容器运行"
fi

echo ""
echo "================================"
echo "✅ 所有服务已停止"
echo "================================"
