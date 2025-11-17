import { format } from 'date-fns';
import { RiskLevel } from '@/types';

/**
 * 格式化地址（缩短显示）
 */
export function formatAddress(address: string, startLength = 6, endLength = 4): string {
  if (!address) return '';
  if (address.length < startLength + endLength) return address;
  return `${address.slice(0, startLength)}...${address.slice(-endLength)}`;
}

/**
 * 格式化交易哈希
 */
export function formatTxHash(hash: string): string {
  return formatAddress(hash, 8, 6);
}

/**
 * 格式化数字（带千分位）
 */
export function formatNumber(num: number, decimals = 2): string {
  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(num);
}

/**
 * 格式化大数字（K、M、B）
 */
export function formatLargeNumber(num: number): string {
  if (num >= 1e9) return `${(num / 1e9).toFixed(2)}B`;
  if (num >= 1e6) return `${(num / 1e6).toFixed(2)}M`;
  if (num >= 1e3) return `${(num / 1e3).toFixed(2)}K`;
  return num.toFixed(2);
}

/**
 * 格式化金额（美元）
 */
export function formatUSD(amount: number): string {
  return `$${formatLargeNumber(amount)}`;
}

/**
 * 格式化百分比
 */
export function formatPercentage(value: number, decimals = 2): string {
  return `${(value * 100).toFixed(decimals)}%`;
}

/**
 * 格式化时间戳
 */
export function formatTimestamp(timestamp: number, formatStr = 'yyyy-MM-dd HH:mm:ss'): string {
  return format(new Date(timestamp * 1000), formatStr);
}

/**
 * 格式化相对时间
 */
export function formatRelativeTime(timestamp: number): string {
  const now = Date.now();
  const diff = now - timestamp * 1000;

  const seconds = Math.floor(diff / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);

  if (days > 0) return `${days}d ago`;
  if (hours > 0) return `${hours}h ago`;
  if (minutes > 0) return `${minutes}m ago`;
  return `${seconds}s ago`;
}

/**
 * 获取风险等级颜色类
 */
export function getRiskLevelColor(level: RiskLevel): string {
  const colors: Record<RiskLevel, string> = {
    0: 'text-risk-0',
    1: 'text-risk-1',
    2: 'text-risk-2',
    3: 'text-risk-3',
  };
  return colors[level];
}

/**
 * 获取风险等级背景色类
 */
export function getRiskLevelBgColor(level: RiskLevel): string {
  const colors: Record<RiskLevel, string> = {
    0: 'bg-risk-0/10',
    1: 'bg-risk-1/10',
    2: 'bg-risk-2/10',
    3: 'bg-risk-3/10',
  };
  return colors[level];
}

/**
 * 获取风险等级边框色类
 */
export function getRiskLevelBorderColor(level: RiskLevel): string {
  const colors: Record<RiskLevel, string> = {
    0: 'border-risk-0/20',
    1: 'border-risk-1/20',
    2: 'border-risk-2/20',
    3: 'border-risk-3/20',
  };
  return colors[level];
}

/**
 * 复制到剪贴板
 */
export async function copyToClipboard(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch (error) {
    console.error('Failed to copy:', error);
    return false;
  }
}

/**
 * 生成marketId（与合约保持一致）
 */
export function generateMarketId(label: string): string {
  // 简化版本，实际应该使用ethers的keccak256
  return label;
}
