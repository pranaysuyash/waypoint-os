'use client';

import { Settings, ToggleLeft, ToggleRight } from 'lucide-react';
import { Drawer } from '@/components/ui/drawer';
import { useWorkbenchStore } from '@/stores/workbench';

interface SettingsPanelProps {
  open: boolean;
  onClose: () => void;
}

export default function SettingsPanel({ open, onClose }: SettingsPanelProps) {
  const {
    strict_leakage,
    setStrictLeakage,
  } = useWorkbenchStore();

  return (
    <Drawer
      isOpen={open}
      onClose={onClose}
      title="Settings"
      width="w-80"
      showCloseButton={true}
    >
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
    </Drawer>
  );
}
