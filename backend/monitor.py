# backend/monitor.py

import os
import time
import json
from typing import Dict, Any, List, Optional

from dotenv import load_dotenv
from web3 import Web3

from config import load_risk_monitor_contract
from db import MonitorDatabase
from chain_data import fetch_recent_swaps
from whale_cex import fetch_whale_metrics, fetch_cex_net_inflow, estimate_pool_liquidity

load_dotenv()

# ----------------------------------------------------------------------
# 1. 监控 & 风险配置（可按需要微调）
# ----------------------------------------------------------------------

RISK_CONFIG: Dict[str, Any] = {
    "poll_interval": 60,
    "blocks_back": 2000,

    "min_update_interval_sec": 5 * 60,
    "min_stable_rounds_for_update": 2,

    # 这些还是保留，用于“历史不足时”的 fallback 静态打分
    "dex": {
        "baseline_ratio": 0.01,
        "score_thresholds": [1, 2, 5],
        "score_values": [10, 20, 30],
        "extra_trades_threshold": 200,
        "extra_trades_score": 10,
        "max_score": 40,
    },
    "whale": {
        "ratio_thresholds": [0.001, 0.01, 0.03],
        "score_values": [10, 20, 30],
        "extra_whales_threshold": 3,
        "extra_whales_score": 5,
        "max_score": 35,
    },
    "cex": {
        "ratio_thresholds": [0.0, 0.005, 0.02],
        "score_values": [0, 10, 20, 30],
        "max_score": 30,
    },
    "level_thresholds": [20, 40, 70],
}

SCRIPT_DIR = os.path.dirname(__file__)
MARKETS_PATH = os.path.join(SCRIPT_DIR, "markets.json")


def load_markets() -> List[Dict[str, Any]]:
    with open(MARKETS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_default_dex_market(markets: List[Dict[str, Any]]) -> Dict[str, Any]:
    for m in markets:
        if m.get("type") == "dex_pool" and m.get("network", "mainnet") == "mainnet":
            return m
    for m in markets:
        if m.get("type") == "dex_pool":
            return m
    raise RuntimeError("markets.json 中没有 type == 'dex_pool' 的市场配置，请先配置一个 DEX 池子。")


def calc_market_id(label: str) -> bytes:
    return Web3.keccak(text=label)


def is_valid_eth_address(addr: str) -> bool:
    return isinstance(addr, str) and addr.startswith("0x") and len(addr) == 42


def send_update_risk_tx(w3: Web3, contract, level: int, market_id: bytes) -> str:
    private_key = os.getenv("PRIVATE_KEY")
    if not private_key:
        raise RuntimeError("请在 .env 中配置 PRIVATE_KEY（建议用测试网私钥）")

    account = w3.eth.account.from_key(private_key)
    nonce = w3.eth.get_transaction_count(account.address)

    tx = contract.functions.updateRisk(market_id, level).build_transaction(
        {
            "from": account.address,
            "nonce": nonce,
            "gas": 300_000,
            "maxFeePerGas": w3.eth.gas_price,
        }
    )

    signed = w3.eth.account.sign_transaction(tx, private_key)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    print(f"📨 发送 updateRisk 交易: {tx_hash.hex()}")
    return tx_hash.hex()


# ----------------------------------------------------------------------
# 4. 原有静态打分逻辑（保留，用作历史不足时的 fallback）
# ----------------------------------------------------------------------

def score_dex_activity(dex_volume: int, dex_trades: int, pool_liquidity: int) -> int:
    cfg = RISK_CONFIG["dex"]
    baseline_ratio = cfg["baseline_ratio"]

    baseline_volume = pool_liquidity * baseline_ratio if pool_liquidity > 0 else 0
    r = dex_volume / baseline_volume if baseline_volume > 0 else 0

    thresholds = cfg["score_thresholds"]
    values = cfg["score_values"]

    dex_score = 0
    if thresholds[0] <= r < thresholds[1]:
        dex_score = values[0]
    elif thresholds[1] <= r < thresholds[2]:
        dex_score = values[1]
    elif r >= thresholds[2]:
        dex_score = values[2]

    if dex_trades > cfg["extra_trades_threshold"]:
        dex_score += cfg["extra_trades_score"]

    dex_score = min(dex_score, cfg["max_score"])
    return int(dex_score)


def score_whale_pressure(whale_sell_total: int, whale_count_selling: int, pool_liquidity: int) -> int:
    cfg = RISK_CONFIG["whale"]

    if pool_liquidity <= 0:
        return 0

    p = whale_sell_total / pool_liquidity
    thresholds = cfg["ratio_thresholds"]
    values = cfg["score_values"]

    whale_score = 0
    if thresholds[0] <= p < thresholds[1]:
        whale_score = values[0]
    elif thresholds[1] <= p < thresholds[2]:
        whale_score = values[1]
    elif p >= thresholds[2]:
        whale_score = values[2]

    if whale_count_selling >= cfg["extra_whales_threshold"]:
        whale_score += cfg["extra_whales_score"]

    whale_score = min(whale_score, cfg["max_score"])
    return int(whale_score)


def score_cex_inflow(cex_net_inflow: int, pool_liquidity: int) -> int:
    cfg = RISK_CONFIG["cex"]

    if pool_liquidity <= 0 or cex_net_inflow <= 0:
        return 0

    i = cex_net_inflow / pool_liquidity
    thresholds = cfg["ratio_thresholds"]
    values = cfg["score_values"]

    if i <= thresholds[1]:
        cex_score = values[1]
    elif thresholds[1] < i <= thresholds[2]:
        cex_score = values[2]
    else:
        cex_score = values[3]

    cex_score = min(cex_score, cfg["max_score"])
    return int(cex_score)


def compute_risk_level_static(metrics: Dict[str, Any]) -> int:
    dex_volume = metrics["dex_volume"]
    dex_trades = metrics["dex_trades"]
    whale_sell_total = metrics["whale_sell_total"]
    whale_count_selling = metrics["whale_count_selling"]
    cex_net_inflow = metrics["cex_net_inflow"]
    pool_liquidity = metrics["pool_liquidity"] or 1

    dex_score = score_dex_activity(dex_volume, dex_trades, pool_liquidity)
    whale_score = score_whale_pressure(whale_sell_total, whale_count_selling, pool_liquidity)
    cex_score = score_cex_inflow(cex_net_inflow, pool_liquidity)

    score = dex_score + whale_score + cex_score
    print(
        f"📊 综合风险评分(静态): {score} "
        f"(dex={dex_score}, whale={whale_score}, cex={cex_score})"
    )

    t0, t1, t2 = RISK_CONFIG["level_thresholds"]
    if score < t0:
        return 0
    elif score < t1:
        return 1
    elif score < t2:
        return 2
    else:
        return 3


# ----------------------------------------------------------------------
# 4.1 ✅ 动态化方案 1：滚动窗口 + 百分位打分
# ----------------------------------------------------------------------

def percentile_rank(history: List[int], value: int) -> float:
    """
    简单百分位实现：历史中 <= 当前值 的比例 * 100
    history: 历史样本（长度 N）
    value: 当前这一次的值
    """
    if not history:
        return 50.0  # 没历史就视为中位

    sorted_hist = sorted(history)
    count = 0
    for v in sorted_hist:
        if v <= value:
            count += 1
        else:
            break
    return count / len(sorted_hist) * 100.0


def score_from_percentile(p: float) -> int:
    """
    把百分位 p ∈ [0,100] 映射到一个因子得分：
    <60% -> 0
    [60,80) -> 10
    [80,95) -> 20
    >=95 -> 30
    """
    if p < 60:
        return 0
    elif p < 80:
        return 10
    elif p < 95:
        return 20
    else:
        return 30


def compute_risk_level_dynamic(
    db: MonitorDatabase,
    market_id_hex: str,
    metrics: Dict[str, Any],
    history_window: int = 500,
) -> int:
    """
    动态版：根据最近 history_window 条历史数据，计算当前的分位数打分。
    如果历史不足（比如 <30 条），自动 fallback 到静态逻辑。
    """
    history = db.load_recent_metrics(market_id_hex, limit=history_window)

    if len(history) < 30:
        # 历史太少，先用静态逻辑，避免一开始指标抖动太大
        print(f"ℹ️ 历史样本不足 {len(history)} 条，使用静态打分逻辑。")
        return compute_risk_level_static(metrics)

    dex_volume_hist = [h["dex_volume"] for h in history]
    dex_trades_hist = [h["dex_trades"] for h in history]
    whale_sell_hist = [h["whale_sell_total"] for h in history]
    cex_inflow_hist = [h["cex_net_inflow"] for h in history]

    dex_volume = metrics["dex_volume"]
    dex_trades = metrics["dex_trades"]
    whale_sell_total = metrics["whale_sell_total"]
    cex_net_inflow = metrics["cex_net_inflow"]

    # DEX：成交量与笔数各算一个分位，然后平均
    p_dex_vol = percentile_rank(dex_volume_hist, dex_volume)
    p_dex_trd = percentile_rank(dex_trades_hist, dex_trades)
    p_dex = (p_dex_vol + p_dex_trd) / 2.0
    dex_score = score_from_percentile(p_dex)

    # Whale：按卖出总量的分位
    p_whale = percentile_rank(whale_sell_hist, whale_sell_total)
    whale_score = score_from_percentile(p_whale)

    # CEX：按净流入分位
    p_cex = percentile_rank(cex_inflow_hist, cex_net_inflow)
    cex_score = score_from_percentile(p_cex)

    score = dex_score + whale_score + cex_score

    print(
        f"📊 综合风险评分(动态): {score} "
        f"(dex={dex_score} @p≈{p_dex:.1f}%, "
        f"whale={whale_score} @p≈{p_whale:.1f}%, "
        f"cex={cex_score} @p≈{p_cex:.1f}%)"
    )

    # 分数区间 → 风险等级，沿用原来的阈值
    t0, t1, t2 = RISK_CONFIG["level_thresholds"]
    if score < t0:
        return 0
    elif score < t1:
        return 1
    elif score < t2:
        return 2
    else:
        return 3


# ----------------------------------------------------------------------
# 5. 主监控循环（加入动态打分）
# ----------------------------------------------------------------------

def monitor_loop(
    network: str = "sepolia",
    poll_interval: Optional[int] = None,
    blocks_back: Optional[int] = None,
):
    if poll_interval is None:
        poll_interval = RISK_CONFIG["poll_interval"]
    if blocks_back is None:
        blocks_back = RISK_CONFIG["blocks_back"]

    db = MonitorDatabase()
    w3, contract = load_risk_monitor_contract(network)

    markets = load_markets()
    dex_market = get_default_dex_market(markets)

    pair_address: str = dex_market.get("pairAddress") or dex_market.get("address")
    label: str = dex_market["label"]
    market_id: bytes = calc_market_id(label)
    market_id_hex = market_id.hex()

    whales: List[str] = []
    cex_addresses: List[str] = []

    for m in markets:
        if m.get("network", "mainnet") != "mainnet":
            continue

        addr = m.get("address")
        if not is_valid_eth_address(addr or ""):
            continue

        t = m.get("type")

        if t in ("whale_eth", "whale"):
            whales.append(addr)
        if t in ("exchange_eth", "exchange"):
            cex_addresses.append(addr)

    print("🚀 启动监控：")
    print(f"  监控市场 label      : {label}")
    print(f"  DEX 池子地址        : {pair_address}")
    print(f"  marketId(bytes32)   : {market_id_hex}")
    print(f"  巨鲸地址数          : {len(whales)}")
    print(f"  交易所热钱包地址数  : {len(cex_addresses)}")

    last_level: Optional[int] = None
    onchain_level: Optional[int] = None
    last_update_ts: Optional[float] = None
    stable_rounds: int = 0

    while True:
        print("\n=== 开始新一轮监控 ===")
        loop_start = time.time()

        try:
            trades = fetch_recent_swaps(
                pair_address=pair_address,
                blocks_back=blocks_back,
                network="mainnet",
            )
            db.save_trades(trades)

            dex_volume = sum(int(t["amount_in"]) for t in trades)
            dex_trades = len(trades)

            pool_liquidity = estimate_pool_liquidity(pair_address, network="mainnet")

            try:
                if whales:
                    whale_sell_total, whale_count_selling = fetch_whale_metrics(
                        whales=whales,
                        cex_addresses=cex_addresses,
                        pair_address=pair_address,
                        blocks_back=blocks_back,
                        network="mainnet",
                    )
                else:
                    whale_sell_total, whale_count_selling = 0, 0
                    print("ℹ️ 没有配置巨鲸地址，跳过巨鲸抛压统计。")
            except Exception as e:
                print(f"⚠️ 巨鲸统计失败，本轮按 0 处理: {e}")
                whale_sell_total, whale_count_selling = 0, 0

            try:
                if cex_addresses:
                    cex_net_inflow = fetch_cex_net_inflow(
                        cex_addresses=cex_addresses,
                        blocks_back=blocks_back,
                        network="mainnet",
                    )
                else:
                    cex_net_inflow = 0
                    print("ℹ️ 没有配置交易所热钱包地址，CEX 净流入视为 0。")
            except Exception as e:
                print(f"⚠️ CEX 净流入统计失败，本轮按 0 处理: {e}")
                cex_net_inflow = 0

            metrics = {
                "dex_volume": dex_volume,
                "dex_trades": dex_trades,
                "whale_sell_total": whale_sell_total,
                "whale_count_selling": whale_count_selling,
                "cex_net_inflow": cex_net_inflow,
                "pool_liquidity": pool_liquidity,
            }

            print(
                f"DEX 交易笔数: {dex_trades}, "
                f"volume(原始单位): {dex_volume}, "
                f"pool_liquidity(估计): {pool_liquidity}"
            )
            print(
                f"巨鲸卖出总量: {whale_sell_total}, "
                f"卖出巨鲸数: {whale_count_selling}, "
                f"CEX 净流入: {cex_net_inflow}"
            )

            # ✅ 先把本轮指标存进 risk_metrics 表
            db.save_metrics(market_id_hex, metrics)

            # ✅ 使用动态分位打分逻辑（内部会在历史太少时自动 fallback）
            level = compute_risk_level_dynamic(db, market_id_hex, metrics)
            print(f"当前计算风险等级(动态): {level}")

            # 原来的 risk_levels 表照样记录
            db.save_risk_level(
                market_id=market_id_hex,
                level=level,
                source="multi_factor_dynamic",
            )
            print(f"💾 已写入本地数据库 {os.path.basename(db.db_path)}")

            # ===== 防抖逻辑：判断是否需要上链 =====
            if last_level is None:
                stable_rounds = 1
            elif level == last_level:
                stable_rounds += 1
            else:
                stable_rounds = 1

            last_level = level

            now_ts = time.time()
            min_interval = RISK_CONFIG["min_update_interval_sec"]
            min_rounds = RISK_CONFIG["min_stable_rounds_for_update"]

            if onchain_level is None:
                should_update = True
                reason = "首次初始化 onchain_level"
            else:
                enough_rounds = stable_rounds >= min_rounds
                enough_time = (
                    last_update_ts is None
                    or (now_ts - last_update_ts) >= min_interval
                )
                should_update = (level != onchain_level) and enough_rounds and enough_time
                reason = (
                    f"等级变化且已稳定 {stable_rounds} 轮且距离上次更新 "
                    f"{0 if last_update_ts is None else int(now_ts - last_update_ts)} 秒"
                )

            if should_update:
                print(f"⚠️ 符合上链条件（{reason}），调用合约更新...")
                tx_hash = send_update_risk_tx(w3, contract, level, market_id=market_id)
                print(f"✅ 已提交交易，tx = {tx_hash}")
                onchain_level = level
                last_update_ts = now_ts
            else:
                print(
                    f"风险等级暂不更新到链上（onchain_level={onchain_level}, "
                    f"stable_rounds={stable_rounds}, reason={reason})"
                )

        except Exception as e:
            print(f"❌ 本轮监控出现异常，跳过本轮：{e}")

        elapsed = time.time() - loop_start
        sleep_sec = max(1, poll_interval - elapsed)
        print(f"⏳ 等待 {int(sleep_sec)} 秒后进行下一轮...")
        time.sleep(sleep_sec)


if __name__ == "__main__":
    monitor_loop()