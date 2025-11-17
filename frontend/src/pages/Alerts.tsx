import React, { useState } from 'react';
import { Card, Button, RiskBadge } from '@/components/common';
import { EventFeed } from '@/components/features';
import { useAlerts } from '@/hooks/useAlerts';
import { useAllMarkets } from '@/hooks/useRiskData';
import { RiskLevel } from '@/types';
import { Bell, Settings } from 'lucide-react';

export const Alerts: React.FC = () => {
  const { alerts } = useAlerts();
  const { markets } = useAllMarkets();
  const [threshold, setThreshold] = useState<RiskLevel>(2);
  const [enabled, setEnabled] = useState(true);
  const [selectedMarket, setSelectedMarket] = useState('UNISWAP_USDC_WETH');

  const handleSaveConfig = () => {
    // In production, this would call the smart contract
    console.log('Saving alert config:', {
      market: selectedMarket,
      threshold,
      enabled,
    });
    alert('Alert configuration saved! (Demo mode - requires wallet connection in production)');
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-text-primary">Alert Management</h1>
          <p className="text-text-tertiary mt-2">
            Configure your risk alert preferences
          </p>
        </div>
        <div className="flex items-center gap-2 px-4 py-2 bg-bg-surface rounded-lg border border-border">
          <Bell className="w-5 h-5 text-primary" />
          <span className="text-text-secondary">
            {alerts.length} total alerts
          </span>
        </div>
      </div>

      {/* Alert Configuration */}
      <Card>
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
            <Settings className="w-5 h-5 text-primary" />
          </div>
          <h2 className="text-xl font-semibold text-text-primary">
            Alert Configuration
          </h2>
        </div>

        <div className="space-y-6">
          {/* Market Selection */}
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-2">
              Market
            </label>
            <select
              value={selectedMarket}
              onChange={(e) => setSelectedMarket(e.target.value)}
              className="input w-full md:w-96"
            >
              {markets.map((market) => (
                <option key={market.marketId} value={market.marketId}>
                  {market.label.replace(/_/g, ' ')}
                </option>
              ))}
            </select>
          </div>

          {/* Threshold Slider */}
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-3">
              Risk Threshold
            </label>
            <p className="text-sm text-text-tertiary mb-4">
              Trigger alert when risk level reaches or exceeds:
            </p>

            <div className="mb-4">
              <input
                type="range"
                min="0"
                max="3"
                step="1"
                value={threshold}
                onChange={(e) => setThreshold(Number(e.target.value) as RiskLevel)}
                className="w-full h-2 bg-bg-light rounded-lg appearance-none cursor-pointer"
                style={{
                  background: `linear-gradient(to right,
                    #10B981 0%,
                    #F59E0B 33%,
                    #F97316 66%,
                    #EF4444 100%)`
                }}
              />
              <div className="flex justify-between mt-2 text-xs text-text-tertiary">
                <span>Level 0</span>
                <span>Level 1</span>
                <span>Level 2</span>
                <span>Level 3</span>
              </div>
            </div>

            <div className="flex items-center justify-center p-4 bg-bg-dark rounded-lg">
              <RiskBadge level={threshold} size="lg" />
            </div>
          </div>

          {/* Enable/Disable */}
          <div className="flex items-center justify-between p-4 bg-bg-dark rounded-lg">
            <div>
              <h3 className="text-sm font-medium text-text-primary mb-1">
                Enable Automatic Alerts
              </h3>
              <p className="text-xs text-text-tertiary">
                Receive notifications when risk threshold is reached
              </p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={enabled}
                onChange={(e) => setEnabled(e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-bg-light peer-focus:ring-2 peer-focus:ring-primary rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
            </label>
          </div>

          {/* Email Notifications (future feature) */}
          <div className="flex items-center justify-between p-4 bg-bg-dark rounded-lg opacity-50">
            <div>
              <h3 className="text-sm font-medium text-text-primary mb-1">
                Email Notifications
              </h3>
              <p className="text-xs text-text-tertiary">
                Coming soon - receive alerts via email
              </p>
            </div>
            <label className="relative inline-flex items-center cursor-not-allowed">
              <input
                type="checkbox"
                disabled
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-bg-light rounded-full peer"></div>
            </label>
          </div>

          {/* Save Button */}
          <div className="flex justify-end gap-3 pt-4 border-t border-border">
            <Button variant="secondary" onClick={() => {
              setThreshold(2);
              setEnabled(true);
            }}>
              Reset to Defaults
            </Button>
            <Button variant="primary" onClick={handleSaveConfig}>
              Save Configuration
            </Button>
          </div>
        </div>
      </Card>

      {/* Alert History */}
      <EventFeed events={alerts} limit={50} />

      {/* Info Card */}
      <Card className="bg-primary/5 border-primary/20">
        <h3 className="text-sm font-semibold text-primary mb-2">
          ℹ️ About Alerts
        </h3>
        <p className="text-sm text-text-secondary leading-relaxed">
          Alerts are triggered on-chain when the risk level reaches your configured threshold.
          To receive alerts, you need to connect your wallet and save your preferences to the smart contract.
          Gas fees apply for updating your configuration on Sepolia testnet.
        </p>
      </Card>
    </div>
  );
};
