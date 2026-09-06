'use client';

import React, { useState, useEffect } from 'react';
import {
  Plane,
  MapPin,
  Calendar,
  AlertTriangle,
  Radio,
  FileText,
  ShieldCheck,
  CreditCard,
  PhoneCall,
  Clock,
  Compass,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Download,
} from 'lucide-react';

export default function TravelerCompanionPage() {
  const [sosActive, setSosActive] = useState(false);
  // GM-01/F-03 honesty: the SOS flow is a client-side simulation — no beacon
  // is transmitted, no concierge is contacted. The state models the demo flow
  // completing, not any real transmission.
  const [sosDemoComplete, setSosDemoComplete] = useState(false);
  const [activeDay, setActiveDay] = useState(1);
  const [isOffline, setIsOffline] = useState(false);

  useEffect(() => {
    // Check service worker registration
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('/sw.js').catch((err) => console.log('SW reg error:', err));
    }
  }, []);

  const handleTriggerSOS = () => {
    setSosActive(true);
    setTimeout(() => {
      setSosDemoComplete(true);
    }, 1500);
  };

  return (
    <div className="min-h-screen bg-[#090d16] text-slate-100 font-sans pb-16">
      {/* Mobile Sticky App Header */}
      <header className="sticky top-0 z-50 bg-[#090d16]/90 backdrop-blur-md border-b border-slate-800/80 px-4 py-3.5 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-indigo-600 to-indigo-400 flex items-center justify-center font-bold text-white shadow-lg shadow-indigo-500/20">
            W
          </div>
          <div>
            <span className="text-sm font-bold text-white tracking-tight block">Waypoint Companion</span>
            <span className="text-[10px] text-emerald-400 font-mono flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
              Trip Sync: Tokyo & Kyoto
            </span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-slate-800 text-slate-300 border border-slate-700">
            Offline Ready
          </span>
        </div>
      </header>

      {/* Main Container */}
      <main className="max-w-md mx-auto p-4 space-y-4">
        {/* GM-01 honesty banner: this page renders sample itinerary content. */}
        <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-[11px] text-amber-200 flex items-center gap-2">
          <span className="px-2 py-0.5 rounded-lg bg-amber-500/10 text-amber-300 text-[10px] font-semibold uppercase tracking-wide border border-amber-500/30">
            Sample data
          </span>
          <span>
            Demo preview with sample itinerary content — no real bookings, beacons, or transmissions are behind this page.
          </span>
        </div>

        {/* Live Flight Status Card */}
        <section className="rounded-2xl border border-indigo-500/30 bg-gradient-to-br from-indigo-950/40 via-slate-900 to-slate-900 p-4 shadow-xl relative overflow-hidden">
          <div className="flex items-center justify-between text-xs text-indigo-400 font-mono">
            <span className="flex items-center gap-1.5">
              <Plane className="w-3.5 h-3.5" /> Next Flight · British Airways
            </span>
            <span className="text-emerald-400 font-bold px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/20">
              ON TIME
            </span>
          </div>

          <div className="mt-3 flex items-center justify-between">
            <div>
              <span className="text-2xl font-black tracking-tight text-white">LHR</span>
              <span className="text-[11px] text-slate-400 block">London Heathrow</span>
            </div>
            <div className="flex flex-col items-center px-4">
              <span className="text-[10px] text-slate-400 font-mono">11h 45m · Nonstop</span>
              <div className="w-24 h-[2px] bg-slate-700 my-1 relative flex items-center justify-center">
                <Plane className="w-3 h-3 text-indigo-400 absolute" />
              </div>
              <span className="text-[10px] text-indigo-300 font-mono">Flight BA 178</span>
            </div>
            <div className="text-right">
              <span className="text-2xl font-black tracking-tight text-white">HND</span>
              <span className="text-[11px] text-slate-400 block">Tokyo Haneda</span>
            </div>
          </div>

          <div className="mt-3 pt-3 border-t border-slate-800 flex items-center justify-between text-xs">
            <div>
              <span className="text-slate-400 block text-[10px]">TERMINAL / GATE</span>
              <span className="font-bold text-white">T5 · Gate B22</span>
            </div>
            <div>
              <span className="text-slate-400 block text-[10px]">SEAT / CLASS</span>
              <span className="font-bold text-indigo-300">02A · Club World</span>
            </div>
            <div>
              <span className="text-slate-400 block text-[10px]">BOARDING</span>
              <span className="font-bold text-emerald-400">10:55 GMT</span>
            </div>
          </div>
        </section>

        {/* Emergency SOS Duty-of-Care Beacon */}
        <section className={`rounded-2xl border transition-all duration-300 p-4 ${
          sosActive
            ? 'border-red-500/60 bg-gradient-to-b from-red-950/60 to-slate-900 text-white shadow-2xl shadow-red-950/50'
            : 'border-slate-800 bg-slate-900/60 text-slate-300'
        }`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className={`p-2 rounded-xl ${sosActive ? 'bg-red-500 text-white animate-pulse' : 'bg-slate-800 text-slate-400'}`}>
                <Radio className="w-4 h-4" />
              </div>
              <div>
                <h3 className="text-xs font-bold text-white tracking-wide uppercase">24/7 Crisis SOS Beacon</h3>
                <p className="text-[10px] text-slate-400">Direct satellite & consular duty desk link</p>
              </div>
            </div>
            {!sosActive ? (
              <button
                onClick={handleTriggerSOS}
                className="px-3 py-1.5 bg-red-600 hover:bg-red-500 text-white text-xs font-bold rounded-xl shadow-lg shadow-red-600/30 transition-transform active:scale-95"
              >
                SIMULATE SOS (DEMO)
              </button>
            ) : (
              <span className="text-[10px] font-mono font-bold text-red-400 bg-red-500/20 px-2 py-1 rounded border border-red-500/30">
                BEACON ACTIVE
              </span>
            )}
          </div>

          {sosActive && (
            <div className="mt-3 p-2.5 rounded-xl bg-slate-950/80 border border-red-500/30 space-y-1.5 text-[11px] font-mono">
              <div className="flex items-center justify-between text-red-300">
                <span>GPS Telemetry:</span>
                <span className="font-bold text-white">35.6762° N, 139.6503° E (Tokyo)</span>
              </div>
              <div className="flex items-center justify-between text-slate-400">
                <span>Consular Protocol:</span>
                <span className="text-emerald-400 font-bold">
                  {sosDemoComplete ? 'SAMPLE CASE DOS-EMERG-JP-994 — flow simulated, nothing transmitted' : 'ENCRYPTING PAYLOAD...'}
                </span>
              </div>
              <div className="text-[10px] text-amber-300 pt-1 border-t border-slate-800">
                Demo only: no beacon was sent and no security concierge was contacted. In a real emergency contact local emergency services.
              </div>
            </div>
          )}
        </section>

        {/* Offline Day-by-Day Interactive Itinerary */}
        <section className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
              <Calendar className="w-3.5 h-3.5 text-indigo-400" />
              Day-by-Day Itinerary (Offline Cached)
            </h3>
            <span className="text-[10px] font-mono text-slate-400">10 Days Total</span>
          </div>

          {/* Day Selector Pills */}
          <div className="flex gap-2 overflow-x-auto pb-1 scrollbar-none">
            {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((d) => (
              <button
                key={d}
                onClick={() => setActiveDay(d)}
                className={`px-3 py-1.5 rounded-xl text-xs font-mono font-semibold shrink-0 transition-all ${
                  activeDay === d
                    ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                    : 'bg-slate-800 text-slate-400 hover:bg-slate-750'
                }`}
              >
                Day {d}
              </button>
            ))}
          </div>

          {/* Day Details */}
          <div className="space-y-2.5 pt-1">
            {activeDay === 1 && (
              <div className="space-y-2">
                <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-1">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-bold text-white">Private Luxury Airport Transfer</span>
                    <span className="text-[10px] font-mono text-indigo-400">15:30 JST</span>
                  </div>
                  <p className="text-[11px] text-slate-400">
                    Chauffeured Toyota Alphard Executive VIP from Tokyo Haneda to Aman Tokyo.
                  </p>
                  <div className="text-[10px] text-emerald-400 font-mono">Voucher #TF-HND-9912 (Confirmed)</div>
                </div>

                <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-1">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-bold text-white">Check-in: Aman Tokyo (Premier Room)</span>
                    <span className="text-[10px] font-mono text-indigo-400">16:30 JST</span>
                  </div>
                  <p className="text-[11px] text-slate-400">
                    Otemachi Tower, 1-5-6 Otemachi, Chiyoda-ku. Confirmed with VIP welcome amenities.
                  </p>
                  <div className="text-[10px] text-emerald-400 font-mono">Confirmation: AMAN-TYO-88219</div>
                </div>
              </div>
            )}

            {activeDay !== 1 && (
              <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-1">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-bold text-white">Curated Cultural Exploration — Day {activeDay}</span>
                  <span className="text-[10px] font-mono text-indigo-400">10:00 JST</span>
                </div>
                <p className="text-[11px] text-slate-400">
                  Private licensed English-speaking master guide and reserved VIP admissions.
                </p>
                <div className="text-[10px] text-emerald-400 font-mono">Status: Sample (nominal)</div>
              </div>
            )}
          </div>
        </section>

        {/* Digital Wallet & Documents Quick Access */}
        <section className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4 space-y-2.5">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
              <CreditCard className="w-3.5 h-3.5 text-indigo-400" />
              Digital Travel Wallet
            </h3>
            <span className="text-[10px] font-mono text-indigo-400">3 Passes</span>
          </div>

          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800 flex items-center justify-between">
              <div>
                <span className="font-bold text-white block">E-Ticket</span>
                <span className="text-[10px] text-slate-400">006-2345678901</span>
              </div>
              <Download className="w-4 h-4 text-indigo-400" />
            </div>

            <div className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800 flex items-center justify-between">
              <div>
                <span className="font-bold text-white block">Hotel Voucher</span>
                <span className="text-[10px] text-slate-400">HTL-AMAN-88219</span>
              </div>
              <Download className="w-4 h-4 text-indigo-400" />
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
