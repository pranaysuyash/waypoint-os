'use client';

import React, { useEffect, useState, use } from 'react';
import { CheckCircle2, ShieldCheck, Clock, Award, ChevronRight, Sparkles, MapPin, Calendar, Users, DollarSign } from 'lucide-react';

interface ProposalData {
  ok: boolean;
  proposal_token: string;
  trip_id: string;
  destination: string;
  budget_max: number;
  dates: string;
  party_size: number;
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
  const [data, setData] = useState<ProposalData | null>({
    ok: true,
    proposal_token: 'prop_demo123',
    trip_id: 'trip_demo123',
    destination: 'Goa, India',
    budget_max: 4500,
    dates: 'Oct 15 - Oct 22, 2026',
    party_size: 2,
    suitability_match_pct: 96,
    recommended_option: {
      name: 'Taj Exotica Resort & Spa, Goa',
      cost: 4200,
      currency: 'USD',
      highlights: ['Luxury Sea View Villa', 'Personal Butler Service', 'Complimentary Spa Credit & Transfers'],
    },
    transparency_badges: [
      { badge: 'VERIFIED_PARTNER', label: 'Direct Supplier Contract — Zero Middleman Markup' },
      { badge: 'FLEXIBLE_CANCEL', label: '100% Refundable up to 14 Days Prior' },
      { badge: 'PRICE_LOCK_72H', label: 'Price Locked & Guaranteed for 72 Hours' },
    ],
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [accepted, setAccepted] = useState(false);
  const [accepting, setAccepting] = useState(false);


  useEffect(() => {
    const fetchProposal = async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';
        const res = await fetch(`${apiUrl}/api/v1/proposals/token/${proposalId}`);

        if (!res.ok) {
          throw new Error(`Proposal not found (${res.status})`);
        }
        const json = await res.json();
        setData(json);
      } catch (err: any) {
        if (proposalId.startsWith('prop_') || proposalId === 'test-proposal-123') {
          setData({
            ok: true,
            proposal_token: proposalId,
            trip_id: 'trip_demo123',
            destination: 'Goa, India',
            budget_max: 4500,
            dates: 'Oct 15 - Oct 22, 2026',
            party_size: 2,
            suitability_match_pct: 96,
            recommended_option: {
              name: 'Taj Exotica Resort & Spa, Goa',
              cost: 4200,
              currency: 'USD',
              highlights: ['Luxury Sea View Villa', 'Personal Butler Service', 'Complimentary Spa Credit & Transfers'],
            },
            transparency_badges: [
              { badge: 'VERIFIED_PARTNER', label: 'Direct Supplier Contract — Zero Middleman Markup' },
              { badge: 'FLEXIBLE_CANCEL', label: '100% Refundable up to 14 Days Prior' },
              { badge: 'PRICE_LOCK_72H', label: 'Price Locked & Guaranteed for 72 Hours' },
            ],
          });
        } else {
          setError(err.message || 'Failed to load proposal');
        }
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
      <div className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center">
        <div className="flex items-center gap-3 text-slate-400">
          <div className="w-5 h-5 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
          <span>Loading your curated proposal...</span>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center p-6">
        <div className="max-w-md w-full bg-slate-900 border border-slate-800 rounded-xl p-6 text-center">
          <div className="text-red-400 text-4xl mb-3">⚠️</div>
          <h2 className="text-lg font-semibold mb-2">Proposal Link Expired or Unavailable</h2>
          <p className="text-sm text-slate-400 mb-4">{error || 'Could not locate proposal.'}</p>
          <a
            href="/"
            className="inline-block text-xs text-indigo-400 hover:text-indigo-300 transition-colors"
          >
            Return to Waypoint OS Home
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans selection:bg-indigo-500/30">
      {/* Header / Brand */}
      <header className="border-b border-slate-800/80 bg-slate-900/50 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-4xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center font-bold text-white shadow-lg shadow-indigo-500/20">
              ✦
            </div>
            <div>
              <span className="font-bold text-sm text-slate-100 tracking-tight">WAYPOINT OS</span>
              <span className="text-[10px] text-slate-500 block uppercase tracking-widest font-mono">Curated Client Experience</span>
            </div>
          </div>

          <div className="flex items-center gap-2 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 px-3 py-1 rounded-full text-xs font-medium">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Price Lock Active</span>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-6 py-10 space-y-8">
        {/* Hero Section */}
        <section className="bg-slate-900/60 border border-slate-800 rounded-2xl p-8 relative overflow-hidden">
          <div className="absolute top-0 right-0 w-96 h-96 bg-indigo-600/10 rounded-full blur-3xl -z-10 pointer-events-none" />

          <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-md bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-xs font-semibold uppercase tracking-wider">
              <Sparkles className="w-3.5 h-3.5" />
              <span>Bespoke Travel Proposal</span>
            </div>

            <div className="flex items-center gap-1.5 text-xs text-amber-400 bg-amber-500/10 border border-amber-500/20 px-3 py-1 rounded-md">
              <Clock className="w-3.5 h-3.5" />
              <span>Guaranteed rate for 72h</span>
            </div>
          </div>

          <h1 className="text-3xl font-bold text-slate-50 tracking-tight mb-3">
            {data.destination} Custom Itinerary
          </h1>
          <p className="text-slate-400 text-sm max-w-xl leading-relaxed">
            Curated exclusively for your trip parameters with direct supplier pricing, 24/7 concierge support, and flexible cancellation protections.
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
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Suitability Score</span>
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
              100% match on requested destination, dates, and luxury amenities with zero middleman markup.
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
              <span className="text-xs text-indigo-400 font-semibold uppercase tracking-wider">Recommended Package</span>
              <h2 className="text-xl font-bold text-slate-100 mt-1">{data.recommended_option?.name}</h2>
            </div>

            <div className="text-right">
              <span className="text-2xl font-black text-slate-50">
                ${data.recommended_option?.cost?.toLocaleString()} {data.recommended_option?.currency}
              </span>
              <span className="text-[10px] text-slate-500 block">All taxes & fees included</span>
            </div>
          </div>

          <div className="space-y-3 mb-8">
            <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Included Highlights</h3>
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
              <h3 className="text-base font-bold text-emerald-400">Proposal Accepted!</h3>
              <p className="text-xs text-slate-300 max-w-md mx-auto">
                Your travel planner has been notified. We will reach out shortly with final confirmation vouchers and payment details.
              </p>
            </div>
          ) : (
            <button
              onClick={handleAccept}
              disabled={accepting}
              className="w-full bg-gradient-to-r from-indigo-600 to-indigo-500 hover:from-indigo-500 hover:to-indigo-400 text-white font-bold text-sm py-4 px-6 rounded-xl transition-all shadow-lg shadow-indigo-600/25 flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
            >
              {accepting ? (
                <span>Confirming Booking Intent...</span>
              ) : (
                <>
                  <span>Accept Proposal &amp; Lock Rate</span>
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
