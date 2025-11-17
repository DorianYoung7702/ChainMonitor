import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { Card, RiskBadge, LoadingSpinner, ProgressBar } from '@/components/common';
import { RiskTrendChart } from '@/components/charts';
import { TransactionTable } from '@/components/features';
import { useRiskData } from '@/hooks/useRiskData';
import { formatTimestamp, formatUSD, formatPercentage } from '@/utils/formatters';
import { ArrowLeft, ExternalLink } from 'lucide-react';
import { Transaction, ChartDataPoint } from '@/types';

export const MarketDetail: React.FC = () => {
  const { marketId } = useParams<{ marketId: string }>();
  const { data: market, loading } = useRiskData(marketId);

  // Mock transactions data
  const mockTransactions: Transaction[] = Array.from({ length: 15 }, (_, i) => ({
    timestamp: Math.floor(Date.now() / 1000) - i * 300,
    blockNumber: 18123456 - i * 10,
    txHash: `0x${Math.random().toString(16).substring(2, 66)}`,
    tokenIn: i % 2 === 0 ? 'USDC' : 'WETH',
    tokenOut: i % 2 === 0 ? 'WETH' : 'USDC',
    amountIn: (Math.random() * 10000).toFixed(2),
    amountOut: (Math.random() * 5).toFixed(4),
    type: i % 3 === 0 ? 'sell' : 'buy',
  }));

  // Mock historical data
  const historyData: ChartDataPoint[] = Array.from({ length: 48 }, (_, i) => ({
    timestamp: Math.floor(Date.now() / 1000) - (47 - i) * 1800, // 30 min intervals
    value: Math.random() * 40 + 20,
  }));

  if (loading) {
    return <LoadingSpinner size="lg" text="Loading market data..." />;
  }

  if (!market) {
    return (
      <div className="text-center py-12">
        <p className="text-text-tertiary">Market not found</p>
        <Link to="/" className="text-primary hover:text-primary-hover mt-4 inline-block">
          Return to Dashboard
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link
          to="/"
          className="p-2 rounded-lg hover:bg-bg-light transition-colors"
        >
          <ArrowLeft className="w-5 h-5 text-text-secondary" />
        </Link>
        <div className="flex-1">
          <h1 className="text-3xl font-bold text-text-primary">
            {market.label.replace(/_/g, ' ')}
          </h1>
          <p className="text-text-tertiary mt-1">
            Last updated: {formatTimestamp(market.lastUpdated)}
          </p>
        </div>
        <a
          href={`https://etherscan.io/address/0xB4e16d0168e52d35CaCD2c6185b44281Ec28C9Dc`}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-2 text-primary hover:text-primary-hover text-sm"
        >
          View on Etherscan
          <ExternalLink className="w-4 h-4" />
        </a>
      </div>

      {/* Current Risk Level */}
      <Card gradient={market.currentRiskLevel >= 2}>
        <div className="text-center py-8">
          <h2 className="text-lg font-semibold text-text-tertiary mb-4">
            Current Risk Level
          </h2>
          <div className="flex justify-center mb-6">
            <RiskBadge level={market.currentRiskLevel} size="lg" />
          </div>
          <div className="flex items-baseline justify-center gap-2 mb-4">
            <span className="text-5xl font-bold text-text-primary">
              {market.riskScore}
            </span>
            <span className="text-2xl text-text-tertiary">/100</span>
          </div>
          <p className="text-text-secondary max-w-md mx-auto">
            {market.currentRiskLevel === 0 && 'Market conditions are stable with normal trading activity'}
            {market.currentRiskLevel === 1 && 'Elevated activity detected. Monitor for further changes'}
            {market.currentRiskLevel === 2 && 'Significant risk indicators present. Exercise caution'}
            {market.currentRiskLevel === 3 && 'High risk conditions. Immediate attention required'}
          </p>
        </div>
      </Card>

      {/* Factor Details */}
      <div>
        <h2 className="text-xl font-bold text-text-primary mb-4">
          Multi-Factor Risk Analysis
        </h2>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* DEX Activity */}
          <Card>
            <h3 className="text-lg font-semibold text-text-primary mb-4">
              🔹 DEX Activity
            </h3>
            <div className="mb-4">
              <ProgressBar
                value={market.factors.dex.score}
                max={market.factors.dex.maxScore}
                label="Score"
                color="primary"
              />
            </div>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-text-tertiary">Volume/Liquidity</span>
                <span className="font-mono text-text-primary">
                  {formatPercentage(market.factors.dex.volumeRatio)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-tertiary">24h Transactions</span>
                <span className="font-mono text-text-primary">
                  {market.factors.dex.txCount.toLocaleString()}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-tertiary">Liquidity</span>
                <span className="font-mono text-text-primary">
                  {formatUSD(market.factors.dex.liquidity)}
                </span>
              </div>
            </div>
          </Card>

          {/* Whale Pressure */}
          <Card>
            <h3 className="text-lg font-semibold text-text-primary mb-4">
              🔹 Whale Pressure
            </h3>
            <div className="mb-4">
              <ProgressBar
                value={market.factors.whale.score}
                max={market.factors.whale.maxScore}
                label="Score"
                color="risk-2"
              />
            </div>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-text-tertiary">Sell Volume</span>
                <span className="font-mono text-text-primary">
                  {formatUSD(market.factors.whale.sellVolume)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-tertiary">Active Whales</span>
                <span className="font-mono text-text-primary">
                  {market.factors.whale.activeWhales} addresses
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-tertiary">Sell/Liquidity</span>
                <span className="font-mono text-text-primary">
                  {formatPercentage(market.factors.whale.sellRatio)}
                </span>
              </div>
            </div>
          </Card>

          {/* CEX Flow */}
          <Card>
            <h3 className="text-lg font-semibold text-text-primary mb-4">
              🔹 CEX Net Inflow
            </h3>
            <div className="mb-4">
              <ProgressBar
                value={market.factors.cex.score}
                max={market.factors.cex.maxScore}
                label="Score"
                color="risk-1"
              />
            </div>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-text-tertiary">Total Inflow</span>
                <span className="font-mono text-text-primary">
                  {formatUSD(market.factors.cex.totalInflow)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-tertiary">Total Outflow</span>
                <span className="font-mono text-text-primary">
                  {formatUSD(market.factors.cex.totalOutflow)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-tertiary">Net Inflow</span>
                <span className="font-mono text-risk-1">
                  +{formatUSD(market.factors.cex.netInflow)}
                </span>
              </div>
            </div>
          </Card>
        </div>
      </div>

      {/* Risk History Chart */}
      <Card>
        <h2 className="text-xl font-bold text-text-primary mb-4">
          Risk Score History (24h)
        </h2>
        <RiskTrendChart data={historyData} height={350} />
      </Card>

      {/* Recent Transactions */}
      <Card>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-text-primary">
            Recent Swaps
          </h2>
          <button className="text-sm text-primary hover:text-primary-hover">
            Export CSV
          </button>
        </div>
        <TransactionTable transactions={mockTransactions} />
      </Card>
    </div>
  );
};
