# ChainMonitor - DeFi市场风险监控系统

一个完整的DeFi市场风险监控和预警系统，结合智能合约、链上数据分析、数据库存储和专业前端界面。

## 📁 项目结构

```
ChainMonitor/
├── contracts/          # Solidity智能合约
│   └── RiskMonitor.sol
├── scripts/            # 部署脚本
│   └── deployRiskMonitor.js
├── backend/            # Python后端监控服务
│   ├── monitor.py      # 主监控脚本
│   ├── chain_data.py   # DEX数据采集
│   ├── whale_cex.py    # 巨鲸和CEX分析
│   └── db.py           # 数据库操作
├── database/           # PostgreSQL数据库模块
│   ├── migrations/     # Schema迁移脚本
│   ├── seeds/          # 测试数据生成器
│   ├── utils/          # 数据库工具类
│   └── examples/       # API集成示例
├── frontend/           # React前端应用
│   ├── src/
│   │   ├── components/ # UI组件
│   │   ├── pages/      # 页面组件
│   │   ├── hooks/      # React Hooks
│   │   └── utils/      # 工具函数
│   └── package.json
└── README.md
```

## ✨ 核心功能

### 智能合约（Sepolia测试网）
- ✅ 多市场风险等级管理（0-3级）
- ✅ 用户自定义告警阈值
- ✅ 链上事件触发和记录
- ✅ 角色权限管理（Owner/Keeper）

### 后端监控服务
- ✅ 实时DEX交易数据采集（Uniswap V2）
- ✅ 巨鲸地址行为追踪
- ✅ CEX资金流动分析
- ✅ 多因子风险评分模型
- ✅ 自动上链风险等级

### 数据库（PostgreSQL）
- ✅ 完整的schema设计（10张表）
- ✅ 时序数据优化（分区表）
- ✅ 测试数据生成器
- ✅ API集成示例

### 前端界面（React）
- ✅ 实时风险监控仪表盘
- ✅ 市场详情和因子分析
- ✅ 告警配置和历史
- ✅ 数据可视化图表
- ✅ 钱包连接和合约交互

## 🚀 快速开始

### ⚡ 5分钟快速测试（推荐）

使用Docker一键启动所有服务，无需安装PostgreSQL：

```bash
# 1. 配置环境变量
cp .env.docker .env

# 2. 一键启动所有服务
./quick-start.sh
```

这将自动：
- ✅ 启动PostgreSQL Docker容器
- ✅ 创建数据库schema
- ✅ 生成测试数据
- ✅ 启动前端开发服务器

然后访问 **http://localhost:3000** 查看效果！

详细测试流程见：[TESTING_GUIDE.md](TESTING_GUIDE.md)

---

### 📦 完整部署流程

#### 1. 部署智能合约

```bash
# 安装依赖
npm install

# 编译合约
npx hardhat compile

# 配置.env文件
cp .env.example .env
# 填写 SEPOLIA_RPC_URL, PRIVATE_KEY 等

# 部署到Sepolia测试网
npm run deploy:sepolia
# 记录输出的合约地址
```

#### 2. 设置数据库

**方式A: 使用Docker（推荐）**

```bash
cd database

# Docker一键安装
./setup-docker.sh
```

**方式B: 使用本地PostgreSQL**

```bash
cd database

# 本地PostgreSQL安装
./setup.sh

# 或手动安装
psql -U postgres -c "CREATE DATABASE chainmonitor"
psql -U chainmonitor_user -d chainmonitor -f migrations/001_init_schema.sql
pip install -r requirements.txt
python seeds/generate_test_data.py
```

详见 [database/QUICKSTART.md](database/QUICKSTART.md)

### 3. 运行后端监控

```bash
cd backend
pip install -r requirements.txt

# 配置.env（添加数据库连接）
export CONTRACT_ADDRESS=0x...  # 步骤1的合约地址
export DB_HOST=localhost
export DB_NAME=chainmonitor

# 运行监控脚本
python monitor.py
```

监控脚本会：
- 从以太坊主网抓取Uniswap V2交易数据
- 追踪巨鲸地址和CEX资金流动
- 计算多因子风险评分（0-100）
- 自动上链风险等级变化

### 4. 启动前端界面

```bash
cd frontend
npm install

# 配置.env
cp .env.example .env
# 填写 VITE_CONTRACT_ADDRESS, VITE_SEPOLIA_RPC_URL 等

# 启动开发服务器
npm run dev

# 访问 http://localhost:3000
```

详见 [frontend/README.md](frontend/README.md)

## 📊 技术栈

| 层级 | 技术 |
|------|------|
| 智能合约 | Solidity 0.8.20, Hardhat, OpenZeppelin |
| 后端 | Python 3.x, web3.py, psycopg2 |
| 数据库 | PostgreSQL 14+ (分区表, 索引优化) |
| 前端 | React 18, TypeScript, Vite |
| 样式 | Tailwind CSS |
| 图表 | Recharts |
| 区块链交互 | ethers.js v6 |

## 📖 详细文档

- **合约文档**: [contracts/README.md](contracts/README.md)
- **后端文档**: [backend/README.md](backend/README.md)
- **数据库文档**: [database/README.md](database/README.md)
- **前端文档**: [frontend/README.md](frontend/README.md)
- **API集成**: [database/examples/api_integration.py](database/examples/api_integration.py)

## 🎯 使用场景

1. **DeFi投资者**: 实时监控市场风险，及时规避损失
2. **量化团队**: 集成风险数据到交易策略
3. **研究机构**: 分析链上数据和市场行为
4. **开发者**: 学习全栈DeFi应用开发

## 🔧 配置示例

### 环境变量（.env）

```env
# 合约部署
SEPOLIA_RPC_URL=https://sepolia.infura.io/v3/YOUR_KEY
PRIVATE_KEY=0x...

# 监控配置
CONTRACT_ADDRESS=0x...
ETHERSCAN_API_KEY=YOUR_KEY
ETH_RPC_URL=https://mainnet.infura.io/v3/YOUR_KEY

# 数据库
DB_HOST=localhost
DB_PORT=5432
DB_NAME=chainmonitor
DB_USER=chainmonitor_user
DB_PASSWORD=your_password
```

## 🛠️ 开发指南

### 添加新的监控市场

1. 更新 `backend/markets.json`
2. 在合约中注册市场ID
3. 修改 `monitor.py` 添加数据采集逻辑
4. 前端会自动显示新市场

### 自定义风险因子

编辑 `backend/monitor.py` 中的评分函数：

```python
def calculate_risk_score(dex_data, whale_data, cex_data):
    # 自定义评分逻辑
    score = (
        dex_score * 0.4 +
        whale_score * 0.35 +
        cex_score * 0.25
    )
    return score
```

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 License

MIT License
