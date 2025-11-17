# ChainMonitor Frontend

A professional DeFi risk monitoring dashboard built with React, TypeScript, and Tailwind CSS.

## Features

- **Real-time Risk Monitoring**: Live risk level updates from the blockchain
- **Multi-Factor Analysis**: DEX activity, whale behavior, and CEX flow tracking
- **Interactive Dashboards**: Beautiful data visualizations with Recharts
- **Alert Management**: Configure custom risk thresholds
- **Wallet Integration**: Connect with MetaMask for on-chain interactions
- **Responsive Design**: Optimized for desktop, tablet, and mobile

## Tech Stack

- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **Charts**: Recharts
- **Blockchain**: ethers.js v6
- **Routing**: React Router v6
- **Animations**: Framer Motion
- **Icons**: Lucide React

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- MetaMask or another Web3 wallet (for production features)

### Installation

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Configure environment variables:
```bash
cp .env.example .env
```

Edit `.env` and add your configuration:
```
VITE_CONTRACT_ADDRESS=0x... # Your deployed RiskMonitor contract
VITE_SEPOLIA_RPC_URL=https://sepolia.infura.io/v3/YOUR_KEY
VITE_MAINNET_RPC_URL=https://mainnet.infura.io/v3/YOUR_KEY
```

3. Start the development server:
```bash
npm run dev
```

The app will be available at `http://localhost:3000`

### Build for Production

```bash
npm run build
```

The production build will be in the `dist/` directory.

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── common/          # Reusable UI components
│   │   ├── charts/          # Chart components
│   │   ├── layout/          # Layout components (Header, Sidebar)
│   │   └── features/        # Feature-specific components
│   ├── pages/               # Page components
│   ├── hooks/               # Custom React hooks
│   ├── utils/               # Utility functions
│   ├── types/               # TypeScript type definitions
│   ├── styles/              # Global styles
│   ├── App.tsx              # Main app component
│   └── main.tsx             # Entry point
├── public/                  # Static assets
├── index.html               # HTML template
├── package.json
├── tsconfig.json
├── vite.config.ts
└── tailwind.config.js
```

## Key Components

### Pages
- **Dashboard**: Main overview with risk metrics and charts
- **MarketDetail**: Detailed analysis of a specific market
- **Alerts**: Alert configuration and history
- **Analytics**: Advanced analytics (coming soon)

### Hooks
- `useRiskData`: Fetch market risk data
- `useContract`: Interact with the RiskMonitor smart contract
- `useAlerts`: Manage alert events

### Components
- **RiskBadge**: Visual risk level indicator
- **MarketCard**: Market summary card
- **TransactionTable**: Transaction history table
- **RiskTrendChart**: Time-series risk chart
- **EventFeed**: Live event stream

## Design System

### Colors
- **Primary**: Blue (#3B82F6) - Main actions and highlights
- **Risk Levels**:
  - Level 0: Green (#10B981) - Normal
  - Level 1: Yellow (#F59E0B) - Caution
  - Level 2: Orange (#F97316) - Warning
  - Level 3: Red (#EF4444) - Critical

### Typography
- **Headings**: Inter (Bold, Semi-Bold)
- **Body**: Inter (Regular, Medium)
- **Code/Data**: JetBrains Mono

## Development

### Code Style
- TypeScript strict mode enabled
- ESLint for code quality
- Prettier for formatting (recommended)

### Key Scripts
```bash
npm run dev      # Start development server
npm run build    # Build for production
npm run preview  # Preview production build
npm run lint     # Run ESLint
```

## Integration with Backend

The frontend is designed to work with:
1. **Smart Contract**: RiskMonitor.sol on Sepolia testnet
2. **Backend API** (optional): Can be extended to use the Python backend for historical data

Currently, the app uses mock data for demonstration. To integrate real data:

1. Update `CONTRACT_ADDRESS` in `.env`
2. Implement API endpoints in the backend
3. Update hooks to fetch from real sources

## Wallet Connection

Click "Connect Wallet" in the header to connect MetaMask. Required for:
- Viewing your alert configurations
- Setting custom alert thresholds
- Interacting with the smart contract

## Browser Support

- Chrome/Edge (recommended)
- Firefox
- Safari
- Brave

## Performance

- Lazy loading for routes
- Memoized components
- Optimized re-renders
- Code splitting with Vite

## Future Enhancements

- [ ] Real-time WebSocket updates
- [ ] Multi-chain support
- [ ] Email/Telegram notifications
- [ ] Export data to CSV/PDF
- [ ] Advanced analytics dashboard
- [ ] Mobile app (React Native)
- [ ] Dark/Light theme toggle
- [ ] Multi-language support

## Contributing

Contributions are welcome! Please follow the existing code style and component patterns.

## License

MIT License - see LICENSE file for details

## Support

For issues and questions, please open an issue on GitHub.
