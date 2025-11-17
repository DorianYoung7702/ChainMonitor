import React from 'react';
import { Card, RiskBadge } from '@/components/common';
import { RiskLevel, RiskLevelDescriptions } from '@/types';
import { formatRelativeTime } from '@/utils/formatters';
import { Activity } from 'lucide-react';

interface RiskOverviewProps {
  currentLevel: RiskLevel;
  lastUpdated: number;
  totalMarkets: number;
  marketsAtRisk: number;
}

export const RiskOverview: React.FC<RiskOverviewProps> = ({
  currentLevel,
  lastUpdated,
  totalMarkets,
  marketsAtRisk,
}) => {
  return (
    <Card gradient={currentLevel >= 2} className="relative overflow-hidden">
      {/* Animated background */}
      {currentLevel >= 2 && (
        <div className="absolute inset-0 animate-pulse-slow opacity-10">
          <div className={`absolute inset-0 bg-risk-${currentLevel}`} />
        </div>
      )}

      <div className="relative z-10">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h2 className="text-2xl font-bold text-text-primary mb-2">
              Global Risk Status
            </h2>
            <p className="text-text-secondary">
              {RiskLevelDescriptions[currentLevel]}
            </p>
          </div>
          <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-bg-dark/50">
            <Activity className="w-4 h-4 text-primary animate-pulse" />
            <span className="text-xs text-text-tertiary">
              Live
            </span>
          </div>
        </div>

        <div className="flex items-center gap-6 mb-6">
          <RiskBadge level={currentLevel} size="lg" />
          <div className="text-sm text-text-tertiary">
            Updated {formatRelativeTime(lastUpdated)}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="p-4 bg-bg-dark rounded-lg">
            <div className="text-sm text-text-tertiary mb-1">
              Total Markets
            </div>
            <div className="text-2xl font-bold text-text-primary">
              {totalMarkets}
            </div>
          </div>
          <div className="p-4 bg-bg-dark rounded-lg">
            <div className="text-sm text-text-tertiary mb-1">
              Markets at Risk
            </div>
            <div className="text-2xl font-bold text-risk-2">
              {marketsAtRisk}
            </div>
          </div>
        </div>
      </div>
    </Card>
  );
};
