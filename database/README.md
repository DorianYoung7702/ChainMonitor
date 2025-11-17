# ChainMonitor Database Module

PostgreSQL数据库模块，用于存储DeFi市场风险监控数据。

## 📊 数据库设计

### 核心表结构

1. **markets** - 监控的市场/池子列表
2. **risk_levels** - 风险等级历史（时序数据）
3. **risk_factors** - 详细的风险因子数据
4. **dex_transactions** - DEX交易记录（按月分区）
5. **whale_transactions** - 巨鲸交易记录
6. **cex_flows** - CEX资金流动
7. **liquidity_snapshots** - 流动性快照
8. **alerts** - 告警事件
9. **user_configs** - 用户配置
10. **monitoring_stats** - 监控统计

### 视图

- **v_latest_risk** - 每个市场的最新风险等级
- **v_market_overview** - 市场概览（含风险信息）

## 🚀 快速开始

### 1. 安装PostgreSQL

```bash
# Ubuntu/Debian
sudo apt-get install postgresql postgresql-contrib

# macOS
brew install postgresql@14
```

### 2. 创建数据库

```bash
# 登录PostgreSQL
sudo -u postgres psql

# 创建数据库和用户
CREATE DATABASE chainmonitor;
CREATE USER chainmonitor_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE chainmonitor TO chainmonitor_user;
\q
```

### 3. 运行迁移脚本

```bash
# 执行schema创建
psql -U chainmonitor_user -d chainmonitor -f migrations/001_init_schema.sql
```

### 4. 生成测试数据

```bash
cd seeds

# 安装依赖
pip install psycopg2-binary

# 配置环境变量
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=chainmonitor
export DB_USER=chainmonitor_user
export DB_PASSWORD=your_password

# 生成测试数据
python generate_test_data.py
```

## 🔧 配置

### 环境变量

创建 `.env` 文件：

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=chainmonitor
DB_USER=chainmonitor_user
DB_PASSWORD=your_secure_password
```

### 后端集成

更新 `backend/config.py`：

```python
import psycopg2

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'chainmonitor'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', '')
}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)
```

## 📈 数据量估算

基于测试数据生成器的默认配置：

| 表名 | 记录数 | 增长率 |
|------|--------|--------|
| markets | 1 | 低 |
| risk_levels | ~28/周 | 中 |
| risk_factors | ~100/周 | 中 |
| dex_transactions | ~500/周 | 高 |
| whale_transactions | ~50/周 | 低-中 |
| alerts | ~20/周 | 低 |

## 🎯 性能优化

### 索引策略

- **时序查询**: `(market_id, timestamp DESC)` 复合索引
- **点查询**: 主键和唯一键
- **范围查询**: B-tree索引
- **部分索引**: 用于活跃数据（如未解决的alerts）

### 分区策略

- **dex_transactions**: 按月分区（Range Partitioning）
- 自动创建新分区脚本（可选）

### 查询优化

```sql
-- 获取最新风险等级（使用视图）
SELECT * FROM v_latest_risk WHERE market_id = 'UNISWAP_USDC_WETH';

-- 获取24小时内的交易（利用分区）
SELECT * FROM dex_transactions
WHERE market_id = 'UNISWAP_USDC_WETH'
  AND timestamp > EXTRACT(EPOCH FROM NOW()) - 86400
ORDER BY timestamp DESC
LIMIT 100;

-- 获取风险因子趋势（窗口函数）
SELECT
    created_at,
    dex_score,
    whale_score,
    cex_score,
    AVG(dex_score) OVER (ORDER BY created_at ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as dex_ma7
FROM risk_factors
WHERE market_id = 'UNISWAP_USDC_WETH'
ORDER BY created_at DESC
LIMIT 50;
```

## 🔍 监控和维护

### 定期维护任务

```sql
-- 更新统计信息
ANALYZE risk_levels;
ANALYZE dex_transactions;

-- 清理旧数据（可选）
DELETE FROM dex_transactions WHERE timestamp < EXTRACT(EPOCH FROM NOW() - INTERVAL '90 days');

-- 检查表大小
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### 备份

```bash
# 完整备份
pg_dump -U chainmonitor_user chainmonitor > backup_$(date +%Y%m%d).sql

# 恢复
psql -U chainmonitor_user chainmonitor < backup_20250117.sql
```

## 📝 API集成示例

### Python示例

```python
import psycopg2
from psycopg2.extras import RealDictCursor

def get_latest_risk(market_id):
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    query = """
    SELECT risk_level, risk_score, created_at
    FROM v_latest_risk
    WHERE market_id = %s
    """

    cursor.execute(query, (market_id,))
    result = cursor.fetchone()

    cursor.close()
    conn.close()

    return result

# 使用
risk_data = get_latest_risk('UNISWAP_USDC_WETH')
print(f"当前风险等级: {risk_data['risk_level']}")
print(f"风险评分: {risk_data['risk_score']}")
```

## 🛠️ 故障排除

### 常见问题

**1. 连接被拒绝**
```bash
# 检查PostgreSQL是否运行
sudo systemctl status postgresql

# 启动服务
sudo systemctl start postgresql
```

**2. 权限错误**
```sql
-- 授予权限
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO chainmonitor_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO chainmonitor_user;
```

**3. 分区表插入失败**
- 检查timestamp是否在现有分区范围内
- 需要时手动创建新分区

## 📚 参考资源

- [PostgreSQL官方文档](https://www.postgresql.org/docs/)
- [Time-series数据最佳实践](https://www.timescale.com/blog/time-series-data-postgresql/)
- [索引优化指南](https://www.postgresql.org/docs/current/indexes.html)

## 📄 License

MIT License - 与主项目相同
