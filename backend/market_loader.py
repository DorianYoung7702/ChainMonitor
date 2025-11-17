"""
market_loader.py

负责从 backend/markets.json 中加载监控对象：
- DEX 池子（type = "dex_pool"）
- ETH 巨鲸地址（type = "whale_eth" 或 "whale"）
- 交易所热钱包（type = "exchange_eth" 或 "exchange"）
"""

import json
from pathlib import Path
from typing import List, Dict, Any


MARKETS_PATH = Path(__file__).parent / "markets.json"


def load_markets() -> List[Dict[str, Any]]:
    if not MARKETS_PATH.exists():
        return []
    with MARKETS_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def get_mainnet_dex_pool() -> Dict[str, Any]:
    """返回一个主网 DEX 池子配置（目前你只有 UNISWAP_USDC_WETH）"""
    markets = load_markets()
    for m in markets:
        if m.get("type") == "dex_pool" and m.get("network", "mainnet") == "mainnet":
            return m
    raise RuntimeError("markets.json 中没有找到 type=dex_pool, network=mainnet 的配置")


def get_mainnet_eth_whales() -> List[str]:
    """返回所有主网 ETH 巨鲸地址（自动收集 + 手工配置）"""
    markets = load_markets()
    addrs = []
    for m in markets:
        if m.get("network", "mainnet") != "mainnet":
            continue
        if m.get("type") in ("whale_eth", "whale"):
            addr = m.get("address")
            if addr:
                addrs.append(addr)
    return addrs


def get_mainnet_cex_hot_wallets() -> List[str]:
    """返回所有主网 CEX 热钱包地址"""
    markets = load_markets()
    addrs = []
    for m in markets:
        if m.get("network", "mainnet") != "mainnet":
            continue
        if m.get("type") in ("exchange_eth", "exchange"):
            addr = m.get("address")
            if addr:
                addrs.append(addr)
    return addrs
