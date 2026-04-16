'use client';

import { useSearchParams, useRouter } from 'next/navigation';
import { Suspense, useState, lazy } from 'react';
import { Tabs } from '@/components/ui/tabs';
import { PipelineFlow } from './PipelineFlow';
import { Play, RotateCcw, Settings } from 'lucide-react';
import { InlineLoading } from '@/components/ui/loading';

// Code split tab components for better initial load performance
const IntakeTab = lazy(() =>
  import('./IntakeTab').then((m) => ({ default: m.IntakeTab }))
);
const PacketTab = lazy(() =>
  import('./PacketTab').then((m) => ({ default: m.PacketTab }))
);
const DecisionTab = lazy(() =>
  import('./DecisionTab').then((m) => ({ default: m.DecisionTab }))
);
const StrategyTab = lazy(() =>
  import('./StrategyTab').then((m) => ({ default: m.StrategyTab }))
);
const SafetyTab = lazy(() =>
  import('./SafetyTab').then((m) => ({ default: m.SafetyTab }))
);

const workbenchTabs = [
  { id: 'intake', label: 'New Inquiry' },
  { id: 'packet', label: 'Trip Details' },
  { id: 'decision', label: 'Ready to Quote?' },
  { id: 'strategy', label: 'Build Options' },
  { id: 'safety', label: 'Final Review' },
];

type WorkbenchTabId = (typeof workbenchTabs)[number]['id'];

function WorkbenchContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const tabParam = searchParams.get('tab') as WorkbenchTabId | null;
  const activeTab =
    tabParam && workbenchTabs.some((t) => t.id === tabParam)
      ? tabParam
      : 'intake';

  const handleTabChange = (tab: WorkbenchTabId) => {
    const params = new URLSearchParams(searchParams.toString());
    params.set('tab', tab);
    router.push(`?${params.toString()}`, { scroll: false });
  };

  const [isRunning, setIsRunning] = useState(false);

  return (
    <div className='min-h-screen bg-[#080a0c]'>
      {/* Pipeline Flow Visualization */}
      <PipelineFlow currentStage={activeTab} />

      {/* Main Content */}
      <div className='px-6 py-6'>
        {/* Header */}
        <header className='flex items-center justify-between mb-6'>
          <div>
            <h1 className='text-2xl font-semibold text-[#e6edf3] mb-1'>
              Trip Pipeline
            </h1>
            <p className='text-base text-[#a8b3c1]'>
              Process travel requests through the pipeline
            </p>
          </div>
          <div className='flex items-center gap-3'>
            <button
              type='button'
              disabled={isRunning}
              className='flex items-center gap-2 px-4 py-2 bg-[#58a6ff] text-[#0d1117] rounded-lg font-medium hover:bg-[#6eb5ff] disabled:opacity-50 disabled:cursor-not-allowed transition-colors'
              aria-label={
                isRunning ? 'Processing trip' : 'Process trip'
              }
            >
              {isRunning ? (
                <>
                  <div
                    className='w-4 h-4 border-2 border-[#0d1117]/30 border-t-[#0d1117] rounded-full animate-spin'
                    aria-hidden='true'
                  />
                  Processing...
                </>
              ) : (
                <>
                  <Play className='w-4 h-4' aria-hidden='true' />
                  Process Trip
                </>
              )}
            </button>
            <button
              type='button'
              className='flex items-center gap-2 px-3 py-2 bg-[#161b22] text-[#e6edf3] border border-[#30363d] rounded-lg font-medium hover:bg-[#21262d] transition-colors'
              aria-label='Reset pipeline'
            >
              <RotateCcw className='w-4 h-4' aria-hidden='true' />
              Reset
            </button>
            <button
              type='button'
              className='flex items-center gap-2 px-3 py-2 bg-[#161b22] text-[#e6edf3] border border-[#30363d] rounded-lg font-medium hover:bg-[#21262d] transition-colors'
              aria-label='Open settings'
            >
              <Settings className='w-4 h-4' aria-hidden='true' />
            </button>
          </div>
        </header>

        {/* Tab Navigation */}
        <div className='bg-[#0f1115] border border-[#30363d] rounded-t-xl overflow-hidden'>
          <Tabs
            tabs={workbenchTabs}
            activeTab={activeTab}
            onTabChange={handleTabChange}
          />
        </div>

        {/* Tab Content */}
        <div
          className='bg-[#0f1115] border-x border-b border-[#30363d] rounded-b-xl'
          role='tabpanel'
          id={`tabpanel-${activeTab}`}
          aria-labelledby={`tab-${activeTab}`}
          tabIndex={0}
        >
          <div className='p-6'>
            <Suspense fallback={<InlineLoading message='Loading tab...' />}>
              {activeTab === 'intake' && <IntakeTab />}
              {activeTab === 'packet' && <PacketTab />}
              {activeTab === 'decision' && <DecisionTab />}
              {activeTab === 'strategy' && <StrategyTab />}
              {activeTab === 'safety' && <SafetyTab />}
            </Suspense>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function WorkbenchPage() {
  return (
    <Suspense fallback={<WorkbenchLoading />}>
      <WorkbenchContent />
    </Suspense>
  );
}

function WorkbenchLoading() {
  return (
    <div className='min-h-screen bg-[#080a0c] px-6 py-6'>
      <div className='h-8 bg-[#161b22] rounded animate-pulse mb-6 w-48' />
      <div className='h-12 bg-[#0f1115] rounded animate-pulse mb-4' />
      <div className='h-64 bg-[#0f1115] rounded animate-pulse' />
    </div>
  );
}
