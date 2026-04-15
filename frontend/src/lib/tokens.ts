/**
 * Design System Tokens
 *
 * Centralized design tokens for colors, spacing, typography, elevation, and animation.
 * All hardcoded values should be replaced with these tokens.
 */

// ============================================================================
// COLORS
// ============================================================================

export const COLORS = {
  // Backgrounds - Cartographic Dark
  bgCanvas: "#080a0c",
  bgSurface: "#0f1115",
  bgElevated: "#161b22",
  bgHighlight: "#1c2128",
  bgInput: "#111318",

  // Text
  textPrimary: "#e6edf3",
  textSecondary: "#8b949e",
  textTertiary: "#6e7681",
  textMuted: "#484f58",

  // Accents - State Colors
  accentGreen: "#3fb950",
  accentAmber: "#d29922",
  accentRed: "#f85149",
  accentBlue: "#58a6ff",
  accentPurple: "#a371f7",
  accentCyan: "#39d0d8",
  accentOrange: "#ff9248",

  // Geographic Colors
  geoLand: "#1c2128",
  geoWater: "#0d2137",
  geoRoute: "#39d0d8",
  geoRouteDim: "#1a3a3f",
  geoWaypoint: "#d29922",
  geoDestination: "#3fb950",

  // Borders
  borderDefault: "#30363d",
  borderHover: "#8b949e",
  borderActive: "#58a6ff",
} as const;

// ============================================================================
// STATE COLORS (with backgrounds and borders)
// ============================================================================

export const STATE_COLORS = {
  green: {
    color: COLORS.accentGreen,
    bg: "rgba(63, 185, 80, 0.1)",
    border: "rgba(63, 185, 80, 0.3)",
  },
  amber: {
    color: COLORS.accentAmber,
    bg: "rgba(210, 153, 34, 0.1)",
    border: "rgba(210, 153, 34, 0.3)",
  },
  red: {
    color: COLORS.accentRed,
    bg: "rgba(248, 81, 73, 0.1)",
    border: "rgba(248, 81, 73, 0.3)",
  },
  blue: {
    color: COLORS.accentBlue,
    bg: "rgba(88, 166, 255, 0.1)",
    border: "rgba(88, 166, 255, 0.3)",
  },
  purple: {
    color: COLORS.accentPurple,
    bg: "rgba(163, 113, 247, 0.1)",
    border: "rgba(163, 113, 247, 0.3)",
  },
  neutral: {
    color: COLORS.textSecondary,
    bg: "rgba(139, 148, 158, 0.08)",
    border: "rgba(139, 148, 158, 0.15)",
  },
} as const;

// ============================================================================
// SPACING
// ============================================================================

export const SPACING = {
  0: "0px",
  1: "4px",
  2: "8px",
  3: "12px",
  4: "16px",
  5: "20px",
  6: "24px",
  8: "32px",
  10: "40px",
  12: "48px",
  16: "64px",
  20: "80px",
  24: "96px",
} as const;

// ============================================================================
// TYPOGRAPHY
// ============================================================================

export const FONT_FAMILY = {
  display: "var(--font-display)",
  mono: "var(--font-mono)",
  data: "var(--font-data)",
} as const;

export const FONT_SIZE = {
  xs: "10px",
  sm: "11px",
  base: "12px",
  md: "13px",
  lg: "14px",
  xl: "15px",
  "2xl": "16px",
  "3xl": "18px",
  "4xl": "20px",
} as const;

export const FONT_WEIGHT = {
  normal: "400",
  medium: "500",
  semibold: "600",
  bold: "700",
} as const;

export const LINE_HEIGHT = {
  tight: "1.25",
  normal: "1.5",
  relaxed: "1.75",
} as const;

// ============================================================================
// ELEVATION (Box Shadows)
// ============================================================================

export const ELEVATION = {
  none: "none",
  sm: "0 1px 2px rgba(0, 0, 0, 0.3)",
  md: "0 4px 6px rgba(0, 0, 0, 0.3)",
  lg: "0 10px 15px rgba(0, 0, 0, 0.3)",
  xl: "0 20px 25px rgba(0, 0, 0, 0.3)",
  glow: {
    blue: "0 0 20px rgba(88, 166, 255, 0.15)",
    amber: "0 0 20px rgba(210, 153, 34, 0.2)",
    green: "0 0 20px rgba(63, 185, 80, 0.15)",
    red: "0 0 20px rgba(248, 81, 73, 0.15)",
    cyan: "0 0 20px rgba(57, 208, 216, 0.2)",
  },
} as const;

// ============================================================================
// BORDER RADIUS
// ============================================================================

export const RADIUS = {
  none: "0",
  sm: "4px",
  md: "6px",
  lg: "8px",
  xl: "12px",
  "2xl": "16px",
  full: "9999px",
} as const;

// ============================================================================
// TRANSITION
// ============================================================================

export const TRANSITION = {
  fast: "150ms ease",
  base: "200ms ease",
  slow: "300ms ease",
} as const;

// ============================================================================
// LAYOUT
// ============================================================================

export const LAYOUT = {
  sidebarWidth: "220px",
  headerHeight: "56px",
  commandBarHeight: "44px",
  mobileNavHeight: "56px",
  maxWidth: "1400px",
} as const;

// ============================================================================
// Z-INDEX
// ============================================================================

export const Z_INDEX = {
  base: 0,
  dropdown: 10,
  sticky: 20,
  overlay: 30,
  modal: 40,
  tooltip: 50,
} as const;

// ============================================================================
// BREAKPOINTS (Tailwind defaults for reference)
// ============================================================================

export const BREAKPOINTS = {
  sm: "640px",
  md: "768px",
  lg: "1024px",
  xl: "1280px",
  "2xl": "1536px",
} as const;

// ============================================================================
// TYPE EXPORTS
// ============================================================================

export type ColorKey = keyof typeof COLORS;
export type StateColorKey = keyof typeof STATE_COLORS;
export type SpacingKey = keyof typeof SPACING;
export type FontSizeKey = keyof typeof FONT_SIZE;
export type FontWeightKey = keyof typeof FONT_WEIGHT;
export type RadiusKey = keyof typeof RADIUS;
export type ElevationKey = keyof typeof ELEVATION;
