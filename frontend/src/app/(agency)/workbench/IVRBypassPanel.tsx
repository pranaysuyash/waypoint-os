'use client';

import React, { useState } from 'react';
import { PhoneCall, Radio, UserCheck, Volume2 } from 'lucide-react';
import SimulatedBadge from '@/components/ui/SimulatedBadge';

/**
 * GM-01 honesty fix: the IVR bypass bot is a deterministic simulator. The
 * "call" synthesizes a transcript, the hold window matches the simulator's
 * actual constant (~145 seconds, ~2 minutes — not an 18-minute queue), and no
 * telephony occurs.
 */

export default function IVRBypassPanel() {
  const [carrier, setCarrier] = useState('BA');
  const [pnr, setPnr] = useState('6XY7ZQ');
  const [isCalling, setIsCalling] = useState(false);
  const [session, setSession] = useState<{
    session_id: string;
    carrier_code: string;
    pnr_locator: string;
    status: string;
    dtmf_tones_sent: string[];
    live_audio_transcript: string;
    carrier_agent_name: string;
    hold_duration_seconds: number;
  } | null>(null);

  const handleDispatchCall = async () => {
    setIsCalling(true);
    try {
      const res = await fetch('/api/v1/ivr-bypass/calls/dispatch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          carrier_code: carrier,
          pnr_locator: pnr,
          advisor_phone: '+1-415-555-0144',
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setSession(data.call_session);
      }
    } catch {
      // Fallback local preview
      setSession({
        session_id: 'CALL-B9182A',
        carrier_code: carrier,
        pnr_locator: pnr,
        status: 'on_hold_listening',
        dtmf_tones_sent: ['1', '2', '4'],
        live_audio_transcript: 'Dialed +1-800-452-1201 -> DTMF Sequence 1 -> 2 -> 4 -> In Hold Queue (hold window: ~2 minutes — simulated, no real call placed)',
        carrier_agent_name: 'Waiting in Queue',
        hold_duration_seconds: 145,
      });
    } finally {
      setIsCalling(false);
    }
  };

  const handleSimulatePickup = async () => {
    if (!session) return;
    try {
      const res = await fetch('/api/v1/ivr-bypass/calls/bridge', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: session.session_id,
          carrier_agent_name: 'Sarah (BA Trade Support Lead)',
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setSession(data.call_session);
      }
    } catch {
      setSession({
        ...session,
        status: 'bridged_to_advisor',
        carrier_agent_name: 'Sarah (BA Trade Support Lead)',
        live_audio_transcript: "Carrier human agent answered: 'British Airways Trade Desk, Sarah speaking.' -> Audio bridged to advisor +1-415-555-0144.",
      });
    }
  };

  return (
    <div className="p-4 rounded-xl border border-border bg-card space-y-4">
      <div className="flex items-center justify-between gap-2">
        <h4 className="text-sm font-semibold text-foreground flex items-center gap-2">
          <PhoneCall className="h-4 w-4 text-violet-400" />
          Voice AI & Airline Trade Support IVR Bypass (Simulator)
        </h4>
        <div className="flex items-center gap-2 shrink-0">
          <SimulatedBadge label="Simulated" />
          <span className="text-[10px] font-mono bg-violet-500/10 text-violet-400 px-2 py-0.5 rounded">FRONTIER 3 · TELEPHONY SIMULATOR (NO REAL CALLS)</span>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-3">
        <div>
          <label className="text-[10px] font-mono text-muted-foreground block mb-1">Carrier Airline</label>
          <select
            value={carrier}
            onChange={(e) => setCarrier(e.target.value)}
            className="w-full p-2 text-xs font-semibold rounded border border-border bg-background text-foreground"
          >
            <option value="BA">British Airways (Trade Desk)</option>
            <option value="DL">Delta Air Lines (Global Sales)</option>
            <option value="AF">Air France (B2B Trade)</option>
          </select>
        </div>
        <div>
          <label className="text-[10px] font-mono text-muted-foreground block mb-1">PNR Record Locator</label>
          <input
            value={pnr}
            onChange={(e) => setPnr(e.target.value.toUpperCase())}
            className="w-full p-2 text-xs font-mono font-bold rounded border border-border bg-background text-foreground"
          />
        </div>
        <div className="flex items-end">
          <button
            onClick={handleDispatchCall}
            disabled={isCalling}
            className="w-full py-2 px-3 rounded-lg bg-violet-600 text-white text-xs font-semibold hover:bg-violet-700 flex items-center justify-center gap-1.5"
          >
            <Radio className={`h-3.5 w-3.5 ${isCalling ? 'animate-pulse' : ''}`} />
            {isCalling ? 'Dialing IVR...' : 'Dial & Bypass Carrier IVR'}
          </button>
        </div>
      </div>

      {session && (
        <div className="p-4 rounded-xl border border-violet-500/20 bg-violet-500/5 space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <span className="text-xs font-mono text-violet-400 font-semibold">{session.session_id}</span>
              <h5 className="text-sm font-bold text-foreground">{session.carrier_code} Trade Desk Automation</h5>
            </div>
            <div className="flex items-center gap-2">
              <span className={`px-2 py-0.5 rounded text-xs font-semibold flex items-center gap-1 ${
                session.status === 'bridged_to_advisor'
                  ? 'bg-emerald-500/10 text-emerald-400'
                  : 'bg-amber-500/10 text-amber-400'
              }`}>
                {session.status === 'bridged_to_advisor' ? <UserCheck className="h-3.5 w-3.5" /> : <Volume2 className="h-3.5 w-3.5 animate-pulse" />}
                {session.status.replace(/_/g, ' ').toUpperCase()}
              </span>
            </div>
          </div>

          <div className="p-3 rounded-lg border border-border bg-background text-xs space-y-1.5 font-mono">
            <span className="text-[10px] text-muted-foreground block">SIMULATED TELEPHONY TRANSCRIPT & DTMF LOG (NOT A REAL CALL):</span>
            <p className="text-foreground text-[11px] leading-relaxed">{session.live_audio_transcript}</p>
            {typeof session.hold_duration_seconds === 'number' && (
              <p className="text-[10px] text-muted-foreground">Simulated hold window: ~{Math.max(1, Math.round(session.hold_duration_seconds / 60))} minute(s)</p>
            )}
          </div>

          {session.status !== 'bridged_to_advisor' && (
            <div className="flex items-center justify-between pt-1">
              <span className="text-[11px] text-muted-foreground">
                Bot is waiting through hold music on behalf of advisor.
              </span>
              <button
                onClick={handleSimulatePickup}
                className="py-1.5 px-3 bg-emerald-600 text-white rounded text-xs font-semibold hover:bg-emerald-700 flex items-center gap-1"
              >
                <UserCheck className="h-3.5 w-3.5" />
                Simulate Carrier Representative Answer
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
