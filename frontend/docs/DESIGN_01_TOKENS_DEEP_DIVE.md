# Design System — Design Tokens Deep Dive

> Colors, typography, spacing, elevation, and the foundation of the design system

---

## Document Overview

**Series:** Design System | **Document:** 1 of 4 | **Focus:** Design Tokens

**Related Documents:**
- [02: Components Deep Dive](./DESIGN_02_COMPONENTS_DEEP_DIVE.md) — UI components
- [03: Patterns Deep Dive](./DESIGN_03_PATTERNS_DEEP_DIVE.md) — UX patterns
- [04: Accessibility Deep Dive](./DESIGN_04_ACCESSIBILITY_DEEP_DIVE.md) — WCAG compliance

---

## Table of Contents

1. [Token Architecture](#1-token-architecture)
2. [Color System](#2-color-system)
3. [Typography](#3-typography)
4. [Spacing System](#4-spacing-system)
5. [Elevation & Shadows](#5-elevation--shadows)
6. [Border Radius](#6-border-radius)
7. [Animation & Transitions](#7-animation--transitions)
8. [Breakpoints](#8-breakpoints)

---

## 1. Token Architecture

### 1.1 Token Hierarchy

```
┌────────────────────────────────────────────────────────────────────────────┐
│                         DESIGN TOKEN HIERARCHY                            │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  GLOBAL TOKENS (Primitive values)                                         │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │  color.blue.500: #3B82F6                                            │ │
│  │  spacing.4: 16px                                                    │ │
│  │  font.size.md: 14px                                                 │ │
│  │  radius.md: 6px                                                     │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
│                                 │                                         │
│                                 ▼                                         │
│  SEMANTIC TOKENS (Purpose-named aliases)                               │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │  color.primary: color.blue.500                                      │ │
│  │  color.text: color.neutral.900                                     │ │
│  │  color.bg: color.neutral.50                                        │ │
│  │  color.border: color.neutral.200                                   │ │
│  │  color.success: color.green.500                                    │ │
│  │  color.warning: color.amber.500                                    │ │
│  │  color.error: color.red.500                                        │ │
│  │  spacing.gap: spacing.4                                            │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
│                                 │                                         │
│                                 ▼                                         │
│  COMPONENT TOKENS (Component-specific)                                 │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │  button.primary.bg: color.primary                                  │ │
│  │  button.primary.text: color.white                                  │ │
│  │  button.primary.hover.bg: color.blue.600                            │ │
│  │  input.border: color.border                                        │ │
│  │  input.focus.border: color.primary                                  │ │
│  │  card.bg: color.white                                              │ │
│  │  card.shadow: elevation.2                                          │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Token Implementation (Stitches)

```typescript
// stitches.config.ts
import { createStitches } from '@stitches/react';

export const { styled, css, globalCss, theme, getCssText } = createStitches({
  theme: {
    colors: {
      // Primary colors
      primary: {
        50: '#EFF6FF',
        100: '#DBEAFE',
        200: '#BFDBFE',
        300: '#93C5FD',
        400: '#60A5FA',
        500: '#3B82F6',
        600: '#2563EB',
        700: '#1D4ED8',
        800: '#1E40AF',
        900: '#1E3A8A',
      },

      // Neutral colors
      neutral: {
        50: '#F9FAFB',
        100: '#F3F4F6',
        200: '#E5E7EB',
        300: '#D1D5DB',
        400: '#9CA3AF',
        500: '#6B7280',
        600: '#4B5563',
        700: '#374151',
        800: '#1F2937',
        900: '#111827',
        950: '#0B0F19',
      },

      // Semantic colors
      success: {
        50: '#F0FDF4',
        500: '#22C55E',
        600: '#16A34A',
      },

      warning: {
        50: '#FFFBEB',
        500: '#F59E0B',
        600: '#D97706',
      },

      error: {
        50: '#FEF2F2',
        500: '#EF4444',
        600: '#DC2626',
      },

      info: {
        50: '#EFF6FF',
        500: '#3B82F6',
        600: '#2563EB',
      },
    },

    // Spacing scale (8px base unit)
    space: {
      '0': '0',
      '0.5': '2px',
      '1': '4px',
      '1.5': '6px',
      '2': '8px',
      '2.5': '10px',
      '3': '12px',
      '3.5': '14px',
      '4': '16px',
      '5': '20px',
      '6': '24px',
      '7': '28px',
      '8': '32px',
      '9': '36px',
      '10': '40px',
      '11': '44px',
      '12': '48px',
      '14': '56px',
      '16': '64px',
      '20': '80px',
      '24': '96px',
      '32': '128px',
      '40': '160px',
      '48': '192px',
      '56': '224px',
      '64': '256px',
    },

    // Typography
    fonts: {
      sans: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      mono: '"JetBrains Mono", "Fira Code", monospace',
    },

    fontSizes: {
      'xs': '12px',
      'sm': '14px',
      'base': '16px',
      'lg': '18px',
      'xl': '20px',
      '2xl': '24px',
      '3xl': '30px',
      '4xl': '36px',
      '5xl': '48px',
      '6xl': '60px',
    },

    fontWeights: {
      'normal': '400',
      'medium': '500',
      'semibold': '600',
      'bold': '700',
    },

    lineHeights: {
      'none': '1',
      'tight': '1.25',
      'snug': '1.375',
      'normal': '1.5',
      'relaxed': '1.625',
      'loose': '2',
    },

    letterSpacings: {
      'tighter': '-0.05em',
      'tight': '-0.025em',
      'normal': '0',
      'wide': '0.025em',
      'wider': '0.05em',
      'widest': '0.1em',
    },

    // Border radius
    radii: {
      'none': '0',
      'sm': '2px',
      'DEFAULT': '4px',
      'md': '6px',
      'lg': '8px',
      'xl': '12px',
      '2xl': '16px',
      '3xl': '24px',
      'full': '9999px',
    },

    // Shadows
    shadows: {
      'sm': '0 1px 2px 0 rgb(0 0 0 / 0.05)',
      'DEFAULT': '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)',
      'md': '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
      'lg': '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',
      'xl': '0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)',
      '2xl': '0 25px 50px -12px rgb(0 0 0 / 0.25)',
      'inner': 'inset 0 2px 4px 0 rgb(0 0 0 / 0.05)',
    },

    // Z-index scale
    zIndex: {
      'hide': -1,
      'base': 0,
      'dropdown': 1000,
      'sticky': 1100,
      'fixed': 1200,
      'modalBackdrop': 1300,
      'modal': 1400,
      'popover': 1500,
      'tooltip': 1600,
      'notification': 1700,
    },

    // Breakpoints
    breakpoints: {
      'sm': '640px',
      'md': '768px',
      'lg': '1024px',
      'xl': '1280px',
      '2xl': '1536px',
    },
  },

  media: {
    'sm': '(min-width: 640px)',
    'md': '(min-width: 768px)',
    'lg': '(min-width: 1024px)',
    'xl': '(min-width: 1280px)',
    '2xl': '(min-width: 1536px)',
  },
});

// Type exports for TypeScript
export type Tokens = typeof theme;
export type Colors = Tokens['colors'];
export type Space = Tokens['space'];
export type FontSizes = Tokens['fontSizes'];
```

---

## 2. Color System

### 2.1 Color Palette

```
┌────────────────────────────────────────────────────────────────────────────┐
│                              COLOR PALETTE                                │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  PRIMARY (Blue)              NEUTRAL (Gray)                                │
│  ┌─────────────────────────┐  ┌─────────────────────────────────────────┐│
│  │ 50  #EFF6FF  ███░░░░░  │  │ 50  #F9FAFB  ████████████████████████  ││
│  │ 100 #DBEAFE  ██████░░  │  │ 100 #F3F4F6  ████████████████████████  ││
│  │ 200 #BFDBFE  ████████  │  │ 200 #E5E7EB  ████████████████████████  ││
│  │ 300 #93C5FD  ████████  │  │ 300 #D1D5DB  ████████████████████████  ││
│  │ 400 #60A5FA  ████████  │  │ 400 #9CA3AF  ████████████████████████  ││
│  │ 500 #3B82F6  ████████  │  │ 500 #6B7280  ████████████████████████  ││
│  │ 600 #2563EB  ████████  │  │ 600 #4B5563  ████████████████████████  ││
│  │ 700 #1D4ED8  ████████  │  │ 700 #374151  ████████████████████████  ││
│  │ 800 #1E40AF  ████████  │  │ 800 #1F2937  ████████████████████████  ││
│  │ 900 #1E3A8A  ████████  │  │ 900 #111827  ████████████████████████  ││
│  └─────────────────────────┘  │ 950 #0B0F19  ████████████████████████  ││
│                              └─────────────────────────────────────────┘│
│                                                                            │
│  SEMANTIC COLORS                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │ SUCCESS (Green)   WARNING (Amber)   ERROR (Red)    INFO (Blue)     │  │
│  │ ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ ┌───────────┐  │  │
│  │ │50  #F0FDF4   │  │50  #FFFBEB   │  │50  #FEF2F2   │ │50 #EFF6FF │  │  │
│  │ │500 #22C55E   │  │500 #F59E0B   │  │500 #EF4444   │ │500 #3B82F6│  │  │
│  │ │600 #16A34A   │  │600 #D97706   │  │600 #DC2626   │ │600 #2563EB│  │  │
│  │ └──────────────┘  └──────────────┘  └──────────────┘ └───────────┘  │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Semantic Color Mapping

```typescript
// Semantic color tokens
const semanticColors = {
  // Background colors
  bg: {
    DEFAULT: '$white',
    primary: '$primary50',
    secondary: '$neutral100',
    muted: '$neutral50',
    accent: '$primary500',
  },

  // Text colors
  text: {
    DEFAULT: '$neutral900',
    primary: '$neutral900',
    secondary: '$neutral500',
    muted: '$neutral400',
    inverse: '$white',
    accent: '$primary600',
  },

  // Border colors
  border: {
    DEFAULT: '$neutral200',
    muted: '$neutral100',
    focus: '$primary500',
    error: '$error500',
    success: '$success500',
    warning: '$warning500',
  },

  // Interactive colors
  interactive: {
    DEFAULT: '$primary500',
    hover: '$primary600',
    active: '$primary700',
    disabled: '$neutral300',
  },

  // Status colors
  status: {
    success: '$success500',
    warning: '$warning500',
    error: '$error500',
    info: '$info500',
  },

  // Overlay colors
  overlay: {
    DEFAULT: 'rgba(0, 0, 0, 0.5)',
    light: 'rgba(0, 0, 0, 0.25)',
    dark: 'rgba(0, 0, 0, 0.75)',
  },
};
```

### 2.3 Dark Mode Colors

```typescript
// Dark mode color overrides
export const darkTheme = {
  colors: {
    // Invert neutrals for dark mode
    neutral: {
      50: '#0B0F19',
      100: '#111827',
      200: '#1F2937',
      300: '#374151',
      400: '#4B5563',
      500: '#6B7280',
      600: '#9CA3AF',
      700: '#D1D5DB',
      800: '#E5E7EB',
      900: '#F3F4F6',
      950: '#F9FAFB',
    },

    // Adjust primary for dark backgrounds
    primary: {
      50: '#1E3A8A',
      400: '#3B82F6',
      500: '#60A5FA',
      600: '#93C5FD',
    },
  },

  // Semantic overrides for dark mode
  bg: {
    DEFAULT: '$neutral900',
    elevated: '$neutral800',
    muted: '$neutral800',
  },

  text: {
    DEFAULT: '$neutral100',
    muted: '$neutral400',
  },

  border: {
    DEFAULT: '$neutral700',
    muted: '$neutral800',
  },
};
```

### 2.4 Color Usage Guidelines

```typescript
// Color usage rules
const colorGuidelines = {
  // Primary: Actions, links, brand elements
  primary: {
    usage: ['Buttons', 'Links', 'Active states', 'Brand accents'],
    contrast: ['White text on primary bg', 'Primary text on white bg'],
    avoid: ['Large backgrounds', 'Body text'],
  },

  // Neutral: Structure, text, borders
  neutral: {
    usage: ['Text', 'Borders', 'Backgrounds', 'Dividers'],
    contrast: {
      light: '900/800 for text, 50/100 for backgrounds',
      dark: '100/200 for text, 900/800 for backgrounds',
    },
  },

  // Semantic: Status and feedback
  success: { usage: ['Success states', 'Positive trends', 'Confirmation'] },
  warning: { usage: ['Warnings', 'Cautionary states', 'Attention needed'] },
  error: { usage: ['Errors', 'Destructive actions', 'Negative trends'] },
  info: { usage: ['Information', 'Helpful hints', 'Neutral feedback'] },
};
```

---

## 3. Typography

### 3.1 Type Scale

```
┌────────────────────────────────────────────────────────────────────────────┐
│                         TYPOGRAPHY SCALE                                  │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  DISPLAY (Hero headings)                                                   │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │ 6xl 60px  Hero Title                                                 │ │
│  │ 5xl 48px  Large Hero                                                 │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│  HEADINGS (Section hierarchy)                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │ 4xl 36px  H1 Page title                                              │ │
│  │ 3xl 30px  H2 Section title                                           │ │
│  │ 2xl 24px  H3 Subsection title                                        │ │
│  │ xl  20px  H4 Component title                                          │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│  BODY (Text content)                                                       │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │ lg  18px  Large body text                                            │ │
│  │ base 16px  Default body text                                        │ │
│  │ sm  14px  Secondary text, captions                                   │ │
│  │ xs  12px  Fine print, labels                                        │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│  LINE HEIGHT                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │ none  1.00  Headings with no descenders                              │ │
│  │ tight 1.25  Large headings                                           │ │
│  │ snug  1.375 Headings with some descenders                            │ │
│  │ normal 1.5  Body text (default)                                      │ │
│  │ relaxed 1.625 Paragraphs with longer lines                            │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Typography Tokens

```typescript
// Typography component
export const Text = styled('span', {
  variants: {
    size: {
      xs: {
        fontSize: '$xs',
        lineHeight: '$normal',
      },
      sm: {
        fontSize: '$sm',
        lineHeight: '$normal',
      },
      base: {
        fontSize: '$base',
        lineHeight: '$normal',
      },
      lg: {
        fontSize: '$lg',
        lineHeight: '$normal',
      },
      xl: {
        fontSize: '$xl',
        lineHeight: '$snug',
      },
      '2xl': {
        fontSize: '$2xl',
        lineHeight: '$snug',
      },
      '3xl': {
        fontSize: '$3xl',
        lineHeight: '$tight',
      },
      '4xl': {
        fontSize: '$4xl',
        lineHeight: '$tight',
      },
      '5xl': {
        fontSize: '$5xl',
        lineHeight: '$none',
      },
      '6xl': {
        fontSize: '$6xl',
        lineHeight: '$none',
      },
    },
    weight: {
      normal: { fontWeight: '$normal' },
      medium: { fontWeight: '$medium' },
      semibold: { fontWeight: '$semibold' },
      bold: { fontWeight: '$bold' },
    },
    color: {
      DEFAULT: { color: '$text' },
      primary: { color: '$primary' },
      secondary: { color: '$textSecondary' },
      muted: { color: '$textMuted' },
      accent: { color: '$textAccent' },
      inverse: { color: '$textInverse' },
      success: { color: '$success500' },
      warning: { color: '$warning500' },
      error: { color: '$error500' },
    },
  },

  defaultVariants: {
    size: 'base',
    weight: 'normal',
    color: 'DEFAULT',
  },
});
```

### 3.3 Font Families

```typescript
// Font family configuration
export const fontFamilies = {
  sans: [
    // Inter for UI
    'Inter',
    // System fonts fallback
    '-apple-system',
    'BlinkMacSystemFont',
    '"Segoe UI"',
    'Roboto',
    'sans-serif',
  ].join(', '),

  mono: [
    // JetBrains Mono for code
    '"JetBrains Mono"',
    '"Fira Code"',
    'Consolas',
    'Monaco',
    'monospace',
  ].join(', '),

  display: [
    // Optional: Display font for hero headings
    'Cal Sans',
    'Inter',
    'sans-serif',
  ].join(', '),
};

// Global font import
export const globalFontFace = css`
  @font-face {
    font-family: 'Inter';
    font-style: normal;
    font-weight: 400;
    font-display: swap;
    src: url('/fonts/inter-regular.woff2') format('woff2');
  }

  @font-face {
    font-family: 'Inter';
    font-style: normal;
    font-weight: 500;
    font-display: swap;
    src: url('/fonts/inter-medium.woff2') format('woff2');
  }

  @font-face {
    font-family: 'Inter';
    font-style: normal;
    font-weight: 600;
    font-display: swap;
    src: url('/fonts/inter-semibold.woff2') format('woff2');
  }

  @font-face {
    font-family: 'JetBrains Mono';
    font-style: normal;
    font-weight: 400;
    font-display: swap;
    src: url('/fonts/jetbrains-mono-regular.woff2') format('woff2');
  }
`;
```

---

## 4. Spacing System

### 4.1 Spacing Scale

```
┌────────────────────────────────────────────────────────────────────────────┐
│                         SPACING SCALE (8px BASE)                          │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  Token    Value    Usage                                                  │
│  ──────   ─────    ─────────────────────────────────────────────────────  │
│  0        0px      None                                                   │
│  0.5      2px      Hairline, tight spacing                                │
│  1        4px      Extra tight, icon padding                              │
│  1.5      6px      Compact                                               │
│  2        8px      Tight spacing, small gaps                             │
│  2.5      10px     Small padding                                         │
│  3        12px     Compact padding                                       │
│  3.5      14px     -                                                      │
│  4        16px     DEFAULT spacing, comfortable padding                  │
│  5        20px     Medium spacing                                        │
│  6        24px     Large padding, section spacing                       │
│  7        28px     -                                                      │
│  8        32px     Extra large padding                                   │
│  10       40px     Section gaps                                          │
│  12       48px     Large sections                                         │
│  16       64px     Component spacing                                     │
│  20       80px     Page sections                                         │
│  24       96px     Major sections                                        │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Spacing Usage Patterns

```typescript
// Common spacing patterns
const spacingPatterns = {
  // Component internal padding
  padding: {
    sm: '$3',      // 12px - Compact components
    DEFAULT: '$4', // 16px - Default components
    md: '$5',      // 20px - Medium components
    lg: '$6',      // 24px - Large components
    xl: '$8',      // 32px - Extra large
  },

  // Gap between elements
  gap: {
    xs: '$1',      // 4px - Tight lists
    sm: '$2',      // 8px - Compact rows
    DEFAULT: '$4', // 16px - Default gap
    md: '$5',      // 20px - Medium gap
    lg: '$6',      // 24px - Large gap
    xl: '$8',      // 32px - Section gap
  },

  // Margin for layout separation
  margin: {
    sm: '$4',      // 16px - Small separation
    DEFAULT: '$6', // 24px - Default separation
    md: '$8',      // 32px - Medium separation
    lg: '$12',     // 48px - Large separation
    xl: '$16',     // 64px - Section separation
  },
};
```

---

## 5. Elevation & Shadows

### 5.1 Elevation Scale

```
┌────────────────────────────────────────────────────────────────────────────┐
│                         ELEVATION & SHADOWS                              │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  Level 0: Flat (No shadow)                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │  • Ground level, attached to surface                                 │  │
│  │  • Inset fields, disabled states                                     │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│  Level 1: Raised (Subtle)                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │ ╔═══════════════════════════════════════╗                             │  │
│  │ ║ ═════════════════════════════════════ ║  shadow: sm                 │  │
│  │ ╚═══════════════════════════════════════╝                             │  │
│  │  • Hover states, buttons, cards                                     │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│  Level 2: Low (Default)                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │ ╔═══════════════════════════════════════╗                             │  │
│  │ ║ ═════════════════════════════════════ ║  shadow: DEFAULT            │  │
│  │ ╚═══════════════════════════════════════╝                             │  │
│  │  • Dropdowns, popovers, elevated cards                             │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│  Level 3: Medium                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │ ╔═══════════════════════════════════════╗                             │  │
│  │ ║ ═════════════════════════════════════ ║  shadow: md                 │  │
│  │ ╚═══════════════════════════════════════╝                             │  │
│  │  • Modals, sheets, drawers                                         │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│  Level 4: High                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │ ╔═══════════════════════════════════════╗                             │  │
│  │ ║ ═════════════════════════════════════ ║  shadow: lg                 │  │
│  │ ╚═══════════════════════════════════════╝                             │  │
│  │  • Dialogs, tooltips, notifications                               │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│  Level 5: Highest                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │ ╔═══════════════════════════════════════╗                             │  │
│  │ ║ ═════════════════════════════════════ ║  shadow: xl / 2xl            │  │
│  │ ╚═══════════════════════════════════════╝                             │  │
│  │  • Modals with backdrop, persistent overlays                       │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Shadow Tokens

```typescript
// Shadow elevation tokens
const shadows = {
  sm: '0 1px 2px 0 rgb(0 0 0 / 0.05)',

  DEFAULT: '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)',

  md: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',

  lg: '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',

  xl: '0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)',

  '2xl': '0 25px 50px -12px rgb(0 0 0 / 0.25)',

  inner: 'inset 0 2px 4px 0 rgb(0 0 0 / 0.05)',
};

// Colored shadows for accent elements
const coloredShadows = {
  primary: {
    sm: '0 1px 2px 0 rgb(59 130 246 / 0.2)',
    DEFAULT: '0 4px 6px -1px rgb(59 130 246 / 0.3), 0 2px 4px -2px rgb(59 130 246 / 0.2)',
    md: '0 10px 15px -3px rgb(59 130 246 / 0.3), 0 4px 6px -4px rgb(59 130 246 / 0.2)',
  },
};
```

---

## 6. Border Radius

### 6.1 Radius Scale

```
┌────────────────────────────────────────────────────────────────────────────┐
│                         BORDER RADIUS SCALE                               │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  none: 0px               sm: 2px              DEFAULT: 4px                  │
│  ┌──────────┐            ┌──────────┐           ┌──────────┐               │
│  │          │            │ ┌──────┐ │           │ ┌────┐   │               │
│  │          │            │ │      │ │           │ │    │   │               │
│  │          │            │ └──────┘ │           │ └────┘   │               │
│  └──────────┘            └──────────┘           └──────────┘               │
│                                                                            │
│  md: 6px                 lg: 8px              xl: 12px                      │
│  ┌──────────┐            ┌──────────┐           ┌──────────┐               │
│  │ ╔──────┐ │            │ ╔───────╗ │           │ ╔───────╗ │               │
│  │ ╚──────┘ │            │ ╚───────╝ │           │ ╚═══════╝ │               │
│  └──────────┘            └──────────┘           └──────────┘               │
│                                                                            │
│  2xl: 16px               3xl: 24px            full: Pill                     │
│  ┌──────────┐            ┌──────────┐           ┌──────────┐               │
│  │ ╔═══════╗ │            │ ╔═══════╗ │           │ ╱─────────╲│               │
│  │ ╚═══════╝ │            │ ╚═══════╝ │           │ ╲─────────╱│               │
│  └──────────┘            └──────────┘           └──────────┘               │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

### 6.2 Radius Usage Guidelines

```typescript
// Border radius usage
const radiusUsage = {
  none: {
    usage: ['Images', 'Dividers', 'Layout edges'],
  },
  sm: {
    usage: ['Input fields', 'Small buttons', 'Tags'],
  },
  DEFAULT: {
    usage: ['Default buttons', 'Cards', 'Dropdown items'],
  },
  md: {
    usage: ['Pills', 'Chips', 'Toggle switches'],
  },
  lg: {
    usage: ['Large buttons', 'Modal containers'],
  },
  xl: {
    usage: ['Hero cards', 'Callout boxes'],
  },
  '2xl': {
    usage: ['Hero sections', 'Featured content'],
  },
  full: {
    usage: ['Avatars', 'Badges', 'Pill buttons'],
  },
};
```

---

## 7. Animation & Transitions

### 7.1 Animation Tokens

```typescript
// Animation duration tokens
export const durations = {
  instant: '0ms',
  fast: '150ms',
  DEFAULT: '200ms',
  normal: '300ms',
  slow: '500ms',
  slower: '700ms',
};

// Easing functions
export const easings = {
  linear: 'linear',
  DEFAULT: 'cubic-bezier(0.4, 0, 0.2, 1)', // ease-in-out
  in: 'cubic-bezier(0.4, 0, 1, 1)',       // ease-in
  out: 'cubic-bezier(0, 0, 0.2, 1)',       // ease-out
  bounce: 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',
};

// Animation presets
export const animations = {
  // Fade
  fadeIn: css({
    animation: 'fadeIn 200ms ease-out',
  }),
  fadeOut: css({
    animation: 'fadeOut 150ms ease-in',
  }),

  // Slide
  slideInUp: css({
    animation: 'slideInUp 200ms ease-out',
  }),
  slideInDown: css({
    animation: 'slideInDown 200ms ease-out',
  }),

  // Scale
  scaleIn: css({
    animation: 'scaleIn 200ms ease-out',
  }),

  // Spin
  spin: css({
    animation: 'spin 1s linear infinite',
  }),

  // Pulse
  pulse: css({
    animation: 'pulse 2s ease-in-out infinite',
  }),
};

// Keyframe definitions
export const keyframes = {
  fadeIn: {
    '0%': { opacity: '0' },
    '100%': { opacity: '1' },
  },
  fadeOut: {
    '0%': { opacity: '1' },
    '100%': { opacity: '0' },
  },
  slideInUp: {
    '0%': { transform: 'translateY(10px)', opacity: '0' },
    '100%': { transform: 'translateY(0)', opacity: '1' },
  },
  slideInDown: {
    '0%': { transform: 'translateY(-10px)', opacity: '0' },
    '100%': { transform: 'translateY(0)', opacity: '1' },
  },
  scaleIn: {
    '0%': { transform: 'scale(0.95)', opacity: '0' },
    '100%': { transform: 'scale(1)', opacity: '1' },
  },
  spin: {
    '0%': { transform: 'rotate(0deg)' },
    '100%': { transform: 'rotate(360deg)' },
  },
  pulse: {
    '0%, 100%': { opacity: '1' },
    '50%': { opacity: '0.5' },
  },
};
```

### 7.2 Motion Principles

```
┌────────────────────────────────────────────────────────────────────────────┐
│                         MOTION PRINCIPLES                                 │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  1. PURPOSEFUL                                                             │
│     Animations should guide attention and provide feedback                │
│     Avoid decorative animations that don't add value                      │
│                                                                            │
│  2. SUBTLE                                                                 │
│     Prefer smaller, faster transitions                                    │
│     Default: 200ms ease-out                                               │
│                                                                            │
│  3. CONSISTENT                                                              │
│     Similar interactions use similar animations                           │
│     Use shared animation tokens                                          │
│                                                                            │
│  4. RESPECTFUL                                                             │
│     Honor prefers-reduced-motion                                         │
│     Don't animate automatically without user intent                       │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Breakpoints

### 8.1 Responsive Scale

```typescript
// Breakpoint tokens
export const breakpoints = {
  sm: '640px',   // Mobile landscape
  md: '768px',   // Tablet portrait
  lg: '1024px',  // Tablet landscape / Small desktop
  xl: '1280px',  // Desktop
  '2xl': '1536px', // Large desktop
};

// Media query helper
export const media = {
  sm: '(min-width: 640px)',
  md: '(min-width: 768px)',
  lg: '(min-width: 1024px)',
  xl: '(min-width: 1280px)',
  '2xl': '(min-width: 1536px)',

  // Max-width for mobile-first
  maxSm: '(max-width: 639px)',
  maxMd: '(max-width: 767px)',
  maxLg: '(max-width: 1023px)',
  maxXl: '(max-width: 1279px)',

  // Orientation
  portrait: '(orientation: portrait)',
  landscape: '(orientation: landscape)',

  // Dark mode
  dark: '(prefers-color-scheme: dark)',
  light: '(prefers-color-scheme: light)',

  // Reduced motion
  reducedMotion: '(prefers-reduced-motion: reduce)',
};

// Responsive container max-widths
export const container = {
  sm: '640px',
  md: '768px',
  lg: '1024px',
  xl: '1280px',
  '2xl': '1536px',
};
```

### 8.2 Responsive Typography

```typescript
// Fluid typography scale
export const fluidText = {
  // Scale text based on viewport width
  clamp: {
    xs: 'clamp(12px, 2vw, 14px)',
    sm: 'clamp(14px, 2vw, 16px)',
    base: 'clamp(16px, 2vw, 18px)',
    lg: 'clamp(18px, 2vw, 20px)',
    xl: 'clamp(20px, 3vw, 24px)',
    '2xl': 'clamp(24px, 4vw, 30px)',
    '3xl': 'clamp(30px, 5vw, 36px)',
  },
};

// Responsive component example
export const ResponsiveText = styled('h1', {
  // Mobile first
  fontSize: '$2xl',
  lineHeight: '$snug',

  // Tablet and up
  '@md': {
    fontSize: '$3xl',
  },

  // Desktop and up
  '@lg': {
    fontSize: '$4xl',
  },
});
```

---

## Summary

Design tokens provide the foundation for consistent UI:

| Token Category | Purpose |
|----------------|---------|
| **Colors** | Primary palette, semantic colors, dark mode |
| **Typography** | Font families, size scale, weights, line heights |
| **Spacing** | 8px-based scale for consistent gaps and padding |
| **Elevation** | Shadow levels for depth hierarchy |
| **Border Radius** | Rounded corners from sharp to pill |
| **Animation** | Duration, easing, and keyframe presets |
| **Breakpoints** | Responsive scale from mobile to desktop |

**Key Takeaways:**
- Use token hierarchy: Global → Semantic → Component
- Base spacing on 8px grid for consistency
- Support dark mode with token overrides
- Honor prefers-reduced-motion
- Use semantic names (primary, success) over literal (blue, green)
- Provide fluid typography for responsive text

---

**Related:** [02: Components Deep Dive](./DESIGN_02_COMPONENTS_DEEP_DIVE.md) → UI components built on tokens
