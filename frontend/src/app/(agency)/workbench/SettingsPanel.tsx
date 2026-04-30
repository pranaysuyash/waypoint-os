'use client';

import { X, Settings, ToggleLeft, ToggleRight } from 'lucide-react';
import { useWorkbenchStore } from '@/stores/workbench';

interface SettingsPanelProps {
  open: boolean;
  onClose: () => void;
}

export default function SettingsPanel({ open, onClose }: SettingsPanelProps) {
  const {
    strict_leakage,
    setStrictLeakage,
    debug_raw_json,
    setDebugRawJson,
  } = useWorkbenchStore();

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
        aria-label='Settings'
      >
        <div className='flex items-center justify-between p-4 border-b border-[#30363d]'>
          <div className='flex items-center gap-2'>
            <Settings className='w-4 h-4 text-[#8b949e]' />
            <h2 className='text-ui-sm font-semibold text-[#e6edf3]'>Settings</h2>
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
            <h3 className='text-ui-xs font-semibold text-[#8b949e] uppercase tracking-wide'>
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
                  <p className='text-ui-sm text-[#e6edf3]'>Strict Leakage Check</p>
                  <p className='text-ui-xs text-[#8b949e]'>
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
                className={`w-9 h-5 rounded-full transition-colors relative ${
                  strict_leakage ? 'bg-[#f85149]' : 'bg-[#30363d]'
                }`}
              >
                <div
                  className={`absolute top-0.5 w-4 h-4 bg-white rounded-full transition-transform ${
                    strict_leakage ? 'left-[18px]' : 'left-0.5'
                  }`}
                />
              </div>
            </label>
          </div>

        </div>
      </aside>
    </>
  );
}
