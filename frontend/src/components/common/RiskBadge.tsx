import React from 'react';
import clsx from 'clsx';
import { RiskLevel, RiskLevelLabels } from '@/types';
import { AlertCircle, AlertTriangle, Info, CheckCircle } from 'lucide-react';

interface RiskBadgeProps {
  level: RiskLevel;
  showIcon?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

const icons = {
  0: CheckCircle,
  1: Info,
  2: AlertTriangle,
  3: AlertCircle,
};

export const RiskBadge: React.FC<RiskBadgeProps> = ({
  level,
  showIcon = true,
  size = 'md',
}) => {
  const Icon = icons[level];

  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-sm px-3 py-1',
    lg: 'text-base px-4 py-1.5',
  };

  const iconSizes = {
    sm: 'w-3 h-3',
    md: 'w-4 h-4',
    lg: 'w-5 h-5',
  };

  return (
    <span
      className={clsx(
        'badge',
        `risk-badge-${level}`,
        sizeClasses[size],
        'inline-flex items-center gap-1.5'
      )}
    >
      {showIcon && <Icon className={iconSizes[size]} />}
      <span className="font-semibold">Level {level}</span>
      <span className="opacity-80">- {RiskLevelLabels[level]}</span>
    </span>
  );
};
