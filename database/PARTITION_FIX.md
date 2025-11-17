# 分区表错误修复指南

## 问题

如果您遇到以下错误：

```
❌ Error: no partition of relation "dex_transactions" found for row
DETAIL:  Partition key of the failing row contains ("timestamp") = (1763007671).
```

这是因为 `dex_transactions` 表的分区只创建到2025年3月，而测试数据生成的时间戳是当前时间（可能在更后面的月份）。

## 快速修复（1分钟）

### 方法1: 自动修复脚本

```bash
cd database
chmod +x fix-partitions.sh
./fix-partitions.sh
```

### 方法2: 手动添加分区

如果您使用Docker：

```bash
docker exec -i chainmonitor-db psql -U chainmonitor_user -d chainmonitor < database/migrations/002_add_partitions.sql
```

如果您使用本地PostgreSQL：

```bash
psql -U chainmonitor_user -d chainmonitor -f database/migrations/002_add_partitions.sql
```

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

PostgreSQL的分区表需要预先创建分区范围。原始schema只创建了2025年1-3月的分区：

```sql
-- 旧版本
CREATE TABLE dex_transactions_2025_01 ... -- Jan
CREATE TABLE dex_transactions_2025_02 ... -- Feb
CREATE TABLE dex_transactions_2025_03 ... -- Mar
```

新版本扩展到全年：

```sql
-- 新版本
CREATE TABLE dex_transactions_2025_01 ... -- Jan
CREATE TABLE dex_transactions_2025_02 ... -- Feb
...
CREATE TABLE dex_transactions_2025_12 ... -- Dec
```

如果数据的时间戳超出预定义的分区范围，PostgreSQL会报错。修复方法是添加缺失的分区。

## 未来扩展

如果需要2026年的分区，可以创建新的迁移脚本：

```sql
-- migrations/003_add_2026_partitions.sql
CREATE TABLE dex_transactions_2026_01 PARTITION OF dex_transactions
    FOR VALUES FROM (1735689600) TO (1738368000); -- 2026-01-01 to 2026-02-01
-- ... 更多月份
```
