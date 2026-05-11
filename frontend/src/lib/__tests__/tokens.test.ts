import { describe, expect, it } from 'vitest';
import {
  COLORS,
  STATE_COLORS,
  SPACING,
  FONT_FAMILY,
  FONT_SIZE,
  FONT_WEIGHT,
  LINE_HEIGHT,
  ELEVATION,
  RADIUS,
  TRANSITION,
  LAYOUT,
  Z_INDEX,
  BREAKPOINTS,
  type ColorKey,
  type StateColorKey,
  type SpacingKey,
  type FontSizeKey,
  type FontWeightKey,
  type RadiusKey,
  type ElevationKey,
} from '../tokens';

describe('design tokens', () => {
  it('keeps semantic color and state token contracts stable', () => {
    const colorKey: ColorKey = 'accentBlue';
    const stateColorKey: StateColorKey = 'green';

    expect(COLORS[colorKey]).toMatch(/^oklch\(/);
    expect(STATE_COLORS[stateColorKey]).toMatchObject({ color: COLORS.accentGreen });
  });

  it('exposes layout, typography, radius, and elevation scales for shared UI primitives', () => {
    const spacingKey: SpacingKey = 4;
    const fontSizeKey: FontSizeKey = 'base';
    const fontWeightKey: FontWeightKey = 'semibold';
    const radiusKey: RadiusKey = 'xl';
    const elevationKey: ElevationKey = 'glow';

    expect(SPACING[spacingKey]).toBe('16px');
    expect(FONT_FAMILY.display).toBe('var(--font-display)');
    expect(FONT_SIZE[fontSizeKey]).toBe('16px');
    expect(FONT_WEIGHT[fontWeightKey]).toBe('600');
    expect(LINE_HEIGHT.normal).toBe('1.5');
    expect(RADIUS[radiusKey]).toBe('12px');
    expect(ELEVATION[elevationKey].blue).toContain('rgba');
    expect(TRANSITION.base).toBe('200ms ease');
    expect(LAYOUT.sidebarWidth).toBe('220px');
    expect(Z_INDEX.modal).toBeGreaterThan(Z_INDEX.overlay);
    expect(BREAKPOINTS.lg).toBe('1024px');
  });
});
