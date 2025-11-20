# backend/api_server.py

import os
import sqlite3
from pathlib import Path
from flask import Flask, jsonify, request, Response

from dotenv import load_dotenv
from web3 import Web3

from db import MonitorDatabase
from config import load_risk_monitor_contract

# -------------------------------------------------------------------
# 基础路径 / DB / 前端路径
# -------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "defi_monitor.db"

# 假设 frontend_simple 和 backend 是同级目录
FRONTEND_DIR = BASE_DIR.parent / "frontend_simple"
INDEX_PATH = FRONTEND_DIR / "index.html"

app = Flask(__name__)

# -------------------------------------------------------------------
# 链上合约配置：读取真实 level
# -------------------------------------------------------------------
load_dotenv()

# 和 monitor.py 使用同一个网络（例如 sepolia）
RISK_NETWORK = os.getenv("RISK_NETWORK", "sepolia")
# 和 monitor.py / 部署脚本使用同一个 label
MARKET_LABEL = os.getenv("MARKET_LABEL", "UNISWAP_USDC_WETH")


def calc_market_id(label: str) -> bytes:
    """与部署脚本 / monitor.py 保持一致：keccak(text)"""
    return Web3.keccak(text=label)


# bytes32 原始值（合约调用用这个）
MARKET_ID_BYTES = calc_market_id(MARKET_LABEL)
# 方便前端展示用的 hex 字符串
MARKET_ID_HEX = Web3.to_hex(MARKET_ID_BYTES)

# 初始化 Web3 + 风险监控合约（只读调用）
w3, risk_contract = load_risk_monitor_contract(RISK_NETWORK)


# ==================== 路由：前端 ====================

@app.route("/")
def index():
    """
    直接读取 frontend_simple/index.html 返回
    """
    if not INDEX_PATH.exists():
        return Response("index.html not found", status=500)

    html = INDEX_PATH.read_text(encoding="utf-8")
    return Response(html, mimetype="text/html")


# ==================== 路由：API ====================

@app.route("/api/status")
def api_status():
    try:
        if not DB_PATH.exists():
            return jsonify({
                "ok": False,
                "message": "数据库文件不存在，请先运行 monitor.py 生成数据"
            }), 200

        db = MonitorDatabase(DB_PATH)
        cur = db.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM risk_levels")
        count = cur.fetchone()[0] or 0

        cur.execute(
            """
            SELECT created_at, market_id, level, source
            FROM risk_levels
            ORDER BY created_at DESC
            LIMIT 1
            """
        )
        row = cur.fetchone()
        last_record = None
        if row:
            last_record = {
                "created_at": row[0],
                "market_id": row[1],
                "level": row[2],
                "source": row[3],
            }

        return jsonify({"ok": True, "records": int(count), "last": last_record}), 200
    except Exception as e:
        return jsonify({"ok": False, "message": f"后端异常: {e}"}), 500


@app.route("/api/risk")
def api_risk():
    """
    本地 SQLite 中的历史风险点，用于画时间序列图
    """
    limit = int(request.args.get("limit", 100))
    market = request.args.get("market")

    base_sql = """
        SELECT created_at, market_id, level, source
        FROM risk_levels
    """
    params = []
    if market:
        base_sql += " WHERE market_id = ?"
        params.append(market)

    # 关键：先按时间倒序取最新 N 条
    base_sql += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)

    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute(base_sql, params)
        rows = cur.fetchall()
        conn.close()

        # 再反转一次，让结果按时间正序返回，方便前端画图
        rows.reverse()

        data = [
            {
                "created_at": r[0],
                "market_id": r[1],
                "level": r[2],
                "source": r[3],
            }
            for r in rows
        ]
        return jsonify({"ok": True, "items": data}), 200
    except Exception as e:
        return jsonify({
            "ok": False,
            "message": f"查询失败: {e}",
            "items": []
        }), 500


@app.route("/api/onchain_risk")
def api_onchain_risk():
    """
    读取链上合约 RiskMonitor.markets[marketId] 的真实 level
    用于驱动前端的 🚥 风险灯
    """
    try:
        # struct MarketRisk { uint8 level; uint256 lastUpdate; bool exists; }
        m = risk_contract.functions.markets(MARKET_ID_BYTES).call()
        level = int(m[0])
        last_update = int(m[1])
        exists = bool(m[2])

        if not exists:
            return jsonify({
                "ok": False,
                "exists": False,
                "message": "Market not registered on-chain",
                "market_label": MARKET_LABEL,
                "market_id": MARKET_ID_HEX,
            }), 200

        return jsonify({
            "ok": True,
            "exists": True,
            "market_label": MARKET_LABEL,
            "market_id": MARKET_ID_HEX,
            "level": level,
            "last_update": last_update,  # 区块时间（秒级 Unix 时间戳）
        }), 200

    except Exception as e:
        return jsonify({
            "ok": False,
            "message": f"On-chain query failed: {e}"
        }), 500


if __name__ == "__main__":
    # 默认端口 8000
    app.run(host="0.0.0.0", port=8000, debug=True)