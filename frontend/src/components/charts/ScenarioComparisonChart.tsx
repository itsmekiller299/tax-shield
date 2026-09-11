'use client';

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { cn } from '@/lib/utils';

interface ScenarioData {
  name: string;
  estimated_income: number;
  estimated_deductions: number;
  estimated_liability: number;
}

interface ScenarioComparisonChartProps {
  scenarios: ScenarioData[];
}

export function ScenarioComparisonChart({ scenarios }: ScenarioComparisonChartProps) {
  const chartData = scenarios.map((s) => ({
    name: s.name,
    Income: s.estimated_income,
    Deductions: s.estimated_deductions,
    Liability: s.estimated_liability,
  }));

  const COLORS = {
    Income: '#0ea5e9',
    Deductions: '#22c55e',
    Liability: '#ef4444',
  };

  return (
    <div className="card p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Scenario Comparison</h3>
      <div className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" vertical={false} />
            <XAxis type="number" tickFormatter={(value) => `₹${(value / 100000).toFixed(1)}L`} />
            <YAxis dataKey="name" type="category" width={100} />
            <Tooltip
              formatter={(value: number) => [`₹${value.toLocaleString('en-IN')}`, 'Amount']}
              contentStyle={{
                backgroundColor: 'white',
                border: '1px solid #e5e7eb',
                borderRadius: '8px',
                boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
              }}
            />
            <Legend />
            {Object.entries(COLORS).map(([key, color]) => (
              <Bar
                key={key}
                dataKey={key}
                fill={color}
                radius={[0, 4, 4, 0]}
                maxBarSize={40}
              />
            ))}
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="mt-4 flex flex-wrap gap-4 justify-center">
        {Object.entries(COLORS).map(([key, color]) => (
          <div key={key} className="flex items-center gap-2">
            <span className="w-3 h-3 rounded" style={{ backgroundColor: color }} />
            <span className="text-sm text-gray-600 capitalize">{key.toLowerCase()}</span>
          </div>
        ))}
      </div>
    </div>
  );
}