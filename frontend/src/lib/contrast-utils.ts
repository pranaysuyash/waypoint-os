/**
 * Color Contrast Utilities
 *
 * Functions for calculating and validating color contrast ratios for WCAG compliance.
 */

/**
 * Calculate relative luminance of a color
 * @param hex - Hex color string (with or without #)
 * @returns Relative luminance (0-1)
 */
export function luminance(hex: string): number {
  const hexColor = hex.replace("#", "");
  const r = parseInt(hexColor.substring(0, 2), 16) / 255;
  const g = parseInt(hexColor.substring(2, 4), 16) / 255;
  const b = parseInt(hexColor.substring(4, 6), 16) / 255;

  const toLinear = (c: number): number => {
    return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
  };

  const R = toLinear(r);
  const G = toLinear(g);
  const B = toLinear(b);

  return 0.2126 * R + 0.7152 * G + 0.0722 * B;
}

/**
 * Calculate contrast ratio between two colors
 * @param foreground - Foreground color (hex)
 * @param background - Background color (hex)
 * @returns Contrast ratio (1-21)
 */
export function contrastRatio(foreground: string, background: string): number {
  const fgLum = luminance(foreground);
  const bgLum = luminance(background);

  const lighter = Math.max(fgLum, bgLum);
  const darker = Math.min(fgLum, bgLum);

  return (lighter + 0.05) / (darker + 0.05);
}

/**
 * Check if contrast meets WCAG AA standard
 * @param ratio - Contrast ratio
 * @param isLargeText - Whether text is large (18px+ or 14px+ bold)
 * @returns Whether contrast passes AA
 */
export function passesAA(ratio: number, isLargeText = false): boolean {
  return isLargeText ? ratio >= 3.0 : ratio >= 4.5;
}

/**
 * Check if contrast meets WCAG AAA standard
 * @param ratio - Contrast ratio
 * @param isLargeText - Whether text is large (18px+ or 14px+ bold)
 * @returns Whether contrast passes AAA
 */
export function passesAAA(ratio: number, isLargeText = false): boolean {
  return isLargeText ? ratio >= 4.5 : ratio >= 7.0;
}

/**
 * WCAG Compliance Levels
 */
export const WCAG = {
  AA_NORMAL: 4.5,
  AA_LARGE: 3.0,
  AAA_NORMAL: 7.0,
  AAA_LARGE: 4.5,
} as const;

/**
 * Check contrast and return compliance info
 * @param foreground - Foreground color (hex)
 * @param background - Background color (hex)
 * @param isLargeText - Whether text is large
 */
export function checkContrast(
  foreground: string,
  background: string,
  isLargeText = false
): {
  ratio: number;
  passesAA: boolean;
  passesAAA: boolean;
} {
  const ratio = contrastRatio(foreground, background);
  return {
    ratio: Math.round(ratio * 100) / 100,
    passesAA: passesAA(ratio, isLargeText),
    passesAAA: passesAAA(ratio, isLargeText),
  };
}

/**
 * Find the lightest color that meets contrast requirement
 * @param baseColor - Starting color to lighten (hex)
 * @param backgroundColor - Background to ensure contrast against (hex)
 * @param targetRatio - Target contrast ratio (default 4.5 for AA)
 * @returns A color that meets the contrast requirement
 */
export function ensureContrast(
  baseColor: string,
  backgroundColor: string,
  targetRatio = 4.5
): string {
  const currentRatio = contrastRatio(baseColor, backgroundColor);
  if (currentRatio >= targetRatio) {
    return baseColor;
  }

  // Lighten the color by increasing RGB values
  const hex = baseColor.replace("#", "");
  let r = parseInt(hex.substring(0, 2), 16);
  let g = parseInt(hex.substring(2, 4), 16);
  let b = parseInt(hex.substring(4, 6), 16);

  // Gradually lighten until contrast is met
  for (let i = 0; i < 100; i++) {
    r = Math.min(255, r + 3);
    g = Math.min(255, g + 3);
    b = Math.min(255, b + 3);

    const newColor = `#${r.toString(16).padStart(2, "0")}${g
      .toString(16)
      .padStart(2, "0")}${b.toString(16).padStart(2, "0")}`;
    const newRatio = contrastRatio(newColor, backgroundColor);

    if (newRatio >= targetRatio) {
      return newColor;
    }
  }

  // Fallback to white
  return "#ffffff";
}

/**
 * Validate all design token colors against backgrounds
 */
export function validateTokenColors() {
  const results: { name: string; ratio: number; passesAA: boolean }[] = [];

  const backgrounds = {
    bgCanvas: "#080a0c",
    bgSurface: "#0f1115",
    bgElevated: "#161b22",
    bgHighlight: "#1c2128",
  };

  const textColors = {
    textPrimary: "#e6edf3",
    textSecondary: "#a8b3c1",
    textTertiary: "#9ba3b0",
    textMuted: "#8b949e",
  };

  for (const [bgName, bgValue] of Object.entries(backgrounds)) {
    for (const [textName, textValue] of Object.entries(textColors)) {
      const ratio = contrastRatio(textValue, bgValue);
      results.push({
        name: `${textName} on ${bgName}`,
        ratio,
        passesAA: ratio >= 4.5,
      });
    }
  }

  return results;
}
