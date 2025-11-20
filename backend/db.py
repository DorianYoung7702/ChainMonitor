# backend/db.py

import sqlite3
from pathlib import Path
from typing import List, Dict, Any

# 统一使用这个数据库文件
DB_PATH = Path(__file__).resolve().parent / "defi_monitor.db"


class MonitorDatabase:
    def __init__(self, db_path: Path | str = DB_PATH):
        self.db_path = str(db_path)
        # 加上 check_same_thread=False，方便 Flask / 监控脚本复用同一个类
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.create_tables()

    # ------------------------------------------------------------------
    # 建表：交易明细 / 风险等级 / 多因子原始指标
    # ------------------------------------------------------------------
    def create_tables(self):
        c = self.conn.cursor()

        # 1) DEX swap 明细
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp INTEGER,
                block_number INTEGER,
                tx_hash TEXT UNIQUE,
                token_in TEXT,
                token_out TEXT,
                amount_in TEXT,     -- 大整数，统一按字符串存
                amount_out TEXT,    -- 同上
                gas_used TEXT,      -- 同上
                gas_price TEXT,     -- 同上
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # 2) 风险等级时间序列（给前端画图）
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS risk_levels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                market_id TEXT,
                level INTEGER,
                source TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # 3) 多因子原始指标，用于动态分位数打分 & 回测
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS risk_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                market_id TEXT,
                dex_volume TEXT,           -- 注意这里用 TEXT 存大整数
                dex_trades INTEGER,
                whale_sell_total TEXT,
                whale_count_selling INTEGER,
                cex_net_inflow TEXT,
                pool_liquidity TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        self.conn.commit()

    # ------------------------------------------------------------------
    # 交易明细
    # ------------------------------------------------------------------
    def save_trades(self, trades: List[Dict[str, Any]]):
        if not trades:
            return

        with self.conn:
            c = self.conn.cursor()
            c.executemany(
                """
                INSERT OR IGNORE INTO trades(
                    tx_hash,
                    timestamp,
                    block_number,
                    token_in,
                    token_out,
                    amount_in,
                    amount_out,
                    gas_used,
                    gas_price
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        t["tx_hash"],
                        int(t["timestamp"]),
                        int(t["block_number"]),
                        t["token_in"],
                        t["token_out"],
                        str(t["amount_in"]),
                        str(t["amount_out"]),
                        str(t.get("gas_used", 0)),
                        str(t.get("gas_price", 0)),
                    )
                    for t in trades
                ],
            )

    # ------------------------------------------------------------------
    # 风险等级（给前端用）
    # ------------------------------------------------------------------
    def save_risk_level(self, market_id: str, level: int, source: str = "local"):
        c = self.conn.cursor()
        c.execute(
            """
            INSERT INTO risk_levels (market_id, level, source)
            VALUES (?, ?, ?)
            """,
            (market_id, int(level), source),
        )
        self.conn.commit()

    # ------------------------------------------------------------------
    # 多因子原始指标：保存 & 读取（动态分位打分会用到）
    # ------------------------------------------------------------------
    def save_metrics(self, market_id: str, metrics: Dict[str, Any]):
        """
        metrics 示例:
        {
            "dex_volume": int,
            "dex_trades": int,
            "whale_sell_total": int,
            "whale_count_selling": int,
            "cex_net_inflow": int,
            "pool_liquidity": int,
        }
        """
        dex_volume = int(metrics.get("dex_volume", 0) or 0)
        dex_trades = int(metrics.get("dex_trades", 0) or 0)
        whale_sell_total = int(metrics.get("whale_sell_total", 0) or 0)
        whale_count_selling = int(metrics.get("whale_count_selling", 0) or 0)
        cex_net_inflow = int(metrics.get("cex_net_inflow", 0) or 0)
        pool_liquidity = int(metrics.get("pool_liquidity", 0) or 0)

        with self.conn:
            self.conn.execute(
                """
                INSERT INTO risk_metrics (
                    market_id,
                    dex_volume,
                    dex_trades,
                    whale_sell_total,
                    whale_count_selling,
                    cex_net_inflow,
                    pool_liquidity
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    market_id,
                    str(dex_volume),          # 大整数转字符串
                    dex_trades,
                    str(whale_sell_total),
                    whale_count_selling,
                    str(cex_net_inflow),
                    str(pool_liquidity),
                ),
            )

    def load_recent_metrics(self, market_id: str, limit: int = 500) -> List[Dict[str, Any]]:
        """
        返回最近 limit 条历史指标，**全部转成 int**，
        确保 compute_risk_level_dynamic / percentile_rank 不会出现 str <= int 的问题。
        """
        c = self.conn.cursor()
        c.execute(
            """
            SELECT
                dex_volume,
                dex_trades,
                whale_sell_total,
                whale_count_selling,
                cex_net_inflow,
                pool_liquidity
            FROM risk_metrics
            WHERE market_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (market_id, int(limit)),
        )
        rows = c.fetchall()

        # rows 现在是从“最新 → 最旧”，反转成“最旧 → 最新”方便做时间序列分析
        rows.reverse()

        history: List[Dict[str, Any]] = []
        for row in rows:
            (
                dex_volume_raw,
                dex_trades_raw,
                whale_sell_total_raw,
                whale_count_selling_raw,
                cex_net_inflow_raw,
                pool_liquidity_raw,
            ) = row

            # 小心一点：任何异常都兜底成 0，避免线上崩溃
            try:
                dex_volume = int(dex_volume_raw)
            except Exception:
                dex_volume = 0

            try:
                dex_trades = int(dex_trades_raw)
            except Exception:
                dex_trades = 0

            try:
                whale_sell_total = int(whale_sell_total_raw)
            except Exception:
                whale_sell_total = 0

            try:
                whale_count_selling = int(whale_count_selling_raw)
            except Exception:
                whale_count_selling = 0

            try:
                cex_net_inflow = int(cex_net_inflow_raw)
            except Exception:
                cex_net_inflow = 0

            try:
                pool_liquidity = int(pool_liquidity_raw)
            except Exception:
                pool_liquidity = 0

            history.append(
                {
                    "dex_volume": dex_volume,
                    "dex_trades": dex_trades,
                    "whale_sell_total": whale_sell_total,
                    "whale_count_selling": whale_count_selling,
                    "cex_net_inflow": cex_net_inflow,
                    "pool_liquidity": pool_liquidity,
                }
            )

        return history

    # ------------------------------------------------------------------
    def close(self):
        try:
            self.conn.close()
        except Exception:
            pass