# DeFi Risk Sentinel · 链上多因子市场风险监控系统

> 基于以太坊主网真实数据的 **DeFi 风险“红绿灯”系统**：Python 监控脚本 + Solidity 风险合约 + 前端可视化仪表盘。

---

## 1. 项目简介

- **监控目标**：以太坊主网 Uniswap V2 USDC/WETH 池子
- **核心能力**：
  - 定期抓取链上交易和流动性数据
  - 统计巨鲸卖出行为与交易所热钱包净流入
  - 使用静态 + 动态多因子打分，将结果映射为 0–3 级风险等级
  - 通过 `RiskMonitor` 智能合约把风险等级写入链上
  - 前端 Dashboard 实时展示风险时间序列与当前“信号灯”

项目结构侧重**端到端链路**：**链上数据 → Python 计算 → SQLite 存储 → 合约写链 → 前端可视化**。

---

## 2. 系统架构

```text
Ethereum mainnet + Sepolia
        │
        ▼
Python monitor (backend/monitor.py)
  - fetch_recent_swaps
  - estimate_pool_liquidity
  - fetch_whale_metrics
  - fetch_cex_net_inflow
  - compute_risk_level_static / dynamic
  - send_update_risk_tx (updateRisk)
        │
        ▼
SQLite (defi_monitor.db)
  - risk_levels
  - risk_metrics
        │
        ├── Flask API (backend/api_server.py)
        │     - /api/status
        │     - /api/risk
        │     - /api/onchain_risk
        │
        ▼
RiskMonitor.sol (Sepolia)
  - markets[marketId].level
  - keeper = Python 脚本
        ▼
frontend_simple/index.html
  - 风险等级时间序列
  - 当前风险灯 & 提示
```

---

## 3. 核心组件说明

### 3.1 智能合约：`RiskMonitor.sol`

- 作用：在链上记录每个市场的风险等级。
- 主要数据结构：

```solidity
struct MarketRisk {
    uint8 level;       // 0=正常,1=注意,2=警告,3=高危
    uint256 lastUpdate;
    bool exists;
}
```

- 关键接口：
  - `registerMarket(bytes32 marketId)`：注册监控市场
  - `updateRisk(bytes32 marketId, uint8 newLevel)`：keeper/owner 更新风险
  - `setUserConfig(marketId, thresholdLevel, autoAlert)`：用户配置关注阈值
  - `checkAndAlert(marketId)` / `triggerAlertForUser(user, marketId)`：触发告警事件

合约由 `Ownable` 控制权限，Python 监控脚本作为 `keeper`。

---

### 3.2 后端监控脚本：`backend/monitor.py`

主要职责：

1. 周期性从主网抓取数据：
   - Uniswap V2 USDC/WETH Swap 事件（成交笔数、成交量）
   - 池子储备 `getReserves()`（估算流动性基数）
   - 已知巨鲸地址近期是否卖出（数量+规模）
   - 已知交易所热钱包净流入（短期资金进出）
2. 将原始指标写入 `risk_metrics` 表
3. 使用**静态 + 动态**多因子打分得到风险等级 0–3
4. 在满足“稳定 + 冷却时间”的条件下，调用合约 `updateRisk` 写入链上

关键函数：

```python
def compute_risk_level_static(metrics: Dict[str, Any]) -> int: ...
def compute_risk_level_dynamic(
    db: MonitorDatabase,
    market_id_hex: str,
    metrics: Dict[str, Any],
    history_window: int = 500,
) -> int: ...
```

- 当历史样本 < 30 条时，回退到静态规则；否则使用滚动窗口 + 百分位的动态打分。

---

### 3.3 数据库模块：`backend/db.py`

使用 SQLite 存储所有监控结果和原始指标。

重要表结构：

```sql
CREATE TABLE IF NOT EXISTS risk_levels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    market_id TEXT NOT NULL,
    level INTEGER NOT NULL,
    source TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS risk_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    market_id TEXT NOT NULL,
    dex_volume TEXT NOT NULL,
    dex_trades INTEGER NOT NULL,
    whale_sell_total TEXT NOT NULL,
    whale_count_selling INTEGER NOT NULL,
    cex_net_inflow TEXT NOT NULL,
    pool_liquidity TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

对应的封装方法：

```python
db.save_metrics(market_id_hex, metrics)
db.save_risk_level(market_id=market_id_hex, level=level, source="multi_factor_dynamic")
db.load_recent_metrics(market_id_hex, limit=history_window)
```

这些方法支持：
- 时间序列回放/可视化
- 事后回测与统计分析
- 支持未来接入回测脚本（PnL、最大回撤 vs. 风险等级）

---

### 3.4 市场配置与动态鲸鱼收集

- 静态配置文件：`backend/markets.json`
- 动态加载模块：`backend/market_loader.py`
- 动态鲸鱼收集脚本：`backend/collect_eth_whales.py`

工作流程：

1. `collect_eth_whales.py`：
   - 连接主网 RPC，扫描某个 token（默认 WETH）的 `Transfer` 日志
   - 聚合地址的总成交额与笔数，按照成交额排序
   - 选出 Top N 地址，写回 `markets.json`，并标记为 `AUTO_WHALE_*`
2. `market_loader.py`：
   - 统一从 `markets.json` 中加载所有市场，包括静态 DEX 池、手动 whales、动态 AUTO_WHALE_* 条目
   - `monitor.py` 使用 `load_markets()` 拿到鲸鱼地址列表和交易所地址列表

这样可以避免手工维护鲸鱼列表，让监控对象随着市场结构轻量动态更新。

---

### 3.5 前端仪表盘：`frontend_simple/index.html`

技术栈：**纯静态 HTML + 原生 JS + Chart.js**

- 启动方式：通过 `backend/api_server.py` 返回 `index.html`，前端再通过 `/api/*` 请求数据。
- UI 功能：
  - 左侧导航 + 顶部状态栏
  - 中间风险“信号灯”（Level 0–3）
  - 底部风险等级时间序列折线图
  - DEX Activity / Whales & CEX / Strategy Hint 三块统计卡片
- 主要接口：
  - `/api/status`：获取记录总数、最新一条时间戳
  - `/api/risk?limit=100`：获取最近 N 条 `risk_levels` 记录，绘制时间序列
  - 轮询 `pollRiskSeries()` 每 60 秒刷新一批新数据，图像“向前滚动”

---

## 4. 风险计算逻辑

### 4.1 静态多因子打分

1. **DEX 活跃度**：
   - 用池子流动性的某个比例作为 baseline
   - 计算 `dex_volume / baseline_volume` 的比值
   - 映射到 0–30 分区间，根据成交笔数附加奖励分

2. **巨鲸抛压**：
   - 以 `whale_sell_total / pool_liquidity` 的比例为核心
   - 再根据卖出巨鲸地址数附加分数
   - 最大上限 35 分

3. **CEX 净流入**：
   - `cex_net_inflow / pool_liquidity` 越高，得分越高
   - 最大上限 30 分

最终总分：`0–100`，映射成风险等级：

```text
score < 20  → Level 0
20 ≤ score < 40 → Level 1
40 ≤ score < 70 → Level 2
score ≥ 70 → Level 3
```

### 4.2 动态百分位打分

当历史样本足够（≥ 30 条）时：

- 分别对以下指标计算**历史百分位**：
  - DEX 成交量
  - DEX 成交笔数
  - 巨鲸卖出总量
  - CEX 净流入
- 把百分位映射为因子得分：

```text
p < 60%        → 0 分
60% ≤ p < 80%  → 10 分
80% ≤ p < 95%  → 20 分
p ≥ 95%        → 30 分
```

- DEX 分数：成交量和笔数的百分位平均后再映射
- Whale & CEX：各自独立映射，然后累加
- 总分同样通过 `level_thresholds = [20, 40, 70]` 映射到 0–3 级

这样可以做到：
- 在不同市场波动环境下自适应
- 高波动时期不会被“常态高波动”误判为极端风险

---

## 5. 部署与运行

### 5.1 前置依赖

- Python 3.10+
- Node.js（仅用于 Hardhat 部署合约）
- 一个以太坊主网 RPC（Infura/Alchemy 等）
- 一个 Sepolia 测试网 RPC
- Etherscan API Key（用于辅助查询，可选）

### 5.2 安装依赖

```bash
git clone <your-repo-url>
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

在 `backend/.env` 中配置：

```env
MAINNET_RPC=...
SEPOLIA_RPC=...
PRIVATE_KEY=...        # 部署/更新风险的 keeper 钱包私钥（建议测试网）
ETHERSCAN_API_KEY=...
RISK_NETWORK=sepolia
MARKET_LABEL=UNISWAP_USDC_WETH
```

### 5.3 部署合约（示意）

使用 Hardhat 或 Foundry 部署 `RiskMonitor.sol` 至 Sepolia，并记录：

- `RISK_MONITOR_ADDRESS`
- `KEEPER_ADDRESS`（即 Python 脚本使用的账户地址）

在 `config.py` 中填入对应信息。

### 5.4 运行监控脚本

```bash
cd backend
python monitor.py
```

脚本会：
- 周期性抓取主网数据
- 计算风险等级并写入 SQLite
- 在满足条件时调用合约 `updateRisk` 更新链上 level

### 5.5 启动 API + 前端

```bash
cd backend
python api_server.py
```

浏览器访问：`http://localhost:8000/` 即可看到仪表盘。

---

## 6. 如何用于回测与量化评估

利用 SQLite 中的 `risk_levels` 与 `risk_metrics`：

1. 导出为 CSV，在 Python / Pandas 中对比：
   - 不同风险等级区间内的市场波动率
   - 自定义策略在不同等级下的收益/回撤
2. 基于 `created_at` 和链上价格数据重构当时的市场状态：
   - 举例：Level ≥ 2 时减半仓位，与不减仓对比最大回撤
3. 统计指标示例：
   - “高危等级占比时间”
   - “进入 Level 3 前的平均预警时间”
   - “按风险等级的年化收益 / 波动 / Sharpe”

---

## 7. 后续扩展方向

- 引入更多因子：资金费率、永续 Basis、链上借贷利率等
- 尝试简单机器学习模型，做非线性风险映射（例如 Gradient Boosting）
- 支持多市场多池子管理，用统一 Dashboard 展示风险矩阵
- 与自动化交易策略/做市机器人集成，实现真正的“自动降仓 / 自动调参”
