import React from 'react';
import { Loader2 } from 'lucide-react';
import clsx from 'clsx';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  text?: string;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = 'md',
  className,
  text,
}) => {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
  };

  return (
    <div className={clsx('flex flex-col items-center justify-center gap-3', className)}>
      <Loader2 className={clsx(sizeClasses[size], 'animate-spin text-primary')} />
      {text && <p className="text-text-secondary text-sm">{text}</p>}
    </div>
  );
};

export const FullPageLoader: React.FC = () => {
  return (
    <div className="min-h-screen flex items-center justify-center bg-bg-dark">
      <LoadingSpinner size="lg" text="Loading ChainMonitor..." />
    </div>
  );
};
