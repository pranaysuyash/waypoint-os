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
  dates: "WhatsApp Msg 03 · Epistemic Gate",
  tripStyle: "WhatsApp Msg 02 + Msg 04",
};

const SLOT_FOLLOW_UP_FALLBACKS: Record<BoardRowId, string> = {
  destination:
    "Verify preferred entry/exit gateway airports and internal rail or private transfer routing.",
  travelers:
    "Confirm rooming configuration (suite split vs. interconnecting rooms) and passenger ages.",
  duration:
    "Validate pacing across hubs so no single transfer day exceeds client comfort thresholds.",
  dates:
    "Hold supplier quotes until the traveler locks an exact departure and return window.",
  tripStyle:
    "Match tier-1 boutique property inventory and private guide allocation to stated style.",
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
  const [activeChannelTab, setActiveChannelTab] = useState<
    "voice" | "whatsapp" | "email"
  >("voice");
  const [activeGateStep, setActiveGateStep] = useState<number>(1);
  const [foldCustomQuery, setFoldCustomQuery] = useState<string>("");
  const [activeBentoRowId, setActiveBentoRowId] =
    useState<BoardRowId>("dates");

  const persistHandoffSession = () => {
    try {
      window.sessionStorage.setItem(
        "waypoint_departure_board_handoff",
        JSON.stringify({
          source: "departure-board",
          caseSlug: activeCaseSlug,
          caseTitle: fixture.pillTitle,
          iataCode: fixture.tagCode,
          prefill: fixture.voiceNote.quote.replace(/^[“"]|[”"]$/g, ""),
        })
      );
    } catch {
      // non-blocking
    }
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

  return (
    <div className="relative bg-[#030d29] text-white overflow-hidden">
      {/* =====================================================================
          ARCHITECTURAL TRANSITION LEDGE: HERO MONUMENT -> FOLD 2
         ===================================================================== */}
      <div className="relative border-t border-b border-white/10 bg-[#051339]/90 py-4 px-6 sm:px-12">
        <div className="max-w-[1440px] mx-auto flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <span className="inline-flex h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="font-mono text-[11px] font-bold uppercase tracking-[0.2em] text-slate-300">
              LIVE TELEMETRY SYNCHRONIZED ACROSS ALL FOLDS
            </span>
          </div>
          <div className="flex flex-wrap items-center gap-4 font-mono text-[11px]">
            <span className="text-slate-400">
              ACTIVE DESK CASE:{" "}
              <strong className="text-white">
                {fixture.pillTitle.toUpperCase()}
              </strong>
            </span>
            <span className="text-slate-600">/</span>
            <span className="text-slate-400">
              IATA: <strong className="text-[#fde047]">{fixture.tagCode}</strong>
            </span>
            <span className="text-slate-600">/</span>
            <span className="text-slate-400">
              PARTY:{" "}
              <strong className="text-white">
                {fixture.rows[1]?.fact.value}
              </strong>
            </span>
            <span className="text-slate-600">/</span>
            <span className="text-slate-400">
              DURATION:{" "}
              <strong className="text-white">
                {fixture.rows[2]?.fact.value}
              </strong>
            </span>
            <span className="text-slate-600">/</span>
            <span
              className={
                isDatesConfirmed
                  ? "text-emerald-300 font-bold"
                  : "text-[#fde047] font-bold"
              }
            >
              {isDatesConfirmed
                ? `DATES LOCKED (${datesResolvedString})`
                : "ROW 04: EPISTEMIC HOLD"}
            </span>
          </div>
        </div>
      </div>

      {/* =====================================================================
          FOLD 2: INTERACTIVE INTAKE & MECHANICAL SPLIT-FLAP WORKBENCH (#product)
         ===================================================================== */}
      <section
        id="product"
        className="relative py-24 sm:py-32 px-6 sm:px-12 max-w-[1440px] mx-auto"
      >
        {/* Ambient Terminal Lighting */}
        <div
          aria-hidden="true"
          className="pointer-events-none absolute inset-0 opacity-30"
          style={{
            backgroundImage:
              "radial-gradient(circle at 14% 22%, rgba(245,196,24,0.16), transparent 42%), radial-gradient(circle at 84% 62%, rgba(56,189,248,0.16), transparent 48%)",
          }}
        />

        <div className="relative z-10 grid grid-cols-1 lg:grid-cols-12 gap-10 xl:gap-12 items-start">
          {/* LEFT COLUMN (5 cols): Editorial Narrative + Physical Destination Pass Wallet + Live NLU Compiler */}
          <div className="lg:col-span-5 space-y-7">
            <div className="inline-flex items-center gap-2.5 rounded-full bg-[#09215c] border border-[#f5c418]/45 px-4 py-1.5 text-[10.5px] font-mono uppercase tracking-[0.22em] text-[#fde047] shadow-[0_8px_24px_rgba(0,0,0,0.35)]">
              <span className="h-2 w-2 rounded-full bg-[#f5c418] animate-pulse" />
              <span>Waypoint OS · Intake & Epistemic Gate</span>
            </div>

            <h2 className="text-3xl sm:text-4xl lg:text-[44px] font-bold tracking-[-0.03em] text-white leading-[1.06]">
              Turn raw trip notes into quote-ready briefs
            </h2>

            <p className="text-base sm:text-[17px] text-slate-200/90 leading-relaxed">
              Waypoint helps boutique travel agencies turn the notes they already
              have, whether from calls, emails, WhatsApp messages, or copied
              itineraries, into structured trip briefs ready for advisor review.
            </p>

            {/* DOUBLE-BEZEL PHYSICAL DESTINATION FLIGHT DOSSIER CARD */}
            <div className="rounded-[28px] bg-gradient-to-b from-white/20 via-white/8 to-white/5 p-1.5 shadow-[0_24px_60px_rgba(0,0,0,0.5)]">
              <div className="rounded-[22px] bg-[#061640] border border-white/12 p-5 space-y-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.15)]">
                {/* Top Header Bar: Non-wrapping status & IATA badge */}
                <div className="flex flex-wrap items-center justify-between gap-2 border-b border-white/10 pb-3.5">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-[10px] font-extrabold uppercase tracking-[0.16em] text-slate-300">
                      ACTIVE FLIGHT DOSSIER
                    </span>
                    <span className="rounded-md bg-[#f5c418]/15 border border-[#f5c418]/40 px-2 py-0.5 font-mono text-[10px] font-black text-[#fde047]">
                      IATA · {fixture.tagCode}
                    </span>
                  </div>

                  <button
                    type="button"
                    onClick={onToggleAutoCycle}
                    className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 font-mono text-[10px] font-extrabold whitespace-nowrap transition-all ${
                      isAutoCycling
                        ? "bg-emerald-400/15 text-emerald-300 border border-emerald-400/40"
                        : "bg-amber-400/15 text-amber-300 border border-amber-400/40"
                    }`}
                    data-testid="fold2-auto-stream-toggle"
                  >
                    <span
                      className={`h-1.5 w-1.5 rounded-full shrink-0 ${
                        isAutoCycling
                          ? "bg-emerald-400 animate-pulse"
                          : "bg-amber-400"
                      }`}
                    />
                    <span>
                      {isAutoCycling ? "Auto-Stream: ON" : "Auto-Stream: PAUSED"}
                    </span>
                  </button>
                </div>

                {/* Visual Destination Dual-Plate Card + Cream Luggage Tag Stamp */}
                <div className="grid grid-cols-12 gap-3 items-stretch">
                  <div className="col-span-7 relative rounded-2xl overflow-hidden border border-white/15 min-h-[126px] bg-slate-950 group">
                    <img
                      src={primaryPhotoSrc}
                      alt={`${fixture.pillTitle} primary plate`}
                      className="h-full w-full object-cover transition-transform duration-700 ease-[cubic-bezier(0.32,0.72,0,1)] group-hover:scale-105"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-slate-950/90 via-slate-950/25 to-transparent" />
                    <div className="absolute top-2.5 left-2.5 inline-flex items-center gap-1.5 rounded-md bg-slate-950/80 backdrop-blur-md border border-white/20 px-2 py-0.5 font-mono text-[9.5px] font-bold uppercase tracking-wider text-white">
                      <span>PLATE 01</span>
                      <span className="text-[#fde047]">· {fixture.tagCode}</span>
                    </div>
                    <div className="absolute bottom-2.5 left-2.5 right-2.5 flex items-end justify-between gap-2">
                      <div>
                        <p className="font-mono text-[9px] uppercase tracking-[0.16em] text-amber-300">
                          {fixture.rows[4]?.fact.value}
                        </p>
                        <p className="text-lg font-extrabold tracking-tight text-white leading-none mt-0.5">
                          {fixture.pillTitle}
                        </p>
                      </div>
                      <span className="rounded-lg bg-[#f4efe6] text-slate-950 border border-amber-900/20 px-2 py-1 font-mono text-xs font-black tracking-wider shadow">
                        {fixture.tagCode}
                      </span>
                    </div>
                  </div>

                  <div className="col-span-5 flex flex-col justify-between gap-2.5">
                    <div className="relative rounded-2xl overflow-hidden border border-white/15 h-[72px] bg-slate-950">
                      <img
                        src={secondaryPhotoSrc}
                        alt={`${fixture.pillTitle} secondary plate`}
                        className="h-full w-full object-cover"
                      />
                      <div className="absolute inset-0 bg-gradient-to-t from-slate-950/85 via-transparent to-transparent" />
                      <span className="absolute bottom-1.5 left-2 font-mono text-[9.5px] font-bold text-white">
                        {fixture.rows[2]?.fact.value} ·{" "}
                        {fixture.rows[1]?.fact.value}
                      </span>
                    </div>

                    <div className="rounded-xl bg-[#f4efe6] text-slate-950 px-3 py-2 border border-amber-900/20 shadow-inner flex items-center justify-between">
                      <div>
                        <span className="block font-mono text-[8.5px] font-bold uppercase tracking-widest text-slate-500">
                          SOLARI TAG
                        </span>
                        <span className="font-mono text-xs font-black tracking-tight text-slate-900">
                          {fixture.pillSubtitle}
                        </span>
                      </div>
                      <span className="h-2.5 w-2.5 rounded-full bg-amber-600/30 border border-amber-800/40" />
                    </div>
                  </div>
                </div>

                {/* Interactive 15-Destination Switcher Matrix */}
                <div className="space-y-1.5">
                  <span className="block font-mono text-[9.5px] font-bold uppercase tracking-[0.16em] text-slate-400">
                    Click Any Destination to Flip Mechanical Drums Inline:
                  </span>
                  <div className="flex flex-wrap items-center gap-1.5">
                    {DESTINATION_CATALOG_REGISTRY.map((entry) => {
                      const isActive =
                        fixture.pillTitle.toLowerCase() ===
                        entry.displayName.toLowerCase();
                      return (
                        <button
                          key={entry.slug}
                          type="button"
                          onClick={() =>
                            handleDestinationSelect(
                              entry.slug,
                              entry.displayName
                            )
                          }
                          className={`inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-[11px] font-bold transition-all active:scale-[0.98] ${
                            isActive
                              ? "bg-[#f5c418] text-slate-950 shadow-[0_4px_14px_rgba(245,196,24,0.35)]"
                              : "bg-white/[0.06] text-white/85 hover:bg-white/14 border border-white/10"
                          }`}
                          data-testid={`fold2-switch-${entry.slug}`}
                        >
                          <span className="font-mono text-[9.5px] opacity-75">
                            {entry.iataCode}
                          </span>
                          <span>{entry.displayName}</span>
                        </button>
                      );
                    })}
                  </div>
                </div>

                {/* Inline Natural-Language Inquiry Compiler inside Fold 2 */}
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    if (!foldCustomQuery.trim()) return;
                    onApplyDynamicInquiry(foldCustomQuery.trim());
                  }}
                  className="pt-2 border-t border-white/10 flex items-center gap-2"
                >
                  <input
                    type="text"
                    value={foldCustomQuery}
                    onChange={(e) => setFoldCustomQuery(e.target.value)}
                    placeholder="Or type any inquiry: e.g. 4 travelers to Amalfi for 10 days in Sept..."
                    aria-label="Compile custom travel inquiry in Fold 2"
                    className="flex-1 rounded-xl bg-slate-950/90 border border-white/15 px-3 py-2 text-xs text-white placeholder:text-slate-400 focus:outline-none focus:border-[#f5c418]"
                    data-testid="fold2-custom-inquiry-input"
                  />
                  <button
                    type="submit"
                    className="rounded-xl bg-[#f5c418] hover:bg-[#fde047] text-slate-950 font-mono text-[10.5px] font-extrabold uppercase tracking-wider px-3.5 py-2 transition-all active:scale-[0.98] shrink-0"
                    data-testid="fold2-custom-inquiry-submit"
                  >
                    Compile →
                  </button>
                </form>
              </div>
            </div>

            {/* Nested Button-in-Button CTAs */}
            <div className="pt-1 flex flex-wrap items-center gap-3.5">
              <Link
                href="/signup"
                onClick={persistHandoffSession}
                className="group inline-flex items-center gap-3 rounded-full bg-[#f5c418] hover:bg-[#fde047] text-slate-950 font-bold text-sm pl-6 pr-2 py-2 shadow-[0_14px_32px_rgba(245,196,24,0.32)] transition-all active:scale-[0.98]"
              >
                <span>Create workspace</span>
                <span
                  aria-hidden="true"
                  className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-950/15 text-slate-950 transition-transform duration-300 group-hover:translate-x-0.5"
                >
                  →
                </span>
              </Link>
              <Link
                href={workbenchCaseHref}
                className="inline-flex items-center gap-2 rounded-full bg-white/10 hover:bg-white/15 border border-white/25 text-white font-semibold text-sm px-6 py-3 transition-all active:scale-[0.98]"
              >
                <span>Open Advisor Workbench</span>
              </Link>
            </div>
          </div>

          {/* RIGHT COLUMN (7 cols): Brushed-Steel Mechanical Split-Flap & Multi-Channel Console */}
          <div className="lg:col-span-7 rounded-[32px] bg-gradient-to-b from-slate-300/35 via-[#1e293b] to-[#061338] p-[2.5px] shadow-[0_32px_80px_rgba(0,0,0,0.65)]">
            <div className="rounded-[30px] bg-[#061539] p-6 sm:p-8 space-y-6 relative overflow-hidden">
              {/* Warm Recessed Terminal LED Strip along top bezel */}
              <div
                aria-hidden="true"
                className="mx-auto h-1.5 w-3/4 rounded-full bg-gradient-to-r from-transparent via-[#fde047] to-transparent opacity-80 blur-[1px] -mt-3 mb-2"
              />

              {/* Top Brushed-Steel Bezel Header + Physical Split-Flap IATA Drum */}
              <div className="flex flex-wrap items-start justify-between gap-4 border-b border-white/12 pb-5">
                <div className="space-y-1.5 max-w-xl">
                  <div className="flex items-center gap-2">
                    <span className="h-2 w-2 rounded-full bg-emerald-400" />
                    <p className="text-[11px] font-mono uppercase tracking-[0.2em] text-[#fde047]">
                      Not a prettier CRM. A faster intake and quoting surface
                    </p>
                  </div>
                  <h3 className="text-xl sm:text-2xl font-bold text-white leading-snug">
                    It helps teams answer faster, quote cleaner, and keep owners out
                    of every tiny decision
                  </h3>
                </div>

                {/* 3-Tile Cream Mechanical Split-Flap IATA Code Drum */}
                <div
                  className="flex items-center gap-1 rounded-xl bg-slate-950 p-1.5 border border-white/20 shadow-inner"
                  aria-label={`Active IATA code ${fixture.tagCode}`}
                >
                  {fixture.tagCode
                    .slice(0, 3)
                    .padEnd(3, " ")
                    .split("")
                    .map((char, idx) => (
                      <span
                        key={`${char}-${idx}`}
                        className="relative flex h-9 w-7 items-center justify-center rounded-md bg-[#f4efe6] font-mono text-sm font-black text-slate-950 shadow-[0_2px_4px_rgba(0,0,0,0.4)]"
                      >
                        <span
                          aria-hidden="true"
                          className="pointer-events-none absolute inset-x-0 top-1/2 h-[1px] bg-slate-900/25"
                        />
                        {char}
                      </span>
                    ))}
                </div>
              </div>

              {/* Interactive Channel Switcher + Live Source Visualizer */}
              <div className="rounded-2xl bg-[#030b22] border border-white/15 p-4 sm:p-5 space-y-4 shadow-inner">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex flex-wrap items-center gap-1.5">
                    {(
                      [
                        {
                          id: "voice",
                          label: `01 · Voice Note (${fixture.voiceNote.durationLabel})`,
                        },
                        {
                          id: "whatsapp",
                          label: "02 · WhatsApp Thread (4 msgs)",
                        },
                        {
                          id: "email",
                          label: "03 · Epistemic Hold & Brief",
                        },
                      ] as const
                    ).map((tab) => (
                      <button
                        key={tab.id}
                        type="button"
                        onClick={() => setActiveChannelTab(tab.id)}
                        className={`rounded-xl px-3.5 py-2 font-mono text-[11px] font-bold transition-all active:scale-[0.98] ${
                          activeChannelTab === tab.id
                            ? "bg-[#f5c418] text-slate-950 shadow-[0_4px_14px_rgba(245,196,24,0.3)]"
                            : "bg-white/[0.06] text-slate-300 hover:bg-white/12 border border-white/10"
                        }`}
                      >
                        {tab.label}
                      </button>
                    ))}
                  </div>

                  <span
                    className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 font-mono text-[10px] font-extrabold uppercase tracking-wider ${
                      isDatesConfirmed
                        ? "bg-emerald-500/20 text-emerald-300 border border-emerald-400/40"
                        : "bg-amber-400/20 text-[#fde047] border border-amber-400/45"
                    }`}
                  >
                    <span
                      className={`h-1.5 w-1.5 rounded-full ${
                        isDatesConfirmed
                          ? "bg-emerald-400"
                          : "bg-[#f5c418] animate-ping"
                      }`}
                    />
                    <span>
                      {isDatesConfirmed
                        ? "5/5 SLOTS LOCKED"
                        : "4/5 LOCKED · DATES HOLD"}
                    </span>
                  </span>
                </div>

                {/* Rich Multi-Channel Stage Preview */}
                <div className="rounded-2xl bg-[#07163b] border border-white/12 p-4 text-xs sm:text-sm text-slate-200 font-medium leading-relaxed">
                  {activeChannelTab === "voice" ? (
                    <div className="space-y-3.5">
                      {/* Audio Waveform Bar + Metadata */}
                      <div className="flex items-center justify-between gap-3 rounded-xl bg-slate-950/80 border border-white/10 px-3.5 py-2.5">
                        <div className="flex items-center gap-2.5">
                          <button
                            type="button"
                            onClick={() => {
                              splitFlapAudio.playFlapClack(4, true);
                              onTriggerVoiceSequence();
                            }}
                            aria-label="Play voice note ingestion"
                            className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[#f5c418] text-slate-950 font-mono text-xs font-black shadow"
                          >
                            ▶
                          </button>
                          <div>
                            <span className="block font-mono text-[9.5px] font-bold uppercase tracking-wider text-sky-300">
                              INCOMING CLIENT VOICE NOTE ·{" "}
                              {fixture.pillTitle.toUpperCase()}
                            </span>
                            <span className="font-mono text-[10px] text-slate-400">
                              {fixture.voiceNote.durationLabel} · Auto-transcribed &
                              entity-linked
                            </span>
                          </div>
                        </div>

                        {/* Animated 24-Bar Acoustic Spectrum */}
                        <div
                          aria-hidden="true"
                          className="hidden sm:flex items-center gap-[3px] h-7 px-2"
                        >
                          {WAVEFORM_BARS.slice(0, 24).map((pct, i) => (
                            <span
                              key={i}
                              className={`w-[3px] rounded-full ${
                                i % 5 === 0
                                  ? "bg-[#f5c418]"
                                  : i < 16
                                  ? "bg-sky-400"
                                  : "bg-white/30"
                              }`}
                              style={{ height: `${Math.max(20, pct * 0.26)}px` }}
                            />
                          ))}
                        </div>

                        <button
                          type="button"
                          onClick={() => {
                            onOpenStageOnHero("voice_ingest");
                            window.scrollTo({ top: 0, behavior: "smooth" });
                          }}
                          className="shrink-0 rounded-lg bg-white/10 hover:bg-white/15 border border-white/20 px-2.5 py-1 font-mono text-[10px] font-bold text-[#fde047]"
                        >
                          Stage on Monument ↑
                        </button>
                      </div>

                      {/* Verbatim Quote + Extracted Token Pills */}
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                        <p className="italic text-white/95 text-sm leading-relaxed">
                          {fixture.voiceNote.quote}
                        </p>
                      </div>

                      <div className="flex flex-wrap items-center gap-1.5 pt-1 border-t border-white/10">
                        <span className="font-mono text-[9.5px] uppercase tracking-wider text-slate-400 mr-1">
                          EXTRACTED TOKENS:
                        </span>
                        {fixture.rows.map((r) => (
                          <button
                            key={r.id}
                            type="button"
                            onClick={() => onSelectRow(r.id)}
                            className={`rounded-md px-2 py-0.5 font-mono text-[10px] font-bold transition-all ${
                              r.id === "dates" && !isDatesConfirmed
                                ? "bg-[#f5c418] text-slate-950"
                                : "bg-sky-400/15 text-sky-200 border border-sky-400/30"
                            }`}
                          >
                            {r.label} · {r.fact.value}
                          </button>
                        ))}
                      </div>
                    </div>
                  ) : activeChannelTab === "whatsapp" ? (
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                      {fixture.chatThread.map((msg, idx) => (
                        <div
                          key={msg.id}
                          className="rounded-xl bg-[#f4efe6] text-slate-900 p-3 text-xs font-medium shadow-md border border-amber-900/15 flex flex-col justify-between gap-2"
                        >
                          <div>
                            <div className="flex items-center justify-between font-mono text-[9.5px] text-slate-500 mb-1">
                              <span>CLIENT MSG 0{idx + 1}</span>
                              <span>10:1{idx + 4} AM ✓✓</span>
                            </div>
                            <p className="leading-snug text-slate-900">
                              {msg.segments.map((s, sIdx) => (
                                <span
                                  key={sIdx}
                                  className={
                                    s.highlight
                                      ? "rounded bg-[#f5c418] px-1 py-0.5 font-extrabold text-slate-950"
                                      : ""
                                  }
                                >
                                  {s.text}
                                </span>
                              ))}
                            </p>
                          </div>
                          <div className="flex items-center justify-between pt-1.5 border-t border-slate-900/10 font-mono text-[9px] font-bold text-slate-600">
                            <span>PROVENANCE WIRE ACTIVE</span>
                            <span className="text-slate-950">
                              → SLOT 0{idx + 1}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                      <div className="space-y-1">
                        <div className="inline-flex items-center gap-1.5 font-mono text-[10px] font-bold uppercase tracking-wider text-amber-300">
                          <span>AUTO-DRAFTED ADVISOR CLARIFICATION</span>
                          <span>· ROW 04 (DATES)</span>
                        </div>
                        <p className="text-white font-semibold text-sm sm:text-base">
                          &ldquo;
                          {fixture.rows.find((r) => r.id === "dates")?.fact
                            .advisorFollowUp ??
                            "Which exact departure window works best for your party?"}
                          &rdquo;
                        </p>
                      </div>
                      <button
                        type="button"
                        onClick={onToggleDatesConfirmed}
                        className={`shrink-0 rounded-xl px-4 py-2.5 font-mono text-[11px] font-extrabold uppercase tracking-wider transition-all active:scale-[0.98] ${
                          isDatesConfirmed
                            ? "bg-emerald-400 text-slate-950 shadow-[0_6px_20px_rgba(52,211,153,0.3)]"
                            : "bg-[#f5c418] hover:bg-[#fde047] text-slate-950 shadow-[0_6px_20px_rgba(245,196,24,0.3)]"
                        }`}
                        data-testid="fold2-confirm-dates-toggle"
                      >
                        {isDatesConfirmed
                          ? "✓ Client Dates Confirmed (Reset)"
                          : "Confirm Client Dates →"}
                      </button>
                    </div>
                  )}
                </div>

                {/* AUTHENTIC 5-ROW CREAM & SIGNAL-YELLOW SOLARI MECHANICAL READOUT */}
                <div className="space-y-2 pt-1">
                  <div className="flex items-center justify-between font-mono text-[10px] text-slate-400 px-1">
                    <span>
                      SOLARI 5-ROW TELEMETRY RACK (CLICK ANY ROW TO INSPECT)
                    </span>
                    <span className="text-[#fde047]">
                      {fixture.pillTitle.toUpperCase()} · {fixture.tagCode}
                    </span>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-5 gap-2">
                    {fixture.rows.map((row, rIdx) => {
                      const isDatesRow = row.id === "dates";
                      const resolvedValue =
                        isDatesRow &&
                        isDatesConfirmed &&
                        row.confirmedValueLabel
                          ? row.confirmedValueLabel.replace(
                              /\s*\(Confirmed\)/i,
                              ""
                            )
                          : row.fact.value;
                      const isHold =
                        isDatesRow &&
                        !isDatesConfirmed &&
                        row.fact.basis !== "explicit";
                      const isSelected = selectedRowId === row.id;

                      return (
                        <button
                          key={row.id}
                          type="button"
                          onClick={() => {
                            splitFlapAudio.playFlapClack(rIdx * 2, true);
                            onSelectRow(row.id);
                          }}
                          className={`group relative text-left rounded-xl p-2.5 border transition-all active:scale-[0.98] ${
                            isHold
                              ? "bg-[#f5c418] text-slate-950 border-amber-300 shadow-[0_8px_20px_rgba(245,196,24,0.28)]"
                              : "bg-[#f4efe6] text-slate-950 border-amber-900/20 shadow-[0_4px_12px_rgba(0,0,0,0.3)] hover:bg-white"
                          } ${
                            isSelected
                              ? "ring-2 ring-[#f5c418] ring-offset-2 ring-offset-[#030b22]"
                              : ""
                          }`}
                        >
                          {/* Split-flap horizontal mechanical seam */}
                          <span
                            aria-hidden="true"
                            className="pointer-events-none absolute inset-x-0 top-1/2 h-[1px] bg-slate-950/15"
                          />
                          <div className="relative flex items-center justify-between gap-1">
                            <span className="font-mono text-[8.5px] font-black uppercase tracking-wider text-slate-600">
                              0{rIdx + 1} · {row.label}
                            </span>
                            <span
                              className={`h-2 w-2 rounded-full ${
                                isHold
                                  ? "bg-slate-950 animate-pulse"
                                  : "bg-emerald-600"
                              }`}
                            />
                          </div>
                          <p className="relative mt-1.5 font-mono text-xs font-black tracking-tight truncate uppercase text-slate-950">
                            {resolvedValue}
                          </p>
                          <span className="relative mt-1 block font-mono text-[8.5px] font-bold uppercase tracking-wider text-slate-600">
                            {isHold
                              ? "HOLD · UNCONFIRMED"
                              : isDatesRow && isDatesConfirmed
                              ? "LOCKED · CONFIRMED"
                              : `BASIS · ${row.fact.basis.toUpperCase()}`}
                          </span>
                        </button>
                      );
                    })}
                  </div>
                </div>
              </div>

              {/* 3 Interactive Workflow Gate Rows (Preserves exact required test copy) */}
              <ul className="space-y-3">
                {[
                  {
                    num: "01",
                    title:
                      "Extract dates, party size, budget, pace, and trip type from messy messages",
                    body: "Voice notes, WhatsApp forwards, and email threads resolve directly onto structured departure slots with verbatim quote provenance.",
                    badge: `${fixture.pillTitle} · 4 Verbatim Quotes Linked`,
                    actionLabel: "Inspect Voice Stream",
                    onTrigger: () => {
                      setActiveGateStep(0);
                      setActiveChannelTab("voice");
                    },
                  },
                  {
                    num: "02",
                    title:
                      "Surface the missing facts that change itinerary quality before anyone quotes",
                    body: "Waypoint never invents a travel date. Unconfirmed windows lock onto a signal-yellow epistemic hold until verified.",
                    badge: isDatesConfirmed
                      ? `Dates Confirmed (${fixture.rows[3]?.confirmedValueLabel ?? "LOCKED"})`
                      : "Hold Active · NEED CONFIRMATION",
                    actionLabel: isDatesConfirmed
                      ? "Dates Locked ✓ (Toggle)"
                      : "Trigger Dates Latch",
                    onTrigger: () => {
                      setActiveGateStep(1);
                      setActiveChannelTab("email");
                      onToggleDatesConfirmed();
                    },
                  },
                  {
                    num: "03",
                    title:
                      "Protect owner time by showing what needs a human decision and what does not",
                    body: "Senior advisors review a clean brief with explicit vs. unconfirmed facts separated before supplier outreach begins.",
                    badge: `Ready for Review · ${fixture.tagCode}`,
                    actionLabel: "Inspect WhatsApp Provenance",
                    onTrigger: () => {
                      setActiveGateStep(2);
                      setActiveChannelTab("whatsapp");
                    },
                  },
                ].map((step, idx) => {
                  const isActive = activeGateStep === idx;
                  return (
                    <li
                      key={step.num}
                      onClick={step.onTrigger}
                      className={`cursor-pointer flex items-start justify-between gap-4 rounded-2xl border p-4 transition-all ${
                        isActive
                          ? "bg-white/10 border-[#f5c418]/65 shadow-[0_12px_30px_rgba(0,0,0,0.35)]"
                          : "bg-white/[0.04] hover:bg-white/[0.08] border-white/10"
                      }`}
                    >
                      <div className="flex items-start gap-3.5">
                        <span
                          className={`mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full font-mono text-xs font-black ${
                            isActive
                              ? "bg-[#f5c418] text-slate-950 shadow"
                              : "bg-white/15 text-white"
                          }`}
                        >
                          {step.num}
                        </span>
                        <div>
                          <p className="font-semibold text-white text-sm sm:text-base">
                            {step.title}
                          </p>
                          <p className="text-xs sm:text-sm text-slate-300 mt-1">
                            {step.body}
                          </p>
                          <div className="mt-2.5 flex flex-wrap items-center gap-2">
                            <span className="rounded-md bg-slate-950/80 border border-white/15 px-2.5 py-0.5 font-mono text-[10px] font-bold text-[#fde047]">
                              {step.badge}
                            </span>
                            <span className="font-mono text-[10px] font-bold text-sky-300 underline decoration-sky-400/50 underline-offset-2">
                              {step.actionLabel} →
                            </span>
                          </div>
                        </div>
                      </div>
                    </li>
                  );
                })}
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* =====================================================================
          FOLD 3: ASYMMETRIC BENTO EPISTEMIC ARCHITECTURE (#why-waypoint)
         ===================================================================== */}
      <section
        id="why-waypoint"
        className="relative py-24 sm:py-32 px-6 sm:px-12 border-t border-white/10 bg-[#020a21]"
      >
        <div className="max-w-[1440px] mx-auto space-y-12">
          {/* Section Header */}
          <div className="flex flex-col xl:flex-row xl:items-end justify-between gap-6">
            <div className="max-w-2xl space-y-3">
              <div className="inline-flex items-center gap-2 rounded-full bg-white/[0.06] border border-white/15 px-3.5 py-1 font-mono text-[10.5px] uppercase tracking-[0.22em] text-[#f5c418]">
                <span>Inside the Machine · Solari Epistemic Architecture</span>
              </div>
              <h2 className="text-3xl sm:text-4xl lg:text-[42px] font-bold tracking-[-0.03em] text-white leading-[1.08]">
                Built like flight operations. Designed for boutique travel desks.
              </h2>
            </div>

            {/* Single-Line Interactive Stage Sync Pill Bar */}
            <div className="inline-flex flex-wrap sm:flex-nowrap items-center gap-2 rounded-2xl bg-[#071846] border border-white/15 p-2 shadow-lg shrink-0">
              <span className="px-2.5 py-1 font-mono text-[10px] font-bold uppercase tracking-wider text-slate-300 whitespace-nowrap">
                Sync Hero Stage:
              </span>
              <button
                type="button"
                onClick={() => {
                  onOpenStageOnHero("voice_ingest");
                  window.scrollTo({ top: 0, behavior: "smooth" });
                }}
                className="rounded-xl bg-sky-500/20 hover:bg-sky-500/30 border border-sky-400/40 px-3 py-1.5 font-mono text-[11px] font-bold text-sky-200 whitespace-nowrap transition-all"
              >
                Gate 01 · Voice Note
              </button>
              <button
                type="button"
                onClick={() => {
                  onOpenStageOnHero("provenance_brief");
                  onSelectRow("dates");
                  window.scrollTo({ top: 0, behavior: "smooth" });
                }}
                className="rounded-xl bg-[#f5c418] hover:bg-[#fde047] px-3 py-1.5 font-mono text-[11px] font-extrabold text-slate-950 whitespace-nowrap transition-all"
              >
                Gate 02 · Epistemic Hold
              </button>
              <button
                type="button"
                onClick={() => {
                  if (!isDatesConfirmed) onToggleDatesConfirmed();
                  onOpenStageOnHero("provenance_brief");
                  onSelectRow("destination");
                  window.scrollTo({ top: 0, behavior: "smooth" });
                }}
                className="rounded-xl bg-emerald-500/20 hover:bg-emerald-500/30 border border-emerald-400/40 px-3 py-1.5 font-mono text-[11px] font-bold text-emerald-200 whitespace-nowrap transition-all"
              >
                Gate 03 · Verified Brief
              </button>
            </div>
          </div>

          {/* ASYMMETRIC BENTO GRID (7 cols + 5 cols + 12 cols full-width showcase) */}
          <div className="grid grid-cols-1 lg:grid-cols-12 grid-flow-dense gap-6 xl:gap-8">
            {/* BENTO TILE 1 (7 Cols): Interactive Provenance X-Ray & Multi-Channel Threading */}
            <div className="lg:col-span-7 rounded-[32px] bg-gradient-to-b from-sky-400/35 via-white/10 to-[#071846] p-1.5 shadow-[0_24px_60px_rgba(0,0,0,0.5)]">
              <div className="h-full rounded-[26px] bg-[#06153d] border border-white/10 p-6 sm:p-8 flex flex-col justify-between space-y-6">
                <div className="space-y-3">
                  <div className="flex flex-wrap items-center justify-between gap-2 border-b border-white/10 pb-3.5">
                    <span className="font-mono text-xs font-bold uppercase tracking-wider text-sky-300">
                      Gate 01 · Interactive Provenance X-Ray
                    </span>
                    <span className="inline-flex items-center gap-1.5 rounded-full bg-sky-400/15 border border-sky-400/30 px-3 py-0.5 font-mono text-[10px] font-bold text-sky-200">
                      <span className="h-2 w-2 rounded-full bg-sky-400 animate-pulse" />
                      {fixture.pillTitle.toUpperCase()} · 4 CHANNELS THREADED
                    </span>
                  </div>
                  <h3 className="text-2xl font-bold text-white tracking-tight">
                    Multi-channel message ingestion with verbatim trace wires
                  </h3>
                  <p className="text-sm text-slate-300 leading-relaxed">
                    Clients send voice notes at 10:14 AM and follow up with three
                    WhatsApp texts. Click any slot below to trace how Waypoint
                    links every extracted brief field back to the exact sentence
                    the traveler spoke or typed.
                  </p>
                </div>

                {/* Interactive Provenance Trace Explorer */}
                <div className="grid grid-cols-1 sm:grid-cols-12 gap-3 items-stretch rounded-2xl bg-[#030b22] border border-white/12 p-4">
                  {/* Left: 5 Clickable Brief Slots */}
                  <div className="sm:col-span-5 space-y-1.5">
                    <span className="block font-mono text-[9.5px] font-bold uppercase tracking-wider text-slate-400 mb-2">
                      1. Select Brief Slot:
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
                          className={`w-full flex items-center justify-between rounded-xl px-3 py-2 text-left font-mono text-xs transition-all ${
                            isSelected
                              ? "bg-[#f5c418] text-slate-950 font-black shadow"
                              : "bg-white/[0.05] text-slate-200 hover:bg-white/10 border border-white/10"
                          }`}
                          data-testid={`fold3-trace-slot-${row.id}`}
                        >
                          <span className="truncate">
                            0{idx + 1} · {row.label}
                          </span>
                          <span
                            className={`ml-2 shrink-0 rounded px-1.5 py-0.5 text-[9.5px] font-bold ${
                              isSelected
                                ? "bg-slate-950/15 text-slate-950"
                                : isHold
                                ? "bg-amber-400/20 text-[#fde047]"
                                : "bg-emerald-400/20 text-emerald-300"
                            }`}
                          >
                            {row.fact.value}
                          </span>
                        </button>
                      );
                    })}
                  </div>

                  {/* Right: Live Connected Verbatim Evidence Card */}
                  <div className="sm:col-span-7 rounded-xl bg-[#081c4f] border border-[#f5c418]/45 p-4 flex flex-col justify-between space-y-3">
                    <div className="space-y-2.5">
                      <div className="flex flex-wrap items-center justify-between gap-1.5">
                        <span className="font-mono text-[10px] font-extrabold uppercase tracking-wider text-[#fde047]">
                          2. Verbatim Source ({SLOT_CHANNEL_LABELS[activeBentoRow.id]})
                        </span>
                        <span className="rounded-md bg-slate-950 px-2 py-0.5 font-mono text-[9.5px] font-bold text-sky-300 border border-white/15">
                          {activeBentoRow.fact.basis === "explicit"
                            ? "EXPLICIT SIGNAL"
                            : activeBentoRow.fact.basis === "inferred"
                            ? "INFERRED SIGNAL"
                            : "HOLD · UNCONFIRMED"}
                        </span>
                      </div>

                      <div className="rounded-xl bg-[#f4efe6] text-slate-950 p-3.5 font-medium text-xs sm:text-sm shadow-inner border border-amber-900/20 leading-relaxed">
                        &ldquo;
                        {activeBentoRow.fact.evidenceQuote ||
                          fixture.voiceNote.quote.replace(/^[“"]|[”"]$/g, "")}
                        &rdquo;
                      </div>
                    </div>

                    <div className="space-y-1.5 pt-2 border-t border-white/10 text-xs">
                      <div className="flex items-center justify-between font-mono text-[10px]">
                        <span className="text-slate-400">EPISTEMIC BASIS:</span>
                        <span className="font-bold uppercase text-white">
                          {activeBentoRow.fact.basis}
                        </span>
                      </div>
                      <p className="text-slate-300 text-xs leading-relaxed">
                        <strong className="text-[#fde047]">
                          Advisor Next Step:
                        </strong>{" "}
                        {activeBentoRow.fact.advisorFollowUp ||
                          SLOT_FOLLOW_UP_FALLBACKS[activeBentoRow.id]}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* BENTO TILE 2 (5 Cols): Gate 02 Physical Split-Flap Epistemic Hold Drum */}
            <div className="lg:col-span-5 rounded-[32px] bg-gradient-to-b from-[#f5c418] via-[#f5c418]/40 to-[#071846] p-1.5 shadow-[0_24px_60px_rgba(245,196,24,0.18)]">
              <div className="h-full rounded-[26px] bg-[#06153d] p-6 sm:p-8 flex flex-col justify-between space-y-5">
                <div className="space-y-3">
                  <div className="flex items-center justify-between border-b border-white/10 pb-3.5">
                    <span className="font-mono text-xs font-bold uppercase tracking-wider text-[#fde047]">
                      Gate 02 · Epistemic Hold Drum
                    </span>
                    <span className="inline-flex items-center gap-1.5 rounded-full bg-[#f5c418]/20 border border-[#f5c418]/50 px-2.5 py-0.5 font-mono text-[10px] font-bold text-[#fde047]">
                      <span className="h-2 w-2 rounded-full bg-[#f5c418] animate-ping" />
                      ROW 04 · DATES
                    </span>
                  </div>
                  <h3 className="text-2xl font-bold text-white tracking-tight">
                    Zero hallucinated dates or budgets
                  </h3>
                  <p className="text-sm text-slate-300 leading-relaxed">
                    When a traveler says &ldquo;around June next year&rdquo; or
                    &ldquo;dates flexible,&rdquo; the board physically locks Row 04
                    onto{" "}
                    <strong className="text-[#fde047]">NEED CONFIRMATION</strong>{" "}
                    until the advisor verifies the exact window.
                  </p>
                </div>

                {/* Auto-Drafted Clarification Prompt Box (fills middle with high-signal utility) */}
                <div className="rounded-2xl bg-[#081c4f] border border-white/12 p-3.5 space-y-1.5">
                  <div className="flex items-center justify-between font-mono text-[9.5px] uppercase tracking-wider text-amber-300">
                    <span>AUTO-GENERATED CLIENT FOLLOW-UP</span>
                    <span>{fixture.tagCode} DESK</span>
                  </div>
                  <p className="text-xs sm:text-sm text-white font-medium leading-snug">
                    &ldquo;
                    {datesRow?.fact.advisorFollowUp ??
                      `Confirm exact ${fixture.pillTitle} departure window before locking inventory.`}
                    &rdquo;
                  </p>
                </div>

                {/* Authentic 8-Column Solari 2-Line Yellow NEED CONFIRMATION Drum Strip */}
                <div className="rounded-2xl bg-slate-950 border border-white/15 p-4 space-y-3 shadow-inner">
                  <div className="flex items-center justify-between font-mono text-[10px]">
                    <span className="text-slate-400">
                      ROW 04 MECHANICAL DRUM ({fixture.tagCode})
                    </span>
                    <span
                      className={
                        isDatesConfirmed
                          ? "text-emerald-400 font-bold"
                          : "text-[#fde047] font-bold"
                      }
                    >
                      {isDatesConfirmed ? "✓ LATCH LOCKED" : "⚠️ HOLD ACTIVE"}
                    </span>
                  </div>

                  {!isDatesConfirmed ? (
                    <div className="grid grid-cols-8 gap-1.5">
                      {NEED_CONFIRMATION_CELLS.map((cell, idx) => (
                        <div
                          key={idx}
                          className="relative flex flex-col items-center justify-center h-12 rounded-md bg-[#f5c418] text-slate-950 font-mono font-black shadow"
                        >
                          <span
                            aria-hidden="true"
                            className="pointer-events-none absolute inset-x-0 top-1/2 h-[1px] bg-slate-950/25"
                          />
                          <span className="text-[11px] leading-none">
                            {cell.top.trim() || "\u00A0"}
                          </span>
                          <span className="text-[10px] leading-none mt-1">
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
                            className="relative flex h-12 items-center justify-center rounded-md bg-[#f4efe6] text-slate-950 font-mono text-xs font-black shadow"
                          >
                            <span
                              aria-hidden="true"
                              className="pointer-events-none absolute inset-x-0 top-1/2 h-[1px] bg-slate-950/25"
                            />
                            {ch}
                          </span>
                        ))}
                    </div>
                  )}

                  <div className="pt-1 flex items-center justify-between gap-2">
                    <span className="font-mono text-[10px] text-slate-400">
                      {isDatesConfirmed
                        ? `Confirmed: ${fixture.rows[3]?.confirmedValueLabel}`
                        : "8 two-line Solari hold flaps active"}
                    </span>
                    <button
                      type="button"
                      onClick={onToggleDatesConfirmed}
                      className="rounded-xl bg-[#f5c418] hover:bg-[#fde047] text-slate-950 px-3.5 py-1.5 font-mono text-[10.5px] font-extrabold uppercase tracking-wider transition-all active:scale-[0.98]"
                      data-testid="fold3-latch-toggle"
                    >
                      {isDatesConfirmed ? "Reset Hold" : "Test Latch →"}
                    </button>
                  </div>
                </div>
              </div>
            </div>

            {/* BENTO TILE 3 (12 Cols Wide Showcase): Gate 03 + Live Photorealistic Destination Pass Gallery */}
            <div className="lg:col-span-12 rounded-[32px] bg-gradient-to-r from-emerald-400/40 via-sky-400/25 to-[#f5c418]/40 p-1.5 shadow-[0_28px_70px_rgba(0,0,0,0.55)]">
              <div className="rounded-[26px] bg-[#06153d] p-6 sm:p-8 grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
                <div className="lg:col-span-5 space-y-4">
                  <div className="flex items-center justify-between border-b border-white/10 pb-3">
                    <span className="font-mono text-xs font-bold uppercase tracking-wider text-emerald-300">
                      Gate 03 · Ready for Review
                    </span>
                    <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-400/15 border border-emerald-400/35 px-2.5 py-0.5 font-mono text-[10px] font-bold text-emerald-300">
                      <span className="h-2 w-2 rounded-full bg-emerald-400" />
                      {fixture.tagCode} BRIEF PACKET
                    </span>
                  </div>

                  <h3 className="text-2xl sm:text-3xl font-bold text-white tracking-tight leading-tight">
                    One-click brief to workbench handoff
                  </h3>

                  <p className="text-sm sm:text-base text-slate-300 leading-relaxed">
                    Once facts are confirmed, advisors promote the brief straight
                    into the Waypoint Workbench with seasonal suitability, route
                    sequencing, and bespoke destination visual assets already
                    attached.
                  </p>

                  <div className="pt-2 flex flex-wrap items-center gap-3">
                    <Link
                      href={workbenchCaseHref}
                      className="group inline-flex items-center gap-3 rounded-full bg-emerald-400 hover:bg-emerald-300 text-slate-950 font-bold text-xs sm:text-sm pl-5 pr-2 py-2 shadow-lg transition-all active:scale-[0.98]"
                    >
                      <span>
                        Open {fixture.pillTitle} ({fixture.tagCode}) in Workbench
                      </span>
                      <span className="flex h-7 w-7 items-center justify-center rounded-full bg-slate-950/15 text-slate-950">
                        →
                      </span>
                    </Link>
                    <Link
                      href="/itinerary-checker"
                      className="rounded-full bg-white/10 hover:bg-white/15 border border-white/20 px-4 py-2.5 font-mono text-xs font-bold text-white transition-all"
                    >
                      Run Public Itinerary Checker
                    </Link>
                  </div>
                </div>

                {/* Right 7 Cols: Interactive Photorealistic Destination Dossier Strip */}
                <div className="lg:col-span-7 space-y-3">
                  <div className="flex items-center justify-between font-mono text-[10px] text-slate-300">
                    <span>
                      LIVE DESTINATION FLIGHT DECK · CLICK ANY PASS TO LOAD BRIEF
                    </span>
                    <span className="text-[#fde047]">
                      15 BESPOKE ASSET PACKETS
                    </span>
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
                            handleDestinationSelect(
                              entry.slug,
                              entry.displayName
                            )
                          }
                          className={`group relative rounded-2xl overflow-hidden border text-left transition-all active:scale-[0.98] ${
                            isCurrent
                              ? "border-[#f5c418] ring-2 ring-[#f5c418]/60 shadow-[0_12px_30px_rgba(245,196,24,0.28)]"
                              : "border-white/15 hover:border-white/35"
                          }`}
                          data-testid={`fold3-gallery-card-${entry.slug}`}
                        >
                          <div className="relative h-28 w-full bg-slate-950 overflow-hidden">
                            <img
                              src={entry.destinationPhotoUrl}
                              alt={entry.displayName}
                              className="h-full w-full object-cover transition-transform duration-700 group-hover:scale-105"
                            />
                            <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-slate-950/35 to-transparent" />
                            <span className="absolute top-2 right-2 rounded bg-[#f4efe6] text-slate-950 px-1.5 py-0.5 font-mono text-[9.5px] font-black shadow">
                              {entry.iataCode}
                            </span>
                            <div className="absolute bottom-2 left-2.5 right-2.5">
                              <p className="font-bold text-white text-sm leading-tight">
                                {entry.displayName}
                              </p>
                              <p className="font-mono text-[9.5px] text-amber-300 truncate">
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
        </div>
      </section>

      {/* =====================================================================
          FOLD 4: ACCESS TIERS & PRE-FLIGHT DEPLOYMENT (#pricing)
         ===================================================================== */}
      <section
        id="pricing"
        className="relative py-24 sm:py-32 px-6 sm:px-12 border-t border-white/10 bg-[#041030]"
      >
        <div className="max-w-[1440px] mx-auto space-y-12">
          <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-6">
            <div className="max-w-2xl space-y-3">
              <div className="inline-flex items-center gap-2 rounded-full bg-[#f5c418]/15 border border-[#f5c418]/40 px-3.5 py-1 font-mono text-[10.5px] uppercase tracking-[0.22em] text-[#fde047]">
                <span>Pricing & Workspace Access · No Theater</span>
              </div>
              <h2 className="text-3xl sm:text-4xl font-bold tracking-[-0.03em] text-white leading-tight">
                Start with the operating surface that fits your desk today.
              </h2>
            </div>
            <p className="text-sm sm:text-base text-slate-300 max-w-md leading-relaxed">
              Self-serve workspace creation is live right now and carries your
              active{" "}
              <strong className="text-[#fde047]">
                {fixture.pillTitle} ({fixture.tagCode})
              </strong>{" "}
              flight brief directly into onboarding.
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 xl:gap-8 items-stretch">
            {/* Tier 1: Free Public Checker (4 cols) */}
            <div className="lg:col-span-4 rounded-[28px] bg-white/10 p-1.5 flex">
              <div className="w-full rounded-[22px] bg-[#061539] border border-white/10 p-6 sm:p-7 flex flex-col justify-between space-y-6">
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-[10.5px] font-bold uppercase tracking-widest text-sky-300">
                      01 · Traveler Pre-Qualification
                    </span>
                    <span className="rounded-md bg-sky-400/15 border border-sky-400/30 px-2.5 py-0.5 font-mono text-[10px] font-bold text-sky-200">
                      PUBLIC TOOL
                    </span>
                  </div>
                  <div>
                    <h3 className="text-2xl font-bold text-white">
                      Free Itinerary Checker
                    </h3>
                    <p className="text-xs font-mono uppercase tracking-wider text-slate-400 mt-1">
                      No sign-up required · Instant stress-test
                    </p>
                  </div>
                  <p className="text-sm text-slate-300 leading-relaxed">
                    A dedicated public surface for travelers or advisors to paste,
                    upload, or screenshot a draft trip plan and surface pacing,
                    transfer, and weather risks.
                  </p>
                  <ul className="space-y-2 text-xs sm:text-sm text-slate-200 pt-2 border-t border-white/10">
                    <li className="flex items-center gap-2">
                      <span className="text-sky-400 font-bold">✓</span>
                      <span>Upload PDF, screenshot, or ChatGPT draft</span>
                    </li>
                    <li className="flex items-center gap-2">
                      <span className="text-sky-400 font-bold">✓</span>
                      <span>Live Open-Meteo climate & transfer sanity checks</span>
                    </li>
                    <li className="flex items-center gap-2">
                      <span className="text-sky-400 font-bold">✓</span>
                      <span>Produces a cleaner brief before agency intake</span>
                    </li>
                  </ul>
                </div>

                <Link
                  href="/itinerary-checker"
                  className="w-full inline-flex items-center justify-center gap-2 rounded-full bg-white/10 hover:bg-white/15 border border-white/25 text-white font-semibold text-sm py-3 px-5 transition-all"
                >
                  <span>Try the Public Checker</span>
                  <span aria-hidden="true">→</span>
                </Link>
              </div>
            </div>

            {/* Tier 2: B2B Agency Workspace (Featured 5 cols) */}
            <div className="lg:col-span-5 rounded-[28px] bg-gradient-to-b from-[#f5c418] via-[#f5c418]/50 to-[#061539] p-1.5 shadow-[0_24px_60px_rgba(245,196,24,0.22)] flex">
              <div className="w-full rounded-[22px] bg-[#071946] p-6 sm:p-8 flex flex-col justify-between space-y-6">
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-[10.5px] font-bold uppercase tracking-widest text-[#fde047]">
                      02 · B2B Agency Operating System
                    </span>
                    <span className="rounded-full bg-[#f5c418] text-slate-950 px-3 py-0.5 font-mono text-[10px] font-black uppercase tracking-wider">
                      Recommended
                    </span>
                  </div>
                  <div>
                    <h3 className="text-2xl sm:text-3xl font-bold text-white">
                      Self-Serve Workspace
                    </h3>
                    <p className="text-xs font-mono uppercase tracking-wider text-amber-300 mt-1">
                      Pre-loaded with your {fixture.pillTitle} ({fixture.tagCode})
                      case
                    </p>
                  </div>
                  <p className="text-sm text-slate-200 leading-relaxed">
                    The full B2B intake and quoting workbench for boutique travel
                    agencies. Capture voice notes, WhatsApp threads, and emails into
                    epistemically gated briefs.
                  </p>
                  <ul className="space-y-2 text-xs sm:text-sm text-white pt-2 border-t border-white/15">
                    <li className="flex items-center gap-2">
                      <span className="text-[#fde047] font-bold">✓</span>
                      <span>
                        5-slot Solari brief compilation with verbatim provenance
                      </span>
                    </li>
                    <li className="flex items-center gap-2">
                      <span className="text-[#fde047] font-bold">✓</span>
                      <span>
                        Signal-yellow epistemic holds prevent unverified quotes
                      </span>
                    </li>
                    <li className="flex items-center gap-2">
                      <span className="text-[#fde047] font-bold">✓</span>
                      <span>
                        Internal risk notes stay private from traveler-facing replies
                      </span>
                    </li>
                  </ul>
                </div>

                <div className="space-y-2.5">
                  <Link
                    href="/signup"
                    onClick={persistHandoffSession}
                    className="w-full inline-flex items-center justify-center gap-2 rounded-full bg-[#f5c418] hover:bg-[#fde047] text-slate-950 font-bold text-sm py-3.5 px-6 shadow-[0_12px_28px_rgba(245,196,24,0.3)] transition-all"
                  >
                    <span>Create workspace</span>
                    <span aria-hidden="true">→</span>
                  </Link>
                  <p className="text-center font-mono text-[10px] text-slate-400">
                    Carries active {fixture.tagCode} ·{" "}
                    {fixture.rows[1]?.fact.value} ·{" "}
                    {fixture.rows[2]?.fact.value} brief into signup
                  </p>
                </div>
              </div>
            </div>

            {/* Tier 3: Multi-Advisor Guided Rollout (3 cols) */}
            <div className="lg:col-span-3 rounded-[28px] bg-white/10 p-1.5 flex">
              <div className="w-full rounded-[22px] bg-[#061539] border border-white/10 p-6 sm:p-7 flex flex-col justify-between space-y-6">
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-[10.5px] font-bold uppercase tracking-widest text-emerald-300">
                      03 · Multi-Desk Rollout
                    </span>
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-white">
                      Guided Team Setup
                    </h3>
                    <p className="text-xs font-mono uppercase tracking-wider text-slate-400 mt-1">
                      Optional multi-advisor onboarding
                    </p>
                  </div>
                  <p className="text-sm text-slate-300 leading-relaxed">
                    For multi-advisor agencies that want shared intake conventions,
                    owner review gates, and custom destination templates.
                  </p>
                  <ul className="space-y-2 text-xs text-slate-300 pt-2 border-t border-white/10">
                    <li className="flex items-center gap-2">
                      <span className="text-emerald-400 font-bold">✓</span>
                      <span>Shared desk routing & owner escalation rules</span>
                    </li>
                    <li className="flex items-center gap-2">
                      <span className="text-emerald-400 font-bold">✓</span>
                      <span>Full pricing details & FAQ on dedicated page</span>
                    </li>
                  </ul>
                </div>

                <Link
                  href="/pricing"
                  className="w-full inline-flex items-center justify-center gap-2 rounded-full bg-white/10 hover:bg-white/15 border border-white/20 text-white font-semibold text-xs sm:text-sm py-3 px-4 transition-all"
                >
                  <span>Full Pricing & FAQ →</span>
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* =====================================================================
          TERMINAL DEPARTURE FOOTER
         ===================================================================== */}
      <footer className="py-16 px-6 sm:px-12 border-t border-white/10 bg-[#02081c]">
        <div className="max-w-[1440px] mx-auto flex flex-col sm:flex-row items-start sm:items-center justify-between gap-8">
          <div className="space-y-2">
            <div className="flex items-center gap-3">
              <span className="inline-flex h-2.5 w-2.5 rounded-full bg-[#f5c418]" />
              <p className="font-mono text-sm font-black tracking-[0.22em] text-white uppercase">
                WAYPOINT® · FROM MESSAGES TO MEANINGFUL TRAVEL PLANS
              </p>
            </div>
            <p className="text-sm text-slate-400">
              Interactive Departure Board intake, epistemic gating, and quoting
              surface for boutique travel agencies.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-3.5">
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
              className="inline-flex items-center gap-2 rounded-full bg-white/10 hover:bg-white/15 border border-white/20 text-white font-semibold text-sm px-5 py-2.5 transition-all"
            >
              <span>Advisor Workbench</span>
            </Link>
            <Link
              href="/itinerary-checker"
              className="inline-flex items-center gap-2 rounded-full bg-white/10 hover:bg-white/15 border border-white/20 text-white font-semibold text-sm px-5 py-2.5 transition-all"
            >
              <span>Free Itinerary Checker</span>
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
};
