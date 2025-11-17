import React from 'react';
import { Link } from 'react-router-dom';
import { Card, RiskBadge, ProgressBar } from '@/components/common';
import { MarketData } from '@/types';
import { formatRelativeTime, formatNumber } from '@/utils/formatters';
import { ArrowRight, TrendingUp, TrendingDown } from 'lucide-react';

interface MarketCardProps {
  market: MarketData;
}

export const MarketCard: React.FC<MarketCardProps> = ({ market }) => {
  const riskChanged = market.previousRiskLevel !== undefined &&
    market.previousRiskLevel !== market.currentRiskLevel;

  const riskIncreased = riskChanged &&
    market.currentRiskLevel > (market.previousRiskLevel || 0);

  return (
    <Link to={`/markets/${market.marketId}`}>
      <Card hover gradient={market.currentRiskLevel >= 2}>
        <div className="flex items-start justify-between mb-4">
          <div>
            <h3 className="text-lg font-semibold text-text-primary mb-1">
              {market.label.replace(/_/g, ' ')}
            </h3>
            <p className="text-sm text-text-tertiary">
              Updated {formatRelativeTime(market.lastUpdated)}
            </p>
          </div>
          <RiskBadge level={market.currentRiskLevel} size="md" />
        </div>

        {/* Risk Score */}
        <div className="mb-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-text-secondary">Risk Score</span>
            <div className="flex items-center gap-2">
              <span className="text-xl font-bold font-mono text-text-primary">
                {formatNumber(market.riskScore, 0)}/100
              </span>
              {riskChanged && (
                riskIncreased ? (
                  <TrendingUp className="w-4 h-4 text-risk-3" />
                ) : (
                  <TrendingDown className="w-4 h-4 text-risk-0" />
                )
              )}
            </div>
          </div>
          <ProgressBar
            value={market.riskScore}
            max={100}
            color={`risk-${market.currentRiskLevel}`}
            showValue={false}
          />
        </div>

        {/* Factors Summary */}
        <div className="grid grid-cols-3 gap-3 mb-4">
          <div className="text-center p-2 bg-bg-dark rounded-lg">
            <div className="text-xs text-text-tertiary mb-1">DEX</div>
            <div className="text-sm font-semibold text-text-primary">
              {market.factors.dex.score}/{market.factors.dex.maxScore}
            </div>
          </div>
          <div className="text-center p-2 bg-bg-dark rounded-lg">
            <div className="text-xs text-text-tertiary mb-1">Whale</div>
            <div className="text-sm font-semibold text-text-primary">
              {market.factors.whale.score}/{market.factors.whale.maxScore}
            </div>
          </div>
          <div className="text-center p-2 bg-bg-dark rounded-lg">
            <div className="text-xs text-text-tertiary mb-1">CEX</div>
            <div className="text-sm font-semibold text-text-primary">
              {market.factors.cex.score}/{market.factors.cex.maxScore}
            </div>
          </div>
        </div>

        {/* View Details Link */}
        <div className="flex items-center justify-end text-primary text-sm font-medium group">
          <span>View Details</span>
          <ArrowRight className="w-4 h-4 ml-1 group-hover:translate-x-1 transition-transform" />
        </div>
      </Card>
    </Link>
  );
};
