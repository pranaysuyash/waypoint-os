"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  DESTINATION_CATALOG_REGISTRY,
  NEED_CONFIRMATION_CELLS,
  type BoardRowId,
  type DepartureInquiryFixture,
  type InquiryId,
} from "./board-fixtures";
import { splitFlapAudio } from "./board-engine";
import { writeDepartureBoardHandoff } from "@/lib/departure-board-handoff";

interface DepartureBoardFoldsProps {
  fixture: DepartureInquiryFixture;
  activeCaseSlug: string;
  workbenchCaseHref: string;
  isAutoCycling: boolean;
  onToggleAutoCycle: () => void;
  isDatesConfirmed: boolean;
  onToggleDatesConfirmed: () => void;
  selectedRowId: BoardRowId | null;
  onSelectRow: (rowId: BoardRowId) => void;
  onSelectPresetInquiry: (id: InquiryId) => void;
  onApplyDynamicInquiry: (rawInput: string) => void;
  onTriggerVoiceSequence: () => void;
  onOpenStageOnHero: (mode: "hero" | "voice_ingest" | "provenance_brief") => void;
}

const WAVEFORM_BARS = [
  28, 52, 74, 42, 88, 64, 35, 92, 78, 48, 62, 85, 96, 58, 40, 72, 84, 50, 36,
  68, 90, 60, 44, 76, 54, 82, 46, 66, 38, 70, 56, 42,
];

const SLOT_CHANNEL_LABELS: Record<BoardRowId, string> = {
  destination: "Voice Note (0:04) + WhatsApp Msg 01",
  travelers: "Voice Note (0:09) + WhatsApp Msg 01",
  duration: "Voice Note (0:14) + WhatsApp Msg 01",
  dates: "WhatsApp Msg 03 · Assumptions Register",
  tripStyle: "WhatsApp Msg 02 + Msg 04",
};

const SLOT_AUTHORITY_META: Record<
  BoardRowId,
  { fieldKey: string; confidence: string; authority: string }
> = {
  destination: {
    fieldKey: "destination_candidates",
    confidence: "98%",
    authority: "explicit_user",
  },
  travelers: {
    fieldKey: "party_size",
    confidence: "96%",
    authority: "explicit_user",
  },
  duration: {
    fieldKey: "duration_days",
    confidence: "92%",
    authority: "explicit_user",
  },
  dates: {
    fieldKey: "date_window",
    confidence: "54%",
    authority: "unconfirmed_assumption",
  },
  tripStyle: {
    fieldKey: "trip_purpose",
    confidence: "89%",
    authority: "derived_signal",
  },
};

const SLOT_FOLLOW_UP_FALLBACKS: Record<BoardRowId, string> = {
  destination:
    "Verify preferred arrival/departure city pair and internal transfer preferences.",
  travelers:
    "Confirm rooming configuration (suite split vs. interconnecting rooms) and traveler ages.",
  duration:
    "Validate pacing across stops so no single transfer day exceeds traveler comfort.",
  dates:
    "Ask the traveler to confirm exact departure and return dates before locking supplier quotes.",
  tripStyle:
    "Match boutique property tier and private guide allocation to stated trip style.",
};

export const DepartureBoardFolds: React.FC<DepartureBoardFoldsProps> = ({
  fixture,
  activeCaseSlug,
  workbenchCaseHref,
  isAutoCycling,
  onToggleAutoCycle,
  isDatesConfirmed,
  onToggleDatesConfirmed,
  selectedRowId,
  onSelectRow,
  onSelectPresetInquiry,
  onApplyDynamicInquiry,
  onTriggerVoiceSequence,
  onOpenStageOnHero,
}) => {
  const [activeWorkbenchTab, setActiveWorkbenchTab] = useState<
    "intake" | "packet" | "channels" | "decision"
  >("intake");
  const [activeGateStep, setActiveGateStep] = useState<number>(0);
  const [foldCustomQuery, setFoldCustomQuery] = useState<string>("");
  const [activeBentoRowId, setActiveBentoRowId] =
    useState<BoardRowId>("dates");

  const persistHandoffSession = () => {
    writeDepartureBoardHandoff({
      source: "departure-board",
      caseSlug: activeCaseSlug,
      caseTitle: fixture.pillTitle,
      iataCode: fixture.tagCode,
      prefill: fixture.voiceNote.quote.replace(/^[“"]|[”"]$/g, ""),
    });
  };

  const handleDestinationSelect = (slug: string, displayName: string) => {
    if (slug === "italy" || slug === "japan" || slug === "morocco") {
      onSelectPresetInquiry(slug);
    } else {
      onApplyDynamicInquiry(displayName);
    }
  };

  const primaryPhotoSrc =
    fixture.rows[0]?.photoFlap?.src ??
    fixture.briefSummary[0]?.thumbUrl ??
    "/landing/departure-board/photo-italy-1.png";
  const secondaryPhotoSrc =
    fixture.rows[2]?.photoFlap?.src ??
    fixture.briefSummary[4]?.thumbUrl ??
    "/landing/departure-board/photo-italy-2.png";

  const activeBentoRow =
    fixture.rows.find((r) => r.id === activeBentoRowId) ?? fixture.rows[3];

  const datesRow = fixture.rows.find((r) => r.id === "dates");
  const datesConfirmedClean =
    datesRow?.confirmedValueLabel
      ?.replace(/\s*\(Confirmed\)/i, "")
      ?.replace(/[–—]/g, "-")
      ?.toUpperCase() ?? "JUN 10 - 16";

  const datesResolvedString = isDatesConfirmed
    ? datesConfirmedClean
    : "NEED CONFIRMATION";

  const pipelineSteps = [
    { id: "intake", label: "New Inquiry", done: true },
    { id: "packet", label: "Trip Details", done: true },
    {
      id: "decision",
      label: "Ready to Quote?",
      done: isDatesConfirmed,
      current: !isDatesConfirmed,
    },
    {
      id: "strategy",
      label: "Build Options",
      done: false,
      current: isDatesConfirmed,
    },
    { id: "safety", label: "Final Review", done: false, current: false },
  ];

  return (
    <div className="relative bg-[#030d29] text-white overflow-hidden">
      {/* =====================================================================
          SYNCHRONIZED INQUIRY STATUS BAR: HERO -> WAYPOINT OS WORKBENCH
         ===================================================================== */}
      <div className="relative border-t border-b border-white/10 bg-[#051339]/90 py-3.5 px-6 sm:px-12">
        <div className="max-w-[1440px] mx-auto flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-2.5">
            <span className="inline-flex h-2 w-2 rounded-full bg-[#3fb950] animate-pulse" />
            <span className="font-mono text-[11px] font-bold uppercase tracking-[0.18em] text-slate-300">
              LIVE INQUIRY SYNCHRONIZED WITH WAYPOINT OS WORKSPACE
            </span>
          </div>
          <div className="flex flex-wrap items-center gap-4 font-mono text-[11px]">
            <span className="text-slate-400">
              DESTINATION:{" "}
              <strong className="text-white">
                {fixture.pillTitle} ({fixture.tagCode})
              </strong>
            </span>
            <span className="text-slate-600">·</span>
            <span className="text-slate-400">
              PARTY:{" "}
              <strong className="text-white">
                {fixture.rows[1]?.fact.value}
              </strong>
            </span>
            <span className="text-slate-600">·</span>
            <span className="text-slate-400">
              DURATION:{" "}
              <strong className="text-white">
                {fixture.rows[2]?.fact.value}
              </strong>
            </span>
            <span className="text-slate-600">·</span>
            <span
              className={
                isDatesConfirmed
                  ? "text-[#3fb950] font-bold"
                  : "text-[#d29922] font-bold"
              }
            >
              {isDatesConfirmed
                ? `READY TO QUOTE (${datesResolvedString})`
                : "WAITING ON CUSTOMER · DATES UNCONFIRMED"}
            </span>
          </div>
        </div>
      </div>

      {/* =====================================================================
          FOLD 2: ACTUAL WAYPOINT OS WORKBENCH PREVIEW (#product)
         ===================================================================== */}
      <section
        id="product"
        className="relative py-20 sm:py-28 px-6 sm:px-12 max-w-[1440px] mx-auto"
      >
        <div className="relative z-10 grid grid-cols-1 lg:grid-cols-12 gap-8 xl:gap-10 items-start">
          {/* LEFT COLUMN (4 cols): Product Copy + Inquiry Switcher + 3 Workflow Steps */}
          <div className="lg:col-span-4 space-y-6">
            <div className="inline-flex items-center gap-2.5 rounded-full bg-[#09215c] border border-[#58a6ff]/40 px-4 py-1.5 text-[10.5px] font-mono uppercase tracking-[0.2em] text-[#93c5fd]">
              <span className="h-2 w-2 rounded-full bg-[#58a6ff] animate-pulse" />
              <span>Waypoint OS · Live Agency Workspace</span>
            </div>

            <h2 className="text-3xl sm:text-4xl font-bold tracking-[-0.03em] text-white leading-[1.08]">
              Turn raw trip notes into quote-ready briefs
            </h2>

            <p className="text-sm sm:text-base text-slate-200/90 leading-relaxed">
              Waypoint helps boutique travel agencies turn the notes they already
              have, whether from calls, emails, WhatsApp messages, or copied
              itineraries, into structured trip briefs ready for advisor review.
            </p>

            {/* Active Traveler Inquiry Card (Syncs with Workbench on the right) */}
            <div className="rounded-2xl bg-[#0d1117] border border-[#30363d] p-4 space-y-4 shadow-[0_20px_50px_rgba(0,0,0,0.45)]">
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#30363d] pb-3">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-[10px] font-bold uppercase tracking-wider text-[#8b949e]">
                    Active Inquiry
                  </span>
                  <span className="rounded bg-[#21262d] border border-[#30363d] px-2 py-0.5 font-mono text-[10px] font-bold text-[#58a6ff]">
                    {fixture.pillTitle} · {fixture.tagCode}
                  </span>
                </div>

                <button
                  type="button"
                  onClick={onToggleAutoCycle}
                  className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 font-mono text-[10px] font-bold whitespace-nowrap transition-all ${
                    isAutoCycling
                      ? "bg-[#238636]/20 text-[#3fb950] border border-[#3fb950]/40"
                      : "bg-[#d29922]/20 text-[#d29922] border border-[#d29922]/40"
                  }`}
                  data-testid="fold2-auto-stream-toggle"
                >
                  <span
                    className={`h-1.5 w-1.5 rounded-full shrink-0 ${
                      isAutoCycling
                        ? "bg-[#3fb950] animate-pulse"
                        : "bg-[#d29922]"
                    }`}
                  />
                  <span>
                    {isAutoCycling ? "Auto-Stream: ON" : "Auto-Stream: PAUSED"}
                  </span>
                </button>
              </div>

              {/* Destination Visual Thumbnail Pair */}
              <div className="grid grid-cols-12 gap-2.5 items-stretch">
                <div className="col-span-7 relative rounded-xl overflow-hidden border border-[#30363d] h-[104px] bg-slate-950">
                  <img
                    src={primaryPhotoSrc}
                    alt={`${fixture.pillTitle} destination preview`}
                    className="h-full w-full object-cover"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-slate-950/90 via-slate-950/20 to-transparent" />
                  <div className="absolute bottom-2 left-2.5 right-2.5 flex items-end justify-between">
                    <div>
                      <p className="font-mono text-[8.5px] uppercase tracking-wider text-[#58a6ff]">
                        {fixture.rows[4]?.fact.value}
                      </p>
                      <p className="text-sm font-bold text-white leading-tight">
                        {fixture.pillTitle}
                      </p>
                    </div>
                    <span className="rounded bg-[#f4efe6] text-slate-950 px-1.5 py-0.5 font-mono text-[10px] font-black">
                      {fixture.tagCode}
                    </span>
                  </div>
                </div>

                <div className="col-span-5 flex flex-col justify-between gap-2">
                  <div className="relative rounded-xl overflow-hidden border border-[#30363d] h-[58px] bg-slate-950">
                    <img
                      src={secondaryPhotoSrc}
                      alt={`${fixture.pillTitle} secondary view`}
                      className="h-full w-full object-cover"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-slate-950/85 via-transparent to-transparent" />
                    <span className="absolute bottom-1 left-2 font-mono text-[9px] font-bold text-white">
                      {fixture.rows[2]?.fact.value} · {fixture.rows[1]?.fact.value}
                    </span>
                  </div>
                  <div className="rounded-lg bg-[#161b22] border border-[#30363d] px-2.5 py-1.5 flex items-center justify-between">
                    <span className="font-mono text-[9px] text-[#8b949e]">
                      {fixture.pillSubtitle}
                    </span>
                    <span className="h-2 w-2 rounded-full bg-[#58a6ff]" />
                  </div>
                </div>
              </div>

              {/* 15-Destination Switcher */}
              <div className="space-y-1.5">
                <span className="block text-[11px] font-medium text-[#8b949e]">
                  Load a sample client inquiry into the Workbench:
                </span>
                <div className="flex flex-wrap items-center gap-1">
                  {DESTINATION_CATALOG_REGISTRY.map((entry) => {
                    const isActive =
                      fixture.pillTitle.toLowerCase() ===
                      entry.displayName.toLowerCase();
                    return (
                      <button
                        key={entry.slug}
                        type="button"
                        onClick={() =>
                          handleDestinationSelect(entry.slug, entry.displayName)
                        }
                        className={`inline-flex items-center gap-1 rounded-md px-2 py-1 text-[10.5px] font-semibold transition-all ${
                          isActive
                            ? "bg-[#58a6ff] text-[#0d1117]"
                            : "bg-[#161b22] text-[#c9d1d9] hover:bg-[#21262d] border border-[#30363d]"
                        }`}
                        data-testid={`fold2-switch-${entry.slug}`}
                      >
                        <span>{entry.displayName}</span>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Custom Natural-Language Inquiry Input */}
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  if (!foldCustomQuery.trim()) return;
                  onApplyDynamicInquiry(foldCustomQuery.trim());
                }}
                className="pt-2 border-t border-[#30363d] flex items-center gap-2"
              >
                <input
                  type="text"
                  value={foldCustomQuery}
                  onChange={(e) => setFoldCustomQuery(e.target.value)}
                  placeholder="Or paste any inquiry: 4 travelers to Amalfi for 10 days..."
                  aria-label="Compile custom travel inquiry in Fold 2"
                  className="flex-1 rounded-lg bg-[#0f1115] border border-[#30363d] px-3 py-1.5 text-xs text-[#e6edf3] placeholder:text-[#8b949e] focus:outline-none focus:border-[#58a6ff]"
                  data-testid="fold2-custom-inquiry-input"
                />
                <button
                  type="submit"
                  className="rounded-lg bg-[#58a6ff] hover:bg-[#6eb5ff] text-[#0d1117] text-xs font-semibold px-3 py-1.5 transition-all shrink-0"
                  data-testid="fold2-custom-inquiry-submit"
                >
                  Process →
                </button>
              </form>
            </div>

            {/* 3 Concrete Workflow Improvements (Click to switch Workbench tabs) */}
            <ul className="space-y-2.5">
              {[
                {
                  num: "01",
                  title:
                    "Extract dates, party size, budget, pace, and trip type from messy messages",
                  body: "Customer voice notes, WhatsApp messages, and emails populate Captured Details and Real-Time Triage automatically.",
                  tabLabel: "View in New Inquiry Tab →",
                  onTrigger: () => {
                    setActiveGateStep(0);
                    setActiveWorkbenchTab("intake");
                  },
                },
                {
                  num: "02",
                  title:
                    "Surface the missing facts that change itinerary quality before anyone quotes",
                  body: "Unconfirmed dates or budgets are flagged in the Trip Details Assumptions register so no advisor quotes on guesswork.",
                  tabLabel: "View in Trip Details Tab →",
                  onTrigger: () => {
                    setActiveGateStep(1);
                    setActiveWorkbenchTab("packet");
                  },
                },
                {
                  num: "03",
                  title:
                    "Protect owner time by showing what needs a human decision and what does not",
                  body: "Decision & Risk Review separates ready-to-quote trips from inquiries waiting on customer confirmation.",
                  tabLabel: "View in Decision Tab →",
                  onTrigger: () => {
                    setActiveGateStep(2);
                    setActiveWorkbenchTab("decision");
                  },
                },
              ].map((step, idx) => {
                const isActive = activeGateStep === idx;
                return (
                  <li
                    key={step.num}
                    onClick={step.onTrigger}
                    className={`cursor-pointer rounded-xl border p-3.5 transition-all ${
                      isActive
                        ? "bg-[#161b22] border-[#58a6ff] shadow-md"
                        : "bg-[#0d1117]/80 hover:bg-[#161b22] border-[#30363d]"
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <span
                        className={`mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-md font-mono text-xs font-bold ${
                          isActive
                            ? "bg-[#58a6ff] text-[#0d1117]"
                            : "bg-[#21262d] text-[#8b949e]"
                        }`}
                      >
                        {step.num}
                      </span>
                      <div>
                        <p className="font-semibold text-[#e6edf3] text-xs sm:text-sm">
                          {step.title}
                        </p>
                        <p className="text-xs text-[#8b949e] mt-1 leading-relaxed">
                          {step.body}
                        </p>
                        <span className="mt-1.5 inline-block font-mono text-[10px] font-semibold text-[#58a6ff]">
                          {step.tabLabel}
                        </span>
                      </div>
                    </div>
                  </li>
                );
              })}
            </ul>

            {/* Primary CTAs */}
            <div className="pt-1 flex flex-wrap items-center gap-3">
              <Link
                href="/signup"
                onClick={persistHandoffSession}
                className="inline-flex items-center gap-2 rounded-full bg-[#f5c418] hover:bg-[#fde047] text-slate-950 font-bold text-sm px-6 py-2.5 shadow-lg transition-all"
              >
                <span>Create workspace</span>
                <span aria-hidden="true">→</span>
              </Link>
              <Link
                href={workbenchCaseHref}
                className="inline-flex items-center gap-2 rounded-full bg-[#161b22] hover:bg-[#21262d] border border-[#30363d] text-[#e6edf3] font-semibold text-sm px-5 py-2.5 transition-all"
              >
                <span>Open Advisor Workbench</span>
              </Link>
            </div>
          </div>

          {/* RIGHT COLUMN (8 cols): THE ACTUAL WAYPOINT OS AGENCY WORKSPACE UI */}
          <div className="lg:col-span-8 rounded-2xl bg-[#0d1117] border border-[#30363d] shadow-[0_32px_90px_rgba(0,0,0,0.75)] overflow-hidden">
            {/* 1. Waypoint OS Top Application Bar (Matches Shell.tsx) */}
            <div className="flex flex-wrap items-center justify-between gap-3 bg-[#0d1117] border-b border-[#30363d] px-4 py-2.5">
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-2">
                  <span className="flex h-6 w-6 items-center justify-center rounded-md bg-[#58a6ff]/15 border border-[#58a6ff]/40 text-[#58a6ff] text-xs font-bold">
                    W
                  </span>
                  <div className="leading-none">
                    <span className="text-xs font-semibold text-[#e6edf3] block">
                      Waypoint OS
                    </span>
                    <span className="text-[10px] text-[#8b949e]">
                      Agency Workspace
                    </span>
                  </div>
                </div>
                <span className="text-[#30363d]">/</span>
                <span className="text-xs text-[#8b949e]">
                  Inquiries /{" "}
                  <strong className="text-[#e6edf3]">
                    {fixture.pillTitle} ({fixture.tagCode})
                  </strong>
                </span>
              </div>

              <div className="flex items-center gap-3">
                <span className="inline-flex items-center gap-1.5 text-[11px] text-[#8b949e]">
                  <span className="text-[#d29922]">⚡</span> System ready
                </span>
                <span className="inline-flex items-center gap-1.5 text-[11px] text-[#3fb950]">
                  <span className="h-2 w-2 rounded-full bg-[#3fb950]" />
                  Operations live
                </span>
                <span className="flex h-6 w-6 items-center justify-center rounded-full bg-[#1f6feb] text-[10px] font-bold text-white">
                  AG
                </span>
              </div>
            </div>

            {/* 2. Routing Guidance Banner (Matches PageClient.tsx) */}
            <div className="bg-[#161b22]/70 border-b border-[#30363d] px-4 py-1.5 text-[11px] text-[#8b949e]">
              After processing: incomplete leads appear in{" "}
              <span className="text-[#c9d1d9] font-medium">Lead Inbox</span> ·
              planning continues in{" "}
              <span className="text-[#c9d1d9] font-medium">
                Trips in Planning
              </span>{" "}
              · quotes needing approval appear in{" "}
              <span className="text-[#c9d1d9] font-medium">Quote Review</span>
            </div>

            {/* 3. Shell Body: Left Navigation Sidebar + Main Workbench */}
            <div className="grid grid-cols-1 xl:grid-cols-12 min-h-[640px]">
              {/* Left Sidebar (Matches Shell.tsx + nav-modules.ts) */}
              <aside className="hidden xl:flex xl:col-span-3 flex-col justify-between bg-[#0d1117] border-r border-[#30363d] p-3 select-none">
                <div className="space-y-4">
                  <Link
                    href={workbenchCaseHref}
                    className="w-full flex items-center justify-center gap-2 rounded-lg border border-[#30363d] bg-[#161b22] hover:bg-[#21262d] px-3 py-2 text-xs font-medium text-[#e6edf3] transition-colors"
                  >
                    <span>+ New Inquiry</span>
                  </Link>

                  {/* Current Trip Context Card (Matches SidebarTripContext in Shell.tsx) */}
                  <div
                    className="rounded-lg border p-2.5 space-y-1.5"
                    style={{
                      background: isDatesConfirmed
                        ? "rgba(63, 185, 80, 0.08)"
                        : "rgba(210, 153, 34, 0.08)",
                      borderColor: isDatesConfirmed
                        ? "rgba(63, 185, 80, 0.28)"
                        : "rgba(210, 153, 34, 0.28)",
                    }}
                  >
                    <div className="flex items-center justify-between gap-1">
                      <span className="text-[9.5px] font-semibold uppercase tracking-wider text-[#8b949e]">
                        Current trip
                      </span>
                      <span
                        className={`inline-flex items-center gap-1 rounded px-1.5 py-0.5 text-[9.5px] font-semibold ${
                          isDatesConfirmed
                            ? "text-[#3fb950]"
                            : "text-[#d29922]"
                        }`}
                      >
                        <span
                          className={`h-1.5 w-1.5 rounded-full ${
                            isDatesConfirmed ? "bg-[#3fb950]" : "bg-[#d29922]"
                          }`}
                        />
                        {isDatesConfirmed ? "Ready" : "Needs Dates"}
                      </span>
                    </div>
                    <p className="text-xs font-semibold text-[#e6edf3] truncate">
                      {fixture.pillTitle} · {fixture.rows[1]?.fact.value}
                    </p>
                    <p className="text-[10.5px] text-[#8b949e] leading-snug">
                      {isDatesConfirmed
                        ? "All 5 fields verified. Ready to build quote options."
                        : "Waiting on customer to confirm exact travel dates."}
                    </p>
                  </div>

                  {/* Nav Sections from nav-modules.ts */}
                  {[
                    {
                      section: "COMMAND",
                      items: [
                        { label: "Overview", active: false },
                        { label: "Lead Inbox", active: false, badge: "4" },
                        { label: "Quote Review", active: false },
                      ],
                    },
                    {
                      section: "PLANNING",
                      items: [
                        { label: "Trips in Planning", active: true },
                        { label: "Quotes", active: false },
                        { label: "Bookings", active: false },
                      ],
                    },
                    {
                      section: "OPERATIONS",
                      items: [
                        { label: "Documents", active: false },
                        { label: "Payments", active: false },
                        { label: "Suppliers", active: false },
                      ],
                    },
                    {
                      section: "INTELLIGENCE",
                      items: [
                        { label: "Insights", active: false },
                        { label: "Destination Intel", active: false },
                        { label: "Audit", active: false },
                        { label: "Knowledge Base", active: false },
                      ],
                    },
                  ].map((group) => (
                    <div key={group.section} className="space-y-1">
                      <p className="px-2 text-[9.5px] font-semibold uppercase tracking-wider text-[#8b949e]">
                        {group.section}
                      </p>
                      {group.items.map((item) => (
                        <div
                          key={item.label}
                          className={`flex items-center justify-between rounded-md px-2 py-1 text-[11.5px] ${
                            item.active
                              ? "bg-[#1f242c] text-[#e6edf3] font-medium"
                              : "text-[#8b949e]"
                          }`}
                        >
                          <span>{item.label}</span>
                          {item.badge && (
                            <span className="rounded-full bg-[#21262d] px-1.5 py-0.2 text-[9.5px] text-[#58a6ff] font-mono">
                              {item.badge}
                            </span>
                          )}
                        </div>
                      ))}
                    </div>
                  ))}
                </div>

                <div className="pt-3 border-t border-[#30363d] flex items-center justify-between text-[10.5px] text-[#8b949e]">
                  <span>● Operations live</span>
                  <span className="font-mono">{fixture.tagCode}</span>
                </div>
              </aside>

              {/* Main Workbench Content Area (Matches PageClient.tsx) */}
              <div className="xl:col-span-9 bg-[#080a0c] p-4 sm:p-6 space-y-5">
                {/* Workbench Header + Primary Actions */}
                <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4 border-b border-[#30363d] pb-4">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="text-[11px] font-mono uppercase tracking-wider text-[#58a6ff]">
                        New Inquiry · {fixture.pillTitle}
                      </span>
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-medium border ${
                          isDatesConfirmed
                            ? "bg-[#238636]/15 text-[#3fb950] border-[#3fb950]/40"
                            : "bg-[#d29922]/15 text-[#d29922] border-[#d29922]/40"
                        }`}
                      >
                        {isDatesConfirmed ? "Promoted · Ready" : "Waiting on Customer"}
                      </span>
                    </div>
                    <h3 className="text-lg sm:text-xl font-bold text-[#e6edf3] leading-snug">
                      It helps teams answer faster, quote cleaner, and keep owners
                      out of every tiny decision
                    </h3>
                    <p className="text-xs text-[#8b949e]">
                      Capture a customer request and send it into the workflow ·{" "}
                      <span className="text-[#3fb950]">
                        Synced with {fixture.pillTitle} ({fixture.tagCode})
                      </span>
                    </p>
                  </div>

                  {/* Workbench Action Buttons (Matches PageClient.tsx lines 715-847) */}
                  <div className="flex flex-wrap items-center gap-2 shrink-0">
                    <button
                      type="button"
                      onClick={() => {
                        splitFlapAudio.playFlapClack(4, true);
                        onTriggerVoiceSequence();
                      }}
                      className="inline-flex items-center gap-1.5 rounded-lg bg-[#58a6ff] hover:bg-[#6eb5ff] px-3.5 py-2 text-xs font-semibold text-[#0d1117] transition-colors"
                    >
                      <span>▷ Process Inquiry</span>
                    </button>
                    <button
                      type="button"
                      onClick={onToggleDatesConfirmed}
                      className="inline-flex items-center gap-1.5 rounded-lg border border-[#30363d] bg-[#161b22] hover:bg-[#21262d] px-3 py-2 text-xs font-medium text-[#e6edf3] transition-colors"
                      data-testid="fold2-confirm-dates-toggle"
                    >
                      <span>
                        {isDatesConfirmed
                          ? "✓ Dates Confirmed (Reset)"
                          : "Confirm Client Dates"}
                      </span>
                    </button>
                  </div>
                </div>

                {/* 5-Stage Pipeline Progress Bar (Matches PipelineFlow.tsx) */}
                <div className="rounded-xl bg-[#0f1115] border border-[#30363d] px-3.5 py-2.5 flex flex-wrap items-center justify-between gap-2">
                  {pipelineSteps.map((step, idx) => (
                    <div key={step.id} className="flex items-center gap-2">
                      <span
                        className={`flex h-5 w-5 items-center justify-center rounded-full text-[10px] font-bold ${
                          step.done
                            ? "bg-[#3fb950] text-[#0d1117]"
                            : step.current
                            ? "bg-[#58a6ff] text-[#0d1117]"
                            : "bg-[#21262d] text-[#8b949e]"
                        }`}
                      >
                        {step.done ? "✓" : idx + 1}
                      </span>
                      <span
                        className={`text-xs font-medium ${
                          step.done || step.current
                            ? "text-[#e6edf3]"
                            : "text-[#8b949e]"
                        }`}
                      >
                        {step.label}
                      </span>
                      {idx < pipelineSteps.length - 1 && (
                        <span className="text-[#30363d] hidden sm:inline ml-1">
                          →
                        </span>
                      )}
                    </div>
                  ))}
                </div>

                {/* Workspace Tabs (Matches workspaceTabs in workbench-state.ts) */}
                <div className="flex flex-wrap items-center gap-1 border-b border-[#30363d]">
                  {(
                    [
                      { id: "intake", label: "New Inquiry" },
                      { id: "packet", label: "Trip Details" },
                      { id: "channels", label: "Lead Inbox Thread (4)" },
                      { id: "decision", label: "Decision & Destination Intel" },
                    ] as const
                  ).map((tab) => (
                    <button
                      key={tab.id}
                      type="button"
                      onClick={() => setActiveWorkbenchTab(tab.id)}
                      className={`px-3.5 py-2 text-xs font-medium border-b-2 transition-colors ${
                        activeWorkbenchTab === tab.id
                          ? "border-[#58a6ff] text-[#e6edf3] bg-[#161b22]/60"
                          : "border-transparent text-[#8b949e] hover:text-[#c9d1d9]"
                      }`}
                    >
                      {tab.label}
                    </button>
                  ))}
                </div>

                {/* Captured Details 6-Column Bar (Matches IntakeTab.tsx lines 141-182) */}
                <div className="bg-[#161b22] border border-[#30363d] rounded-xl p-3.5">
                  <div className="flex items-center justify-between gap-2 mb-3">
                    <div className="flex items-center gap-2">
                      <span className="text-[#58a6ff] text-xs">✈</span>
                      <h4 className="text-xs font-semibold text-[#e6edf3]">
                        Captured Details
                      </h4>
                    </div>
                    <span className="font-mono text-[10px] text-[#8b949e]">
                      Click any field to inspect source quote
                    </span>
                  </div>
                  <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2.5">
                    {fixture.rows.map((row) => {
                      const isDates = row.id === "dates";
                      const val =
                        isDates && isDatesConfirmed && row.confirmedValueLabel
                          ? row.confirmedValueLabel.replace(
                              /\s*\(Confirmed\)/i,
                              ""
                            )
                          : row.fact.value;
                      const isUnconfirmed = isDates && !isDatesConfirmed;
                      return (
                        <button
                          key={row.id}
                          type="button"
                          onClick={() => onSelectRow(row.id)}
                          className={`text-left rounded-lg p-2 border transition-all ${
                            isUnconfirmed
                              ? "bg-[#d29922]/10 border-[#d29922]/40"
                              : "bg-[#0f1115] border-[#30363d] hover:border-[#58a6ff]/50"
                          }`}
                        >
                          <span className="block text-[10px] text-[#8b949e] uppercase tracking-wide">
                            {row.label}
                          </span>
                          <span
                            className={`block text-xs font-semibold mt-0.5 truncate ${
                              isUnconfirmed
                                ? "text-[#d29922]"
                                : "text-[#e6edf3]"
                            }`}
                          >
                            {val}
                          </span>
                        </button>
                      );
                    })}
                    <div className="rounded-lg p-2 bg-[#0f1115] border border-[#30363d]">
                      <span className="block text-[10px] text-[#8b949e] uppercase tracking-wide">
                        Reference
                      </span>
                      <span className="block text-xs font-mono text-[#e6edf3] mt-0.5">
                        TRP-{fixture.tagCode}
                      </span>
                    </div>
                  </div>
                </div>

                {/* TAB CONTENT AREA */}
                {activeWorkbenchTab === "intake" ? (
                  <div className="space-y-4">
                    {/* Repeat Traveler Recall Card (Matches RepeatTravelerRecallCard in IntakeTab.tsx) */}
                    <div className="rounded-xl border border-indigo-500/30 bg-[#121624] p-3.5 space-y-2.5">
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="text-xs font-semibold text-[#e6edf3]">
                            Repeat Traveler Memory
                          </span>
                          <span className="rounded-full bg-indigo-500/20 border border-indigo-400/30 px-2 py-0.5 text-[10px] font-medium text-indigo-300">
                            Repeat Client (3 Bookings)
                          </span>
                          <span className="rounded-full bg-[#d29922]/15 border border-[#d29922]/30 px-2 py-0.5 text-[10px] font-medium text-[#d29922]">
                            {fixture.pillSubtitle}
                          </span>
                        </div>
                        <span className="rounded border border-[#d29922]/40 bg-[#d29922]/10 px-2 py-0.5 font-mono text-[9.5px] text-[#d29922]">
                          AUTO-RECALLED
                        </span>
                      </div>
                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5 text-xs">
                        <div className="rounded-lg bg-[#0d1117] border border-[#30363d] p-2.5">
                          <div className="flex items-center justify-between text-[10px] text-[#8b949e]">
                            <span>Dietary / Pacing</span>
                            <span className="text-[#3fb950]">
                              Permanent Safety
                            </span>
                          </div>
                          <p className="text-[#e6edf3] font-medium mt-1 text-[11.5px]">
                            Max 2 property moves · private transfers preferred
                          </p>
                        </div>
                        <div className="rounded-lg bg-[#0d1117] border border-[#30363d] p-2.5">
                          <div className="flex items-center justify-between text-[10px] text-[#8b949e]">
                            <span>Property Tier</span>
                            <span className="text-[#3fb950]">92% Fresh</span>
                          </div>
                          <p className="text-[#e6edf3] font-medium mt-1 text-[11.5px]">
                            Boutique 5-star &amp; design-led heritage stays
                          </p>
                        </div>
                        <div className="rounded-lg bg-[#0d1117] border border-[#30363d] p-2.5">
                          <div className="flex items-center justify-between text-[10px] text-[#8b949e]">
                            <span>Past Destination History</span>
                            <span className="text-[#3fb950]">95% Fresh</span>
                          </div>
                          <p className="text-[#e6edf3] font-medium mt-1 text-[11.5px]">
                            Active brief: {fixture.pillTitle} (
                            {fixture.rows[2]?.fact.value})
                          </p>
                        </div>
                      </div>
                    </div>

                    {/* Customer Message + Agent Notes 2-Column Split (Matches IntakeTab.tsx lines 210-324) */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {/* Customer Message Card */}
                      <div className="bg-[#161b22] border border-[#30363d] rounded-xl p-4 space-y-3">
                        <div className="flex items-center justify-between gap-2">
                          <span className="text-xs font-semibold text-[#e6edf3]">
                            Customer Message (Voice + WhatsApp)
                          </span>
                          <button
                            type="button"
                            onClick={() => {
                              splitFlapAudio.playFlapClack(4, true);
                              onTriggerVoiceSequence();
                            }}
                            className="inline-flex items-center gap-1.5 rounded-md bg-[#21262d] hover:bg-[#30363d] border border-[#30363d] px-2 py-1 text-[10.5px] font-medium text-[#58a6ff]"
                          >
                            <span>▶ Play Voice ({fixture.voiceNote.durationLabel})</span>
                          </button>
                        </div>

                        {/* Acoustic Waveform Strip */}
                        <div
                          aria-hidden="true"
                          className="flex items-center gap-[3px] h-6 px-2.5 rounded-lg bg-[#0f1115] border border-[#30363d]"
                        >
                          {WAVEFORM_BARS.slice(0, 24).map((pct, i) => (
                            <span
                              key={i}
                              className={`w-[3px] rounded-full ${
                                i % 5 === 0
                                  ? "bg-[#58a6ff]"
                                  : i < 16
                                  ? "bg-[#3fb950]"
                                  : "bg-[#30363d]"
                              }`}
                              style={{ height: `${Math.max(6, pct * 0.18)}px` }}
                            />
                          ))}
                        </div>

                        {/* Monospace Transcript Box */}
                        <div className="rounded-lg bg-[#0f1115] border border-[#30363d] p-3 font-mono text-xs text-[#e6edf3] leading-relaxed">
                          {fixture.voiceNote.quote}
                        </div>

                        {/* Live Semantic Triage Telemetry (Matches IntakeTab.tsx lines 243-298) */}
                        <div className="rounded-lg border border-[#30363d] bg-[#0d1117] p-2.5 space-y-1.5 text-[11px]">
                          <div className="flex items-center justify-between">
                            <span className="font-medium text-[#c9d1d9] flex items-center gap-1">
                              <span className="text-[#58a6ff]">⚡</span>{" "}
                              Real-Time Triage
                            </span>
                            <span className="font-mono text-[10px] text-[#8b949e]">
                              typesafe-jev • 18ms
                            </span>
                          </div>
                          <div className="flex flex-wrap items-center gap-1.5">
                            <span className="px-2 py-0.5 rounded bg-[#21262d] text-[#58a6ff] font-semibold uppercase text-[9.5px]">
                              Intent: new_inquiry
                            </span>
                            <span className="px-2 py-0.5 rounded bg-[#238636]/20 text-[#3fb950] font-medium text-[9.5px]">
                              Tone: HIGH_INTENT
                            </span>
                            <span className="px-2 py-0.5 rounded bg-[#1f242c] text-[#8b949e] text-[9.5px]">
                              Route: discovery_intake
                            </span>
                          </div>
                        </div>
                      </div>

                      {/* Agent Notes Card (Matches IntakeTab.tsx lines 301-323) */}
                      <div className="bg-[#161b22] border border-[#30363d] rounded-xl p-4 flex flex-col justify-between space-y-3">
                        <div className="space-y-2.5">
                          <div className="flex items-center justify-between">
                            <span className="text-xs font-semibold text-[#e6edf3]">
                              Agent Notes (Internal Only)
                            </span>
                            <span className="font-mono text-[10px] text-[#8b949e]">
                              Never shown to traveler
                            </span>
                          </div>
                          <p className="text-[11px] text-[#8b949e] leading-relaxed">
                            Internal qualification signals, risk flags, supplier
                            constraints, margin targets, and next-step
                            instructions for the team.
                          </p>
                          <div className="rounded-lg bg-[#0f1115] border border-[#30363d] p-3 text-xs text-[#c9d1d9] leading-relaxed space-y-1.5">
                            <p>
                              •{" "}
                              <strong className="text-[#e6edf3]">
                                Case:
                              </strong>{" "}
                              {fixture.pillTitle} ({fixture.rows[1]?.fact.value},{" "}
                              {fixture.rows[2]?.fact.value},{" "}
                              {fixture.rows[4]?.fact.value}).
                            </p>
                            <p>
                              •{" "}
                              <strong className="text-[#e6edf3]">
                                Commercial rule:
                              </strong>{" "}
                              Keep agency margin &gt;= 18% on boutique land
                              components.
                            </p>
                            <p>
                              •{" "}
                              <strong className="text-[#d29922]">
                                Next action:
                              </strong>{" "}
                              {datesRow?.fact.advisorFollowUp ??
                                "Confirm exact departure dates before locking rates."}
                            </p>
                          </div>
                        </div>

                        <div className="pt-2 border-t border-[#30363d] flex flex-wrap items-center justify-between gap-2">
                          <span className="text-[10.5px] text-[#8b949e]">
                            Extracted tokens:
                          </span>
                          <div className="flex flex-wrap gap-1">
                            {fixture.rows.map((r) => (
                              <button
                                key={r.id}
                                type="button"
                                onClick={() => onSelectRow(r.id)}
                                className="rounded bg-[#21262d] hover:bg-[#30363d] px-2 py-0.5 font-mono text-[9.5px] text-[#c9d1d9]"
                              >
                                {r.label} · {r.fact.value}
                              </button>
                            ))}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                ) : activeWorkbenchTab === "packet" ? (
                  /* TAB 2: TRIP DETAILS (Matches PacketTab.tsx: Validation Banner + Extracted Information Table + Assumptions) */
                  <div className="space-y-4">
                    {!isDatesConfirmed ? (
                      <div className="rounded-xl border border-[#f85149]/40 bg-[#2b1011] p-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                        <div className="space-y-1">
                          <h4 className="text-xs font-semibold text-[#f85149]">
                            Waiting on Customer — Unconfirmed Travel Dates
                          </h4>
                          <p className="text-[11px] text-[#ffa198]">
                            Missing or unconfirmed fields: Travel Dates
                            [PROPOSAL]. Confirm exact dates below before sending
                            a commercial quote.
                          </p>
                        </div>
                        <button
                          type="button"
                          onClick={onToggleDatesConfirmed}
                          className="shrink-0 rounded-lg border border-[#3fb950]/40 bg-[#3fb950]/15 px-3 py-1.5 text-xs font-semibold text-[#7ee787]"
                        >
                          Confirm Dates →
                        </button>
                      </div>
                    ) : (
                      <div className="rounded-xl border border-[#3fb950]/40 bg-[#132b1a] p-3.5 flex items-center justify-between">
                        <div>
                          <h4 className="text-xs font-semibold text-[#3fb950]">
                            All Checks Passed
                          </h4>
                          <p className="text-[11px] text-[#7ee787]">
                            All 5 trip fields verified ({datesConfirmedClean}).
                            Ready to build quote options.
                          </p>
                        </div>
                        <button
                          type="button"
                          onClick={onToggleDatesConfirmed}
                          className="rounded-lg border border-[#30363d] bg-[#161b22] px-2.5 py-1 text-[11px] text-[#8b949e]"
                        >
                          Reset to Unconfirmed
                        </button>
                      </div>
                    )}

                    {/* Extracted Information Table (Matches PacketTab.tsx lines 333-360) */}
                    <div className="bg-[#161b22] border border-[#30363d] rounded-xl overflow-hidden">
                      <div className="px-3.5 py-2.5 border-b border-[#30363d] flex items-center justify-between">
                        <span className="text-xs font-semibold text-[#e6edf3]">
                          Extracted Information
                        </span>
                        <span className="font-mono text-[10px] text-[#8b949e]">
                          PacketTab · Authority &amp; Confidence
                        </span>
                      </div>
                      <table className="w-full border-collapse text-left text-xs">
                        <thead>
                          <tr className="border-b border-[#30363d] text-[10.5px] text-[#8b949e]">
                            <th className="px-3.5 py-2 font-medium">Field</th>
                            <th className="px-3.5 py-2 font-medium">Value</th>
                            <th className="px-3.5 py-2 font-medium">
                              Confidence
                            </th>
                            <th className="px-3.5 py-2 font-medium">
                              Authority
                            </th>
                          </tr>
                        </thead>
                        <tbody>
                          {fixture.rows.map((row) => {
                            const meta = SLOT_AUTHORITY_META[row.id];
                            const isDates = row.id === "dates";
                            const displayVal =
                              isDates &&
                              isDatesConfirmed &&
                              row.confirmedValueLabel
                                ? row.confirmedValueLabel
                                : row.fact.value;
                            return (
                              <tr
                                key={row.id}
                                className="border-b border-[#30363d] last:border-0"
                              >
                                <td className="px-3.5 py-2 text-[#e6edf3] font-medium">
                                  {row.label}
                                </td>
                                <td className="px-3.5 py-2 text-[#e6edf3]">
                                  {displayVal}
                                </td>
                                <td className="px-3.5 py-2 text-[#8b949e] font-mono">
                                  {isDates && isDatesConfirmed
                                    ? "100%"
                                    : meta.confidence}
                                </td>
                                <td className="px-3.5 py-2 font-mono text-[11px]">
                                  <span
                                    className={
                                      isDates && !isDatesConfirmed
                                        ? "text-[#d29922]"
                                        : "text-[#3fb950]"
                                    }
                                  >
                                    {isDates && isDatesConfirmed
                                      ? "operator_confirmed"
                                      : meta.authority}
                                  </span>
                                </td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>

                    {/* Assumptions Register (Matches PacketTab.tsx lines 387-498) */}
                    <div className="bg-[#161b22] border border-[#30363d] rounded-xl p-3.5 space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-semibold text-[#d29922]">
                          Assumptions &amp; Traveler Prompts
                        </span>
                        <span className="rounded bg-[#f85149]/15 px-1.5 py-0.5 text-[10px] font-medium uppercase text-[#f85149]">
                          {isDatesConfirmed ? "Reviewed" : "Critical"}
                        </span>
                      </div>
                      <p className="text-xs text-[#e6edf3]">
                        ~ Travel Dates ={" "}
                        {isDatesConfirmed
                          ? datesConfirmedClean
                          : fixture.rows[3]?.fact.value}
                      </p>
                      <p className="text-[11px] text-[#8b949e]">
                        Prompt:{" "}
                        {datesRow?.fact.advisorFollowUp ??
                          "Confirm exact travel dates with the customer before locking supplier rates."}
                      </p>
                    </div>
                  </div>
                ) : activeWorkbenchTab === "channels" ? (
                  /* TAB 3: LEAD INBOX CHANNEL THREAD */
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {fixture.chatThread.map((msg, idx) => (
                      <div
                        key={msg.id}
                        className="rounded-xl bg-[#161b22] border border-[#30363d] p-3.5 space-y-2 flex flex-col justify-between"
                      >
                        <div>
                          <div className="flex items-center justify-between text-[10px] font-mono text-[#8b949e] mb-1.5">
                            <span>Inbound WhatsApp · Msg 0{idx + 1}</span>
                            <span className="text-[#3fb950]">
                              Linked to Trip Details
                            </span>
                          </div>
                          <p className="text-xs text-[#e6edf3] leading-relaxed">
                            {msg.segments.map((s, sIdx) => (
                              <span
                                key={sIdx}
                                className={
                                  s.highlight
                                    ? "rounded bg-[#58a6ff]/20 border border-[#58a6ff]/40 px-1 py-0.5 font-semibold text-[#93c5fd]"
                                    : ""
                                }
                              >
                                {s.text}
                              </span>
                            ))}
                          </p>
                        </div>
                        <div className="pt-2 border-t border-[#30363d] flex items-center justify-between text-[10px] text-[#8b949e]">
                          <span>Source Authority: explicit_user</span>
                          <span className="text-[#58a6ff]">
                            ✓ Captured in Packet
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  /* TAB 4: DECISION & DESTINATION INTEL (Matches DecisionPanel.tsx + destination-intelligence) */
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div className="bg-[#161b22] border border-[#30363d] rounded-xl p-4 space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-semibold text-[#e6edf3]">
                          Decision State
                        </span>
                        <span
                          className={`rounded-full px-2.5 py-0.5 text-[10px] font-semibold ${
                            isDatesConfirmed
                              ? "bg-[#238636]/20 text-[#3fb950]"
                              : "bg-[#d29922]/20 text-[#d29922]"
                          }`}
                        >
                          {isDatesConfirmed
                            ? "Draft Quote (PROCEED_INTERNAL_DRAFT)"
                            : "Waiting on Customer (ASK_FOLLOWUP)"}
                        </span>
                      </div>
                      <p className="text-xs text-[#8b949e] leading-relaxed">
                        {isDatesConfirmed
                          ? `All required fields for ${fixture.pillTitle} are confirmed. Advisor can generate commercial quote versions.`
                          : `Waypoint holds quote generation until the customer confirms the exact ${fixture.pillTitle} date window.`}
                      </p>
                      <div className="space-y-1.5 pt-2 border-t border-[#30363d] text-xs">
                        <div className="flex justify-between text-[#c9d1d9]">
                          <span>Stay &amp; Boutique Properties</span>
                          <span className="font-mono text-[#3fb950]">
                            48% allocation
                          </span>
                        </div>
                        <div className="flex justify-between text-[#c9d1d9]">
                          <span>Private Transfers &amp; Rail</span>
                          <span className="font-mono text-[#58a6ff]">
                            22% allocation
                          </span>
                        </div>
                        <div className="flex justify-between text-[#c9d1d9]">
                          <span>Activities, Guides &amp; Dining</span>
                          <span className="font-mono text-[#d29922]">
                            30% allocation
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="bg-[#161b22] border border-[#30363d] rounded-xl p-4 space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-semibold text-[#e6edf3]">
                          Destination Intel ({fixture.pillTitle})
                        </span>
                        <span className="rounded bg-[#238636]/20 px-2 py-0.5 font-mono text-[10px] text-[#3fb950]">
                          Band 1 · Normal Precautions
                        </span>
                      </div>
                      <p className="text-xs text-[#8b949e] leading-relaxed">
                        Live FCDO travel safety advisory + ERA5 climate
                        suitability baseline for{" "}
                        <strong className="text-[#e6edf3]">
                          {fixture.pillTitle}
                        </strong>{" "}
                        ({fixture.rows[2]?.fact.value},{" "}
                        {fixture.rows[4]?.fact.value}).
                      </p>
                      <div className="pt-2 border-t border-[#30363d] flex items-center justify-between">
                        <span className="font-mono text-[10px] text-[#8b949e]">
                          Source: FCDO + Open-Meteo ERA5
                        </span>
                        <Link
                          href={workbenchCaseHref}
                          className="text-xs font-semibold text-[#58a6ff] hover:underline"
                        >
                          Open in Workbench →
                        </Link>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* =====================================================================
          FOLD 3: CORE WAYPOINT OS MODULES IN ACTION (#why-waypoint)
         ===================================================================== */}
      <section
        id="why-waypoint"
        className="relative py-20 sm:py-28 px-6 sm:px-12 border-t border-white/10 bg-[#020a21]"
      >
        <div className="max-w-[1440px] mx-auto space-y-10">
          {/* Section Header — Honest Agency Workflow Copy (Zero "Flight Ops" Jargon) */}
          <div className="flex flex-col xl:flex-row xl:items-end justify-between gap-6">
            <div className="max-w-2xl space-y-3">
              <div className="inline-flex items-center gap-2 rounded-full bg-white/[0.06] border border-white/15 px-3.5 py-1 font-mono text-[10.5px] uppercase tracking-[0.2em] text-[#58a6ff]">
                <span>Why Agencies Run on Waypoint OS</span>
              </div>
              <h2 className="text-3xl sm:text-4xl lg:text-[42px] font-bold tracking-[-0.03em] text-white leading-[1.08]">
                Every detail traced to the customer. Every assumption caught
                before you quote.
              </h2>
            </div>

            {/* Interactive Hero Stage Sync Bar */}
            <div className="inline-flex flex-wrap sm:flex-nowrap items-center gap-2 rounded-xl bg-[#0d1117] border border-[#30363d] p-2 shrink-0">
              <span className="px-2 py-1 font-mono text-[10px] font-semibold uppercase tracking-wider text-[#8b949e] whitespace-nowrap">
                Preview on Hero Board:
              </span>
              <button
                type="button"
                onClick={() => {
                  onOpenStageOnHero("voice_ingest");
                  window.scrollTo({ top: 0, behavior: "smooth" });
                }}
                className="rounded-lg bg-[#161b22] hover:bg-[#21262d] border border-[#30363d] px-3 py-1.5 text-xs font-medium text-[#58a6ff] whitespace-nowrap transition-all"
              >
                1 · Voice &amp; Message Capture
              </button>
              <button
                type="button"
                onClick={() => {
                  onOpenStageOnHero("provenance_brief");
                  onSelectRow("dates");
                  window.scrollTo({ top: 0, behavior: "smooth" });
                }}
                className="rounded-lg bg-[#d29922]/20 hover:bg-[#d29922]/30 border border-[#d29922]/40 px-3 py-1.5 text-xs font-semibold text-[#fde047] whitespace-nowrap transition-all"
              >
                2 · Missing-Date Hold
              </button>
              <button
                type="button"
                onClick={() => {
                  if (!isDatesConfirmed) onToggleDatesConfirmed();
                  onOpenStageOnHero("provenance_brief");
                  onSelectRow("destination");
                  window.scrollTo({ top: 0, behavior: "smooth" });
                }}
                className="rounded-lg bg-[#238636]/20 hover:bg-[#238636]/30 border border-[#3fb950]/40 px-3 py-1.5 text-xs font-medium text-[#3fb950] whitespace-nowrap transition-all"
              >
                3 · Quote-Ready Brief
              </button>
            </div>
          </div>

          {/* 3-CARD BENTO GRID MAPPED TO REAL WAYPOINT OS MODULES */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 xl:gap-8">
            {/* BENTO CARD 1 (7 Cols): Trip Details (`PacketTab`) · Extracted Information & Source Provenance */}
            <div className="lg:col-span-7 rounded-2xl bg-[#0d1117] border border-[#30363d] p-6 sm:p-8 flex flex-col justify-between space-y-6 shadow-[0_24px_60px_rgba(0,0,0,0.5)]">
              <div className="space-y-2.5">
                <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#30363d] pb-3">
                  <span className="font-mono text-xs font-bold uppercase tracking-wider text-[#58a6ff]">
                    Trip Details · Extracted Information &amp; Authority
                  </span>
                  <span className="inline-flex items-center gap-1.5 rounded-full bg-[#161b22] border border-[#30363d] px-3 py-0.5 font-mono text-[10px] font-semibold text-[#c9d1d9]">
                    <span className="h-2 w-2 rounded-full bg-[#3fb950]" />
                    {fixture.pillTitle} · Source Provenance
                  </span>
                </div>
                <h3 className="text-2xl font-bold text-[#e6edf3] tracking-tight">
                  See exactly which message produced every field in the brief
                </h3>
                <p className="text-sm text-[#8b949e] leading-relaxed">
                  In Waypoint OS, every extracted field in{" "}
                  <strong className="text-[#c9d1d9]">Trip Details</strong> carries
                  its confidence score, authority level (
                  <code className="text-[#58a6ff]">explicit_user</code> vs.{" "}
                  <code className="text-[#d29922]">derived_signal</code>), and
                  the exact sentence the traveler sent.
                </p>
              </div>

              {/* Interactive 5-Field Inspector */}
              <div className="grid grid-cols-1 sm:grid-cols-12 gap-3 items-stretch rounded-xl bg-[#161b22] border border-[#30363d] p-4">
                <div className="sm:col-span-5 space-y-1.5">
                  <span className="block font-mono text-[10px] font-semibold uppercase tracking-wider text-[#8b949e] mb-2">
                    Select Extracted Field:
                  </span>
                  {fixture.rows.map((row, idx) => {
                    const isSelected = activeBentoRow.id === row.id;
                    const isHold = row.id === "dates" && !isDatesConfirmed;
                    return (
                      <button
                        key={row.id}
                        type="button"
                        onClick={() => {
                          splitFlapAudio.playFlapClack(idx * 2, true);
                          setActiveBentoRowId(row.id);
                        }}
                        className={`w-full flex items-center justify-between rounded-lg px-3 py-2 text-left text-xs transition-all ${
                          isSelected
                            ? "bg-[#58a6ff] text-[#0d1117] font-bold"
                            : "bg-[#0d1117] text-[#c9d1d9] hover:bg-[#21262d] border border-[#30363d]"
                        }`}
                        data-testid={`fold3-trace-slot-${row.id}`}
                      >
                        <span className="truncate">{row.label}</span>
                        <span
                          className={`ml-2 shrink-0 rounded px-1.5 py-0.5 font-mono text-[9.5px] font-semibold ${
                            isSelected
                              ? "bg-[#0d1117]/15 text-[#0d1117]"
                              : isHold
                              ? "bg-[#d29922]/20 text-[#d29922]"
                              : "bg-[#238636]/20 text-[#3fb950]"
                          }`}
                        >
                          {row.fact.value}
                        </span>
                      </button>
                    );
                  })}
                </div>

                {/* Connected Customer Quote & Authority Card */}
                <div className="sm:col-span-7 rounded-xl bg-[#0d1117] border border-[#30363d] p-4 flex flex-col justify-between space-y-3">
                  <div className="space-y-2.5">
                    <div className="flex flex-wrap items-center justify-between gap-1.5">
                      <span className="font-mono text-[10px] font-bold uppercase tracking-wider text-[#58a6ff]">
                        Source ({SLOT_CHANNEL_LABELS[activeBentoRow.id]})
                      </span>
                      <span className="rounded bg-[#161b22] px-2 py-0.5 font-mono text-[10px] font-semibold text-[#3fb950] border border-[#30363d]">
                        {SLOT_AUTHORITY_META[activeBentoRow.id].authority} ·{" "}
                        {SLOT_AUTHORITY_META[activeBentoRow.id].confidence}
                      </span>
                    </div>

                    <div className="rounded-lg bg-[#161b22] text-[#e6edf3] p-3.5 text-xs sm:text-sm border border-[#30363d] leading-relaxed">
                      &ldquo;
                      {activeBentoRow.fact.evidenceQuote ||
                        fixture.voiceNote.quote.replace(/^[“"]|[”"]$/g, "")}
                      &rdquo;
                    </div>
                  </div>

                  <div className="space-y-1.5 pt-2 border-t border-[#30363d] text-xs">
                    <div className="flex items-center justify-between font-mono text-[10px]">
                      <span className="text-[#8b949e]">EXTRACTION BASIS:</span>
                      <span className="font-bold uppercase text-[#e6edf3]">
                        {activeBentoRow.fact.basis}
                      </span>
                    </div>
                    <p className="text-[#8b949e] text-xs leading-relaxed">
                      <strong className="text-[#c9d1d9]">
                        Suggested Traveler Prompt:
                      </strong>{" "}
                      {activeBentoRow.fact.advisorFollowUp ||
                        SLOT_FOLLOW_UP_FALLBACKS[activeBentoRow.id]}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* BENTO CARD 2 (5 Cols): Quote Review & Assumptions Gate */}
            <div className="lg:col-span-5 rounded-2xl bg-[#0d1117] border border-[#30363d] p-6 sm:p-8 flex flex-col justify-between space-y-5 shadow-[0_24px_60px_rgba(0,0,0,0.5)]">
              <div className="space-y-2.5">
                <div className="flex items-center justify-between border-b border-[#30363d] pb-3">
                  <span className="font-mono text-xs font-bold uppercase tracking-wider text-[#d29922]">
                    Assumptions &amp; Missing-Field Gate
                  </span>
                  <span className="inline-flex items-center gap-1.5 rounded-full bg-[#d29922]/15 border border-[#d29922]/40 px-2.5 py-0.5 font-mono text-[10px] font-bold text-[#d29922]">
                    {isDatesConfirmed ? "Dates Confirmed" : "Waiting on Customer"}
                  </span>
                </div>
                <h3 className="text-2xl font-bold text-[#e6edf3] tracking-tight">
                  Zero hallucinated dates or budgets
                </h3>
                <p className="text-sm text-[#8b949e] leading-relaxed">
                  When a client says &ldquo;around June next year&rdquo; or
                  &ldquo;dates flexible,&rdquo; Waypoint flags{" "}
                  <strong className="text-[#e6edf3]">Travel Dates</strong> in the{" "}
                  <strong className="text-[#d29922]">Assumptions</strong>{" "}
                  register and holds quote generation until confirmed.
                </p>
              </div>

              {/* Traveler Follow-up Prompt Card */}
              <div className="rounded-xl bg-[#161b22] border border-[#30363d] p-3.5 space-y-1">
                <div className="flex items-center justify-between font-mono text-[10px] uppercase tracking-wider text-[#d29922]">
                  <span>AUTO-DRAFTED CLIENT QUESTION</span>
                  <span>{fixture.pillTitle}</span>
                </div>
                <p className="text-xs sm:text-sm text-[#e6edf3] font-medium leading-snug">
                  &ldquo;
                  {datesRow?.fact.advisorFollowUp ??
                    `Confirm exact ${fixture.pillTitle} departure window before locking inventory.`}
                  &rdquo;
                </p>
              </div>

              {/* Synchronized Travel Dates Status Strip */}
              <div className="rounded-xl bg-[#161b22] border border-[#30363d] p-4 space-y-3">
                <div className="flex items-center justify-between font-mono text-[10px]">
                  <span className="text-[#8b949e]">
                    TRAVEL DATES STATUS ({fixture.pillTitle.toUpperCase()})
                  </span>
                  <span
                    className={
                      isDatesConfirmed
                        ? "text-[#3fb950] font-bold"
                        : "text-[#d29922] font-bold"
                    }
                  >
                    {isDatesConfirmed
                      ? "✓ CONFIRMED BY ADVISOR"
                      : "⚠️ UNCONFIRMED ASSUMPTION"}
                  </span>
                </div>

                {!isDatesConfirmed ? (
                  <div className="grid grid-cols-8 gap-1">
                    {NEED_CONFIRMATION_CELLS.map((cell, idx) => (
                      <div
                        key={idx}
                        className="relative flex flex-col items-center justify-center h-11 rounded bg-[#f5c418] text-slate-950 font-mono font-black"
                      >
                        <span className="text-[10.5px] leading-none">
                          {cell.top.trim() || "\u00A0"}
                        </span>
                        <span className="text-[9.5px] leading-none mt-1">
                          {cell.bottom.trim() || "\u00A0"}
                        </span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="grid grid-cols-11 gap-1">
                    {datesConfirmedClean
                      .slice(0, 11)
                      .padEnd(11, " ")
                      .split("")
                      .map((ch, idx) => (
                        <span
                          key={`${ch}-${idx}`}
                          className="flex h-11 items-center justify-center rounded bg-[#238636]/20 border border-[#3fb950]/40 text-[#3fb950] font-mono text-xs font-bold"
                        >
                          {ch}
                        </span>
                      ))}
                  </div>
                )}

                <div className="pt-1 flex items-center justify-between gap-2">
                  <span className="font-mono text-[10px] text-[#8b949e]">
                    {isDatesConfirmed
                      ? `Confirmed: ${fixture.rows[3]?.confirmedValueLabel}`
                      : "Blocked from quoting until confirmed"}
                  </span>
                  <button
                    type="button"
                    onClick={onToggleDatesConfirmed}
                    className="rounded-lg bg-[#58a6ff] hover:bg-[#6eb5ff] text-[#0d1117] px-3.5 py-1.5 text-xs font-semibold transition-all"
                    data-testid="fold3-latch-toggle"
                  >
                    {isDatesConfirmed ? "Reset Hold" : "Confirm Dates →"}
                  </button>
                </div>
              </div>
            </div>

            {/* BENTO CARD 3 (12 Cols): Lead Inbox & Trips in Planning Queue */}
            <div className="lg:col-span-12 rounded-2xl bg-[#0d1117] border border-[#30363d] p-6 sm:p-8 grid grid-cols-1 lg:grid-cols-12 gap-8 items-center shadow-[0_28px_70px_rgba(0,0,0,0.55)]">
              <div className="lg:col-span-5 space-y-4">
                <div className="flex items-center justify-between border-b border-[#30363d] pb-3">
                  <span className="font-mono text-xs font-bold uppercase tracking-wider text-[#3fb950]">
                    Lead Inbox → Trips in Planning
                  </span>
                  <span className="inline-flex items-center gap-1.5 rounded-full bg-[#238636]/15 border border-[#3fb950]/35 px-2.5 py-0.5 font-mono text-[10px] font-bold text-[#3fb950]">
                    {fixture.pillTitle} Active
                  </span>
                </div>

                <h3 className="text-2xl sm:text-3xl font-bold text-[#e6edf3] tracking-tight leading-tight">
                  One-click handoff from intake brief to full trip planning
                </h3>

                <p className="text-sm sm:text-base text-[#8b949e] leading-relaxed">
                  Switch between active client inquiries in your{" "}
                  <strong className="text-[#c9d1d9]">Lead Inbox</strong> or promote
                  a verified brief straight into{" "}
                  <strong className="text-[#c9d1d9]">Trips in Planning</strong>{" "}
                  with destination safety advisories, weather suitability, and
                  customer preferences attached.
                </p>

                <div className="pt-2 flex flex-wrap items-center gap-3">
                  <Link
                    href={workbenchCaseHref}
                    className="inline-flex items-center gap-2 rounded-lg bg-[#58a6ff] hover:bg-[#6eb5ff] text-[#0d1117] font-semibold text-xs sm:text-sm px-5 py-2.5 transition-all"
                  >
                    <span>Open {fixture.pillTitle} in Workbench</span>
                    <span>→</span>
                  </Link>
                  <Link
                    href="/itinerary-checker"
                    className="rounded-lg bg-[#161b22] hover:bg-[#21262d] border border-[#30363d] px-4 py-2.5 text-xs font-medium text-[#e6edf3] transition-all"
                  >
                    Try Free Itinerary Checker
                  </Link>
                </div>
              </div>

              {/* Right 7 Cols: 6 Active Client Inquiries in Trips in Planning */}
              <div className="lg:col-span-7 space-y-3">
                <div className="flex items-center justify-between font-mono text-[10px] text-[#8b949e]">
                  <span>
                    TRIPS IN PLANNING · CLICK ANY INQUIRY TO PREVIEW IN WORKBENCH
                  </span>
                  <span className="text-[#58a6ff]">15 DESTINATION TEMPLATES</span>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                  {DESTINATION_CATALOG_REGISTRY.slice(0, 6).map((entry) => {
                    const isCurrent =
                      fixture.pillTitle.toLowerCase() ===
                      entry.displayName.toLowerCase();
                    return (
                      <button
                        key={entry.slug}
                        type="button"
                        onClick={() =>
                          handleDestinationSelect(entry.slug, entry.displayName)
                        }
                        className={`group relative rounded-xl overflow-hidden border text-left transition-all ${
                          isCurrent
                            ? "border-[#58a6ff] ring-2 ring-[#58a6ff]/50"
                            : "border-[#30363d] hover:border-[#8b949e]"
                        }`}
                        data-testid={`fold3-gallery-card-${entry.slug}`}
                      >
                        <div className="relative h-28 w-full bg-slate-950 overflow-hidden">
                          <img
                            src={entry.destinationPhotoUrl}
                            alt={entry.displayName}
                            className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
                          />
                          <div className="absolute inset-0 bg-gradient-to-t from-[#0d1117] via-[#0d1117]/35 to-transparent" />
                          <span className="absolute top-2 right-2 rounded bg-[#161b22]/90 border border-[#30363d] text-[#e6edf3] px-1.5 py-0.5 font-mono text-[9.5px] font-bold">
                            {entry.iataCode}
                          </span>
                          <div className="absolute bottom-2 left-2.5 right-2.5">
                            <p className="font-bold text-white text-sm leading-tight">
                              {entry.displayName}
                            </p>
                            <p className="font-mono text-[9.5px] text-[#93c5fd] truncate">
                              {entry.defaultDurationDays}d ·{" "}
                              {entry.defaultTravelersCount} pax ·{" "}
                              {entry.defaultStyleLabel}
                            </p>
                          </div>
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* =====================================================================
          FOLD 4: PRICING & WORKSPACE ACCESS (#pricing)
         ===================================================================== */}
      <section
        id="pricing"
        className="relative py-20 sm:py-28 px-6 sm:px-12 border-t border-white/10 bg-[#041030]"
      >
        <div className="max-w-[1440px] mx-auto space-y-12">
          <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-6">
            <div className="max-w-2xl space-y-3">
              <div className="inline-flex items-center gap-2 rounded-full bg-[#58a6ff]/15 border border-[#58a6ff]/40 px-3.5 py-1 font-mono text-[10.5px] uppercase tracking-[0.2em] text-[#93c5fd]">
                <span>Pricing &amp; Workspace Access</span>
              </div>
              <h2 className="text-3xl sm:text-4xl font-bold tracking-[-0.03em] text-white leading-tight">
                Start with the workflow that fits your agency today.
              </h2>
            </div>
            <p className="text-sm sm:text-base text-slate-300 max-w-md leading-relaxed">
              Self-serve workspace creation is live right now and carries your
              active{" "}
              <strong className="text-[#fde047]">{fixture.pillTitle}</strong>{" "}
              inquiry directly into your new Workbench.
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 xl:gap-8 items-stretch">
            {/* Tier 1: Free Public Checker (4 cols) */}
            <div className="lg:col-span-4 rounded-2xl bg-[#0d1117] border border-[#30363d] p-6 sm:p-7 flex flex-col justify-between space-y-6">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-[10.5px] font-bold uppercase tracking-widest text-[#58a6ff]">
                    01 · Public Tool
                  </span>
                  <span className="rounded bg-[#161b22] border border-[#30363d] px-2.5 py-0.5 font-mono text-[10px] font-semibold text-[#c9d1d9]">
                    FREE
                  </span>
                </div>
                <div>
                  <h3 className="text-2xl font-bold text-[#e6edf3]">
                    Free Itinerary Checker
                  </h3>
                  <p className="text-xs font-mono uppercase tracking-wider text-[#8b949e] mt-1">
                    No sign-up required · Instant review
                  </p>
                </div>
                <p className="text-sm text-[#8b949e] leading-relaxed">
                  Paste, upload, or screenshot a draft trip plan to check
                  pacing, transfer realism, and seasonal weather suitability.
                </p>
                <ul className="space-y-2 text-xs sm:text-sm text-[#c9d1d9] pt-2 border-t border-[#30363d]">
                  <li className="flex items-center gap-2">
                    <span className="text-[#3fb950] font-bold">✓</span>
                    <span>Upload PDF, screenshot, or pasted draft</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="text-[#3fb950] font-bold">✓</span>
                    <span>Live Open-Meteo climate &amp; pacing checks</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="text-[#3fb950] font-bold">✓</span>
                    <span>Surfaces missing details before agency intake</span>
                  </li>
                </ul>
              </div>

              <Link
                href="/itinerary-checker"
                className="w-full inline-flex items-center justify-center gap-2 rounded-lg bg-[#161b22] hover:bg-[#21262d] border border-[#30363d] text-[#e6edf3] font-semibold text-sm py-3 px-5 transition-all"
              >
                <span>Try the Public Checker</span>
                <span aria-hidden="true">→</span>
              </Link>
            </div>

            {/* Tier 2: B2B Agency Workspace (5 cols) */}
            <div className="lg:col-span-5 rounded-2xl bg-[#0d1117] border-2 border-[#58a6ff] p-6 sm:p-8 flex flex-col justify-between space-y-6 shadow-[0_24px_60px_rgba(88,166,255,0.18)]">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-[10.5px] font-bold uppercase tracking-widest text-[#58a6ff]">
                    02 · Agency Workspace
                  </span>
                  <span className="rounded-full bg-[#58a6ff] text-[#0d1117] px-3 py-0.5 font-mono text-[10px] font-bold uppercase tracking-wider">
                    Recommended
                  </span>
                </div>
                <div>
                  <h3 className="text-2xl sm:text-3xl font-bold text-[#e6edf3]">
                    Self-Serve Workspace
                  </h3>
                  <p className="text-xs font-mono uppercase tracking-wider text-[#58a6ff] mt-1">
                    Pre-loaded with your {fixture.pillTitle} inquiry
                  </p>
                </div>
                <p className="text-sm text-[#c9d1d9] leading-relaxed">
                  The full Waypoint OS workbench for travel advisors: Lead Inbox,
                  New Inquiry capture, Trip Details validation, Quote Review,
                  and Destination Intel.
                </p>
                <ul className="space-y-2 text-xs sm:text-sm text-[#e6edf3] pt-2 border-t border-[#30363d]">
                  <li className="flex items-center gap-2">
                    <span className="text-[#3fb950] font-bold">✓</span>
                    <span>
                      Extracted Information table with source authority &amp;
                      confidence
                    </span>
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="text-[#3fb950] font-bold">✓</span>
                    <span>
                      Assumptions &amp; Unknowns gate prevents quoting on
                      unconfirmed dates
                    </span>
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="text-[#3fb950] font-bold">✓</span>
                    <span>
                      Private Agent Notes kept separate from client-facing
                      proposals
                    </span>
                  </li>
                </ul>
              </div>

              <div className="space-y-2">
                <Link
                  href="/signup"
                  onClick={persistHandoffSession}
                  className="w-full inline-flex items-center justify-center gap-2 rounded-lg bg-[#58a6ff] hover:bg-[#6eb5ff] text-[#0d1117] font-bold text-sm py-3 px-6 transition-all"
                >
                  <span>Create workspace</span>
                  <span aria-hidden="true">→</span>
                </Link>
                <p className="text-center font-mono text-[10px] text-[#8b949e]">
                  Carries {fixture.pillTitle} · {fixture.rows[1]?.fact.value} ·{" "}
                  {fixture.rows[2]?.fact.value} into your new workspace
                </p>
              </div>
            </div>

            {/* Tier 3: Guided Team Setup (3 cols) */}
            <div className="lg:col-span-3 rounded-2xl bg-[#0d1117] border border-[#30363d] p-6 sm:p-7 flex flex-col justify-between space-y-6">
              <div className="space-y-4">
                <span className="font-mono text-[10.5px] font-bold uppercase tracking-widest text-[#3fb950]">
                  03 · Multi-Advisor Team
                </span>
                <div>
                  <h3 className="text-xl font-bold text-[#e6edf3]">
                    Guided Team Setup
                  </h3>
                  <p className="text-xs font-mono uppercase tracking-wider text-[#8b949e] mt-1">
                    Multi-advisor agencies
                  </p>
                </div>
                <p className="text-sm text-[#8b949e] leading-relaxed">
                  For agencies that want shared Lead Inbox routing, owner Quote
                  Review approval rules, and custom supplier playbooks in
                  Knowledge Base.
                </p>
                <ul className="space-y-2 text-xs text-[#c9d1d9] pt-2 border-t border-[#30363d]">
                  <li className="flex items-center gap-2">
                    <span className="text-[#3fb950] font-bold">✓</span>
                    <span>Shared Lead Inbox &amp; Quote Review gates</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="text-[#3fb950] font-bold">✓</span>
                    <span>Full pricing details &amp; FAQ on dedicated page</span>
                  </li>
                </ul>
              </div>

              <Link
                href="/pricing"
                className="w-full inline-flex items-center justify-center gap-2 rounded-lg bg-[#161b22] hover:bg-[#21262d] border border-[#30363d] text-[#e6edf3] font-semibold text-xs sm:text-sm py-3 px-4 transition-all"
              >
                <span>Full Pricing &amp; FAQ →</span>
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* =====================================================================
          FOOTER
         ===================================================================== */}
      <footer className="py-14 px-6 sm:px-12 border-t border-white/10 bg-[#02081c]">
        <div className="max-w-[1440px] mx-auto flex flex-col sm:flex-row items-start sm:items-center justify-between gap-8">
          <div className="space-y-1.5">
            <div className="flex items-center gap-2.5">
              <span className="inline-flex h-2.5 w-2.5 rounded-full bg-[#58a6ff]" />
              <p className="font-mono text-sm font-black tracking-[0.2em] text-white uppercase">
                WAYPOINT OS · AGENCY WORKSPACE
              </p>
            </div>
            <p className="text-sm text-slate-400">
              Turn messy travel inquiries into verified, quote-ready trip briefs.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <Link
              href="/signup"
              onClick={persistHandoffSession}
              className="inline-flex items-center gap-2 rounded-full bg-[#f5c418] hover:bg-[#fde047] text-slate-950 font-semibold text-sm px-6 py-2.5 transition-all"
            >
              <span>Create workspace</span>
              <span aria-hidden="true">→</span>
            </Link>
            <Link
              href={workbenchCaseHref}
              className="inline-flex items-center gap-2 rounded-full bg-[#161b22] hover:bg-[#21262d] border border-[#30363d] text-[#e6edf3] font-semibold text-sm px-5 py-2.5 transition-all"
            >
              <span>Advisor Workbench</span>
            </Link>
            <Link
              href="/itinerary-checker"
              className="inline-flex items-center gap-2 rounded-full bg-[#161b22] hover:bg-[#21262d] border border-[#30363d] text-[#e6edf3] font-semibold text-sm px-5 py-2.5 transition-all"
            >
              <span>Free Itinerary Checker</span>
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
};
