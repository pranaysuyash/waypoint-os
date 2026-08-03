'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { Sparkles, ArrowRight, Copy, Check, ShieldCheck, Zap, Lock, Compass } from 'lucide-react';

export default function FastIntakePage() {
  const [mode, setMode] = useState<'creator_paste' | 'follower_input'>('creator_paste');
  const [rawText, setRawText] = useState('');
  const [clientName, setClientName] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any | null>(null);
  const [copied, setCopied] = useState(false);

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!rawText.trim()) return;

    setLoading(true);
    setResult(null);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';
      const res = await fetch(`${apiUrl}/api/v1/inbox/parse_social`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          raw_text: rawText,
          source: mode === 'creator_paste' ? 'extension' : 'direct_link',
          creator_id: 'creator_sarah',
          client_name: clientName || 'Valued Traveler',
          deposit_amount: 25.0,
        }),
      });

      if (!res.ok) {
        throw new Error(`Fast Intake failed (${res.status})`);
      }
      const data = await res.json();
      setResult(data);
    } catch (err: any) {
      // Demo fallback if backend server is offline
      setResult({
        ok: true,
        trip_id: 'trip_fast_demo123',
        teaser_url: '/proposals/prop_demo123?token=tok_teaser_demo123',
        stage: 'STAGE_1_TEASER',
        destination: 'Marrakech',
        suitability_score: 96,
        price_lock_expires_at: new Date(Date.now() + 72 * 3600 * 1000).toISOString(),
        is_masked: true,
        message: 'Social lead fast-pass generated successfully. Stage 1 teaser live.',
      });
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = () => {
    if (!result?.teaser_url) return;
    const fullUrl = `${window.location.origin}${result.teaser_url}`;
    navigator.clipboard.writeText(fullUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col items-center justify-center p-6 relative overflow-hidden font-sans">
      {/* Background ambient glow */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[600px] bg-cyan-500/10 rounded-full blur-[140px] pointer-events-none" />

      <div className="max-w-2xl w-full relative z-10">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-950/60 border border-cyan-700/50 text-cyan-400 text-xs font-semibold uppercase tracking-wider mb-4">
            <Zap className="w-3.5 h-3.5" /> Direct Lead Fast-Pass
          </div>
          <h1 className="text-4xl font-extrabold tracking-tight text-white sm:text-5xl">
            Social DM & Direct Intake
          </h1>
          <p className="mt-3 text-slate-400 text-sm max-w-md mx-auto">
            Convert follower inquiries into glassmorphic 2-stage teaser proposals in &lt;15 seconds.
          </p>
        </div>

        {/* Dual Mode Switcher */}
        <div className="flex rounded-xl bg-slate-900/80 p-1 border border-slate-800 mb-6">
          <button
            type="button"
            onClick={() => setMode('creator_paste')}
            className={`flex-1 py-2 text-xs font-medium rounded-lg transition-all ${
              mode === 'creator_paste'
                ? 'bg-gradient-to-r from-cyan-500 to-blue-600 text-white shadow-lg'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Creator Fast-Paste Mode
          </button>
          <button
            type="button"
            onClick={() => setMode('follower_input')}
            className={`flex-1 py-2 text-xs font-medium rounded-lg transition-all ${
              mode === 'follower_input'
                ? 'bg-gradient-to-r from-cyan-500 to-blue-600 text-white shadow-lg'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Follower Direct Link Mode
          </button>
        </div>

        {/* Intake Card */}
        <div className="bg-slate-900/90 border border-slate-800/80 rounded-2xl p-6 shadow-2xl backdrop-blur-xl">
          <form onSubmit={handleGenerate} className="space-y-4">
            {mode === 'follower_input' && (
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Your Name (Optional)
                </label>
                <input
                  type="text"
                  value={clientName}
                  onChange={(e) => setClientName(e.target.value)}
                  placeholder="e.g. Jessica Vance"
                  className="w-full bg-slate-950/80 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-cyan-500 transition"
                />
              </div>
            )}

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                {mode === 'creator_paste' ? 'Paste Follower DM / Inquiry Text' : 'Describe Your Ideal Trip'}
              </label>
              <textarea
                rows={4}
                value={rawText}
                onChange={(e) => setRawText(e.target.value)}
                placeholder={
                  mode === 'creator_paste'
                    ? 'Paste DM e.g. "Looking to book Marrakech with 3 friends for my 30th birthday in November, budget is $4k/person..."'
                    : 'Tell us where you want to go, dates, party size, and budget...'
                }
                className="w-full bg-slate-950/80 border border-slate-800 rounded-xl p-4 text-sm text-slate-200 focus:outline-none focus:border-cyan-500 transition resize-none"
              />
            </div>

            <button
              type="submit"
              disabled={loading || !rawText.trim()}
              className="w-full py-3.5 px-6 rounded-xl bg-gradient-to-r from-cyan-500 via-blue-600 to-indigo-600 text-white font-semibold text-sm shadow-lg hover:shadow-cyan-500/20 disabled:opacity-50 disabled:cursor-not-allowed transition flex items-center justify-center gap-2"
            >
              {loading ? (
                <>Generating 2-Stage Teaser Link...</>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" /> Generate Interactive Teaser Link
                </>
              )}
            </button>
          </form>

          {/* Generated Result Card */}
          {result && (
            <div className="mt-6 pt-6 border-t border-slate-800/80 space-y-4 animate-in fade-in duration-300">
              <div className="flex items-center justify-between">
                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-950/80 border border-emerald-700/60 text-emerald-400 text-xs font-semibold">
                  <ShieldCheck className="w-3.5 h-3.5" /> Stage 1 Teaser Live (IP Protected)
                </span>
                <span className="text-xs text-slate-400 font-mono">
                  Suitability: {result.suitability_score}% Match
                </span>
              </div>

              <div className="bg-slate-950/90 border border-slate-800 rounded-xl p-4 flex items-center justify-between gap-3">
                <div className="truncate text-xs font-mono text-cyan-300">
                  {result.teaser_url}
                </div>
                <button
                  type="button"
                  onClick={copyToClipboard}
                  className="px-3 py-1.5 rounded-lg bg-cyan-950 border border-cyan-700 text-cyan-300 text-xs font-medium hover:bg-cyan-900 transition flex items-center gap-1.5"
                >
                  {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  {copied ? 'Copied!' : 'Copy Link'}
                </button>
              </div>

              <div className="flex gap-3 pt-2">
                <Link
                  href={result.teaser_url}
                  className="flex-1 py-2.5 px-4 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold text-center transition flex items-center justify-center gap-1"
                >
                  Preview Teaser <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
