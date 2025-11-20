# DeFi Risk Sentinel · On-chain Multi-factor Market Risk Monitor

> An end-to-end **DeFi risk “traffic light” system** powered by real Ethereum mainnet data: Python monitor, Solidity risk contract, and a web-based dashboard.

---

## 1. Overview

- **Market under watch**: Ethereum mainnet Uniswap V2 USDC/WETH pool  
- **What it does**:
  - Periodically pulls swaps and liquidity from on-chain data
  - Tracks whale selling and CEX hot-wallet net inflows
  - Combines static rules and dynamic percentile scoring into a 0–3 risk level
  - Writes the risk level on-chain via a `RiskMonitor` smart contract
  - Visualises the whole time series and current “signal light” in a dashboard

The project demonstrates a complete pipeline:  
**On-chain data → Python analytics → SQLite storage → on-chain risk level → frontend visualisation**.

---

## 2. System Architecture

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
  - keeper = Python monitor script
        ▼
frontend_simple/index.html
  - risk level time series
  - current traffic light & hints
```

---

## 3. Core Components

### 3.1 Smart Contract: `RiskMonitor.sol`

- Purpose: store the risk level of each market on-chain.
- Key struct:

```solidity
struct MarketRisk {
    uint8 level;       // 0=normal,1=watch,2=alert,3=danger
    uint256 lastUpdate;
    bool exists;
}
```

- Key functions:
  - `registerMarket(bytes32 marketId)`: register a DEX pool / market
  - `updateRisk(bytes32 marketId, uint8 newLevel)`: keeper/owner updates risk level
  - `setUserConfig(marketId, thresholdLevel, autoAlert)`: user sets alert thresholds
  - `checkAndAlert(marketId)` / `triggerAlertForUser(user, marketId)`: emit alert events

Ownership and a dedicated `keeper` address enforce who is allowed to write risk levels.

---

### 3.2 Backend Monitor Script: `backend/monitor.py`

Responsibilities:

1. Periodically pull data from Ethereum mainnet:
   - Uniswap V2 USDC/WETH swap events (trade count & volume)
   - Pool reserves via `getReserves()` (estimate liquidity baseline)
   - Whale selling activity (aggregated size and number of whale addresses)
   - CEX hot-wallet net inflow (short-term capital movement)
2. Persist raw metrics into `risk_metrics`
3. Compute a 0–3 risk level using **static + dynamic** scoring
4. When “stable and cooled down” conditions are met, call the contract’s `updateRisk` to write the level on-chain

Key functions:

```python
def compute_risk_level_static(metrics: Dict[str, Any]) -> int: ...
def compute_risk_level_dynamic(
    db: MonitorDatabase,
    market_id_hex: str,
    metrics: Dict[str, Any],
    history_window: int = 500,
) -> int: ...
```

- If the number of historical points is < 30, fall back to the static rules.
- Otherwise, use a rolling window and percentile-based scoring for dynamic, regime-aware risk.

---

### 3.3 Database Layer: `backend/db.py`

SQLite is used for persisting monitoring outputs and raw metrics.

Key tables:

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

Key helper methods:

```python
db.save_metrics(market_id_hex, metrics)
db.save_risk_level(market_id=market_id_hex, level=level, source="multi_factor_dynamic")
db.load_recent_metrics(market_id_hex, limit=history_window)
```

These support:

- Time-series visualisation on the frontend
- Offline backtesting & analysis
- Future integration with PnL-based backtest scripts (e.g. max drawdown vs. risk level)

---

### 3.4 Market Config & Dynamic Whale Collection

- Static config file: `backend/markets.json`
- Unified loader: `backend/market_loader.py`
- Dynamic whale collector: `backend/collect_eth_whales.py`

Workflow:

1. `collect_eth_whales.py`:
   - Connects to mainnet via RPC and scans `Transfer` logs of a given ERC20 (default: WETH)
   - Aggregates total transferred volume and tx count per address
   - Picks top-N addresses and writes them back into `markets.json` as `AUTO_WHALE_*` entries
2. `market_loader.py`:
   - Loads all markets from `markets.json`, combining static DEX pools, manually configured whales, and dynamic `AUTO_WHALE_*` items
   - `monitor.py` calls `load_markets()` to obtain whale and exchange address lists

This removes manual maintenance of whale lists and lets the monitor adapt as market structure evolves.

---

### 3.5 Frontend Dashboard: `frontend_simple/index.html`

Tech: **plain HTML + vanilla JS + Chart.js**

- Served by `backend/api_server.py` as a static page
- Frontend calls:
  - `/api/status` – global stats & last record
  - `/api/risk?limit=100` – recent `risk_levels` for the time series
- UI:
  - Sidebar navigation + top status bar
  - Central risk “traffic light” (levels 0–3)
  - Time-series chart of risk levels (last 100 points)
  - Three stat cards: DEX Activity / Whales & CEX / Strategy Hint
- Polling:
  - `pollRiskSeries()` runs every 60 seconds to fetch new points and append them to the chart (keeping only the latest 100 points)

---

## 4. Risk Scoring Logic

### 4.1 Static Multi-factor Scoring

1. **DEX activity**:
   - Define a baseline volume as a fraction of pool liquidity
   - Compute `dex_volume / baseline_volume`
   - Map the ratio into a 0–30 score, with extra points for large trade counts

2. **Whale pressure**:
   - Use `whale_sell_total / pool_liquidity` as core ratio
   - Add extra points when more whales are selling
   - Cap at 35 points

3. **CEX net inflow**:
   - Higher `cex_net_inflow / pool_liquidity` → higher score
   - Cap at 30 points

Total score is in `[0, 100]`, mapped to levels by `level_thresholds`:

```text
score < 20        → Level 0
20 ≤ score < 40   → Level 1
40 ≤ score < 70   → Level 2
score ≥ 70        → Level 3
```

### 4.2 Dynamic Percentile-based Scoring

When enough history exists (≥ 30 data points):

- Compute historical percentiles for:
  - DEX volume
  - DEX trade count
  - Whale selling total
  - CEX net inflow

Map each percentile `p` to a factor score:

```text
p < 60%        → 0
60% ≤ p < 80%  → 10
80% ≤ p < 95%  → 20
p ≥ 95%        → 30
```

- DEX factor: average of volume percentile and trade-count percentile, then mapped to score
- Whale & CEX factors: each mapped independently, then added
- The final score is fed through the same `level_thresholds = [20, 40, 70]` to get levels 0–3

This makes the system more **regime-aware**, preventing normal high-volatility regimes from being constantly flagged as “danger”.

---

## 5. Deployment & Usage

### 5.1 Prerequisites

- Python 3.10+
- Node.js (for Hardhat contract deployment)
- Ethereum mainnet RPC (e.g. Infura / Alchemy)
- Sepolia testnet RPC
- Etherscan API Key (optional but useful)

### 5.2 Install Dependencies

```bash
git clone <your-repo-url>
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Set up `backend/.env`:

```env
MAINNET_RPC=...
SEPOLIA_RPC=...
PRIVATE_KEY=...        # keeper wallet private key (ideally on testnet)
ETHERSCAN_API_KEY=...
RISK_NETWORK=sepolia
MARKET_LABEL=UNISWAP_USDC_WETH
```

### 5.3 Deploy Smart Contract (sketch)

Deploy `RiskMonitor.sol` to Sepolia via Hardhat or Foundry, then record:

- `RISK_MONITOR_ADDRESS`
- `KEEPER_ADDRESS` (the account whose `PRIVATE_KEY` the Python monitor uses)

Wire these into `config.py`.

### 5.4 Run the Monitor

```bash
cd backend
python monitor.py
```

The script will:

- Periodically fetch mainnet data
- Compute risk levels and store them in SQLite
- Push new levels on-chain via `updateRisk` when conditions are met

### 5.5 Start API & Frontend

```bash
cd backend
python api_server.py
```

Visit `http://localhost:8000/` to view the dashboard.

---

## 6. Backtesting & Evaluation

Using data from `risk_levels` and `risk_metrics`, you can:

1. Export to CSV & analyse with pandas:
   - Volatility under each risk regime (Level 0–3)
   - Strategy PnL / max drawdown conditional on risk level
2. Rebuild market states around each risk timestamp:
   - Example: “cut position by half when level ≥ 2” vs. “never de-risk”
3. Compute summary statistics:
   - Fraction of time spent in each risk level
   - Average lead time before Level 3 events
   - Annualised return / volatility / Sharpe by regime

This turns the dashboard into a quant research tool rather than just a visualisation.

---

## 7. Possible Extensions

- Add more factors: funding rates, perp basis, on-chain lending rates, etc.
- Experiment with simple ML models (e.g. gradient boosting) to learn non-linear mappings from factors to risk
- Extend to multiple markets/pools and show a risk matrix on the dashboard
- Integrate with market-making / trading bots for fully automated de-risking and parameter tuning
