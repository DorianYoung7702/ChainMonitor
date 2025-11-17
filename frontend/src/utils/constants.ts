import { MarketConfig } from '@/types';

// 合约配置
export const CONTRACT_ADDRESS = import.meta.env.VITE_CONTRACT_ADDRESS || '0x...';
export const SEPOLIA_CHAIN_ID = 11155111;
export const MAINNET_CHAIN_ID = 1;

// RPC配置
export const SEPOLIA_RPC_URL = import.meta.env.VITE_SEPOLIA_RPC_URL || 'https://sepolia.infura.io/v3/YOUR_KEY';
export const MAINNET_RPC_URL = import.meta.env.VITE_MAINNET_RPC_URL || 'https://mainnet.infura.io/v3/YOUR_KEY';

// 市场配置
export const MARKETS: MarketConfig[] = [
  {
    label: 'UNISWAP_USDC_WETH',
    type: 'dex_pool',
    address: '0xB4e16d0168e52d35CaCD2c6185b44281Ec28C9Dc',
    description: 'Uniswap V2 USDC/WETH Pool',
  },
];

// 风险评分阈值
export const RISK_THRESHOLDS = {
  0: { min: 0, max: 19 },
  1: { min: 20, max: 39 },
  2: { min: 40, max: 69 },
  3: { min: 70, max: 100 },
};

// 刷新间隔（毫秒）
export const REFRESH_INTERVALS = {
  REAL_TIME: 5000,      // 5秒
  MARKET_DATA: 30000,   // 30秒
  HISTORICAL: 60000,    // 1分钟
};

// 时间格式
export const DATE_FORMATS = {
  FULL: 'yyyy-MM-dd HH:mm:ss',
  SHORT: 'HH:mm:ss',
  DATE_ONLY: 'yyyy-MM-dd',
};

// Etherscan链接
export const ETHERSCAN_BASE_URL = {
  mainnet: 'https://etherscan.io',
  sepolia: 'https://sepolia.etherscan.io',
};

// 数据展示限制
export const DISPLAY_LIMITS = {
  RECENT_TRANSACTIONS: 20,
  ALERT_HISTORY: 50,
  CHART_DATA_POINTS: 100,
};
