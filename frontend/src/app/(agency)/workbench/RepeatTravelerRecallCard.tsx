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
    <div className="rounded-xl border border-indigo-500/30 bg-gradient-to-r from-indigo-950/30 via-slate-900/60 to-slate-950/80 p-4 shadow-lg backdrop-blur-sm space-y-3">
      {/* Card Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2.5 border-b border-indigo-500/20">
        <div className="flex items-center gap-2.5">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-indigo-500/20 text-indigo-400 border border-indigo-400/30">
            <Brain className="h-4 w-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-white tracking-wide">{traveler.name}</span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 font-medium border border-indigo-500/30">
                Repeat Client ({traveler.tripsCount} Bookings)
              </span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-300 font-medium border border-amber-500/20">
                {traveler.vipStatus}
              </span>
            </div>
            <p className="text-[11px] text-slate-400">
              Sample of the repeat-traveler memory panel — real recalls appear here once your agency has booking history.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* IMP-03: visible honesty badge — this is illustrative content, not a recall. */}
          <span
            data-testid="sample-data-badge"
            className="px-2.5 py-1 rounded-lg bg-amber-500/10 text-amber-300 text-[10px] font-semibold uppercase tracking-wide border border-amber-500/30"
          >
            Sample data
          </span>

          <button
            onClick={() => setShowAddForm(!showAddForm)}
            className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium transition-colors flex items-center gap-1 border border-slate-700"
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
            className="p-2.5 rounded-lg bg-slate-950/70 border border-slate-800/80 space-y-1"
          >
            <div className="flex items-center justify-between text-[11px]">
              <span className="font-semibold text-indigo-300">{p.category}</span>
              <span className="text-[10px] font-medium text-emerald-400">
                {p.isPermanent ? '🛡️ Permanent Safety' : `${p.freshness}% Fresh`}
              </span>
            </div>
            <p className="text-xs text-slate-200">{p.summary}</p>
            <p className="text-[10px] text-slate-500 font-mono pt-0.5">
              Source: {p.source}
            </p>
          </div>
        ))}
      </div>

      {/* Add New Preference Form (sample demonstration — saves nothing) */}
      {showAddForm && (
        <div className="p-3 rounded-lg bg-slate-950 border border-indigo-500/30 space-y-2.5">
          <div className="flex items-center justify-between text-xs text-slate-300 font-medium">
            <span>Log New Persistent Preference for {traveler.name} (Sample)</span>
            <label className="flex items-center gap-1.5 cursor-pointer text-[11px] text-slate-400">
              <input
                type="checkbox"
                checked={isPermanentSafety}
                onChange={(e) => setIsPermanentSafety(e.target.checked)}
                className="rounded border-slate-700 bg-slate-900 text-indigo-500"
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
              className="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-indigo-500"
            />
            <button
              onClick={handleSaveNew}
              className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-medium"
            >
              Save Fact
            </button>
          </div>
        </div>
      )}

      {saveStatus && (
        <div className="p-2 rounded-lg bg-amber-950/40 border border-amber-500/30 text-xs text-amber-300 font-medium">
          {saveStatus}
        </div>
      )}
    </div>
  );
}
