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
  // Backgrounds - Cartographic Dark (OKLCH - matching globals.css)
  bgCanvas: "oklch(2.5% 0.008 260)",       // was #080a0c
  bgSurface: "oklch(4.5% 0.009 260)",     // was #0f1115
  bgElevated: "oklch(7% 0.009 260)",      // was #161b22
  bgHighlight: "oklch(9% 0.01 260)",       // was #1c2128
  bgInput: "oklch(4.2% 0.008 260)",      // was #111318
  
  // Text - WCAG AA compliant on dark backgrounds (4.5:1 minimum)
  textPrimary: "oklch(90% 0.012 260)",      // was #e6edf3 - 15.4:1 on bgCanvas
  textSecondary: "oklch(72% 0.01 260)",    // was #a8b3c1 - 5.2:1 on bgCanvas
  textTertiary: "oklch(66% 0.009 260)",   // was #9ba3b0 - ~4.5:1
  textMuted: "oklch(58% 0.008 260)",      // was #8b949e - 3.9:1 - For large text only
  
  // Accents - State Colors (OKLCH)
  accentGreen: "oklch(65% 0.15 155)",    // was #3fb950
  accentAmber: "oklch(70% 0.18 80)",    // was #d29922
  accentRed: "oklch(60% 0.22 25)",      // was #f85149
  accentBlue: "oklch(76% 0.14 265)",    // was #58a6ff - proper OKLCH from DESIGN.md
  accentPurple: "oklch(68% 0.2 295)",    // was #a371f7 - proper OKLCH from DESIGN.md
  accentCyan: "oklch(76% 0.12 210)",     // was #39d0d8 - proper OKLCH from DESIGN.md
  accentOrange: "oklch(74% 0.2 50)",    // was #ff9248 - proper OKLCH from DESIGN.md
  
  // Geographic Colors (OKLCH)
  geoLand: "oklch(8% 0.008 260)",        // was #1c2128
  geoWater: "oklch(4.5% 0.008 260)",    // was #0d2137
  geoRoute: "oklch(80% 0.12 210)",      // was #39d0d8
  geoRouteDim: "oklch(7% 0.01 210)",      // was #1a3a3f
  geoWaypoint: "oklch(70% 0.18 80)",     // was #d29922
  geoDestination: "oklch(65% 0.15 155)", // was #3fb950
  
  // Borders (OKLCH)
  borderDefault: "oklch(18% 0.01 260)",    // was #30363d
  borderHover: "oklch(38% 0.012 260)",    // was #8b949e
  borderActive: "oklch(85% 0.15 265)",    // was #58a6ff
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
  xs: "12px",    // Small labels, captions (minimum readable)
  sm: "14px",    // Secondary text, metadata
  base: "16px",  // Body text - WCAG recommended minimum
  md: "18px",    // Emphasized body, subheadings
  lg: "20px",    // Small headings
  xl: "22px",    // Medium headings
  "2xl": "24px", // Large headings
  "3xl": "28px", // Extra large headings
  "4xl": "32px", // Display text
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
