"use client";

import React, { useEffect, useRef, useState } from "react";
import type { FlapCellSpec } from "./board-fixtures";
import {
  computeFlapSequence,
  isSameFlapCell,
  splitFlapAudio,
  type FlapStepFrame,
} from "./board-engine";

export interface SplitFlapCellProps {
  spec: FlapCellSpec;
  rowIndex: number;
  colIndex: number;
  totalCols?: number;
  continuousRowText?: string;
  startDelayMs?: number;
  stepDurationMs?: number;
  compact?: boolean;
  forceTriggerKey?: number;
  highlighted?: boolean;
  highlightColor?: string;
}

export const SplitFlapCell: React.FC<SplitFlapCellProps> = ({
  spec,
  rowIndex,
  colIndex,
  totalCols = 12,
  continuousRowText,
  startDelayMs = 0,
  stepDurationMs = 56,
  compact = false,
  forceTriggerKey = 0,
  highlighted = false,
  highlightColor,
}) => {
  const [displayed, setDisplayed] = useState<FlapStepFrame>({
    topText: spec.topText,
    bottomText: spec.bottomText,
    variant: spec.variant,
    subLabel: spec.subLabel,
  });
  const [incoming, setIncoming] = useState<FlapStepFrame | null>(null);
  const [flipPhase, setFlipPhase] = useState<"idle" | "upper" | "lower">("idle");

  const prevSpecRef = useRef<FlapCellSpec>(spec);
  const prevForceKeyRef = useRef<number>(forceTriggerKey);
  const timersRef = useRef<number[]>([]);

  useEffect(() => {
    const clearAllTimers = () => {
      timersRef.current.forEach((id) => window.clearTimeout(id));
      timersRef.current = [];
    };

    const forceCascade = forceTriggerKey !== prevForceKeyRef.current;
    const specChanged = !isSameFlapCell(prevSpecRef.current, spec);

    if (!specChanged && !forceCascade) {
      return;
    }

    clearAllTimers();

    const fromSpec: FlapCellSpec = {
      topText: displayed.topText,
      bottomText: displayed.bottomText,
      variant: displayed.variant,
      subLabel: displayed.subLabel,
    };

    const sequence = computeFlapSequence(fromSpec, spec, {
      maxSteps: 6,
      forceCascade,
      seedOffset: rowIndex * 11 + colIndex * 7,
    });

    prevSpecRef.current = spec;
    prevForceKeyRef.current = forceTriggerKey;

    if (sequence.length <= 1 && !specChanged && !forceCascade) {
      setDisplayed(sequence[0]);
      setIncoming(null);
      setFlipPhase("idle");
      return;
    }

    const halfDuration = Math.max(22, Math.floor(stepDurationMs / 2));

    sequence.forEach((stepFrame, idx) => {
      const stepStart = startDelayMs + idx * stepDurationMs;
      const isLast = idx === sequence.length - 1;

      const tStart = window.setTimeout(() => {
        setIncoming(stepFrame);
        setFlipPhase("upper");
        splitFlapAudio.playFlapClack(colIndex, isLast);
      }, stepStart);

      const tMid = window.setTimeout(() => {
        setFlipPhase("lower");
      }, stepStart + halfDuration);

      const tEnd = window.setTimeout(() => {
        setDisplayed(stepFrame);
        if (isLast) {
          setIncoming(null);
          setFlipPhase("idle");
        }
      }, stepStart + stepDurationMs - 2);

      timersRef.current.push(tStart, tMid, tEnd);
    });

    return clearAllTimers;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [spec, forceTriggerKey, rowIndex, colIndex, startDelayMs, stepDurationMs]);

  const isFlipping = flipPhase !== "idle" && incoming !== null;
  const topStaticFrame = isFlipping && incoming ? incoming : displayed;
  const bottomStaticFrame = displayed;
  const rotatingUpperFrame = displayed;
  const rotatingLowerFrame = incoming ?? displayed;

  // Compute warm left-to-right terminal lighting across the board row (#f3ede0 on left -> #d6c8b2 on right)
  const colRatio = Math.max(0, Math.min(1, colIndex / Math.max(1, totalCols - 1)));
  const lerp = (a: number, b: number, t: number) => Math.round(a + (b - a) * t);
  const creamTopStart = `rgb(${lerp(244, 219, colRatio)}, ${lerp(239, 209, colRatio)}, ${lerp(227, 190, colRatio)})`;
  const creamTopEnd = `rgb(${lerp(235, 210, colRatio)}, ${lerp(229, 199, colRatio)}, ${lerp(215, 179, colRatio)})`;
  const creamBotStart = `rgb(${lerp(231, 206, colRatio)}, ${lerp(224, 194, colRatio)}, ${lerp(209, 174, colRatio)})`;
  const creamBotEnd = `rgb(${lerp(224, 199, colRatio)}, ${lerp(216, 187, colRatio)}, ${lerp(200, 166, colRatio)})`;

  const renderFaceContent = (
    frame: FlapStepFrame,
    half: "top" | "bottom"
  ): React.ReactNode => {
    if (frame.variant === "yellow_two_line") {
      // Continuous multi-flap yellow banner (`NEED` across top, `CONFIRMATION` across bottom)
      // Each flap clips its own horizontal slice (`left: -colIndex * 100%`, `width: 800%`) so 3D per-flap rotation works while letters flow continuously without artificial gaps!
      return (
        <div
          className={`relative w-full h-full overflow-hidden select-none ${
            half === "top"
              ? "bg-gradient-to-b from-[#f7cc22] to-[#eab812]"
              : "bg-gradient-to-b from-[#e4b10e] to-[#d8a208]"
          }`}
        >
          {/* Screen-reader accessible per-cell text */}
          <span className="sr-only">
            {half === "top" ? frame.topText : frame.bottomText ?? ""}
          </span>
          <div
            aria-hidden="true"
            className="pointer-events-none absolute inset-y-0 flex items-center pl-[2.8%]"
            style={{
              left: `${-colIndex * 100}%`,
              width: "800%",
            }}
          >
            {half === "top" ? (
              <span
                className="font-sans font-extrabold text-[#141923] text-[20px] sm:text-[26px] lg:text-[31px] tracking-[0.12em] leading-none uppercase whitespace-nowrap translate-y-[4%]"
                style={{ transform: "scaleX(0.75) scaleY(1.06)", transformOrigin: "left center" }}
              >
                NEED
              </span>
            ) : (
              <span
                className="font-sans font-extrabold text-[#141923] text-[20px] sm:text-[26px] lg:text-[31px] tracking-[0.145em] leading-none uppercase whitespace-nowrap -translate-y-[4%]"
                style={{ transform: "scaleX(0.76) scaleY(1.06)", transformOrigin: "left center" }}
              >
                CONFIRMATION
              </span>
            )}
          </div>
        </div>
      );
    }

    const isBlurredFlip = frame.variant === "blurred_flip";
    const isDarkRow4Blur = isBlurredFlip && rowIndex === 3 && colIndex <= 1;
    const isCream = frame.variant === "cream" || (isBlurredFlip && !isDarkRow4Blur);

    const bgClass =
      frame.variant === "scanning_amber"
        ? half === "top"
          ? "bg-gradient-to-b from-[#fcf6e3] to-[#f2e6c7] text-[#171d28]"
          : "bg-gradient-to-b from-[#ebdcb8] to-[#e2d0a6] text-[#171d28]"
        : isDarkRow4Blur
          ? half === "top"
            ? "bg-gradient-to-b from-[#6e5623] via-[#917232] to-[#594419] text-[#f5e7c4]/70"
            : "bg-gradient-to-b from-[#523e16] via-[#785d26] to-[#423110] text-[#f5e7c4]/70"
          : frame.variant === "dark_question"
            ? half === "top"
              ? "bg-gradient-to-b from-[#232a38] to-[#1a202c] text-[#f7f3e8]"
              : "bg-gradient-to-b from-[#171d28] to-[#121720] text-[#f7f3e8]"
            : frame.variant === "dark_blank"
              ? half === "top"
                ? "bg-gradient-to-b from-[#1d222c] to-[#161b24] text-[#64748b]"
                : "bg-gradient-to-b from-[#141820] to-[#10141b] text-[#64748b]"
              : "text-[#141a24]";

    const creamGradientStyle = isCream
      ? {
          backgroundImage:
            half === "top"
              ? `linear-gradient(to bottom, ${creamTopStart}, ${creamTopEnd})`
              : `linear-gradient(to bottom, ${creamBotStart}, ${creamBotEnd})`,
        }
      : undefined;

    const glyphSize = compact
      ? "text-[25px] sm:text-[33px] lg:text-[40px]"
      : "text-[28px] sm:text-[38px] lg:text-[46px]";

    if (
      continuousRowText &&
      frame.variant === "cream" &&
      (!isFlipping || frame.topText === spec.topText)
    ) {
      // Continuous multi-flap condensed typography across the 12 physical flaps (`4 TRAVELERS`, `CULTURE + COAST`)
      const isTravelersRow = rowIndex === 1;
      const firstChar = continuousRowText.charAt(0);
      const restText = continuousRowText.slice(1).trimStart();

      return (
        <div
          className={`relative w-full h-full overflow-hidden select-none ${bgClass}`}
          style={creamGradientStyle}
        >
          <span className="sr-only">
            {frame.topText === " " ? "\u00A0" : frame.topText}
          </span>
          <div
            aria-hidden="true"
            className="pointer-events-none absolute inset-x-0 flex items-center"
            style={{
              left: `${-colIndex * 100}%`,
              width: `${totalCols * 100}%`,
              top: half === "top" ? "100%" : "0%",
              transform: "translateY(-50%)",
            }}
          >
            {isTravelersRow ? (
              <div className="flex items-center w-full pl-[2.4%]">
                <span
                  className={`font-sans font-extrabold leading-none ${glyphSize} text-[#141a24] inline-block w-[17.5%] shrink-0`}
                  style={{
                    transform: "scaleX(0.75) scaleY(1.06)",
                    transformOrigin: "left center",
                  }}
                >
                  {firstChar}
                </span>
                <div className="flex items-center justify-between w-[71.5%] shrink-0">
                  {Array.from(restText).map((ch, idx) => (
                    <span
                      key={idx}
                      className={`font-sans font-extrabold leading-none ${glyphSize} text-[#141a24]`}
                      style={{
                        transform: "scaleX(0.74) scaleY(1.06)",
                      }}
                    >
                      {ch}
                    </span>
                  ))}
                </div>
              </div>
            ) : (
              <div className="flex items-center w-full pl-[2.1%]">
                <div className="flex items-center justify-between w-[89.5%] shrink-0">
                  {Array.from(continuousRowText).map((ch, idx) => (
                    <span
                      key={idx}
                      className={`font-sans font-extrabold leading-none ${
                        ch === "+"
                          ? "text-[20px] sm:text-[26px] lg:text-[31px] mx-[1.2%]"
                          : glyphSize
                      } text-[#141a24] ${
                        ch === " " ? "inline-block w-[4.8%]" : ""
                      }`}
                      style={{
                        transform: "scaleX(0.70) scaleY(1.06)",
                      }}
                    >
                      {ch === " " ? "\u00A0" : ch}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      );
    }

    return (
      <div
        className={`relative w-full h-full overflow-hidden select-none ${bgClass}`}
        style={creamGradientStyle}
      >
        <span
          className={`absolute left-1/2 font-sans font-extrabold leading-none ${glyphSize} ${
            half === "top" ? "bottom-0" : "top-0"
          } ${isBlurredFlip ? "blur-[1.6px] opacity-80" : ""}`}
          style={{
            transform:
              half === "top"
                ? `translate(-50%, 50%) scaleX(${compact ? 0.72 : 0.74}) scaleY(${isBlurredFlip ? 1.22 : 1.06})`
                : `translate(-50%, -50%) scaleX(${compact ? 0.72 : 0.74}) scaleY(${isBlurredFlip ? 1.22 : 1.06})`,
          }}
        >
          {frame.topText === " " ? "\u00A0" : frame.topText}
        </span>
      </div>
    );
  };

  const isYellowTwoLine = displayed.variant === "yellow_two_line";
  const isDarkBlank = displayed.variant === "dark_blank";

  return (
    <div
      className={`relative w-full h-full min-w-0 rounded-[2.5px] ${
        isYellowTwoLine
          ? "bg-[#2c2106]/65 p-0"
          : isDarkBlank
            ? "bg-[#0a0d13]/85 p-0"
            : "bg-[#1a1815]/60 p-0"
      } shadow-[0_2px_3px_rgba(0,0,0,0.45)] transition-shadow duration-200`}
      style={{
        perspective: "420px",
        boxShadow:
          highlighted && highlightColor
            ? `0 0 0 1.5px ${highlightColor}, 0 0 12px ${highlightColor}66`
            : undefined,
      }}
      data-testid={`split-flap-cell-${rowIndex}-${colIndex}`}
    >
      <div
        className="relative w-full h-full rounded-[2.5px] overflow-hidden"
        style={{
          filter: isFlipping ? "url(#split-flap-motion-blur)" : undefined,
        }}
      >
        {/* Static Upper Half */}
        <div className="absolute inset-x-0 top-0 h-1/2 overflow-hidden rounded-t-[2.5px]">
          {renderFaceContent(topStaticFrame, "top")}
        </div>

        {/* Static Lower Half */}
        <div className="absolute inset-x-0 bottom-0 h-1/2 overflow-hidden rounded-b-[2.5px]">
          {renderFaceContent(bottomStaticFrame, "bottom")}
        </div>

        {/* Rotating Upper Leaf (0deg -> -90deg) */}
        {isFlipping && flipPhase === "upper" ? (
          <div
            className="absolute inset-x-0 top-0 h-1/2 overflow-hidden rounded-t-[2.5px] z-20"
            style={{
              transformOrigin: "50% 100%",
              transform: "rotateX(-78deg)",
              transition: `transform ${Math.max(20, Math.floor(stepDurationMs / 2))}ms cubic-bezier(0.4, 0, 1, 1)`,
              backfaceVisibility: "hidden",
              boxShadow: "0 6px 10px rgba(0,0,0,0.45)",
            }}
          >
            {renderFaceContent(rotatingUpperFrame, "top")}
          </div>
        ) : null}

        {/* Rotating Lower Leaf (90deg -> 0deg) */}
        {isFlipping && flipPhase === "lower" ? (
          <div
            className="absolute inset-x-0 bottom-0 h-1/2 overflow-hidden rounded-b-[2.5px] z-20"
            style={{
              transformOrigin: "50% 0%",
              transform: "rotateX(0deg)",
              transition: `transform ${Math.max(20, Math.floor(stepDurationMs / 2))}ms cubic-bezier(0.16, 1, 0.3, 1)`,
              backfaceVisibility: "hidden",
              boxShadow: "0 -4px 8px rgba(0,0,0,0.35)",
            }}
          >
            {renderFaceContent(rotatingLowerFrame, "bottom")}
          </div>
        ) : null}

        {/* Physical 3D Mid-Flip Horizontal Leaf + Cast Shadow (matches Reference Frame 2 & Frame 4 mid-flip flaps) */}
        {displayed.variant === "blurred_flip" || isFlipping ? (
          <div
            aria-hidden="true"
            className={`pointer-events-none absolute inset-x-0 z-25 rounded-[1.5px] border-t ${
              rowIndex === 3 && colIndex <= 1 && displayed.variant === "blurred_flip"
                ? "bg-gradient-to-b from-[#9c7b34] via-[#705621] to-[#3d2d0e] border-[#e8c674]/55 shadow-[0_7px_9px_rgba(0,0,0,0.68)]"
                : "bg-gradient-to-b from-[#faf6ec] via-[#e2d6c1] to-[#b5a68e] border-white/80 shadow-[0_7px_9px_rgba(0,0,0,0.52)]"
            }`}
            style={{
              top: flipPhase === "lower" ? "48%" : "24%",
              height: "25%",
            }}
          />
        ) : null}

        {/* Ultra-faint Horizontal Split Seam (matches ground truth physical hinge line without cutting through letters) */}
        <div
          className={`pointer-events-none absolute inset-x-0 top-1/2 -translate-y-1/2 h-[1px] z-30 ${
            isYellowTwoLine
              ? "bg-[#5c4304]/22"
              : isDarkBlank
                ? "bg-black/45"
                : "bg-[#2a241c]/12"
          }`}
        />

        {/* Subtle Mechanical Hinge Notches at Left/Right Edges */}
        <div className="pointer-events-none absolute left-0 top-1/2 -translate-y-1/2 w-[1.5px] h-[3px] bg-black/28 z-40" />
        <div className="pointer-events-none absolute right-0 top-1/2 -translate-y-1/2 w-[1.5px] h-[3px] bg-black/28 z-40" />
      </div>
    </div>
  );
};
