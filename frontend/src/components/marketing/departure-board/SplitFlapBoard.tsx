"use client";

import React from "react";
import type {
  BoardRowId,
  DepartureInquiryFixture,
  FlapCellSpec,
} from "./board-fixtures";
import { computeCellStartDelayMs } from "./board-engine";
import { SplitFlapCell } from "./SplitFlapCell";
import { SplitFlapPhotoModule } from "./SplitFlapPhotoModule";

export interface SplitFlapBoardProps {
  fixture: DepartureInquiryFixture;
  isScanningDates: boolean;
  selectedRowId: BoardRowId | null;
  onSelectRow: (rowId: BoardRowId) => void;
  showProvenanceWires: boolean;
  forceTriggerKey: number;
  parallaxOffset: { x: number; y: number; rotateY: number; rotateX: number };
}

interface RowGeometryConfig {
  id: BoardRowId;
  /** Left X in 1672x941 reference coordinates */
  leftPct: number;
  /** Top Y at left edge in 1672x941 reference coordinates */
  topPct: number;
  /** Width in 1672x941 reference coordinates */
  widthPct: number;
  /** Height in 1672x941 reference coordinates */
  heightPct: number;
  /** Perspective vertical skew angle (deg) matching the horizontal steel mullions */
  skewYDeg: number;
  /** Left category plate clickable region */
  plateLeftPct: number;
  plateTopPct: number;
  plateWidthPct: number;
  plateHeightPct: number;
}

/**
 * Sub-pixel calibrated row cavities mapped directly from the 1672x941 reference frame.
 */
const ROW_GEOMETRIES: readonly RowGeometryConfig[] = [
  {
    id: "destination",
    leftPct: (876 / 1672) * 100,
    topPct: (254 / 941) * 100,
    widthPct: (480 / 1672) * 100,
    heightPct: (90 / 941) * 100,
    skewYDeg: -3.05,
    plateLeftPct: (683 / 1672) * 100,
    plateTopPct: (273 / 941) * 100,
    plateWidthPct: (184 / 1672) * 100,
    plateHeightPct: (84 / 941) * 100,
  },
  {
    id: "travelers",
    leftPct: (876 / 1672) * 100,
    topPct: (351 / 941) * 100,
    widthPct: (480 / 1672) * 100,
    heightPct: (85 / 941) * 100,
    skewYDeg: -2.01,
    plateLeftPct: (683 / 1672) * 100,
    plateTopPct: (364 / 941) * 100,
    plateWidthPct: (184 / 1672) * 100,
    plateHeightPct: (82 / 941) * 100,
  },
  {
    id: "duration",
    leftPct: (876 / 1672) * 100,
    topPct: (442 / 941) * 100,
    widthPct: (480 / 1672) * 100,
    heightPct: (84 / 941) * 100,
    skewYDeg: -1.3,
    plateLeftPct: (683 / 1672) * 100,
    plateTopPct: (451 / 941) * 100,
    plateWidthPct: (184 / 1672) * 100,
    plateHeightPct: (81 / 941) * 100,
  },
  {
    id: "dates",
    leftPct: (876 / 1672) * 100,
    topPct: (533 / 941) * 100,
    widthPct: (480 / 1672) * 100,
    heightPct: (86 / 941) * 100,
    skewYDeg: -0.35,
    plateLeftPct: (683 / 1672) * 100,
    plateTopPct: (537 / 941) * 100,
    plateWidthPct: (184 / 1672) * 100,
    plateHeightPct: (82 / 941) * 100,
  },
  {
    id: "tripStyle",
    leftPct: (876 / 1672) * 100,
    topPct: (624 / 941) * 100,
    widthPct: (481 / 1672) * 100,
    heightPct: (89 / 941) * 100,
    skewYDeg: 0.35,
    plateLeftPct: (683 / 1672) * 100,
    plateTopPct: (623 / 941) * 100,
    plateWidthPct: (184 / 1672) * 100,
    plateHeightPct: (84 / 941) * 100,
  },
];

/**
 * Sub-pixel calibrated row cavities for Frame 3 (`provenance_brief` mode, 1672x941),
 * where the Departure Board sits at x=616..1248 completely clear of the right brief drawer.
 */
const ROW_GEOMETRIES_FRAME3: readonly RowGeometryConfig[] = [
  {
    id: "destination",
    leftPct: (777 / 1672) * 100,
    topPct: (294 / 941) * 100,
    widthPct: (391 / 1672) * 100,
    heightPct: (76 / 941) * 100,
    skewYDeg: -2.4,
    plateLeftPct: (616 / 1672) * 100,
    plateTopPct: (305 / 941) * 100,
    plateWidthPct: (155 / 1672) * 100,
    plateHeightPct: (78 / 941) * 100,
  },
  {
    id: "travelers",
    leftPct: (777 / 1672) * 100,
    topPct: (375 / 941) * 100,
    widthPct: (391 / 1672) * 100,
    heightPct: (80 / 941) * 100,
    skewYDeg: -1.1,
    plateLeftPct: (616 / 1672) * 100,
    plateTopPct: (382 / 941) * 100,
    plateWidthPct: (155 / 1672) * 100,
    plateHeightPct: (77 / 941) * 100,
  },
  {
    id: "duration",
    leftPct: (777 / 1672) * 100,
    topPct: (459 / 941) * 100,
    widthPct: (391 / 1672) * 100,
    heightPct: (80 / 941) * 100,
    skewYDeg: -0.6,
    plateLeftPct: (616 / 1672) * 100,
    plateTopPct: (463 / 941) * 100,
    plateWidthPct: (155 / 1672) * 100,
    plateHeightPct: (77 / 941) * 100,
  },
  {
    id: "dates",
    leftPct: (777 / 1672) * 100,
    topPct: (542 / 941) * 100,
    widthPct: (391 / 1672) * 100,
    heightPct: (78 / 941) * 100,
    skewYDeg: 0.25,
    plateLeftPct: (616 / 1672) * 100,
    plateTopPct: (543 / 941) * 100,
    plateWidthPct: (155 / 1672) * 100,
    plateHeightPct: (77 / 941) * 100,
  },
  {
    id: "tripStyle",
    leftPct: (777 / 1672) * 100,
    topPct: (623 / 941) * 100,
    widthPct: (391 / 1672) * 100,
    heightPct: (82 / 941) * 100,
    skewYDeg: 0.85,
    plateLeftPct: (616 / 1672) * 100,
    plateTopPct: (625 / 941) * 100,
    plateWidthPct: (155 / 1672) * 100,
    plateHeightPct: (79 / 941) * 100,
  },
];

const WIRE_COLORS_BY_ROW: Partial<Record<BoardRowId, string>> = {
  destination: "#f5c418",
  travelers: "#38bdf8",
  duration: "#4ade80",
  tripStyle: "#c084fc",
};

export const SplitFlapBoard: React.FC<SplitFlapBoardProps> = ({
  fixture,
  isScanningDates,
  selectedRowId,
  onSelectRow,
  showProvenanceWires,
  forceTriggerKey,
  parallaxOffset,
}) => {
  return (
    <div
      className="pointer-events-none absolute inset-0 select-none"
      style={{
        transform: `translate3d(${parallaxOffset.x}px, ${parallaxOffset.y}px, 0) perspective(1600px) rotateY(${parallaxOffset.rotateY}deg) rotateX(${parallaxOffset.rotateX}deg)`,
        transformStyle: "preserve-3d",
        transition: "transform 180ms cubic-bezier(0.22, 1, 0.36, 1)",
      }}
      data-testid="departure-board-layer-2"
    >
      {/* Hidden SVG Filter for Vertical Mechanical Flap Motion Blur */}
      <svg className="sr-only" aria-hidden="true">
        <defs>
          <filter
            id="split-flap-motion-blur"
            x="-10%"
            y="-25%"
            width="120%"
            height="150%"
          >
            <feGaussianBlur in="SourceGraphic" stdDeviation="0, 3.6" />
          </filter>
        </defs>
      </svg>

      {/* Physical Brushed-Steel Board Chassis Cutout (SAM 3 + SAM 2.1 + ViTMatte Layer 2) */}
      <img
        src={
          showProvenanceWires
            ? "/landing/departure-board/board-chassis-frame3-layer.png"
            : "/landing/departure-board/board-chassis-layer.png"
        }
        alt="Waypoint Brushed Steel Departure Board Monument"
        className="pointer-events-none absolute inset-0 w-full h-full object-fill select-none"
        draggable={false}
      />

      {/* Swinging Physical IATA Baggage Tag on Right Rigging (ITA / JPN / MAR) */}
      <div
        key={`tag-${fixture.id}`}
        className={`pointer-events-none absolute origin-top animate-[tagSwing_480ms_cubic-bezier(0.22,1,0.36,1)] ${
          showProvenanceWires ? "opacity-0" : "opacity-100"
        }`}
        style={{
          left: `${(1480 / 1672) * 100}%`,
          top: `${(230 / 941) * 100}%`,
          width: `${(122 / 1672) * 100}%`,
          height: `${(305 / 941) * 100}%`,
        }}
        data-testid="board-hanging-iata-tag"
      >
        <img
          src={fixture.hangingTagImage}
          alt={`${fixture.tagCode} luggage tag`}
          className="w-full h-full object-fill select-none"
          draggable={false}
        />
      </div>

      {/* Interactive 5-Row Split-Flap Matrix — Built Straight-On, Placed Diagonally into Cavity */}
      {(showProvenanceWires ? ROW_GEOMETRIES_FRAME3 : ROW_GEOMETRIES).map((geo, rowIdx) => {
        const rowSpec = fixture.rows.find((r) => r.id === geo.id);
        if (!rowSpec) return null;

        const isDatesRow = geo.id === "dates";
        const activeCells: FlapCellSpec[] =
          isScanningDates && rowSpec.scanningCells
            ? rowSpec.scanningCells
            : rowSpec.cells;

        const isSelected = selectedRowId === geo.id;
        const wireColor = WIRE_COLORS_BY_ROW[geo.id];
        const isHighlighted = isSelected;
        const isCompactRow = geo.id === "tripStyle";

        return (
          <React.Fragment key={geo.id}>
            {/* Invisible Interactive Hit Target over the Left Category Plate (DESTINATION, TRAVELERS, etc.) */}
            <button
              type="button"
              onClick={() => onSelectRow(geo.id)}
              aria-label={`Inspect ${rowSpec.label} provenance`}
              className={`pointer-events-auto absolute rounded-[4px] transition-all duration-200 focus:outline-none ${
                isDatesRow && isScanningDates
                  ? "ring-2 ring-[#fbbf24] shadow-[0_0_24px_rgba(251,191,36,0.55)] bg-[#fbbf24]/10"
                  : isSelected
                    ? "ring-2 ring-[#f5c418] bg-[#f5c418]/10"
                    : "hover:bg-white/5"
              }`}
              style={{
                left: `${geo.plateLeftPct}%`,
                top: `${geo.plateTopPct}%`,
                width: `${geo.plateWidthPct}%`,
                height: `${geo.plateHeightPct}%`,
                transform: `skewY(${geo.skewYDeg}deg)`,
              }}
              data-testid={`board-plate-${geo.id}`}
            />

            {/* Straight-Built Split-Flap Row Placed Diagonally in the Steel Cavity */}
            <div
              onClick={() => onSelectRow(geo.id)}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault();
                  onSelectRow(geo.id);
                }
              }}
              aria-label={`${rowSpec.label}: ${rowSpec.fact.value}`}
              className={`pointer-events-auto absolute flex items-stretch justify-between gap-[1.5px] px-[1.5px] py-[1.5px] rounded-[4px] cursor-pointer transition-all duration-200 ${
                isDatesRow && isScanningDates
                  ? "ring-2 ring-[#fbbf24] shadow-[0_0_32px_rgba(251,191,36,0.75)] bg-[#fbbf24]/15"
                  : isSelected
                    ? "ring-2 ring-[#f5c418] shadow-[0_0_20px_rgba(245,196,24,0.35)]"
                    : "hover:ring-1 hover:ring-white/30"
              }`}
              style={{
                left: `${geo.leftPct}%`,
                top: `${geo.topPct}%`,
                width: `${geo.widthPct}%`,
                height: `${geo.heightPct}%`,
                transform: `skewY(${geo.skewYDeg}deg)`,
                transformOrigin: "left center",
              }}
              data-testid={`board-row-${geo.id}`}
            >
              {/* Split-Flap Character Cells (Scaled cleanly to fill 100% of the cavity height & width) */}
              <div className="flex-1 h-full flex items-stretch gap-[1.5px] min-w-0">
                {activeCells.map((cellSpec, colIdx) => (
                  <div
                    key={`${geo.id}-col-${colIdx}`}
                    className="flex-1 h-full min-w-0 flex"
                  >
                    <ResponsiveSplitFlapCell
                      spec={cellSpec}
                      rowIndex={rowIdx}
                      colIndex={colIdx}
                      startDelayMs={computeCellStartDelayMs(rowIdx, colIdx)}
                      compact={isCompactRow}
                      forceTriggerKey={forceTriggerKey}
                      highlighted={isHighlighted}
                      highlightColor={wireColor ?? "#f5c418"}
                    />
                  </div>
                ))}
              </div>

              {/* Embedded Double-Wide Photo Split-Flap Module (Rows 1 & 3) */}
              {rowSpec.photoFlap ? (
                <div className="w-[30.6%] h-full shrink-0 pl-[2px]">
                  <ResponsivePhotoFlap
                    src={rowSpec.photoFlap.src}
                    alt={rowSpec.photoFlap.alt}
                    caption={rowSpec.photoFlap.caption}
                    rowIndex={rowIdx}
                    startDelayMs={computeCellStartDelayMs(rowIdx, 8)}
                    forceTriggerKey={forceTriggerKey}
                  />
                </div>
              ) : null}
            </div>
          </React.Fragment>
        );
      })}

      {/* Frame 2 Scanning Badge: Signal-Yellow "Finalizing dates..." Pill Covering Row 4 End-Cap */}
      {isScanningDates ? (
        <div
          className="pointer-events-none absolute z-40 flex items-center gap-2.5 rounded-[14px] bg-[#f7ca24] border border-[#fef08a] px-5 py-3 text-[#111827] shadow-[0_12px_36px_rgba(247,202,36,0.65)]"
          style={{
            left: `${(1422 / 1672) * 100}%`,
            top: `${(543 / 941) * 100}%`,
          }}
          data-testid="finalizing-dates-pill"
        >
          <svg
            viewBox="0 0 20 20"
            className="h-4 w-4 text-[#111827] animate-spin"
            fill="none"
          >
            <circle
              cx="10"
              cy="10"
              r="7"
              stroke="currentColor"
              strokeWidth="2.2"
              strokeDasharray="3.2 3.2"
            />
          </svg>
          <span className="text-[14px] sm:text-[15px] font-bold tracking-tight text-[#111827] whitespace-nowrap">
            Finalizing dates...
          </span>
        </div>
      ) : null}

      {/* Row 5 Right End-Cap Icon Split-Flap (Flips between Palm / Torii Gate / Sahara Dunes) */}
      <div
        className={`pointer-events-none absolute p-[2px] ${
          showProvenanceWires && fixture.tripStyleIcon === "palm"
            ? "opacity-0"
            : "opacity-100"
        }`}
        style={{
          left: `${((showProvenanceWires ? 1171 : 1368) / 1672) * 100}%`,
          top: `${((showProvenanceWires ? 627 : 624) / 941) * 100}%`,
          width: `${((showProvenanceWires ? 77 : 101) / 1672) * 100}%`,
          height: `${((showProvenanceWires ? 86 : 94) / 941) * 100}%`,
          transform: showProvenanceWires ? "skewY(0.85deg)" : "skewY(0.35deg)",
          transformOrigin: "left center",
        }}
        data-testid="board-trip-style-icon-flap"
      >
        <TripStyleIconFlap icon={fixture.tripStyleIcon} />
      </div>
    </div>
  );
};

/**
 * Wrapper that stretches SplitFlapCell to 100% of its cavity cell slot while preserving
 * the exact 4-plane 3D hinge geometry and typography proportions.
 */
const ResponsiveSplitFlapCell: React.FC<{
  spec: FlapCellSpec;
  rowIndex: number;
  colIndex: number;
  startDelayMs: number;
  compact: boolean;
  forceTriggerKey: number;
  highlighted: boolean;
  highlightColor: string;
}> = (props) => {
  return (
    <div className="w-full h-full [&>div]:!w-full [&>div]:!h-full">
      <SplitFlapCell {...props} />
    </div>
  );
};

const ResponsivePhotoFlap: React.FC<{
  src: string;
  alt: string;
  caption?: string;
  rowIndex: number;
  startDelayMs: number;
  forceTriggerKey: number;
}> = (props) => {
  return (
    <div className="w-full h-full [&>div]:!w-full [&>div]:!h-full">
      <SplitFlapPhotoModule {...props} />
    </div>
  );
};

const TripStyleIconFlap: React.FC<{
  icon: DepartureInquiryFixture["tripStyleIcon"];
}> = ({ icon }) => {
  return (
    <div className="relative w-full h-full rounded-[4px] bg-[#141923] border border-white/10 shadow-[inset_0_2px_5px_rgba(0,0,0,0.85)] flex items-center justify-center overflow-hidden">
      {icon === "palm" ? (
        <svg
          viewBox="0 0 36 36"
          className="w-[56%] h-[56%] text-[#f3ead8]"
          fill="currentColor"
          aria-label="Coast Palm Icon"
        >
          <path d="M18.8 14.2c-1.1 3.9-1.7 8.9-1.8 15.8h3.4c-.1-6.7.5-11.7 1.6-15.6 2.8.8 5.6 2.5 7.4 4.8.4-.9.5-2.1.1-3.3-.8-2.3-3.2-4.1-6.2-4.7 2.4-1.6 5.4-2.1 8.2-1.3-.4-1.2-1.3-2.3-2.6-3-2.6-1.4-5.9-1.1-8.5.7.9-2.2 2.9-3.9 5.3-4.5-1.2-.6-2.7-.8-4.2-.3-2.4.7-4.3 2.6-5 5-.7-2.4-2.6-4.3-5-5-1.5-.5-3-.3-4.2.3 2.4.6 4.4 2.3 5.3 4.5-2.6-1.8-5.9-2.1-8.5-.7-1.3.7-2.2 1.8-2.6 3 2.8-.8 5.8-.3 8.2 1.3-3 .6-5.4 2.4-6.2 4.7-.4 1.2-.3 2.4.1 3.3 1.8-2.3 4.6-4 7.4-4.8z" />
        </svg>
      ) : icon === "torii" ? (
        <svg
          viewBox="0 0 36 36"
          className="w-[58%] h-[58%] text-[#f3ead8]"
          fill="currentColor"
          aria-label="Japan Torii Gate Icon"
        >
          <path d="M4 8.5c4.5 1.2 9.2 1.8 14 1.8s9.5-.6 14-1.8l1.2 2.7c-3.2.9-6.6 1.5-10.2 1.7v3.1h5.5v2.6H23v11.4h-3V18.6h-4v11.4h-3V18.6H7.5V16H13v-3.1c-3.6-.2-7-.8-10.2-1.7L4 8.5zm12 4.5v3h4v-3c-.7 0-1.3.1-2 .1s-1.3 0-2-.1z" />
        </svg>
      ) : (
        <svg
          viewBox="0 0 36 36"
          className="w-[58%] h-[58%] text-[#f3ead8]"
          fill="currentColor"
          aria-label="Morocco Desert Dunes Icon"
        >
          <circle cx="24" cy="11" r="4.2" />
          <path d="M4 26.5c4.2-4.8 8.6-6.2 13.2-4.2 3.4 1.5 6.8 1.2 10.2-.9 1.8-1.1 3.3-1.3 4.6-.6v6.2H4v-.5zm0-4.2c3.5-3.4 7.3-4.3 11.4-2.7 2.8 1.1 5.6 1 8.4-.3-2.4-.5-4.8-.1-7.2 1.1-4.1 2-8.3 2.6-12.6 1.9z" />
        </svg>
      )}
      {/* Center horizontal split seam across the icon flap */}
      <div className="pointer-events-none absolute inset-x-0 top-1/2 -translate-y-1/2 h-[1.5px] bg-[#080b11]/90" />
    </div>
  );
};
