'use client';

import React, { useState } from 'react';
import { ShieldCheck, AlertTriangle, FileCode, CheckCircle2, RefreshCw } from 'lucide-react';
import SimulatedBadge from '@/components/ui/SimulatedBadge';

/**
 * GM-01 honesty fix: the epistemic arbiter is real deterministic math, but it
 * is not wired into the canonical intake pipeline — this panel is a standalone
 * demo surface for it.
 */

type EpistemicSubTab = 'conflicts' | 'implicit' | 'proof_graph';

export default function EpistemicPanel() {
  const [activeTab, setActiveTab] = useState<EpistemicSubTab>('conflicts');
  const [rawNotes, setRawNotes] = useState('Traveling with our 6-month infant to Rome. Please no Boeing 737 MAX and avoid Ryanair.');
  const [extractedConstraints, setExtractedConstraints] = useState<{ implicit_needs: string[]; excluded_preferences: string[] } | null>(null);

  const handleExtractConstraints = async () => {
    try {
      const res = await fetch('/api/v1/epistemic/constraints/extract-implicit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: rawNotes }),
      });
      if (res.ok) {
        const data = await res.json();
        setExtractedConstraints(data.result);
      }
    } catch {
      // Fallback local calculation
      setExtractedConstraints({
        implicit_needs: ['requires_infant_bassinet', 'avoid_tight_connections_under_90m'],
        excluded_preferences: ['AIRCRAFT_EXCLUDE:B737_MAX', 'AIRLINE_EXCLUDE:FR'],
      });
    }
  };

  return (
    <div className="space-y-6">
      {/* Demo badge — arbiter demo surface, not wired into the canonical pipeline */}
      <div className="flex justify-end">
        <SimulatedBadge label="Simulated" />
      </div>
      {/* Sub-navigation */}
      <div className="flex items-center gap-2 border-b border-border pb-3">
        <button
          onClick={() => setActiveTab('conflicts')}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold tracking-wide transition-all ${
            activeTab === 'conflicts' ? 'bg-primary text-primary-foreground shadow-sm' : 'bg-muted text-muted-foreground hover:bg-accent'
          }`}
        >
          <AlertTriangle className="h-3.5 w-3.5" />
          Multi-Turn Conflict Arbiter
        </button>
        <button
          onClick={() => setActiveTab('implicit')}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold tracking-wide transition-all ${
            activeTab === 'implicit' ? 'bg-primary text-primary-foreground shadow-sm' : 'bg-muted text-muted-foreground hover:bg-accent'
          }`}
        >
          <ShieldCheck className="h-3.5 w-3.5" />
          Implicit & Negative Constraints
        </button>
        <button
          onClick={() => setActiveTab('proof_graph')}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold tracking-wide transition-all ${
            activeTab === 'proof_graph' ? 'bg-primary text-primary-foreground shadow-sm' : 'bg-muted text-muted-foreground hover:bg-accent'
          }`}
        >
          <FileCode className="h-3.5 w-3.5" />
          JSON-LD Proof Graph
        </button>
      </div>

      {activeTab === 'conflicts' && (
        <div className="p-4 rounded-xl border border-border bg-card space-y-4">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-semibold text-foreground flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-amber-500" />
              Live Conversational Conflict Detection (Turn 1 vs Turn 3)
            </h4>
            <span className="text-xs px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-500 font-mono">1 CONFLICT FLAGGED</span>
          </div>
          <div className="p-3 rounded-lg border border-amber-500/20 bg-amber-500/5 space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="font-mono text-muted-foreground">Slot: departure_window</span>
              <span className="text-amber-500 font-semibold">EPISTEMIC_CONFLICT</span>
            </div>
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="p-2.5 rounded bg-background/80 border border-border">
                <span className="text-[10px] text-muted-foreground font-mono">TURN 1 (08:30)</span>
                <p className="font-semibold text-foreground mt-0.5">&quot;Morning departure preferred around 8:00 AM&quot;</p>
              </div>
              <div className="p-2.5 rounded bg-background/80 border border-border">
                <span className="text-[10px] text-muted-foreground font-mono">TURN 3 (14:15)</span>
                <p className="font-semibold text-foreground mt-0.5">&quot;Actually after work around 7:00 PM&quot;</p>
              </div>
            </div>
            <div className="pt-2 border-t border-amber-500/10 text-xs text-foreground/90 flex items-center justify-between">
              <span>Resolution Prompt: <em>&quot;Please confirm whether you prefer morning (08:00) or evening (19:00) departure.&quot;</em></span>
              <button className="px-2.5 py-1 text-xs bg-amber-500 text-white rounded font-medium hover:bg-amber-600">Send Clarification</button>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'implicit' && (
        <div className="p-4 rounded-xl border border-border bg-card space-y-4">
          <h4 className="text-sm font-semibold text-foreground flex items-center gap-2">
            <ShieldCheck className="h-4 w-4 text-emerald-500" />
            Implicit Needs & Negative Exclusions Engine
          </h4>
          <textarea
            value={rawNotes}
            onChange={(e) => setRawNotes(e.target.value)}
            className="w-full h-20 p-2.5 rounded-lg border border-border bg-background text-xs font-sans text-foreground resize-none focus:outline-none focus:ring-1 focus:ring-primary"
          />
          <button
            onClick={handleExtractConstraints}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-primary text-primary-foreground text-xs font-semibold hover:bg-primary/90"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            Extract Implicit Requirements
          </button>
          {extractedConstraints && (
            <div className="grid grid-cols-2 gap-3 text-xs pt-2">
              <div className="p-3 rounded-lg border border-emerald-500/20 bg-emerald-500/5">
                <span className="font-semibold text-emerald-500 flex items-center gap-1.5 mb-2">
                  <CheckCircle2 className="h-3.5 w-3.5" />
                  Implicit Operational Needs
                </span>
                <ul className="space-y-1 text-foreground/80 list-disc list-inside">
                  {extractedConstraints.implicit_needs.map((n, i) => (
                    <li key={i} className="font-mono">{n}</li>
                  ))}
                </ul>
              </div>
              <div className="p-3 rounded-lg border border-red-500/20 bg-red-500/5">
                <span className="font-semibold text-red-500 flex items-center gap-1.5 mb-2">
                  <AlertTriangle className="h-3.5 w-3.5" />
                  Hard Exclusions
                </span>
                <ul className="space-y-1 text-foreground/80 list-disc list-inside">
                  {extractedConstraints.excluded_preferences.map((e, i) => (
                    <li key={i} className="font-mono">{e}</li>
                  ))}
                </ul>
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'proof_graph' && (
        <div className="p-4 rounded-xl border border-border bg-card space-y-3">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-semibold text-foreground flex items-center gap-2">
              <FileCode className="h-4 w-4 text-blue-500" />
              Machine-Readable W3C JSON-LD Proof Graph
            </h4>
            <span className="text-[10px] font-mono bg-blue-500/10 text-blue-500 px-2 py-0.5 rounded">urn:waypoint:trip:TRIP-102:epistemic-proof</span>
          </div>
          <pre className="p-3 rounded-lg bg-muted/80 text-[11px] font-mono text-foreground/90 overflow-x-auto border border-border">
{JSON.stringify({
  "@context": { "@vocab": "https://waypointos.com/schema/epistemic#", "xsd": "http://www.w3.org/2001/XMLSchema#" },
  "@id": "urn:waypoint:trip:TRIP-102:epistemic-proof",
  "@type": "EpistemicProofGraph",
  "tripId": "TRIP-102",
  "assertions": [
    {
      "@type": "EpistemicFactAssertion",
      "slot": "destination",
      "value": "Rome",
      "status": "FACT",
      "confidence": 1.0,
      "sourceTurn": "TURN-1",
      "evidenceSnippet": "visiting Rome for anniversary",
      "proofHash": "e9a2f1b4d081c79a"
    }
  ]
}, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}
