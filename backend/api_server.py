"""
ChainMonitor API Server
FastAPI服务器，为前端提供数据接口
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'database'))

from database.utils.db_helper import DatabaseHelper

load_dotenv()

app = FastAPI(
    title="ChainMonitor API",
    description="DeFi市场风险监控API",
    version="1.0.0"
)

# CORS配置 - 允许前端访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # Vite默认5173
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 数据库连接
db = DatabaseHelper()


@app.get("/")
def root():
    return {
        "message": "ChainMonitor API Server",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/api/health")
def health_check():
    """健康检查"""
    try:
        # 测试数据库连接
        db.execute_query("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


@app.get("/api/markets")
def get_markets():
    """获取所有市场列表"""
    query = """
    SELECT
        m.market_id,
        m.label,
        m.market_type,
        m.contract_address,
        m.token0_symbol,
        m.token1_symbol,
        lr.risk_level AS current_risk_level,
        lr.risk_score AS current_risk_score,
        lr.created_at AS last_updated,
        m.is_active
    FROM markets m
    LEFT JOIN v_latest_risk lr ON m.market_id = lr.market_id
    WHERE m.is_active = TRUE
    ORDER BY lr.risk_level DESC NULLS LAST, m.label
    """

    results = db.execute_query(query)

    markets = []
    for row in results:
        markets.append({
            "id": row[0],
            "label": row[1],
            "type": row[2],
            "address": row[3],
            "token0": row[4],
            "token1": row[5],
            "riskLevel": row[6] if row[6] is not None else 0,
            "riskScore": float(row[7]) if row[7] is not None else 0,
            "lastUpdated": row[8].isoformat() if row[8] else None,
            "isActive": row[9]
        })

    return {"markets": markets, "total": len(markets)}


@app.get("/api/markets/{market_id}")
def get_market_detail(market_id: str):
    """获取市场详情"""
    # 基本信息
    query = """
    SELECT
        market_id, label, market_type, contract_address,
        token0_symbol, token1_symbol, description
    FROM markets
    WHERE market_id = %s
    """

    result = db.execute_query(query, (market_id,))
    if not result:
        raise HTTPException(status_code=404, detail="Market not found")

    row = result[0]
    market = {
        "id": row[0],
        "label": row[1],
        "type": row[2],
        "address": row[3],
        "token0": row[4],
        "token1": row[5],
        "description": row[6]
    }

    # 最新风险信息
    risk_query = """
    SELECT risk_level, risk_score, created_at
    FROM v_latest_risk
    WHERE market_id = %s
    """
    risk_result = db.execute_query(risk_query, (market_id,))
    if risk_result:
        market["currentRisk"] = {
            "level": risk_result[0][0],
            "score": float(risk_result[0][1]),
            "updatedAt": risk_result[0][2].isoformat()
        }

    return market


@app.get("/api/markets/{market_id}/risk-history")
def get_risk_history(
    market_id: str,
    hours: int = Query(24, description="最近N小时的数据")
):
    """获取市场风险历史"""
    query = """
    SELECT
        created_at,
        risk_level,
        risk_score
    FROM risk_levels
    WHERE market_id = %s
        AND created_at >= NOW() - INTERVAL '%s hours'
    ORDER BY created_at ASC
    """

    results = db.execute_query(query, (market_id, hours))

    history = []
    for row in results:
        history.append({
            "timestamp": row[0].isoformat(),
            "level": row[1],
            "score": float(row[2])
        })

    return {"marketId": market_id, "history": history}


@app.get("/api/markets/{market_id}/factors")
def get_risk_factors(market_id: str):
    """获取最新风险因子"""
    query = """
    SELECT
        dex_score, dex_volume_ratio, dex_tx_count, dex_liquidity,
        whale_score, whale_sell_volume, whale_active_count, whale_sell_ratio,
        cex_score, cex_total_inflow, cex_total_outflow, cex_net_inflow, cex_net_inflow_ratio,
        created_at
    FROM risk_factors
    WHERE market_id = %s
    ORDER BY created_at DESC
    LIMIT 1
    """

    result = db.execute_query(query, (market_id,))
    if not result:
        return {"marketId": market_id, "factors": None}

    row = result[0]
    factors = {
        "dex": {
            "score": float(row[0]) if row[0] else 0,
            "volumeRatio": float(row[1]) if row[1] else 0,
            "txCount": row[2] if row[2] else 0,
            "liquidity": float(row[3]) if row[3] else 0
        },
        "whale": {
            "score": float(row[4]) if row[4] else 0,
            "sellVolume": float(row[5]) if row[5] else 0,
            "activeCount": row[6] if row[6] else 0,
            "sellRatio": float(row[7]) if row[7] else 0
        },
        "cex": {
            "score": float(row[8]) if row[8] else 0,
            "totalInflow": float(row[9]) if row[9] else 0,
            "totalOutflow": float(row[10]) if row[10] else 0,
            "netInflow": float(row[11]) if row[11] else 0,
            "netInflowRatio": float(row[12]) if row[12] else 0
        },
        "updatedAt": row[13].isoformat()
    }

    return {"marketId": market_id, "factors": factors}


@app.get("/api/markets/{market_id}/transactions")
def get_dex_transactions(
    market_id: str,
    limit: int = Query(100, le=500),
    offset: int = 0
):
    """获取DEX交易记录"""
    query = """
    SELECT
        tx_hash, block_number, timestamp,
        token_in, token_out, amount_in, amount_out,
        trader_address, created_at
    FROM dex_transactions
    WHERE market_id = %s
    ORDER BY timestamp DESC
    LIMIT %s OFFSET %s
    """

    results = db.execute_query(query, (market_id, limit, offset))

    transactions = []
    for row in results:
        transactions.append({
            "txHash": row[0],
            "blockNumber": row[1],
            "timestamp": row[2],
            "tokenIn": row[3],
            "tokenOut": row[4],
            "amountIn": str(row[5]),
            "amountOut": str(row[6]),
            "trader": row[7],
            "createdAt": row[8].isoformat()
        })

    return {"transactions": transactions, "total": len(transactions)}


@app.get("/api/alerts")
def get_alerts(
    severity: Optional[str] = None,
    limit: int = Query(50, le=200)
):
    """获取告警列表"""
    base_query = """
    SELECT
        a.id, a.market_id, m.label, a.alert_type, a.severity,
        a.previous_level, a.new_level, a.message,
        a.is_resolved, a.created_at
    FROM alerts a
    JOIN markets m ON a.market_id = m.market_id
    """

    params = []
    if severity:
        base_query += " WHERE a.severity = %s"
        params.append(severity.upper())

    base_query += " ORDER BY a.created_at DESC LIMIT %s"
    params.append(limit)

    results = db.execute_query(base_query, tuple(params))

    alerts = []
    for row in results:
        alerts.append({
            "id": row[0],
            "marketId": row[1],
            "marketLabel": row[2],
            "type": row[3],
            "severity": row[4],
            "previousLevel": row[5],
            "newLevel": row[6],
            "message": row[7],
            "isResolved": row[8],
            "createdAt": row[9].isoformat()
        })

    return {"alerts": alerts, "total": len(alerts)}


@app.get("/api/stats/daily")
def get_daily_stats(days: int = Query(7, le=90)):
    """获取每日统计数据"""
    query = """
    SELECT
        stat_date, total_markets, total_transactions,
        total_alerts, avg_risk_score, max_risk_level
    FROM monitoring_stats
    WHERE stat_date >= CURRENT_DATE - INTERVAL '%s days'
    ORDER BY stat_date DESC
    """

    results = db.execute_query(query, (days,))

    stats = []
    for row in results:
        stats.append({
            "date": row[0].isoformat(),
            "totalMarkets": row[1],
            "totalTransactions": row[2],
            "totalAlerts": row[3],
            "avgRiskScore": float(row[4]) if row[4] else 0,
            "maxRiskLevel": row[5]
        })

    return {"stats": stats}


@app.get("/api/stats/overview")
def get_overview_stats():
    """获取总览统计"""
    # 市场总数
    markets_query = "SELECT COUNT(*) FROM markets WHERE is_active = TRUE"
    markets_count = db.execute_query(markets_query)[0][0]

    # 高危市场数
    high_risk_query = """
    SELECT COUNT(*) FROM v_latest_risk WHERE risk_level >= 2
    """
    high_risk_count = db.execute_query(high_risk_query)[0][0]

    # 今日交易数
    today_tx_query = """
    SELECT COUNT(*) FROM dex_transactions
    WHERE created_at >= CURRENT_DATE
    """
    today_tx = db.execute_query(today_tx_query)[0][0]

    # 未解决告警数
    unresolved_alerts_query = """
    SELECT COUNT(*) FROM alerts WHERE is_resolved = FALSE
    """
    unresolved_alerts = db.execute_query(unresolved_alerts_query)[0][0]

    return {
        "totalMarkets": markets_count,
        "highRiskMarkets": high_risk_count,
        "todayTransactions": today_tx,
        "unresolvedAlerts": unresolved_alerts
    }


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("API_PORT", 8000))
    print(f"🚀 启动 ChainMonitor API Server on http://localhost:{port}")
    print(f"📚 API文档: http://localhost:{port}/docs")

    uvicorn.run(app, host="0.0.0.0", port=port)
