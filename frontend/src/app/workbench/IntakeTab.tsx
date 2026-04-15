'use client';

import { useState } from 'react';
import {
  ChevronDown,
  FileText,
  User,
  MapPin,
  Calendar,
  Users,
  Wallet,
  Sparkles,
  Settings,
} from 'lucide-react';

interface Scenario {
  id: string;
  title: string;
  stage: string;
}

const scenarios: Scenario[] = [
  { id: 'sgp-family', title: 'Singapore Family Trip', stage: 'discovery' },
  { id: 'dubai-corp', title: 'Dubai Corporate Retreat', stage: 'shortlist' },
  { id: 'andaman-rom', title: 'Andaman Honeymoon', stage: 'discovery' },
  { id: 'europe-multi', title: 'Europe Multi-City', stage: 'proposal' },
];

const stages = [
  { value: 'discovery', label: 'Discovery' },
  { value: 'shortlist', label: 'Shortlist' },
  { value: 'proposal', label: 'Proposal' },
  { value: 'booking', label: 'Booking' },
];

const modes = [
  { value: 'normal_intake', label: 'Normal Intake' },
  { value: 'audit', label: 'Audit' },
  { value: 'emergency', label: 'Emergency' },
  { value: 'follow_up', label: 'Follow Up' },
  { value: 'cancellation', label: 'Cancellation' },
  { value: 'post_trip', label: 'Post Trip' },
];

export function IntakeTab() {
  const [selectedScenario, setSelectedScenario] = useState('');
  const [stage, setStage] = useState('discovery');
  const [mode, setMode] = useState('normal_intake');
  const [rawNote, setRawNote] = useState('');
  const [ownerNote, setOwnerNote] = useState('');
  const [structuredJson, setStructuredJson] = useState('');

  return (
    <div className='space-y-6'>
      {/* Scenario Selection */}
      <div className='bg-[#161b22] border border-[#30363d] rounded-xl p-4'>
        <div className='flex items-center gap-2 mb-4'>
          <Sparkles className='w-4 h-4 text-[#a371f7]' />
          <h3 className='text-sm font-semibold text-[#e6edf3]'>
            Scenario Selection
          </h3>
        </div>
        <div className='relative'>
          <select
            value={selectedScenario}
            onChange={(e) => setSelectedScenario(e.target.value)}
            className='w-full px-4 py-2.5 bg-[#0f1115] border border-[#30363d] rounded-lg text-sm text-[#e6edf3] focus:outline-none focus:border-[#58a6ff] appearance-none cursor-pointer'
          >
            <option value=''>Select a scenario...</option>
            {scenarios.map((s) => (
              <option key={s.id} value={s.id}>
                {s.title} ({s.stage})
              </option>
            ))}
          </select>
          <ChevronDown className='absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#6e7681] pointer-events-none' />
        </div>
      </div>

      {/* Input Fields Grid */}
      <div className='grid grid-cols-1 lg:grid-cols-2 gap-6'>
        {/* Raw Note */}
        <div className='bg-[#161b22] border border-[#30363d] rounded-xl p-4'>
          <div className='flex items-center gap-2 mb-3'>
            <FileText className='w-4 h-4 text-[#8b949e]' />
            <label className='text-sm font-medium text-[#e6edf3]'>
              Raw Note
            </label>
          </div>
          <textarea
            value={rawNote}
            onChange={(e) => setRawNote(e.target.value)}
            placeholder='Paste the incoming traveler note here...'
            rows={6}
            className='w-full px-3 py-2 bg-[#0f1115] border border-[#30363d] rounded-lg text-sm text-[#e6edf3] placeholder:text-[#6e7681] focus:outline-none focus:border-[#58a6ff] resize-none font-mono'
          />
        </div>

        {/* Owner Note */}
        <div className='bg-[#161b22] border border-[#30363d] rounded-xl p-4'>
          <div className='flex items-center gap-2 mb-3'>
            <User className='w-4 h-4 text-[#58a6ff]' />
            <label className='text-sm font-medium text-[#e6edf3]'>
              Owner Note
            </label>
          </div>
          <textarea
            value={ownerNote}
            onChange={(e) => setOwnerNote(e.target.value)}
            placeholder="Add owner's comments or clarifications..."
            rows={6}
            className='w-full px-3 py-2 bg-[#0f1115] border border-[#30363d] rounded-lg text-sm text-[#e6edf3] placeholder:text-[#6e7681] focus:outline-none focus:border-[#58a6ff] resize-none'
          />
        </div>
      </div>

      {/* Configuration */}
      <div className='bg-[#161b22] border border-[#30363d] rounded-xl p-4'>
        <h3 className='text-sm font-semibold text-[#e6edf3] mb-4 flex items-center gap-2'>
          <Settings className='w-4 h-4 text-[#8b949e]' />
          Configuration
        </h3>
        <div className='grid grid-cols-1 sm:grid-cols-2 gap-4'>
          <div>
            <label className='block text-xs font-medium text-[#8b949e] mb-2'>
              Stage
            </label>
            <div className='relative'>
              <select
                value={stage}
                onChange={(e) => setStage(e.target.value)}
                className='w-full px-3 py-2 bg-[#0f1115] border border-[#30363d] rounded-lg text-sm text-[#e6edf3] focus:outline-none focus:border-[#58a6ff] appearance-none'
              >
                {stages.map((s) => (
                  <option key={s.value} value={s.value}>
                    {s.label}
                  </option>
                ))}
              </select>
              <ChevronDown className='absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#6e7681] pointer-events-none' />
            </div>
          </div>
          <div>
            <label className='block text-xs font-medium text-[#8b949e] mb-2'>
              Operating Mode
            </label>
            <div className='relative'>
              <select
                value={mode}
                onChange={(e) => setMode(e.target.value)}
                className='w-full px-3 py-2 bg-[#0f1115] border border-[#30363d] rounded-lg text-sm text-[#e6edf3] focus:outline-none focus:border-[#58a6ff] appearance-none'
              >
                {modes.map((m) => (
                  <option key={m.value} value={m.value}>
                    {m.label}
                  </option>
                ))}
              </select>
              <ChevronDown className='absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#6e7681] pointer-events-none' />
            </div>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className='flex items-center justify-between pt-4 border-t border-[#30363d]'>
        <div className='flex items-center gap-4 text-sm text-[#8b949e]'>
          <div className='flex items-center gap-2'>
            <div className='w-2 h-2 rounded-full bg-[#3fb950]'></div>
            <span>API Connected</span>
          </div>
        </div>
      </div>
    </div>
  );
}
