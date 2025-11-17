import React from 'react';
import { Card, LoadingSpinner, ProgressBar } from '@/components/common';
import { RiskTrendChart, FactorBarChart } from '@/components/charts';
import { RiskOverview, MarketCard, EventFeed } from '@/components/features';
import { useAllMarkets } from '@/hooks/useRiskData';
import { useAlerts } from '@/hooks/useAlerts';
import { ChartDataPoint } from '@/types';

export const Dashboard: React.FC = () => {
  const { markets, loading: marketsLoading } = useAllMarkets();
  const { alerts, loading: alertsLoading } = useAlerts();

  // Mock trend data for the chart
  const trendData: ChartDataPoint[] = Array.from({ length: 24 }, (_, i) => ({
    timestamp: Math.floor(Date.now() / 1000) - (23 - i) * 3600,
    value: Math.random() * 30 + 30 + (i > 18 ? 20 : 0), // Spike in recent hours
  }));

  if (marketsLoading || alertsLoading) {
    return <LoadingSpinner size="lg" text="Loading dashboard..." />;
  }

  const currentMarket = markets[0];
  const marketsAtRisk = markets.filter((m) => m.currentRiskLevel >= 2).length;

  return (
    <div className="space-y-6">
      {/* Risk Overview */}
      <RiskOverview
        currentLevel={currentMarket?.currentRiskLevel || 0}
        lastUpdated={currentMarket?.lastUpdated || Math.floor(Date.now() / 1000)}
        totalMarkets={markets.length}
        marketsAtRisk={marketsAtRisk}
      />

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <h3 className="text-sm font-semibold text-text-tertiary uppercase tracking-wider mb-4">
            Overall Score
          </h3>
          <div className="flex items-baseline gap-2 mb-4">
            <span className="text-4xl font-bold text-text-primary">
              {currentMarket?.riskScore || 0}
            </span>
            <span className="text-xl text-text-tertiary">/100</span>
          </div>
          <ProgressBar
            value={currentMarket?.riskScore || 0}
            max={100}
            color={`risk-${currentMarket?.currentRiskLevel || 0}`}
            showValue={false}
          />
        </Card>

        <Card>
          <h3 className="text-sm font-semibold text-text-tertiary uppercase tracking-wider mb-4">
            DEX Activity
          </h3>
          <div className="flex items-baseline gap-2 mb-2">
            <span className="text-4xl font-bold text-text-primary">
              {currentMarket?.factors.dex.score || 0}
            </span>
            <span className="text-xl text-text-tertiary">
              /{currentMarket?.factors.dex.maxScore || 40}
            </span>
          </div>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-text-tertiary">Transactions</span>
              <span className="text-text-secondary font-mono">
                {currentMarket?.factors.dex.txCount.toLocaleString() || 0}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-text-tertiary">Volume Ratio</span>
              <span className="text-text-secondary font-mono">
                {((currentMarket?.factors.dex.volumeRatio || 0) * 100).toFixed(2)}%
              </span>
            </div>
          </div>
        </Card>

        <Card>
          <h3 className="text-sm font-semibold text-text-tertiary uppercase tracking-wider mb-4">
            Whale Pressure
          </h3>
          <div className="flex items-baseline gap-2 mb-2">
            <span className="text-4xl font-bold text-text-primary">
              {currentMarket?.factors.whale.score || 0}
            </span>
            <span className="text-xl text-text-tertiary">
              /{currentMarket?.factors.whale.maxScore || 35}
            </span>
          </div>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-text-tertiary">Active Whales</span>
              <span className="text-text-secondary font-mono">
                {currentMarket?.factors.whale.activeWhales || 0}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-text-tertiary">Sell Ratio</span>
              <span className="text-text-secondary font-mono">
                {((currentMarket?.factors.whale.sellRatio || 0) * 100).toFixed(2)}%
              </span>
            </div>
          </div>
        </Card>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <h3 className="text-lg font-semibold text-text-primary mb-4">
            Risk Trend (24h)
          </h3>
          <RiskTrendChart data={trendData} />
        </Card>

        <Card>
          <h3 className="text-lg font-semibold text-text-primary mb-4">
            Factor Breakdown
          </h3>
          <FactorBarChart
            dexScore={currentMarket?.factors.dex.score || 0}
            whaleScore={currentMarket?.factors.whale.score || 0}
            cexScore={currentMarket?.factors.cex.score || 0}
          />
        </Card>
      </div>

      {/* Markets and Events */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="space-y-6">
          <h2 className="text-xl font-bold text-text-primary">Monitored Markets</h2>
          {markets.map((market) => (
            <MarketCard key={market.marketId} market={market} />
          ))}
        </div>

        <EventFeed events={alerts} limit={10} />
      </div>
    </div>
  );
};
