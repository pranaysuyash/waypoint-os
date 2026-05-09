'use client';

import { useEffect, useState } from 'react';
import {
  ResponsiveContainer,
  ComposedChart,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Bar,
  Line,
} from 'recharts';

type RevenuePoint = {
  month: string;
  inquiries: number;
  booked: number;
  revenue: number;
};

type RevenueChartProps = {
  data: RevenuePoint[];
};

const CURRENCY_FORMATTER = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
  maximumFractionDigits: 0,
});

export function RevenueChart({ data }: RevenueChartProps) {
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  return (
    <div className='rounded-xl border border-[#1c2128] bg-[#0f1115] p-5'>
      <div className='mb-4 flex items-center justify-between'>
        <h2 className='text-base font-semibold text-[#e6edf3]'>Monthly Trend</h2>
        <div className='flex items-center gap-4 text-xs text-[#8b949e]'>
          <span className='inline-flex items-center gap-1.5'>
            <span className='size-2 rounded-full bg-[#58a6ff]' aria-hidden='true' />
            Revenue
          </span>
          <span className='inline-flex items-center gap-1.5'>
            <span className='size-2 rounded-full bg-[#3fb950]' aria-hidden='true' />
            Booked
          </span>
        </div>
      </div>

      {data.length === 0 ? (
        <p className='py-10 text-center text-sm text-[#8b949e]'>No revenue data available.</p>
      ) : (
        <>
          <div className='h-[260px] w-full'>
            {isMounted ? (
              <ResponsiveContainer width='100%' height='100%'>
                <ComposedChart data={data}>
                  <CartesianGrid stroke='#30363d' strokeDasharray='3 3' vertical={false} />
                  <XAxis dataKey='month' tick={{ fill: '#8b949e', fontSize: 12 }} axisLine={{ stroke: '#30363d' }} tickLine={false} />
                  <YAxis
                    yAxisId='revenue'
                    tick={{ fill: '#8b949e', fontSize: 12 }}
                    axisLine={{ stroke: '#30363d' }}
                    tickLine={false}
                    tickFormatter={(value: number) => `$${Math.round(value / 1000)}k`}
                  />
                  <YAxis
                    yAxisId='booked'
                    orientation='right'
                    tick={{ fill: '#8b949e', fontSize: 12 }}
                    axisLine={{ stroke: '#30363d' }}
                    tickLine={false}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#161b22',
                      border: '1px solid #30363d',
                      borderRadius: '0.5rem',
                      color: '#e6edf3',
                    }}
                    formatter={(value, name) => {
                      const numericValue = typeof value === 'number' ? value : Number(value ?? 0);

                      if (name === 'revenue') {
                        return [CURRENCY_FORMATTER.format(numericValue), 'Revenue'];
                      }
                      return [numericValue, 'Booked'];
                    }}
                  />
                  <Bar yAxisId='revenue' dataKey='revenue' fill='#58a6ff' radius={[6, 6, 0, 0]} />
                  <Line
                    yAxisId='booked'
                    type='monotone'
                    dataKey='booked'
                    stroke='#3fb950'
                    strokeWidth={2}
                    dot={{ r: 3, fill: '#3fb950', stroke: '#3fb950' }}
                    activeDot={{ r: 5 }}
                  />
                </ComposedChart>
              </ResponsiveContainer>
            ) : (
              <div className='flex h-full items-center justify-center text-sm text-[#8b949e]'>
                Loading chart…
              </div>
            )}
          </div>

          <ul className='sr-only' aria-label='Months shown'>
            {data.map((point) => (
              <li key={point.month}>{point.month}</li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}
