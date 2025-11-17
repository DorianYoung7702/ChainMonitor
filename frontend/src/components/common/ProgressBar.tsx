import React from 'react';
import { motion } from 'framer-motion';
import clsx from 'clsx';

interface ProgressBarProps {
  value: number;
  max: number;
  label?: string;
  showValue?: boolean;
  color?: 'primary' | 'risk-0' | 'risk-1' | 'risk-2' | 'risk-3';
  height?: 'sm' | 'md' | 'lg';
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  value,
  max,
  label,
  showValue = true,
  color = 'primary',
  height = 'md',
}) => {
  const percentage = Math.min((value / max) * 100, 100);

  const heightClasses = {
    sm: 'h-1.5',
    md: 'h-2.5',
    lg: 'h-4',
  };

  const colorClasses = {
    primary: 'bg-primary',
    'risk-0': 'bg-risk-0',
    'risk-1': 'bg-risk-1',
    'risk-2': 'bg-risk-2',
    'risk-3': 'bg-risk-3',
  };

  return (
    <div className="w-full">
      {(label || showValue) && (
        <div className="flex justify-between items-center mb-2">
          {label && <span className="text-sm text-text-secondary">{label}</span>}
          {showValue && (
            <span className="text-sm font-mono text-text-primary">
              {value}/{max}
            </span>
          )}
        </div>
      )}
      <div className={clsx('w-full bg-bg-light rounded-full overflow-hidden', heightClasses[height])}>
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${percentage}%` }}
          transition={{ duration: 0.5, ease: 'easeOut' }}
          className={clsx('h-full rounded-full', colorClasses[color])}
        />
      </div>
    </div>
  );
};
