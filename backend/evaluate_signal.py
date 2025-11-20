# backend/evaluate_signal.py

import sqlite3
from datetime import datetime, timedelta
from typing import List, Tuple, Dict, Any

from db import MonitorDatabase, DB_PATH


# ============ 1. 价格序列获取（你可以按自己的数据源实现） ============

def fetch_price_series(
    market_id: str,
    start_time: datetime,
    end_time: datetime,
) -> List[Tuple[datetime, float]]:
    """
    返回 [(ts, price), ...]，ts 是 datetime，price 是 float。
    这里先写成占位版本：
      - 实际用的时候，你可以从：
          1) 你自己保存的价格 CSV;
          2) Dune / CEX K 线导出;
          3) 或者后面我们用 Uniswap 池子 reserve 算 mid price。
    """
    # TODO: 实现真实价格数据的获取逻辑
    # 先返回空，表示没数据（脚本里会跳过）
    return []


# ============ 2. 价格序列 → 收益率 / 波动率 / 回撤 ============

def compute_realized_stats(
    prices: List[Tuple[datetime, float]]
) -> Dict[str, float]:
    """
    prices: [(ts, price), ...] 按时间升序
    返回:
      realized_return: (last / first - 1)*100
      realized_vol:    简单用收益率标准差 * sqrt(n) * 100   (示意)
      realized_dd:     最大回撤(%)，负值
    """
    if len(prices) < 2:
        return {
            "realized_return": 0.0,
            "realized_vol": 0.0,
            "realized_drawdown": 0.0,
        }

    prices_sorted = sorted(prices, key=lambda x: x[0])
    ps = [p for _, p in prices_sorted]

    p0 = ps[0]
    p_last = ps[-1]
    realized_return = (p_last / p0 - 1.0) * 100.0

    # 简单收益率序列
    rets = []
    for i in range(1, len(ps)):
        if ps[i-1] > 0:
            rets.append(ps[i] / ps[i-1] - 1.0)
    if len(rets) > 1:
        mean_ret = sum(rets) / len(rets)
        var = sum((r - mean_ret) ** 2 for r in rets) / (len(rets) - 1)
        std = var ** 0.5
        realized_vol = std * (len(rets) ** 0.5) * 100.0
    else:
        realized_vol = 0.0

    # 最大回撤
    max_dd = 0.0
    peak = ps[0]
    for p in ps:
        if p > peak:
            peak = p
        dd = (p / peak - 1.0) * 100.0
        if dd < max_dd:
            max_dd = dd  # 负数
    realized_drawdown = max_dd

    return {
        "realized_return": realized_return,
        "realized_vol": realized_vol,
        "realized_drawdown": realized_drawdown,
    }


# ============ 3. 规则：什么算“坏事件”(bad_event) ============

def label_bad_event(
    stats: Dict[str, float],
    vol_threshold: float = 40.0,   # 比如：1 小时内年化波动率>40% 就算激烈波动
    dd_threshold: float = -3.0,    # 或者：最大回撤<-3%
) -> int:
    """
    返回 1 表示“发生了大波动/大回撤”，0 表示正常。
    这个阈值可以之后根据你想要的敏感度进行调参。
    """
    if stats["realized_vol"] >= vol_threshold:
        return 1
    if stats["realized_drawdown"] <= dd_threshold:
        return 1
    return 0


# ============ 4. 主流程：根据 risk_levels 推出 risk_eval ============

def backfill_eval_for_market(
    db: MonitorDatabase,
    market_id: str,
    window_minutes: int = 60,
):
    """
    对某个 market_id，遍历历史 risk_levels：
      - 对每个快照时间 t，取 t~t+window 的价格
      - 计算真实波动 & 回撤
      - 打 bad_event 标签
      - 写入 risk_eval
    """

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT created_at, level
        FROM risk_levels
        WHERE market_id = ?
        ORDER BY created_at ASC
        """,
        (market_id,),
    )
    rows = cur.fetchall()
    conn.close()

    if not rows:
        print(f"⚠️ risk_levels 中没有 market_id={market_id} 的记录。")
        return

    for created_at_str, level in rows:
        snapshot_time = datetime.fromisoformat(created_at_str)
        end_time = snapshot_time + timedelta(minutes=window_minutes)

        prices = fetch_price_series(market_id, snapshot_time, end_time)
        if len(prices) < 2:
            print(f"ℹ️ {snapshot_time} ~ {end_time} 没有足够价格数据，跳过。")
            continue

        stats = compute_realized_stats(prices)
        bad = label_bad_event(stats)

        row = {
            "snapshot_time": snapshot_time.isoformat(timespec="seconds"),
            "market_id": market_id,
            "risk_level": int(level),
            "realized_window_minutes": window_minutes,
            "realized_return": stats["realized_return"],
            "realized_vol": stats["realized_vol"],
            "realized_drawdown": stats["realized_drawdown"],
            "bad_event": bad,
        }
        db.save_eval_result(row)
        print(
            f"✅ 写入评估: t={row['snapshot_time']}, "
            f"level={level}, ret={stats['realized_return']:.2f}%, "
            f"vol={stats['realized_vol']:.2f}%, dd={stats['realized_drawdown']:.2f}%, "
            f"bad_event={bad}"
        )


# ============ 5. 统计量：混淆矩阵 & 各等级表现 ============

def summarize_performance(
    db: MonitorDatabase,
    market_id: str,
    window_minutes: int = 60,
    high_risk_threshold: int = 2,
):
    """
    输出两个维度的量化反馈：
      1) 不同风险等级 → 平均真实 vol / dd / bad_event 发生率
      2) 把 level>=high_risk_threshold 当“发出警报”，算精确率/召回率
    """
    rows = db.load_eval_results(market_id, window_minutes)
    if not rows:
        print("⚠️ risk_eval 中暂无数据，请先跑 backfill_eval_for_market。")
        return

    # 1) 各等级统计
    buckets: Dict[int, Dict[str, Any]] = {}
    for r in rows:
        lvl = int(r["risk_level"])
        b = buckets.setdefault(
            lvl,
            {
                "n": 0,
                "sum_vol": 0.0,
                "sum_dd": 0.0,
                "sum_ret": 0.0,
                "bad_count": 0,
            },
        )
        b["n"] += 1
        b["sum_vol"] += r["realized_vol"]
        b["sum_dd"] += r["realized_drawdown"]
        b["sum_ret"] += r["realized_return"]
        b["bad_count"] += int(r["bad_event"])

    print("\n=== 按风险等级的实际表现 ===")
    for lvl in sorted(buckets.keys()):
        b = buckets[lvl]
        n = b["n"]
        print(
            f"Level {lvl}: "
            f"样本数={n}, "
            f"平均波动率={b['sum_vol']/n:.2f}%, "
            f"平均最大回撤={b['sum_dd']/n:.2f}%, "
            f"平均收益率={b['sum_ret']/n:.2f}%, "
            f"坏事件发生率={b['bad_count']/n*100:.1f}%"
        )

    # 2) 把 level>=high_risk_threshold 视为“系统发出高风险警报”
    tp = fp = tn = fn = 0
    for r in rows:
        lvl = int(r["risk_level"])
        bad = int(r["bad_event"])
        pred_alert = int(lvl >= high_risk_threshold)
        if pred_alert == 1 and bad == 1:
            tp += 1
        elif pred_alert == 1 and bad == 0:
            fp += 1
        elif pred_alert == 0 and bad == 0:
            tn += 1
        elif pred_alert == 0 and bad == 1:
            fn += 1

    print("\n=== 高风险告警 (level >= %d) 的效果 ===" % high_risk_threshold)
    print(f"TP={tp}, FP={fp}, TN={tn}, FN={fn}")
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    print(f"精确率(Precision) = {precision:.2f}")
    print(f"召回率(Recall)    = {recall:.2f}")


if __name__ == "__main__":
    db = MonitorDatabase(DB_PATH)
    # 这里 market_id_hex 用你 monitor.py 里打印的那个（UNISWAP_USDC_WETH 的 keccak(hex)）
    MARKET_ID_HEX = "0xf8aef9bb697ca70b8d1b632a3f78532b1ad5f66e2643890ce09c75ce7e313c74"

    # 1) 先用历史 risk_levels 回填 eval（例如窗口 60 分钟）
    backfill_eval_for_market(db, MARKET_ID_HEX, window_minutes=60)

    # 2) 再做量化统计
    summarize_performance(db, MARKET_ID_HEX, window_minutes=60, high_risk_threshold=2)