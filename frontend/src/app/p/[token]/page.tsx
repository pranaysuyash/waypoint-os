'use client';

import React, { useCallback, useEffect, useState } from 'react';
import { Check, CheckCircle, Sparkles, ShieldCheck, ShieldAlert, AlertTriangle, MapPin, Calendar, ArrowRight, UserCheck } from 'lucide-react';
import { CURRENCY_CONFIG, type SupportedCurrency } from '@/lib/currency';

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
  stated_requirements?: string[];
  why_this_fits?: string | null;
  open_questions?: Array<{ field_name: string; question: string; priority: string }>;
  booking_changes?: Array<{
    change_id: string;
    change_kind: string;
    supplier: string;
    supplier_ref?: string | null;
    reported_at?: string;
    notes?: string;
    affected_travelers?: string[];
    source_label?: string;
  }>;
  // AT-20 renewed consent: the backend sends these when a new revision needs
  // the traveler to re-accept (accepted_agreement = the superseded terms).
  revision_id?: string | null;
  requires_reacceptance?: boolean;
  accepted_agreement?: {
    revision_id?: string;
    selected_total_price?: number;
    currency?: string;
    accepted_at?: string;
  } | null;
  // Native-currency wire alias (backend PublicProposalView); _usd is legacy.
  selected_total_price?: number;
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
  const [isCalculating, setIsCalculating] = useState(false);
  const [pricingError, setPricingError] = useState<string | null>(null);
  // AT-20: recoverable acceptance failure (e.g. revision conflict 409) and
  // renewed-consent state surface honestly — never silent, never fake success.
  const [acceptanceError, setAcceptanceError] = useState<string | null>(null);
  const [isSuccess, setIsSuccess] = useState(false);
  const [requiresRevisionReview, setRequiresRevisionReview] = useState(false);
  const [isReviewingRevision, setIsReviewingRevision] = useState(false);
  const signingBlocked = isCalculating || isSubmitting || requiresRevisionReview || isReviewingRevision;

  const loadProposal = useCallback(async (reviewing = false) => {
      const showLoadError = reviewing ? setAcceptanceError : setLoadError;
      try {
        const res = await fetch(`/api/public/proposals/${token}`);
        if (res.ok) {
          const parsed = asProposal(await res.json());
          if (!parsed) {
            showLoadError('This proposal exists but its details are incomplete. Please ask your travel advisor for assistance.');
            return;
          }
          setProposal(parsed);
          if (reviewing) {
            setAcceptanceError(null);
            setRequiresRevisionReview(false);
          }
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
          showLoadError('This proposal link has expired or was revoked.');
        } else if (res.status === 404) {
          showLoadError('We could not find a proposal for this link.');
        } else if (res.status >= 500) {
          showLoadError('This proposal could not be loaded right now.');
        } else {
          showLoadError('This proposal link is not valid.');
        }
      } catch {
        showLoadError('This proposal could not be loaded right now.');
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    void loadProposal();
  }, [token, loadProposal]);

  const toggleOption = async (optionId: string) => {
    if (signingBlocked || isSuccess) return;
    const nextSelected = selectedOptionIds.includes(optionId)
      ? selectedOptionIds.filter((id) => id !== optionId)
      : [...selectedOptionIds, optionId];

    setSelectedOptionIds(nextSelected);
    setESignConsent(false);
    setPricingError(null);
    setIsCalculating(true);

    try {
      const res = await fetch(`/api/public/proposals/${token}/calculate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ selected_option_ids: nextSelected }),
      });
      const parsed = res.ok ? asProposal(await res.json()) : null;
      if (!parsed) throw new Error('Price could not be confirmed.');
      setProposal(parsed);
    } catch {
      setSelectedOptionIds(selectedOptionIds);
      setPricingError('We could not update the price. Your previous options are still selected. Try again.');
    } finally {
      setIsCalculating(false);
    }
  };

  const handleAccept = async (e: React.FormEvent) => {
    e.preventDefault();
    if (signingBlocked || !signerName || !signerEmail || !eSignConsent) return;

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
          // AT-20: bind the acceptance to the revision the traveler actually
          // viewed — the backend rejects a stale revision instead of
          // recording consent for terms that changed mid-review.
          revision_id: proposal?.revision_id ?? null,
        }),
      });

      if (res.ok) {
        // Part-J #8: acceptance success is only claimed on a valid accepted
        // proposal payload.
        const parsed = asProposal(await res.json());
        if (parsed && parsed.status === 'accepted') {
          setProposal(parsed);
          setIsSuccess(true);
          setAcceptanceError(null);
        }
      } else {
        // AT-20: a revision conflict (409) or other rejection is a
        // recoverable, traveler-readable error — not a silent failure.
        let detail = 'The proposal changed while you were reviewing it. Refresh the page to review the updated terms.';
        try {
          const errBody = await res.json();
          if (errBody?.detail) detail = String(errBody.detail);
        } catch {
          // keep the default message
        }
        if (res.status === 409) {
          setESignConsent(false);
          setRequiresRevisionReview(true);
        }
        setAcceptanceError(detail);
      }
    } catch {
      setAcceptanceError('Something went wrong while recording your acceptance. Please try again.');
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

  const currency = proposal.currency || 'USD';
  const locale = CURRENCY_CONFIG[currency as SupportedCurrency]?.locale ?? 'en-US';
  const currentTotal = proposal.selected_total_price;
  const total = typeof currentTotal === 'number' && Number.isFinite(currentTotal) && currentTotal > 0
    ? currentTotal
    : proposal.selected_total_price_usd;
  const formatPrice = (amount: number) => {
    if (!/^[A-Za-z]{3}$/.test(currency)) return `${amount.toLocaleString(locale)} ${currency}`;
    return amount.toLocaleString(locale, {
      style: 'currency', currency, minimumFractionDigits: 0, maximumFractionDigits: 2,
    });
  };
  const selectedTotalLabel = formatPrice(total);

  return (
    <div className="min-h-screen bg-[#080a0c] text-[#e6edf3] font-sans antialiased pb-24">
      {/* Hero Banner */}
      <header className="border-b border-[#21262d] bg-[#0d1117]/80 backdrop-blur-md sticky top-0 z-30 px-6 py-4">
        <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-x-4 gap-y-2">
          <div className="flex min-w-0 grow basis-60 items-center gap-3">
            <span className="inline-flex items-center justify-center size-8 shrink-0 rounded-lg bg-[#58a6ff]/10 text-[#58a6ff] font-bold text-sm">
              W
            </span>
            <div className="min-w-0">
              <p className="text-xs text-[#8b949e] font-medium tracking-wide uppercase">Waypoint Curated Proposal</p>
              <h1 className="text-sm font-semibold text-white [overflow-wrap:anywhere]">
                {proposal.title}
              </h1>
            </div>
          </div>

          <div className="ml-auto flex max-w-full flex-wrap items-center justify-end gap-3">
            <div className="text-right">
              <p className="text-xs text-[#8b949e]">Total Package</p>
              <p className="text-lg font-bold text-[#3fb950] tracking-tight">
                {selectedTotalLabel}
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

        {/* Stated requirements (T8 trust render): what the plan accounts for,
            de-attributed — the backend never sends traveler names here. */}
        {(proposal.stated_requirements?.length ?? 0) > 0 && (
          <section data-testid="proposal-stated-requirements" className="rounded-xl border border-[#30363d] bg-[#161b22] p-6">
            <h3 className="text-lg font-bold text-white tracking-tight mb-2 flex items-center gap-2">
              <ShieldCheck className="size-5 text-[#3fb950]" /> Planning Around Your Requirements
            </h3>
            <ul className="space-y-1.5">
              {proposal.stated_requirements!.map((req) => (
                <li key={req} className="text-sm text-[#8b949e] flex items-start gap-2">
                  <CheckCircle className="size-4 text-[#3fb950] shrink-0 mt-0.5" /> {req}
                </li>
              ))}
            </ul>
            <p className="text-xs text-[#484f58] mt-3">
              Held on file for this trip. Your travel advisor confirms each one is covered before any booking is made.
            </p>
          </section>
        )}

        {/* Why this option (gap-4 trust render): deterministic rationale built
            only from this trip's persisted decision facts — no generated prose. */}
        {proposal.why_this_fits && (
          <section data-testid="proposal-why-this-fits" className="rounded-xl border border-[#58a6ff]/30 bg-[#58a6ff]/5 p-6">
            <h3 className="text-lg font-bold text-white tracking-tight mb-2 flex items-center gap-2">
              <CheckCircle className="size-5 text-[#58a6ff]" /> Why This Plan Fits
            </h3>
            <p className="text-sm text-[#c9d1d9] leading-relaxed">{proposal.why_this_fits}</p>
          </section>
        )}

        {/* Open questions with field names (gap-4 repair banner): the traveler
            sees exactly what is still open; answers arrive via the advisor's
            ask link — capability tokens are never mixed on this page. */}
        {(proposal.open_questions?.length ?? 0) > 0 && (
          <section data-testid="proposal-open-questions" className="rounded-xl border border-[#d29922]/30 bg-[#d29922]/10 p-6">
            <h3 className="text-lg font-bold text-white tracking-tight mb-2 flex items-center gap-2">
              <AlertTriangle className="size-5 text-[#d29922]" /> Still Open Before Booking
            </h3>
            <ul className="space-y-1.5">
              {proposal.open_questions!.map((q) => (
                <li key={q.field_name} className="text-sm text-[#c9d1d9] flex items-start gap-2">
                  <span className="text-[#d29922] shrink-0 mt-0.5">•</span>
                  <span>
                    {q.question}
                    <span className="ml-1 text-[#8b949e]">({q.field_name.replace(/_/g, ' ')}{q.priority === 'high' ? ' · high priority' : ''})</span>
                  </span>
                </li>
              ))}
            </ul>
            <p className="text-xs text-[#484f58] mt-3">
              Your travel advisor will send you a secure answer link for these — answering them finishes your plan.
            </p>
          </section>
        )}

        {/* Booking changes (FND-0410): supplier-side changes to confirmed
            bookings with honest provenance — advisor-reported until a
            provider feed supersedes. Never renders as provider-confirmed. */}
        {(proposal.booking_changes?.length ?? 0) > 0 && (
          <section data-testid="proposal-booking-changes" className="rounded-xl border border-[#f85149]/30 bg-[#f85149]/5 p-6">
            <h3 className="text-lg font-bold text-white tracking-tight mb-2 flex items-center gap-2">
              <AlertTriangle className="size-5 text-[#f85149]" /> Changes To Your Bookings
            </h3>
            <ul className="space-y-2">
              {proposal.booking_changes!.map((change) => (
                <li key={change.change_id} className="rounded border border-[#30363d] bg-[#0d1117] px-3 py-2.5">
                  <p className="text-sm font-semibold text-[#e6edf3]">
                    {change.supplier} · {change.change_kind.replace(/_/g, ' ')}
                    {change.supplier_ref ? ` · ${change.supplier_ref}` : ''}
                  </p>
                  {change.notes && <p className="text-xs text-[#c9d1d9] mt-1">{change.notes}</p>}
                  <p className="text-[10px] text-[#d29922] mt-1">
                    {change.source_label ?? 'Reported by your travel advisor'}
                    {change.reported_at ? ` · ${new Date(change.reported_at).toLocaleString()}` : ''}
                  </p>
                </li>
              ))}
            </ul>
            <p className="text-xs text-[#484f58] mt-3">
              Your travel advisor is acting on these and will contact you with next steps.
            </p>
          </section>
        )}

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
          <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
            <h3 className="text-lg font-bold text-white tracking-tight">
              Customize Your Experience
            </h3>
            <p className="text-xs text-[#8b949e]">Select options to update your price in real-time</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {(proposal?.available_options ?? []).map((opt) => {
              const isSelected = selectedOptionIds.includes(opt.id);
              return (
                <button
                  key={opt.id}
                  type="button"
                  aria-pressed={isSelected}
                  disabled={isSuccess || signingBlocked}
                  onClick={() => void toggleOption(opt.id)}
                  className={`flex min-w-0 flex-col justify-between rounded-xl border p-5 text-left transition-colors [overflow-wrap:anywhere] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#58a6ff] ${
                    isSelected
                      ? 'border-[#58a6ff] bg-[#58a6ff]/5 shadow-lg shadow-[#58a6ff]/5'
                      : 'border-[#30363d] bg-[#161b22] hover:border-[#8b949e]/40'
                  }`}
                >
                  <span className="block space-y-2">
                    <span className="flex flex-wrap items-center justify-between gap-2">
                      <span className="text-[11px] font-bold uppercase tracking-wider text-[#8b949e]">
                        {opt.category}
                      </span>
                      <span
                        aria-hidden="true"
                        className={`size-5 shrink-0 rounded-md flex items-center justify-center border ${
                          isSelected
                            ? 'bg-[#58a6ff] border-[#58a6ff] text-[#080a0c]'
                            : 'border-[#484f58] bg-[#0d1117]'
                        }`}
                      >
                        {isSelected && <Check className="size-3.5 stroke-[3]" />}
                      </span>
                    </span>
                    <span className="block text-sm font-semibold text-white">{opt.name}</span>
                    <span className="block text-xs leading-relaxed text-[#8b949e]">{opt.description}</span>
                  </span>

                  <span className="mt-4 pt-3 border-t border-[#21262d] flex flex-wrap items-center justify-between gap-2 text-xs">
                    <span className="text-[#8b949e]">Add-on price</span>
                    <span className="font-bold text-[#3fb950]">+{formatPrice(opt.price_delta_usd)}</span>
                  </span>
                </button>
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

              {/* AT-20: renewed consent — the traveler previously accepted an
                  older revision; show those terms and prompt re-review. */}
              {proposal?.requires_reacceptance && (
                <div
                  role="note"
                  data-testid="reacceptance-banner"
                  className="rounded-lg border border-[#d29922]/40 bg-[#d29922]/10 p-4 text-sm text-[#d29922]"
                >
                  <p className="font-semibold">
                    You previously accepted this proposal
                    {proposal.accepted_agreement?.accepted_at
                      ? ` on ${new Date(proposal.accepted_agreement.accepted_at).toLocaleDateString()}`
                      : ''}.
                  </p>
                  <p className="mt-1 text-[#c9d1d9]">
                    The proposal has since been updated. Review the updated
                    proposal and accept again — your earlier acceptance terms
                    {proposal.accepted_agreement?.selected_total_price
                      ? ` (total ${proposal.accepted_agreement.currency ?? ''} ${proposal.accepted_agreement.selected_total_price.toLocaleString()})`
                      : ''} are superseded only once you re-accept.
                  </p>
                </div>
              )}

              {isCalculating && <p role="status" className="text-xs text-[#8b949e]">Updating proposal price…</p>}
              {pricingError && <p role="alert" className="text-xs text-[#ff7b72]">{pricingError}</p>}
              {acceptanceError && (
                <div
                  role="alert"
                  data-testid="acceptance-error"
                  className="rounded-lg border border-red-500/40 bg-red-500/10 p-4 text-sm text-red-400"
                >
                  <p>{acceptanceError}</p>
                  {/* AT-20 recovery action: re-fetch the proposal so the
                      traveler reviews the CURRENT revision before re-signing. */}
                  <button
                    type="button"
                    disabled={isReviewingRevision}
                    onClick={async () => {
                      setESignConsent(false);
                      setIsReviewingRevision(true);
                      try {
                        await loadProposal(true);
                      } finally {
                        setIsReviewingRevision(false);
                      }
                    }}
                    className="mt-2 px-3 py-1.5 rounded-lg border border-red-500/40 bg-red-500/10 text-xs font-semibold text-red-300 hover:bg-red-500/20 transition-colors"
                  >
                    {isReviewingRevision ? 'Loading latest proposal…' : 'Review latest proposal'}
                  </button>
                </div>
              )}

              <form onSubmit={handleAccept} className="space-y-4 max-w-xl">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="space-y-1.5">
                    <label htmlFor="proposal-signer-name" className="text-xs font-semibold text-[#8b949e]">Full Legal Name</label>
                    <input
                      type="text"
                      required
                      id="proposal-signer-name"
                      value={signerName}
                      onChange={(e) => setSignerName(e.target.value)}
                      placeholder="e.g. Priya Sharma"
                      className="w-full px-3.5 py-2.5 rounded-lg border border-[#30363d] bg-[#0d1117] text-white text-sm focus:outline-none focus:border-[#58a6ff]"
                    />
                  </div>
                  <div className="space-y-1.5">
                    <label htmlFor="proposal-signer-email" className="text-xs font-semibold text-[#8b949e]">Email Address</label>
                    <input
                      type="email"
                      required
                      id="proposal-signer-email"
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
                    disabled={signingBlocked}
                    onChange={(e) => setESignConsent(e.target.checked)}
                    className="mt-1 size-4 rounded border-[#30363d] bg-[#0d1117] text-[#58a6ff]"
                  />
                  <label htmlFor="consent-check" className="text-xs text-[#8b949e] leading-relaxed cursor-pointer">
                    I agree to the terms of this itinerary and authorize Waypoint OS to
                    record my acceptance of this proposal at the selected total of{' '}
                    <strong className="text-white">{selectedTotalLabel}</strong>. A
                    travel advisor will then secure the reservations.
                  </label>
                </div>

                <button
                  type="submit"
                  disabled={signingBlocked || !signerName || !signerEmail || !eSignConsent}
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
