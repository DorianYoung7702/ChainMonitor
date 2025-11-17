import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Header, Sidebar } from './components/layout';
import { Dashboard } from './pages/Dashboard';
import { MarketDetail } from './pages/MarketDetail';
import { Alerts } from './pages/Alerts';
import { Analytics } from './pages/Analytics';
import { useAllMarkets } from './hooks/useRiskData';
import { useAlerts } from './hooks/useAlerts';

function App() {
  const { markets } = useAllMarkets();
  const { alerts } = useAlerts();
  const recentAlerts = alerts.filter(
    (a) => a.timestamp > Math.floor(Date.now() / 1000) - 3600
  ).length;

  return (
    <Router>
      <div className="min-h-screen bg-bg-dark">
        <Header />
        <div className="flex">
          <Sidebar markets={markets} recentAlerts={recentAlerts} />
          <main className="flex-1 p-6 lg:p-8">
            <div className="max-w-7xl mx-auto">
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/markets" element={<Dashboard />} />
                <Route path="/markets/:marketId" element={<MarketDetail />} />
                <Route path="/alerts" element={<Alerts />} />
                <Route path="/analytics" element={<Analytics />} />
              </Routes>
            </div>
          </main>
        </div>
      </div>
    </Router>
  );
}

export default App;
