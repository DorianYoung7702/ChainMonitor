import { useState, useEffect } from 'react';
import { MarketData, RiskLevel } from '@/types';
import { REFRESH_INTERVALS } from '@/utils/constants';

/**
 * Hook to fetch and manage risk data for markets
 * In production, this would fetch from the backend API
 * For now, it provides mock data for demonstration
 */
export function useRiskData(marketId?: string) {
  const [data, setData] = useState<MarketData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    // Mock data generator
    const fetchRiskData = () => {
      try {
        setLoading(true);

        // Simulate API call delay
        setTimeout(() => {
          const mockData: MarketData = {
            marketId: marketId || 'UNISWAP_USDC_WETH',
            label: 'UNISWAP_USDC_WETH',
            currentRiskLevel: 2 as RiskLevel,
            previousRiskLevel: 1 as RiskLevel,
            lastUpdated: Math.floor(Date.now() / 1000) - 120, // 2 minutes ago
            riskScore: 62,
            factors: {
              dex: {
                score: 28,
                maxScore: 40,
                volumeRatio: 0.152,
                txCount: 1245,
                liquidity: 45200000,
              },
              whale: {
                score: 21,
                maxScore: 35,
                sellVolume: 2300000,
                activeWhales: 5,
                sellRatio: 0.051,
              },
              cex: {
                score: 13,
                maxScore: 30,
                totalInflow: 8900000,
                totalOutflow: 7100000,
                netInflow: 1800000,
                netInflowRatio: 0.04,
              },
            },
          };

          setData(mockData);
          setLoading(false);
        }, 500);
      } catch (err) {
        setError(err as Error);
        setLoading(false);
      }
    };

    fetchRiskData();

    // Set up polling for real-time updates
    const interval = setInterval(fetchRiskData, REFRESH_INTERVALS.MARKET_DATA);

    return () => clearInterval(interval);
  }, [marketId]);

  return { data, loading, error };
}

/**
 * Hook to fetch all markets data
 */
export function useAllMarkets() {
  const [markets, setMarkets] = useState<MarketData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    const fetchMarkets = () => {
      try {
        setLoading(true);

        setTimeout(() => {
          // Mock data for all markets
          const mockMarkets: MarketData[] = [
            {
              marketId: 'UNISWAP_USDC_WETH',
              label: 'UNISWAP_USDC_WETH',
              currentRiskLevel: 2 as RiskLevel,
              previousRiskLevel: 1 as RiskLevel,
              lastUpdated: Math.floor(Date.now() / 1000) - 120,
              riskScore: 62,
              factors: {
                dex: {
                  score: 28,
                  maxScore: 40,
                  volumeRatio: 0.152,
                  txCount: 1245,
                  liquidity: 45200000,
                },
                whale: {
                  score: 21,
                  maxScore: 35,
                  sellVolume: 2300000,
                  activeWhales: 5,
                  sellRatio: 0.051,
                },
                cex: {
                  score: 13,
                  maxScore: 30,
                  totalInflow: 8900000,
                  totalOutflow: 7100000,
                  netInflow: 1800000,
                  netInflowRatio: 0.04,
                },
              },
            },
          ];

          setMarkets(mockMarkets);
          setLoading(false);
        }, 300);
      } catch (err) {
        setError(err as Error);
        setLoading(false);
      }
    };

    fetchMarkets();
    const interval = setInterval(fetchMarkets, REFRESH_INTERVALS.MARKET_DATA);

    return () => clearInterval(interval);
  }, []);

  return { markets, loading, error };
}
