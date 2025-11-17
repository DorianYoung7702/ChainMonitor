/**
 * ChainMonitor API Data Hooks
 * 真实API数据获取hooks
 */

import { useState, useEffect } from 'react';
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
});

// ============================================
// 类型定义
// ============================================

export interface Market {
  id: string;
  label: string;
  type: string;
  address: string;
  token0: string;
  token1: string;
  riskLevel: number;
  riskScore: number;
  lastUpdated: string | null;
  isActive: boolean;
}

export interface RiskHistoryPoint {
  timestamp: string;
  level: number;
  score: number;
}

export interface RiskFactors {
  dex: {
    score: number;
    volumeRatio: number;
    txCount: number;
    liquidity: number;
  };
  whale: {
    score: number;
    sellVolume: number;
    activeCount: number;
    sellRatio: number;
  };
  cex: {
    score: number;
    totalInflow: number;
    totalOutflow: number;
    netInflow: number;
    netInflowRatio: number;
  };
  updatedAt: string;
}

export interface Transaction {
  txHash: string;
  blockNumber: number;
  timestamp: number;
  tokenIn: string;
  tokenOut: string;
  amountIn: string;
  amountOut: string;
  trader: string;
  createdAt: string;
}

export interface Alert {
  id: number;
  marketId: string;
  marketLabel: string;
  type: string;
  severity: string;
  previousLevel: number | null;
  newLevel: number;
  message: string | null;
  isResolved: boolean;
  createdAt: string;
}

// ============================================
// Hooks
// ============================================

/**
 * 获取所有市场列表
 */
export function useMarkets() {
  const [markets, setMarkets] = useState<Market[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchMarkets = async () => {
      try {
        setLoading(true);
        const response = await api.get('/markets');
        setMarkets(response.data.markets);
        setError(null);
      } catch (err) {
        console.error('Failed to fetch markets:', err);
        setError(err instanceof Error ? err.message : 'Failed to fetch markets');
        // 降级到mock数据
        setMarkets(getMockMarkets());
      } finally {
        setLoading(false);
      }
    };

    fetchMarkets();
    const interval = setInterval(fetchMarkets, 30000); // 每30秒刷新
    return () => clearInterval(interval);
  }, []);

  return { markets, loading, error };
}

/**
 * 获取单个市场详情
 */
export function useMarketDetail(marketId: string) {
  const [market, setMarket] = useState<Market | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchMarket = async () => {
      try {
        setLoading(true);
        const response = await api.get(`/markets/${marketId}`);
        setMarket(response.data);
        setError(null);
      } catch (err) {
        console.error('Failed to fetch market detail:', err);
        setError(err instanceof Error ? err.message : 'Failed to fetch market');
      } finally {
        setLoading(false);
      }
    };

    if (marketId) {
      fetchMarket();
    }
  }, [marketId]);

  return { market, loading, error };
}

/**
 * 获取市场风险历史
 */
export function useRiskHistory(marketId: string, hours: number = 24) {
  const [history, setHistory] = useState<RiskHistoryPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        setLoading(true);
        const response = await api.get(`/markets/${marketId}/risk-history`, {
          params: { hours }
        });
        setHistory(response.data.history);
        setError(null);
      } catch (err) {
        console.error('Failed to fetch risk history:', err);
        setError(err instanceof Error ? err.message : 'Failed to fetch history');
        // 降级到mock数据
        setHistory(getMockRiskHistory());
      } finally {
        setLoading(false);
      }
    };

    if (marketId) {
      fetchHistory();
      const interval = setInterval(fetchHistory, 60000); // 每分钟刷新
      return () => clearInterval(interval);
    }
  }, [marketId, hours]);

  return { history, loading, error };
}

/**
 * 获取风险因子
 */
export function useRiskFactors(marketId: string) {
  const [factors, setFactors] = useState<RiskFactors | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchFactors = async () => {
      try {
        setLoading(true);
        const response = await api.get(`/markets/${marketId}/factors`);
        setFactors(response.data.factors);
        setError(null);
      } catch (err) {
        console.error('Failed to fetch risk factors:', err);
        setError(err instanceof Error ? err.message : 'Failed to fetch factors');
        // 降级到mock数据
        setFactors(getMockFactors());
      } finally {
        setLoading(false);
      }
    };

    if (marketId) {
      fetchFactors();
      const interval = setInterval(fetchFactors, 30000); // 每30秒刷新
      return () => clearInterval(interval);
    }
  }, [marketId]);

  return { factors, loading, error };
}

/**
 * 获取交易记录
 */
export function useTransactions(marketId: string, limit: number = 100) {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchTransactions = async () => {
      try {
        setLoading(true);
        const response = await api.get(`/markets/${marketId}/transactions`, {
          params: { limit }
        });
        setTransactions(response.data.transactions);
        setError(null);
      } catch (err) {
        console.error('Failed to fetch transactions:', err);
        setError(err instanceof Error ? err.message : 'Failed to fetch transactions');
        setTransactions([]);
      } finally {
        setLoading(false);
      }
    };

    if (marketId) {
      fetchTransactions();
      const interval = setInterval(fetchTransactions, 60000); // 每分钟刷新
      return () => clearInterval(interval);
    }
  }, [marketId, limit]);

  return { transactions, loading, error };
}

/**
 * 获取告警列表
 */
export function useAlerts(severity?: string) {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchAlerts = async () => {
      try {
        setLoading(true);
        const response = await api.get('/alerts', {
          params: severity ? { severity } : {}
        });
        setAlerts(response.data.alerts);
        setError(null);
      } catch (err) {
        console.error('Failed to fetch alerts:', err);
        setError(err instanceof Error ? err.message : 'Failed to fetch alerts');
        setAlerts([]);
      } finally {
        setLoading(false);
      }
    };

    fetchAlerts();
    const interval = setInterval(fetchAlerts, 30000); // 每30秒刷新
    return () => clearInterval(interval);
  }, [severity]);

  return { alerts, loading, error };
}

/**
 * 获取总览统计
 */
export function useOverviewStats() {
  const [stats, setStats] = useState({
    totalMarkets: 0,
    highRiskMarkets: 0,
    todayTransactions: 0,
    unresolvedAlerts: 0,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        setLoading(true);
        const response = await api.get('/stats/overview');
        setStats(response.data);
        setError(null);
      } catch (err) {
        console.error('Failed to fetch stats:', err);
        setError(err instanceof Error ? err.message : 'Failed to fetch stats');
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
    const interval = setInterval(fetchStats, 30000); // 每30秒刷新
    return () => clearInterval(interval);
  }, []);

  return { stats, loading, error };
}

// ============================================
// Mock数据（降级方案）
// ============================================

function getMockMarkets(): Market[] {
  return [
    {
      id: 'UNISWAP_USDC_WETH',
      label: 'Uniswap USDC/WETH',
      type: 'dex_pool',
      address: '0xB4e16d0168e52d35CaCD2c6185b44281Ec28C9Dc',
      token0: 'USDC',
      token1: 'WETH',
      riskLevel: 1,
      riskScore: 45.5,
      lastUpdated: new Date().toISOString(),
      isActive: true,
    },
  ];
}

function getMockRiskHistory(): RiskHistoryPoint[] {
  const now = Date.now();
  return Array.from({ length: 24 }, (_, i) => ({
    timestamp: new Date(now - (23 - i) * 3600000).toISOString(),
    level: Math.floor(Math.random() * 4),
    score: Math.random() * 100,
  }));
}

function getMockFactors(): RiskFactors {
  return {
    dex: { score: 20, volumeRatio: 0.05, txCount: 245, liquidity: 1000000 },
    whale: { score: 15, sellVolume: 50000, activeCount: 2, sellRatio: 0.05 },
    cex: { score: 10, totalInflow: 100000, totalOutflow: 80000, netInflow: 20000, netInflowRatio: 0.02 },
    updatedAt: new Date().toISOString(),
  };
}
