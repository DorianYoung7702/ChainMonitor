# backend/whale_cex.py

"""
巨鲸行为 & 交易所热钱包行为 的真实数据实现：
- 使用 Etherscan API 统计指定地址在最近区块区间内的转账
- 使用本地节点 + Uniswap V2 Pair 合约的 getReserves() 估算池子流动性
"""

import os
from typing import Tuple, List, Dict, Any

import requests
from web3 import Web3

from config import make_web3

ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY")


# ----------------------------------------------------------------------
#  Etherscan 帮助函数
# ----------------------------------------------------------------------

def _etherscan_base_url(network: str) -> str:
    """
    根据网络返回对应的 Etherscan API 域名。
    这里只用到了 mainnet / sepolia，必要时你可以继续扩展。
    """
    network = network.lower()
    if network in ("mainnet", "ethereum"):
        return "https://api.etherscan.io/api"
    if network in ("sepolia", "sepolia-testnet"):
        return "https://api-sepolia.etherscan.io/api"
    # 默认走 mainnet
    return "https://api.etherscan.io/api"


def _etherscan_get(params: Dict[str, Any], network: str) -> List[Dict[str, Any]]:
    """
    调用 Etherscan account/txlist 接口，返回 result 数组。
    """
    if not ETHERSCAN_API_KEY:
        print("⚠️ ETHERSCAN_API_KEY 未配置，返回空结果。")
        return []

    base_url = _etherscan_base_url(network)
    query = {
        "apikey": ETHERSCAN_API_KEY,
        **params,
    }
    try:
        resp = requests.get(base_url, params=query, timeout=10)
        data = resp.json()
    except Exception as e:
        print(f"❌ 调用 Etherscan 失败: {e}")
        return []

    if data.get("status") != "1":
        # status=0 可能表示“没有交易”，也可能是错误；这里统一打印一下
        print(f"⚠️ Etherscan 返回非成功状态: {data}")
        return []

    return data.get("result", [])


def _fetch_normal_txs_in_range(
    address: str,
    start_block: int,
    end_block: int,
    network: str,
) -> List[Dict[str, Any]]:
    """
    使用 account/txlist 获取某地址在指定区块范围内的 ETH 普通交易。
    只拿最近一页（offset=1000）已经够你的监控使用。
    """
    address = Web3.to_checksum_address(address)
    params = {
        "module": "account",
        "action": "txlist",
        "address": address,
        "startblock": start_block,
        "endblock": end_block,
        "page": 1,
        "offset": 1000,
        "sort": "desc",
    }
    return _etherscan_get(params, network)


# ----------------------------------------------------------------------
#  巨鲸 & 交易所指标
# ----------------------------------------------------------------------

def fetch_whale_metrics(
    whales: List[str],
    cex_addresses: List[str],
    pair_address: str,
    blocks_back: int = 2000,
    network: str = "mainnet",
) -> Tuple[int, int]:
    """
    统计最近 blocks_back 个区块里：
    - 巨鲸地址向 CEX 热钱包 + Uniswap 池子地址 发送的 ETH 数量（视为“卖出/充值”）
    - 有过“卖出”行为的巨鲸个数

    返回:
        whale_sell_total: int  以 Wei 为单位的总卖出量
        whale_count_selling: int  有卖出行为的巨鲸地址个数
    """
    if not whales:
        return 0, 0

    w3 = make_web3(network)
    latest = w3.eth.block_number
    start_block = max(0, latest - blocks_back)

    cex_set = {addr.lower() for addr in cex_addresses}
    # 把 DEX pair 地址也视作“卖出目标”
    cex_set.add(pair_address.lower())

    whale_sell_total = 0
    whale_count_selling = 0

    print(f"📡 [Whale] 统计区块区间 {start_block} ~ {latest}")

    for whale in whales:
        whale = Web3.to_checksum_address(whale)
        txs = _fetch_normal_txs_in_range(
            address=whale,
            start_block=start_block,
            end_block=latest,
            network=network,
        )

        this_whale_sell = 0
        for tx in txs:
            # from == whale, to == CEX or DEX 池子，视为“卖出/充值”
            if tx.get("from", "").lower() == whale.lower() and tx.get("to", "").lower() in cex_set:
                # value 是字符串形式的 Wei
                value_wei = int(tx.get("value", "0"))
                this_whale_sell += value_wei

        if this_whale_sell > 0:
            whale_count_selling += 1
            whale_sell_total += this_whale_sell

    print(
        f"📡 [Whale] 卖出巨鲸数: {whale_count_selling}, "
        f"卖出总量(Wei): {whale_sell_total}"
    )
    return whale_sell_total, whale_count_selling


def fetch_cex_net_inflow(
    cex_addresses: List[str],
    blocks_back: int = 2000,
    network: str = "mainnet",
) -> int:
    """
    统计最近 blocks_back 个区块里，多个 CEX 热钱包地址的 **ETH 净流入量**：
        net_inflow = 总流入 - 总流出  （Wei 单位）

    - inflow: from != cex, to == cex
    - outflow: from == cex, to != cex
    """
    if not cex_addresses:
        return 0

    w3 = make_web3(network)
    latest = w3.eth.block_number
    start_block = max(0, latest - blocks_back)

    total_in = 0
    total_out = 0

    print(f"📡 [CEX] 统计区块区间 {start_block} ~ {latest}")

    for cex in cex_addresses:
        cex = Web3.to_checksum_address(cex)
        txs = _fetch_normal_txs_in_range(
            address=cex,
            start_block=start_block,
            end_block=latest,
            network=network,
        )

        for tx in txs:
            frm = tx.get("from", "").lower()
            to = tx.get("to", "").lower()
            value_wei = int(tx.get("value", "0"))

            if to == cex.lower() and frm != cex.lower():
                total_in += value_wei
            elif frm == cex.lower() and to != cex.lower():
                total_out += value_wei

    net_inflow = total_in - total_out
    print(
        f"📡 [CEX] 总流入(Wei): {total_in}, 总流出(Wei): {total_out}, 净流入(Wei): {net_inflow}"
    )
    return net_inflow


# ----------------------------------------------------------------------
#  Uniswap V2 池子流动性估算
# ----------------------------------------------------------------------

UNISWAP_V2_PAIR_RESERVES_ABI = [
    {
        "inputs": [],
        "name": "getReserves",
        "outputs": [
            {"internalType": "uint112", "name": "reserve0", "type": "uint112"},
            {"internalType": "uint112", "name": "reserve1", "type": "uint112"},
            {"internalType": "uint32", "name": "blockTimestampLast", "type": "uint32"},
        ],
        "stateMutability": "view",
        "type": "function",
    }
]


def estimate_pool_liquidity(pair_address: str, network: str = "mainnet") -> int:
    """
    使用 Uniswap V2 Pair 合约的 getReserves() 估算池子流动性。
    - 直接把 reserve0 + reserve1 作为一个“规模量级”的代理即可
    - 返回值是原始 token 数量之和（没有做 USD 换算）

    如果调用失败，会返回一个默认值 10**24，保证不会因为 0 导致评分出错。
    """
    try:
        w3 = make_web3(network)
        pair = w3.eth.contract(
            address=Web3.to_checksum_address(pair_address),
            abi=UNISWAP_V2_PAIR_RESERVES_ABI,
        )
        reserve0, reserve1, _ = pair.functions.getReserves().call()
        liquidity = int(reserve0) + int(reserve1)
        print(
            f"📡 [DEX] getReserves 返回: reserve0={reserve0}, "
            f"reserve1={reserve1}, 估算流动性: {liquidity}"
        )
        if liquidity <= 0:
            return 10**24
        return liquidity
    except Exception as e:
        print(f"⚠️ 获取 Uniswap 池子流动性失败，使用默认值: {e}")
        return 10**24