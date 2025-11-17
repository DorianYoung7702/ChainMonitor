# backend/monitor.py

import os
import time
import json
from typing import Dict, Any, List, Tuple

from dotenv import load_dotenv
from web3 import Web3

from config import load_risk_monitor_contract
from db import MonitorDatabase
from chain_data import fetch_recent_swaps
from whale_cex import fetch_whale_metrics, fetch_cex_net_inflow, estimate_pool_liquidity

load_dotenv()

# ----------------------------------------------------------------------
# 读取 markets.json 配置
# ----------------------------------------------------------------------


SCRIPT_DIR = os.path.dirname(__file__)
MARKETS_PATH = os.path.join(SCRIPT_DIR, "markets.json")


def load_markets() -> List[Dict[str, Any]]:
    with open(MARKETS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_default_dex_market(markets: List[Dict[str, Any]]) -> Dict[str, Any]:
    for m in markets:
        if m.get("type") == "dex_pool":
            return m
    raise RuntimeError("markets.json 中没有 type == 'dex_pool' 的市场配置，请先配置一个 DEX 池子。")


def calc_market_id(label: str) -> bytes:
    """和部署脚本保持一致：keccak(label)"""
    return Web3.keccak(text=label)


# ----------------------------------------------------------------------
# 发送合约交易
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
# 风险评分逻辑：整合 交易对 + 巨鲸 + 交易所
# ----------------------------------------------------------------------


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

    # ===== A. DEX 活跃度得分 (0~40) =====
    # 先用一个简单经验值：池子 1% 流动性视为“正常”交易量
    baseline_volume = pool_liquidity * 0.01
    r = dex_volume / baseline_volume if baseline_volume > 0 else 0

    dex_score = 0
    if 1 <= r < 2:
        dex_score = 10
    elif 2 <= r < 5:
        dex_score = 20
    elif r >= 5:
        dex_score = 30

    if dex_trades > 200:
        dex_score += 10

    # ===== B. 巨鲸抛压得分 (0~35) =====
    p = whale_sell_total / pool_liquidity

    whale_score = 0
    if 0.001 <= p < 0.01:
        whale_score = 10
    elif 0.01 <= p < 0.03:
        whale_score = 20
    elif p >= 0.03:
        whale_score = 30

    if whale_count_selling >= 3:
        whale_score += 5

    # ===== C. CEX 净流入得分 (0~30) =====
    cex_score = 0
    if 0 < cex_net_inflow < 0.005 * pool_liquidity:
        cex_score = 10
    elif 0.005 * pool_liquidity <= cex_net_inflow < 0.02 * pool_liquidity:
        cex_score = 20
    elif cex_net_inflow >= 0.02 * pool_liquidity:
        cex_score = 30

    score = dex_score + whale_score + cex_score
    print(
        f"📊 综合风险评分: {score} "
        f"(dex={dex_score}, whale={whale_score}, cex={cex_score})"
    )

    # 映射到 0~3 风险等级
    if score < 20:
        return 0
    elif score < 40:
        return 1
    elif score < 70:
        return 2
    else:
        return 3


# ----------------------------------------------------------------------
# 主监控循环
# ----------------------------------------------------------------------


def monitor_loop(
    network: str = "sepolia",
    poll_interval: int = 60,
    blocks_back: int = 2000,
):
    db = MonitorDatabase()
    w3, contract = load_risk_monitor_contract(network)

    markets = load_markets()
    dex_market = get_default_dex_market(markets)

    pair_address: str = dex_market["pairAddress"]
    label: str = dex_market["label"]
    market_id: bytes = calc_market_id(label)

    # 从 markets.json 中整理巨鲸地址 & 交易所地址列表
    whales: List[str] = [m["address"] for m in markets if m.get("type") == "whale"]
    cex_addresses: List[str] = [m["address"] for m in markets if m.get("type") == "exchange"]

    print("🚀 启动监控：")
    print(f"  监控市场 label      : {label}")
    print(f"  DEX 池子地址        : {pair_address}")
    print(f"  marketId(bytes32)   : {market_id.hex()}")
    print(f"  巨鲸地址数          : {len(whales)}")
    print(f"  交易所热钱包地址数  : {len(cex_addresses)}")

    last_level: int | None = None

    while True:
        print("\n=== 开始新一轮监控 ===")

        # 1) DEX 交易数据
        trades = fetch_recent_swaps(
            pair_address=pair_address,
            blocks_back=blocks_back,
            network="mainnet",
        )
        db.save_trades(trades)

        dex_volume = sum(int(t["amount_in"]) for t in trades)
        dex_trades = len(trades)

        # 2) 池子流动性估计
        pool_liquidity = estimate_pool_liquidity(pair_address, network="mainnet")

        # 3) 巨鲸行为
        whale_sell_total, whale_count_selling = fetch_whale_metrics(
            whales=whales,
            cex_addresses=cex_addresses,
            blocks_back=blocks_back,
            network="mainnet",
        )

        # 4) 交易所净流入
        cex_net_inflow = fetch_cex_net_inflow(
            cex_addresses=cex_addresses,
            blocks_back=blocks_back,
            network="mainnet",
        )

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

        # 如果风险等级变化，就调用合约更新
        if last_level is None or level != last_level:
            print(f"⚠️ 风险等级从 {last_level} 变为 {level}，调用合约更新...")
            send_update_risk_tx(w3, contract, level, market_id=market_id)
            last_level = level
        else:
            print("风险等级无变化，不调用合约")

        print(f"⏳ 等待 {poll_interval} 秒后进行下一轮...")
        time.sleep(poll_interval)


if __name__ == "__main__":
    monitor_loop()