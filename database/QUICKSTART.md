# 快速开始

5分钟内设置ChainMonitor数据库并生成测试数据。

## 🚀 一键安装

```bash
cd database
./setup.sh
```

这个脚本会自动：
1. ✅ 检查PostgreSQL安装
2. ✅ 创建数据库和用户
3. ✅ 运行schema迁移
4. ✅ 安装Python依赖
5. ✅ 生成测试数据
6. ✅ 创建.env配置文件

## 📋 手动安装

如果你想手动控制每个步骤：

### 1. 创建数据库

```bash
sudo -u postgres psql

CREATE DATABASE chainmonitor;
CREATE USER chainmonitor_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE chainmonitor TO chainmonitor_user;
\q
```

### 2. 运行迁移

```bash
psql -U chainmonitor_user -d chainmonitor -f migrations/001_init_schema.sql
```

### 3. 安装Python依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

```bash
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=chainmonitor
export DB_USER=chainmonitor_user
export DB_PASSWORD=your_password
```

### 5. 生成测试数据

```bash
python seeds/generate_test_data.py
```

## 🔍 验证安装

测试数据库连接：

```bash
python utils/db_helper.py
```

你应该看到：

```
=== Testing DatabaseHelper ===

1. Market Overview:
   UNISWAP_USDC_WETH: Risk Level 2, Score 62.45

2. Latest Risk for UNISWAP_USDC_WETH:
   Level: 2, Score: 62.45

...

✅ All tests completed
```

## 📊 查看数据

连接到数据库：

```bash
psql -U chainmonitor_user -d chainmonitor
```

查询示例：

```sql
-- 查看所有市场
SELECT * FROM v_market_overview;

-- 查看最新风险等级
SELECT * FROM v_latest_risk;

-- 查看最近的交易
SELECT * FROM dex_transactions ORDER BY timestamp DESC LIMIT 10;

-- 查看告警
SELECT * FROM alerts ORDER BY created_at DESC LIMIT 10;
```

## 🔧 常见问题

### PostgreSQL未运行

```bash
# Linux
sudo systemctl start postgresql

# macOS
brew services start postgresql@14
```

### 权限错误

```sql
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO chainmonitor_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO chainmonitor_user;
```

### Python依赖安装失败

使用虚拟环境：

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 🎯 下一步

1. **集成到后端**: 查看 `examples/api_integration.py`
2. **前端对接**: 使用API返回的JSON格式数据
3. **自定义数据**: 修改 `seeds/generate_test_data.py`

## 📚 更多文档

- [完整文档](README.md)
- [Schema详情](migrations/001_init_schema.sql)
- [API示例](examples/api_integration.py)
