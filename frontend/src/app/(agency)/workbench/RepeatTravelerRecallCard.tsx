'use client';

import React, { useState } from 'react';
import {
  Brain,
  ShieldCheck,
  UserCheck,
  Sparkles,
  CheckCircle2,
  AlertCircle,
  Plus,
  Plane,
  HeartHandshake,
  Fingerprint,
} from 'lucide-react';

interface RepeatTravelerRecallCardProps {
  customerMessage: string;
  onApplyPreferences?: (preferences: Record<string, any>) => void;
}

export function RepeatTravelerRecallCard({
  customerMessage,
  onApplyPreferences,
}: RepeatTravelerRecallCardProps) {
  const [isApplied, setIsApplied] = useState(false);
  const [showAddForm, setShowAddForm] = useState(false);
  const [newPreference, setNewPreference] = useState('');
  const [isPermanentSafety, setIsPermanentSafety] = useState(false);
  const [saveStatus, setSaveStatus] = useState<string | null>(null);

  // Simulated repeat traveler memory match
  const traveler = {
    id: 'cust_alex_m',
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
        source: 'Direct Message (Trip #9842)',
      },
      {
        id: 'pref_2',
        category: 'Seating Choice',
        summary: 'Aisle seat preferred on long-haul transatlantic sectors',
        isPermanent: false,
        freshness: 88,
        source: 'Verified Ticket Scan',
      },
      {
        id: 'pref_3',
        category: 'Loyalty Credentials',
        summary: 'Delta SkyMiles #928410294 · Marriott Bonvoy #48192041',
        isPermanent: false,
        freshness: 95,
        source: 'Passport & Loyalty Sync',
      },
    ],
  };

  const handleApply = () => {
    setIsApplied(true);
    if (onApplyPreferences) {
      onApplyPreferences({
        dietary: 'Strict Vegan',
        seating: 'Aisle',
        loyalty_delta: '928410294',
        loyalty_marriott: '48192041',
      });
    }
  };

  const handleSaveNew = () => {
    if (!newPreference.trim()) return;
    setSaveStatus('Saving to permanent traveler profile...');
    setTimeout(() => {
      setSaveStatus('✅ Saved: Added to Alex Morgan’s permanent profile memory.');
      setNewPreference('');
      setShowAddForm(false);
    }, 400);
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
              Verified historical profile recalled from agency memory.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowAddForm(!showAddForm)}
            className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium transition-colors flex items-center gap-1 border border-slate-700"
          >
            <Plus className="h-3 w-3" />
            {showAddForm ? 'Cancel' : 'Add Note'}
          </button>

          <button
            onClick={handleApply}
            disabled={isApplied}
            className={`px-3.5 py-1 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 shadow-md ${
              isApplied
                ? 'bg-emerald-600/30 text-emerald-300 border border-emerald-500/40 cursor-default'
                : 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-indigo-600/20'
            }`}
          >
            {isApplied ? (
              <>
                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
                Applied to Quote
              </>
            ) : (
              <>
                <Sparkles className="h-3.5 w-3.5" />
                Apply to Proposal
              </>
            )}
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

      {/* Add New Preference Form */}
      {showAddForm && (
        <div className="p-3 rounded-lg bg-slate-950 border border-indigo-500/30 space-y-2.5">
          <div className="flex items-center justify-between text-xs text-slate-300 font-medium">
            <span>Log New Persistent Preference for Alex Morgan</span>
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
        <div className="p-2 rounded-lg bg-emerald-950/40 border border-emerald-500/30 text-xs text-emerald-300 font-medium">
          {saveStatus}
        </div>
      )}
    </div>
  );
}
