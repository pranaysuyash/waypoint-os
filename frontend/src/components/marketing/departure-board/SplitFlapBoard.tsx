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
  isDatesConfirmed?: boolean;
  selectedRowId: BoardRowId | null;
  onSelectRow: (rowId: BoardRowId) => void;
  showProvenanceWires: boolean;
  forceTriggerKey: number;
  rowForceKeys?: Partial<Record<BoardRowId, number>>;
  parallaxOffset: { x: number; y: number; rotateY: number; rotateX: number };
}

export interface QuadCorners {
  /** Top-left (x, y) in 1672x941 reference coordinates */
  tl: readonly [number, number];
  /** Top-right (x, y) in 1672x941 reference coordinates */
  tr: readonly [number, number];
  /** Bottom-right (x, y) in 1672x941 reference coordinates */
  br: readonly [number, number];
  /** Bottom-left (x, y) in 1672x941 reference coordinates */
  bl: readonly [number, number];
}

interface RowGeometryConfig {
  id: BoardRowId;
  /** Exact 4-corner perspective quadrilateral of the recessed split-flap cavity in 1672x941 space */
  quad: QuadCorners;
  /** Left category plate clickable region */
  plateLeftPct: number;
  plateTopPct: number;
  plateWidthPct: number;
  plateHeightPct: number;
  plateSkewYDeg: number;
}

/**
 * Solves the exact 2D projective homography mapping the rectangle `(0, 0)..(W, H)`
 * onto arbitrary destination quad `(x0, y0), (x1, y1), (x2, y2), (x3, y3)` in `1672x941` space
 * and returns a CSS `matrix3d(...)` string.
 * Because 2D projective homography is invariant under uniform/anisotropic scaling when conjugated
 * or when operating in a canonical 1672x941 coordinate plane, we render the board in an exact
 * `1672x941` coordinate space scaled via ResizeObserver / CSS so every row's 4 corners lock
 * sub-pixel-accurately to the SAM 3 / SAM 2.1 / ViTMatte steel cavity corners!
 */
export function computeHomographyMatrix3d(
  w: number,
  h: number,
  quad: QuadCorners
): string {
  const [x0, y0] = quad.tl;
  const [x1, y1] = quad.tr;
  const [x2, y2] = quad.br;
  const [x3, y3] = quad.bl;

  const dx1 = x1 - x2;
  const dx2 = x3 - x2;
  const dx3 = x0 - x1 + x2 - x3;
  const dy1 = y1 - y2;
  const dy2 = y3 - y2;
  const dy3 = y0 - y1 + y2 - y3;

  const det = dx1 * dy2 - dx2 * dy1;
  if (Math.abs(det) < 1e-9) {
    return `translate3d(${x0}px, ${y0}px, 0)`;
  }

  const g = (dx3 * dy2 - dx2 * dy3) / det;
  const hCoeff = (dx1 * dy3 - dx3 * dy1) / det;

  const a = x1 - x0 + g * x1;
  const b = x3 - x0 + hCoeff * x3;
  const c = x0;
  const d = y1 - y0 + g * y1;
  const e = y3 - y0 + hCoeff * y3;
  const f = y0;

  // Scale source basis from unit square [0,1]x[0,1] to [0,w]x[0,h]
  const m11 = a / w;
  const m21 = d / w;
  const m41 = g / w;

  const m12 = b / h;
  const m22 = e / h;
  const m42 = hCoeff / h;

  // Column-major 4x4 CSS matrix3d:
  return `matrix3d(${m11}, ${m21}, 0, ${m41}, ${m12}, ${m22}, 0, ${m42}, 0, 0, 1, 0, ${c}, ${f}, 0, 1)`;
}

const CANONICAL_ROW_W = 477;
const CANONICAL_ROW_H = 82;

/**
 * Exact 4-corner perspective quadrilaterals measured from the dark recessed steel channels
 * of `chatgpt-concept-2026-10-26-1.png`, `2.png`, and `4.png` (`1672x941`).
 * Notice how the right edge (`x=1358`) expands from `82px` tall to `86px` tall due to the
 * 3D camera frustum, while the top and bottom mullions converge toward the left vanishing point!
 */
const ROW_GEOMETRIES: readonly RowGeometryConfig[] = [
  {
    id: "destination",
    quad: {
      tl: [881, 272],
      tr: [1358, 244],
      br: [1358, 333],
      bl: [881, 351],
    },
    plateLeftPct: (683 / 1672) * 100,
    plateTopPct: (273 / 941) * 100,
    plateWidthPct: (184 / 1672) * 100,
    plateHeightPct: (84 / 941) * 100,
    plateSkewYDeg: -2.85,
  },
  {
    id: "travelers",
    quad: {
      tl: [881, 360],
      tr: [1358, 342],
      br: [1358, 425],
      bl: [881, 437],
    },
    plateLeftPct: (683 / 1672) * 100,
    plateTopPct: (364 / 941) * 100,
    plateWidthPct: (184 / 1672) * 100,
    plateHeightPct: (82 / 941) * 100,
    plateSkewYDeg: -1.9,
  },
  {
    id: "duration",
    quad: {
      tl: [881, 447],
      tr: [1358, 436],
      br: [1358, 521],
      bl: [881, 524],
    },
    plateLeftPct: (683 / 1672) * 100,
    plateTopPct: (451 / 941) * 100,
    plateWidthPct: (184 / 1672) * 100,
    plateHeightPct: (81 / 941) * 100,
    plateSkewYDeg: -1.15,
  },
  {
    id: "dates",
    quad: {
      tl: [881, 535],
      tr: [1358, 531],
      br: [1358, 619],
      bl: [881, 614],
    },
    plateLeftPct: (683 / 1672) * 100,
    plateTopPct: (537 / 941) * 100,
    plateWidthPct: (184 / 1672) * 100,
    plateHeightPct: (82 / 941) * 100,
    plateSkewYDeg: -0.35,
  },
  {
    id: "tripStyle",
    quad: {
      tl: [881, 626],
      tr: [1358, 631],
      br: [1358, 716],
      bl: [881, 704],
    },
    plateLeftPct: (683 / 1672) * 100,
    plateTopPct: (623 / 941) * 100,
    plateWidthPct: (184 / 1672) * 100,
    plateHeightPct: (84 / 941) * 100,
    plateSkewYDeg: 0.65,
  },
];

/**
 * Exact 4-corner perspective quadrilaterals for Frame 3 (`provenance_brief` mode, `1672x941`),
 * where the Departure Board sits at `x=616..1248` completely clear of the right brief drawer.
 */
const ROW_GEOMETRIES_FRAME3: readonly RowGeometryConfig[] = [
  {
    id: "destination",
    quad: {
      tl: [782, 301],
      tr: [1148, 281],
      br: [1148, 358],
      bl: [782, 370],
    },
    plateLeftPct: (616 / 1672) * 100,
    plateTopPct: (305 / 941) * 100,
    plateWidthPct: (155 / 1672) * 100,
    plateHeightPct: (78 / 941) * 100,
    plateSkewYDeg: -2.35,
  },
  {
    id: "travelers",
    quad: {
      tl: [782, 380],
      tr: [1148, 368],
      br: [1148, 444],
      bl: [782, 451],
    },
    plateLeftPct: (616 / 1672) * 100,
    plateTopPct: (382 / 941) * 100,
    plateWidthPct: (155 / 1672) * 100,
    plateHeightPct: (77 / 941) * 100,
    plateSkewYDeg: -1.6,
  },
  {
    id: "duration",
    quad: {
      tl: [782, 462],
      tr: [1148, 454],
      br: [1148, 530],
      bl: [782, 531],
    },
    plateLeftPct: (616 / 1672) * 100,
    plateTopPct: (463 / 941) * 100,
    plateWidthPct: (155 / 1672) * 100,
    plateHeightPct: (77 / 941) * 100,
    plateSkewYDeg: -0.8,
  },
  {
    id: "dates",
    quad: {
      tl: [782, 543],
      tr: [1148, 541],
      br: [1148, 619],
      bl: [782, 616],
    },
    plateLeftPct: (616 / 1672) * 100,
    plateTopPct: (543 / 941) * 100,
    plateWidthPct: (155 / 1672) * 100,
    plateHeightPct: (77 / 941) * 100,
    plateSkewYDeg: 0.05,
  },
  {
    id: "tripStyle",
    quad: {
      tl: [782, 627],
      tr: [1148, 632],
      br: [1148, 713],
      bl: [782, 702],
    },
    plateLeftPct: (616 / 1672) * 100,
    plateTopPct: (625 / 941) * 100,
    plateWidthPct: (155 / 1672) * 100,
    plateHeightPct: (79 / 941) * 100,
    plateSkewYDeg: 0.85,
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
  isDatesConfirmed = false,
  selectedRowId,
  onSelectRow,
  showProvenanceWires,
  forceTriggerKey,
  rowForceKeys,
  parallaxOffset,
}) => {
  const containerRef = React.useRef<HTMLDivElement>(null);
  const [stageScale, setStageScale] = React.useState<{ sx: number; sy: number }>({
    sx: 1,
    sy: 1,
  });

  React.useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const updateScale = () => {
      const rect = el.getBoundingClientRect();
      if (rect.width > 0 && rect.height > 0) {
        setStageScale({
          sx: rect.width / 1672,
          sy: rect.height / 941,
        });
      }
    };
    updateScale();
    if (typeof ResizeObserver !== "undefined") {
      const ro = new ResizeObserver(updateScale);
      ro.observe(el);
      return () => ro.disconnect();
    }
    window.addEventListener("resize", updateScale);
    return () => window.removeEventListener("resize", updateScale);
  }, []);

  return (
    <div
      ref={containerRef}
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

      {/* Swinging Physical IATA Baggage Tag on Right Rigging (ITA / JPN / MAR + Dynamic Catalog IATA Codes) */}
      <div
        key={`tag-${fixture.pillTitle}-${fixture.tagCode}`}
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
        data-iata-code={fixture.tagCode}
      >
        <img
          src={fixture.hangingTagImage}
          alt={`${fixture.tagCode} luggage tag`}
          className="w-full h-full object-fill select-none"
          draggable={false}
        />
        {!["ITA", "JPN", "MAR"].includes(fixture.tagCode) ? (
          <svg
            viewBox="0 0 84 36"
            className="absolute overflow-visible select-none"
            style={{
              left: "39.5%",
              top: "71.2%",
              width: "42%",
              height: "13.5%",
              transform: "rotate(-11.5deg) skewX(-5deg)",
              mixBlendMode: "multiply",
            }}
            aria-hidden="true"
          >
            <text
              x="42"
              y="27"
              textAnchor="middle"
              fill="#17191c"
              fontFamily="'Inter', 'Oswald', 'Arial Narrow', sans-serif"
              fontWeight="900"
              fontSize="27"
              letterSpacing="-0.8"
            >
              {fixture.tagCode}
            </text>
          </svg>
        ) : null}
      </div>

      {/* Interactive 5-Row Split-Flap Matrix — Built Straight-On, Placed Diagonally into Cavity */}
      {(showProvenanceWires ? ROW_GEOMETRIES_FRAME3 : ROW_GEOMETRIES).map((geo, rowIdx) => {
        const rowSpec = fixture.rows.find((r) => r.id === geo.id);
        if (!rowSpec) return null;

        const isDatesRow = geo.id === "dates";
        const activeCells: FlapCellSpec[] =
          isScanningDates && rowSpec.scanningCells
            ? rowSpec.scanningCells
            : isDatesRow && isDatesConfirmed && rowSpec.confirmedCells
              ? rowSpec.confirmedCells
              : rowSpec.cells;

        const isSelected = selectedRowId === geo.id;
        const wireColor = WIRE_COLORS_BY_ROW[geo.id];
        const isHighlighted = isSelected;
        const isCompactRow = geo.id === "tripStyle";
        const effectiveRowForceKey =
          forceTriggerKey + (rowForceKeys?.[geo.id] ?? 0);

        // Continuous multi-flap row banner text for Rows 2 (`4 TRAVELERS`) and 5 (`CULTURE + COAST`)
        // so the 12 physical flaps (`~40px` wide) align 1:1 with the columns above and below while
        // displaying full condensed words across the row (including the `+` sign in Frame 3)!
        const baseRowText = rowSpec.cells.map((c) => c.topText).join("").trimEnd();
        const continuousRowText =
          geo.id === "travelers" || geo.id === "tripStyle"
            ? baseRowText
            : undefined;
        const displayCells =
          geo.id === "tripStyle" && !isScanningDates && activeCells.length > 12
            ? activeCells.slice(0, 12)
            : activeCells;

        const scaledQuad: QuadCorners = {
          tl: [geo.quad.tl[0] * stageScale.sx, geo.quad.tl[1] * stageScale.sy],
          tr: [geo.quad.tr[0] * stageScale.sx, geo.quad.tr[1] * stageScale.sy],
          br: [geo.quad.br[0] * stageScale.sx, geo.quad.br[1] * stageScale.sy],
          bl: [geo.quad.bl[0] * stageScale.sx, geo.quad.bl[1] * stageScale.sy],
        };
        const homographyTransform = computeHomographyMatrix3d(
          CANONICAL_ROW_W,
          CANONICAL_ROW_H,
          scaledQuad
        );

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
                transform: `skewY(${geo.plateSkewYDeg}deg)`,
              }}
              data-testid={`board-plate-${geo.id}`}
            />

            {/* Straight-Built Split-Flap Row Projected via Exact 8-DOF 2D Homography (`matrix3d`) into the 4-Corner Steel Cavity */}
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
              className={`pointer-events-auto absolute left-0 top-0 flex items-stretch justify-between gap-[1px] rounded-[3px] cursor-pointer transition-shadow duration-200 ${
                isDatesRow && isScanningDates
                  ? "ring-2 ring-[#fbbf24] shadow-[0_0_32px_rgba(251,191,36,0.75)] bg-[#fbbf24]/15"
                  : isSelected
                    ? "ring-2 ring-[#f5c418] shadow-[0_0_20px_rgba(245,196,24,0.35)]"
                    : "hover:ring-1 hover:ring-white/30"
              }`}
              style={{
                width: `${CANONICAL_ROW_W}px`,
                height: `${CANONICAL_ROW_H}px`,
                transformOrigin: "0 0",
                transform: homographyTransform,
              }}
              data-testid={`board-row-${geo.id}`}
            >
              {/*Split-Flap Character Cells (Exact 36-unit Solari chassis grid so 8 yellow = 24u and 3 dark = 12u) */}
              <div
                className={`${
                  rowSpec.photoFlap ? "w-[66.6667%] shrink-0" : "flex-1"
                } h-full grid gap-[1px] min-w-0`}
                style={{
                  gridTemplateColumns:
                    rowSpec.photoFlap
                      ? "repeat(8, minmax(0, 1fr))"
                      : isDatesRow
                        ? "repeat(36, minmax(0, 1fr))"
                        : `repeat(${displayCells.length}, minmax(0, 1fr))`,
                }}
              >
                {displayCells.map((cellSpec, colIdx) => {
                  const isDarkBlankInDates =
                    isDatesRow && !isScanningDates && cellSpec.variant === "dark_blank";
                  const isScanningWideTailInDates =
                    isDatesRow && isScanningDates && colIdx >= 8;

                  return (
                    <div
                      key={`${geo.id}-col-${colIdx}`}
                      className="h-full min-w-0 flex"
                      style={
                        isDatesRow
                          ? {
                              gridColumn: isDarkBlankInDates
                                ? "span 4 / span 4"
                                : isScanningWideTailInDates
                                  ? "span 6 / span 6"
                                  : "span 3 / span 3",
                            }
                          : undefined
                      }
                    >
                      <ResponsiveSplitFlapCell
                        spec={cellSpec}
                        rowIndex={rowIdx}
                        colIndex={colIdx}
                        totalCols={rowSpec.photoFlap ? 12 : displayCells.length}
                        continuousRowText={continuousRowText}
                        startDelayMs={computeCellStartDelayMs(rowIdx, colIdx)}
                        compact={isCompactRow}
                        forceTriggerKey={effectiveRowForceKey}
                        highlighted={isHighlighted}
                        highlightColor={wireColor ?? "#f5c418"}
                      />
                    </div>
                  );
                })}
              </div>

              {/* Embedded Double-Wide Photo Split-Flap Module (Rows 1 & 3 — spans 4 of 12 columns = 33.3333%) */}
              {rowSpec.photoFlap ? (
                <div className="w-[33.3333%] h-full shrink-0 pl-[1px]">
                  <ResponsivePhotoFlap
                    src={rowSpec.photoFlap.src}
                    alt={rowSpec.photoFlap.alt}
                    caption={rowSpec.photoFlap.caption}
                    rowIndex={rowIdx}
                    startDelayMs={computeCellStartDelayMs(rowIdx, 8)}
                    forceTriggerKey={effectiveRowForceKey}
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

      {/* Row 5 Right End-Cap Icon Split-Flap (Preserves native 3D palm flap in chassis for Italy; overlays inside recess for Torii / Dunes) */}
      <div
        className={`pointer-events-none absolute p-[1px] ${
          fixture.tripStyleIcon === "palm" ? "opacity-0" : "opacity-100"
        }`}
        style={{
          left: `${((showProvenanceWires ? 1166 : 1372) / 1672) * 100}%`,
          top: `${((showProvenanceWires ? 631 : 631) / 941) * 100}%`,
          width: `${((showProvenanceWires ? 68 : 92) / 1672) * 100}%`,
          height: `${((showProvenanceWires ? 75 : 79) / 941) * 100}%`,
          transform: showProvenanceWires ? "skewY(0.85deg)" : "skewY(0.65deg)",
          transformOrigin: "left top",
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
  totalCols?: number;
  continuousRowText?: string;
  startDelayMs: number;
  compact: boolean;
  forceTriggerKey: number;
  highlighted: boolean;
  highlightColor: string;
}> = (props) => {
  return (
    <div className="w-full h-full min-w-0 [&>div]:!w-full [&>div]:!h-full [&>div]:!min-w-0">
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
