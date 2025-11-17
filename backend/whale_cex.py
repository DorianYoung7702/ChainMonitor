# backend/whale_cex.py
import os
from typing import List, Dict, Any, Tuple

import requests
from web3 import Web3

from config import make_web3

# -------------------- Etherscan V2 基础配置 --------------------

ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY", "")
ETHERSCAN_BASE_URL = "https://api.etherscan.io/v2/api"
ETH_MAINNET_CHAIN_ID = "1"  # 只监控以太坊主网


def _etherscan_get_normal_txs(
    address: str,
    start_block: int,
    end_block: int,
    page: int = 1,
    offset: int = 10_000,
    sort: str = "asc",
) -> List[Dict[str, Any]]:
    """
    调用 Etherscan V2 的 normal txlist 接口，只返回 ETH 普通转账（不含 token 转账）。
    """
    if not ETHERSCAN_API_KEY:
        print("⚠️ 未配置 ETHERSCAN_API_KEY，跳过 Etherscan 请求")
        return []

    params = {
        "apikey": ETHERSCAN_API_KEY,
        "chainid": ETH_MAINNET_CHAIN_ID,  # V2 必须带 chainid
        "module": "account",
        "action": "txlist",
        "address": address,
        "startblock": start_block,
        "endblock": end_block,
        "page": page,
        "offset": offset,
        "sort": sort,
    }

    try:
        resp = requests.get(ETHERSCAN_BASE_URL, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        status = data.get("status")
        result = data.get("result")

        # 正常返回
        if status == "1" and isinstance(result, list):
            return result

        # 没有交易：不算错误，直接当 0 处理
        if isinstance(result, str) and "No transactions found" in result:
            return []

        # 其他情况打印一下错误说明
        print(f"⚠️ Etherscan 返回非成功状态: {data}")
        return []
    except Exception as e:
        print(f"⚠️ 请求 Etherscan 失败: {e}")
        return []


# -------------------- DEX 池子流动性估计 --------------------

UNISWAP_V2_PAIR_ABI = [
    {
        "inputs": [],
        "name": "getReserves",
        "outputs": [
            {"internalType": "uint112", "name": "_reserve0", "type": "uint112"},
            {"internalType": "uint112", "name": "_reserve1", "type": "uint112"},
            {"internalType": "uint32", "name": "_blockTimestampLast", "type": "uint32"},
        ],
        "stateMutability": "view",
        "type": "function",
    }
]


def estimate_pool_liquidity(pair_address: str, network: str = "mainnet") -> int:
    """
    用 Uniswap V2 的 getReserves 估算池子流动性（这里简单用 reserve0 + reserve1）。
    对 USDC/WETH 这种池子来说，数值可以作为一个“量级”参考，用来归一化风险。
    """
    w3 = make_web3(network)
    pair = w3.eth.contract(
        address=Web3.to_checksum_address(pair_address),
        abi=UNISWAP_V2_PAIR_ABI,
    )
    reserves = pair.functions.getReserves().call()
    reserve0, reserve1, _ = reserves
    liquidity = int(reserve0) + int(reserve1)

    print(
        f"📡 [DEX] getReserves 返回: reserve0={reserve0}, reserve1={reserve1}, "
        f"估算流动性: {liquidity}"
    )
    return liquidity


# -------------------- 巨鲸行为统计 --------------------


def fetch_whale_metrics(
    whales: List[str],
    cex_addresses: List[str],
    pair_address: str,
    blocks_back: int = 2000,
    network: str = "mainnet",
) -> Tuple[int, int]:
    """
    统计巨鲸在最近 blocks_back 个区块里，往交易所地址转出的 ETH 总量。

    返回:
    - whale_sell_total: 所有巨鲸 -> 交易所 的 ETH 卖出总量 (wei)
    - whale_count_selling: 有卖出行为的巨鲸数量
    """
    if not whales:
        return 0, 0

    w3 = make_web3(network)
    latest = w3.eth.block_number
    from_block = max(0, latest - blocks_back)
    to_block = latest

    print(f"✅ 已连接 {network}, 最新区块: {latest}")
    print(f"📡 [Whale] 统计区块区间 {from_block} ~ {to_block}")

    # 统一小写用于比较
    cex_lower = {addr.lower() for addr in cex_addresses}
    whale_sell_total = 0
    selling_whales: set[str] = set()

    for whale in whales:
        try:
            whale_checksum = Web3.to_checksum_address(whale)
        except ValueError:
            print(f"⚠️ 非法巨鲸地址，已跳过: {whale}")
            continue

        txs = _etherscan_get_normal_txs(
            address=whale_checksum,
            start_block=from_block,
            end_block=to_block,
        )

        # 遍历这个巨鲸地址在区间内的所有普通 ETH 转账
        for tx in txs:
            from_addr = (tx.get("from") or "").lower()
            to_addr = (tx.get("to") or "").lower()
            value_wei = int(tx.get("value") or 0)

            # 条件：巨鲸 -> CEX 热钱包，视为“卖压”
            if from_addr == whale_checksum.lower() and to_addr in cex_lower:
                whale_sell_total += value_wei
                selling_whales.add(whale_checksum)

    whale_count_selling = len(selling_whales)
    print(
        f"📡 [Whale] 卖出巨鲸数: {whale_count_selling}, "
        f"卖出总量(Wei): {whale_sell_total}"
    )
    return whale_sell_total, whale_count_selling


# -------------------- 交易所净流入统计 --------------------


def fetch_cex_net_inflow(
    cex_addresses: List[str],
    blocks_back: int = 2000,
    network: str = "mainnet",
) -> int:
    """
    统计一组 CEX 热钱包地址，在最近 blocks_back 区块里的 ETH 净流入量 (wei)。

    净流入 = 其它地址 -> CEX 的 ETH 总和 - CEX -> 其它地址 的 ETH 总和
    """
    if not cex_addresses:
        return 0

    w3 = make_web3(network)
    latest = w3.eth.block_number
    from_block = max(0, latest - blocks_back)
    to_block = latest

    print(f"✅ 已连接 {network}, 最新区块: {latest}")
    print(f"📡 [CEX] 统计区块区间 {from_block} ~ {to_block}")

    net_inflow = 0

    for cex in cex_addresses:
        try:
            cex_checksum = Web3.to_checksum_address(cex)
        except ValueError:
            print(f"⚠️ 非法交易所地址，已跳过: {cex}")
            continue

        txs = _etherscan_get_normal_txs(
            address=cex_checksum,
            start_block=from_block,
            end_block=to_block,
        )

        for tx in txs:
            from_addr = (tx.get("from") or "").lower()
            to_addr = (tx.get("to") or "").lower()
            value_wei = int(tx.get("value") or 0)

            # inflow: 其它地址 -> CEX
            if to_addr == cex_checksum.lower() and from_addr != cex_checksum.lower():
                net_inflow += value_wei
            # outflow: CEX -> 其它地址
            elif from_addr == cex_checksum.lower() and to_addr != cex_checksum.lower():
                net_inflow -= value_wei

    print(f"📡 [CEX] 统计得到净流入(Wei): {net_inflow}")
    return net_inflow