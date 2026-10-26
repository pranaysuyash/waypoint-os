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

  const renderFaceContent = (
    frame: FlapStepFrame,
    half: "top" | "bottom"
  ): React.ReactNode => {
    if (frame.variant === "yellow_two_line") {
      return (
        <div
          className={`w-full h-full flex flex-col items-center justify-center select-none ${
            half === "top"
              ? "bg-gradient-to-b from-[#fad02c] to-[#efb913]"
              : "bg-gradient-to-b from-[#e6ae0e] to-[#d99f07]"
          }`}
        >
          {half === "top" ? (
            <span
              className="font-sans font-black text-[#141a24] text-[18px] sm:text-[22px] lg:text-[26px] leading-none uppercase"
              style={{ transform: "scaleX(0.84) scaleY(1.08)" }}
            >
              {frame.topText}
            </span>
          ) : (
            <div className="flex flex-col items-center justify-center w-full leading-none">
              <span
                className="font-sans font-black text-[#141a24] text-[17px] sm:text-[20px] lg:text-[24px] tracking-[0.05em] leading-none uppercase"
                style={{ transform: "scaleX(0.85) scaleY(1.08)" }}
              >
                {frame.bottomText ?? ""}
              </span>
            </div>
          )}
        </div>
      );
    }

    const isBlurredFlip = frame.variant === "blurred_flip";
    const isDarkRow4Blur = isBlurredFlip && rowIndex === 3 && colIndex <= 1;

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
                ? "bg-gradient-to-b from-[#1f2633] to-[#181e29] text-[#64748b]"
                : "bg-gradient-to-b from-[#151a24] to-[#11161f] text-[#64748b]"
              : half === "top"
                ? "bg-gradient-to-b from-[#f7f3e9] to-[#ece5d5] text-[#151c28]"
                : "bg-gradient-to-b from-[#e6dfd0] to-[#ddd4c2] text-[#151c28]";

    const glyphSize = compact
      ? "text-[20px] sm:text-[25px] lg:text-[31px]"
      : "text-[27px] sm:text-[36px] lg:text-[45px]";

    return (
      <div className={`relative w-full h-full overflow-hidden select-none ${bgClass}`}>
        <span
          className={`absolute left-1/2 font-sans font-extrabold leading-none ${glyphSize} ${
            half === "top" ? "bottom-0" : "top-0"
          } ${isBlurredFlip ? "blur-[1.6px] opacity-80" : ""}`}
          style={{
            transform:
              half === "top"
                ? `translate(-50%, 50%) scaleX(0.74) scaleY(${isBlurredFlip ? 1.24 : 1.08})`
                : `translate(-50%, -50%) scaleX(0.74) scaleY(${isBlurredFlip ? 1.24 : 1.08})`,
          }}
        >
          {frame.topText === " " ? "\u00A0" : frame.topText}
        </span>
      </div>
    );
  };

  const isYellowTwoLine = displayed.variant === "yellow_two_line";

  return (
    <div
      className={`relative rounded-[3px] ${
        isYellowTwoLine ? "bg-[#3b2c08]/75 p-[0.5px]" : "bg-[#0e131d]/85 p-[0.75px]"
      } shadow-[inset_0_1px_2px_rgba(0,0,0,0.65)] transition-shadow duration-200 ${
        compact
          ? "w-[22px] sm:w-[25.5px] h-[44px] sm:h-[50px]"
          : "w-[31px] sm:w-[36.5px] h-[44px] sm:h-[50px]"
      }`}
      style={{
        perspective: "420px",
        boxShadow: highlighted && highlightColor
          ? `0 0 0 1.5px ${highlightColor}, 0 0 12px ${highlightColor}66, inset 0 1px_2px rgba(0,0,0,0.65)`
          : undefined,
      }}
      data-testid={`split-flap-cell-${rowIndex}-${colIndex}`}
    >
      <div
        className="relative w-full h-full rounded-[2px] overflow-hidden"
        style={{
          filter: isFlipping ? "url(#split-flap-motion-blur)" : undefined,
        }}
      >
        {/* Static Upper Half */}
        <div className="absolute inset-x-0 top-0 h-[calc(50%-0.5px)] overflow-hidden rounded-t-[2px]">
          {renderFaceContent(topStaticFrame, "top")}
        </div>

        {/* Static Lower Half */}
        <div className="absolute inset-x-0 bottom-0 h-[calc(50%-0.5px)] overflow-hidden rounded-b-[2px]">
          {renderFaceContent(bottomStaticFrame, "bottom")}
        </div>

        {/* Rotating Upper Leaf (0deg -> -90deg) */}
        {isFlipping && flipPhase === "upper" ? (
          <div
            className="absolute inset-x-0 top-0 h-[calc(50%-0.5px)] overflow-hidden rounded-t-[2px] z-20"
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
            className="absolute inset-x-0 bottom-0 h-[calc(50%-0.5px)] overflow-hidden rounded-b-[2px] z-20"
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

        {/* Center Horizontal Split Gap & Hinge Shadow (subtle hairline, no strikethrough) */}
        <div
          className={`pointer-events-none absolute inset-x-0 top-1/2 -translate-y-1/2 h-[1px] z-30 ${
            isYellowTwoLine ? "bg-[#7a5804]/30" : "bg-[#090d14]/28"
          }`}
        />

        {/* Subtle Dark Mechanical Hinge Notches (no bright silver dash artifact) */}
        <div className="pointer-events-none absolute left-0 top-1/2 -translate-y-1/2 w-[1px] h-[2.5px] bg-black/30 z-40" />
        <div className="pointer-events-none absolute right-0 top-1/2 -translate-y-1/2 w-[1px] h-[2.5px] bg-black/30 z-40" />
      </div>
    </div>
  );
};
