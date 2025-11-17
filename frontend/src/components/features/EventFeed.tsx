import React from 'react';
import { Card } from '@/components/common';
import { AlertEvent } from '@/types';
import { formatRelativeTime, formatTxHash, getRiskLevelColor } from '@/utils/formatters';
import { Bell, TrendingUp, ExternalLink } from 'lucide-react';
import clsx from 'clsx';

interface EventFeedProps {
  events: AlertEvent[];
  limit?: number;
}

export const EventFeed: React.FC<EventFeedProps> = ({
  events,
  limit = 10,
}) => {
  const displayEvents = limit ? events.slice(0, limit) : events;

  const getEtherscanLink = (txHash: string) => {
    return `https://sepolia.etherscan.io/tx/${txHash}`;
  };

  return (
    <Card>
      <h3 className="text-lg font-semibold text-text-primary mb-4">
        Latest Events
      </h3>
      <div className="space-y-3">
        {displayEvents.map((event) => (
          <div
            key={event.id}
            className="p-3 bg-bg-dark rounded-lg border border-border hover:border-border-light transition-all"
          >
            <div className="flex items-start gap-3">
              <div className={clsx(
                'w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0',
                event.riskLevel >= 2 ? 'bg-risk-2/10' : 'bg-primary/10'
              )}>
                {event.riskLevel >= 2 ? (
                  <Bell className={clsx('w-4 h-4', getRiskLevelColor(event.riskLevel))} />
                ) : (
                  <TrendingUp className="w-4 h-4 text-primary" />
                )}
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between gap-2 mb-1">
                  <h4 className="text-sm font-medium text-text-primary">
                    {event.marketLabel.replace(/_/g, ' ')}
                  </h4>
                  <span className="text-xs text-text-tertiary whitespace-nowrap">
                    {formatRelativeTime(event.timestamp)}
                  </span>
                </div>

                <p className="text-sm text-text-secondary mb-2">
                  {event.message}
                </p>

                <div className="flex items-center gap-3 text-xs">
                  <span className={clsx('font-medium', getRiskLevelColor(event.previousLevel))}>
                    Level {event.previousLevel}
                  </span>
                  <span className="text-text-tertiary">→</span>
                  <span className={clsx('font-medium', getRiskLevelColor(event.riskLevel))}>
                    Level {event.riskLevel}
                  </span>
                  <a
                    href={getEtherscanLink(event.txHash)}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="ml-auto flex items-center gap-1 text-primary hover:text-primary-hover font-mono"
                  >
                    {formatTxHash(event.txHash)}
                    <ExternalLink className="w-3 h-3" />
                  </a>
                </div>
              </div>
            </div>
          </div>
        ))}

        {displayEvents.length === 0 && (
          <div className="text-center py-8 text-text-tertiary">
            No recent events
          </div>
        )}
      </div>
    </Card>
  );
};
