"use client";

import React, { useEffect, useLayoutEffect, useRef, useState } from "react";
import Link from "next/link";
import type {
  BoardRowId,
  DepartureInquiryFixture,
  InquiryId,
} from "./board-fixtures";
import {
  INQUIRY_ORDER,
  DEPARTURE_INQUIRIES,
  DESTINATION_CATALOG_REGISTRY,
} from "./board-fixtures";

export type InteractiveStageMode = "hero" | "voice_ingest" | "provenance_brief";

/**
 * Helper to segment a raw voice quote into interactive highlighted workflow tokens
 * (Destination, Travelers, Duration, Ambiguous Dates, Trip Style) synchronized with voiceProgress.
 */
function escapeRegExp(str: string): string {
  return str.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function buildVoiceWorkflowSegments(
  quote: string,
  pillTitle: string,
  styleSubcopy?: string
): Array<{
  text: string;
  targetRow?: BoardRowId;
  color?: "yellow" | "cyan" | "green" | "amber" | "purple";
  threshold: number;
}> {
  const escapedDest = escapeRegExp(pillTitle.trim() || "Italy");
  const escapedStyleSub = styleSubcopy?.trim()
    ? `|${escapeRegExp(styleSubcopy.trim())}`
    : "";

  const tokenMatchers: Array<{
    regex: RegExp;
    targetRow: BoardRowId;
    color: "yellow" | "cyan" | "green" | "amber" | "purple";
    threshold: number;
  }> = [
    {
      regex: new RegExp(
        `\\b(${escapedDest}|Italy|Japan|Morocco|Dubai|Greece|Switzerland|Peru|Iceland|Kenya|Portugal|Bali|Patagonia|Norway|Maldives|France|Amalfi)\\b`,
        "i"
      ),
      targetRow: "destination",
      color: "yellow",
      threshold: 0.12,
    },
    {
      regex:
        /\b(group of \d+|\d+ travelers?|\d+ travellers?|two of us|\d+ of us|family of \d+|couple|solo traveler)\b/i,
      targetRow: "travelers",
      color: "cyan",
      threshold: 0.08,
    },
    {
      regex: /\b(about \d+ days|\d+ days|\d+ weeks)\b/i,
      targetRow: "duration",
      color: "green",
      threshold: 0.28,
    },
    {
      regex:
        /\b(next spring|autumn foliage, exact dates still open|Still checking November school break dates|still coordinating exact dates|still coordinating dates|exact dates still open|sometime in October|around November|still coordinating|flexible on dates|in (?:January|February|March|April|May|June|July|August|September|October|November|December)(?: next year| 202\d)?)\b/i,
      targetRow: "dates",
      color: "amber",
      threshold: 0.42,
    },
    {
      regex: new RegExp(
        `\\b(Food, history, and some time on the coast|Tokyo, Kyoto, and great culinary spots|Atlas Mountain kasbah, and a luxury Sahara camp|private catamaran in the Cyclades and caldera suites|first-class panoramic rail and Zermatt chalets|Sacred Valley lodges, Hiram Bingham train, and Lima dining|South Coast super-jeep, ice caves, and geothermal retreats|private conservancy safari camps and Masai Mara bush flights|Douro Valley wine quintas, Lisbon, and Comporta coast|Ubud jungle wellness sanctuary and private coastal villa|Torres del Paine luxury estancia and glacier trekking|private fjord cruise, Lofoten cabins, and northern lights|Downtown skyline suites, private desert oasis, and yacht charter|overwater pool villa and private sandbank dining|Paris Left Bank, Provence wine estates, and Riviera coast|culture and coastal time|food, culture, and ryokan|desert camp and Atlas kasbah${escapedStyleSub}|culture|adventure|coastal|food)\\b`,
        "i"
      ),
      targetRow: "tripStyle",
      color: "purple",
      threshold: 0.62,
    },
  ];

  type MatchSpan = {
    start: number;
    end: number;
    text: string;
    targetRow: BoardRowId;
    color: "yellow" | "cyan" | "green" | "amber" | "purple";
    threshold: number;
  };

  const spans: MatchSpan[] = [];
  for (const m of tokenMatchers) {
    const match = m.regex.exec(quote);
    if (match && match.index !== undefined) {
      const start = match.index;
      const end = start + match[0].length;
      if (!spans.some((s) => start < s.end && end > s.start)) {
        spans.push({
          start,
          end,
          text: match[0],
          targetRow: m.targetRow,
          color: m.color,
          threshold: m.threshold,
        });
      }
    }
  }
  spans.sort((a, b) => a.start - b.start);

  const result: Array<{
    text: string;
    targetRow?: BoardRowId;
    color?: "yellow" | "cyan" | "green" | "amber" | "purple";
    threshold: number;
  }> = [];
  let cursor = 0;
  for (const s of spans) {
    if (s.start > cursor) {
      result.push({ text: quote.slice(cursor, s.start), threshold: 0 });
    }
    result.push({
      text: s.text,
      targetRow: s.targetRow,
      color: s.color,
      threshold: s.threshold,
    });
    cursor = s.end;
  }
  if (cursor < quote.length) {
    result.push({ text: quote.slice(cursor), threshold: 0 });
  }
  return result;
}

/**
 * Frame 2 Overlay: Floating glassmorphic "Incoming request · 10:14 AM" card
 * positioned at the upper-middle-left (between headline and departure board)
 * with playable 0:24 voice-note waveform, live token extraction highlights,
 * destination voice switcher, and glowing cyan feed vector into Row 4 (DATES).
 */
export const IncomingRequestVoiceCard: React.FC<{
  fixture: DepartureInquiryFixture;
  isScanningDates: boolean;
  onReplayIngest: () => void;
  onSelectInquiry?: (id: InquiryId) => void;
  onShuffleRandom?: () => void;
  onSelectRow?: (rowId: BoardRowId) => void;
  onLockDatesAndOpenBrief?: () => void;
}> = ({
  fixture,
  isScanningDates,
  onReplayIngest,
  onSelectInquiry,
  onSelectRow,
  onLockDatesAndOpenBrief,
}) => {
  const [isPlayingVoice, setIsPlayingVoice] = useState(false);
  const [voiceProgress, setVoiceProgress] = useState(0.72);

  useEffect(() => {
    // When switching destination in Frame 2, animate the voice extraction progress from 0 -> 1
    setVoiceProgress(0.15);
    setIsPlayingVoice(true);
  }, [fixture.pillTitle, fixture.voiceNote.quote]);

  useEffect(() => {
    if (!isPlayingVoice) return;
    const start = performance.now();
    const durationMs = 2600;
    const interval = window.setInterval(() => {
      const elapsed = performance.now() - start;
      const next = Math.min(1, 0.15 + (elapsed / durationMs) * 0.85);
      setVoiceProgress(next);
      if (next >= 1) {
        setIsPlayingVoice(false);
        window.clearInterval(interval);
      }
    }, 50);
    return () => window.clearInterval(interval);
  }, [isPlayingVoice, fixture.pillTitle, fixture.voiceNote.quote]);

  const handleTogglePlay = () => {
    if (!isPlayingVoice) {
      setVoiceProgress(0);
      setIsPlayingVoice(true);
      onReplayIngest();
    } else {
      setIsPlayingVoice(false);
    }
  };

  const workflowSegments = buildVoiceWorkflowSegments(
    fixture.voiceNote.quote,
    fixture.pillTitle,
    fixture.briefSummary[4]?.subtitle
  );

  const tokenColorClasses: Record<string, string> = {
    yellow: "bg-[#fde047]/90 text-slate-950 font-semibold px-1 rounded",
    cyan: "bg-[#bae6fd]/90 text-slate-950 font-semibold px-1 rounded",
    green: "bg-[#bbf7d0]/90 text-slate-950 font-semibold px-1 rounded",
    amber:
      "bg-[#fbbf24] text-slate-950 font-bold px-1 rounded ring-1 ring-white/70",
    purple: "bg-[#e9d5ff]/90 text-slate-950 font-semibold px-1 rounded",
  };

  return (
    <>
      {/* Glowing Cyan/Blue Neon Feed Arrow from Bottom of Voice Card into Row 4 (DATES) */}
      <svg
        viewBox="0 0 1672 941"
        className="pointer-events-none absolute inset-0 w-full h-full z-20"
        preserveAspectRatio="none"
        aria-hidden="true"
      >
        <defs>
          <linearGradient id="ingest-arrow-grad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#93c5fd" stopOpacity="0.65" />
            <stop offset="60%" stopColor="#60a5fa" stopOpacity="0.95" />
            <stop offset="100%" stopColor="#dbeafe" stopOpacity="1" />
          </linearGradient>
          <filter id="ingest-glow" x="-25%" y="-25%" width="150%" height="150%">
            <feGaussianBlur stdDeviation="4.5" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>
        {/* Right-edge cyan connector bracket from Voice Card to Board Frame */}
        <path
          d="M 715 418 L 728 418 Q 734 418 734 426 L 734 438"
          fill="none"
          stroke="#93c5fd"
          strokeWidth="2.8"
          strokeLinecap="round"
          filter="url(#ingest-glow)"
        />
        <path
          d="M 584 484 C 584 528, 616 546, 666 548"
          fill="none"
          stroke="url(#ingest-arrow-grad)"
          strokeWidth="3.5"
          strokeLinecap="round"
          filter="url(#ingest-glow)"
        />
        <path
          d="M 656 540 L 671 548 L 655 556"
          fill="none"
          stroke="#dbeafe"
          strokeWidth="3.2"
          strokeLinecap="round"
          strokeLinejoin="round"
          filter="url(#ingest-glow)"
        />
      </svg>

      {/* Glassmorphic Incoming Request Card (Upper-Middle-Left, Matching Frame 2 Exact 435..715 x 232..484 Bounds) */}
      <div
        key={`voice-card-${fixture.pillTitle}`}
        className="pointer-events-auto absolute z-30 flex flex-col justify-between rounded-[18px] bg-[#163d82]/78 backdrop-blur-xl border border-[#93c5fd]/55 p-4 text-white shadow-[0_24px_60px_rgba(3,12,38,0.6),0_0_28px_rgba(96,165,250,0.22),inset_0_1px_1px_rgba(255,255,255,0.35)] animate-[cardFlipIn_360ms_cubic-bezier(0.22,1,0.36,1)]"
        style={{
          left: `${(435 / 1672) * 100}%`,
          top: `${(232 / 941) * 100}%`,
          width: `${(280 / 1672) * 100}%`,
          height: `${(252 / 941) * 100}%`,
          minWidth: "268px",
        }}
        data-testid="incoming-request-voice-card"
      >
        <div className="flex items-center justify-between text-[12px] text-white/95">
          <div className="flex items-center gap-2">
            <svg
              viewBox="0 0 20 20"
              className="h-4 w-4 text-[#bae6fd] shrink-0"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.7"
            >
              <rect x="2.5" y="4.5" width="15" height="11" rx="2" />
              <path d="M3 5.5l7 5 7-5" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            <span className="font-semibold text-white">Incoming request</span>
          </div>
          <span className="text-[11.5px] text-white/80 font-medium">
            {fixture.voiceNote.timestamp}
          </span>
          {isScanningDates ? (
            <span className="sr-only">Extracting</span>
          ) : (
            <span className="sr-only">Parsed</span>
          )}
        </div>

        <p className="text-[13px] sm:text-[13.5px] leading-[1.36] text-white/95 font-normal line-clamp-5">
          &ldquo;
          {workflowSegments.map((seg, i) => {
            const isHighlighted =
              seg.targetRow && seg.color && voiceProgress >= seg.threshold;
            if (isHighlighted && seg.targetRow && seg.color) {
              return (
                <button
                  key={i}
                  type="button"
                  onClick={() => onSelectRow?.(seg.targetRow!)}
                  className={`inline transition-all duration-200 hover:scale-105 ${
                    tokenColorClasses[seg.color]
                  }`}
                  title={`Extracted ${seg.targetRow} — Click to inspect`}
                >
                  {seg.text}
                </button>
              );
            }
            return <span key={i}>{seg.text}</span>;
          })}
          &rdquo;
        </p>

        {/* Playable Voice Note Waveform Row (Top Border + Ice-Blue Play Button + Glowing Cyan Bars) */}
        <div className="flex items-center gap-2.5 border-t border-white/20 pt-2">
          <button
            type="button"
            onClick={handleTogglePlay}
            aria-label={isPlayingVoice ? "Pause voice note" : "Replay voice note"}
            className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-[#dbeafe] text-[#0c2766] hover:bg-white transition-colors shadow-sm"
            data-testid="voice-note-play-button"
          >
            {isPlayingVoice ? (
              <svg viewBox="0 0 16 16" className="h-3.5 w-3.5" fill="currentColor">
                <rect x="3.5" y="3" width="3" height="10" rx="0.8" />
                <rect x="9.5" y="3" width="3" height="10" rx="0.8" />
              </svg>
            ) : (
              <svg viewBox="0 0 16 16" className="h-3.5 w-3.5 ml-0.5" fill="currentColor">
                <path d="M4 2.8l9.2 5.2L4 13.2V2.8z" />
              </svg>
            )}
          </button>

          <div className="relative flex-1 flex items-center gap-[2px] h-5">
            <div className="pointer-events-none absolute inset-x-0 top-1/2 -translate-y-1/2 h-[1px] bg-[#93c5fd]/45" />
            {fixture.voiceNote.waveformHeights.map((h, i) => {
              const pct = i / fixture.voiceNote.waveformHeights.length;
              const active = pct <= voiceProgress;
              return (
                <span
                  key={i}
                  className={`relative z-10 flex-1 rounded-full transition-all duration-150 ${
                    active
                      ? "bg-[#bae6fd] shadow-[0_0_6px_rgba(186,230,253,0.65)]"
                      : "bg-white/35"
                  }`}
                  style={{
                    height: `${Math.max(20, Math.round(h * 100))}%`,
                  }}
                />
              );
            })}
          </div>

          <span className="text-[11.5px] font-medium text-[#dbeafe] shrink-0">
            {fixture.voiceNote.durationLabel}
          </span>
        </div>
      </div>

      {/* Live Epistemic Workflow Status & Voice Note Destination Switcher Pill Strip (Docked cleanly above Voice Card at y=160..222) */}
      <div
        className="pointer-events-auto absolute z-30 flex flex-col gap-1 rounded-xl bg-[#0b2154]/92 backdrop-blur-md border border-[#fde047]/50 px-3 py-1.5 text-white shadow-[0_10px_24px_rgba(0,0,0,0.4)]"
        style={{
          left: `${(435 / 1672) * 100}%`,
          top: `${(162 / 941) * 100}%`,
          width: `${(280 / 1672) * 100}%`,
          minWidth: "268px",
        }}
        data-testid="voice-workflow-status-card"
      >
        <div className="flex items-center justify-between gap-2">
          <span
            className="inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider text-[#fde047] shrink-0"
            title="4/5 slots extracted · Ambiguous date window holds Row 4 until advisor confirms"
          >
            <span>⚠️ Dates Need Clarity</span>
          </span>
          <span className="sr-only">
            4/5 slots extracted · Ambiguous date window holds Row 4 until advisor
            confirms.
          </span>
          {onLockDatesAndOpenBrief ? (
            <button
              type="button"
              onClick={onLockDatesAndOpenBrief}
              className="shrink-0 rounded-full bg-[#f5c418] hover:bg-[#fde047] text-slate-950 font-bold text-[9.5px] px-2.5 py-0.5 transition-colors"
              data-testid="voice-lock-brief-button"
            >
              Lock & Brief →
            </button>
          ) : null}
        </div>
        {onSelectInquiry ? (
          <div className="flex items-center justify-between gap-1 pt-1 border-t border-white/15">
            <span className="text-[9.5px] font-medium text-white/70">
              Voice ({fixture.pillTitle}):
            </span>
            <div className="flex items-center gap-1">
              {INQUIRY_ORDER.map((id) => {
                const active =
                  fixture.pillTitle.toLowerCase() ===
                  DEPARTURE_INQUIRIES[id].pillTitle.toLowerCase();
                return (
                  <button
                    key={id}
                    type="button"
                    onClick={() => onSelectInquiry(id)}
                    className={`rounded-full px-1.5 py-0.5 text-[9.5px] font-semibold transition-all ${
                      active
                        ? "bg-white text-[#0c2766]"
                        : "bg-white/10 text-white/80 hover:bg-white/20"
                    }`}
                    data-testid={`voice-switch-${id}`}
                  >
                    {DEPARTURE_INQUIRIES[id].pillTitle}
                  </button>
                );
              })}
              <span className="inline-flex items-center gap-1 rounded-full bg-emerald-400/15 border border-emerald-300/35 px-1.5 py-0.5 text-[9px] font-semibold text-emerald-200">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
                <span>Live</span>
              </span>
            </div>
          </div>
        ) : null}
      </div>
    </>
  );
};

/**
 * Frame 3 Overlay:
 * 1) Bottom-left glass container ("Incoming inquiry · Today, 9:14 AM") with 4 light frosted white chat bubbles
 * 2) 4 solid glowing SVG provenance wires routing up the left margin of the board into circular ports on the category plates
 * 3) Right-side pearl-white brief drawer ("From message to brief") with category icons, thumbnails, and badges
 */
export const ProvenanceAndBriefOverlay: React.FC<{
  fixture: DepartureInquiryFixture;
  selectedRowId: BoardRowId | null;
  isDatesConfirmed?: boolean;
  onSelectRow: (rowId: BoardRowId) => void;
  onSelectInquiry?: (id: InquiryId) => void;
  onShuffleRandom?: () => void;
  onCloseBrief: () => void;
}> = ({
  fixture,
  selectedRowId,
  isDatesConfirmed = false,
  onSelectRow,
  onSelectInquiry,
  onShuffleRandom,
  onCloseBrief,
}) => {
  const overlayRootRef = useRef<HTMLDivElement>(null);
  const [measuredOrigins, setMeasuredOrigins] = useState<
    Partial<Record<BoardRowId, { x: number; y: number }>>
  >({});

  // Measure live DOM positions of the highlighted chat pills inside the 1672x941 stage
  // so every provenance wire originates directly at its highlighted chat phrase!
  useLayoutEffect(() => {
    const root = overlayRootRef.current;
    if (!root) return;

    const measure = () => {
      const rootRect = root.getBoundingClientRect();
      if (rootRect.width <= 0 || rootRect.height <= 0) return;

      const next: Partial<Record<BoardRowId, { x: number; y: number }>> = {};
      const rows: BoardRowId[] = [
        "destination",
        "travelers",
        "duration",
        "dates",
        "tripStyle",
      ];
      for (const rId of rows) {
        const el = root.querySelector<HTMLElement>(
          `[data-wire-origin="${rId}"]`
        );
        if (el) {
          const rect = el.getBoundingClientRect();
          const x = ((rect.right - rootRect.left) / rootRect.width) * 1672 + 4;
          const y =
            ((rect.top + rect.height * 0.5 - rootRect.top) / rootRect.height) *
            941;
          next[rId] = { x: Math.round(x), y: Math.round(y) };
        }
      }
      setMeasuredOrigins(next);
    };

    measure();
    const t = window.setTimeout(measure, 60);
    if (typeof ResizeObserver !== "undefined") {
      const ro = new ResizeObserver(measure);
      ro.observe(root);
      return () => {
        window.clearTimeout(t);
        ro.disconnect();
      };
    }
    window.addEventListener("resize", measure);
    return () => {
      window.clearTimeout(t);
      window.removeEventListener("resize", measure);
    };
  }, [fixture.pillTitle, selectedRowId]);

  const buildWireSpec = (
    rowId: BoardRowId,
    color: string,
    fallbackStart: [number, number],
    busX: number,
    endY: number
  ) => {
    const origin = measuredOrigins[rowId];
    const startX = origin ? origin.x : fallbackStart[0];
    const startY = origin ? origin.y : fallbackStart[1];
    const endX = 618;
    const midY = startY + (endY - startY) * 0.18;
    const d = `M ${startX} ${startY} L ${busX} ${startY} C ${busX + 26} ${startY}, ${busX + 46} ${midY}, 574 ${endY + 18} C 582 ${endY + 2}, 596 ${endY}, ${endX} ${endY}`;
    return { rowId, color, startX, startY, endX, endY, d };
  };

  // Exact slanted-bus glowing wire paths routing directly from the highlighted chat phrases
  // out of the bubbles and into the circular ports on the 4 Frame 3 category plates (endX=618)
  const wirePaths: Array<{
    rowId: BoardRowId;
    color: string;
    d: string;
    startX: number;
    startY: number;
    endX: number;
    endY: number;
  }> = [
    buildWireSpec("destination", "#fde047", [318, 560], 496, 348),
    buildWireSpec("travelers", "#38bdf8", [308, 582], 504, 424),
    buildWireSpec("duration", "#4ade80", [254, 650], 512, 500),
    ...(selectedRowId === "dates"
      ? [buildWireSpec("dates", "#fbbf24", [386, 650], 516, 582)]
      : []),
    buildWireSpec("tripStyle", "#d8b4fe", [406, 742], 520, 663),
  ];

  const highlightStyles: Record<string, string> = {
    yellow:
      "bg-[#fde047] text-[#111827] border border-[#f59e0b]/40 shadow-[0_1px_4px_rgba(245,196,24,0.35)]",
    cyan: "bg-[#bae6fd] text-[#0c4a6e] border border-[#38bdf8]/40 shadow-[0_1px_4px_rgba(56,189,248,0.28)]",
    green:
      "bg-[#bbf7d0] text-[#064e3b] border border-[#4ade80]/40 shadow-[0_1px_4px_rgba(74,222,128,0.28)]",
    purple:
      "bg-[#e9d5ff] text-[#4c1d95] border border-[#c084fc]/40 shadow-[0_1px_4px_rgba(192,132,252,0.28)]",
  };

  const rowAccentRing: Record<BoardRowId, string> = {
    destination: "ring-2 ring-[#fde047] shadow-[0_0_14px_rgba(253,224,71,0.75)] scale-105",
    travelers: "ring-2 ring-[#38bdf8] shadow-[0_0_14px_rgba(56,189,248,0.75)] scale-105",
    duration: "ring-2 ring-[#4ade80] shadow-[0_0_14px_rgba(74,222,128,0.75)] scale-105",
    dates: "ring-2 ring-[#fbbf24] shadow-[0_0_14px_rgba(251,191,36,0.75)] scale-105",
    tripStyle: "ring-2 ring-[#d8b4fe] shadow-[0_0_14px_rgba(216,180,254,0.75)] scale-105",
  };

  const renderBriefRowIcon = (rowId: BoardRowId) => {
    switch (rowId) {
      case "destination":
        return (
          <svg viewBox="0 0 20 20" className="h-5 w-5 text-[#1d4ed8]" fill="currentColor">
            <path
              fillRule="evenodd"
              d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z"
              clipRule="evenodd"
            />
          </svg>
        );
      case "travelers":
        return (
          <svg viewBox="0 0 20 20" className="h-5 w-5 text-[#1d4ed8]" fill="currentColor">
            <path d="M9 6a3 3 0 11-6 0 3 3 0 016 0zM17 6a3 3 0 11-6 0 3 3 0 016 0zM12.93 17c.046-.327.07-.66.07-1a6.97 6.97 0 00-1.5-4.33A5 5 0 0119 16v1h-6.07zM6 11a5 5 0 015 5v1H1v-1a5 5 0 015-5z" />
          </svg>
        );
      case "duration":
      case "dates":
        return (
          <svg viewBox="0 0 20 20" className="h-5 w-5 text-[#1d4ed8]" fill="currentColor">
            <path
              fillRule="evenodd"
              d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z"
              clipRule="evenodd"
            />
          </svg>
        );
      case "tripStyle":
        return (
          <svg viewBox="0 0 20 20" className="h-5 w-5 text-[#1d4ed8]" fill="currentColor">
            <path
              fillRule="evenodd"
              d="M6 6V5a3 3 0 013-3h2a3 3 0 013 3v1h2a2 2 0 012 2v3.57A22.952 22.952 0 0110 13a22.95 22.95 0 01-8-1.43V8a2 2 0 012-2h2zm2-1a1 1 0 011-1h2a1 1 0 011 1v1H8V5zm1 5a1 1 0 011-1h.01a1 1 0 110 2H10a1 1 0 01-1-1z"
              clipRule="evenodd"
            />
            <path d="M2 13.692V16a2 2 0 002 2h12a2 2 0 002-2v-2.308A24.974 24.974 0 0110 15c-2.796 0-5.487-.46-8-1.308z" />
          </svg>
        );
    }
  };

  const bubbleWidthClasses = [
    "w-[85%]",
    "w-[83%]",
    "w-[77%]",
    "w-[82%] ml-auto",
  ];

  // Track which wire origins have already been assigned to the first matching pill in the chat thread
  const assignedOrigins = new Set<BoardRowId>();

  return (
    <div ref={overlayRootRef} className="pointer-events-none absolute inset-0">
      {/* SVG Provenance Wires rendered at z-[35] (above chat bubbles, matching GT Frame 3) */}
      <svg
        viewBox="0 0 1672 941"
        className="pointer-events-none absolute inset-0 w-full h-full z-[35]"
        preserveAspectRatio="none"
        data-testid="provenance-svg-wires"
      >
        <defs>
          <filter id="wire-neon-glow" x="-25%" y="-25%" width="150%" height="150%">
            <feGaussianBlur stdDeviation="3.2" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>
        {wirePaths.map((wire) => {
          const isSelectedWire = selectedRowId === wire.rowId;
          const isFocused = !selectedRowId || isSelectedWire;
          return (
            <g
              key={wire.rowId}
              style={{ opacity: isFocused ? 1 : 0.16 }}
              className="transition-opacity duration-200"
            >
              <path
                d={wire.d}
                fill="none"
                stroke={wire.color}
                strokeWidth={isSelectedWire ? "3.8" : "2.5"}
                strokeLinecap="round"
                strokeLinejoin="round"
                filter="url(#wire-neon-glow)"
              />
              {/* Origin Node next to Highlighted Chat Phrase */}
              <circle
                cx={wire.startX}
                cy={wire.startY}
                r={isSelectedWire ? "4" : "2.5"}
                fill={wire.color}
                filter="url(#wire-neon-glow)"
              />
              {/* Glowing Circular Port on Left Edge of Category Plate */}
              <circle
                cx={wire.endX}
                cy={wire.endY}
                r={isSelectedWire ? "5.2" : "4"}
                fill={wire.color}
                stroke="#ffffff"
                strokeWidth="1.5"
                filter="url(#wire-neon-glow)"
              />
            </g>
          );
        })}
      </svg>

      {/* Bottom-Left Frosted Container ("Incoming inquiry" / "Today, 9:14 AM") with 4 Staggered White Chat Bubbles */}
      <div
        key={`chat-thread-${fixture.pillTitle}`}
        className="pointer-events-auto absolute z-30 flex flex-col justify-between rounded-[18px] bg-[#1a3875]/62 backdrop-blur-xl border border-[#93c5fd]/40 p-3.5 sm:p-4 text-white shadow-[0_22px_50px_rgba(3,10,28,0.6),inset_0_1px_1px_rgba(255,255,255,0.28)] animate-[cardFlipIn_340ms_cubic-bezier(0.22,1,0.36,1)]"
        style={{
          left: `${(96 / 1672) * 100}%`,
          top: `${(478 / 941) * 100}%`,
          width: `${(400 / 1672) * 100}%`,
          height: `${(394 / 941) * 100}%`,
          minWidth: "310px",
        }}
        data-testid="provenance-chat-thread"
      >
        {/* Container Header Bar */}
        <div className="flex items-center justify-between px-1 pb-1.5 text-[12px]">
          <div className="flex items-center gap-2">
            <svg
              viewBox="0 0 20 20"
              className="h-4 w-4 text-white/90 shrink-0"
              fill="currentColor"
            >
              <path d="M2.003 5.884L10 9.882l7.997-3.998A2 2 0 0016 4H4a2 2 0 00-1.997 1.884z" />
              <path d="M18 8.118l-8 4-8-4V14a2 2 0 002 2h12a2 2 0 002-2V8.118z" />
            </svg>
            <span className="font-semibold text-white">Incoming inquiry</span>
          </div>
          <span className="text-[11px] text-white/75 font-medium">
            Today, {fixture.chatThread[0]?.timestamp ?? "9:14 AM"}
          </span>
        </div>

        {/* 4 Staggered Light Frosted White Speech Bubbles */}
        <div className="flex-1 flex flex-col justify-between gap-2">
          {fixture.chatThread.map((msg, msgIdx) => {
            const bubbleHasSelectedTarget =
              selectedRowId &&
              (msg.segments.some(
                (s) => s.highlight?.targetRow === selectedRowId
              ) ||
                (selectedRowId === "dates" && msgIdx === 1));
            const isDimmedBubble =
              Boolean(selectedRowId) && !bubbleHasSelectedTarget;

            const registerTripStyleBubbleOrigin =
              msgIdx === 2 && !assignedOrigins.has("tripStyle");
            if (registerTripStyleBubbleOrigin) {
              assignedOrigins.add("tripStyle");
            }

            return (
              <div
                key={msg.id}
                data-wire-origin={
                  registerTripStyleBubbleOrigin ? "tripStyle" : undefined
                }
                className={`rounded-xl bg-[#eef3fb]/95 border px-3 py-2 text-[#1e293b] shadow-[0_4px_12px_rgba(5,15,40,0.18)] transition-all duration-200 ${
                  bubbleWidthClasses[msgIdx] ?? "w-[85%]"
                } ${
                  bubbleHasSelectedTarget
                    ? "border-[#fde047] ring-2 ring-[#fde047]/65 bg-white"
                    : "border-white/90"
                } ${isDimmedBubble ? "opacity-55" : "opacity-100"}`}
              >
                <div className="flex items-end justify-between gap-2 text-[11.5px] sm:text-[12px] leading-[1.36]">
                  <div>
                    {msg.segments.map((seg, idx) => {
                      if (seg.highlight) {
                        const tRow = seg.highlight.targetRow;
                        const isFirstForRow =
                          tRow !== "tripStyle" && !assignedOrigins.has(tRow);
                        if (isFirstForRow) {
                          assignedOrigins.add(tRow);
                        }
                        const isSelectedPill = selectedRowId === tRow;
                        return (
                          <button
                            key={idx}
                            type="button"
                            data-wire-origin={isFirstForRow ? tRow : undefined}
                            data-testid={`chat-pill-${tRow}-${msgIdx}-${idx}`}
                            onClick={() => onSelectRow(tRow)}
                            className={`inline-flex items-center rounded px-1.5 py-0.2 mx-0.5 font-bold text-[11px] sm:text-[11.5px] transition-all hover:scale-105 ${
                              highlightStyles[seg.highlight.color]
                            } ${isSelectedPill ? rowAccentRing[tRow] : ""}`}
                          >
                            {seg.text}
                          </button>
                        );
                      }
                      const isDatesFallback =
                        msgIdx === 1 && !assignedOrigins.has("dates");
                      if (isDatesFallback) {
                        assignedOrigins.add("dates");
                      }
                      return (
                        <span
                          key={idx}
                          data-wire-origin={isDatesFallback ? "dates" : undefined}
                          onClick={
                            msgIdx === 1 ? () => onSelectRow("dates") : undefined
                          }
                          className={`text-[#1e293b] font-medium ${
                            msgIdx === 1
                              ? "cursor-pointer hover:underline decoration-[#d97706]"
                              : ""
                          } ${
                            selectedRowId === "dates" && msgIdx === 1
                              ? "bg-[#fef3c7] text-[#92400e] font-bold px-1 rounded"
                              : ""
                          }`}
                        >
                          {seg.text}
                        </span>
                      );
                    })}
                  </div>
                  <span className="text-[9.5px] font-sans text-slate-400 shrink-0">
                    {msg.timestamp}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Right-Hand Slide-Over Pearl-White Structured Brief Drawer ("From message to brief") */}
      <aside
        className="pointer-events-auto absolute z-30 flex flex-col justify-between rounded-[24px] bg-[#f8fafc] border border-white p-5 sm:p-5.5 text-slate-900 shadow-[0_28px_70px_rgba(4,10,28,0.62)] transition-all duration-300"
        style={{
          left: `${(1249 / 1672) * 100}%`,
          top: `${(162 / 941) * 100}%`,
          width: `${(375 / 1672) * 100}%`,
          height: `${(622 / 941) * 100}%`,
          minWidth: "320px",
          transform: "perspective(1600px) rotateY(-4.5deg) skewY(-1.15deg)",
          transformOrigin: "left center",
        }}
        aria-label="From message to brief"
        data-testid="structured-brief-drawer"
      >
        <div>
          <div className="flex items-start justify-between gap-2 mb-1.5">
            <div className="flex items-center gap-2">
              <svg
                viewBox="0 0 20 20"
                className="h-4 w-4 text-[#2563eb] shrink-0"
                fill="currentColor"
                aria-hidden="true"
              >
                <path d="M10 2l2.1 5.9L18 10l-5.9 2.1L10 18l-2.1-5.9L2 10l5.9-2.1L10 2z" />
              </svg>
              <h3 className="text-[19px] sm:text-[20px] font-bold tracking-tight text-[#0f172a]">
                From message to brief
              </h3>
            </div>
            <div className="flex items-center gap-1">
              {onSelectInquiry ? (
                <div className="flex items-center gap-0.5 rounded-full bg-slate-200/80 p-0.5 mr-1">
                  {INQUIRY_ORDER.map((id) => {
                    const active =
                      fixture.pillTitle.toLowerCase() ===
                      DEPARTURE_INQUIRIES[id].pillTitle.toLowerCase();
                    return (
                      <button
                        key={id}
                        type="button"
                        onClick={() => onSelectInquiry(id)}
                        className={`rounded-full px-2 py-0.5 text-[10px] font-bold transition-all ${
                          active
                            ? "bg-[#0f296b] text-white shadow-sm"
                            : "text-slate-600 hover:text-slate-900"
                        }`}
                        data-testid={`brief-switch-${id}`}
                      >
                        {DEPARTURE_INQUIRIES[id].pillTitle}
                      </button>
                    );
                  })}
                  <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/15 px-2 py-0.5 text-[9.5px] font-bold text-emerald-800">
                    <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
                    <span>Live</span>
                  </span>
                </div>
              ) : null}
              <button
                type="button"
                onClick={onCloseBrief}
                aria-label="Close brief drawer"
                className="rounded-full p-1 text-slate-400 hover:bg-slate-200/70 hover:text-slate-600 transition-colors"
              >
                <svg viewBox="0 0 20 20" className="h-4 w-4" fill="currentColor">
                  <path
                    fillRule="evenodd"
                    d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                    clipRule="evenodd"
                  />
                </svg>
              </button>
            </div>
          </div>

          <p className="text-[12.5px] text-slate-600 leading-[1.38] mb-3">
            Waypoint automatically finds key details, fills what it can, and flags
            what&apos;s missing, so you can send a polished quote faster.
          </p>
        </div>

        {/* 5 Rounded White Row Cards with Icons, Subtitles, Photo Thumbnails, and 3D Card-Flip on Destination Switch */}
        <div
          key={`brief-cards-${fixture.pillTitle}`}
          className="flex-1 flex flex-col justify-between gap-2 min-h-0 animate-[cardFlipIn_360ms_cubic-bezier(0.22,1,0.36,1)]"
        >
          {fixture.briefSummary.map((item) => {
            const isRowSelected = selectedRowId === item.rowId;
            const isTripStyleRow = item.rowId === "tripStyle";
            const isDatesCard = item.rowId === "dates";
            const rowSpec = fixture.rows.find((r) => r.id === item.rowId);
            const effectiveStatus =
              isDatesCard && isDatesConfirmed ? "confirmed" : item.status;
            const effectiveValue =
              isDatesCard && isDatesConfirmed
                ? rowSpec?.confirmedValueLabel ?? "Apr 18 – Apr 27 (Confirmed)"
                : item.value;

            return (
              <button
                key={item.label}
                type="button"
                onClick={() => onSelectRow(item.rowId)}
                data-testid={`brief-card-${item.rowId}`}
                className={`w-full rounded-xl bg-white border px-3.5 py-2.5 flex items-center justify-between gap-3 text-left transition-all shadow-[0_1px_3px_rgba(15,23,42,0.04)] ${
                  isRowSelected
                    ? "border-[#2563eb] ring-2 ring-[#2563eb]/20 bg-blue-50/40"
                    : "border-slate-200/80 hover:border-slate-300"
                }`}
              >
                <div className="flex items-center gap-3 min-w-0">
                  <span className="flex h-6 w-6 shrink-0 items-center justify-center">
                    {renderBriefRowIcon(item.rowId)}
                  </span>
                  <div className="min-w-0">
                    <div className="flex items-center gap-1.5">
                      <span className="block text-[12px] font-bold text-slate-800 leading-tight">
                        {item.label}
                      </span>
                      {isRowSelected ? (
                        <span className="rounded bg-[#dbeafe] px-1.5 py-0.2 text-[9.5px] font-bold text-[#1d4ed8]">
                          {isDatesCard
                            ? isDatesConfirmed
                              ? "Click to unconfirm"
                              : "Click to confirm"
                            : "Verified on board"}
                        </span>
                      ) : null}
                    </div>
                    {effectiveStatus === "needs_confirmation" ? (
                      <span className="mt-1 inline-flex items-center gap-1.5 rounded-full bg-[#fef3c7] border border-[#fde68a] px-2.5 py-0.5 text-[11.5px] font-semibold text-[#92400e]">
                        <svg
                          viewBox="0 0 16 16"
                          className="h-3.5 w-3.5 text-[#d97706] shrink-0"
                          fill="currentColor"
                          aria-hidden="true"
                        >
                          <path d="M8.865 1.52c-.38-.68-1.35-.68-1.73 0L1.14 12.24c-.37.66.11 1.48.865 1.48h11.99c.755 0 1.235-.82.865-1.48L8.865 1.52zM8 5a.75.75 0 01.75.75v3a.75.75 0 01-1.5 0v-3A.75.75 0 018 5zm0 6.75a.85.85 0 100-1.7.85.85 0 000 1.7z" />
                        </svg>
                        <span>{effectiveValue}</span>
                      </span>
                    ) : (
                      <>
                        <span className="block text-[14px] font-bold text-slate-900 leading-tight truncate mt-0.5">
                          {effectiveValue}
                        </span>
                        {isDatesCard && isDatesConfirmed ? (
                          <span className="block text-[10.5px] text-emerald-700 font-semibold leading-[1.25] mt-0.5">
                            ✓ Confirmed on board · Click to toggle hold
                          </span>
                        ) : isRowSelected && rowSpec?.fact.evidenceQuote ? (
                          <span className="block text-[10.5px] text-[#1d4ed8] font-medium leading-[1.25] mt-0.5 line-clamp-1">
                            Source: &ldquo;{rowSpec.fact.evidenceQuote}&rdquo;
                          </span>
                        ) : item.subtitle ? (
                          <span className="block text-[11px] text-slate-500 leading-[1.25] mt-0.5 line-clamp-2">
                            {item.subtitle}
                          </span>
                        ) : null}
                      </>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  {item.thumbUrl ? (
                    <img
                      src={item.thumbUrl}
                      alt=""
                      aria-hidden="true"
                      className={
                        isTripStyleRow
                          ? "h-14 w-14 rounded-xl object-cover border border-slate-200"
                          : "h-10 w-13 rounded-lg object-cover border border-slate-200"
                      }
                    />
                  ) : null}
                  {!(isTripStyleRow && item.thumbUrl) ? (
                    <svg
                      viewBox="0 0 16 16"
                      className="h-3.5 w-3.5 text-slate-400"
                      fill="none"
                    >
                      <path
                        d="M6 3.5L10.5 8 6 12.5"
                        stroke="currentColor"
                        strokeWidth="1.6"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                    </svg>
                  ) : null}
                </div>
              </button>
            );
          })}
        </div>

        <Link
          href={`/workbench?source=departure-board&case=${encodeURIComponent(
            fixture.pillTitle.toLowerCase().replace(/\s+/g, "-")
          )}&iata=${encodeURIComponent(fixture.tagCode)}&prefill=${encodeURIComponent(
            fixture.voiceNote.quote.replace(/^[“"]|[”"]$/g, "")
          )}`}
          className="sr-only"
          data-testid="review-brief-cta"
        >
          <span>Review brief</span>
          <span aria-hidden="true">→</span>
        </Link>
      </aside>
    </div>
  );
};

/**
 * Frame 4 Overlay: Bottom frosted-glass "Explore different inquiries" switcher dock
 * with left/right circular chevron buttons and stadium destination pills with icons.
 */
export const InquirySwitcherDock: React.FC<{
  activeInquiryId: InquiryId;
  activeDisplayTitle?: string;
  activeDisplaySubtitle?: string;
  onSelectInquiry: (id: InquiryId) => void;
  onApplyDynamicInquiry?: (rawInput: string) => void;
  onShuffleRandom?: () => void;
  isAutoCycling?: boolean;
  onToggleAutoCycle?: () => void;
  stageMode: InteractiveStageMode;
  onChangeStageMode: (mode: InteractiveStageMode) => void;
  soundEnabled: boolean;
  onToggleSound: () => void;
  visibleInHero?: boolean;
}> = ({
  activeInquiryId,
  activeDisplayTitle,
  activeDisplaySubtitle,
  onSelectInquiry,
  onApplyDynamicInquiry,
  onShuffleRandom,
  isAutoCycling = false,
  onToggleAutoCycle,
  stageMode,
  onChangeStageMode,
  soundEnabled,
  onToggleSound,
  visibleInHero = false,
}) => {
  const [isCustomDrawerOpen, setIsCustomDrawerOpen] = useState(false);
  const [customDraft, setCustomDraft] = useState("");
  const currentIdx = INQUIRY_ORDER.indexOf(activeInquiryId);

  const handleCyclePrev = () => {
    const activeSlug = (activeDisplayTitle ?? activeInquiryId).toLowerCase();
    const catIdx = DESTINATION_CATALOG_REGISTRY.findIndex(
      (entry) =>
        entry.slug === activeSlug ||
        entry.displayName.toLowerCase() === activeSlug
    );
    if (catIdx >= 0 && onApplyDynamicInquiry) {
      const prevEntry =
        DESTINATION_CATALOG_REGISTRY[
          (catIdx - 1 + DESTINATION_CATALOG_REGISTRY.length) %
            DESTINATION_CATALOG_REGISTRY.length
        ];
      if (
        prevEntry.slug === "italy" ||
        prevEntry.slug === "japan" ||
        prevEntry.slug === "morocco"
      ) {
        onSelectInquiry(prevEntry.slug);
      } else {
        onApplyDynamicInquiry(prevEntry.displayName);
      }
      return;
    }
    const nextIdx = (currentIdx - 1 + INQUIRY_ORDER.length) % INQUIRY_ORDER.length;
    onSelectInquiry(INQUIRY_ORDER[nextIdx]);
  };

  const handleCycleNext = () => {
    const activeSlug = (activeDisplayTitle ?? activeInquiryId).toLowerCase();
    const catIdx = DESTINATION_CATALOG_REGISTRY.findIndex(
      (entry) =>
        entry.slug === activeSlug ||
        entry.displayName.toLowerCase() === activeSlug
    );
    if (catIdx >= 0 && onApplyDynamicInquiry) {
      const nextEntry =
        DESTINATION_CATALOG_REGISTRY[
          (catIdx + 1) % DESTINATION_CATALOG_REGISTRY.length
        ];
      if (
        nextEntry.slug === "italy" ||
        nextEntry.slug === "japan" ||
        nextEntry.slug === "morocco"
      ) {
        onSelectInquiry(nextEntry.slug);
      } else {
        onApplyDynamicInquiry(nextEntry.displayName);
      }
      return;
    }
    const nextIdx = (currentIdx + 1) % INQUIRY_ORDER.length;
    onSelectInquiry(INQUIRY_ORDER[nextIdx]);
  };

  const handleSubmitCustom = (e: React.FormEvent) => {
    e.preventDefault();
    if (!customDraft.trim() || !onApplyDynamicInquiry) return;
    onApplyDynamicInquiry(customDraft.trim());
    setIsCustomDrawerOpen(false);
  };

  const renderDockIcon = (id: InquiryId, isActive: boolean) => {
    const iconColor = isActive ? "text-[#0f296b]" : "text-white";
    if (id === "japan") {
      return (
        <svg viewBox="0 0 24 24" className={`h-5 w-5 shrink-0 ${iconColor}`} fill="currentColor">
          <path d="M3 6.2c3 .8 6 1.2 9 1.2s6-.4 9-1.2l.8 1.8c-2.1.6-4.4 1-6.8 1.1v2.1h3.6v1.8H15v7.5h-2V13h-2v7.5H9V13H5.4v-1.8H9V9.1c-2.4-.1-4.7-.5-6.8-1.1L3 6.2z" />
        </svg>
      );
    }
    if (id === "morocco") {
      return (
        <svg viewBox="0 0 24 24" className={`h-5 w-5 shrink-0 ${iconColor}`} fill="currentColor">
          <path d="M12.5 9.5c-.7 2.6-1.1 5.9-1.2 10.5h2.2c-.1-4.5.3-7.8 1.1-10.4 1.9.5 3.7 1.7 4.9 3.2.3-.6.3-1.4.1-2.2-.5-1.5-2.1-2.7-4.1-3.1 1.6-1.1 3.6-1.4 5.5-.9-.3-.8-.9-1.5-1.7-2-1.7-.9-3.9-.7-5.7.5.6-1.5 1.9-2.6 3.5-3-.8-.4-1.8-.5-2.8-.2-1.6.5-2.9 1.7-3.3 3.3-.5-1.6-1.7-2.8-3.3-3.3-1-.3-2-.2-2.8.2 1.6.4 2.9 1.5 3.5 3-1.7-1.2-3.9-1.4-5.7-.5-.8.5-1.4 1.2-1.7 2 1.9-.5 3.9.2 5.5.9-2 .4-3.6 1.6-4.1 3.1-.3.8-.2 1.6.1 2.2 1.2-1.5 3-2.7 4.9-3.2z" />
        </svg>
      );
    }
    return (
      <svg viewBox="0 0 24 24" className={`h-5 w-5 shrink-0 ${iconColor}`} fill="currentColor">
        <path d="M12 3L4 8v2h16V8l-8-5zm-6 9v6H4v2h16v-2h-2v-6h-2v6h-3v-6h-2v6H8v-6H6z" />
      </svg>
    );
  };

  return (
    <>
      <div
        className={`pointer-events-auto absolute bottom-[3.2%] sm:bottom-[5.2%] left-1/2 -translate-x-1/2 z-40 flex flex-nowrap items-center justify-start sm:justify-center gap-2 sm:gap-3.5 rounded-[22px] sm:rounded-[26px] bg-[#1a2234]/68 sm:bg-[#1a2234]/58 backdrop-blur-2xl border border-white/25 px-3 sm:px-7 py-2 sm:py-3.5 text-white shadow-[0_22px_55px_rgba(0,0,0,0.55),inset_0_1px_1px_rgba(255,255,255,0.28)] max-w-[94vw] overflow-x-auto whitespace-nowrap transition-opacity duration-300 ${
          visibleInHero
            ? "opacity-100"
            : "opacity-0 hover:opacity-100 focus-within:opacity-100"
        }`}
        data-testid="inquiry-switcher-dock"
      >
        <span className="hidden lg:inline-block text-[15px] font-medium text-white/95 pr-2">
          Explore different inquiries
        </span>

        <button
          type="button"
          onClick={handleCyclePrev}
          aria-label="Previous inquiry"
          className="hidden sm:inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-white/5 hover:bg-white/15 border border-white/35 text-white/90 hover:text-white transition-colors"
        >
          <svg viewBox="0 0 16 16" className="h-4 w-4" fill="none">
            <path
              d="M10 3.5L5.5 8 10 12.5"
              stroke="currentColor"
              strokeWidth="1.7"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </button>

        <div className="flex items-center gap-2 sm:gap-3">
          {INQUIRY_ORDER.map((id) => {
            const item = DEPARTURE_INQUIRIES[id];
            const isActive =
              id === activeInquiryId &&
              (!activeDisplayTitle ||
                activeDisplayTitle.toLowerCase() === item.pillTitle.toLowerCase());
            return (
              <button
                key={id}
                type="button"
                onClick={() => onSelectInquiry(id)}
                className={`flex items-center gap-2 sm:gap-3 rounded-full px-3.5 sm:px-6 py-1.5 sm:py-2.5 sm:min-w-[156px] text-left transition-all duration-200 whitespace-nowrap shrink-0 ${
                  isActive
                    ? "bg-white text-[#0f296b] shadow-[0_6px_20px_rgba(255,255,255,0.28)]"
                    : "bg-white/5 text-white hover:bg-white/15 border border-white/35"
                }`}
                data-testid={`inquiry-pill-${id}`}
              >
                {renderDockIcon(id, isActive)}
                <div className="flex flex-col leading-tight">
                  <span className="text-[12.5px] sm:text-[14px] font-bold">{item.pillTitle}</span>
                  <span
                    className={`hidden sm:inline text-[12px] ${
                      isActive
                        ? "text-[#1e3a8a]/85 font-medium"
                        : "text-white/80 font-normal"
                    }`}
                  >
                    {item.pillSubtitle}
                  </span>
                </div>
              </button>
            );
          })}

          {activeDisplayTitle &&
          !["italy", "japan", "morocco"].includes(
            activeDisplayTitle.toLowerCase()
          ) ? (
            <button
              type="button"
              onClick={() => setIsCustomDrawerOpen(true)}
              className="flex items-center gap-2 sm:gap-2.5 rounded-full px-3.5 sm:px-5 py-1.5 sm:py-2.5 bg-white text-[#0f296b] shadow-[0_6px_20px_rgba(255,255,255,0.28)] text-left transition-all duration-200 whitespace-nowrap shrink-0"
              data-testid="inquiry-pill-dynamic"
            >
              {renderDockIcon(activeInquiryId, true)}
              <div className="flex flex-col leading-tight">
                <span className="text-[12.5px] sm:text-[14px] font-bold">
                  {activeDisplayTitle}
                </span>
                <span className="hidden sm:inline text-[12px] text-[#1e3a8a]/85 font-medium">
                  {activeDisplaySubtitle ?? "Catalog Inquiry"}
                </span>
              </div>
            </button>
          ) : null}

          {onApplyDynamicInquiry ? (
            <button
              type="button"
              onClick={() => setIsCustomDrawerOpen((prev) => !prev)}
              className="flex items-center gap-1.5 sm:gap-2 rounded-full px-3 sm:px-4 py-1.5 sm:py-2.5 bg-[#f5c418] hover:bg-[#fde047] text-slate-950 font-bold text-[11.5px] sm:text-[12.5px] shadow-[0_6px_18px_rgba(245,196,24,0.35)] transition-all whitespace-nowrap shrink-0"
              data-testid="inquiry-custom-trigger"
              title="Type any natural-language travel request or select from 15 destinations"
            >
              <span>✦ Custom Inquiry</span>
            </button>
          ) : null}
        </div>

        <button
          type="button"
          onClick={handleCycleNext}
          aria-label="Next inquiry"
          className="hidden sm:inline-flex h-9 w-9 items-center justify-center rounded-full bg-white/5 hover:bg-white/15 border border-white/35 text-white/90 hover:text-white transition-colors"
        >
          <svg viewBox="0 0 16 16" className="h-4 w-4" fill="none">
            <path
              d="M6 3.5L10.5 8 6 12.5"
              stroke="currentColor"
              strokeWidth="1.7"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </button>
      </div>

      {/* Live Dynamic Inquiry & Catalog Drawer (Revealed when clicking "Custom Inquiry" button) */}
      {isCustomDrawerOpen && onApplyDynamicInquiry ? (
        <div
          className="pointer-events-auto absolute bottom-[16.5%] right-4 z-50 w-[340px] sm:w-[410px] rounded-2xl bg-[#0d1f4d]/95 backdrop-blur-2xl border border-[#93c5fd]/40 p-4 text-white shadow-[0_24px_60px_rgba(0,0,0,0.65)]"
          data-testid="dynamic-inquiry-popover"
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-[12px] font-bold uppercase tracking-wider text-[#f5c418]">
              Live Dynamic Catalog & NLU Parser
            </span>
            <button
              type="button"
              onClick={() => setIsCustomDrawerOpen(false)}
              aria-label="Close custom inquiry input"
              className="text-white/60 hover:text-white text-xs px-1.5 py-0.5"
            >
              ✕
            </button>
          </div>
          <form onSubmit={handleSubmitCustom} className="flex items-center gap-2 mb-3">
            <input
              type="text"
              value={customDraft}
              onChange={(e) => setCustomDraft(e.target.value)}
              placeholder="e.g. 2 travelers for dubai around june next year..."
              aria-label="Custom travel inquiry text"
              className="flex-1 rounded-xl bg-white/10 border border-white/25 px-3 py-1.5 text-xs text-white placeholder:text-white/50 focus:outline-none focus:border-[#f5c418]"
              data-testid="dynamic-inquiry-input"
            />
            <button
              type="submit"
              className="rounded-xl bg-[#f5c418] hover:bg-[#fde047] text-slate-950 font-bold text-xs px-3 py-1.5 transition-colors"
              data-testid="dynamic-inquiry-submit"
            >
              Clack →
            </button>
          </form>
          <div className="flex flex-wrap gap-1.5">
            {DESTINATION_CATALOG_REGISTRY.filter(
              (entry) => !["italy", "japan", "morocco"].includes(entry.slug)
            ).map((entry) => (
              <button
                key={entry.slug}
                type="button"
                onClick={() => {
                  onApplyDynamicInquiry(entry.displayName);
                  setIsCustomDrawerOpen(false);
                }}
                className="rounded-full bg-white/10 hover:bg-white/20 border border-white/20 px-2.5 py-1 text-[11px] font-medium text-white transition-colors"
                data-testid={`catalog-chip-${entry.slug}`}
              >
                {entry.displayName} · {entry.defaultStyleLabel}
              </button>
            ))}
          </div>
        </div>
      ) : null}

      {/* Discreet Stage Mode & Sound Utility Controls (outside the visual dock, revealed on hover) */}
      <div className="pointer-events-auto absolute bottom-2 right-3 z-40 flex items-center gap-1 opacity-0 hover:opacity-100 focus-within:opacity-100 transition-opacity duration-200">
        {onToggleAutoCycle ? (
          <button
            type="button"
            onClick={onToggleAutoCycle}
            className={`rounded-full px-2.5 py-1 text-[11px] font-medium transition-colors ${
              isAutoCycling
                ? "bg-emerald-400 text-slate-950 font-semibold"
                : "bg-slate-900/70 text-white/80 hover:bg-slate-900"
            }`}
            data-testid="inquiry-auto-cycle-toggle"
          >
            {isAutoCycling ? "Auto-Rotate: LIVE" : "Auto-Rotate: PAUSED"}
          </button>
        ) : null}
        {onApplyDynamicInquiry ? (
          <button
            type="button"
            onClick={() => setIsCustomDrawerOpen((prev) => !prev)}
            className={`rounded-full px-2.5 py-1 text-[11px] font-medium transition-colors ${
              isCustomDrawerOpen
                ? "bg-[#f5c418] text-slate-950 font-semibold"
                : "bg-slate-900/70 text-white/80 hover:bg-slate-900"
            }`}
            data-testid="mode-toggle-custom-inquiry"
          >
            Custom Inquiry
          </button>
        ) : null}
        <button
          type="button"
          onClick={() =>
            onChangeStageMode(
              stageMode === "voice_ingest" ? "hero" : "voice_ingest"
            )
          }
          className={`rounded-full px-2.5 py-1 text-[11px] font-medium transition-colors ${
            stageMode === "voice_ingest"
              ? "bg-[#f5c418] text-slate-950 font-semibold"
              : "bg-slate-900/70 text-white/80 hover:bg-slate-900"
          }`}
          data-testid="mode-toggle-voice-ingest"
        >
          Voice Ingest
        </button>
        <button
          type="button"
          onClick={() =>
            onChangeStageMode(
              stageMode === "provenance_brief" ? "hero" : "provenance_brief"
            )
          }
          className={`rounded-full px-2.5 py-1 text-[11px] font-medium transition-colors ${
            stageMode === "provenance_brief"
              ? "bg-[#f5c418] text-slate-950 font-semibold"
              : "bg-slate-900/70 text-white/80 hover:bg-slate-900"
          }`}
          data-testid="mode-toggle-provenance"
        >
          Brief X-Ray
        </button>
        <button
          type="button"
          onClick={onToggleSound}
          aria-label={
            soundEnabled
              ? "Mute mechanical split-flap sound"
              : "Enable mechanical split-flap sound"
          }
          title={
            soundEnabled
              ? "Mechanical Solari sound enabled"
              : "Mechanical Solari sound muted"
          }
          className={`rounded-full p-1.5 transition-colors ${
            soundEnabled
              ? "bg-slate-900/70 text-[#f5c418] hover:bg-slate-900"
              : "bg-slate-900/50 text-white/45 hover:bg-slate-900/80"
          }`}
          data-testid="sound-toggle-button"
        >
          {soundEnabled ? (
            <svg viewBox="0 0 20 20" className="h-3.5 w-3.5" fill="currentColor">
              <path d="M9.383 3.076A1 1 0 0110 4v12a1 1 0 01-1.707.707L4.586 13H2a1 1 0 01-1-1V8a1 1 0 011-1h2.586l3.707-3.707a1 1 0 011.09-.217zM14.657 2.929a1 1 0 011.414 0A9.972 9.972 0 0119 10a9.972 9.972 0 01-2.929 7.071 1 1 0 01-1.414-1.414A7.971 7.971 0 0017 10c0-2.21-.894-4.208-2.343-5.657a1 1 0 010-1.414zm-2.829 2.828a1 1 0 011.415 0A5.983 5.983 0 0115 10a5.984 5.984 0 01-1.757 4.243 1 1 0 01-1.415-1.415A3.984 3.984 0 0013 10a3.983 3.983 0 00-1.172-2.828 1 1 0 010-1.415z" />
            </svg>
          ) : (
            <svg viewBox="0 0 20 20" className="h-3.5 w-3.5" fill="currentColor">
              <path
                fillRule="evenodd"
                d="M9.383 3.076A1 1 0 0110 4v12a1 1 0 01-1.707.707L4.586 13H2a1 1 0 01-1-1V8a1 1 0 011-1h2.586l3.707-3.707a1 1 0 011.09-.217zM12.293 7.293a1 1 0 011.414 0L15 8.586l1.293-1.293a1 1 0 111.414 1.414L16.414 10l1.293 1.293a1 1 0 01-1.414 1.414L15 11.414l-1.293 1.293a1 1 0 01-1.414-1.414L13.586 10l-1.293-1.293a1 1 0 010-1.414z"
                clipRule="evenodd"
              />
            </svg>
          )}
        </button>
      </div>
    </>
  );
};
