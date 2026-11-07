"use client";

import React, { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import {
  DEPARTURE_INQUIRIES,
  DESTINATION_CATALOG_REGISTRY,
  pickNextCatalogDestination,
  resolveDynamicInquiryFixture,
  type BoardRowId,
  type DepartureInquiryFixture,
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
import { DepartureBoardFolds } from "./DepartureBoardFolds";

export const DepartureBoardLandingPage: React.FC = () => {
  const [activeInquiryId, setActiveInquiryId] = useState<InquiryId>("italy");
  const [customFixture, setCustomFixture] =
    useState<DepartureInquiryFixture | null>(null);
  const [stageMode, setStageMode] = useState<InteractiveStageMode>("hero");
  const [isScanningDates, setIsScanningDates] = useState(false);
  const [isDatesConfirmed, setIsDatesConfirmed] = useState(false);
  const [selectedRowId, setSelectedRowId] = useState<BoardRowId | null>(null);
  const [forceTriggerKey, setForceTriggerKey] = useState(0);
  const [rowForceKeys, setRowForceKeys] = useState<
    Partial<Record<BoardRowId, number>>
  >({});
  const [soundEnabled, setSoundEnabled] = useState(true);
  const [hasSwitchedInquiry, setHasSwitchedInquiry] = useState(false);
  const [isAutoCycling, setIsAutoCycling] = useState(true);
  const [heroCustomInput, setHeroCustomInput] = useState("");

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

  const fixture = customFixture ?? DEPARTURE_INQUIRIES[activeInquiryId];

  /**
   * Triggers the Frame 2 -> Frame 1 -> Frame 3 live ingestion story choreography
   * when clicking "See it work ->" or replaying the voice note.
   */
  const triggerSeeItWorkSequence = useCallback(() => {
    clearScanTimers();
    setStageMode("voice_ingest");
    setIsScanningDates(true);
    setSelectedRowId(null);
    setForceTriggerKey((prev) => prev + 1);
    splitFlapAudio.playConfirmationLatch();
  }, [clearScanTimers]);

  const handleSelectInquiry = useCallback(
    (nextId: InquiryId) => {
      clearScanTimers();
      setCustomFixture(null);
      setActiveInquiryId(nextId);
      setHasSwitchedInquiry(true);
      setIsScanningDates(false);
      setIsDatesConfirmed(false);
      setForceTriggerKey((prev) => prev + 1);
    },
    [clearScanTimers]
  );

  const handleApplyDynamicInquiry = useCallback(
    (rawInput: string) => {
      const trimmed = rawInput.trim();
      if (!trimmed) return;
      clearScanTimers();
      const resolved = resolveDynamicInquiryFixture(trimmed);
      setCustomFixture(resolved);
      setActiveInquiryId(resolved.id);
      setHasSwitchedInquiry(true);
      setIsScanningDates(false);
      setIsDatesConfirmed(false);
      setForceTriggerKey((prev) => prev + 1);
    },
    [clearScanTimers]
  );

  const handleShuffleRandomInquiry = useCallback(
    (
      mode: "random" | "sequential" = "random",
      userInitiated: boolean = false
    ) => {
      clearScanTimers();
      const nextEntry = pickNextCatalogDestination(fixture.pillTitle, mode);
      const resolved = resolveDynamicInquiryFixture(nextEntry.displayName, {
        randomizeNumbers: true,
      });
      setCustomFixture(resolved);
      setActiveInquiryId(resolved.id);
      if (userInitiated) {
        setHasSwitchedInquiry(true);
      }
      setIsScanningDates(stageMode === "voice_ingest");
      setIsDatesConfirmed(false);
      setForceTriggerKey((prev) => prev + 1);
    },
    [clearScanTimers, fixture.pillTitle, stageMode]
  );

  // Built-In Autonomous Multi-Destination & Dynamic Number Rotation Engine
  // Runs continuously by default every 5.5s across all 15 destinations with synchronized randomized numbers.
  useEffect(() => {
    if (!isAutoCycling) return;
    const timer = window.setInterval(() => {
      handleShuffleRandomInquiry("random", false);
    }, 5500);
    return () => window.clearInterval(timer);
  }, [isAutoCycling, handleShuffleRandomInquiry]);

  const handleSelectRow = useCallback((rowId: BoardRowId) => {
    setStageMode("provenance_brief");
    setSelectedRowId(rowId);
    setRowForceKeys((prev) => ({
      ...prev,
      [rowId]: (prev[rowId] ?? 0) + 1,
    }));
    if (rowId === "dates") {
      setIsDatesConfirmed((prev) => !prev);
      splitFlapAudio.playConfirmationLatch();
    }
  }, []);

  const handleToggleDatesConfirmed = useCallback(() => {
    setIsDatesConfirmed((prev) => !prev);
    setRowForceKeys((prev) => ({
      ...prev,
      dates: (prev.dates ?? 0) + 1,
    }));
    splitFlapAudio.playConfirmationLatch();
  }, []);

  const handleChangeStageMode = useCallback(
    (nextMode: InteractiveStageMode) => {
      clearScanTimers();
      setStageMode(nextMode);
      setSelectedRowId(null);
      if (nextMode === "voice_ingest") {
        setIsScanningDates(true);
        setForceTriggerKey((prev) => prev + 1);
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

  const activeCaseSlug = fixture.pillTitle.toLowerCase().replace(/\s+/g, "-");
  const signupCaseHref = `/signup?source=departure-board&case=${encodeURIComponent(activeCaseSlug)}&iata=${encodeURIComponent(fixture.tagCode)}`;
  const workbenchCaseHref = `/workbench?source=departure-board&case=${encodeURIComponent(activeCaseSlug)}&iata=${encodeURIComponent(fixture.tagCode)}&prefill=${encodeURIComponent(fixture.voiceNote.quote.replace(/^[“"]|[”"]$/g, ""))}`;

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
      {/* Keyframe animations for the swinging IATA luggage tag & 3D card flip */}
      <style>{`
        @keyframes tagSwing {
          0% { transform: rotate(11deg); }
          35% { transform: rotate(-7deg); }
          65% { transform: rotate(4deg); }
          85% { transform: rotate(-1.8deg); }
          100% { transform: rotate(0deg); }
        }
        @keyframes cardFlipIn {
          0% {
            opacity: 0.35;
            transform: perspective(1200px) rotateX(-12deg) translateY(6px);
          }
          100% {
            opacity: 1;
            transform: perspective(1200px) rotateX(0deg) translateY(0);
          }
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
            className="pointer-events-none absolute inset-0"
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
                  onClick={(e) => {
                    e.preventDefault();
                    document
                      .getElementById("product")
                      ?.scrollIntoView({ behavior: "smooth" });
                  }}
                  className="inline-flex items-center gap-1 hover:text-white transition-colors"
                >
                  <span>Product</span>
                  <svg viewBox="0 0 12 12" className="h-3 w-3 opacity-70" fill="currentColor">
                    <path d="M2.5 4.5L6 8l3.5-3.5" stroke="currentColor" strokeWidth="1.4" fill="none" />
                  </svg>
                </a>
                <a
                  href="#why-waypoint"
                  onClick={(e) => {
                    e.preventDefault();
                    document
                      .getElementById("why-waypoint")
                      ?.scrollIntoView({ behavior: "smooth" });
                  }}
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
                  onClick={(e) => {
                    e.preventDefault();
                    document
                      .getElementById("pricing")
                      ?.scrollIntoView({ behavior: "smooth" });
                  }}
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
                href={signupCaseHref}
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
            isDatesConfirmed={isDatesConfirmed}
            selectedRowId={selectedRowId}
            onSelectRow={handleSelectRow}
            showProvenanceWires={stageMode === "provenance_brief"}
            forceTriggerKey={forceTriggerKey}
            rowForceKeys={rowForceKeys}
            parallaxOffset={{
              x: 0,
              y: 0,
              rotateY: mouseNorm.x * 0.45,
              rotateX: mouseNorm.y * -0.35,
            }}
          />

          {/* LAYER 3: Foreground Carry-On Suitcase Overlap (1:1 Pixel-Registered with Layer 1 & Layer 2) */}
          {stageMode !== "provenance_brief" ? (
            <div
              className="pointer-events-none absolute inset-0 z-20"
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
          ) : null}

          {/* LAYER 4: Left Cobalt-Blue Editorial Copy & CTAs (Matches Frame 1-4 Typography & Position) */}
          <div
            className="pointer-events-none absolute z-30 flex flex-col justify-start transition-all duration-300"
            style={{
              left: stageMode === "provenance_brief" ? "5.7%" : "7.6%",
              top:
                stageMode === "provenance_brief"
                  ? "11.2%"
                  : stageMode === "hero"
                    ? "11.5%"
                    : "16.0%",
              width: stageMode === "provenance_brief" ? "28.5%" : "32%",
            }}
          >
            <div className="flex items-center gap-3 mb-2 sm:mb-2.5">
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
                  ? "text-[42px] sm:text-[60px] lg:text-[74px] xl:text-[82px] leading-[0.93] mb-3 sm:mb-4"
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
              <p className="text-white/90 font-normal text-[14.5px] sm:text-[17px] lg:text-[18.5px] xl:text-[19.5px] leading-[1.32] max-w-[365px] mb-4">
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
            <div className="pointer-events-auto flex flex-wrap items-center gap-3">
              <button
                type="button"
                onClick={
                  stageMode === "voice_ingest"
                    ? () => handleChangeStageMode("provenance_brief")
                    : stageMode === "provenance_brief"
                      ? () => {
                          if (!isDatesConfirmed) {
                            handleSelectRow("dates");
                          } else {
                            const order: InquiryId[] = [
                              "japan",
                              "morocco",
                              "italy",
                            ];
                            const nextId =
                              order[
                                (order.indexOf(activeInquiryId) + 1) %
                                  order.length
                              ];
                            handleSelectInquiry(nextId);
                          }
                        }
                      : triggerSeeItWorkSequence
                }
                className={`inline-flex items-center justify-center gap-2 rounded-full bg-[#f5c418] hover:bg-[#fde047] text-[#111827] font-semibold whitespace-nowrap shadow-[0_14px_34px_rgba(245,196,24,0.38)] transition-all active:scale-[0.99] ${
                  stageMode === "provenance_brief"
                    ? "h-[42px] sm:h-[48px] text-[13px] sm:text-[15px] px-4 sm:px-6"
                    : "h-[44px] sm:h-[52px] text-[13.5px] sm:text-[15.5px] px-5 sm:px-7"
                }`}
                data-testid="see-it-work-cta"
              >
                <span>{heroCopy.primaryCtaLabel}</span>
                <span aria-hidden="true">→</span>
              </button>

              <Link
                href={signupCaseHref}
                className={`inline-flex items-center justify-center rounded-full bg-white/10 hover:bg-white/18 backdrop-blur-md border-[1.5px] border-white/55 text-white font-semibold transition-all ${
                  stageMode === "provenance_brief"
                    ? "h-[42px] sm:h-[48px] text-[13px] sm:text-[15px] px-4 sm:px-6"
                    : "h-[44px] sm:h-[52px] text-[13.5px] sm:text-[15.5px] px-5 sm:px-7"
                }`}
                data-testid="hero-book-demo-cta"
              >
                Book a demo
              </Link>
            </div>

            {/* Built-In Autonomous Multi-Destination Stream Status & Quick-Select Strip */}
            {stageMode === "hero" ? (
              <div
                className="pointer-events-auto mt-3 rounded-2xl bg-[#071c54]/90 backdrop-blur-md border border-white/20 px-3 py-2 max-w-[440px] shadow-[0_14px_34px_rgba(0,0,0,0.35)] space-y-1.5"
                data-testid="hero-live-destination-strip"
              >
                <div className="flex items-center justify-between gap-2">
                  <button
                    type="button"
                    onClick={() => setIsAutoCycling((prev) => !prev)}
                    className="inline-flex items-center gap-1.5 font-mono text-[9.5px] font-bold uppercase tracking-[0.12em] text-white/95 hover:text-white whitespace-nowrap"
                    data-testid="hero-auto-rotate-toggle"
                  >
                    <span
                      className={`h-2 w-2 rounded-full shrink-0 ${
                        isAutoCycling
                          ? "bg-emerald-400 animate-pulse"
                          : "bg-amber-400"
                      }`}
                    />
                    <span>
                      {isAutoCycling
                        ? "Live · 15 Destinations Auto-Cycling"
                        : "Paused · 15 Destinations"}
                    </span>
                  </button>
                  <span
                    className="rounded-full bg-white/10 border border-white/20 text-[#fde047] font-mono text-[9.5px] font-bold px-2 py-0.5 whitespace-nowrap"
                    data-testid="hero-live-sync-badge"
                  >
                    {fixture.tagCode} · {fixture.briefSummary[1]?.value} · {fixture.briefSummary[2]?.value}
                  </span>
                </div>
                {!hasSwitchedInquiry &&
                mouseNorm.x === 0 &&
                mouseNorm.y === 0 ? (
                  <>
                    <div className="flex flex-wrap items-center gap-1">
                      {DESTINATION_CATALOG_REGISTRY.slice(0, 7).map((entry) => {
                        const isEntryActive =
                          fixture.pillTitle.toLowerCase() ===
                          entry.displayName.toLowerCase();
                        return (
                          <button
                            key={entry.slug}
                            type="button"
                            onClick={() => {
                              if (
                                entry.slug === "italy" ||
                                entry.slug === "japan" ||
                                entry.slug === "morocco"
                              ) {
                                handleSelectInquiry(entry.slug);
                              } else {
                                handleApplyDynamicInquiry(entry.displayName);
                              }
                            }}
                            className={`rounded-md px-1.5 py-0.5 font-mono text-[9.5px] font-bold transition-all ${
                              isEntryActive
                                ? "bg-white text-[#0c2766] shadow-sm"
                                : "bg-white/10 text-white/80 hover:bg-white/20"
                            }`}
                            data-testid={`hero-dest-chip-${entry.slug}`}
                          >
                            {entry.displayName}
                          </button>
                        );
                      })}
                    </div>
                    <form
                      onSubmit={(e) => {
                        e.preventDefault();
                        if (!heroCustomInput.trim()) return;
                        setIsAutoCycling(false);
                        handleApplyDynamicInquiry(heroCustomInput.trim());
                      }}
                      className="flex items-center gap-1.5 pt-1 border-t border-white/15"
                    >
                      <input
                        type="text"
                        value={heroCustomInput}
                        onFocus={() => setIsAutoCycling(false)}
                        onChange={(e) => setHeroCustomInput(e.target.value)}
                        placeholder="Try: 2 travelers for dubai around june next year..."
                        aria-label="Enter any travel inquiry"
                        className="flex-1 rounded-lg bg-white/10 border border-white/20 px-2.5 py-1 text-[11px] text-white placeholder:text-white/55 focus:outline-none focus:border-[#f5c418]"
                        data-testid="hero-custom-inquiry-input"
                      />
                      <button
                        type="submit"
                        className="rounded-lg bg-[#f5c418] hover:bg-[#fde047] text-slate-950 font-mono text-[10px] font-extrabold px-2.5 py-1 transition-colors shrink-0"
                        data-testid="hero-custom-inquiry-submit"
                      >
                        Clack →
                      </button>
                    </form>
                  </>
                ) : null}
              </div>
            ) : null}
          </div>

          {/* FRAME 2 OVERLAY: Incoming Request Voice Note Card + Neon Feed Vector */}
          {stageMode === "voice_ingest" ? (
            <IncomingRequestVoiceCard
              fixture={fixture}
              isScanningDates={isScanningDates}
              onReplayIngest={triggerSeeItWorkSequence}
              onSelectInquiry={handleSelectInquiry}
              onShuffleRandom={() => handleShuffleRandomInquiry("random")}
              onSelectRow={handleSelectRow}
              onLockDatesAndOpenBrief={() => {
                handleChangeStageMode("provenance_brief");
                setSelectedRowId("dates");
              }}
            />
          ) : null}

          {/* FRAME 3 OVERLAY: Multi-Message Chat Thread + 4 Provenance Wires + Slide-Over Brief Drawer */}
          {stageMode === "provenance_brief" ? (
            <ProvenanceAndBriefOverlay
              fixture={fixture}
              selectedRowId={selectedRowId}
              isDatesConfirmed={isDatesConfirmed}
              onSelectRow={handleSelectRow}
              onSelectInquiry={handleSelectInquiry}
              onShuffleRandom={() => handleShuffleRandomInquiry("random")}
              onCloseBrief={() => setStageMode("hero")}
            />
          ) : null}

          {/* FRAME 4 OVERLAY: Bottom Frosted-Glass Inquiry Switcher Dock */}
          <InquirySwitcherDock
            activeInquiryId={activeInquiryId}
            activeDisplayTitle={customFixture?.pillTitle}
            activeDisplaySubtitle={customFixture?.pillTitle ? `${fixture.tagCode} · ${fixture.briefSummary[1]?.value}` : undefined}
            onSelectInquiry={handleSelectInquiry}
            onApplyDynamicInquiry={handleApplyDynamicInquiry}
            onShuffleRandom={() => handleShuffleRandomInquiry("random")}
            isAutoCycling={isAutoCycling}
            onToggleAutoCycle={() => setIsAutoCycling((prev) => !prev)}
            stageMode={stageMode}
            onChangeStageMode={handleChangeStageMode}
            soundEnabled={soundEnabled}
            onToggleSound={handleToggleSound}
            visibleInHero={
              stageMode === "hero" &&
              (hasSwitchedInquiry || mouseNorm.x !== 0 || mouseNorm.y !== 0)
            }
          />
        </div>
      </section>

      {/* =====================================================================
          FOLDS 2, 3, 4 & TERMINAL FOOTER (100% Synchronized Solari Architecture)
         ===================================================================== */}
      <DepartureBoardFolds
        fixture={fixture}
        activeCaseSlug={activeCaseSlug}
        workbenchCaseHref={workbenchCaseHref}
        isAutoCycling={isAutoCycling}
        onToggleAutoCycle={() => setIsAutoCycling((prev) => !prev)}
        isDatesConfirmed={isDatesConfirmed}
        onToggleDatesConfirmed={handleToggleDatesConfirmed}
        selectedRowId={selectedRowId}
        onSelectRow={handleSelectRow}
        onSelectPresetInquiry={handleSelectInquiry}
        onApplyDynamicInquiry={handleApplyDynamicInquiry}
        onTriggerVoiceSequence={triggerSeeItWorkSequence}
        onOpenStageOnHero={handleChangeStageMode}
      />
    </div>
  );
};
