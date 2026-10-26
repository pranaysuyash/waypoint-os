"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import type {
  BoardRowId,
  DepartureInquiryFixture,
  InquiryId,
} from "./board-fixtures";
import { INQUIRY_ORDER, DEPARTURE_INQUIRIES } from "./board-fixtures";

export type InteractiveStageMode = "hero" | "voice_ingest" | "provenance_brief";

/**
 * Frame 2 Overlay: Floating glassmorphic "Incoming request · 10:14 AM" card
 * positioned at the upper-middle-left (between headline and departure board)
 * with playable 0:24 voice-note waveform and glowing cyan feed vector into Row 4 (DATES).
 */
export const IncomingRequestVoiceCard: React.FC<{
  fixture: DepartureInquiryFixture;
  isScanningDates: boolean;
  onReplayIngest: () => void;
}> = ({ fixture, isScanningDates, onReplayIngest }) => {
  const [isPlayingVoice, setIsPlayingVoice] = useState(false);
  const [voiceProgress, setVoiceProgress] = useState(0.58);

  useEffect(() => {
    if (!isPlayingVoice) return;
    const start = performance.now();
    const durationMs = 2800;
    const interval = window.setInterval(() => {
      const elapsed = performance.now() - start;
      const next = Math.min(1, elapsed / durationMs);
      setVoiceProgress(next);
      if (next >= 1) {
        setIsPlayingVoice(false);
        window.clearInterval(interval);
      }
    }, 50);
    return () => window.clearInterval(interval);
  }, [isPlayingVoice]);

  const handleTogglePlay = () => {
    if (!isPlayingVoice) {
      setVoiceProgress(0);
      setIsPlayingVoice(true);
      onReplayIngest();
    } else {
      setIsPlayingVoice(false);
    }
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
          d="M 714 418 L 728 418 Q 734 418 734 426 L 734 438"
          fill="none"
          stroke="#93c5fd"
          strokeWidth="2.8"
          strokeLinecap="round"
          filter="url(#ingest-glow)"
        />
        <path
          d="M 584 484 C 584 536, 618 552, 666 554"
          fill="none"
          stroke="url(#ingest-arrow-grad)"
          strokeWidth="3.5"
          strokeLinecap="round"
          filter="url(#ingest-glow)"
        />
        <path
          d="M 656 546 L 671 554 L 655 562"
          fill="none"
          stroke="#dbeafe"
          strokeWidth="3.2"
          strokeLinecap="round"
          strokeLinejoin="round"
          filter="url(#ingest-glow)"
        />
      </svg>

      {/* Glassmorphic Incoming Request Card (Upper-Middle-Left, Matching Frame 2) */}
      <div
        className="pointer-events-auto absolute z-30 rounded-[18px] bg-[#163d82]/78 backdrop-blur-xl border border-[#93c5fd]/45 p-4 sm:p-4.5 text-white shadow-[0_24px_60px_rgba(3,12,38,0.6),0_0_28px_rgba(96,165,250,0.22),inset_0_1px_1px_rgba(255,255,255,0.35)] transition-all duration-300"
        style={{
          left: "25.9%",
          top: "24.1%",
          width: "17.0%",
          minWidth: "272px",
        }}
        data-testid="incoming-request-voice-card"
      >
        <div className="flex items-center justify-between text-[12px] text-white/95 mb-2.5">
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

        <p className="text-[13.5px] sm:text-[14px] leading-[1.42] text-white/95 font-normal mb-3.5">
          &ldquo;{fixture.voiceNote.quote}&rdquo;
        </p>

        {/* Playable Voice Note Waveform Row (Top Border + Ice-Blue Play Button + Glowing Cyan Bars) */}
        <div className="flex items-center gap-2.5 border-t border-white/20 pt-2.5">
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
  onSelectRow: (rowId: BoardRowId) => void;
  onCloseBrief: () => void;
}> = ({ fixture, selectedRowId, onSelectRow, onCloseBrief }) => {
  // Exact slanted-bus glowing wire paths routing from the chat bubbles inside the container
  // to the vertical center of the 4 Frame 3 category plates (endX=614) in 1672x941 coordinates
  const wirePaths: Array<{
    rowId: BoardRowId;
    color: string;
    d: string;
    startX: number;
    startY: number;
    endX: number;
    endY: number;
  }> = [
    {
      rowId: "destination",
      color: "#fde047",
      startX: 438,
      startY: 622,
      endX: 614,
      endY: 345,
      d: "M 438 622 L 492 622 C 522 622, 540 530, 566 378 C 572 350, 584 345, 614 345",
    },
    {
      rowId: "travelers",
      color: "#38bdf8",
      startX: 438,
      startY: 644,
      endX: 614,
      endY: 423,
      d: "M 438 644 L 502 644 C 534 644, 550 560, 574 446 C 580 426, 592 423, 614 423",
    },
    {
      rowId: "duration",
      color: "#4ade80",
      startX: 430,
      startY: 706,
      endX: 614,
      endY: 500,
      d: "M 430 706 L 512 706 C 544 706, 560 618, 582 522 C 587 503, 596 500, 614 500",
    },
    {
      rowId: "tripStyle",
      color: "#d8b4fe",
      startX: 408,
      startY: 790,
      endX: 614,
      endY: 664,
      d: "M 408 790 L 520 790 C 554 790, 566 710, 586 672 C 592 664, 600 664, 614 664",
    },
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

  return (
    <>
      {/* SVG Provenance Wires connecting Chat Container -> Left Edge of Category Plates */}
      <svg
        viewBox="0 0 1672 941"
        className="pointer-events-none absolute inset-0 w-full h-full z-20"
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
          const isFocused = !selectedRowId || selectedRowId === wire.rowId;
          return (
            <g
              key={wire.rowId}
              style={{ opacity: isFocused ? 1 : 0.35 }}
              className="transition-opacity duration-200"
            >
              <path
                d={wire.d}
                fill="none"
                stroke={wire.color}
                strokeWidth={selectedRowId === wire.rowId ? "3.4" : "2.5"}
                strokeLinecap="round"
                strokeLinejoin="round"
                filter="url(#wire-neon-glow)"
              />
              {/* Glowing Circular Port on Left Edge of Category Plate */}
              <circle
                cx={wire.endX}
                cy={wire.endY}
                r="4"
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
        className="pointer-events-auto absolute z-30 rounded-[18px] bg-[#1a3875]/62 backdrop-blur-xl border border-[#93c5fd]/40 p-3 sm:p-3.5 text-white shadow-[0_22px_50px_rgba(3,10,28,0.6),inset_0_1px_1px_rgba(255,255,255,0.28)]"
        style={{
          left: "6.0%",
          top: "55.4%",
          width: "23.7%",
          minWidth: "310px",
        }}
        data-testid="provenance-chat-thread"
      >
        {/* Container Header Bar */}
        <div className="flex items-center justify-between px-1 pb-2 mb-2 text-[12px]">
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
        <div className="space-y-2">
          {fixture.chatThread.map((msg, msgIdx) => (
            <div
              key={msg.id}
              className={`rounded-xl bg-[#eef3fb]/95 border border-white/90 px-3 py-2 text-[#1e293b] shadow-[0_4px_12px_rgba(5,15,40,0.18)] ${
                bubbleWidthClasses[msgIdx] ?? "w-[85%]"
              }`}
            >
              <div className="flex items-end justify-between gap-2 text-[11.5px] sm:text-[12px] leading-[1.36]">
                <div>
                  {msg.segments.map((seg, idx) =>
                    seg.highlight ? (
                      <button
                        key={idx}
                        type="button"
                        onClick={() => onSelectRow(seg.highlight!.targetRow)}
                        className={`inline-flex items-center rounded px-1.5 py-0.2 mx-0.5 font-bold text-[11px] sm:text-[11.5px] transition-transform hover:scale-105 ${
                          highlightStyles[seg.highlight.color]
                        }`}
                      >
                        {seg.text}
                      </button>
                    ) : (
                      <span key={idx} className="text-[#1e293b] font-medium">
                        {seg.text}
                      </span>
                    )
                  )}
                </div>
                <span className="text-[9.5px] font-sans text-slate-400 shrink-0">
                  {msg.timestamp}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Right-Hand Slide-Over Pearl-White Structured Brief Drawer ("From message to brief") */}
      <aside
        className="pointer-events-auto absolute z-30 flex flex-col justify-between rounded-[24px] bg-[#f8fafc] border border-white p-5 sm:p-6 text-slate-900 shadow-[0_28px_70px_rgba(4,10,28,0.62)] transition-all duration-300"
        style={{
          left: `${(1250 / 1672) * 100}%`,
          top: `${(166 / 941) * 100}%`,
          width: `${(383 / 1672) * 100}%`,
          minHeight: `${(618 / 941) * 100}%`,
          minWidth: "320px",
        }}
        aria-label="From message to brief"
        data-testid="structured-brief-drawer"
      >
        <div>
          <div className="flex items-start justify-between gap-2 mb-2">
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

          <p className="text-[12.5px] text-slate-600 leading-[1.42] mb-4">
            Waypoint automatically finds key details, fills what it can, and flags
            what&apos;s missing, so you can send a polished quote faster.
          </p>
        </div>

        {/* 5 Rounded White Row Cards with Icons, Subtitles, Photo Thumbnails, and Chevrons */}
        <div className="flex-1 flex flex-col justify-between gap-2.5">
          {fixture.briefSummary.map((item) => {
            const isRowSelected = selectedRowId === item.rowId;
            const isTripStyleRow = item.rowId === "tripStyle";
            return (
              <button
                key={item.label}
                type="button"
                onClick={() => onSelectRow(item.rowId)}
                className={`w-full rounded-xl bg-white border px-4 py-3 flex items-center justify-between gap-3 text-left transition-all shadow-[0_1px_3px_rgba(15,23,42,0.04)] ${
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
                    <span className="block text-[12px] font-bold text-slate-800 leading-tight">
                      {item.label}
                    </span>
                    {item.status === "needs_confirmation" ? (
                      <span className="mt-1 inline-flex items-center gap-1.5 rounded-full bg-[#fef3c7] border border-[#fde68a] px-2.5 py-0.5 text-[11.5px] font-semibold text-[#92400e]">
                        <svg
                          viewBox="0 0 16 16"
                          className="h-3.5 w-3.5 text-[#d97706] shrink-0"
                          fill="currentColor"
                          aria-hidden="true"
                        >
                          <path d="M8.865 1.52c-.38-.68-1.35-.68-1.73 0L1.14 12.24c-.37.66.11 1.48.865 1.48h11.99c.755 0 1.235-.82.865-1.48L8.865 1.52zM8 5a.75.75 0 01.75.75v3a.75.75 0 01-1.5 0v-3A.75.75 0 018 5zm0 6.75a.85.85 0 100-1.7.85.85 0 000 1.7z" />
                        </svg>
                        <span>{item.value}</span>
                      </span>
                    ) : (
                      <>
                        <span className="block text-[14.5px] font-bold text-slate-900 leading-tight truncate mt-0.5">
                          {item.value}
                        </span>
                        {item.subtitle ? (
                          <span className="block text-[11px] text-slate-500 leading-[1.3] mt-0.5 line-clamp-2">
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
                          ? "h-16 w-16 rounded-xl object-cover border border-slate-200"
                          : "h-11 w-14 rounded-lg object-cover border border-slate-200"
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

        {/* Epistemic Evidence Callout for Selected Row */}
        {selectedRowId ? (
          <div className="mt-3 rounded-xl bg-slate-900 text-white p-2.5 text-[11px] leading-relaxed">
            {(() => {
              const row = fixture.rows.find((r) => r.id === selectedRowId);
              if (!row) return null;
              return (
                <>
                  <div className="flex items-center justify-between mb-0.5">
                    <span className="font-mono uppercase tracking-wider text-[9.5px] text-slate-400">
                      {row.label} · {row.fact.basis.toUpperCase()}
                    </span>
                    <span
                      className={`text-[9.5px] font-semibold px-1.5 py-0.2 rounded ${
                        row.fact.basis === "unknown"
                          ? "bg-[#f5c418] text-slate-950"
                          : "bg-emerald-500/20 text-emerald-300"
                      }`}
                    >
                      {row.fact.basis === "unknown"
                        ? "Epistemic Hold"
                        : "Verified Quote"}
                    </span>
                  </div>
                  <p className="text-white/90 font-medium line-clamp-2">
                    {row.fact.evidenceQuote
                      ? `"${row.fact.evidenceQuote}"`
                      : row.fact.advisorFollowUp}
                  </p>
                </>
              );
            })()}
          </div>
        ) : null}

        <Link
          href="/workbench"
          className="sr-only"
          data-testid="review-brief-cta"
        >
          <span>Review brief</span>
          <span aria-hidden="true">→</span>
        </Link>
      </aside>
    </>
  );
};

/**
 * Frame 4 Overlay: Bottom frosted-glass "Explore different inquiries" switcher dock
 * with left/right circular chevron buttons and stadium destination pills with icons.
 */
export const InquirySwitcherDock: React.FC<{
  activeInquiryId: InquiryId;
  onSelectInquiry: (id: InquiryId) => void;
  stageMode: InteractiveStageMode;
  onChangeStageMode: (mode: InteractiveStageMode) => void;
  soundEnabled: boolean;
  onToggleSound: () => void;
  visibleInHero?: boolean;
}> = ({
  activeInquiryId,
  onSelectInquiry,
  stageMode,
  onChangeStageMode,
  soundEnabled,
  onToggleSound,
  visibleInHero = false,
}) => {
  const currentIdx = INQUIRY_ORDER.indexOf(activeInquiryId);

  const handleCyclePrev = () => {
    const nextIdx = (currentIdx - 1 + INQUIRY_ORDER.length) % INQUIRY_ORDER.length;
    onSelectInquiry(INQUIRY_ORDER[nextIdx]);
  };

  const handleCycleNext = () => {
    const nextIdx = (currentIdx + 1) % INQUIRY_ORDER.length;
    onSelectInquiry(INQUIRY_ORDER[nextIdx]);
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
        className={`pointer-events-auto absolute bottom-[5.2%] left-1/2 -translate-x-1/2 z-40 flex flex-wrap lg:flex-nowrap items-center justify-center gap-3.5 rounded-[26px] bg-[#1a2234]/58 backdrop-blur-2xl border border-white/25 px-6 sm:px-7 py-3 sm:py-3.5 text-white shadow-[0_22px_55px_rgba(0,0,0,0.55),inset_0_1px_1px_rgba(255,255,255,0.28)] max-w-[96vw] whitespace-nowrap transition-opacity duration-300 ${
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
          className="hidden sm:inline-flex h-9 w-9 items-center justify-center rounded-full bg-white/5 hover:bg-white/15 border border-white/35 text-white/90 hover:text-white transition-colors"
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

        <div className="flex items-center gap-3">
          {INQUIRY_ORDER.map((id) => {
            const item = DEPARTURE_INQUIRIES[id];
            const isActive = id === activeInquiryId;
            return (
              <button
                key={id}
                type="button"
                onClick={() => onSelectInquiry(id)}
                className={`flex items-center gap-3 rounded-full px-5 sm:px-6 py-2 sm:py-2.5 min-w-[168px] text-left transition-all duration-200 whitespace-nowrap ${
                  isActive
                    ? "bg-white text-[#0f296b] shadow-[0_6px_20px_rgba(255,255,255,0.28)]"
                    : "bg-white/5 text-white hover:bg-white/15 border border-white/35"
                }`}
                data-testid={`inquiry-pill-${id}`}
              >
                {renderDockIcon(id, isActive)}
                <div className="flex flex-col leading-tight">
                  <span className="text-[14px] font-bold">{item.pillTitle}</span>
                  <span
                    className={`text-[12px] ${
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

      {/* Discreet Stage Mode & Sound Utility Controls (outside the visual dock, revealed on hover) */}
      <div className="pointer-events-auto absolute bottom-2 right-3 z-40 flex items-center gap-1 opacity-0 hover:opacity-100 transition-opacity duration-200">
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
