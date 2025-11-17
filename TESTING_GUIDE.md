# ChainMonitor 完整测试流程

本文档提供ChainMonitor项目从零开始的完整测试流程，包括Docker数据库部署、前端测试、后端测试等。

## 📋 前置要求

### 必需软件

- **Node.js** 18+ 和 npm
- **Python** 3.8+
- **Docker** 和 Docker Compose
- **Git**

### 可选软件

- **MetaMask** 浏览器插件（测试前端钱包功能）
- **PostgreSQL客户端**（如果想直接连接数据库）

## 🚀 测试流程

### 阶段1: 环境准备（5分钟）

#### 1.1 克隆代码（如果还没有）

```bash
git clone https://github.com/Lionheart784/ChainMonitor.git
cd ChainMonitor
```

#### 1.2 切换到正确的分支

```bash
git checkout claude/design-frontend-website-015ocuTnGybH79xGq4eLKFXJ
```

#### 1.3 配置环境变量

```bash
# 复制Docker环境配置模板
cp .env.docker .env

# 编辑.env文件，填写你的配置
nano .env
```

**必填项**：
```env
# 如果要测试真实链上数据，需要Infura Key
ETH_RPC_URL=https://mainnet.infura.io/v3/YOUR_INFURA_KEY
SEPOLIA_RPC_URL=https://sepolia.infura.io/v3/YOUR_INFURA_KEY

# 如果要部署合约，需要私钥（测试网账户即可）
PRIVATE_KEY=0xYOUR_TEST_PRIVATE_KEY

# Etherscan API Key（可选，用于巨鲸数据）
ETHERSCAN_API_KEY=YOUR_KEY
```

**注意**：数据库配置默认已正确设置，无需修改。

---

### 阶段2: 启动数据库（3分钟）

#### 2.1 使用Docker启动PostgreSQL

```bash
# 启动PostgreSQL容器
docker-compose up -d postgres

# 查看容器状态
docker-compose ps

# 查看日志（确认启动成功）
docker-compose logs -f postgres
```

**预期输出**：
```
chainmonitor-db  | PostgreSQL init process complete; ready for start up.
chainmonitor-db  | database system is ready to accept connections
```

按 `Ctrl+C` 退出日志查看。

#### 2.2 运行数据库迁移和生成测试数据

```bash
cd database

# 使用Docker专用安装脚本
chmod +x setup-docker.sh
./setup-docker.sh
```

**操作提示**：
- 当询问"Generate test data? (y/N):"时，输入 `y` 并回车

**预期输出**：
```
✅ Database connected successfully
✅ Generated 1 markets
✅ Generated 28 risk level records
✅ Generated 100 risk factor records
✅ Generated 500 DEX transactions
✅ Generated 50 whale transactions
✅ Generated 20 alerts
```

#### 2.3 验证数据库安装

```bash
# 测试数据库连接
python3 utils/db_helper.py
```

**预期输出**：
```
=== Testing DatabaseHelper ===

1. Market Overview:
   UNISWAP_USDC_WETH: Risk Level 2, Score 62.45

2. Latest Risk for UNISWAP_USDC_WETH:
   Level: 2, Score: 62.45

✅ All tests completed
```

#### 2.4 （可选）使用pgAdmin查看数据库

1. 启动pgAdmin容器：
```bash
docker-compose up -d pgadmin
```

2. 访问 http://localhost:5050
   - 邮箱: `admin@chainmonitor.com`
   - 密码: `admin`

3. 添加服务器连接：
   - Host: `postgres`（容器内部网络）或 `localhost`（外部访问）
   - Port: `5432`
   - Database: `chainmonitor`
   - Username: `chainmonitor_user`
   - Password: `chainmonitor_pass`

---

### 阶段3: 测试前端界面（5分钟）

#### 3.1 安装前端依赖

```bash
cd ../frontend
npm install
```

#### 3.2 配置前端环境变量

```bash
# 复制模板
cp .env.example .env

# 编辑配置（使用测试合约地址即可）
nano .env
```

```env
VITE_CONTRACT_ADDRESS=0x0000000000000000000000000000000000000000
VITE_SEPOLIA_RPC_URL=https://sepolia.infura.io/v3/YOUR_KEY
VITE_MAINNET_RPC_URL=https://mainnet.infura.io/v3/YOUR_KEY
```

**注意**：即使没有真实合约地址，前端也能正常运行（使用mock数据）。

#### 3.3 启动开发服务器

```bash
npm run dev
```

**预期输出**：
```
  VITE v5.0.8  ready in 324 ms

  ➜  Local:   http://localhost:3000/
  ➜  Network: use --host to expose
  ➜  press h + enter to show help
```

#### 3.4 测试前端功能

打开浏览器访问 **http://localhost:3000**

**检查清单**：

✅ **Dashboard页面**
- [ ] 显示全局风险状态卡片
- [ ] 显示综合评分（62/100左右）
- [ ] 显示DEX活跃度、巨鲸抛压、CEX流动三个指标
- [ ] 风险趋势图表正常显示
- [ ] 因子柱状图正常显示
- [ ] 监控市场卡片显示"UNISWAP USDC WETH"
- [ ] 最新事件流显示告警记录

✅ **Market Detail页面**
- [ ] 点击市场卡片进入详情页
- [ ] 显示当前风险等级大卡片
- [ ] 显示三个因子详情卡片
- [ ] 风险历史图表正常显示
- [ ] 最近交易表格显示数据
- [ ] 可点击交易哈希（跳转Etherscan）

✅ **Alerts页面**
- [ ] 点击导航栏"Alerts"
- [ ] 显示告警配置界面
- [ ] 风险阈值滑块可拖动
- [ ] 切换市场下拉菜单正常
- [ ] 告警历史显示记录
- [ ] 保存配置按钮可点击

✅ **响应式设计**
- [ ] 缩小浏览器窗口，布局自适应
- [ ] 侧边栏在小屏幕隐藏
- [ ] 图表在小屏幕下仍可查看

✅ **交互动画**
- [ ] 卡片悬停有上移效果
- [ ] 页面切换有过渡动画
- [ ] 数据加载有骨架屏

---

### 阶段4: 测试数据库API（3分钟）

#### 4.1 运行API集成测试

```bash
cd ../database
python3 examples/api_integration.py
```

**预期输出**：
```
==================================================
  ChainMonitor API Integration Test
==================================================

1. Testing Dashboard Data...
   Markets: 1
   Alerts: 20
   Sample Market: UNISWAP_USDC_WETH
   Risk Level: 2
   Risk Score: 62.45

2. Testing Market Detail...
   Current Risk Level: 2
   Risk Score: 62.45
   History Points: 28
   Transactions: 20

   Factors:
   - DEX Score: 28.5/40
   - Whale Score: 21.0/35
   - CEX Score: 13.0/30

3. Testing Store Monitoring Result...
   ✅ Stored: risk_id=29, factor_id=101

==================================================
  ✅ API Integration Test Complete
==================================================
```

#### 4.2 查看数据库中的数据

```bash
# 方法1: 使用psql客户端（如果已安装）
docker exec -it chainmonitor-db psql -U chainmonitor_user -d chainmonitor

# 在psql中运行查询
SELECT * FROM v_market_overview;
SELECT * FROM v_latest_risk;
SELECT COUNT(*) FROM dex_transactions;
\q

# 方法2: 使用Python脚本
python3 -c "
from utils.db_helper import DatabaseHelper
db = DatabaseHelper()
db.connect()
result = db.execute_query('SELECT COUNT(*) as count FROM dex_transactions', fetch_one=True)
print(f'Total transactions: {result[\"count\"]}')
"
```

---

### 阶段5: 测试后端监控（可选，需要真实RPC）

**注意**：这部分需要真实的以太坊RPC和API密钥。

#### 5.1 安装后端依赖

```bash
cd ../backend
pip install -r requirements.txt
```

#### 5.2 配置后端环境

确保 `.env` 文件包含：
```env
ETH_RPC_URL=https://mainnet.infura.io/v3/YOUR_INFURA_KEY
ETHERSCAN_API_KEY=YOUR_KEY
CONTRACT_ADDRESS=0x...  # 如果已部署合约

# 数据库配置
DB_HOST=localhost
DB_PORT=5432
DB_NAME=chainmonitor
DB_USER=chainmonitor_user
DB_PASSWORD=chainmonitor_pass
```

#### 5.3 运行监控脚本（测试模式）

```bash
# 注释掉monitor.py中上链的部分，只测试数据采集
python monitor.py
```

**预期行为**：
- 从以太坊主网抓取Uniswap V2交易数据
- 分析巨鲸行为
- 计算风险评分
- 打印风险等级（如果没有合约地址，跳过上链步骤）

---

### 阶段6: 测试智能合约部署（可选）

**注意**：需要Sepolia测试网ETH（可从水龙头获取）。

#### 6.1 编译合约

```bash
cd ..
npm install
npx hardhat compile
```

#### 6.2 部署到Sepolia测试网

```bash
# 确保.env中配置了SEPOLIA_RPC_URL和PRIVATE_KEY
npm run deploy:sepolia
```

**预期输出**：
```
Deploying RiskMonitor with keeper: 0x...
RiskMonitor deployed to: 0xABCDEF1234567890...
Registering market: UNISWAP_USDC_WETH
Market registered successfully!
```

#### 6.3 更新配置文件

将输出的合约地址填入：
- `.env` 中的 `CONTRACT_ADDRESS`
- `frontend/.env` 中的 `VITE_CONTRACT_ADDRESS`

#### 6.4 测试合约交互

```bash
# 运行Hardhat测试
npx hardhat test
```

---

## 🔍 故障排除

### 问题1: Docker容器启动失败

**症状**：`docker-compose up` 报错

**解决方案**：
```bash
# 检查Docker是否运行
docker ps

# 查看详细日志
docker-compose logs postgres

# 重启Docker服务
# Linux
sudo systemctl restart docker

# macOS/Windows
# 重启Docker Desktop应用
```

### 问题2: 数据库连接被拒绝

**症状**：`psycopg2.OperationalError: connection refused`

**解决方案**：
```bash
# 检查PostgreSQL容器状态
docker-compose ps

# 确认容器健康
docker exec chainmonitor-db pg_isready -U chainmonitor_user

# 检查端口占用
lsof -i :5432

# 如果端口被占用，修改docker-compose.yml中的端口映射
# 例如："5433:5432"，然后更新.env中的DB_PORT=5433
```

### 问题3: 前端依赖安装失败

**症状**：`npm install` 报错

**解决方案**：
```bash
# 清理缓存
npm cache clean --force

# 删除node_modules重新安装
rm -rf node_modules package-lock.json
npm install

# 或使用yarn
npm install -g yarn
yarn install
```

### 问题4: Python依赖安装失败

**症状**：`pip install` 报错

**解决方案**：
```bash
# 使用虚拟环境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 如果psycopg2安装失败，使用binary版本
pip install psycopg2-binary
```

### 问题5: 测试数据生成失败

**症状**：`generate_test_data.py` 报错

**解决方案**：
```bash
# 确认数据库连接
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=chainmonitor
export DB_USER=chainmonitor_user
export DB_PASSWORD=chainmonitor_pass

# 手动运行迁移
docker exec -i chainmonitor-db psql -U chainmonitor_user -d chainmonitor < database/migrations/001_init_schema.sql

# 重新生成数据
python3 seeds/generate_test_data.py
```

---

## 📊 测试数据说明

### 生成的测试数据包括：

| 数据类型 | 数量 | 说明 |
|---------|------|------|
| 市场 | 1个 | UNISWAP_USDC_WETH |
| 风险历史 | ~28条 | 7天数据，每天4个采样点 |
| 风险因子 | 100条 | 详细的三维度评分 |
| DEX交易 | 500条 | 模拟的Swap记录 |
| 巨鲸交易 | 50条 | 大额交易追踪 |
| 告警记录 | 20条 | 风险等级变化告警 |

### 风险评分范围：

- **风险等级**: 0 (正常) → 1 (注意) → 2 (警告)
- **综合评分**: 10-70分（模拟逐渐上升趋势）
- **DEX因子**: 15-35分 / 40分
- **巨鲸因子**: 10-30分 / 35分
- **CEX因子**: 5-25分 / 30分

---

## 🎯 完整测试检查清单

### 基础功能测试

- [ ] Docker容器成功启动
- [ ] 数据库Schema创建成功
- [ ] 测试数据生成成功
- [ ] 数据库连接测试通过

### 前端测试

- [ ] 前端开发服务器启动成功
- [ ] Dashboard页面正常显示
- [ ] Market Detail页面正常显示
- [ ] Alerts页面正常显示
- [ ] 图表和动画正常工作
- [ ] 响应式布局正常

### 后端测试

- [ ] API集成测试通过
- [ ] 数据库查询正常
- [ ] 数据插入正常

### 可选测试

- [ ] 智能合约编译成功
- [ ] 合约部署成功（测试网）
- [ ] 后端监控脚本运行（需RPC）

---

## 📚 下一步

测试完成后，你可以：

1. **对接真实数据**
   - 获取Infura RPC密钥
   - 部署合约到Sepolia
   - 运行真实的链上数据监控

2. **自定义开发**
   - 添加新的监控市场
   - 修改风险评分模型
   - 扩展前端功能

3. **生产部署**
   - 使用环境变量管理敏感信息
   - 配置反向代理（Nginx）
   - 设置自动化监控和告警

---

## 🆘 获取帮助

- **GitHub Issues**: https://github.com/Lionheart784/ChainMonitor/issues
- **文档**: 查看各模块的README.md
- **Discord**: （如果有社区）

---

**祝测试顺利！** 🎉
