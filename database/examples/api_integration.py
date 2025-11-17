#!/usr/bin/env python3
"""
API集成示例
展示如何在ChainMonitor后端中使用数据库模块
"""

import sys
import os

# 添加数据库utils到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.db_helper import DatabaseHelper
from datetime import datetime
import json

class RiskMonitorAPI:
    """风险监控API示例"""

    def __init__(self):
        self.db = DatabaseHelper()

    def get_dashboard_data(self):
        """
        获取仪表盘数据
        对应前端Dashboard页面
        """
        with self.db as db:
            # 1. 获取市场概览
            markets = db.get_market_overview()

            # 2. 获取每个市场的最新因子
            market_data = []
            for market in markets:
                market_id = market['market_id']

                # 获取因子
                factors = db.get_latest_factors(market_id)

                market_data.append({
                    'marketId': market_id,
                    'label': market['label'],
                    'currentRiskLevel': market['current_risk_level'],
                    'riskScore': float(market['current_risk_score']) if market['current_risk_score'] else 0,
                    'lastUpdated': market['last_updated'].timestamp() if market['last_updated'] else 0,
                    'factors': {
                        'dex': {
                            'score': float(factors['dex_score']) if factors else 0,
                            'maxScore': 40,
                            'volumeRatio': float(factors['dex_volume_ratio']) if factors else 0,
                            'txCount': factors['dex_tx_count'] if factors else 0,
                            'liquidity': float(factors['dex_liquidity']) if factors else 0,
                        },
                        'whale': {
                            'score': float(factors['whale_score']) if factors else 0,
                            'maxScore': 35,
                            'sellVolume': float(factors['whale_sell_volume']) if factors else 0,
                            'activeWhales': factors['whale_active_count'] if factors else 0,
                            'sellRatio': float(factors['whale_sell_ratio']) if factors else 0,
                        },
                        'cex': {
                            'score': float(factors['cex_score']) if factors else 0,
                            'maxScore': 30,
                            'totalInflow': float(factors['cex_total_inflow']) if factors else 0,
                            'totalOutflow': float(factors['cex_total_outflow']) if factors else 0,
                            'netInflow': float(factors['cex_net_inflow']) if factors else 0,
                            'netInflowRatio': float(factors['cex_net_inflow_ratio']) if factors else 0,
                        }
                    }
                })

            # 3. 获取告警
            alerts = db.get_alerts(limit=10)

            return {
                'markets': market_data,
                'alerts': [{
                    'id': str(alert['id']),
                    'timestamp': alert['created_at'].timestamp(),
                    'marketId': alert['market_id'],
                    'riskLevel': alert['new_level'],
                    'previousLevel': alert['previous_level'],
                    'message': alert['message'],
                    'severity': alert['severity']
                } for alert in alerts]
            }

    def get_market_detail(self, market_id):
        """
        获取市场详情
        对应前端MarketDetail页面
        """
        with self.db as db:
            # 1. 获取最新风险
            latest_risk = db.get_latest_risk(market_id)

            # 2. 获取最新因子
            factors = db.get_latest_factors(market_id)

            # 3. 获取风险历史（24小时）
            risk_history = db.get_risk_history(market_id, hours=24)

            # 4. 获取最近交易
            transactions = db.get_recent_transactions(market_id, limit=20)

            return {
                'marketId': market_id,
                'currentRisk': {
                    'level': latest_risk['risk_level'] if latest_risk else 0,
                    'score': float(latest_risk['risk_score']) if latest_risk else 0,
                    'blockNumber': latest_risk['block_number'] if latest_risk else 0,
                    'lastUpdated': latest_risk['created_at'].timestamp() if latest_risk else 0,
                },
                'factors': {
                    'dex': {
                        'score': float(factors['dex_score']) if factors else 0,
                        'maxScore': 40,
                        'volumeRatio': float(factors['dex_volume_ratio']) if factors else 0,
                        'txCount': factors['dex_tx_count'] if factors else 0,
                        'liquidity': float(factors['dex_liquidity']) if factors else 0,
                    },
                    'whale': {
                        'score': float(factors['whale_score']) if factors else 0,
                        'maxScore': 35,
                        'sellVolume': float(factors['whale_sell_volume']) if factors else 0,
                        'activeWhales': factors['whale_active_count'] if factors else 0,
                        'sellRatio': float(factors['whale_sell_ratio']) if factors else 0,
                    },
                    'cex': {
                        'score': float(factors['cex_score']) if factors else 0,
                        'maxScore': 30,
                        'totalInflow': float(factors['cex_total_inflow']) if factors else 0,
                        'totalOutflow': float(factors['cex_total_outflow']) if factors else 0,
                        'netInflow': float(factors['cex_net_inflow']) if factors else 0,
                        'netInflowRatio': float(factors['cex_net_inflow_ratio']) if factors else 0,
                    }
                },
                'history': [{
                    'timestamp': int(risk['created_at'].timestamp()),
                    'value': float(risk['risk_score'])
                } for risk in risk_history],
                'transactions': [{
                    'timestamp': int(tx['timestamp']),
                    'blockNumber': tx['block_number'],
                    'txHash': tx['tx_hash'],
                    'tokenIn': tx['token_in'],
                    'tokenOut': tx['token_out'],
                    'amountIn': str(tx['amount_in']),
                    'amountOut': str(tx['amount_out']),
                    'type': 'buy' if tx['token_in'] == 'WETH' else 'sell'
                } for tx in transactions]
            }

    def store_monitoring_result(self, market_id, risk_level, risk_score, factors):
        """
        存储监控结果
        由monitor.py调用，存储计算结果到数据库
        """
        with self.db as db:
            # 1. 插入风险等级
            risk_id = db.insert_risk_level(
                market_id=market_id,
                risk_level=risk_level,
                risk_score=risk_score
            )

            # 2. 插入风险因子
            factor_id = db.insert_risk_factors(
                market_id=market_id,
                factors=factors
            )

            return {
                'risk_id': risk_id,
                'factor_id': factor_id
            }


def main():
    """测试API"""
    print("="*50)
    print("  ChainMonitor API Integration Test")
    print("="*50)

    api = RiskMonitorAPI()

    # 测试1: 获取仪表盘数据
    print("\n1. Testing Dashboard Data...")
    try:
        dashboard = api.get_dashboard_data()
        print(f"   Markets: {len(dashboard['markets'])}")
        print(f"   Alerts: {len(dashboard['alerts'])}")

        if dashboard['markets']:
            market = dashboard['markets'][0]
            print(f"   Sample Market: {market['label']}")
            print(f"   Risk Level: {market['currentRiskLevel']}")
            print(f"   Risk Score: {market['riskScore']}")

        # 输出JSON格式（可用于前端API）
        print("\n   JSON Output (first 500 chars):")
        json_str = json.dumps(dashboard, indent=2)
        print(f"   {json_str[:500]}...")

    except Exception as e:
        print(f"   ❌ Error: {e}")

    # 测试2: 获取市场详情
    print("\n2. Testing Market Detail...")
    try:
        detail = api.get_market_detail('UNISWAP_USDC_WETH')
        print(f"   Current Risk Level: {detail['currentRisk']['level']}")
        print(f"   Risk Score: {detail['currentRisk']['score']}")
        print(f"   History Points: {len(detail['history'])}")
        print(f"   Transactions: {len(detail['transactions'])}")

        print(f"\n   Factors:")
        print(f"   - DEX Score: {detail['factors']['dex']['score']}/40")
        print(f"   - Whale Score: {detail['factors']['whale']['score']}/35")
        print(f"   - CEX Score: {detail['factors']['cex']['score']}/30")

    except Exception as e:
        print(f"   ❌ Error: {e}")

    # 测试3: 存储监控结果
    print("\n3. Testing Store Monitoring Result...")
    try:
        test_factors = {
            'dex_score': 28.5,
            'dex_volume_ratio': 0.152,
            'dex_tx_count': 1245,
            'dex_liquidity': 45200000,
            'whale_score': 21.0,
            'whale_sell_volume': 2300000,
            'whale_active_count': 5,
            'whale_sell_ratio': 0.051,
            'cex_score': 13.0,
            'cex_total_inflow': 8900000,
            'cex_total_outflow': 7100000,
            'cex_net_inflow': 1800000,
            'cex_net_inflow_ratio': 0.04
        }

        result = api.store_monitoring_result(
            market_id='UNISWAP_USDC_WETH',
            risk_level=2,
            risk_score=62.5,
            factors=test_factors
        )

        print(f"   ✅ Stored: risk_id={result['risk_id']}, factor_id={result['factor_id']}")

    except Exception as e:
        print(f"   ❌ Error: {e}")

    print("\n" + "="*50)
    print("  ✅ API Integration Test Complete")
    print("="*50)


if __name__ == '__main__':
    main()
