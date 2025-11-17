import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Activity, Search, Wallet } from 'lucide-react';
import { Button } from '@/components/common';
import clsx from 'clsx';

const navigation = [
  { name: 'Dashboard', path: '/' },
  { name: 'Markets', path: '/markets' },
  { name: 'Alerts', path: '/alerts' },
  { name: 'Analytics', path: '/analytics' },
];

export const Header: React.FC = () => {
  const location = useLocation();

  return (
    <header className="sticky top-0 z-50 bg-bg-surface/95 backdrop-blur-sm border-b border-border">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-3 group">
            <div className="w-10 h-10 bg-gradient-to-br from-primary to-purple-500 rounded-lg flex items-center justify-center group-hover:scale-110 transition-transform">
              <Activity className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-gradient">ChainMonitor</h1>
              <p className="text-xs text-text-tertiary">DeFi Risk Monitor</p>
            </div>
          </Link>

          {/* Navigation */}
          <nav className="hidden md:flex items-center gap-1">
            {navigation.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={clsx(
                  'px-4 py-2 rounded-lg text-sm font-medium transition-all',
                  location.pathname === item.path
                    ? 'bg-primary/10 text-primary'
                    : 'text-text-secondary hover:text-text-primary hover:bg-bg-light'
                )}
              >
                {item.name}
              </Link>
            ))}
          </nav>

          {/* Right Section */}
          <div className="flex items-center gap-3">
            {/* Search */}
            <div className="hidden lg:flex items-center gap-2 bg-bg-light rounded-lg px-4 py-2 border border-border focus-within:border-primary transition-colors">
              <Search className="w-4 h-4 text-text-tertiary" />
              <input
                type="text"
                placeholder="Search tx hash..."
                className="bg-transparent border-none outline-none text-sm text-text-primary placeholder:text-text-tertiary w-48"
              />
            </div>

            {/* Connect Wallet Button */}
            <Button variant="primary" size="sm">
              <Wallet className="w-4 h-4" />
              Connect Wallet
            </Button>
          </div>
        </div>
      </div>
    </header>
  );
};
