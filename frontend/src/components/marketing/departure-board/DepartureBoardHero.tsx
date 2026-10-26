"use client";

import React, { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import {
  DEPARTURE_INQUIRIES,
  type BoardRowId,
  type InquiryId,
} from "./board-fixtures";
import { splitFlapAudio } from "./board-engine";
import { SplitFlapBoard } from "./SplitFlapBoard";
import {
  IncomingRequestVoiceCard,
  InquirySwitcherDock,
  ProvenanceAndBriefOverlay,
  type InteractiveStageMode,
} from "./DepartureBoardOverlays";

export const DepartureBoardLandingPage: React.FC = () => {
  const [activeInquiryId, setActiveInquiryId] = useState<InquiryId>("italy");
  const [stageMode, setStageMode] = useState<InteractiveStageMode>("hero");
  const [isScanningDates, setIsScanningDates] = useState(false);
  const [selectedRowId, setSelectedRowId] = useState<BoardRowId | null>(null);
  const [forceTriggerKey, setForceTriggerKey] = useState(0);
  const [soundEnabled, setSoundEnabled] = useState(true);
  const [hasSwitchedInquiry, setHasSwitchedInquiry] = useState(false);

  // 3-Layer Mouse Parallax State
  const [mouseNorm, setMouseNorm] = useState<{ x: number; y: number }>({
    x: 0,
    y: 0,
  });

  const scanTimersRef = useRef<number[]>([]);

  const clearScanTimers = useCallback(() => {
    scanTimersRef.current.forEach((id) => window.clearTimeout(id));
    scanTimersRef.current = [];
  }, []);

  useEffect(() => {
    return clearScanTimers;
  }, [clearScanTimers]);

  const fixture = DEPARTURE_INQUIRIES[activeInquiryId];

  /**
   * Triggers the Frame 2 -> Frame 1 -> Frame 3 live ingestion story choreography
   * when clicking "See it work ->" or replaying the voice note.
   */
  const triggerSeeItWorkSequence = useCallback(() => {
    clearScanTimers();
    setStageMode("voice_ingest");
    setIsScanningDates(true);
    setSelectedRowId(null);

    // After 1.9s of scanning "APR 18-3?" with "Finalizing dates...",
    // the epistemic gate locks Row 4 onto signal-yellow "NEED CONFIRMATION"
    const tLock = window.setTimeout(() => {
      setIsScanningDates(false);
      splitFlapAudio.playConfirmationLatch();
    }, 2800);

    scanTimersRef.current.push(tLock);
  }, [clearScanTimers]);

  const handleSelectInquiry = useCallback(
    (nextId: InquiryId) => {
      clearScanTimers();
      setActiveInquiryId(nextId);
      setHasSwitchedInquiry(true);
      setIsScanningDates(false);
      setForceTriggerKey((prev) => prev + 1);
    },
    [clearScanTimers]
  );

  const handleSelectRow = useCallback((rowId: BoardRowId) => {
    setSelectedRowId((prev) => (prev === rowId ? null : rowId));
    setStageMode("provenance_brief");
  }, []);

  const handleChangeStageMode = useCallback(
    (nextMode: InteractiveStageMode) => {
      clearScanTimers();
      setStageMode(nextMode);
      setSelectedRowId(null);
      if (nextMode === "voice_ingest") {
        setIsScanningDates(true);
        const tLock = window.setTimeout(() => {
          setIsScanningDates(false);
          splitFlapAudio.playConfirmationLatch();
        }, 2800);
        scanTimersRef.current.push(tLock);
      } else {
        setIsScanningDates(false);
      }
    },
    [clearScanTimers]
  );

  const handleToggleSound = useCallback(() => {
    const next = splitFlapAudio.toggle();
    setSoundEnabled(next);
  }, []);

  const handleMouseMove = useCallback(
    (e: React.MouseEvent<HTMLElement>) => {
      const rect = e.currentTarget.getBoundingClientRect();
      if (!rect.width || !rect.height) return;
      const nx = ((e.clientX - rect.left) / rect.width - 0.5) * 2;
      const ny = ((e.clientY - rect.top) / rect.height - 0.5) * 2;
      setMouseNorm({
        x: Math.max(-1, Math.min(1, nx)),
        y: Math.max(-1, Math.min(1, ny)),
      });
    },
    []
  );

  const handleMouseLeave = useCallback(() => {
    setMouseNorm({ x: 0, y: 0 });
  }, []);

  // Headlines & subcopy synchronized with the 4 reference frames
  const heroCopy =
    stageMode === "voice_ingest"
      ? {
          eyebrow: "FOR TRAVEL ADVISORS",
          headlineLines: ["From", "inquiry", "to", "itinerary."],
          subcopy:
            "Waypoint turns scattered travel requests into structured, quote-ready plans — so you can focus on your clients.",
          primaryCtaLabel: "See it work",
        }
      : stageMode === "provenance_brief"
        ? {
            eyebrow: "FROM INQUIRY TO ITINERARY",
            headlineLines: ["See how it", "organizes", "the request."],
            subcopy:
              "Waypoint turns scattered messages into a clear, quote-ready brief — so you can move faster with confidence.",
            primaryCtaLabel: "See it in action",
          }
        : {
            eyebrow: fixture.eyebrow,
            headlineLines: ["Every", "inquiry.", "Under", "control."],
            subcopy: fixture.subcopy,
            primaryCtaLabel: "See it work",
          };

  return (
    <div className="min-h-screen bg-[#04133b] text-white selection:bg-[#f5c418] selection:text-slate-950 overflow-x-hidden">
      {/* Keyframe animation for the swinging IATA luggage tag */}
      <style>{`
        @keyframes tagSwing {
          0% { transform: rotate(11deg); }
          35% { transform: rotate(-7deg); }
          65% { transform: rotate(4deg); }
          85% { transform: rotate(-1.8deg); }
          100% { transform: rotate(0deg); }
        }
      `}</style>

      {/* =====================================================================
          HERO STAGE (1672:941 Art-Directed Multi-Layer 3D Interactive Stage)
         ===================================================================== */}
      <section
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
        aria-label="Waypoint Departure Board Interactive Hero"
        className="relative w-full bg-[#051b5c] overflow-hidden border-b border-white/10"
      >
        {/* Desktop 1672x941 Aspect-Locked Interactive Stage */}
        <div
          className="relative mx-auto w-full max-w-[1760px] aspect-[1672/941] min-h-[580px] overflow-hidden select-none"
          data-testid="departure-board-stage"
        >
          {/* LAYER 1: Clean Background Landscape (Royal Blue Diagonal + Sunlit Airport Terminal) */}
          <div
            className="pointer-events-none absolute inset-0 transition-transform duration-200 ease-out"
            style={{
              transform: `translate3d(${mouseNorm.x * -6}px, ${mouseNorm.y * -4}px, 0)`,
            }}
            data-testid="departure-board-layer-1"
          >
            <img
              src={
                stageMode === "provenance_brief"
                  ? "/landing/departure-board/bg-landscape-frame3-clean.png"
                  : "/landing/departure-board/bg-landscape-clean.png"
              }
              alt="Waypoint OS workspace preview showing a boutique travel operations desk and airport departure terminal"
              className="w-full h-full object-fill select-none"
              draggable={false}
            />
          </div>

          {/* TOP NAVIGATION BAR (Matches Reference Frame 1-4 Coordinates & Styling) */}
          <header className="relative z-40 flex items-center justify-between px-[7%] pt-[1.9%]">
            <div className="flex items-center gap-12 lg:gap-28 xl:gap-32">
              <Link
                href="/"
                className="font-sans text-[15px] sm:text-[17.5px] font-extrabold tracking-[0.18em] text-white uppercase flex items-center gap-1"
              >
                <span>WAYPOINT</span>
                <span className="text-[10px] align-top text-white/75">®</span>
                <span className="sr-only">Waypoint OS</span>
              </Link>

              <nav
                aria-label="Primary Navigation"
                className="hidden md:flex items-center gap-6 lg:gap-9 text-[13.5px] font-medium text-white/90"
              >
                <a
                  href="#product"
                  className="inline-flex items-center gap-1 hover:text-white transition-colors"
                >
                  <span>Product</span>
                  <svg viewBox="0 0 12 12" className="h-3 w-3 opacity-70" fill="currentColor">
                    <path d="M2.5 4.5L6 8l3.5-3.5" stroke="currentColor" strokeWidth="1.4" fill="none" />
                  </svg>
                </a>
                <a
                  href="#why-waypoint"
                  className="inline-flex items-center gap-1 hover:text-white transition-colors"
                >
                  <span>Why Waypoint</span>
                  <svg viewBox="0 0 12 12" className="h-3 w-3 opacity-70" fill="currentColor">
                    <path d="M2.5 4.5L6 8l3.5-3.5" stroke="currentColor" strokeWidth="1.4" fill="none" />
                  </svg>
                </a>
                <Link
                  href="/itinerary-checker"
                  className="inline-flex items-center gap-1 hover:text-white transition-colors"
                >
                  <span>Resources</span>
                  <svg viewBox="0 0 12 12" className="h-3 w-3 opacity-70" fill="currentColor">
                    <path d="M2.5 4.5L6 8l3.5-3.5" stroke="currentColor" strokeWidth="1.4" fill="none" />
                  </svg>
                </Link>
                <a
                  href="#pricing"
                  className="hover:text-white transition-colors"
                >
                  Pricing
                </a>
              </nav>
            </div>

            <div className="flex items-center gap-4 sm:gap-5">
              <Link
                href="/login"
                className="text-[13.5px] font-semibold text-white hover:text-[#fde047] transition-colors drop-shadow-[0_1px_4px_rgba(0,0,0,0.45)]"
              >
                Sign in
              </Link>
              <Link
                href="/signup"
                className="inline-flex items-center gap-2 rounded-full bg-white hover:bg-slate-100 text-[#0c2766] font-semibold text-[13.5px] px-4 sm:px-5 py-2 shadow-[0_8px_24px_rgba(0,0,0,0.22)] transition-all"
              >
                <span>Book a demo</span>
                <span aria-hidden="true">→</span>
              </Link>
            </div>
          </header>

          {/* LAYER 2: Physical Brushed-Steel Departure Board + Straight-Built 3D Split-Flap Matrix */}
          <SplitFlapBoard
            fixture={fixture}
            isScanningDates={isScanningDates}
            selectedRowId={selectedRowId}
            onSelectRow={handleSelectRow}
            showProvenanceWires={stageMode === "provenance_brief"}
            forceTriggerKey={forceTriggerKey}
            parallaxOffset={{
              x: mouseNorm.x * 9,
              y: mouseNorm.y * 6,
              rotateY: mouseNorm.x * 1.6,
              rotateX: mouseNorm.y * -1.1,
            }}
          />

          {/* LAYER 3: Foreground Sofa, Coffee Table (with ITA Boarding Pass & Passport), and Carry-On Suitcase */}
          <div
            className="pointer-events-none absolute inset-0 z-20 transition-transform duration-200 ease-out"
            style={{
              transform: `translate3d(${mouseNorm.x * 16}px, ${mouseNorm.y * 10}px, 0)`,
            }}
            data-testid="departure-board-layer-3"
          >
            <img
              src="/landing/departure-board/fg-luggage-layer.png"
              alt=""
              aria-hidden="true"
              className="w-full h-full object-fill select-none"
              draggable={false}
            />
          </div>

          {/* LAYER 4: Left Cobalt-Blue Editorial Copy & CTAs (Matches Frame 1-4 Typography & Position) */}
          <div
            className="pointer-events-none absolute z-30 flex flex-col justify-start transition-all duration-300"
            style={{
              left: stageMode === "provenance_brief" ? "6.0%" : "7.6%",
              top: stageMode === "provenance_brief" ? "13.2%" : "16.0%",
              width: stageMode === "provenance_brief" ? "28%" : "32%",
            }}
          >
            <div className="flex items-center gap-3 mb-2.5 sm:mb-3.5">
              <span
                aria-hidden="true"
                className="h-[1.5px] w-10 sm:w-14 bg-[#f5c418]/90 rounded-full shrink-0"
              />
              <p className="text-[11px] sm:text-[12.5px] font-bold tracking-[0.22em] text-white/90 uppercase whitespace-nowrap">
                {heroCopy.eyebrow}
              </p>
              <span
                aria-hidden="true"
                className="h-[1.5px] w-10 sm:w-14 bg-[#f5c418]/90 rounded-full shrink-0"
              />
            </div>

            <h1
              aria-label={heroCopy.headlineLines.join(" ")}
              className={`font-sans font-bold tracking-[-0.04em] text-white ${
                stageMode === "hero"
                  ? "text-[44px] sm:text-[64px] lg:text-[78px] xl:text-[88px] leading-[0.93] mb-4 sm:mb-5"
                  : stageMode === "voice_ingest"
                    ? "text-[38px] sm:text-[54px] lg:text-[66px] xl:text-[72px] tracking-[-0.045em] leading-[1.03] mb-6 sm:mb-7"
                    : "text-[36px] sm:text-[50px] lg:text-[60px] xl:text-[66px] leading-[0.94] mb-3 sm:mb-4"
              }`}
            >
              {heroCopy.headlineLines.map((line, i) => (
                <span key={i} className="block">
                  {line}
                  {i < heroCopy.headlineLines.length - 1 ? " " : ""}
                </span>
              ))}
            </h1>

            {stageMode === "hero" ? (
              <p className="text-white/90 font-normal text-[15px] sm:text-[18px] lg:text-[20px] xl:text-[20.5px] leading-[1.35] max-w-[365px] mb-6">
                Turn scattered travel requests
                <br />
                into quote-ready briefs <span className="text-[#93c5fd]">your team</span>
                <br />
                can actually use.
              </p>
            ) : stageMode === "voice_ingest" ? (
              <p className="text-white/90 font-normal text-[14.5px] sm:text-[16.5px] lg:text-[18px] xl:text-[18.5px] leading-[1.36] max-w-[415px] mb-5 sm:mb-6">
                {heroCopy.subcopy}
              </p>
            ) : (
              <p className="text-white/90 font-normal text-[14px] sm:text-[16px] lg:text-[17.5px] xl:text-[18px] leading-[1.36] max-w-[385px] mb-4">
                {heroCopy.subcopy}
              </p>
            )}

            {/* Primary & Secondary Action Pills (Preserved Across All 4 Reference Frames) */}
            <div className="pointer-events-auto flex flex-wrap items-center gap-3.5">
              <button
                type="button"
                onClick={
                  stageMode === "voice_ingest"
                    ? () => handleChangeStageMode("provenance_brief")
                    : triggerSeeItWorkSequence
                }
                className={`inline-flex items-center justify-center gap-2.5 rounded-full bg-[#f5c418] hover:bg-[#fde047] text-[#111827] font-semibold shadow-[0_14px_34px_rgba(245,196,24,0.38)] transition-all active:scale-[0.99] ${
                  stageMode === "provenance_brief"
                    ? "h-[48px] text-[14px] sm:text-[15px] px-6"
                    : "h-[58px] text-[15px] sm:text-[16.5px] px-7 sm:px-8"
                }`}
                data-testid="see-it-work-cta"
              >
                <span>{heroCopy.primaryCtaLabel}</span>
                <span aria-hidden="true">→</span>
              </button>

              <Link
                href="/signup"
                className={`inline-flex items-center justify-center rounded-full bg-white/10 hover:bg-white/18 backdrop-blur-md border-[1.5px] border-white/55 text-white font-semibold transition-all ${
                  stageMode === "provenance_brief"
                    ? "h-[48px] text-[14px] sm:text-[15px] px-6"
                    : "h-[58px] text-[15px] sm:text-[16.5px] px-7 sm:px-8"
                }`}
                data-testid="hero-book-demo-cta"
              >
                Book a demo
              </Link>
            </div>
          </div>

          {/* FRAME 2 OVERLAY: Incoming Request Voice Note Card + Neon Feed Vector */}
          {stageMode === "voice_ingest" ? (
            <IncomingRequestVoiceCard
              fixture={fixture}
              isScanningDates={isScanningDates}
              onReplayIngest={triggerSeeItWorkSequence}
            />
          ) : null}

          {/* FRAME 3 OVERLAY: Multi-Message Chat Thread + 4 Provenance Wires + Slide-Over Brief Drawer */}
          {stageMode === "provenance_brief" ? (
            <ProvenanceAndBriefOverlay
              fixture={fixture}
              selectedRowId={selectedRowId}
              onSelectRow={(rowId) => setSelectedRowId(rowId)}
              onCloseBrief={() => setStageMode("hero")}
            />
          ) : null}

          {/* FRAME 4 OVERLAY: Bottom Frosted-Glass Inquiry Switcher Dock */}
          <InquirySwitcherDock
            activeInquiryId={activeInquiryId}
            onSelectInquiry={handleSelectInquiry}
            stageMode={stageMode}
            onChangeStageMode={handleChangeStageMode}
            soundEnabled={soundEnabled}
            onToggleSound={handleToggleSound}
            visibleInHero={hasSwitchedInquiry && stageMode === "hero"}
          />
        </div>
      </section>

      {/* =====================================================================
          BELOW THE FOLD: THE WAYPOINT TERMINAL OPERATING SYSTEM
         ===================================================================== */}
      <section
        id="product"
        className="relative py-20 sm:py-28 px-6 sm:px-12 max-w-7xl mx-auto"
      >
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-start">
          <div className="lg:col-span-6 space-y-5">
            <div className="inline-flex items-center gap-2 rounded-full bg-white/10 border border-white/15 px-3.5 py-1 text-[11px] font-mono uppercase tracking-[0.18em] text-[#fde047]">
              <span>Waypoint OS · Intake & Epistemic Gate</span>
            </div>
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight text-white leading-[1.08]">
              Turn raw trip notes into quote-ready briefs
            </h2>
            <p className="text-base sm:text-lg text-slate-300 leading-relaxed">
              Waypoint helps boutique travel agencies turn the notes they already
              have, whether from calls, emails, WhatsApp messages, or copied
              itineraries, into structured trip briefs ready for advisor review.
            </p>
            <div className="pt-2 flex flex-wrap items-center gap-4">
              <Link
                href="/signup"
                className="inline-flex items-center gap-2 rounded-full bg-[#f5c418] hover:bg-[#fde047] text-slate-950 font-semibold text-sm px-6 py-3 shadow-lg transition-all"
              >
                <span>Create workspace</span>
                <span aria-hidden="true">→</span>
              </Link>
              <Link
                href="/workbench"
                className="inline-flex items-center gap-2 rounded-full bg-white/10 hover:bg-white/15 border border-white/20 text-white font-semibold text-sm px-6 py-3 transition-all"
              >
                <span>Open Advisor Workbench</span>
              </Link>
            </div>
          </div>

          <div className="lg:col-span-6 rounded-3xl bg-[#081d52]/90 border border-white/15 p-6 sm:p-8 shadow-2xl space-y-6">
            <div className="flex items-center justify-between border-b border-white/10 pb-4">
              <div>
                <p className="text-xs font-mono uppercase tracking-widest text-[#fde047]">
                  Not a prettier CRM. A faster intake and quoting surface
                </p>
                <h3 className="text-xl font-bold text-white mt-1">
                  It helps teams answer faster, quote cleaner, and keep owners out
                  of every tiny decision
                </h3>
              </div>
              <span className="rounded-lg bg-white/10 px-2.5 py-1 font-mono text-xs font-bold text-white">
                {fixture.tagCode}
              </span>
            </div>

            <ul className="space-y-4">
              <li className="flex items-start gap-3.5 rounded-2xl bg-white/5 border border-white/10 p-4">
                <span className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-[#f5c418] text-slate-950 font-mono text-xs font-bold">
                  01
                </span>
                <div>
                  <p className="font-semibold text-white text-sm sm:text-base">
                    Extract dates, party size, budget, pace, and trip type from
                    messy messages
                  </p>
                  <p className="text-xs sm:text-sm text-slate-300 mt-1">
                    Voice notes, WhatsApp forwards, and email threads resolve
                    directly onto structured departure slots with verbatim quote
                    provenance.
                  </p>
                </div>
              </li>

              <li className="flex items-start gap-3.5 rounded-2xl bg-white/5 border border-white/10 p-4">
                <span className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-[#f5c418] text-slate-950 font-mono text-xs font-bold">
                  02
                </span>
                <div>
                  <p className="font-semibold text-white text-sm sm:text-base">
                    Surface the missing facts that change itinerary quality before
                    anyone quotes
                  </p>
                  <p className="text-xs sm:text-sm text-slate-300 mt-1">
                    Waypoint never invents a travel date. Unconfirmed windows lock
                    onto a signal-yellow epistemic hold until verified.
                  </p>
                </div>
              </li>

              <li className="flex items-start gap-3.5 rounded-2xl bg-white/5 border border-white/10 p-4">
                <span className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-[#f5c418] text-slate-950 font-mono text-xs font-bold">
                  03
                </span>
                <div>
                  <p className="font-semibold text-white text-sm sm:text-base">
                    Protect owner time by showing what needs a human decision and
                    what does not
                  </p>
                  <p className="text-xs sm:text-sm text-slate-300 mt-1">
                    Senior advisors review a clean brief with explicit vs.
                    unconfirmed facts separated before supplier outreach begins.
                  </p>
                </div>
              </li>
            </ul>
          </div>
        </div>
      </section>

      {/* =====================================================================
          SECTION 2: THREE-STAGE MECHANICAL PIPELINE
         ===================================================================== */}
      <section
        id="why-waypoint"
        className="py-16 sm:py-24 px-6 sm:px-12 border-t border-white/10 bg-[#030e2c]"
      >
        <div className="max-w-7xl mx-auto space-y-12">
          <div className="max-w-3xl space-y-3">
            <p className="font-mono text-xs uppercase tracking-[0.2em] text-[#f5c418]">
              Inside the Machine
            </p>
            <h2 className="text-2xl sm:text-4xl font-bold tracking-tight text-white">
              Built like flight operations. Designed for boutique travel desks.
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="rounded-2xl bg-[#071846] border border-white/12 p-6 space-y-3">
              <div className="flex items-center justify-between">
                <span className="font-mono text-xs uppercase tracking-wider text-sky-300">
                  Gate 01 · The Arrivals Hall
                </span>
                <span className="h-2 w-2 rounded-full bg-sky-400" />
              </div>
              <h3 className="text-lg font-bold text-white">
                Multi-channel message ingestion
              </h3>
              <p className="text-sm text-slate-300 leading-relaxed">
                Clients send voice notes at 10:14 AM and follow up with three
                WhatsApp texts. Waypoint threads every signal into a single trip
                record without manual copy-paste.
              </p>
            </div>

            <div className="rounded-2xl bg-[#071846] border border-[#f5c418]/40 p-6 space-y-3">
              <div className="flex items-center justify-between">
                <span className="font-mono text-xs uppercase tracking-wider text-[#fde047]">
                  Gate 02 · Epistemic Hold
                </span>
                <span className="h-2 w-2 rounded-full bg-[#f5c418]" />
              </div>
              <h3 className="text-lg font-bold text-white">
                Zero hallucinated dates or budgets
              </h3>
              <p className="text-sm text-slate-300 leading-relaxed">
                When a traveler says &ldquo;not sure on dates yet,&rdquo; the board
                explicitly flags <strong className="text-[#fde047]">NEED CONFIRMATION</strong> and
                drafts the exact advisor follow-up question.
              </p>
            </div>

            <div className="rounded-2xl bg-[#071846] border border-white/12 p-6 space-y-3">
              <div className="flex items-center justify-between">
                <span className="font-mono text-xs uppercase tracking-wider text-emerald-300">
                  Gate 03 · Ready for Review
                </span>
                <span className="h-2 w-2 rounded-full bg-emerald-400" />
              </div>
              <h3 className="text-lg font-bold text-white">
                One-click brief to workbench handoff
              </h3>
              <p className="text-sm text-slate-300 leading-relaxed">
                Once facts are confirmed, advisors promote the brief straight into
                the Waypoint Workbench with seasonal suitability and route checks.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* =====================================================================
          FOOTER / CTA
         ===================================================================== */}
      <footer
        id="pricing"
        className="py-16 px-6 sm:px-12 border-t border-white/10 bg-[#02091f]"
      >
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-start sm:items-center justify-between gap-8">
          <div className="space-y-2">
            <p className="font-mono text-sm font-black tracking-[0.22em] text-white uppercase">
              WAYPOINT® · FROM MESSAGES TO MEANINGFUL TRAVEL PLANS
            </p>
            <p className="text-sm text-slate-400">
              Interactive Departure Board intake and quoting surface for travel
              advisors.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-4">
            <Link
              href="/signup"
              className="inline-flex items-center gap-2 rounded-full bg-[#f5c418] hover:bg-[#fde047] text-slate-950 font-semibold text-sm px-6 py-2.5 transition-all"
            >
              <span>Create workspace</span>
              <span aria-hidden="true">→</span>
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
