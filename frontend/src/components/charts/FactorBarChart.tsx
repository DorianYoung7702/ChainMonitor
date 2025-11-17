import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';

interface FactorData {
  name: string;
  score: number;
  maxScore: number;
}

interface FactorBarChartProps {
  dexScore: number;
  whaleScore: number;
  cexScore: number;
  height?: number;
}

export const FactorBarChart: React.FC<FactorBarChartProps> = ({
  dexScore,
  whaleScore,
  cexScore,
  height = 250,
}) => {
  const data: FactorData[] = [
    { name: 'DEX Activity', score: dexScore, maxScore: 40 },
    { name: 'Whale Pressure', score: whaleScore, maxScore: 35 },
    { name: 'CEX Inflow', score: cexScore, maxScore: 30 },
  ];

  const colors = ['#3B82F6', '#8B5CF6', '#EC4899'];

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.5} />
        <XAxis
          dataKey="name"
          stroke="#9CA3AF"
          tick={{ fill: '#9CA3AF', fontSize: 12 }}
        />
        <YAxis
          stroke="#9CA3AF"
          tick={{ fill: '#9CA3AF', fontSize: 12 }}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: '#1F2937',
            border: '1px solid #374151',
            borderRadius: '8px',
            color: '#F9FAFB',
          }}
          formatter={(value: number, name: string, props: any) => [
            `${value}/${props.payload.maxScore}`,
            'Score',
          ]}
        />
        <Bar dataKey="score" radius={[8, 8, 0, 0]}>
          {data.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={colors[index]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
};
