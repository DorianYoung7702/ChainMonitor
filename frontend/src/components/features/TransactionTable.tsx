import React from 'react';
import { Transaction } from '@/types';
import { formatTimestamp, formatTxHash, formatLargeNumber } from '@/utils/formatters';
import { ExternalLink, ArrowDownLeft, ArrowUpRight } from 'lucide-react';
import clsx from 'clsx';

interface TransactionTableProps {
  transactions: Transaction[];
  limit?: number;
}

export const TransactionTable: React.FC<TransactionTableProps> = ({
  transactions,
  limit = 20,
}) => {
  const displayTxs = limit ? transactions.slice(0, limit) : transactions;

  const getEtherscanLink = (txHash: string) => {
    return `https://etherscan.io/tx/${txHash}`;
  };

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="border-b border-border">
            <th className="text-left py-3 px-4 text-sm font-semibold text-text-tertiary">
              Time
            </th>
            <th className="text-left py-3 px-4 text-sm font-semibold text-text-tertiary">
              Block
            </th>
            <th className="text-left py-3 px-4 text-sm font-semibold text-text-tertiary">
              Transaction
            </th>
            <th className="text-left py-3 px-4 text-sm font-semibold text-text-tertiary">
              Type
            </th>
            <th className="text-right py-3 px-4 text-sm font-semibold text-text-tertiary">
              Amount
            </th>
          </tr>
        </thead>
        <tbody>
          {displayTxs.map((tx, index) => (
            <tr
              key={tx.txHash}
              className={clsx(
                'border-b border-border/50 hover:bg-bg-light transition-colors',
                index % 2 === 0 ? 'bg-bg-surface' : 'bg-bg-dark/50'
              )}
            >
              <td className="py-3 px-4 text-sm text-text-secondary">
                {formatTimestamp(tx.timestamp, 'HH:mm:ss')}
              </td>
              <td className="py-3 px-4 text-sm font-mono text-text-secondary">
                {tx.blockNumber.toLocaleString()}
              </td>
              <td className="py-3 px-4">
                <a
                  href={getEtherscanLink(tx.txHash)}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-2 text-sm font-mono text-primary hover:text-primary-hover"
                >
                  {formatTxHash(tx.txHash)}
                  <ExternalLink className="w-3 h-3" />
                </a>
              </td>
              <td className="py-3 px-4">
                <span
                  className={clsx(
                    'inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium',
                    tx.type === 'buy'
                      ? 'bg-risk-0/10 text-risk-0'
                      : 'bg-risk-3/10 text-risk-3'
                  )}
                >
                  {tx.type === 'buy' ? (
                    <ArrowUpRight className="w-3 h-3" />
                  ) : (
                    <ArrowDownLeft className="w-3 h-3" />
                  )}
                  {tx.type.toUpperCase()}
                </span>
              </td>
              <td className="py-3 px-4 text-right text-sm font-mono text-text-primary">
                {formatLargeNumber(parseFloat(tx.amountOut))} {tx.tokenOut}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {displayTxs.length === 0 && (
        <div className="text-center py-12 text-text-tertiary">
          No transactions found
        </div>
      )}
    </div>
  );
};
