#!/bin/bash

# 修复分区问题 - 添加缺失的2025年分区
# 当遇到 "no partition of relation dex_transactions found for row" 错误时运行此脚本

set -e

echo "======================================"
echo " 修复 dex_transactions 分区表"
echo "======================================"

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 使用Docker执行
if docker ps | grep -q chainmonitor-db; then
    echo -e "${YELLOW}检测到Docker容器，使用Docker执行...${NC}"
    docker exec -i chainmonitor-db psql -U chainmonitor_user -d chainmonitor < migrations/002_add_partitions.sql
    echo -e "${GREEN}✓ 分区添加成功！${NC}"
# 或使用本地PostgreSQL
elif command -v psql &> /dev/null; then
    echo -e "${YELLOW}使用本地PostgreSQL执行...${NC}"
    psql -U chainmonitor_user -d chainmonitor -f migrations/002_add_partitions.sql
    echo -e "${GREEN}✓ 分区添加成功！${NC}"
else
    echo "❌ 找不到PostgreSQL或Docker"
    exit 1
fi

echo ""
echo -e "${GREEN}修复完成！现在可以重新运行测试数据生成器。${NC}"
echo ""
echo "运行: python3 seeds/generate_test_data.py"
