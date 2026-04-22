'use client';

import { useState, useMemo, memo } from 'react';
import {
  TrendingUp,
  Users,
  Clock,
  DollarSign,
  AlertTriangle,
  CheckCircle,
  ChevronDown,
  Download,
} from 'lucide-react';
import { useInsightsSummary, usePipelineMetrics, useTeamMetrics, useBottleneckAnalysis, useRevenueMetrics, useOperationalAlerts } from '@/hooks/useGovernance';
import type { TimeRange, StageMetrics, TeamMemberMetrics, BottleneckAnalysis, OperationalAlert } from '@/types/governance';

const VALID_TIME_RANGES = new Set<TimeRange>(['7d', '30d', '90d', 'mtd', 'ytd', 'custom']);
import { RevenueChart, PipelineFunnel, TeamPerformanceChart } from '@/components/visual';

// MOCK DATA REMOVED - Using live telemetry

// ============================================================================
// COMPONENTS
// ============================================================================

const StatCard = memo(function StatCard({
  title,
  value,
  subtext,
  trend,
  icon: Icon,
}: {
  title: string;
  value: string;
  subtext: string;
  trend?: 'up' | 'down' | 'neutral';
  icon: React.ComponentType<{ className?: string }>;
}) {
  return (
    <div className='rounded-xl border border-[#1c2128] bg-[#0f1115] p-4'>
      <div className='flex items-start justify-between'>
        <div>
          <p className='text-sm text-[#8b949e] mb-1'>{title}</p>
          <p className='text-2xl font-bold text-[#e6edf3]'>{value}</p>
          <p className={`text-xs mt-1 ${
            trend === 'up' ? 'text-[#3fb950]' : 
            trend === 'down' ? 'text-[#f85149]' : 
            'text-[#8b949e]'
          }`}>
            {subtext}
          </p>
        </div>
        <div className='h-10 w-10 rounded-lg bg-[#161b22] flex items-center justify-center'>
          <Icon className='h-5 w-5 text-[#58a6ff]' />
        </div>
      </div>
    </div>
  );
});

const VelocityBar = memo(function VelocityBar({ 
  label, 
  value, 
  max, 
  color 
}: { 
  label: string; 
  value: number; 
  max: number;
  color: string;
}) {
  const percentage = Math.min((value / max) * 100, 100);
  
  return (
    <div className='mb-3'>
      <div className='flex items-center justify-between mb-1'>
        <span className='text-sm text-[#e6edf3]'>{label}</span>
        <span className='text-sm font-mono text-[#8b949e]'>{Math.round(value)}h</span>
      </div>
      <div className='h-2 bg-[#161b22] rounded-full overflow-hidden'>
        <div 
          className='h-full rounded-full transition-all'
          style={{ width: `${percentage}%`, background: color }}
        />
      </div>
    </div>
  );
});

const TimeRemaining = ({ deadline }: { deadline: string }) => {
  const [now, setNow] = useState(new Date());
  
  // Update every minute
  useMemo(() => {
    const timer = setInterval(() => setNow(new Date()), 60000);
    return () => clearInterval(timer);
  }, []);

  const diff = new Date(deadline).getTime() - now.getTime();
  const mins = Math.floor(diff / 60000);
  
  if (mins <= 0) return <span className="font-bold">BREACHED</span>;
  if (mins < 60) return <span>{mins}m remaining</span>;
  return <span>{Math.floor(mins / 60)}h {mins % 60}m remaining</span>;
};

const CriticalAlertBanner = memo(function CriticalAlertBanner({ 
  alerts, 
  onDismiss 
}: { 
  alerts: OperationalAlert[];
  onDismiss: (id: string) => void;
}) {
  if (alerts.length === 0) return null;

  return (
    <div className='mb-6 space-y-3'>
      {alerts.map(alert => {
        const slaStatus = alert.metadata?.sla_status as string;
        const isEscalated = alert.metadata?.is_escalated as boolean;
        const deadline = alert.metadata?.deadline as string;
        
        const isBreached = slaStatus === 'breached' || alert.type === 'sla_breach';
        const isAtRisk = slaStatus === 'at_risk';

        return (
          <div 
            key={alert.id}
            className={`flex items-center justify-between p-4 rounded-xl border transition-all ${
              isBreached 
                ? 'bg-[#2b1011] border-[#6b2a2b] text-[#ff7b72] shadow-lg shadow-red-900/20' 
                : isAtRisk
                ? 'bg-[#211a0d] border-[#4e3a12] text-[#d29922]'
                : 'bg-[#161b22] border-[#30363d] text-[#e6edf3]'
            }`}
          >
            <div className='flex items-center gap-3'>
              <div className="relative">
                <AlertTriangle className={`h-5 w-5 flex-shrink-0 ${isBreached ? 'animate-pulse' : ''}`} />
                {isEscalated && (
                  <div className="absolute -top-1 -right-1 h-2 w-2 bg-red-500 rounded-full border border-[#2b1011]" />
                )}
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <p className='font-semibold text-sm'>{alert.message}</p>
                  {isEscalated && (
                    <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-[#ff7b72] text-[#2b1011] uppercase tracking-wider">
                      Escalated
                    </span>
                  )}
                </div>
                <div className='text-xs opacity-80 flex items-center gap-2 mt-0.5'>
                  <span>Trip ID: {alert.tripId}</span>
                  <span>•</span>
                  <span>{new Date(alert.timestamp).toLocaleString()}</span>
                  {deadline && (
                    <>
                      <span>•</span>
                      <span className={`font-mono ${isBreached ? 'font-bold' : ''}`}>
                        <TimeRemaining deadline={deadline} />
                      </span>
                    </>
                  )}
                </div>
              </div>
            </div>
            <div className='flex items-center gap-2'>
              <a 
                href={`/workbench?tripId=${alert.tripId}`}
                className={`px-3 py-1.5 text-xs font-medium border rounded-md transition-colors ${
                  isBreached
                    ? 'bg-[#ff7b72] text-[#2b1011] border-[#ff7b72] hover:bg-[#ff7b72]/90'
                    : 'bg-[#161b22] text-[#e6edf3] border-[#30363d] hover:bg-[#1c2128]'
                }`}
              >
                Recover Now
              </a>
              <button 
                onClick={() => onDismiss(alert.id)}
                className='p-1.5 hover:bg-black/20 rounded-md transition-colors text-[#8b949e] hover:text-[#e6edf3]'
                title="Acknowledge & Dismiss"
              >
                <CheckCircle className='h-4 w-4' />
              </button>
            </div>
          </div>
        );
      })}
    </div>
  );
});

const TeamMemberRow = memo(function TeamMemberRow({ member }: { member: TeamMemberMetrics }) {
  const workloadColors = {
    under: '#58a6ff',
    optimal: '#3fb950',
    over: '#d29922',
    critical: '#f85149',
  };
  
  return (
    <tr className='border-b border-[#1c2128] last:border-0'>
      <td className='py-3'>
        <div className='flex items-center gap-3'>
          <div className='h-8 w-8 rounded-full bg-[#58a6ff]/20 flex items-center justify-center text-[#58a6ff] text-xs font-bold'>
            {member.name.split(' ').map(n => n[0]).join('')}
          </div>
          <div>
            <p className='text-sm font-medium text-[#e6edf3]'>{member.name}</p>
            <p className='text-xs text-[#8b949e]'>{member.role}</p>
          </div>
        </div>
      </td>
      
      <td className='py-3 text-center'>
        <span className='text-sm text-[#e6edf3]'>{member.activeTrips}</span>
      </td>
      
      <td className='py-3 text-center hidden md:table-cell'>
        <div className='flex items-center justify-center gap-2'>
          <div className='w-16 h-1.5 bg-[#161b22] rounded-full overflow-hidden'>
            <div 
              className='h-full rounded-full'
              style={{ width: `${member.workloadScore}%`, background: workloadColors[member.currentWorkload] }}
            />
          </div>
          <span className={`text-xs ${
            member.currentWorkload === 'over' ? 'text-[#d29922]' : 
            member.currentWorkload === 'critical' ? 'text-[#f85149]' :
            'text-[#8b949e]'
          }`}>
            {member.workloadScore}%
          </span>
        </div>
      </td>
      
      <td className='py-3 text-center'>
        <span className='text-sm text-[#e6edf3]'>{member.conversionRate}%</span>
      </td>
      
      <td className='py-3 text-center hidden lg:table-cell'>
        <span className='text-sm text-[#e6edf3]'>{member.avgResponseTime}h</span>
      </td>
      
      <td className='py-3 text-center hidden lg:table-cell'>
        <span className='text-sm text-[#e6edf3]'>{member.customerSatisfaction}/5</span>
      </td>
    </tr>
  );
});

const BottleneckCard = memo(function BottleneckCard({ analysis }: { analysis: BottleneckAnalysis }) {
  return (
    <div className='rounded-xl border border-[#d29922]/30 bg-[#d29922]/5 p-4'>
      <div className='flex items-center gap-2 mb-3'>
        <AlertTriangle className='w-5 h-5 text-[#d29922]' />
        <h3 className='text-base font-semibold text-[#e6edf3]'>
          Bottleneck: {analysis.stageName}
        </h3>
        <span className='ml-auto px-2 py-1 bg-[#d29922]/20 text-[#d29922] text-xs rounded font-medium'>
          {analysis.severity.toUpperCase()}
        </span>
      </div>
      
      <p className='text-sm text-[#8b949e] mb-3'>
        Taking {analysis.avgTimeInStage} hours on average (target: 24h)
      </p>
      
      <div className='space-y-2'>
        {analysis.primaryCauses.map((cause, i) => (
          <div key={i} className='flex items-center justify-between py-2 border-b border-[#30363d]/50 last:border-0'>
            <div>
              <p className='text-sm text-[#e6edf3]'>{cause.cause}</p>
              <p className='text-xs text-[#8b949e]'>Affecting {cause.affectedTrips} trips · {cause.percentage}% of delays</p>
            </div>
            <button className='text-xs text-[#58a6ff] hover:text-[#79b8ff]'>
              {cause.suggestedAction}
            </button>
          </div>
        ))}
      </div>
    </div>
  );
});

// ============================================================================
// MAIN PAGE
// ============================================================================

export default function OwnerInsightsPage() {
  const [timeRange, setTimeRange] = useState<TimeRange>('30d');
  
  const { data: summary, isLoading: isSummaryLoading, error: summaryError } = useInsightsSummary(timeRange);
  const { data: pipelineMetrics, isLoading: isPipelineLoading, error: pipelineError } = usePipelineMetrics(timeRange);
  const { data: teamMetrics, isLoading: isTeamLoading, error: teamError } = useTeamMetrics(timeRange);
  const { data: bottlenecks, isLoading: isBottlenecksLoading, error: bottlenecksError } = useBottleneckAnalysis(timeRange);
  const { data: revenueData, isLoading: isRevenueLoading, error: revenueError } = useRevenueMetrics(timeRange);
  const { data: alertsData, dismiss: dismissAlert } = useOperationalAlerts();

  const isLoading = isSummaryLoading || isPipelineLoading || isTeamLoading || isBottlenecksLoading || isRevenueLoading;
  const hasError = summaryError || pipelineError || teamError || bottlenecksError || revenueError;

  const maxStageTime = useMemo(() => 
    pipelineMetrics.length > 0 ? Math.max(...pipelineMetrics.map(m => m.avgTimeInStage)) : 100
  , [pipelineMetrics]);

  return (
    <div className='p-5 pb-4 max-w-[1400px] mx-auto space-y-5'>
      {/* Header */}
      <header className='flex items-center justify-between pt-1'>
        <div>
          <h1 className='text-2xl font-semibold text-[#e6edf3]'>Insights & Analytics</h1>
          <p className='text-base text-[#8b949e] mt-0.5'>
            Monitor performance, identify bottlenecks, optimize operations
          </p>
        </div>
        
        <div className='flex items-center gap-3'>
          <div className='relative'>
            <select
              value={timeRange}
              onChange={(e) => {
                const v = e.target.value;
                if (VALID_TIME_RANGES.has(v as TimeRange)) setTimeRange(v as TimeRange);
              }}
              className='appearance-none bg-[#161b22] text-[#e6edf3] border border-[#30363d] rounded-lg px-4 py-2 pr-10 text-sm focus:outline-none focus:border-[#58a6ff]'
            >
              <option value='7d'>Last 7 days</option>
              <option value='30d'>Last 30 days</option>
              <option value='90d'>Last 90 days</option>
              <option value='mtd'>This month</option>
              <option value='ytd'>Year to date</option>
            </select>
            <ChevronDown className='absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#8b949e] pointer-events-none' />
          </div>
          
          <button className='flex items-center gap-2 px-3 py-2 bg-[#161b22] text-[#e6edf3] border border-[#30363d] rounded-lg text-sm hover:bg-[#21262d] transition-colors'>
            <Download className='w-4 h-4' /> Export
          </button>
        </div>
      </header>

      {/* Wave 10: Critical Alert Banner */}
      <CriticalAlertBanner 
        alerts={alertsData} 
        onDismiss={dismissAlert} 
      />

      {isLoading && (
        <div className="flex flex-col items-center justify-center py-20 bg-[#0f1115] border border-[#1c2128] rounded-xl">
          <div className="h-10 w-10 border-4 border-[#58a6ff] border-t-transparent rounded-full animate-spin mb-4" />
          <p className="text-[#8b949e]">Calculating latest dashboard telemetry...</p>
        </div>
      )}

      {hasError && (
        <div className="flex flex-col items-center justify-center py-20 bg-[#f85149]/5 border border-[#f85149]/30 rounded-xl">
          <AlertTriangle className="h-10 w-10 text-[#f85149] mb-4" />
          <p className="text-[#e6edf3] font-semibold">Failed to fetch live data</p>
          <p className="text-[#8b949e] text-sm mt-1">Please ensure the backend analytics service is running.</p>
        </div>
      )}

      {!isLoading && !hasError && summary && (
        <>

      {/* Summary Stats */}
      <div className='grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-3'>
        <StatCard
          title='Total Inquiries'
          value={summary.totalInquiries.toString()}
          subtext={`${summary.conversionRate}% conversion`}
          trend='up'
          icon={TrendingUp}
        />
        
        <StatCard
          title='Booked Revenue'
          value={`$${(revenueData?.bookedRevenue || 0).toLocaleString()}`}
          subtext='Confirmed revenue'
          trend='up'
          icon={CheckCircle}
        />
        
        <StatCard
          title='Pipeline Value'
          value={`$${((revenueData?.totalPipelineValue || 0) / 1000).toFixed(0)}k`}
          subtext='In progress'
          trend='neutral'
          icon={DollarSign}
        />
        
        <StatCard
          title='Projected'
          value={`$${((revenueData?.projectedRevenue || 0) / 1000).toFixed(0)}k`}
          subtext='Weighted probability'
          trend='up'
          icon={TrendingUp}
        />

        <StatCard
          title='Near Close'
          value={`$${((revenueData?.nearCloseRevenue || 0) / 1000).toFixed(0)}k`}
          subtext='Safety/Output stage'
          trend='neutral'
          icon={Clock}
        />
      </div>

      {/* Main Content Grid */}
      <div className='grid grid-cols-1 lg:grid-cols-2 gap-5'>
        
        {/* Pipeline Velocity */}
        <div className='rounded-xl border border-[#1c2128] bg-[#0f1115] p-5'>
          <div className='flex items-center justify-between mb-4'>
            <h2 className='text-base font-semibold text-[#e6edf3]'>Average Time to Complete</h2>
            <span className='text-xs text-[#8b949e]'>Avg: {summary.pipelineVelocity.averageTotal} days total</span>
          </div>
          
          <div className='space-y-1'>
            <VelocityBar 
              label='New Inquiry → Details' 
              value={summary.pipelineVelocity.stage1To2 * 24} 
              max={maxStageTime}
              color='#3fb950'
            />
            <VelocityBar 
              label='Details → Ready to Quote' 
              value={summary.pipelineVelocity.stage2To3 * 24} 
              max={maxStageTime}
              color='#58a6ff'
            />
            <VelocityBar 
              label='Ready to Quote → Build Options' 
              value={summary.pipelineVelocity.stage3To4 * 24} 
              max={maxStageTime}
              color='#d29922'
            />
            <VelocityBar 
              label='Build Options → Final Review' 
              value={summary.pipelineVelocity.stage4To5 * 24} 
              max={maxStageTime}
              color='#58a6ff'
            />
            <VelocityBar 
              label='Final Review → Booked' 
              value={summary.pipelineVelocity.stage5ToBooked * 24} 
              max={maxStageTime}
              color='#3fb950'
            />
          </div>
        </div>

        {/* Stage Breakdown */}
        <div className='rounded-xl border border-[#1c2128] bg-[#0f1115] p-5'>
          <h2 className='text-base font-semibold text-[#e6edf3] mb-4'>Stage Breakdown</h2>
          
          <div className='space-y-3'>
            {pipelineMetrics.map((stage) => (
              <div key={stage.stageId} className='flex items-center justify-between'>
                <div className='flex-1'>
                  <div className='flex items-center justify-between mb-1'>
                    <span className='text-sm text-[#e6edf3]'>{stage.stageName}</span>
                    <span className='text-xs text-[#8b949e]'>{stage.tripCount} trips · {stage.exitRate}% exit</span>
                  </div>
                  <div className='h-1.5 bg-[#161b22] rounded-full overflow-hidden'>
                    <div 
                      className='h-full bg-[#58a6ff] rounded-full'
                      style={{ width: `${(stage.tripCount / 20) * 100}%` }}
                    />
                  </div>
                </div>
                
                <span className='ml-4 text-xs text-[#8b949e] w-16 text-right'>
                  {stage.avgTimeInStage}h
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Pipeline Funnel */}
        <div className='lg:col-span-2'>
          <PipelineFunnel data={pipelineMetrics} />
        </div>

        {/* Revenue Chart */}
        <div className='lg:col-span-2'>
          <RevenueChart data={revenueData?.revenueByMonth || []} />
        </div>

        {/* Team Performance Chart */}
        <div className='lg:col-span-2'>
          <TeamPerformanceChart data={teamMetrics.map(member => ({
            name: member.name,
            conversionRate: member.conversionRate,
            avgResponseTime: member.avgResponseTime,
            customerSatisfaction: member.customerSatisfaction,
            workloadScore: member.workloadScore,
          }))} />
        </div>

        {/* Team Performance Table */}
        <div className='rounded-xl border border-[#1c2128] bg-[#0f1115] p-5 lg:col-span-2'>
          <h2 className='text-base font-semibold text-[#e6edf3] mb-4'>Team Performance</h2>
          
          <div className='overflow-x-auto'>
            <table className='w-full'>
              <thead>
                <tr className='border-b border-[#30363d]'>
                  <th className='text-left py-2 text-sm font-medium text-[#8b949e]'>Agent</th>
                  <th className='text-center py-2 text-sm font-medium text-[#8b949e]'>Active</th>
                  <th className='text-center py-2 text-sm font-medium text-[#8b949e] hidden md:table-cell'>Workload</th>
                  <th className='text-center py-2 text-sm font-medium text-[#8b949e]'>Conversion</th>
                  <th className='text-center py-2 text-sm font-medium text-[#8b949e] hidden lg:table-cell'>Response</th>
                  <th className='text-center py-2 text-sm font-medium text-[#8b949e] hidden lg:table-cell'>CSAT</th>
                </tr>
              </thead>
              <tbody>
                {teamMetrics.map((member) => (
                  <TeamMemberRow key={member.userId} member={member} />
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Bottlenecks */}
        <div className='lg:col-span-2'>
          <h2 className='text-base font-semibold text-[#e6edf3] mb-3'>Bottleneck Analysis</h2>
          
          {bottlenecks.length > 0 ? (
            <div className='space-y-3'>
              {bottlenecks.map((bottleneck) => (
                <BottleneckCard key={bottleneck.stageId} analysis={bottleneck} />
              ))}
            </div>
          ) : (
            <div className='rounded-xl border border-[#1c2128] bg-[#0f1115] p-6 text-center'>
              <CheckCircle className='w-8 h-8 text-[#3fb950] mx-auto mb-2' />
              <p className='text-sm text-[#8b949e]'>No bottlenecks detected. Things are flowing smoothly!</p>
            </div>
          )}
        </div>

      </div>
      </>
      )}
    </div>
  );
}
