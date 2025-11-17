# backend/collect_eth_whales.py

import os
import json
import time
from collections import defaultdict
from typing import Dict, Any, List, Tuple

from dotenv import load_dotenv
from web3 import Web3

from config import make_web3

SCRIPT_DIR = os.path.dirname(__file__)
MARKETS_PATH = os.path.join(SCRIPT_DIR, "markets.json")

# 可以按需要调：
BLOCKS_BACK = 500          # 之前如果是 2000，会非常慢；先用 500 测试
MIN_TX_VALUE_ETH = 100     # 只看单笔 >= 100 ETH 的大额转账
TOP_N = 10                 # 取前 N 个巨鲸地址写入 markets.json


def load_markets() -> List[Dict[str, Any]]:
    if not os.path.exists(MARKETS_PATH):
        return []
    with open(MARKETS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_markets(markets: List[Dict[str, Any]]):
    with open(MARKETS_PATH, "w", encoding="utf-8") as f:
        json.dump(markets, f, indent=2, ensure_ascii=False)


def is_valid_eth_address(addr: str) -> bool:
    return isinstance(addr, str) and addr.startswith("0x") and len(addr) == 42


def main():
    load_dotenv()
    w3 = make_web3("mainnet")

    latest_block = w3.eth.block_number
    start_block = max(0, latest_block - BLOCKS_BACK)
    print(f"📡 开始扫描主网区块 {start_block} ~ {latest_block}")
    print(f"   只统计单笔转账金额 >= {MIN_TX_VALUE_ETH} ETH 的交易\n")

    min_value_wei = int(MIN_TX_VALUE_ETH * 10**18)

    # 统计每个地址的 ETH 进出总和（这里简单地把 from 和 to 都记进去）
    volumes: Dict[str, int] = defaultdict(int)

    total_blocks = latest_block - start_block + 1

    for idx, block_num in enumerate(range(start_block, latest_block + 1), start=1):
        # 每隔 20 个区块打印一次进度
        if idx == 1 or idx % 20 == 0 or block_num == latest_block:
            print(f"  ⏳ 进度: {idx}/{total_blocks} 区块, 当前区块号: {block_num}")

        try:
            block = w3.eth.get_block(block_num, full_transactions=True)
        except Exception as e:
            print(f"  ⚠️ 获取区块 {block_num} 失败: {e}")
            time.sleep(0.5)
            continue

        for tx in block.transactions:
            value = int(tx["value"])
            if value <= 0 or value < min_value_wei:
                continue

            from_addr = tx["from"]
            to_addr = tx["to"]

            # 只统计合法的 ETH 地址
            if is_valid_eth_address(from_addr):
                volumes[from_addr] += value
            if to_addr is not None and is_valid_eth_address(to_addr):
                volumes[to_addr] += value

    # 按转账总额排序，取前 TOP_N 个地址
    sorted_addrs: List[Tuple[str, int]] = sorted(
        volumes.items(),
        key=lambda x: x[1],
        reverse=True,
    )[:TOP_N]

    print("\n🏁 扫描完成.")
    if not sorted_addrs:
        print("  没有找到满足条件的巨鲸地址，可以尝试：")
        print("  - 降低 MIN_TX_VALUE_ETH（比如 50 ETH）")
        print("  - 或增大 BLOCKS_BACK（比如 1000）")
        return

    print(f"  找到 {len(sorted_addrs)} 个 ETH 巨鲸候选地址:\n")
    for addr, vol in sorted_addrs:
        print(f"    {addr}  总转账量 ≈ {vol / 10**18:.2f} ETH")

    # 读取原有 markets.json，并追加新的 whale_eth 条目
    markets = load_markets()

    # （可选）先把旧的 whale_eth 删掉，避免越来越多：
    markets = [m for m in markets if m.get("type") != "whale_eth"]

    new_entries: List[Dict[str, Any]] = []
    for i, (addr, vol) in enumerate(sorted_addrs, start=1):
        entry = {
            "label": f"WHALE_ETH_{i}",
            "type": "whale_eth",
            "network": "mainnet",
            "address": addr,
            "description": f"Auto-collected ETH whale, ~{vol / 10**18:.1f} ETH in last {BLOCKS_BACK} blocks",
        }
        markets.append(entry)
        new_entries.append(entry)

    save_markets(markets)
    print(f"\n✅ 已写入 {len(new_entries)} 个巨鲸地址到 markets.json")
    print("   类型为 type = 'whale_eth', network = 'mainnet'")


if __name__ == "__main__":
    main()