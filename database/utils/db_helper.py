#!/usr/bin/env python3
"""
数据库辅助工具
提供常用的数据库查询和管理功能
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime

class DatabaseHelper:
    """数据库辅助类"""

    def __init__(self, config=None):
        if config is None:
            config = {
                'host': os.getenv('DB_HOST', 'localhost'),
                'port': os.getenv('DB_PORT', '5432'),
                'database': os.getenv('DB_NAME', 'chainmonitor'),
                'user': os.getenv('DB_USER', 'postgres'),
                'password': os.getenv('DB_PASSWORD', 'postgres')
            }
        self.config = config
        self.conn = None

    def connect(self):
        """建立连接"""
        if not self.conn or self.conn.closed:
            self.conn = psycopg2.connect(**self.config)
        return self.conn

    def close(self):
        """关闭连接"""
        if self.conn and not self.conn.closed:
            self.conn.close()

    def execute_query(self, query, params=None, fetch_one=False, fetch_all=True):
        """
        执行查询并返回结果

        Args:
            query: SQL查询语句
            params: 查询参数
            fetch_one: 是否只返回一条记录
            fetch_all: 是否返回所有记录

        Returns:
            查询结果（dict或list of dict）
        """
        conn = self.connect()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        try:
            cursor.execute(query, params)

            if fetch_one:
                result = cursor.fetchone()
                return dict(result) if result else None
            elif fetch_all:
                results = cursor.fetchall()
                return [dict(row) for row in results]
            else:
                conn.commit()
                return cursor.rowcount

        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()

    def get_latest_risk(self, market_id):
        """获取最新风险等级"""
        query = """
        SELECT risk_level, risk_score, block_number, tx_hash, created_at
        FROM v_latest_risk
        WHERE market_id = %s
        """
        return self.execute_query(query, (market_id,), fetch_one=True)

    def get_risk_history(self, market_id, hours=24):
        """获取风险历史"""
        query = """
        SELECT risk_level, risk_score, block_number, created_at
        FROM risk_levels
        WHERE market_id = %s
          AND created_at > NOW() - INTERVAL '%s hours'
        ORDER BY created_at DESC
        """
        return self.execute_query(query, (market_id, hours))

    def get_latest_factors(self, market_id, limit=1):
        """获取最新风险因子"""
        query = """
        SELECT *
        FROM risk_factors
        WHERE market_id = %s
        ORDER BY created_at DESC
        LIMIT %s
        """
        result = self.execute_query(query, (market_id, limit))
        return result[0] if result and limit == 1 else result

    def get_recent_transactions(self, market_id, limit=20):
        """获取最近的DEX交易"""
        query = """
        SELECT tx_hash, block_number, timestamp, token_in, token_out,
               amount_in, amount_out, trader_address
        FROM dex_transactions
        WHERE market_id = %s
        ORDER BY timestamp DESC
        LIMIT %s
        """
        return self.execute_query(query, (market_id, limit))

    def get_whale_activity(self, market_id, hours=24):
        """获取巨鲸活动"""
        query = """
        SELECT whale_address, tx_type, COUNT(*) as tx_count,
               SUM(usd_value) as total_value
        FROM whale_transactions
        WHERE market_id = %s
          AND timestamp > EXTRACT(EPOCH FROM NOW() - INTERVAL '%s hours')
        GROUP BY whale_address, tx_type
        ORDER BY total_value DESC
        """
        return self.execute_query(query, (market_id, hours))

    def get_cex_flows(self, market_id, hours=24):
        """获取CEX流动统计"""
        query = """
        SELECT
            flow_type,
            COUNT(*) as tx_count,
            SUM(usd_value) as total_value
        FROM cex_flows
        WHERE market_id = %s
          AND timestamp > EXTRACT(EPOCH FROM NOW() - INTERVAL '%s hours')
        GROUP BY flow_type
        """
        return self.execute_query(query, (market_id, hours))

    def get_alerts(self, market_id=None, severity=None, limit=50):
        """获取告警记录"""
        conditions = []
        params = []

        if market_id:
            conditions.append("market_id = %s")
            params.append(market_id)

        if severity:
            conditions.append("severity = %s")
            params.append(severity)

        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

        query = f"""
        SELECT *
        FROM alerts
        {where_clause}
        ORDER BY created_at DESC
        LIMIT %s
        """
        params.append(limit)

        return self.execute_query(query, tuple(params))

    def insert_risk_level(self, market_id, risk_level, risk_score, block_number=None, tx_hash=None):
        """插入风险等级记录"""
        query = """
        INSERT INTO risk_levels (market_id, risk_level, risk_score, block_number, tx_hash, source)
        VALUES (%s, %s, %s, %s, %s, 'api')
        RETURNING id
        """
        result = self.execute_query(query, (market_id, risk_level, risk_score, block_number, tx_hash), fetch_one=True)
        return result['id'] if result else None

    def insert_risk_factors(self, market_id, factors):
        """插入风险因子数据"""
        query = """
        INSERT INTO risk_factors (
            market_id, dex_score, dex_volume_ratio, dex_tx_count, dex_liquidity,
            whale_score, whale_sell_volume, whale_active_count, whale_sell_ratio,
            cex_score, cex_total_inflow, cex_total_outflow, cex_net_inflow, cex_net_inflow_ratio
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        RETURNING id
        """
        params = (
            market_id,
            factors.get('dex_score'), factors.get('dex_volume_ratio'),
            factors.get('dex_tx_count'), factors.get('dex_liquidity'),
            factors.get('whale_score'), factors.get('whale_sell_volume'),
            factors.get('whale_active_count'), factors.get('whale_sell_ratio'),
            factors.get('cex_score'), factors.get('cex_total_inflow'),
            factors.get('cex_total_outflow'), factors.get('cex_net_inflow'),
            factors.get('cex_net_inflow_ratio')
        )
        result = self.execute_query(query, params, fetch_one=True)
        return result['id'] if result else None

    def get_market_overview(self):
        """获取市场概览"""
        query = "SELECT * FROM v_market_overview"
        return self.execute_query(query)

    def get_table_stats(self):
        """获取表统计信息"""
        query = """
        SELECT
            schemaname,
            tablename,
            pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
            n_live_tup as row_count
        FROM pg_tables t
        JOIN pg_stat_user_tables s ON t.tablename = s.relname
        WHERE schemaname = 'public'
        ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
        """
        return self.execute_query(query)

    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


if __name__ == '__main__':
    # 测试用例
    with DatabaseHelper() as db:
        print("=== Testing DatabaseHelper ===\n")

        # 1. 获取市场概览
        print("1. Market Overview:")
        markets = db.get_market_overview()
        for market in markets:
            print(f"   {market['label']}: Risk Level {market['current_risk_level']}, Score {market['current_risk_score']}")

        # 2. 获取最新风险
        print("\n2. Latest Risk for UNISWAP_USDC_WETH:")
        risk = db.get_latest_risk('UNISWAP_USDC_WETH')
        if risk:
            print(f"   Level: {risk['risk_level']}, Score: {risk['risk_score']}")

        # 3. 获取最新因子
        print("\n3. Latest Factors:")
        factors = db.get_latest_factors('UNISWAP_USDC_WETH')
        if factors:
            print(f"   DEX Score: {factors['dex_score']}")
            print(f"   Whale Score: {factors['whale_score']}")
            print(f"   CEX Score: {factors['cex_score']}")

        # 4. 获取表统计
        print("\n4. Table Statistics:")
        stats = db.get_table_stats()
        for stat in stats[:5]:  # 只显示前5个
            print(f"   {stat['tablename']}: {stat['size']}, {stat['row_count']} rows")

        print("\n✅ All tests completed")
