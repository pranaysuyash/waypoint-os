'use client';

import { useState, useEffect } from 'react';

export interface TeamMember {
  name: string;
  conversionRate: number;
  avgResponseTime: number;
  customerSatisfaction: number;
  workloadScore: number;
}

export function TeamPerformanceChart({ data }: { data: TeamMember[] }) {
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  if (data.length === 0) {
    return (
      <div className='rounded-xl border border-[#1c2128] bg-[#0f1115] p-5'>
        <h2 className='text-base font-semibold text-[#e6edf3] mb-4'>Agent Performance Metrics</h2>
        <p className='text-sm text-[#8b949e]'>No team data available.</p>
      </div>
    );
  }

  if (!isMounted) {
    return (
      <div className='rounded-xl border border-[#1c2128] bg-[#0f1115] p-5'>
        <h2 className='text-base font-semibold text-[#e6edf3] mb-4'>Agent Performance Metrics</h2>
        <p className='text-sm text-[#8b949e]'>Loading metrics…</p>
      </div>
    );
  }

  const getResponseTimeColor = (time: number) => {
    if (time <= 3) return '#3fb950'; // green - fast
    if (time <= 4) return '#58a6ff'; // blue - good
    if (time <= 5) return '#d29922'; // amber - acceptable
    return '#f85149'; // red - slow
  };

  const getConversionColor = (rate: number) => {
    if (rate >= 72) return '#3fb950'; // green - excellent
    if (rate >= 68) return '#58a6ff'; // blue - good
    if (rate >= 65) return '#d29922'; // amber - acceptable
    return '#f85149'; // red - needs improvement
  };

  const getCsatColor = (rating: number) => {
    if (rating >= 4.7) return '#3fb950'; // green - excellent
    if (rating >= 4.5) return '#58a6ff'; // blue - good
    if (rating >= 4.2) return '#d29922'; // amber - acceptable
    return '#f85149'; // red - needs attention
  };

  const getWorkloadColor = (score: number) => {
    if (score <= 60) return '#3fb950'; // green - optimal
    if (score <= 80) return '#58a6ff'; // blue - good
    if (score <= 90) return '#d29922'; // amber - high
    return '#f85149'; // red - critical
  };

  return (
    <div className='rounded-xl border border-[#1c2128] bg-[#0f1115] p-5'>
      <h2 className='text-base font-semibold text-[#e6edf3] mb-4'>Agent Performance Metrics</h2>

      {/* Legend */}
      <div className='grid grid-cols-2 md:grid-cols-4 gap-3 mb-5 text-xs'>
        <div>
          <span className='text-[#8b949e]'>Conversion Rate</span>
          <p className='text-[#e6edf3] font-medium'>↑ Higher is better</p>
        </div>
        <div>
          <span className='text-[#8b949e]'>Response Time</span>
          <p className='text-[#e6edf3] font-medium'>↓ Lower is better</p>
        </div>
        <div>
          <span className='text-[#8b949e]'>CSAT</span>
          <p className='text-[#e6edf3] font-medium'>↑ Out of 5.0</p>
        </div>
        <div>
          <span className='text-[#8b949e]'>Workload</span>
          <p className='text-[#e6edf3] font-medium'>↓ Lower %</p>
        </div>
      </div>

      {/* Agent Cards */}
      <div className='space-y-4'>
        {data.map((agent, index) => (
          <div key={index} className='rounded-lg border border-[#30363d] bg-[#161b22] p-4'>
            <div className='flex items-center justify-between mb-3'>
              <h3 className='text-sm font-medium text-[#e6edf3]'>{agent.name}</h3>
            </div>

            {/* Metrics Grid */}
            <div className='grid grid-cols-2 md:grid-cols-4 gap-3'>
              {/* Conversion Rate */}
              <div>
                <div className='flex items-center justify-between mb-1'>
                  <span className='text-xs text-[#8b949e]'>Conversion</span>
                  <span
                    className='text-sm font-semibold'
                    style={{ color: getConversionColor(agent.conversionRate) }}
                  >
                    {agent.conversionRate}%
                  </span>
                </div>
                <div className='h-2 bg-[#0f1115] rounded-full overflow-hidden'>
                  <div
                    className='h-full rounded-full transition-all'
                    style={{
                      width: `${(agent.conversionRate / 100) * 100}%`,
                      background: getConversionColor(agent.conversionRate),
                    }}
                  />
                </div>
              </div>

              {/* Response Time */}
              <div>
                <div className='flex items-center justify-between mb-1'>
                  <span className='text-xs text-[#8b949e]'>Response</span>
                  <span
                    className='text-sm font-semibold'
                    style={{ color: getResponseTimeColor(agent.avgResponseTime) }}
                  >
                    {agent.avgResponseTime}h
                  </span>
                </div>
                <div className='h-2 bg-[#0f1115] rounded-full overflow-hidden'>
                  <div
                    className='h-full rounded-full transition-all'
                    style={{
                      width: `${Math.max(0, 100 - (agent.avgResponseTime / 8) * 100)}%`,
                      background: getResponseTimeColor(agent.avgResponseTime),
                    }}
                  />
                </div>
              </div>

              {/* Customer Satisfaction */}
              <div>
                <div className='flex items-center justify-between mb-1'>
                  <span className='text-xs text-[#8b949e]'>CSAT</span>
                  <span
                    className='text-sm font-semibold'
                    style={{ color: getCsatColor(agent.customerSatisfaction) }}
                  >
                    {agent.customerSatisfaction}/5
                  </span>
                </div>
                <div className='h-2 bg-[#0f1115] rounded-full overflow-hidden'>
                  <div
                    className='h-full rounded-full transition-all'
                    style={{
                      width: `${(agent.customerSatisfaction / 5) * 100}%`,
                      background: getCsatColor(agent.customerSatisfaction),
                    }}
                  />
                </div>
              </div>

              {/* Workload */}
              <div>
                <div className='flex items-center justify-between mb-1'>
                  <span className='text-xs text-[#8b949e]'>Workload</span>
                  <span
                    className='text-sm font-semibold'
                    style={{ color: getWorkloadColor(agent.workloadScore) }}
                  >
                    {agent.workloadScore}%
                  </span>
                </div>
                <div className='h-2 bg-[#0f1115] rounded-full overflow-hidden'>
                  <div
                    className='h-full rounded-full transition-all'
                    style={{
                      width: `${agent.workloadScore}%`,
                      background: getWorkloadColor(agent.workloadScore),
                    }}
                  />
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
