'use client';

import React, { useEffect, useState, use } from 'react';
import Link from 'next/link';
import { CheckCircle2, ShieldCheck, Clock, Award, ChevronRight, Sparkles, MapPin, Calendar, Users, DollarSign, Loader2, AlertTriangle } from 'lucide-react';

interface ProposalData {
  ok: boolean;
  proposal_token: string;
  trip_id: string;
  destination: string;
  budget_max: number;
  dates: string;
  party_size: number;
  proposal_token_expires_at?: string;
  suitability_match_pct: number;
  recommended_option: {
    name: string;
    cost: number;
    currency: string;
    highlights: string[];
  };
  transparency_badges: Array<{ badge: string; label: string }>;
}

export default function InteractiveProposalPage({
  params,
}: {
  params: Promise<{ proposalId: string }>;
}) {
  const { proposalId } = use(params);
  const [data, setData] = useState<ProposalData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [accepted, setAccepted] = useState(false);
  const [accepting, setAccepting] = useState(false);

  useEffect(() => {
    const fetchProposal = async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';
        const res = await fetch(`${apiUrl}/api/v1/proposals/token/${proposalId}`);

        if (!res.ok) {
          throw new Error(`Proposal not found or expired (${res.status})`);
        }
        const json = await res.json();
        if (!json.ok) {
          throw new Error(json.detail || 'Proposal link invalid');
        }
        setData(json);
      } catch (err: any) {
        setError(err.message || 'Failed to load proposal');
        setData(null);
      } finally {
        setLoading(false);
      }
    };

    fetchProposal();
  }, [proposalId]);

  const handleAccept = async () => {
    setAccepting(true);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const res = await fetch(`${apiUrl}/api/v1/proposals/token/${proposalId}/accept`, {
        method: 'POST',
      });
      if (!res.ok) throw new Error('Acceptance failed');
      setAccepted(true);
    } catch (err: any) {
      alert(`Acceptance failed: ${err.message}`);
    } finally {
      setAccepting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center p-6">
        <div className="flex items-center gap-3 text-sm text-slate-400">
          <Loader2 className="w-5 h-5 animate-spin text-indigo-400" />
          <span>Verifying proposal link...</span>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center p-6">
        <div className="max-w-md w-full bg-slate-900 border border-slate-800 rounded-2xl p-8 text-center space-y-4">
          <div className="w-12 h-12 bg-rose-500/10 border border-rose-500/20 rounded-full flex items-center justify-center mx-auto text-rose-400">
            <AlertTriangle className="w-6 h-6" />
          </div>
          <h1 className="text-xl font-bold text-slate-100">Proposal Unavailable</h1>
          <p className="text-xs text-slate-400 leading-relaxed">
            {error || 'This proposal link is invalid, expired, or has been revoked by the agency.'}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans pb-16">
      {/* Header */}
      <header className="border-b border-slate-800/80 bg-slate-900/50 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-4xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-indigo-400" />
            <span className="font-bold text-sm tracking-tight text-slate-100">Waypoint OS Proposal</span>
          </div>

          <div className="flex items-center gap-2 text-xs text-slate-400 bg-slate-800/60 border border-slate-700/50 px-3 py-1.5 rounded-full">
            <Clock className="w-3.5 h-3.5 text-indigo-400" />
            <span>Link Expires: {data.proposal_token_expires_at ? new Date(data.proposal_token_expires_at).toLocaleDateString() : 'Active Link'}</span>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="max-w-4xl mx-auto px-6 pt-10 space-y-8">
        {/* Banner */}
        <section className="relative overflow-hidden bg-gradient-to-br from-indigo-950/60 via-slate-900 to-slate-900 border border-indigo-500/20 rounded-2xl p-8 shadow-2xl">
          <div className="absolute top-0 right-0 w-96 h-96 bg-indigo-500/5 rounded-full blur-3xl -mr-20 -mt-20 pointer-events-none" />

          <div className="flex items-center gap-2 text-xs font-semibold text-indigo-400 uppercase tracking-widest mb-3">
            <CheckCircle2 className="w-4 h-4" />
            <span>Verified Travel Proposal</span>
          </div>

          <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-50 tracking-tight mb-3">
            Your Custom Itinerary to {data.destination}
          </h1>

          <p className="text-slate-400 text-sm max-w-xl leading-relaxed">
            Curated specifically for your trip parameters based on verified agency availability and terms.
          </p>

          <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 mt-8 pt-6 border-t border-slate-800/80 text-xs">
            <div className="flex items-center gap-2.5 text-slate-300">
              <MapPin className="w-4 h-4 text-indigo-400" />
              <div>
                <span className="text-slate-500 block text-[10px]">Destination</span>
                <span className="font-semibold">{data.destination}</span>
              </div>
            </div>

            <div className="flex items-center gap-2.5 text-slate-300">
              <Calendar className="w-4 h-4 text-indigo-400" />
              <div>
                <span className="text-slate-500 block text-[10px]">Dates</span>
                <span className="font-semibold">{data.dates}</span>
              </div>
            </div>

            <div className="flex items-center gap-2.5 text-slate-300">
              <Users className="w-4 h-4 text-indigo-400" />
              <div>
                <span className="text-slate-500 block text-[10px]">Guests</span>
                <span className="font-semibold">{data.party_size} Travelers</span>
              </div>
            </div>
          </div>
        </section>

        {/* Suitability & Trust Card */}
        <section className="grid sm:grid-cols-2 gap-6">
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6">
            <div className="flex items-center justify-between mb-4">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Suitability Match</span>
              <Award className="w-4 h-4 text-indigo-400" />
            </div>

            <div className="flex items-baseline gap-2 mb-3">
              <span className="text-4xl font-extrabold text-indigo-400">{data.suitability_match_pct}%</span>
              <span className="text-xs text-slate-400">Match to your request</span>
            </div>

            <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden mb-4">
              <div
                className="bg-gradient-to-r from-indigo-500 to-emerald-400 h-full rounded-full transition-all duration-500"
                style={{ width: `${data.suitability_match_pct}%` }}
              />
            </div>

            <p className="text-xs text-slate-400 leading-normal">
              Evaluated against requested destination, dates, and budget parameters.
            </p>
          </div>

          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 space-y-3">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-2">Transparency Badges</span>
            {data.transparency_badges?.map((badge, idx) => (
              <div key={idx} className="flex items-start gap-2.5 text-xs text-slate-300">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                <span>{badge.label}</span>
              </div>
            ))}
          </div>
        </section>

        {/* Recommended Option */}
        <section className="bg-slate-900/60 border border-slate-800 rounded-2xl p-8">
          <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
            <div>
              <span className="text-xs text-indigo-400 font-semibold uppercase tracking-wider">Proposed Package</span>
              <h2 className="text-xl font-bold text-slate-100 mt-1">{data.recommended_option?.name}</h2>
            </div>

            <div className="text-right">
              <span className="text-2xl font-black text-slate-50">
                ${data.recommended_option?.cost?.toLocaleString()} {data.recommended_option?.currency}
              </span>
              <span className="text-[10px] text-slate-500 block">Estimated quote based on current inventory</span>
            </div>
          </div>

          <div className="space-y-3 mb-8">
            <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Package Highlights</h3>
            <div className="grid sm:grid-cols-2 gap-3">
              {data.recommended_option?.highlights?.map((item, idx) => (
                <div key={idx} className="flex items-center gap-2 bg-slate-800/50 border border-slate-800 rounded-lg p-3 text-xs text-slate-200">
                  <Sparkles className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
                  <span>{item}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Action Button */}
          {accepted ? (
            <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-xl p-6 text-center space-y-2">
              <CheckCircle2 className="w-8 h-8 text-emerald-400 mx-auto" />
              <h3 className="text-base font-bold text-emerald-400">Proposal Acceptance Recorded</h3>
              <p className="text-xs text-slate-300 max-w-md mx-auto">
                Your travel agency has been notified of your acceptance intent. An agent will contact you to review options and confirm payment details.
              </p>
            </div>
          ) : (
            <button
              onClick={handleAccept}
              disabled={accepting}
              className="w-full bg-gradient-to-r from-indigo-600 to-indigo-500 hover:from-indigo-500 hover:to-indigo-400 text-white font-bold text-sm py-4 px-6 rounded-xl transition-all shadow-lg shadow-indigo-600/25 flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
            >
              {accepting ? (
                <span>Recording Intent...</span>
              ) : (
                <>
                  <span>Accept Proposal &amp; Express Booking Intent</span>
                  <ChevronRight className="w-4 h-4" />
                </>
              )}
            </button>
          )}
        </section>
      </main>
    </div>
  );
}
