#!/usr/bin/env python3
"""
ChainMonitor 测试数据生成器
生成用于测试前端和后端的模拟数据
"""

import random
import time
from datetime import datetime, timedelta
from decimal import Decimal
import psycopg2
from psycopg2.extras import execute_batch
import os

# 数据库配置
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'chainmonitor'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'postgres')
}

# 常量
UNISWAP_USDC_WETH_PAIR = '0xB4e16d0168e52d35CaCD2c6185b44281Ec28C9Dc'
USDC_ADDRESS = '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48'
WETH_ADDRESS = '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2'

# 巨鲸地址列表（示例）
WHALE_ADDRESSES = [
    '0x47ac0Fb4F2D84898e4D9E7b4DaB3C24507a6D503',  # Binance
    '0x8894E0a0c962CB723c1976a4421c95949bE2D4E3',  # Binance 2
    '0x28C6c06298d514Db089934071355E5743bf21d60',  # Binance 3
    '0x21a31Ee1afC51d94C2eFcCAa2092aD1028285549',  # Binance 4
    '0xDFd5293D8e347dFe59E90eFd55b2956a1343963d',  # Binance 5
]

# CEX地址
CEX_ADDRESSES = {
    'Binance': '0x28C6c06298d514Db089934071355E5743bf21d60',
    'Coinbase': '0x71660c4005BA85c37ccec55d0C4493E66Fe775d3',
    'Kraken': '0x2910543Af39abA0Cd09dBb2D50200b3E800A63D2',
}

class DataGenerator:
    def __init__(self):
        self.conn = None
        self.cursor = None

    def connect(self):
        """连接数据库"""
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            self.cursor = self.conn.cursor()
            print("✅ Database connected successfully")
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            raise

    def close(self):
        """关闭连接"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        print("✅ Database connection closed")

    def clear_all_data(self):
        """清空所有数据（谨慎使用）"""
        tables = [
            'user_configs', 'alerts', 'liquidity_snapshots',
            'cex_flows', 'whale_transactions', 'dex_transactions',
            'risk_factors', 'risk_levels', 'markets', 'monitoring_stats'
        ]

        print("⚠️  Clearing all data...")
        for table in tables:
            try:
                self.cursor.execute(f"TRUNCATE TABLE {table} CASCADE")
                print(f"   Cleared {table}")
            except Exception as e:
                print(f"   Warning: Could not clear {table}: {e}")

        self.conn.commit()
        print("✅ All data cleared")

    def generate_markets(self):
        """生成市场数据"""
        print("\n📊 Generating markets...")

        markets = [
            {
                'market_id': 'UNISWAP_USDC_WETH',
                'label': 'UNISWAP_USDC_WETH',
                'market_type': 'dex_pool',
                'chain': 'ethereum',
                'contract_address': UNISWAP_USDC_WETH_PAIR,
                'token0_address': USDC_ADDRESS,
                'token0_symbol': 'USDC',
                'token1_address': WETH_ADDRESS,
                'token1_symbol': 'WETH',
                'description': 'Uniswap V2 USDC/WETH Pool',
                'is_active': True
            }
        ]

        query = """
        INSERT INTO markets (market_id, label, market_type, chain, contract_address,
                            token0_address, token0_symbol, token1_address, token1_symbol,
                            description, is_active)
        VALUES (%(market_id)s, %(label)s, %(market_type)s, %(chain)s, %(contract_address)s,
                %(token0_address)s, %(token0_symbol)s, %(token1_address)s, %(token1_symbol)s,
                %(description)s, %(is_active)s)
        ON CONFLICT (market_id) DO UPDATE
        SET label = EXCLUDED.label,
            updated_at = CURRENT_TIMESTAMP
        """

        execute_batch(self.cursor, query, markets)
        self.conn.commit()
        print(f"✅ Generated {len(markets)} markets")

    def generate_risk_history(self, days=7):
        """生成风险等级历史数据"""
        print(f"\n📈 Generating risk history for {days} days...")

        market_id = 'UNISWAP_USDC_WETH'
        now = int(time.time())

        risk_data = []

        # 模拟7天的风险变化
        current_risk = 0
        current_score = random.uniform(10, 20)

        for day in range(days):
            # 每天4个数据点
            for hour in [0, 6, 12, 18]:
                timestamp = now - ((days - day) * 86400) + (hour * 3600)
                block_number = 18000000 + (day * 7200) + (hour * 300)

                # 模拟风险逐渐上升
                if day > 3:
                    current_score += random.uniform(5, 15)
                    if current_score > 40:
                        current_risk = 2
                    elif current_score > 20:
                        current_risk = 1
                else:
                    current_score += random.uniform(-5, 5)

                current_score = max(0, min(100, current_score))

                risk_data.append({
                    'market_id': market_id,
                    'risk_level': current_risk,
                    'risk_score': round(current_score, 2),
                    'block_number': block_number,
                    'tx_hash': f"0x{''.join(random.choices('0123456789abcdef', k=64))}",
                    'source': 'test_generator'
                })

        query = """
        INSERT INTO risk_levels (market_id, risk_level, risk_score, block_number, tx_hash, source)
        VALUES (%(market_id)s, %(risk_level)s, %(risk_score)s, %(block_number)s, %(tx_hash)s, %(source)s)
        """

        execute_batch(self.cursor, query, risk_data)
        self.conn.commit()
        print(f"✅ Generated {len(risk_data)} risk level records")

    def generate_risk_factors(self, count=100):
        """生成风险因子数据"""
        print(f"\n🔍 Generating {count} risk factor records...")

        market_id = 'UNISWAP_USDC_WETH'
        factor_data = []

        for i in range(count):
            dex_score = random.uniform(15, 35)
            whale_score = random.uniform(10, 30)
            cex_score = random.uniform(5, 25)

            factor_data.append({
                'market_id': market_id,
                'dex_score': round(dex_score, 2),
                'dex_volume_ratio': round(random.uniform(0.1, 0.3), 6),
                'dex_tx_count': random.randint(800, 2000),
                'dex_liquidity': round(random.uniform(30000000, 60000000), 2),
                'whale_score': round(whale_score, 2),
                'whale_sell_volume': round(random.uniform(1000000, 5000000), 2),
                'whale_active_count': random.randint(3, 8),
                'whale_sell_ratio': round(random.uniform(0.03, 0.08), 6),
                'cex_score': round(cex_score, 2),
                'cex_total_inflow': round(random.uniform(5000000, 15000000), 2),
                'cex_total_outflow': round(random.uniform(4000000, 14000000), 2),
                'cex_net_inflow': round(random.uniform(500000, 3000000), 2),
                'cex_net_inflow_ratio': round(random.uniform(0.02, 0.06), 6)
            })

        query = """
        INSERT INTO risk_factors (market_id, dex_score, dex_volume_ratio, dex_tx_count, dex_liquidity,
                                  whale_score, whale_sell_volume, whale_active_count, whale_sell_ratio,
                                  cex_score, cex_total_inflow, cex_total_outflow, cex_net_inflow, cex_net_inflow_ratio)
        VALUES (%(market_id)s, %(dex_score)s, %(dex_volume_ratio)s, %(dex_tx_count)s, %(dex_liquidity)s,
                %(whale_score)s, %(whale_sell_volume)s, %(whale_active_count)s, %(whale_sell_ratio)s,
                %(cex_score)s, %(cex_total_inflow)s, %(cex_total_outflow)s, %(cex_net_inflow)s, %(cex_net_inflow_ratio)s)
        """

        execute_batch(self.cursor, query, factor_data)
        self.conn.commit()
        print(f"✅ Generated {len(factor_data)} risk factor records")

    def generate_dex_transactions(self, count=500):
        """生成DEX交易记录"""
        print(f"\n💱 Generating {count} DEX transactions...")

        market_id = 'UNISWAP_USDC_WETH'
        now = int(time.time())
        tx_data = []

        for i in range(count):
            timestamp = now - random.randint(0, 86400 * 7)  # 过去7天
            is_buy = random.choice([True, False])

            tx_data.append({
                'market_id': market_id,
                'tx_hash': f"0x{''.join(random.choices('0123456789abcdef', k=64))}",
                'block_number': 18000000 + random.randint(0, 10000),
                'timestamp': timestamp,
                'token_in': 'WETH' if is_buy else 'USDC',
                'token_out': 'USDC' if is_buy else 'WETH',
                'amount_in': str(int(random.uniform(0.1, 100) * 1e18)),
                'amount_out': str(int(random.uniform(100, 200000) * 1e6)),
                'trader_address': f"0x{''.join(random.choices('0123456789abcdef', k=40))}",
                'gas_used': random.randint(100000, 300000),
                'gas_price': random.randint(20, 100) * 1e9
            })

        query = """
        INSERT INTO dex_transactions (market_id, tx_hash, block_number, timestamp,
                                       token_in, token_out, amount_in, amount_out,
                                       trader_address, gas_used, gas_price)
        VALUES (%(market_id)s, %(tx_hash)s, %(block_number)s, %(timestamp)s,
                %(token_in)s, %(token_out)s, %(amount_in)s, %(amount_out)s,
                %(trader_address)s, %(gas_used)s, %(gas_price)s)
        """

        execute_batch(self.cursor, query, tx_data, page_size=100)
        self.conn.commit()
        print(f"✅ Generated {len(tx_data)} DEX transactions")

    def generate_whale_transactions(self, count=50):
        """生成巨鲸交易"""
        print(f"\n🐋 Generating {count} whale transactions...")

        market_id = 'UNISWAP_USDC_WETH'
        now = int(time.time())
        whale_data = []

        for i in range(count):
            timestamp = now - random.randint(0, 86400 * 7)
            tx_type = random.choice(['sell', 'sell', 'buy', 'transfer'])  # 卖出概率更高

            whale_data.append({
                'market_id': market_id,
                'whale_address': random.choice(WHALE_ADDRESSES),
                'tx_hash': f"0x{''.join(random.choices('0123456789abcdef', k=64))}",
                'block_number': 18000000 + random.randint(0, 10000),
                'timestamp': timestamp,
                'to_address': f"0x{''.join(random.choices('0123456789abcdef', k=40))}",
                'token_symbol': random.choice(['USDC', 'WETH']),
                'amount': str(int(random.uniform(100, 10000) * 1e18)),
                'usd_value': round(random.uniform(100000, 5000000), 2),
                'tx_type': tx_type
            })

        query = """
        INSERT INTO whale_transactions (market_id, whale_address, tx_hash, block_number, timestamp,
                                        to_address, token_symbol, amount, usd_value, tx_type)
        VALUES (%(market_id)s, %(whale_address)s, %(tx_hash)s, %(block_number)s, %(timestamp)s,
                %(to_address)s, %(token_symbol)s, %(amount)s, %(usd_value)s, %(tx_type)s)
        """

        execute_batch(self.cursor, query, whale_data)
        self.conn.commit()
        print(f"✅ Generated {len(whale_data)} whale transactions")

    def generate_alerts(self, count=20):
        """生成告警记录"""
        print(f"\n🔔 Generating {count} alerts...")

        market_id = 'UNISWAP_USDC_WETH'
        now = datetime.now()
        alert_data = []

        for i in range(count):
            prev_level = random.randint(0, 2)
            new_level = prev_level + random.randint(0, 2)
            new_level = min(new_level, 3)

            severity_map = {0: 'LOW', 1: 'MEDIUM', 2: 'HIGH', 3: 'CRITICAL'}

            alert_data.append({
                'market_id': market_id,
                'alert_type': 'RISK_LEVEL_CHANGE',
                'severity': severity_map[new_level],
                'previous_level': prev_level,
                'new_level': new_level,
                'message': f'Risk level changed from Level {prev_level} to Level {new_level}',
                'tx_hash': f"0x{''.join(random.choices('0123456789abcdef', k=64))}",
                'user_address': None,
                'is_resolved': random.choice([True, False])
            })

        query = """
        INSERT INTO alerts (market_id, alert_type, severity, previous_level, new_level,
                           message, tx_hash, user_address, is_resolved)
        VALUES (%(market_id)s, %(alert_type)s, %(severity)s, %(previous_level)s, %(new_level)s,
                %(message)s, %(tx_hash)s, %(user_address)s, %(is_resolved)s)
        """

        execute_batch(self.cursor, query, alert_data)
        self.conn.commit()
        print(f"✅ Generated {len(alert_data)} alerts")

    def generate_all(self):
        """生成所有测试数据"""
        print("\n" + "="*50)
        print("  ChainMonitor Test Data Generator")
        print("="*50)

        try:
            self.connect()

            # 选项：是否清空现有数据
            clear = input("\n⚠️  Clear existing data? (y/N): ").lower()
            if clear == 'y':
                self.clear_all_data()

            # 生成数据
            self.generate_markets()
            self.generate_risk_history(days=7)
            self.generate_risk_factors(count=100)
            self.generate_dex_transactions(count=500)
            self.generate_whale_transactions(count=50)
            self.generate_alerts(count=20)

            print("\n" + "="*50)
            print("  ✅ All test data generated successfully!")
            print("="*50)

        except Exception as e:
            print(f"\n❌ Error: {e}")
            if self.conn:
                self.conn.rollback()
            raise
        finally:
            self.close()

if __name__ == '__main__':
    generator = DataGenerator()
    generator.generate_all()
