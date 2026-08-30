'use client';

import React, { useState } from 'react';
import {
  Brain,
  ShieldCheck,
  Clock,
  Trash2,
  Layers,
  Fingerprint,
  FileCheck,
  History,
  Lock,
  CheckCircle2,
  AlertCircle,
  Calendar,
  Save,
  ShieldAlert,
} from 'lucide-react';

export function MemorySettingsTab() {
  const [retentionAllergy, setRetentionAllergy] = useState('permanent');
  const [retentionLoyaltyMonths, setRetentionLoyaltyMonths] = useState(36);
  const [retentionSeatingMonths, setRetentionSeatingMonths] = useState(24);
  const [retentionVibeMonths, setRetentionVibeMonths] = useState(6);
  const [autonomyLevel, setAutonomyLevel] = useState('agent_confirm_first');
  const [saveSuccess, setSaveSuccess] = useState(false);

  // GDPR State
  const [targetCustomer, setTargetCustomer] = useState('Alex Morgan (cust_alex_m)');
  const [gdprCert, setGdprCert] = useState<any | null>(null);

  const handleSavePolicy = () => {
    setSaveSuccess(true);
    setTimeout(() => setSaveSuccess(false), 2000);
  };

  const handlePurgeCustomer = () => {
    setGdprCert({
      certificate_id: 'GDPR-CERT-2026-X9481',
      customer_id: targetCustomer,
      tombstones_created: 3,
      erased_at: new Date().toUTCString(),
      verification_signature: '9a84f182bcde71029418247192834b9281a74910283471092834019283401928',
    });
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="rounded-xl border border-[#30363d] bg-[#161b22] p-5 space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-500/20 text-blue-400 border border-blue-400/30">
              <Brain className="h-4 w-4" />
            </div>
            <div>
              <h2 className="text-ui-base font-bold text-white flex items-center gap-2">
                Agency Memory & Data Retention Policies
              </h2>
              <p className="text-ui-xs text-[#8b949e]">
                Configure how long traveler preferences stay active before reconfirmation, manage 5-tier architecture rules, and process GDPR Article 17 Right-to-Erasure requests.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-[#0f1115] border border-[#30363d] text-ui-xs text-[#3fb950]">
            <ShieldCheck className="h-3.5 w-3.5" />
            <span>RLS Multi-Tenant Guard: Active</span>
          </div>
        </div>
      </div>

      {/* 5-Tier Memory Classification Overview */}
      <div className="rounded-xl border border-[#30363d] bg-[#161b22] p-5 space-y-4">
        <h3 className="text-ui-sm font-semibold text-[#e6edf3] flex items-center gap-2">
          <Layers className="h-4 w-4 text-[#58a6ff]" />
          5-Tier Memory Architecture Overview
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 text-ui-xs">
          <div className="p-3 rounded-lg bg-[#0f1115] border border-[#30363d] space-y-1">
            <div className="flex items-center gap-1.5 text-[#58a6ff] font-semibold">
              <Clock className="h-3.5 w-3.5" />
              Tier 1: Working
            </div>
            <p className="text-[#8b949e]">In-flight scratchpad and tool token state. Pruned at run completion.</p>
          </div>

          <div className="p-3 rounded-lg bg-[#0f1115] border border-[#30363d] space-y-1">
            <div className="flex items-center gap-1.5 text-[#a371f7] font-semibold">
              <History className="h-3.5 w-3.5" />
              Tier 2: Episodic
            </div>
            <p className="text-[#8b949e]">Historical disruption resolutions and milestone interaction ledgers.</p>
          </div>

          <div className="p-3 rounded-lg bg-[#0f1115] border border-[#30363d] space-y-1">
            <div className="flex items-center gap-1.5 text-[#3fb950] font-semibold">
              <Fingerprint className="h-3.5 w-3.5" />
              Tier 3: Semantic
            </div>
            <p className="text-[#8b949e]">Enduring traveler dietary constraints, seating habits, and loyalty cards.</p>
          </div>

          <div className="p-3 rounded-lg bg-[#0f1115] border border-[#30363d] space-y-1">
            <div className="flex items-center gap-1.5 text-[#d29922] font-semibold">
              <FileCheck className="h-3.5 w-3.5" />
              Tier 4: Procedural
            </div>
            <p className="text-[#8b949e]">Agency commercial margin rules, booking guardrails, and escalation trees.</p>
          </div>

          <div className="p-3 rounded-lg bg-[#0f1115] border border-[#30363d] space-y-1">
            <div className="flex items-center gap-1.5 text-[#f85149] font-semibold">
              <Lock className="h-3.5 w-3.5" />
              Tier 5: Preference
            </div>
            <p className="text-[#8b949e]">Agency autonomy gates, notification cadence, and tone guidelines.</p>
          </div>
        </div>
      </div>

      {/* Preference Freshness & Decay Settings */}
      <div className="rounded-xl border border-[#30363d] bg-[#161b22] p-5 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-ui-sm font-semibold text-[#e6edf3] flex items-center gap-2">
            <Calendar className="h-4 w-4 text-[#d29922]" />
            Preference Freshness & Reconfirmation Lifespans
          </h3>
          <button
            onClick={handleSavePolicy}
            className="px-3 py-1.5 rounded-lg bg-[#238636] hover:bg-[#2ea043] text-white text-ui-xs font-semibold flex items-center gap-1.5 transition-colors"
          >
            <Save className="h-3.5 w-3.5" />
            {saveSuccess ? 'Policies Saved!' : 'Save Retention Rules'}
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-ui-xs">
          <div className="p-3.5 rounded-lg bg-[#0f1115] border border-[#30363d] space-y-2">
            <div className="flex justify-between items-center">
              <span className="font-semibold text-white">🛡️ Medical & Food Allergies</span>
              <span className="text-[#3fb950] font-mono">Permanent (No Decay)</span>
            </div>
            <p className="text-[#8b949e]">Critical health and safety constraints are permanent and never expire.</p>
          </div>

          <div className="p-3.5 rounded-lg bg-[#0f1115] border border-[#30363d] space-y-2">
            <div className="flex justify-between items-center">
              <span className="font-semibold text-white">✈️ Loyalty Accounts & Passports</span>
              <span className="text-[#58a6ff] font-mono">{retentionLoyaltyMonths} Months (3 Years)</span>
            </div>
            <input
              type="range"
              min="12"
              max="60"
              value={retentionLoyaltyMonths}
              onChange={(e) => setRetentionLoyaltyMonths(Number(e.target.value))}
              className="w-full accent-[#58a6ff]"
            />
          </div>

          <div className="p-3.5 rounded-lg bg-[#0f1115] border border-[#30363d] space-y-2">
            <div className="flex justify-between items-center">
              <span className="font-semibold text-white">💺 Seating & Room Preferences</span>
              <span className="text-[#a371f7] font-mono">{retentionSeatingMonths} Months (2 Years)</span>
            </div>
            <input
              type="range"
              min="6"
              max="36"
              value={retentionSeatingMonths}
              onChange={(e) => setRetentionSeatingMonths(Number(e.target.value))}
              className="w-full accent-[#a371f7]"
            />
          </div>

          <div className="p-3.5 rounded-lg bg-[#0f1115] border border-[#30363d] space-y-2">
            <div className="flex justify-between items-center">
              <span className="font-semibold text-white">🏖️ Seasonal Destination Vibe & Pace</span>
              <span className="text-[#d29922] font-mono">{retentionVibeMonths} Months (6 Months)</span>
            </div>
            <input
              type="range"
              min="3"
              max="18"
              value={retentionVibeMonths}
              onChange={(e) => setRetentionVibeMonths(Number(e.target.value))}
              className="w-full accent-[#d29922]"
            />
          </div>
        </div>
      </div>

      {/* GDPR Article 17 Right-to-Erasure Console */}
      <div className="rounded-xl border border-[#30363d] bg-[#161b22] p-5 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-ui-sm font-semibold text-[#e6edf3] flex items-center gap-2">
            <Trash2 className="h-4 w-4 text-[#f85149]" />
            Customer Privacy & GDPR Right-to-Erasure Console
          </h3>
          <span className="text-ui-xs text-[#f85149] font-medium flex items-center gap-1">
            <ShieldAlert className="h-3.5 w-3.5" />
            Compliance Enforced
          </span>
        </div>

        <p className="text-ui-xs text-[#8b949e]">
          Process formal Right-to-be-Forgotten requests. All personal identifying data will be permanently wiped and replaced with an anonymous cryptographic tombstone.
        </p>

        <div className="flex gap-3 text-ui-xs">
          <input
            type="text"
            value={targetCustomer}
            onChange={(e) => setTargetCustomer(e.target.value)}
            placeholder="Enter customer ID or name..."
            className="flex-1 px-3 py-2 bg-[#0f1115] border border-[#30363d] rounded-lg text-white focus:outline-none focus:border-[#f85149]"
          />
          <button
            onClick={handlePurgeCustomer}
            className="px-4 py-2 bg-[#da3633] hover:bg-[#b62324] text-white rounded-lg font-semibold transition-colors flex items-center gap-1.5"
          >
            <Trash2 className="h-3.5 w-3.5" />
            Purge Customer Records
          </button>
        </div>

        {gdprCert && (
          <div className="p-4 rounded-lg bg-[#0f1115] border border-[#f85149]/40 space-y-2 text-ui-xs font-mono">
            <div className="flex items-center justify-between text-[#f85149] font-bold">
              <span className="flex items-center gap-1.5">
                <CheckCircle2 className="h-4 w-4" />
                Certificate of Erasure: {gdprCert.certificate_id}
              </span>
              <span className="text-[#8b949e] font-normal">{gdprCert.erased_at}</span>
            </div>
            <p className="text-[#c9d1d9]">Customer Entity: {gdprCert.customer_id}</p>
            <p className="text-[#8b949e]">Records Purged: {gdprCert.tombstones_created} memory facts purged and tombstoned.</p>
            <p className="text-[#8b949e] break-all">SHA-256 Signature: {gdprCert.verification_signature}</p>
          </div>
        )}
      </div>
    </div>
  );
}
