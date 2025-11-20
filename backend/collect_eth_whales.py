# backend/collect_eth_whales.py
from __future__ import annotations

"""
动态收集 ERC20（默认 WETH）鲸鱼地址，直接写入 markets.json

用法（在 backend 目录下）：
    python collect_eth_whales.py
    python collect_eth_whales.py --token <ERC20地址> --top 20 --blocks 200000

依赖：
    pip install python-dotenv web3
"""

import argparse
import json
import os
import time
from pathlib import Path
from typing import Dict, List, Any, Tuple

from dotenv import load_dotenv
from web3 import Web3

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
MARKETS_PATH = BASE_DIR / "markets.json"

# 默认监控 token：主网 WETH
DEFAULT_WETH = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"

# 读取 mainnet RPC（你已经在 .env 里配了 ETH_RPC_URL，这里一并支持）
MAINNET_RPC = (
    os.getenv("MAINNET_RPC")
    or os.getenv("ETH_RPC_URL")
    or os.getenv("MAINNET_HTTP_URL")
    or os.getenv("ALCHEMY_MAINNET_RPC")
)

if not MAINNET_RPC:
    raise RuntimeError(
        "请在 .env 中配置 MAINNET_RPC / ETH_RPC_URL / MAINNET_HTTP_URL / ALCHEMY_MAINNET_RPC 之一"
    )

w3 = Web3(Web3.HTTPProvider(MAINNET_RPC))
if not w3.is_connected():
    raise RuntimeError("无法连接以太坊主网，请检查 RPC 地址是否正确、网络是否可达")

# ERC20 Transfer 事件 topic0
TRANSFER_TOPIC0 = w3.keccak(text="Transfer(address,address,uint256)").hex()


# -------------------------------------------------------------------
# 工具函数：获取最新区块
# -------------------------------------------------------------------
def get_latest_block() -> int:
    latest = w3.eth.block_number
    print(f"✅ mainnet 最新区块: {latest}")
    return latest


# -------------------------------------------------------------------
# 使用 RPC 扫描 Transfer 日志（自适应缩小区间）
# -------------------------------------------------------------------
def fetch_transfer_logs_via_rpc(
    token: str,
    start_block: int,
    end_block: int,
    initial_step: int = 5000,
    min_step: int = 128,
) -> List[Dict[str, Any]]:
    """
    用 eth_getLogs 按区间扫描 ERC20 Transfer 日志。
    如果某个区间日志数 >10000 导致 -32005，则自动缩小 step 重试。
    """
    token = Web3.to_checksum_address(token)
    logs: List[Dict[str, Any]] = []

    print(
        f"📡 通过 RPC 扫描 Transfer 日志: token={token}, "
        f"blocks=[{start_block}, {end_block}], step={initial_step}"
    )

    step = initial_step
    current = start_block

    while current <= end_block:
        to_block = min(current + step - 1, end_block)

        # 内层循环：如果这一段触发 10000 条限制，就缩小步长重试
        while True:
            print(f"  · 扫描区块区间 [{current}, {to_block}] ... ", end="", flush=True)
            try:
                part = w3.eth.get_logs(
                    {
                        "fromBlock": current,
                        "toBlock": to_block,
                        "address": token,
                        "topics": [TRANSFER_TOPIC0],
                    }
                )
                print(f"ok, 本段日志数={len(part)}")
                logs.extend(part)
                break  # 成功则跳出内层 while，向前推进区间
            except ValueError as e:
                # web3 把 RPC 错误塞在 e.args[0] 里（通常是 dict）
                err_obj = e.args[0] if e.args else {}
                code = None
                msg = str(e)
                if isinstance(err_obj, dict):
                    code = err_obj.get("code")
                    msg = err_obj.get("message", msg)

                print(f"⚠️ get_logs 失败: {err_obj}")

                # 典型：{'code': -32005, 'message': 'query returned more than 10000 results. ...'}
                if code == -32005 or "more than 10000 results" in msg:
                    if step <= min_step:
                        print("  ❌ 步长已缩小到下限仍超过 10000 条，跳过这一小段。")
                        break
                    # 把步长减半，重新计算 to_block 再试
                    step = max(step // 2, min_step)
                    to_block = min(current + step - 1, end_block)
                    print(f"  ↪️ 将步长缩小为 {step} 重新尝试该区间。")
                    continue
                else:
                    # 其他错误（比如 RPC 暂时出问题），这段直接跳过，后面继续
                    print("  ❌ 非 10000 条限制类错误，跳过这一小段。")
                    break

        # 推进到下一个区间
        current = to_block + 1

    print(f"✅ 共收集 Transfer 日志 {len(logs)} 条")
    return logs


# -------------------------------------------------------------------
# 把日志转换为类似 Etherscan tokentx 的结构，便于复用聚合逻辑
# -------------------------------------------------------------------
def logs_to_tx_like(logs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    txs: List[Dict[str, Any]] = []
    for log in logs:
        topics = log.get("topics") or []
        data = log.get("data") or "0x"

        if len(topics) < 3:
            continue

        try:
            # topics[1], topics[2] 为 from / to（indexed address）
            from_addr = "0x" + topics[1].hex()[-40:]
            to_addr = "0x" + topics[2].hex()[-40:]

            # data 为 32 bytes 的 uint256 数量
            if isinstance(data, bytes):
                value = int.from_bytes(data, "big")
            else:
                # 字符串形式 '0x...'
                value = int(data, 16)
        except Exception:
            continue

        txs.append(
            {
                "from": from_addr,
                "to": to_addr,
                "value": str(value),
            }
        )
    return txs


# -------------------------------------------------------------------
# 地址聚合 + topN 选择
# -------------------------------------------------------------------
def aggregate_whales(
    txs: List[Dict[str, Any]],
    min_volume_wei: int | None = None,
) -> Dict[str, Dict[str, Any]]:
    """
    把一批 token 转账交易按地址聚合，按「绝对成交额总和」统计。

    - 每条 tx 的 from / to 都视为候选地址
    - volume = 该地址发送 + 接收的总和（单位 Wei）
    """
    stats: Dict[str, Dict[str, Any]] = {}

    for tx in txs:
        value_str = tx.get("value") or "0"
        try:
            value = int(value_str)
        except Exception:
            continue

        if value <= 0:
            continue

        from_addr = (tx.get("from") or "").lower()
        to_addr = (tx.get("to") or "").lower()

        for addr in (from_addr, to_addr):
            if not addr or addr == "0x0000000000000000000000000000000000000000":
                continue
            s = stats.setdefault(addr, {"volume": 0, "tx_count": 0})
            s["volume"] += value
            s["tx_count"] += 1

    if min_volume_wei is not None:
        stats = {
            a: v for a, v in stats.items()
            if v["volume"] >= min_volume_wei
        }

    print(f"📈 完成地址聚合，候选地址数: {len(stats)}")
    return stats


def pick_top_whales(
    stats: Dict[str, Dict[str, Any]],
    top_n: int = 10,
) -> List[Tuple[str, Dict[str, Any]]]:
    """
    按 volume 排序，取前 top_n 名。
    """
    whales = sorted(
        stats.items(),
        key=lambda kv: kv[1]["volume"],
        reverse=True,
    )[:top_n]
    print("🏆 选出前 {} 名鲸鱼地址:".format(len(whales)))
    for i, (addr, v) in enumerate(whales, start=1):
        print(
            f"  #{i} {addr} | volume={v['volume']} Wei | tx_count={v['tx_count']}"
        )
    return whales


# -------------------------------------------------------------------
# 修改 markets.json：把动态鲸鱼写进去
# -------------------------------------------------------------------
def _load_markets_file(path: Path) -> tuple[list[dict[str, Any]], bool]:
    """
    兼容两种写法：
      1) 直接是数组: [ {...}, {...} ]
      2) 对象带 markets 字段: { "markets": [ ... ] }

    返回: (markets_list, use_object_wrapper)
    """
    if not path.exists():
        raise RuntimeError(f"{path} 不存在，请先创建基础的 markets.json")

    raw = json.loads(path.read_text(encoding="utf-8"))

    if isinstance(raw, list):
        return raw, False
    elif isinstance(raw, dict) and isinstance(raw.get("markets"), list):
        return raw["markets"], True
    else:
        raise RuntimeError("markets.json 格式不支持，期望是数组或 {\"markets\": [...]} 结构")


def _dump_markets_file(
    path: Path,
    markets: list[dict[str, Any]],
    use_object_wrapper: bool,
):
    if use_object_wrapper:
        raw = {"markets": markets}
    else:
        raw = markets

    path.write_text(json.dumps(raw, indent=2), encoding="utf-8")
    print(f"💾 已更新 {path}，当前 markets 总条数: {len(markets)}")


def update_markets_with_whales(
    whales: List[Tuple[str, Dict[str, Any]]],
    token_address: str,
    network: str = "mainnet",
):
    """
    在 markets.json 里：
      1) 删除旧的自动鲸鱼条目（label 以 AUTO_WHALE_ 开头或 meta.source == "collect_eth_whales"）
      2) 追加新的鲸鱼条目
    """
    markets, wrapped = _load_markets_file(MARKETS_PATH)

    # 1) 过滤掉旧的自动鲸鱼
    filtered: list[dict[str, Any]] = []
    for m in markets:
        t = m.get("type")
        label = (m.get("label") or "").upper()
        meta = m.get("meta") or {}

        is_auto = (
            label.startswith("AUTO_WHALE_")
            or (meta.get("source") == "collect_eth_whales")
        )
        if t in ("whale_eth", "whale") and is_auto:
            continue
        filtered.append(m)

    print(
        f"🧹 已清理旧的自动鲸鱼条目 {len(markets) - len(filtered)} 个，"
        f"剩余 {len(filtered)} 条 markets。"
    )

    # 2) 追加新的鲸鱼条目
    ts = int(time.time())
    for idx, (addr, v) in enumerate(whales, start=1):
        filtered.append(
            {
                "label": f"AUTO_WHALE_{idx}",
                "address": addr,
                "type": "whale_eth",
                "network": network,
                "meta": {
                    "source": "collect_eth_whales",
                    "token": token_address,
                    "rank": idx,
                    "volume_wei": str(v["volume"]),
                    "tx_count": int(v["tx_count"]),
                    "timestamp": ts,
                },
            }
        )

    _dump_markets_file(MARKETS_PATH, filtered, wrapped)


# -------------------------------------------------------------------
# main
# -------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="动态收集 ERC20 鲸鱼地址并写入 markets.json")
    parser.add_argument(
        "--token",
        type=str,
        default=DEFAULT_WETH,
        help="要分析的 ERC20 Token 地址，默认主网 WETH",
    )
    parser.add_argument(
        "--blocks",
        type=int,
        default=200_000,
        help="回溯多少区块范围（默认 200k，大约几天到一周，可按需调小，如 50000）",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=10,
        help="选出前多少名鲸鱼地址（默认 10）",
    )
    parser.add_argument(
        "--min-volume-eth",
        type=float,
        default=0.0,
        help="过滤最小累计成交额（ETH），默认不过滤，比如 50 表示只保留成交总额 ≥50 ETH 的地址",
    )

    args = parser.parse_args()

    token = Web3.to_checksum_address(args.token)
    latest = get_latest_block()
    start = max(0, latest - args.blocks)

    # 1. 扫描 Transfer 日志
    raw_logs = fetch_transfer_logs_via_rpc(
        token=token,
        start_block=start,
        end_block=latest,
    )

    # 2. 转成类似 tokentx 的结构，再做地址聚合
    tx_like = logs_to_tx_like(raw_logs)

    min_volume_wei = None
    if args.min_volume_eth and args.min_volume_eth > 0:
        min_volume_wei = int(args.min_volume_eth * 10**18)

    stats = aggregate_whales(tx_like, min_volume_wei=min_volume_wei)
    whales = pick_top_whales(stats, top_n=args.top)

    # 3. 直接写回 markets.json
    update_markets_with_whales(whales, token_address=token, network="mainnet")


if __name__ == "__main__":
    main()