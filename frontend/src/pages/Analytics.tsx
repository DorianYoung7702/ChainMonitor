import React from 'react';
import { Card } from '@/components/common';
import { BarChart } from 'lucide-react';

export const Analytics: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-text-primary">Analytics</h1>
        <p className="text-text-tertiary mt-2">
          Advanced analytics and insights coming soon
        </p>
      </div>

      <Card className="text-center py-20">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-primary/10 rounded-full mb-4">
          <BarChart className="w-8 h-8 text-primary" />
        </div>
        <h2 className="text-2xl font-bold text-text-primary mb-2">
          Advanced Analytics
        </h2>
        <p className="text-text-secondary max-w-md mx-auto">
          This section will feature historical analysis, correlation studies,
          multi-market comparisons, and predictive insights based on on-chain data.
        </p>
      </Card>
    </div>
  );
};
