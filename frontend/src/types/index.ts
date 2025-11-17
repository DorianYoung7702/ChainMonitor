// 风险等级类型
export type RiskLevel = 0 | 1 | 2 | 3;

// 风险等级标签
export const RiskLevelLabels: Record<RiskLevel, string> = {
  0: 'NORMAL',
  1: 'CAUTION',
  2: 'WARNING',
  3: 'CRITICAL',
};

// 风险等级描述
export const RiskLevelDescriptions: Record<RiskLevel, string> = {
  0: 'Market conditions are stable',
  1: 'Elevated activity detected',
  2: 'Significant risk indicators present',
  3: 'High risk - immediate attention required',
};

// 市场数据接口
export interface MarketData {
  marketId: string;
  label: string;
  currentRiskLevel: RiskLevel;
  previousRiskLevel?: RiskLevel;
  lastUpdated: number;
  riskScore: number;
  factors: RiskFactors;
}

// 风险因子详情
export interface RiskFactors {
  dex: {
    score: number;
    maxScore: number;
    volumeRatio: number;
    txCount: number;
    liquidity: number;
  };
  whale: {
    score: number;
    maxScore: number;
    sellVolume: number;
    activeWhales: number;
    sellRatio: number;
  };
  cex: {
    score: number;
    maxScore: number;
    totalInflow: number;
    totalOutflow: number;
    netInflow: number;
    netInflowRatio: number;
  };
}

// 交易数据
export interface Transaction {
  timestamp: number;
  blockNumber: number;
  txHash: string;
  tokenIn: string;
  tokenOut: string;
  amountIn: string;
  amountOut: string;
  type: 'buy' | 'sell';
}

// 风险历史记录
export interface RiskHistory {
  timestamp: number;
  riskLevel: RiskLevel;
  riskScore: number;
  txHash?: string;
}

// 用户告警配置
export interface UserAlertConfig {
  marketId: string;
  threshold: RiskLevel;
  enabled: boolean;
  emailNotification?: boolean;
}

// 告警事件
export interface AlertEvent {
  id: string;
  timestamp: number;
  marketId: string;
  marketLabel: string;
  riskLevel: RiskLevel;
  previousLevel: RiskLevel;
  txHash: string;
  message: string;
}

// 链上事件
export interface RiskUpdatedEvent {
  marketId: string;
  newLevel: RiskLevel;
  blockNumber: number;
  transactionHash: string;
  timestamp: number;
}

// 市场配置
export interface MarketConfig {
  label: string;
  type: 'dex_pool' | 'whale' | 'exchange';
  address: string;
  description: string;
}

// 图表数据点
export interface ChartDataPoint {
  timestamp: number;
  value: number;
  label?: string;
}

// 时间范围选项
export type TimeRange = '1h' | '24h' | '7d' | '30d' | 'all';

// 合约配置
export interface ContractConfig {
  address: string;
  chainId: number;
  rpcUrl: string;
}
