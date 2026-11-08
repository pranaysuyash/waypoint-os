'use client';

import React, { useState } from 'react';
import {
  Brain,
  ShieldCheck,
  UserCheck,
  AlertCircle,
  Plus,
  Plane,
  HeartHandshake,
  Fingerprint,
} from 'lucide-react';

/**
 * IMP-03 (DEMO-04/DEMO-08, Option B+): this card is a static sample of the
 * repeat-traveler memory panel. It deliberately takes no props and writes
 * nothing to the pipeline:
 *
 * - The former `customerMessage` prop was never read — dead input removed.
 * - The former `onApplyPreferences` callback injected fabricated preferences
 *   (vegan/aisle/loyalty numbers) into the real Agent Notes store, which feeds
 *   pipeline runs — removed entirely rather than disabled, because the card is
 *   sample content and must never mutate real state.
 * - Loyalty numbers are obviously fake (#000000000 / #00000000) and every
 *   provenance source is marked "Sample:" so nothing reads as tenant-scoped.
 *
 * Real recall wiring (GET /api/v1/customers/memory) is the later Option A
 * slice — see Docs/exploration/DEMO04_SAMPLE_PROFILE_PROVENANCE_2026-08-31.md.
 */
export function RepeatTravelerRecallCard() {
  const [showAddForm, setShowAddForm] = useState(false);
  const [newPreference, setNewPreference] = useState('');
  const [isPermanentSafety, setIsPermanentSafety] = useState(false);
  const [saveStatus, setSaveStatus] = useState<string | null>(null);

  // Sample content only — badged "Sample data", no real tenant data anywhere.
  const traveler = {
    id: 'cust_sample_demo',
    name: 'Alex Morgan',
    tripsCount: 3,
    vipStatus: 'Delta Diamond Medallion',
    preferences: [
      {
        id: 'pref_1',
        category: 'Medical / Dietary Safety',
        summary: 'Strict Vegan Meals on all flights and dining',
        isPermanent: true,
        freshness: 100,
        source: 'Sample: Direct Message',
      },
      {
        id: 'pref_2',
        category: 'Seating Choice',
        summary: 'Aisle seat preferred on long-haul transatlantic sectors',
        isPermanent: false,
        freshness: 88,
        source: 'Sample: Ticket Scan',
      },
      {
        id: 'pref_3',
        category: 'Loyalty Credentials',
        summary: 'Delta SkyMiles #000000000 · Marriott Bonvoy #00000000',
        isPermanent: false,
        freshness: 95,
        source: 'Sample: Loyalty Sync',
      },
    ],
  };

  const handleSaveNew = () => {
    if (!newPreference.trim()) return;
    setSaveStatus('Sample only — nothing was saved. Real memories are stored by the memory engine.');
    setNewPreference('');
    setShowAddForm(false);
  };

  return (
    <div className="rounded-xl border border-[#30363d] bg-[#161b22] p-4 space-y-3">
      {/* Card Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2.5 border-b border-[#21262d]">
        <div className="flex items-center gap-2.5">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-[#58a6ff]/10 text-[#58a6ff] border border-[#58a6ff]/20">
            <Brain className="h-4 w-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-ui-xs font-semibold text-[#e6edf3] tracking-wide">{traveler.name}</span>
              <span className="text-[10px] px-2 py-0.5 rounded-md bg-[#21262d] text-[#79c0ff] font-medium border border-[#30363d]">
                Repeat Client ({traveler.tripsCount} Bookings)
              </span>
              <span className="text-[10px] px-2 py-0.5 rounded-md bg-[#d29922]/10 text-[#e3b341] font-medium border border-[#d29922]/20">
                {traveler.vipStatus}
              </span>
            </div>
            <p className="text-[11px] text-[#8b949e] mt-0.5">
              Sample of the repeat-traveler memory panel — real recalls appear here once your agency has booking history.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* IMP-03: visible honesty badge — this is illustrative content, not a recall. */}
          <span
            data-testid="sample-data-badge"
            className="px-2.5 py-1 rounded-md bg-[#d29922]/10 text-[#e3b341] text-[10px] font-semibold uppercase tracking-wide border border-[#d29922]/30"
          >
            Sample data
          </span>

          <button
            onClick={() => setShowAddForm(!showAddForm)}
            className="px-2.5 py-1 rounded-md bg-[#21262d] hover:bg-[#30363d] text-[#c9d1d9] text-ui-xs font-medium transition-colors flex items-center gap-1 border border-[#30363d]"
          >
            <Plus className="h-3 w-3" />
            {showAddForm ? 'Cancel' : 'Add Note'}
          </button>
        </div>
      </div>

      {/* Preferences Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-2.5">
        {traveler.preferences.map((p) => (
          <div
            key={p.id}
            className="p-2.5 rounded-lg bg-[#0d1117] border border-[#21262d] space-y-1"
          >
            <div className="flex items-center justify-between text-[11px]">
              <span className="font-semibold text-[#79c0ff]">{p.category}</span>
              <span className="text-[10px] font-medium text-[#3fb950]">
                {p.isPermanent ? '🛡️ Permanent Safety' : `${p.freshness}% Fresh`}
              </span>
            </div>
            <p className="text-ui-xs text-[#c9d1d9]">{p.summary}</p>
            <p className="text-[10px] text-[#8b949e] font-mono pt-0.5">
              Source: {p.source}
            </p>
          </div>
        ))}
      </div>

      {/* Add New Preference Form (sample demonstration — saves nothing) */}
      {showAddForm && (
        <div className="p-3 rounded-lg bg-[#0d1117] border border-[#30363d] space-y-2.5">
          <div className="flex items-center justify-between text-ui-xs text-[#c9d1d9] font-medium">
            <span>Log New Persistent Preference for {traveler.name} (Sample)</span>
            <label className="flex items-center gap-1.5 cursor-pointer text-[11px] text-[#8b949e]">
              <input
                type="checkbox"
                checked={isPermanentSafety}
                onChange={(e) => setIsPermanentSafety(e.target.checked)}
                className="rounded border-[#30363d] bg-[#161b22] text-[#58a6ff]"
              />
              <span>Permanent Safety (Allergy/Medical)</span>
            </label>
          </div>
          <div className="flex gap-2">
            <input
              type="text"
              value={newPreference}
              onChange={(e) => setNewPreference(e.target.value)}
              placeholder="e.g. Always prefers high-floor quiet rooms away from elevator..."
              className="flex-1 bg-[#161b22] border border-[#30363d] rounded-lg px-3 py-1.5 text-ui-xs text-[#e6edf3] focus:outline-none focus:border-[#58a6ff]"
            />
            <button
              onClick={handleSaveNew}
              className="px-3 py-1.5 bg-[#1f6feb] hover:bg-[#388bfd] text-white rounded-lg text-ui-xs font-medium"
            >
              Save Fact
            </button>
          </div>
        </div>
      )}

      {saveStatus && (
        <div className="p-2 rounded-lg bg-[#d29922]/10 border border-[#d29922]/30 text-ui-xs text-[#e3b341] font-medium">
          {saveStatus}
        </div>
      )}
    </div>
  );
}
