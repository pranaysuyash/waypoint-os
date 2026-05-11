'use client';

import { useSyncExternalStore, useCallback } from 'react';
import dynamic from 'next/dynamic';

export interface PipelineStage {
  stageId: string;
  stageName: string;
  tripCount: number;
}

interface ChartData {
  name: string;
  trips: number;
  conversion: string;
}

const ResponsiveContainer = dynamic(() => import('recharts').then((mod) => mod.ResponsiveContainer), { ssr: false });
const BarChart = dynamic(() => import('recharts').then((mod) => mod.BarChart), { ssr: false });
const Bar = dynamic(() => import('recharts').then((mod) => mod.Bar), { ssr: false });
const XAxis = dynamic(() => import('recharts').then((mod) => mod.XAxis), { ssr: false });
const YAxis = dynamic(() => import('recharts').then((mod) => mod.YAxis), { ssr: false });
const CartesianGrid = dynamic(() => import('recharts').then((mod) => mod.CartesianGrid), { ssr: false });
const Tooltip = dynamic(() => import('recharts').then((mod) => mod.Tooltip), { ssr: false });

function useHydrated(): boolean {
  return useSyncExternalStore(
    useCallback((onStoreChange) => {
      const timer = setTimeout(onStoreChange, 0);
      return () => clearTimeout(timer);
    }, []),
    () => true,
    () => false
  );
}

export function PipelineFunnel({ data }: { data: PipelineStage[] }) {
  const isMounted = useHydrated();

  if (data.length === 0) {
    return (
      <div className='rounded-xl border border-[#1c2128] bg-[#0f1115] p-5'>
        <h2 className='text-base font-semibold text-[#e6edf3] mb-4'>Conversion Funnel</h2>
        <p className='text-sm text-[#8b949e]'>No pipeline data available.</p>
      </div>
    );
  }

  const maxTrips = Math.max(...data.map(d => d.tripCount));

  const chartData: ChartData[] = data.map((stage, index) => ({
    name: stage.stageName,
    trips: stage.tripCount,
    conversion: index > 0
      ? `${Math.round((stage.tripCount / data[index - 1].tripCount) * 100)}%`
      : '100%',
  }));

  const barColors = ['#3fb950', '#58a6ff', '#d29922', '#f85149', '#79b8ff'];

  return (
    <div className='rounded-xl border border-[#1c2128] bg-[#0f1115] p-5'>
      <h2 className='text-base font-semibold text-[#e6edf3] mb-4'>Conversion Funnel</h2>

      {isMounted ? (
        <ResponsiveContainer width='100%' height={300}>
          <BarChart
            data={chartData}
            layout='vertical'
            margin={{ top: 5, right: 30, left: 200, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray='3 3' stroke='#30363d' />
            <XAxis type='number' stroke='#8b949e' />
            <YAxis dataKey='name' type='category' width={180} tick={{ fontSize: 12, fill: '#e6edf3' }} />
            <Tooltip
              contentStyle={{
                backgroundColor: '#161b22',
                border: '1px solid #30363d',
                borderRadius: '6px',
                color: '#e6edf3',
              }}
              formatter={(value: any) => {
                const numericValue = typeof value === 'number' ? value : Number(value ?? 0);
                return [`${numericValue} trips`, 'Count'];
              }}
            />
            <Bar
              dataKey='trips'
              fill='#58a6ff'
              radius={[0, 8, 8, 0]}
              animationDuration={300}
            />
          </BarChart>
        </ResponsiveContainer>
      ) : (
        <div className='h-[300px] flex items-center justify-center'>
          <p className='text-sm text-[#8b949e]'>Loading funnel…</p>
        </div>
      )}

      {/* Conversion rates below chart */}
      <div className='mt-6 space-y-2'>
        <h3 className='text-sm font-medium text-[#e6edf3] mb-3'>Stage Conversion Rates</h3>
        {chartData.map((stage) => (
          <div key={`stage-${stage.name}`} className='flex items-center justify-between text-sm'>
            <span className='text-[#8b949e]'>{stage.name}</span>
            <span className='text-[#e6edf3] font-medium'>{stage.conversion}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
