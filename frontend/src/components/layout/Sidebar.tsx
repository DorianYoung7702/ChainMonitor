import React from 'react';
import { Link } from 'react-router-dom';
import { TrendingUp, Bell, ChevronRight } from 'lucide-react';
import { Card, RiskBadge } from '@/components/common';
import { MarketData } from '@/types';

interface SidebarProps {
  markets?: MarketData[];
  recentAlerts?: number;
}

export const Sidebar: React.FC<SidebarProps> = ({
  markets = [],
  recentAlerts = 0,
}) => {
  return (
    <aside className="hidden lg:block w-64 min-h-screen bg-bg-surface border-r border-border p-4">
      {/* Quick Access */}
      <div className="mb-6">
        <h3 className="text-sm font-semibold text-text-tertiary uppercase tracking-wider mb-3">
          Quick Access
        </h3>
        <div className="space-y-2">
          <Link
            to="/markets"
            className="flex items-center justify-between p-3 rounded-lg bg-bg-light hover:bg-bg-dark border border-border hover:border-border-light transition-all group"
          >
            <div className="flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-primary" />
              <span className="text-sm text-text-secondary group-hover:text-text-primary">
                Markets
              </span>
            </div>
            <ChevronRight className="w-4 h-4 text-text-tertiary" />
          </Link>

          <Link
            to="/alerts"
            className="flex items-center justify-between p-3 rounded-lg bg-bg-light hover:bg-bg-dark border border-border hover:border-border-light transition-all group"
          >
            <div className="flex items-center gap-2">
              <Bell className="w-4 h-4 text-risk-2" />
              <span className="text-sm text-text-secondary group-hover:text-text-primary">
                Alerts
              </span>
            </div>
            {recentAlerts > 0 && (
              <span className="bg-risk-2 text-white text-xs px-2 py-0.5 rounded-full">
                {recentAlerts}
              </span>
            )}
          </Link>
        </div>
      </div>

      {/* Monitored Markets */}
      <div>
        <h3 className="text-sm font-semibold text-text-tertiary uppercase tracking-wider mb-3">
          Monitored Markets
        </h3>
        <div className="space-y-3">
          {markets.length > 0 ? (
            markets.map((market) => (
              <Link
                key={market.marketId}
                to={`/markets/${market.marketId}`}
                className="block"
              >
                <div className="p-3 rounded-lg bg-bg-light hover:bg-bg-dark border border-border hover:border-border-light transition-all">
                  <div className="flex items-start justify-between mb-2">
                    <span className="text-sm font-medium text-text-primary">
                      {market.label.replace('_', ' ')}
                    </span>
                  </div>
                  <RiskBadge level={market.currentRiskLevel} size="sm" />
                  <div className="mt-2 text-xs text-text-tertiary">
                    Score: {market.riskScore}/100
                  </div>
                </div>
              </Link>
            ))
          ) : (
            <div className="p-4 text-center text-sm text-text-tertiary">
              No markets configured
            </div>
          )}
        </div>
      </div>
    </aside>
  );
};
