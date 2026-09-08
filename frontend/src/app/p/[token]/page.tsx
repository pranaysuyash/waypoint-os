'use client';

import React, { useEffect, useState } from 'react';
import { Check, Sparkles, ShieldCheck, ShieldAlert, MapPin, Calendar, ArrowRight, UserCheck } from 'lucide-react';

interface ProposalOption {
  id: string;
  category: string;
  name: string;
  description: string;
  price_delta_usd: number;
  selected: boolean;
  is_default: boolean;
}

interface ProposalDay {
  day_number: number;
  title: string;
  location: string;
  description: string;
  highlights: string[];
  options: ProposalOption[];
}

interface ProposalData {
  token: string;
  title: string;
  destination: string;
  duration_days: number;
  traveler_name: string;
  base_price_usd: number;
  selected_total_price_usd: number;
  currency: string;
  status: string;
  accepted_at?: string;
  accepted_by?: string;
  days: ProposalDay[];
  available_options: ProposalOption[];
  reality_tier?: string;
}

// Part-H P1 (2026-09-07): a 200 response is not automatically a proposal.
// Casts hide malformed payloads; an incomplete payload must abstain instead
// of rendering a fabricated $0 package.
function asProposal(data: unknown): ProposalData | null {
  if (!data || typeof data !== 'object') return null;
  const d = data as Record<string, unknown>;
  if (typeof d.title !== 'string' || !d.title.trim()) return null;
  if (typeof d.destination !== 'string' || !d.destination.trim()) return null;
  if (typeof d.selected_total_price_usd !== 'number' || !Number.isFinite(d.selected_total_price_usd) || d.selected_total_price_usd <= 0) return null;
  if (typeof d.duration_days !== 'number' || !Number.isFinite(d.duration_days) || d.duration_days <= 0) return null;
  return data as ProposalData;
}

// Next 14 app router: params is a plain object (Promise params + React `use()`
// are Next 15/React 19 patterns — they crash this React 18 runtime, AT-20).
export default function PublicProposalPage({ params }: { params: { token: string } }) {
  const token = params.token;

  const [proposal, setProposal] = useState<ProposalData | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [selectedOptionIds, setSelectedOptionIds] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [signerName, setSignerName] = useState('');
  const [signerEmail, setSignerEmail] = useState('');
  const [eSignConsent, setESignConsent] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);

  useEffect(() => {
    async function loadProposal() {
      try {
        const res = await fetch(`/api/public/proposals/${token}`);
        if (res.ok) {
          const parsed = asProposal(await res.json());
          if (!parsed) {
            setLoadError('This proposal exists but its details are incomplete. Please ask your travel advisor for assistance.');
            return;
          }
          setProposal(parsed);
          setSelectedOptionIds(
            parsed.available_options.filter((o) => o.selected).map((o) => o.id),
          );
          if (parsed.status === 'accepted') {
            setIsSuccess(true);
          }
          return;
        }
        // AT-20: an invalid/expired/revoked link must abstain — never render
        // placeholder itinerary content the backend did not send.
        if (res.status === 410) {
          setLoadError('This proposal link has expired or was revoked.');
        } else if (res.status === 404) {
          setLoadError('We could not find a proposal for this link.');
        } else {
          setLoadError('This proposal link is not valid.');
        }
      } catch {
        setLoadError('This proposal could not be loaded right now.');
      } finally {
        setLoading(false);
      }
    }
    void loadProposal();
  }, [token]);

  const toggleOption = async (optionId: string) => {
    const nextSelected = selectedOptionIds.includes(optionId)
      ? selectedOptionIds.filter((id) => id !== optionId)
      : [...selectedOptionIds, optionId];

    setSelectedOptionIds(nextSelected);

    try {
      const res = await fetch(`/api/public/proposals/${token}/calculate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ selected_option_ids: nextSelected }),
      });
      if (res.ok) {
        // Part-J #8: follow-up responses get the same runtime validation as
        // the initial GET — a malformed recalculation must not corrupt state.
        const parsed = asProposal(await res.json());
        if (parsed) {
          setProposal(parsed);
        }
      }
    } catch {
      // Ignore network errors on local recalculation
    }
  };

  const handleAccept = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!signerName || !signerEmail || !eSignConsent) return;

    setIsSubmitting(true);
    try {
      const res = await fetch(`/api/public/proposals/${token}/accept`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          signer_name: signerName,
          signer_email: signerEmail,
          selected_option_ids: selectedOptionIds,
          e_signature_consent: eSignConsent,
        }),
      });

      if (res.ok) {
        // Part-J #8: acceptance success is only claimed on a valid accepted
        // proposal payload.
        const parsed = asProposal(await res.json());
        if (parsed && parsed.status === 'accepted') {
          setProposal(parsed);
          setIsSuccess(true);
        }
      }
    } catch {
      // Handle acceptance failure
    } finally {
      setIsSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#080a0c] text-white flex items-center justify-center p-6">
        <div className="flex items-center gap-3 text-sm text-[#8b949e]">
          <div className="size-4 border-2 border-[#58a6ff] border-t-transparent rounded-full animate-spin" />
          Loading your bespoke itinerary…
        </div>
      </div>
    );
  }

  // AT-20: no proposal from the backend → honest abstention screen, never
  // placeholder itinerary copy.
  if (!proposal) {
    return (
      <div className="min-h-screen bg-[#080a0c] text-[#e6edf3] font-sans antialiased flex items-center justify-center p-6">
        <div className="max-w-md w-full rounded-2xl border border-[#30363d] bg-[#161b22] p-8 text-center space-y-4">
          <div className="size-12 rounded-full bg-[#f85149]/15 text-[#f85149] flex items-center justify-center mx-auto">
            <ShieldAlert className="size-6" />
          </div>
          <h1 className="text-xl font-bold text-white">Proposal unavailable</h1>
          <p className="text-sm text-[#8b949e] leading-relaxed">
            {loadError ?? 'This proposal link is not valid.'}
          </p>
          <p className="text-xs text-[#8b949e] leading-relaxed">
            Proposal links are private and expire after a while. Please ask
            your travel advisor for a fresh link.
          </p>
        </div>
      </div>
    );
  }

  const currentTotal = proposal.selected_total_price_usd;

  return (
    <div className="min-h-screen bg-[#080a0c] text-[#e6edf3] font-sans antialiased pb-24">
      {/* Hero Banner */}
      <header className="border-b border-[#21262d] bg-[#0d1117]/80 backdrop-blur-md sticky top-0 z-30 px-6 py-4">
        <div className="max-w-5xl mx-auto flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <span className="inline-flex items-center justify-center size-8 rounded-lg bg-[#58a6ff]/10 text-[#58a6ff] font-bold text-sm">
              W
            </span>
            <div>
              <p className="text-xs text-[#8b949e] font-medium tracking-wide uppercase">Waypoint Curated Proposal</p>
              <h1 className="text-sm font-semibold text-white truncate max-w-sm sm:max-w-md">
                {proposal.title}
              </h1>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="text-right">
              <p className="text-xs text-[#8b949e]">Total Package</p>
              <p className="text-lg font-bold text-[#3fb950] tracking-tight">
                ${currentTotal.toLocaleString()} {proposal.currency}
              </p>
            </div>
            {!isSuccess && (
              <a
                href="#accept-section"
                className="hidden sm:inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-[#238636] hover:bg-[#2ea043] text-white text-xs font-semibold shadow-md transition-colors"
              >
                Accept Proposal <ArrowRight className="size-3.5" />
              </a>
            )}
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-8 space-y-10">
        {/* Trip Overview Card */}
        <section className="rounded-2xl border border-[#30363d] bg-gradient-to-b from-[#161b22] to-[#0d1117] p-8 shadow-xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-[#58a6ff]/10 text-[#58a6ff] border border-[#58a6ff]/20 mb-4">
            <Sparkles className="size-3.5" /> Curated for {proposal.traveler_name}
            {proposal.reality_tier === 'demo' && (
              <span className="ml-1 px-2 py-0.5 rounded-md bg-[#d29922]/15 text-[#d29922] border border-[#d29922]/40 text-[10px] font-bold uppercase tracking-wider">
                Demo content
              </span>
            )}
          </div>
          <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-white mb-4">
            {proposal.title}
          </h2>
          <div className="flex flex-wrap items-center gap-6 text-sm text-[#8b949e]">
            <span className="flex items-center gap-1.5">
              <MapPin className="size-4 text-[#58a6ff]" /> {proposal.destination}
            </span>
            <span className="flex items-center gap-1.5">
              <Calendar className="size-4 text-[#58a6ff]" /> {proposal.duration_days} Days /{' '}
              {Math.max(proposal.duration_days - 1, 0)} Nights
            </span>
            <span className="flex items-center gap-1.5">
              <ShieldCheck className="size-4 text-[#3fb950]" /> E-signature secured
            </span>
          </div>
        </section>

        {/* Day by Day Itinerary */}
        <section className="space-y-6">
          <h3 className="text-lg font-bold text-white tracking-tight flex items-center gap-2">
            Day-by-Day Journey Flow
          </h3>
          <div className="space-y-4">
            {(proposal?.days ?? []).map((day) => (
              <div
                key={day.day_number}
                className="rounded-xl border border-[#30363d] bg-[#161b22] p-6 hover:border-[#8b949e]/40 transition-colors"
              >
                <div className="flex items-start justify-between gap-4 mb-2">
                  <div className="flex items-center gap-3">
                    <span className="inline-flex items-center justify-center size-7 rounded-full bg-[#21262d] text-[#58a6ff] font-bold text-xs">
                      {day.day_number}
                    </span>
                    <h4 className="text-base font-semibold text-white">{day.title}</h4>
                  </div>
                  <span className="text-xs text-[#8b949e] font-medium">{day.location}</span>
                </div>
                <p className="text-sm text-[#8b949e] leading-relaxed mb-4">{day.description}</p>
                <div className="flex flex-wrap gap-2">
                  {day.highlights.map((h, i) => (
                    <span
                      key={i}
                      className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-medium bg-[#0d1117] text-[#c9d1d9] border border-[#21262d]"
                    >
                      <Check className="size-3 text-[#3fb950]" /> {h}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Co-Creation Option Customizer */}
        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-bold text-white tracking-tight">
              Customize Your Experience
            </h3>
            <p className="text-xs text-[#8b949e]">Select options to update your price in real-time</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {(proposal?.available_options ?? []).map((opt) => {
              const isSelected = selectedOptionIds.includes(opt.id);
              return (
                <div
                  key={opt.id}
                  onClick={() => !isSuccess && toggleOption(opt.id)}
                  className={`rounded-xl border p-5 cursor-pointer transition-all flex flex-col justify-between ${
                    isSelected
                      ? 'border-[#58a6ff] bg-[#58a6ff]/5 shadow-lg shadow-[#58a6ff]/5'
                      : 'border-[#30363d] bg-[#161b22] hover:border-[#8b949e]/40'
                  } ${isSuccess ? 'pointer-events-none' : ''}`}
                >
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-[11px] font-bold uppercase tracking-wider text-[#8b949e]">
                        {opt.category}
                      </span>
                      <div
                        className={`size-5 rounded-md flex items-center justify-center border ${
                          isSelected
                            ? 'bg-[#58a6ff] border-[#58a6ff] text-[#080a0c]'
                            : 'border-[#484f58] bg-[#0d1117]'
                        }`}
                      >
                        {isSelected && <Check className="size-3.5 stroke-[3]" />}
                      </div>
                    </div>
                    <h4 className="text-sm font-semibold text-white">{opt.name}</h4>
                    <p className="text-xs text-[#8b949e] leading-relaxed">{opt.description}</p>
                  </div>

                  <div className="mt-4 pt-3 border-t border-[#21262d] flex items-center justify-between text-xs">
                    <span className="text-[#8b949e]">Add-on price</span>
                    <span className="font-bold text-[#3fb950]">+${opt.price_delta_usd.toFixed(0)}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </section>

        {/* Accept & E-Sign Section */}
        <section
          id="accept-section"
          className="rounded-2xl border border-[#30363d] bg-[#161b22] p-8 space-y-6"
        >
          {isSuccess ? (
            <div className="text-center py-6 space-y-3">
              <div className="size-12 rounded-full bg-[#238636]/20 text-[#3fb950] flex items-center justify-center mx-auto">
                <UserCheck className="size-6" />
              </div>
              <h3 className="text-xl font-bold text-white">Proposal Successfully Accepted</h3>
              <p className="text-sm text-[#8b949e] max-w-md mx-auto">
                Thank you! Your acceptance has been recorded. Your travel
                advisor will confirm the details and next steps with you
                directly.
              </p>
            </div>
          ) : (
            <>
              <div className="space-y-1">
                <h3 className="text-lg font-bold text-white">Accept Proposal</h3>
                <p className="text-xs text-[#8b949e]">
                  Please provide your name and email to electronically sign and
                  record your acceptance of this proposal.
                </p>
              </div>

              <form onSubmit={handleAccept} className="space-y-4 max-w-xl">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-[#8b949e]">Full Legal Name</label>
                    <input
                      type="text"
                      required
                      value={signerName}
                      onChange={(e) => setSignerName(e.target.value)}
                      placeholder="e.g. Priya Sharma"
                      className="w-full px-3.5 py-2.5 rounded-lg border border-[#30363d] bg-[#0d1117] text-white text-sm focus:outline-none focus:border-[#58a6ff]"
                    />
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-[#8b949e]">Email Address</label>
                    <input
                      type="email"
                      required
                      value={signerEmail}
                      onChange={(e) => setSignerEmail(e.target.value)}
                      placeholder="priya@example.com"
                      className="w-full px-3.5 py-2.5 rounded-lg border border-[#30363d] bg-[#0d1117] text-white text-sm focus:outline-none focus:border-[#58a6ff]"
                    />
                  </div>
                </div>

                <div className="flex items-start gap-3 pt-2">
                  <input
                    type="checkbox"
                    id="consent-check"
                    required
                    checked={eSignConsent}
                    onChange={(e) => setESignConsent(e.target.checked)}
                    className="mt-1 size-4 rounded border-[#30363d] bg-[#0d1117] text-[#58a6ff]"
                  />
                  <label htmlFor="consent-check" className="text-xs text-[#8b949e] leading-relaxed cursor-pointer">
                    I agree to the terms of this itinerary and authorize Waypoint OS to
                    record my acceptance of this proposal at the selected total of{' '}
                    <strong className="text-white">${currentTotal.toLocaleString()} USD</strong>. A
                    travel advisor will then secure the reservations.
                  </label>
                </div>

                <button
                  type="submit"
                  disabled={isSubmitting || !signerName || !signerEmail || !eSignConsent}
                  className="w-full sm:w-auto px-6 py-3 rounded-lg bg-[#238636] hover:bg-[#2ea043] disabled:opacity-50 text-white font-semibold text-sm transition-colors flex items-center justify-center gap-2 shadow-lg"
                >
                  {isSubmitting ? 'Recording acceptance…' : 'Confirm & E-Sign Proposal'}
                </button>
              </form>
            </>
          )}
        </section>
      </main>
    </div>
  );
}
