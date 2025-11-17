import { useState, useEffect } from 'react';
import { AlertEvent } from '@/types';

/**
 * Hook to manage alert events
 */
export function useAlerts() {
  const [alerts, setAlerts] = useState<AlertEvent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Mock alerts data
    const mockAlerts: AlertEvent[] = [
      {
        id: '1',
        timestamp: Math.floor(Date.now() / 1000) - 300, // 5 min ago
        marketId: 'UNISWAP_USDC_WETH',
        marketLabel: 'UNISWAP_USDC_WETH',
        riskLevel: 2,
        previousLevel: 1,
        txHash: '0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef',
        message: 'Risk level elevated to WARNING due to increased whale activity',
      },
      {
        id: '2',
        timestamp: Math.floor(Date.now() / 1000) - 3600, // 1 hour ago
        marketId: 'UNISWAP_USDC_WETH',
        marketLabel: 'UNISWAP_USDC_WETH',
        riskLevel: 1,
        previousLevel: 0,
        txHash: '0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890',
        message: 'Risk level increased to CAUTION',
      },
    ];

    setTimeout(() => {
      setAlerts(mockAlerts);
      setLoading(false);
    }, 300);
  }, []);

  const addAlert = (alert: AlertEvent) => {
    setAlerts((prev) => [alert, ...prev]);
  };

  const clearAlerts = () => {
    setAlerts([]);
  };

  return {
    alerts,
    loading,
    addAlert,
    clearAlerts,
  };
}
