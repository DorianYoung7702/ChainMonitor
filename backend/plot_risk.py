# backend/plot_risk.py

import sqlite3
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
from web3 import Web3

DB_PATH = Path(__file__).resolve().parent / "defi_monitor.db"

# 和 monitor.py 完全一致的 label
MARKET_LABEL = "UNISWAP_USDC_WETH"


def load_risk_levels() -> pd.DataFrame:
    if not DB_PATH.exists():
        raise FileNotFoundError(f"找不到数据库文件: {DB_PATH}，请先运行 monitor.py 生成数据。")

    conn = sqlite3.connect(DB_PATH)
    try:
        # 注意这里只有 created_at，没有 timestamp 字段
        df = pd.read_sql_query(
            """
            SELECT id, created_at, market_id, level, source
            FROM risk_levels
            ORDER BY id ASC
            """,
            conn,
        )
    finally:
        conn.close()

    # 转成 pandas 的时间类型
    df["created_at"] = pd.to_datetime(df["created_at"])
    return df


def main():
    df = load_risk_levels()

    print(f"📊 risk_levels 总记录数: {len(df)}")
    print(df.tail())

    if df.empty:
        print("⚠️ risk_levels 表里没有任何记录，请先运行一段时间 monitor.py。")
        return

    # 计算和 monitor.py 完全相同的 marketId
    market_id = Web3.keccak(text=MARKET_LABEL).hex()
    print(f"当前绘图使用的 market_id: {market_id}")

    df_pair = df[df["market_id"] == market_id].copy()
    print(f"筛选出该池子的记录数: {len(df_pair)}")

    if df_pair.empty:
        print("⚠️ 数据库里没有这个 market_id 对应的记录。")
        print("  请在 sqlite3 里查看 risk_levels 表中实际的 market_id 是否一致。")
        return

    # 画图
    plt.figure(figsize=(12, 5))
    plt.step(df_pair["created_at"], df_pair["level"], where="post", linewidth=2)

    plt.title(f"{MARKET_LABEL} 风险等级随时间变化（合约 RiskMonitor 输出）", fontsize=14)
    plt.xlabel("时间", fontsize=12)
    plt.ylabel("风险等级", fontsize=12)

    plt.yticks(
        [0, 1, 2, 3],
        ["0 级（绿色）", "1 级（浅黄）", "2 级（橙色）", "3 级（红色）"],
        fontsize=10,
    )
    plt.grid(axis="y", linestyle="--", alpha=0.4)
    plt.tight_layout()

    out_path = Path(__file__).resolve().parent / "risk_levels.png"
    plt.savefig(out_path, dpi=150)
    print(f"✅ 已保存图像到: {out_path}")

    plt.show()


if __name__ == "__main__":
    main()