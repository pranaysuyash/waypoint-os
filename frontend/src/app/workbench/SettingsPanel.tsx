'use client';

import { X, Settings, ToggleLeft, ToggleRight, FileCode2 } from 'lucide-react';
import { useWorkbenchStore } from '@/stores/workbench';
import { useScenarios } from '@/hooks/useScenarios';

interface SettingsPanelProps {
  open: boolean;
  onClose: () => void;
}

export function SettingsPanel({ open, onClose }: SettingsPanelProps) {
  const {
    strict_leakage,
    setStrictLeakage,
    debug_raw_json,
    setDebugRawJson,
    scenario_id,
    setScenarioId,
  } = useWorkbenchStore();
  const { data: scenarios, isLoading: scenariosLoading } = useScenarios();

  if (!open) return null;

  return (
    <>
      <div
        className='fixed inset-0 bg-black/50 z-40'
        onClick={onClose}
        aria-hidden='true'
      />
      <aside
        className='fixed right-0 top-0 bottom-0 w-80 bg-[#0f1115] border-l border-[#30363d] z-50 overflow-y-auto'
        role='dialog'
        aria-label='Pipeline settings'
      >
        <div className='flex items-center justify-between p-4 border-b border-[#30363d]'>
          <div className='flex items-center gap-2'>
            <Settings className='w-4 h-4 text-[#8b949e]' />
            <h2 className='text-sm font-semibold text-[#e6edf3]'>Settings</h2>
          </div>
          <button
            type='button'
            onClick={onClose}
            className='p-1 rounded hover:bg-[#21262d] text-[#8b949e] hover:text-[#e6edf3] transition-colors'
            aria-label='Close settings'
          >
            <X className='w-4 h-4' />
          </button>
        </div>

        <div className='p-4 space-y-6'>
          <div className='space-y-3'>
            <h3 className='text-xs font-semibold text-[#8b949e] uppercase tracking-wide'>
              Safety
            </h3>
            <label className='flex items-center justify-between cursor-pointer group'>
              <div className='flex items-center gap-2'>
                {strict_leakage ? (
                  <ToggleRight className='w-5 h-5 text-[#f85149]' />
                ) : (
                  <ToggleLeft className='w-5 h-5 text-[#8b949e] group-hover:text-[#e6edf3]' />
                )}
                <div>
                  <p className='text-sm text-[#e6edf3]'>Strict Leakage Check</p>
                  <p className='text-xs text-[#8b949e]'>
                    Block sending if any internal jargon is found
                  </p>
                </div>
              </div>
              <input
                type='checkbox'
                checked={strict_leakage}
                onChange={(e) => setStrictLeakage(e.target.checked)}
                className='sr-only'
              />
              <div
                className={`w-9 h-5 rounded-full transition-colors relative cursor-pointer ${
                  strict_leakage ? 'bg-[#f85149]' : 'bg-[#30363d]'
                }`}
                onClick={() => setStrictLeakage(!strict_leakage)}
              >
                <div
                  className={`absolute top-0.5 w-4 h-4 bg-white rounded-full transition-transform ${
                    strict_leakage ? 'left-[18px]' : 'left-0.5'
                  }`}
                />
              </div>
            </label>
          </div>

          <div className='space-y-3'>
            <h3 className='text-xs font-semibold text-[#8b949e] uppercase tracking-wide'>
              Debug
            </h3>
            <label className='flex items-center justify-between cursor-pointer group'>
              <div className='flex items-center gap-2'>
                {debug_raw_json ? (
                  <FileCode2 className='w-5 h-5 text-[#58a6ff]' />
                ) : (
                  <FileCode2 className='w-5 h-5 text-[#8b949e] group-hover:text-[#e6edf3]' />
                )}
                <div>
                  <p className='text-sm text-[#e6edf3]'>Show Technical Data</p>
                  <p className='text-xs text-[#8b949e]'>
                    Auto-expand raw JSON in all tabs
                  </p>
                </div>
              </div>
              <input
                type='checkbox'
                checked={debug_raw_json}
                onChange={(e) => setDebugRawJson(e.target.checked)}
                className='sr-only'
              />
              <div
                className={`w-9 h-5 rounded-full transition-colors relative cursor-pointer ${
                  debug_raw_json ? 'bg-[#58a6ff]' : 'bg-[#30363d]'
                }`}
                onClick={() => setDebugRawJson(!debug_raw_json)}
              >
                <div
                  className={`absolute top-0.5 w-4 h-4 bg-white rounded-full transition-transform ${
                    debug_raw_json ? 'left-[18px]' : 'left-0.5'
                  }`}
                />
              </div>
            </label>
          </div>

          <div className='space-y-3'>
            <h3 className='text-xs font-semibold text-[#8b949e] uppercase tracking-wide'>
              Scenario
            </h3>
            <select
              value={scenario_id}
              onChange={(e) => setScenarioId(e.target.value)}
              className='w-full px-3 py-2 bg-[#0d1117] border border-[#30363d] rounded-lg text-sm text-[#e6edf3] focus:outline-none focus:border-[#58a6ff] appearance-none'
            >
              <option value=''>No scenario (live input)</option>
              {scenariosLoading ? (
                <option value='' disabled>Loading scenarios...</option>
              ) : (
                scenarios.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.title}
                  </option>
                ))
              )}
            </select>
            <p className='text-xs text-[#8b949e]'>
              Pre-loaded test scenario for pipeline runs
            </p>
          </div>
        </div>
      </aside>
    </>
  );
}