'use client';

import React, { useState } from 'react';
import {
  Brain,
  ShieldCheck,
  Clock,
  Trash2,
  Search,
  Sparkles,
  Layers,
  Fingerprint,
  FileCheck,
  History,
  Lock,
  CheckCircle2,
  AlertCircle,
  Calendar,
  UserCheck,
} from 'lucide-react';

export function MemoryArchitectPanel() {
  const [activeTier, setActiveTier] = useState<'all' | 'working' | 'episodic' | 'semantic' | 'procedural' | 'preference'>('all');
  
  // Ingest form state
  const [entityId, setEntityId] = useState('Alex Morgan (cust_alex_m)');
  const [rawText, setRawText] = useState('Traveler strictly requires vegan meals and prefers aisle seating on transatlantic flights.');
  const [sourceType, setSourceType] = useState('traveler_direct');
  const [isSafetyCritical, setIsSafetyCritical] = useState(true);
  const [ingestStatus, setIngestStatus] = useState<string | null>(null);

  // Freshness & Expiry simulation state
  const [preferenceCategory, setPreferenceCategory] = useState<'allergy' | 'loyalty' | 'seating' | 'vibe'>('seating');
  const [elapsedMonths, setElapsedMonths] = useState<number>(3); // 3 months ago

  // GDPR state
  const [gdprTarget, setGdprTarget] = useState('Alex Morgan (cust_alex_m)');
  const [gdprCert, setGdprCert] = useState<any | null>(null);

  // Search state
  const [searchQuery, setSearchQuery] = useState('vegan aisle');
  const [searchResults] = useState<any[]>([
    {
      id: 'mem_a910f2c',
      tier: 'semantic',
      category: 'Dietary & Medical Safety',
      summary: 'Traveler strictly requires vegan meals on all flights and hotels.',
      confidence: 1.0,
      isPermanent: true,
      freshness: 100,
      provenance: 'Direct Message from Traveler (Trip #9842)',
      hash: 'e3b0c442...855',
    },
    {
      id: 'mem_7721b01',
      tier: 'semantic',
      category: 'Seating Preference',
      summary: 'Aisle seating preferred on long-haul transatlantic sectors.',
      confidence: 0.95,
      isPermanent: false,
      freshness: 88,
      provenance: 'Verified Passport / Ticket Record',
      hash: 'ca978112...8bb',
    },
  ]);

  // Compute freshness score and half-life based on selected category
  const getCategoryDetails = () => {
    switch (preferenceCategory) {
      case 'allergy':
        return { name: 'Medical / Allergy Constraint', halfLifeMonths: Infinity, isPermanent: true };
      case 'loyalty':
        return { name: 'Loyalty Account & Passport', halfLifeMonths: 36, isPermanent: false };
      case 'seating':
        return { name: 'Seating & Cabin Preference', halfLifeMonths: 24, isPermanent: false };
      case 'vibe':
        return { name: 'Seasonal Trip Vibe / Pace', halfLifeMonths: 6, isPermanent: false };
    }
  };

  const currentDetails = getCategoryDetails();
  const freshnessPercent = currentDetails.isPermanent
    ? 100
    : Math.max(0, Math.min(100, Math.round(100 * Math.pow(2, -elapsedMonths / currentDetails.halfLifeMonths))));

  const isFresh = freshnessPercent >= 35;

  const handleSimulateIngest = () => {
    setIngestStatus('Evaluating source authority and verifying signal...');
    setTimeout(() => {
      setIngestStatus('✅ Verified & Saved: Categorized as Dietary Safety & Seating Preference. Assigned SHA-256 Provenance Hash.');
    }, 500);
  };

  const handleExecuteGDPR = () => {
    setGdprCert({
      certificate_id: 'GDPR-ERASURE-2026-98A7',
      customer_id: gdprTarget,
      records_purged: 2,
      erased_at: new Date().toUTCString(),
      verification_signature: '7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069',
    });
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="rounded-2xl border border-blue-500/20 bg-gradient-to-r from-blue-950/40 via-indigo-950/20 to-slate-900/60 p-6 shadow-xl backdrop-blur-md">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-500/20 text-blue-400 border border-blue-400/30">
                <Brain className="h-4 w-4" />
              </div>
              <h2 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
                Customer Profile Memory & Intelligence
                <span className="text-xs px-2.5 py-0.5 rounded-full bg-blue-500/10 text-blue-300 border border-blue-500/30 font-medium">
                  Autonomous Curation
                </span>
              </h2>
            </div>
            <p className="text-sm text-slate-400 max-w-2xl">
              Persistent memory across bookings with automatic noise filtering, safety guarantees, preference freshness tracking, and one-click GDPR erasure.
            </p>
          </div>
          <div className="flex items-center gap-2 bg-slate-900/80 px-4 py-2 rounded-xl border border-slate-800 text-xs text-slate-300">
            <ShieldCheck className="h-4 w-4 text-emerald-400" />
            <span>Multi-Tenant Isolation: <strong>Agency Secure</strong></span>
          </div>
        </div>
      </div>

      {/* 5-Tier Selector Tabs */}
      <div className="flex flex-wrap gap-2 p-1.5 bg-slate-900/60 rounded-xl border border-slate-800">
        {[
          { key: 'all', label: 'All Records', icon: Layers },
          { key: 'working', label: 'Active Run (Working Context)', icon: Clock },
          { key: 'episodic', label: 'Trip History (Episodic Recall)', icon: History },
          { key: 'semantic', label: 'Traveler Profile (Semantic CRM)', icon: Fingerprint },
          { key: 'procedural', label: 'Agency Playbooks (Rules)', icon: FileCheck },
          { key: 'preference', label: 'Agency Settings', icon: Lock },
        ].map((t) => {
          const Icon = t.icon;
          const isSelected = activeTier === t.key;
          return (
            <button
              key={t.key}
              onClick={() => setActiveTier(t.key as any)}
              className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-medium transition-all ${
                isSelected
                  ? 'bg-blue-600 text-white shadow-md shadow-blue-500/20'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <Icon className="h-3.5 w-3.5" />
              {t.label}
            </button>
          );
        })}
      </div>

      {/* Main Grid: Intake & Smart Search */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Module 1: Verified Preference Intake */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5 space-y-4 backdrop-blur-sm">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-blue-400" />
              Verified Preference Intake
            </h3>
            <span className="text-[11px] text-emerald-400 bg-emerald-950/50 border border-emerald-500/30 px-2 py-0.5 rounded-full font-medium">
              Auto-Curation Active
            </span>
          </div>
          <p className="text-xs text-slate-400">
            Captures traveler preferences, checks signal authenticity, and links them to the traveler profile.
          </p>

          <div className="space-y-3 text-xs">
            <div>
              <label className="text-slate-400 block mb-1 font-medium">Target Traveler</label>
              <input
                type="text"
                value={entityId}
                onChange={(e) => setEntityId(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
              />
            </div>

            <div>
              <label className="text-slate-400 block mb-1 font-medium">Traveler Note / Stated Preference</label>
              <textarea
                rows={2}
                value={rawText}
                onChange={(e) => setRawText(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div>
                <label className="text-slate-400 block mb-1 font-medium">Source of Information</label>
                <select
                  value={sourceType}
                  onChange={(e) => setSourceType(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                >
                  <option value="traveler_direct">Direct Message / Email (100% Authority)</option>
                  <option value="verified_document">Verified Passport / Booking Scan (95%)</option>
                  <option value="agent_manual">Agent Confirmed (90%)</option>
                  <option value="system_inferred">AI Extracted from Notes (75%)</option>
                </select>
              </div>

              <div className="flex items-center pt-2 md:pt-6">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={isSafetyCritical}
                    onChange={(e) => setIsSafetyCritical(e.target.checked)}
                    className="rounded border-slate-700 bg-slate-950 text-blue-500 focus:ring-0"
                  />
                  <span className="text-slate-300 font-medium">🛡️ Medical / Allergy (Never Expires)</span>
                </label>
              </div>
            </div>

            <button
              onClick={handleSimulateIngest}
              className="w-full mt-2 py-2 px-4 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-medium text-xs transition-colors flex items-center justify-center gap-2 shadow-lg shadow-blue-600/20"
            >
              <UserCheck className="h-3.5 w-3.5" />
              Save to Traveler Profile
            </button>

            {ingestStatus && (
              <div className="p-3 rounded-lg bg-blue-950/40 border border-blue-500/30 text-xs text-blue-200">
                {ingestStatus}
              </div>
            )}
          </div>
        </div>

        {/* Module 2: Smart Profile Search & Recall */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5 space-y-4 backdrop-blur-sm">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white flex items-center gap-2">
              <Search className="h-4 w-4 text-indigo-400" />
              Smart Profile Search & Recall
            </h3>
            <span className="text-[11px] text-slate-400 font-medium">Safety Filter: Active</span>
          </div>
          <p className="text-xs text-slate-400">
            Quickly query traveler habits, seating preferences, and loyalty details for upcoming trip proposals.
          </p>

          <div className="flex gap-2">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by keyword (e.g. vegan, aisle, delta)..."
              className="flex-1 bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
            />
            <button className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-medium transition-colors">
              Search
            </button>
          </div>

          <div className="space-y-2.5 max-h-[220px] overflow-y-auto pr-1">
            {searchResults.map((res) => (
              <div key={res.id} className="p-3 rounded-lg bg-slate-950/80 border border-slate-800/80 space-y-1.5">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold text-indigo-300 flex items-center gap-1.5">
                    <span className="h-2 w-2 rounded-full bg-emerald-400" />
                    {res.category}
                  </span>
                  <span className="text-emerald-400 font-medium text-[11px]">
                    {res.isPermanent ? 'Permanent Safety' : `${res.freshness}% Fresh`}
                  </span>
                </div>
                <p className="text-xs text-slate-200">{res.summary}</p>
                <div className="flex items-center justify-between text-[11px] text-slate-400 pt-1 border-t border-slate-900">
                  <span>Source: {res.provenance}</span>
                  <span className="text-slate-500 font-mono text-[10px]">ID: {res.id}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>

      {/* Module 3: Freshness Simulator & GDPR Console */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Freshness & Expiry Simulator */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5 space-y-4 backdrop-blur-sm">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white flex items-center gap-2">
              <Calendar className="h-4 w-4 text-amber-400" />
              Traveler Preference Freshness & Expiry
            </h3>
            <span className={`text-xs font-bold px-2.5 py-0.5 rounded-full ${
              isFresh
                ? 'bg-emerald-950 text-emerald-300 border border-emerald-500/30'
                : 'bg-amber-950 text-amber-300 border border-amber-500/30'
            }`}>
              {currentDetails.isPermanent
                ? 'Permanent (100%)'
                : `${freshnessPercent}% Fresh (${isFresh ? 'Active' : 'Stale'})`}
            </span>
          </div>

          <p className="text-xs text-slate-400">
            Preferences naturally change over time. Waypoint OS tracks age and prompts agents to reconfirm stale preferences before quoting.
          </p>

          <div className="space-y-4 text-xs">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-slate-400 block mb-1 font-medium">Preference Type</label>
                <select
                  value={preferenceCategory}
                  onChange={(e) => setPreferenceCategory(e.target.value as any)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-amber-500"
                >
                  <option value="allergy">Medical / Food Allergy (Permanent)</option>
                  <option value="loyalty">Passport & Loyalty IDs (~3 Years)</option>
                  <option value="seating">Seating & Cabin Choice (~2 Years)</option>
                  <option value="vibe">Seasonal Destination Vibe (~6 Months)</option>
                </select>
              </div>

              <div>
                <label className="text-slate-400 block mb-1 font-medium">
                  Logged: <strong className="text-white">{elapsedMonths} months ago</strong>
                </label>
                <input
                  type="range"
                  min="0"
                  max="48"
                  value={elapsedMonths}
                  disabled={currentDetails.isPermanent}
                  onChange={(e) => setElapsedMonths(Number(e.target.value))}
                  className="w-full accent-amber-500 mt-2"
                />
              </div>
            </div>

            {/* Visual Freshness Bar */}
            <div className="space-y-1.5">
              <div className="flex justify-between text-[11px] text-slate-400">
                <span>Current Relevance</span>
                <span className="font-semibold text-white">{freshnessPercent}%</span>
              </div>
              <div className="w-full h-2.5 rounded-full bg-slate-950 overflow-hidden border border-slate-800">
                <div
                  className={`h-full rounded-full transition-all duration-300 ${
                    freshnessPercent > 70
                      ? 'bg-emerald-500'
                      : freshnessPercent >= 35
                      ? 'bg-amber-500'
                      : 'bg-rose-500'
                  }`}
                  style={{ width: `${freshnessPercent}%` }}
                />
              </div>
            </div>

            {/* Operator Explanation */}
            <div className="p-3 rounded-lg bg-slate-950 border border-slate-800/80">
              <div className="flex items-center gap-2 text-xs">
                {currentDetails.isPermanent ? (
                  <>
                    <CheckCircle2 className="h-4 w-4 text-emerald-400 flex-shrink-0" />
                    <span className="text-slate-200">
                      <strong>Permanent Safety Constraint:</strong> Will always apply to quotes and bookings without expiring.
                    </span>
                  </>
                ) : isFresh ? (
                  <>
                    <CheckCircle2 className="h-4 w-4 text-emerald-400 flex-shrink-0" />
                    <span className="text-slate-200">
                      <strong>Fresh & Active:</strong> Automatically included in new trip proposals.
                    </span>
                  </>
                ) : (
                  <>
                    <AlertCircle className="h-4 w-4 text-amber-400 flex-shrink-0" />
                    <span className="text-slate-200">
                      <strong>Needs Reconfirmation:</strong> Older than expected lifetime. The agent will prompt traveler to confirm on next quote.
                    </span>
                  </>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* GDPR Article 17 Erasure */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5 space-y-4 backdrop-blur-sm">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white flex items-center gap-2">
              <Trash2 className="h-4 w-4 text-rose-400" />
              Customer Privacy & Data Erasure (GDPR)
            </h3>
            <span className="text-[11px] text-rose-400 font-medium">One-Click Compliance</span>
          </div>

          <p className="text-xs text-slate-400">
            Permanently purges a customer's personal data upon request, replaces records with anonymous receipts, and issues a formal Certificate of Erasure.
          </p>

          <div className="space-y-3 text-xs">
            <div>
              <label className="text-slate-400 block mb-1 font-medium">Customer to Forget</label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={gdprTarget}
                  onChange={(e) => setGdprTarget(e.target.value)}
                  className="flex-1 bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-rose-500"
                />
                <button
                  onClick={handleExecuteGDPR}
                  className="px-4 py-2 bg-rose-600 hover:bg-rose-500 text-white rounded-lg font-medium text-xs transition-colors flex items-center gap-1.5 shadow-lg shadow-rose-600/20"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                  Forget Customer
                </button>
              </div>
            </div>

            {gdprCert && (
              <div className="p-3.5 rounded-lg bg-rose-950/30 border border-rose-500/30 space-y-1.5 text-xs">
                <div className="text-rose-300 font-bold flex items-center gap-1.5">
                  <CheckCircle2 className="h-4 w-4 text-rose-400" />
                  Official Certificate of Erasure: {gdprCert.certificate_id}
                </div>
                <div className="text-slate-300">
                  Customer ID: <span className="text-white font-medium">{gdprCert.customer_id}</span>
                </div>
                <div className="text-slate-400">
                  Status: All personal records purged & replaced with anonymous tombstone receipts.
                </div>
                <div className="text-[10px] text-slate-500 font-mono pt-1 border-t border-rose-900/40 break-all">
                  Verification Signature: {gdprCert.verification_signature}
                </div>
              </div>
            )}
          </div>
        </div>

      </div>
    </div>
  );
}
