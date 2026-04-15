'use client';

import { useSearchParams, useRouter } from 'next/navigation';
import { Suspense, useState } from 'react';
import { Tabs } from '@/components/ui/tabs';
import { IntakeTab } from './IntakeTab';
import { PacketTab } from './PacketTab';
import { DecisionTab } from './DecisionTab';
import { StrategyTab } from './StrategyTab';
import { SafetyTab } from './SafetyTab';
import { PipelineFlow } from './PipelineFlow';
import { Play, RotateCcw, Settings } from 'lucide-react';

const workbenchTabs = [
  { id: 'intake', label: 'Intake' },
  { id: 'packet', label: 'Packet' },
  { id: 'decision', label: 'Decision' },
  { id: 'strategy', label: 'Strategy' },
  { id: 'safety', label: 'Safety' },
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
        <div className='flex items-center justify-between mb-6'>
          <div>
            <h1 className='text-xl font-semibold text-[#e6edf3] mb-1'>
              Workbench
            </h1>
            <p className='text-sm text-[#8b949e]'>
              Process travel requests through the NB pipeline
            </p>
          </div>
          <div className='flex items-center gap-3'>
            <button
              type='button'
              disabled={isRunning}
              className='flex items-center gap-2 px-4 py-2 bg-[#58a6ff] text-[#0d1117] rounded-lg font-medium hover:bg-[#6eb5ff] disabled:opacity-50 disabled:cursor-not-allowed transition-colors'
              aria-label={
                isRunning ? 'Running spine pipeline' : 'Run spine pipeline'
              }
            >
              {isRunning ? (
                <>
                  <div
                    className='w-4 h-4 border-2 border-[#0d1117]/30 border-t-[#0d1117] rounded-full animate-spin'
                    aria-hidden='true'
                  />
                  Running...
                </>
              ) : (
                <>
                  <Play className='w-4 h-4' aria-hidden='true' />
                  Run Spine
                </>
              )}
            </button>
            <button
              type='button'
              className='flex items-center gap-2 px-3 py-2 bg-[#161b22] text-[#e6edf3] border border-[#30363d] rounded-lg font-medium hover:bg-[#21262d] transition-colors'
              aria-label='Reset workbench'
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
        </div>

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
          aria-label={`${activeTab} content`}
        >
          <div className='p-6'>
            {activeTab === 'intake' && <IntakeTab />}
            {activeTab === 'packet' && <PacketTab />}
            {activeTab === 'decision' && <DecisionTab />}
            {activeTab === 'strategy' && <StrategyTab />}
            {activeTab === 'safety' && <SafetyTab />}
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
