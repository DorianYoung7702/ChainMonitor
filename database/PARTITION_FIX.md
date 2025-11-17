# 分区表错误修复指南

## 问题

如果您遇到以下错误：

```
❌ Error: no partition of relation "dex_transactions" found for row
DETAIL:  Partition key of the failing row contains ("timestamp") = (1762882084).
```

这是因为早期版本的 `001_init_schema.sql` 使用了**错误的Unix时间戳**：

- **错误**: 使用了2024年的Unix时间戳，但标记为2025年
  - 例如：1704067200 实际上是 2024-01-01，而不是 2025-01-01
- **正确**: 2025-01-01 的Unix时间戳应该是 1735689600

这导致当前时间（2025年11月，约1763000000）落在所有分区范围之外。

## 快速修复（1分钟）

### 方法1: 自动修复脚本（推荐）

```bash
cd database
chmod +x fix-partitions.sh
./fix-partitions.sh
```

此脚本会：
1. 删除所有使用错误时间戳的旧分区
2. 使用正确的2025年Unix时间戳重建分区

### 方法2: 手动修复

**如果您使用Docker：**

```bash
docker exec -i chainmonitor-db psql -U chainmonitor_user -d chainmonitor < database/migrations/002_add_partitions.sql
```

**如果您使用本地PostgreSQL：**

```bash
psql -U chainmonitor_user -d chainmonitor -f database/migrations/002_add_partitions.sql
```

**注意**: `002_add_partitions.sql` 会删除并重建所有2025年分区，如果已有数据请先备份！

## 验证修复

添加分区后，重新运行测试数据生成器：

```bash
cd database
python3 seeds/generate_test_data.py
```

现在应该能成功生成所有数据了！

## 查看已创建的分区

```bash
# 使用Docker
docker exec -it chainmonitor-db psql -U chainmonitor_user -d chainmonitor -c "\d+ dex_transactions"

# 或使用本地PostgreSQL
psql -U chainmonitor_user -d chainmonitor -c "\d+ dex_transactions"
```

应该看到 `dex_transactions_2025_01` 到 `dex_transactions_2025_12` 共12个分区。

## 如果重新开始

如果您想完全重新开始（清空并重建数据库）：

### 使用Docker

```bash
# 停止并删除容器和数据
docker-compose down -v

# 重新启动
docker-compose up -d postgres

# 等待几秒，然后运行迁移（新的schema包含全年分区）
docker exec -i chainmonitor-db psql -U chainmonitor_user -d chainmonitor < database/migrations/001_init_schema.sql

# 生成测试数据
cd database
python3 seeds/generate_test_data.py
```

### 使用本地PostgreSQL

```bash
# 删除并重建数据库
psql -U postgres -c "DROP DATABASE chainmonitor;"
psql -U postgres -c "CREATE DATABASE chainmonitor;"

# 运行新的迁移（包含全年分区）
psql -U chainmonitor_user -d chainmonitor -f database/migrations/001_init_schema.sql

# 生成测试数据
cd database
python3 seeds/generate_test_data.py
```

## 技术说明

PostgreSQL的分区表需要预先创建分区范围。早期版本的schema使用了**错误的Unix时间戳**：

### 错误的时间戳（旧版本）

```sql
-- 错误！使用了2024年的Unix时间戳
CREATE TABLE dex_transactions_2025_01 PARTITION OF dex_transactions
    FOR VALUES FROM (1704067200) TO (1706745600); -- 标记为2025-01，实际是2024-01
```

验证：
- 1704067200 = 2024-01-01 00:00:00 UTC ❌
- 1735689600 = 2025-01-01 00:00:00 UTC ✅

### 正确的时间戳（新版本）

```sql
-- 正确！使用2025年的Unix时间戳
CREATE TABLE dex_transactions_2025_01 PARTITION OF dex_transactions
    FOR VALUES FROM (1735689600) TO (1738368000); -- 2025-01-01 to 2025-02-01
```

### 为什么会出错？

当前时间是2025年11月（Unix时间戳约 1763000000），但所有分区的范围都是2024年的时间戳（1704067200 - 1735689600）。

因此当测试数据生成器尝试插入当前时间戳的记录时，PostgreSQL找不到对应的分区，报错：
```
no partition of relation "dex_transactions" found for row
```

## 未来扩展

如果需要2026年的分区，可以创建新的迁移脚本：

```sql
-- migrations/003_add_2026_partitions.sql
CREATE TABLE dex_transactions_2026_01 PARTITION OF dex_transactions
    FOR VALUES FROM (1735689600) TO (1738368000); -- 2026-01-01 to 2026-02-01
-- ... 更多月份
```
