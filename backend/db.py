# backend/db.py

import sqlite3
from pathlib import Path
from typing import List, Dict, Any

# 统一使用这个数据库文件
DB_PATH = Path(__file__).resolve().parent / "defi_monitor.db"


class MonitorDatabase:
    def __init__(self, db_path: Path | str = DB_PATH):
        self.db_path = str(db_path)
        # allow multi-thread use if将来需要，可以加 check_same_thread=False
        self.conn = sqlite3.connect(self.db_path)
        self.create_tables()

    def create_tables(self):
        c = self.conn.cursor()
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
                gas_used TEXT,      -- 也可能很大，按字符串存
                gas_price TEXT,     -- 同上
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
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
        self.conn.commit()

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
                        int(t["timestamp"]),         # 区块时间戳
                        int(t["block_number"]),      # 区块号
                        t["token_in"],
                        t["token_out"],
                        str(t["amount_in"]),         # 大整数 -> 字符串
                        str(t["amount_out"]),
                        str(t.get("gas_used", 0)),
                        str(t.get("gas_price", 0)),
                    )
                    for t in trades
                ],
            )

    def save_risk_level(self, market_id: str, level: int, source: str = "local"):
        c = self.conn.cursor()
        c.execute(
            """
            INSERT INTO risk_levels (market_id, level, source)
            VALUES (?, ?, ?)
            """,
            (market_id, level, source),
        )
        self.conn.commit()

    def close(self):
        try:
            self.conn.close()
        except Exception:
            pass