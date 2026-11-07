"use client";

import React, { useEffect, useRef, useState } from "react";
import { splitFlapAudio } from "./board-engine";

export interface SplitFlapPhotoModuleProps {
  src: string;
  alt: string;
  caption?: string;
  rowIndex: number;
  startDelayMs?: number;
  forceTriggerKey?: number;
}

export const SplitFlapPhotoModule: React.FC<SplitFlapPhotoModuleProps> = ({
  src,
  alt,
  caption,
  rowIndex,
  startDelayMs = 140,
  forceTriggerKey = 0,
}) => {
  const [displayedSrc, setDisplayedSrc] = useState(src);
  const [incomingSrc, setIncomingSrc] = useState<string | null>(null);
  const [phase, setPhase] = useState<"idle" | "upper" | "lower">("idle");

  const prevSrcRef = useRef(src);
  const prevForceRef = useRef(forceTriggerKey);

  useEffect(() => {
    const changed =
      prevSrcRef.current !== src || prevForceRef.current !== forceTriggerKey;
    if (!changed) return;

    prevSrcRef.current = src;
    prevForceRef.current = forceTriggerKey;

    const t1 = window.setTimeout(() => {
      setIncomingSrc(src);
      setPhase("upper");
      splitFlapAudio.playFlapClack(10, false);
    }, startDelayMs);

    const t2 = window.setTimeout(() => {
      setPhase("lower");
      splitFlapAudio.playFlapClack(11, true);
    }, startDelayMs + 130);

    const t3 = window.setTimeout(() => {
      setDisplayedSrc(src);
      setIncomingSrc(null);
      setPhase("idle");
    }, startDelayMs + 260);

    return () => {
      window.clearTimeout(t1);
      window.clearTimeout(t2);
      window.clearTimeout(t3);
    };
  }, [src, forceTriggerKey, startDelayMs]);

  const isFlipping = phase !== "idle" && incomingSrc !== null;
  const topStaticSrc = isFlipping && incomingSrc ? incomingSrc : displayedSrc;
  const bottomStaticSrc = displayedSrc;

  return (
    <div
      className="relative w-full h-full min-w-0 rounded-[2.5px] bg-[#0c1018]/80 p-0 shadow-[0_2px_3px_rgba(0,0,0,0.45)] shrink-0"
      style={{ perspective: "520px" }}
      title={caption ?? alt}
      data-testid={`split-flap-photo-row-${rowIndex}`}
    >
      <div
        className="relative w-full h-full rounded-[2.5px] overflow-hidden bg-[#121824]"
        style={{
          filter: isFlipping ? "url(#split-flap-motion-blur)" : undefined,
        }}
      >
        {/* Static Upper Half */}
        <div className="absolute inset-x-0 top-0 h-1/2 overflow-hidden">
          <img
            src={topStaticSrc}
            alt={alt}
            className="w-full h-[200%] max-w-none object-cover object-top select-none pointer-events-none"
          />
        </div>

        {/* Static Lower Half */}
        <div className="absolute inset-x-0 bottom-0 h-1/2 overflow-hidden">
          <img
            src={bottomStaticSrc}
            alt={alt}
            className="w-full h-[200%] max-w-none object-cover object-top -translate-y-1/2 select-none pointer-events-none"
          />
        </div>

        {/* Rotating Upper Leaf */}
        {isFlipping && phase === "upper" ? (
          <div
            className="absolute inset-x-0 top-0 h-1/2 overflow-hidden z-20"
            style={{
              transformOrigin: "50% 100%",
              transform: "rotateX(-82deg)",
              transition: "transform 125ms cubic-bezier(0.4, 0, 1, 1)",
              backfaceVisibility: "hidden",
              boxShadow: "0 8px 14px rgba(0,0,0,0.55)",
            }}
          >
            <img
              src={displayedSrc}
              alt={alt}
              className="w-full h-[200%] max-w-none object-cover object-top select-none pointer-events-none"
            />
          </div>
        ) : null}

        {/* Rotating Lower Leaf */}
        {isFlipping && phase === "lower" && incomingSrc ? (
          <div
            className="absolute inset-x-0 bottom-0 h-1/2 overflow-hidden z-20"
            style={{
              transformOrigin: "50% 0%",
              transform: "rotateX(0deg)",
              transition: "transform 130ms cubic-bezier(0.16, 1, 0.3, 1)",
              backfaceVisibility: "hidden",
              boxShadow: "0 -5px 10px rgba(0,0,0,0.45)",
            }}
          >
            <img
              src={incomingSrc}
              alt={alt}
              className="w-full h-[200%] max-w-none object-cover object-top -translate-y-1/2 select-none pointer-events-none"
            />
          </div>
        ) : null}

        {/* Center Horizontal Split Seam */}
        <div className="pointer-events-none absolute inset-x-0 top-1/2 -translate-y-1/2 h-[1px] bg-black/35 z-30" />

        {/* Subtle Left / Right Mechanical Hinge Notches */}
        <div className="pointer-events-none absolute left-0 top-1/2 -translate-y-1/2 w-[1.5px] h-[3.5px] bg-black/35 z-40" />
        <div className="pointer-events-none absolute right-0 top-1/2 -translate-y-1/2 w-[1.5px] h-[3.5px] bg-black/35 z-40" />
      </div>
    </div>
  );
};
