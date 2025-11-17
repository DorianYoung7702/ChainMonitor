"""
ChainMonitor API Server (Mock Data Version)
FastAPI服务器，使用模拟数据，无需数据库
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from datetime import datetime, timedelta
import os
import random
import time

app = FastAPI(
    title="ChainMonitor API (Mock)",
    description="DeFi市场风险监控API - Mock数据版本",
    version="1.0.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# Mock数据生成函数
# ============================================

def generate_mock_markets():
    """生成模拟市场数据"""
    return [
        {
            "id": "UNISWAP_USDC_WETH",
            "label": "Uniswap USDC/WETH",
            "type": "dex_pool",
            "address": "0xB4e16d0168e52d35CaCD2c6185b44281Ec28C9Dc",
            "token0": "USDC",
            "token1": "WETH",
            "riskLevel": random.randint(0, 3),
            "riskScore": round(random.uniform(20, 85), 2),
            "lastUpdated": datetime.now().isoformat(),
            "isActive": True
        },
        {
            "id": "UNISWAP_DAI_USDC",
            "label": "Uniswap DAI/USDC",
            "type": "dex_pool",
            "address": "0xAE461cA67B15dc8dc81CE7615e0320dA1A9aB8D5",
            "token0": "DAI",
            "token1": "USDC",
            "riskLevel": random.randint(0, 2),
            "riskScore": round(random.uniform(10, 60), 2),
            "lastUpdated": datetime.now().isoformat(),
            "isActive": True
        },
        {
            "id": "UNISWAP_WBTC_WETH",
            "label": "Uniswap WBTC/WETH",
            "type": "dex_pool",
            "address": "0xBb2b8038a1640196FbE3e38816F3e67Cba72D940",
            "token0": "WBTC",
            "token1": "WETH",
            "riskLevel": random.randint(0, 2),
            "riskScore": round(random.uniform(15, 70), 2),
            "lastUpdated": datetime.now().isoformat(),
            "isActive": True
        }
    ]

def generate_risk_history(hours=24):
    """生成风险历史数据"""
    history = []
    now = datetime.now()
    for i in range(hours):
        timestamp = now - timedelta(hours=hours-i-1)
        history.append({
            "timestamp": timestamp.isoformat(),
            "level": random.randint(0, 3),
            "score": round(random.uniform(10, 90), 2)
        })
    return history

def generate_risk_factors():
    """生成风险因子数据"""
    return {
        "dex": {
            "score": round(random.uniform(10, 40), 2),
            "volumeRatio": round(random.uniform(0.01, 0.15), 4),
            "txCount": random.randint(100, 500),
            "liquidity": random.randint(1000000, 50000000)
        },
        "whale": {
            "score": round(random.uniform(5, 35), 2),
            "sellVolume": random.randint(10000, 100000),
            "activeCount": random.randint(1, 10),
            "sellRatio": round(random.uniform(0.01, 0.10), 4)
        },
        "cex": {
            "score": round(random.uniform(5, 30), 2),
            "totalInflow": random.randint(50000, 300000),
            "totalOutflow": random.randint(30000, 250000),
            "netInflow": random.randint(-50000, 100000),
            "netInflowRatio": round(random.uniform(-0.05, 0.08), 4)
        },
        "updatedAt": datetime.now().isoformat()
    }

def generate_transactions(limit=20):
    """生成交易记录"""
    transactions = []
    now = int(time.time())

    for i in range(limit):
        transactions.append({
            "txHash": f"0x{''.join(random.choices('0123456789abcdef', k=64))}",
            "blockNumber": random.randint(18000000, 18500000),
            "timestamp": now - random.randint(0, 86400),
            "tokenIn": random.choice(["USDC", "WETH", "DAI"]),
            "tokenOut": random.choice(["USDC", "WETH", "DAI"]),
            "amountIn": str(random.randint(1000000, 100000000)),
            "amountOut": str(random.randint(1000000, 100000000)),
            "trader": f"0x{''.join(random.choices('0123456789abcdef', k=40))}",
            "createdAt": datetime.now().isoformat()
        })

    return transactions

def generate_alerts(limit=10):
    """生成告警数据"""
    alerts = []
    severities = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    alert_types = ["RISK_LEVEL_CHANGE", "HIGH_VOLUME", "WHALE_ACTIVITY", "CEX_INFLOW"]

    for i in range(limit):
        severity = random.choice(severities)
        prev_level = random.randint(0, 2)
        new_level = prev_level + random.randint(1, 2)

        alerts.append({
            "id": i + 1,
            "marketId": random.choice(["UNISWAP_USDC_WETH", "UNISWAP_DAI_USDC", "UNISWAP_WBTC_WETH"]),
            "marketLabel": random.choice(["Uniswap USDC/WETH", "Uniswap DAI/USDC", "Uniswap WBTC/WETH"]),
            "type": random.choice(alert_types),
            "severity": severity,
            "previousLevel": prev_level,
            "newLevel": min(new_level, 3),
            "message": f"Risk level changed from {prev_level} to {min(new_level, 3)}",
            "isResolved": random.choice([True, False, False]),
            "createdAt": (datetime.now() - timedelta(hours=random.randint(0, 48))).isoformat()
        })

    return sorted(alerts, key=lambda x: x["createdAt"], reverse=True)

# ============================================
# API路由
# ============================================

@app.get("/")
def root():
    return {
        "message": "ChainMonitor API Server (Mock Data)",
        "version": "1.0.0-mock",
        "docs": "/docs",
        "note": "使用模拟数据，无需数据库"
    }

@app.get("/api/health")
def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "database": "mock",
        "mode": "development"
    }

@app.get("/api/markets")
def get_markets():
    """获取所有市场列表"""
    markets = generate_mock_markets()
    return {"markets": markets, "total": len(markets)}

@app.get("/api/markets/{market_id}")
def get_market_detail(market_id: str):
    """获取市场详情"""
    markets = generate_mock_markets()
    market = next((m for m in markets if m["id"] == market_id), None)

    if not market:
        raise HTTPException(status_code=404, detail="Market not found")

    market["description"] = f"{market['label']} - DeFi liquidity pool"
    market["currentRisk"] = {
        "level": market["riskLevel"],
        "score": market["riskScore"],
        "updatedAt": market["lastUpdated"]
    }

    return market

@app.get("/api/markets/{market_id}/risk-history")
def get_risk_history(market_id: str, hours: int = Query(24)):
    """获取市场风险历史"""
    history = generate_risk_history(hours)
    return {"marketId": market_id, "history": history}

@app.get("/api/markets/{market_id}/factors")
def get_risk_factors(market_id: str):
    """获取最新风险因子"""
    factors = generate_risk_factors()
    return {"marketId": market_id, "factors": factors}

@app.get("/api/markets/{market_id}/transactions")
def get_dex_transactions(market_id: str, limit: int = Query(100, le=500)):
    """获取DEX交易记录"""
    transactions = generate_transactions(min(limit, 100))
    return {"transactions": transactions, "total": len(transactions)}

@app.get("/api/alerts")
def get_alerts(severity: Optional[str] = None, limit: int = Query(50)):
    """获取告警列表"""
    alerts = generate_alerts(limit)

    if severity:
        alerts = [a for a in alerts if a["severity"] == severity.upper()]

    return {"alerts": alerts, "total": len(alerts)}

@app.get("/api/stats/daily")
def get_daily_stats(days: int = Query(7)):
    """获取每日统计数据"""
    stats = []
    for i in range(days):
        date = datetime.now() - timedelta(days=days-i-1)
        stats.append({
            "date": date.date().isoformat(),
            "totalMarkets": 3,
            "totalTransactions": random.randint(1000, 5000),
            "totalAlerts": random.randint(5, 30),
            "avgRiskScore": round(random.uniform(30, 70), 2),
            "maxRiskLevel": random.randint(1, 3)
        })
    return {"stats": stats}

@app.get("/api/stats/overview")
def get_overview_stats():
    """获取总览统计"""
    return {
        "totalMarkets": 3,
        "highRiskMarkets": random.randint(0, 2),
        "todayTransactions": random.randint(500, 2000),
        "unresolvedAlerts": random.randint(2, 10)
    }

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("API_PORT", 8000))
    print("=" * 60)
    print(f"🚀 ChainMonitor API Server (Mock Data Version)")
    print("=" * 60)
    print(f"📡 Server: http://localhost:{port}")
    print(f"📚 API Docs: http://localhost:{port}/docs")
    print(f"💾 Database: Mock Data (No Database Required)")
    print("=" * 60)

    uvicorn.run(app, host="0.0.0.0", port=port)
