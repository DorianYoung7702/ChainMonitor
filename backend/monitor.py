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
    # 如果没有显式传参，就用这里的默认值
    "poll_interval": 60,          # 每轮监控间隔秒数
    "blocks_back": 2000,          # 回溯多少区块计算统计值（近似 10~15 分钟）

    # 防抖：避免频繁上链
    "min_update_interval_sec": 5 * 60,   # 连续两次上链至少间隔 5 分钟
    "min_stable_rounds_for_update": 2,   # 风险等级需要连续 N 轮不变，才认为“稳定到了新水平”

    # A. DEX 活跃度打分
    "dex": {
        # 用池子总流动性的百分比做基准交易量
        "baseline_ratio": 0.01,          # 1% 池子流动性视为“正常”交易量
        # r = dex_volume / (pool_liquidity * baseline_ratio)
        # 按 r 取分
        "score_thresholds": [1, 2, 5],   # [1,2) -> 10; [2,5) -> 20; >=5 -> 30
        "score_values": [10, 20, 30],
        "extra_trades_threshold": 200,   # 交易笔数 > 200 再加 10 分
        "extra_trades_score": 10,
        "max_score": 40,
    },

    # B. 巨鲸抛压打分
    "whale": {
        # p = whale_sell_total / pool_liquidity
        "ratio_thresholds": [0.001, 0.01, 0.03],  # 0.1%、1%、3% 流动性
        "score_values": [10, 20, 30],
        "extra_whales_threshold": 3,      # 同时卖出的巨鲸地址数 ≥ 3 再加 5 分
        "extra_whales_score": 5,
        "max_score": 35,
    },

    # C. CEX 净流入打分
    "cex": {
        # i = cex_net_inflow / pool_liquidity
        # 区间：(0, 0.5%]、(0.5%, 2%]、>2%
        "ratio_thresholds": [0.0, 0.005, 0.02],
        "score_values": [0, 10, 20, 30],  # 对应三个区间再加一个“>最大阈值”的分数
        "max_score": 30,
    },

    # 综合得分 -> 风险等级 (0~3)
    # score < 20 -> 0(低); <40 -> 1(中); <70 -> 2(高); >=70 -> 3(极高)
    "level_thresholds": [20, 40, 70],
}


# ----------------------------------------------------------------------
# 2. 读取 markets.json 配置 & 辅助函数
# ----------------------------------------------------------------------

SCRIPT_DIR = os.path.dirname(__file__)
MARKETS_PATH = os.path.join(SCRIPT_DIR, "markets.json")


def load_markets() -> List[Dict[str, Any]]:
    with open(MARKETS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_default_dex_market(markets: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    优先选择 Ethereum 主网的 DEX 池子：
    type == "dex_pool" 且 network == "mainnet"
    如果没有 network 字段，就退化为第一个 dex_pool
    """
    for m in markets:
        if m.get("type") == "dex_pool" and m.get("network", "mainnet") == "mainnet":
            return m
    for m in markets:
        if m.get("type") == "dex_pool":
            return m
    raise RuntimeError("markets.json 中没有 type == 'dex_pool' 的市场配置，请先配置一个 DEX 池子。")


def calc_market_id(label: str) -> bytes:
    """和部署脚本保持一致：keccak(label)"""
    return Web3.keccak(text=label)


def is_valid_eth_address(addr: str) -> bool:
    """简单过滤掉占位符，确保是 0x 开头的 42 位地址"""
    return isinstance(addr, str) and addr.startswith("0x") and len(addr) == 42


# ----------------------------------------------------------------------
# 3. 发送合约交易
# ----------------------------------------------------------------------

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
# 4. 风险评分逻辑：整合 交易对 + 巨鲸 + 交易所
# ----------------------------------------------------------------------

def score_dex_activity(dex_volume: int, dex_trades: int, pool_liquidity: int) -> int:
    cfg = RISK_CONFIG["dex"]
    baseline_ratio = cfg["baseline_ratio"]

    baseline_volume = pool_liquidity * baseline_ratio if pool_liquidity > 0 else 0
    r = dex_volume / baseline_volume if baseline_volume > 0 else 0

    thresholds = cfg["score_thresholds"]
    values = cfg["score_values"]

    dex_score = 0
    # r < thresholds[0] -> 0 分
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
    values = cfg["score_values"]  # 长度为 4: 三个区间 + “大于最大阈值”

    if i <= thresholds[1]:
        cex_score = values[1]
    elif thresholds[1] < i <= thresholds[2]:
        cex_score = values[2]
    else:
        cex_score = values[3]

    cex_score = min(cex_score, cfg["max_score"])
    return int(cex_score)


def compute_risk_level(metrics: Dict[str, Any]) -> int:
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
    dex_volume = metrics["dex_volume"]
    dex_trades = metrics["dex_trades"]
    whale_sell_total = metrics["whale_sell_total"]
    whale_count_selling = metrics["whale_count_selling"]
    cex_net_inflow = metrics["cex_net_inflow"]
    pool_liquidity = metrics["pool_liquidity"] or 1  # 避免除以 0

    dex_score = score_dex_activity(dex_volume, dex_trades, pool_liquidity)
    whale_score = score_whale_pressure(whale_sell_total, whale_count_selling, pool_liquidity)
    cex_score = score_cex_inflow(cex_net_inflow, pool_liquidity)

    score = dex_score + whale_score + cex_score
    print(
        f"📊 综合风险评分: {score} "
        f"(dex={dex_score}, whale={whale_score}, cex={cex_score})"
    )

    # 映射到 0~3 风险等级
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
# 5. 主监控循环（加入防抖 & 容错）
# ----------------------------------------------------------------------

def monitor_loop(
    network: str = "sepolia",
    poll_interval: Optional[int] = None,
    blocks_back: Optional[int] = None,
):
    # 如果没有显式传入，就用配置里的默认值
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

    # ===== 从 markets.json 中整理巨鲸地址 & 交易所地址列表 =====
    whales: List[str] = []
    cex_addresses: List[str] = []

    for m in markets:
        # 只看 Ethereum 主网
        if m.get("network", "mainnet") != "mainnet":
            continue

        addr = m.get("address")
        if not is_valid_eth_address(addr or ""):
            continue

        t = m.get("type")

        # ETH 巨鲸：whale_eth / whale
        if t in ("whale_eth", "whale"):
            whales.append(addr)

        # 交易所热钱包：exchange_eth / exchange
        if t in ("exchange_eth", "exchange"):
            cex_addresses.append(addr)

    print("🚀 启动监控：")
    print(f"  监控市场 label      : {label}")
    print(f"  DEX 池子地址        : {pair_address}")
    print(f"  marketId(bytes32)   : {market_id.hex()}")
    print(f"  巨鲸地址数          : {len(whales)}")
    print(f"  交易所热钱包地址数  : {len(cex_addresses)}")

    # 用于防止频繁上链的状态变量
    last_level: Optional[int] = None          # 上一轮计算出来的本地风险等级
    onchain_level: Optional[int] = None       # 认为当前合约里记录的风险等级
    last_update_ts: Optional[float] = None    # 最近一次上链更新时间
    stable_rounds: int = 0                    # 当前等级已连续出现多少轮

    while True:
        print("\n=== 开始新一轮监控 ===")
        loop_start = time.time()

        try:
            # 1) DEX 交易数据（主网真实数据）
            trades = fetch_recent_swaps(
                pair_address=pair_address,
                blocks_back=blocks_back,
                network="mainnet",
            )
            db.save_trades(trades)

            dex_volume = sum(int(t["amount_in"]) for t in trades)
            dex_trades = len(trades)

            # 2) 池子流动性估计（主网）
            pool_liquidity = estimate_pool_liquidity(pair_address, network="mainnet")

            # 3) 巨鲸行为（基于 ETH 转账 + 池子）
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

            # 4) 交易所净流入（只统计 ETH 行为）
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

            level = compute_risk_level(metrics)
            print(f"当前计算风险等级: {level}")

            # 存到本地数据库
            db.save_risk_level(
                market_id=market_id.hex(),
                level=level,
                source="multi_factor",  # 标记来源
            )

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
                # 程序刚启动：第一次直接上链，初始化状态
                should_update = True
                reason = "首次初始化 onchain_level"
            else:
                # 只有本地等级与链上记录不一致时才考虑更新
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
            # 整轮兜底，避免程序直接崩掉
            print(f"❌ 本轮监控出现异常，跳过本轮：{e}")

        # 控制轮询间隔（考虑到本轮耗时）
        elapsed = time.time() - loop_start
        sleep_sec = max(1, poll_interval - elapsed)
        print(f"⏳ 等待 {int(sleep_sec)} 秒后进行下一轮...")
        time.sleep(sleep_sec)


if __name__ == "__main__":
    monitor_loop()