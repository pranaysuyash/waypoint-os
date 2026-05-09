'use client';

import { useState, useEffect } from 'react';

export interface TeamMember {
  name: string;
  conversionRate: number;
  avgResponseTime: number | null;
  customerSatisfaction: number;
  workloadScore: number;
  userId?: string;
}

export interface DrillDownMetric {
  type: 'conversion' | 'response_time' | 'csat' | 'workload';
  value: number;
  label: string;
  tripCount?: number;
}

export function TeamPerformanceChart({ 
  data,
  onDrillDown 
}: { 
  data: TeamMember[];
  onDrillDown?: (agentId: string, metric: DrillDownMetric) => void;
}) {
  const [isMounted, setIsMounted] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);

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
    if (time <= 3) return '#3fb950';
    if (time <= 4) return '#58a6ff';
    if (time <= 5) return '#d29922';
    return '#f85149';
  };

  const getConversionColor = (rate: number) => {
    if (rate >= 72) return '#3fb950';
    if (rate >= 68) return '#58a6ff';
    if (rate >= 65) return '#d29922';
    return '#f85149';
  };

  const getCsatColor = (rating: number) => {
    if (rating >= 4.7) return '#3fb950';
    if (rating >= 4.5) return '#58a6ff';
    if (rating >= 4.2) return '#d29922';
    return '#f85149';
  };

  const getWorkloadColor = (score: number) => {
    if (score <= 60) return '#3fb950';
    if (score <= 80) return '#58a6ff';
    if (score <= 90) return '#d29922';
    return '#f85149';
  };

  const handleMetricClick = (agentId: string | undefined, metric: DrillDownMetric) => {
    if (onDrillDown && agentId) {
      onDrillDown(agentId, metric);
      setSelectedAgent(agentId);
    }
  };

  return (
    <div className='rounded-xl border border-[#1c2128] bg-[#0f1115] p-5'>
      <h2 className='text-base font-semibold text-[#e6edf3] mb-4'>Agent Performance Metrics</h2>

      {onDrillDown && (
        <p className='text-xs text-[#8b949e] mb-4'>💡 Click on any metric to drill down and see trip details</p>
      )}

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
        {data.map((agent) => (
          <div
            key={agent.userId || agent.name}
            className={`rounded-lg border transition-all ${
              selectedAgent === agent.userId
                ? 'border-[#58a6ff] bg-[#161b22]'
                : 'border-[#30363d] bg-[#161b22]'
            } p-4`}
          >
            <div className='flex items-center justify-between mb-3'>
              <h3 className='text-sm font-medium text-[#e6edf3]'>{agent.name}</h3>
            </div>

            {/* Metrics Grid */}
            <div className='grid grid-cols-2 md:grid-cols-4 gap-3'>
              {/* Conversion Rate */}
              <div
                onClick={() =>
                  handleMetricClick(agent.userId, {
                    type: 'conversion',
                    value: agent.conversionRate,
                    label: 'Conversion Rate',
                  })
                }
                className={`rounded p-2 transition-colors ${
                  onDrillDown ? 'cursor-pointer hover:bg-[#0f1115]' : ''
                }`}
              >
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
              <div
                onClick={() =>
                  handleMetricClick(agent.userId, {
                    type: 'response_time',
                    value: agent.avgResponseTime ?? 0,
                    label: 'Response Time',
                  })
                }
                className={`rounded p-2 transition-colors ${
                  onDrillDown ? 'cursor-pointer hover:bg-[#0f1115]' : ''
                }`}
              >
                <div className='flex items-center justify-between mb-1'>
                  <span className='text-xs text-[#8b949e]'>Response</span>
                  <span
                    className='text-sm font-semibold'
                    style={{ color: agent.avgResponseTime != null ? getResponseTimeColor(agent.avgResponseTime) : '#8b949e' }}
                  >
                    {agent.avgResponseTime != null ? `${agent.avgResponseTime}h` : 'N/A'}
                  </span>
                </div>
                <div className='h-2 bg-[#0f1115] rounded-full overflow-hidden'>
                  <div
                    className='h-full rounded-full transition-all'
                    style={{
                      width: agent.avgResponseTime != null ? `${Math.max(0, 100 - (agent.avgResponseTime / 8) * 100)}%` : '0%',
                      background: agent.avgResponseTime != null ? getResponseTimeColor(agent.avgResponseTime) : '#8b949e',
                    }}
                  />
                </div>
              </div>

              {/* Customer Satisfaction */}
              <div
                onClick={() =>
                  handleMetricClick(agent.userId, {
                    type: 'csat',
                    value: agent.customerSatisfaction,
                    label: 'Customer Satisfaction',
                  })
                }
                className={`rounded p-2 transition-colors ${
                  onDrillDown ? 'cursor-pointer hover:bg-[#0f1115]' : ''
                }`}
              >
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
              <div
                onClick={() =>
                  handleMetricClick(agent.userId, {
                    type: 'workload',
                    value: agent.workloadScore,
                    label: 'Workload',
                  })
                }
                className={`rounded p-2 transition-colors ${
                  onDrillDown ? 'cursor-pointer hover:bg-[#0f1115]' : ''
                }`}
              >
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
