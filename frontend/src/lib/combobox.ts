/**
 * Smart combobox utilities for field entry with predefined options
 * that allows custom additions with fuzzy matching and normalization.
 */

// ============================================================================
// TYPES
// ============================================================================

export interface ComboboxOption {
  value: string;
  label: string;
  isCustom?: boolean;
}

export interface FuzzyMatch {
  option: ComboboxOption;
  score: number;
}

// ============================================================================
// TITLE CASE NORMALIZATION
// ============================================================================

/**
 * Convert string to Title Case (First Letter Of Each Word Capitalized).
 * Handles special cases like "and", "or", "of", "in" for better readability.
 */
export function toTitleCase(input: string): string {
  if (!input || typeof input !== 'string') return '';

  const lower = input.toLowerCase().trim();

  // Handle empty after trim
  if (!lower) return '';

  // Special words that should remain lowercase (unless first word)
  const lowerCaseWords = new Set([
    'a', 'an', 'the', 'and', 'or', 'but', 'of', 'in', 'on', 'at', 'to',
    'for', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were'
  ]);

  return lower
    .split(/\s+/)
    .map((word, index) => {
      // Always capitalize first word
      if (index === 0) {
        return word.charAt(0).toUpperCase() + word.slice(1);
      }
      // Keep special words lowercase
      if (lowerCaseWords.has(word)) {
        return word;
      }
      // Capitalize first letter of other words
      return word.charAt(0).toUpperCase() + word.slice(1);
    })
    .join(' ');
}

/**
 * Normalize a value for comparison and storage.
 * Applies title case and trims whitespace.
 */
export function normalizeValue(input: string): string {
  return toTitleCase(input);
}

/**
 * Check if two values are equivalent after normalization.
 */
export function valuesMatch(a: string, b: string): boolean {
  return normalizeValue(a) === normalizeValue(b);
}

// ============================================================================
// FUZZY MATCHING
// ============================================================================

/**
 * Calculate Levenshtein distance between two strings.
 * Returns the minimum number of single-character edits needed to change one string into the other.
 */
function levenshteinDistance(a: string, b: string): number {
  const aLower = a.toLowerCase();
  const bLower = b.toLowerCase();

  const matrix: number[][] = [];

  // Initialize matrix
  for (let i = 0; i <= bLower.length; i++) {
    matrix[i] = [i];
  }
  for (let j = 0; j <= aLower.length; j++) {
    matrix[0][j] = j;
  }

  // Fill matrix
  for (let i = 1; i <= bLower.length; i++) {
    for (let j = 1; j <= aLower.length; j++) {
      if (bLower.charAt(i - 1) === aLower.charAt(j - 1)) {
        matrix[i][j] = matrix[i - 1][j - 1];
      } else {
        matrix[i][j] = Math.min(
          matrix[i - 1][j - 1] + 1, // substitution
          matrix[i][j - 1] + 1,     // insertion
          matrix[i - 1][j] + 1      // deletion
        );
      }
    }
  }

  return matrix[bLower.length][aLower.length];
}

/**
 * Calculate a similarity score between two strings (0-1, where 1 is exact match).
 * Uses normalized Levenshtein distance.
 */
export function calculateSimilarity(a: string, b: string): number {
  const aNorm = normalizeValue(a);
  const bNorm = normalizeValue(b);

  if (aNorm === bNorm) return 1;

  const maxLen = Math.max(aNorm.length, bNorm.length);
  if (maxLen === 0) return 1;

  const distance = levenshteinDistance(aNorm, bNorm);
  return Math.max(0, 1 - distance / maxLen);
}

/**
 * Find fuzzy matches from options for a given input.
 * Returns options sorted by similarity score.
 */
export function findFuzzyMatches(
  input: string,
  options: ComboboxOption[],
  threshold: number = 0.6
): FuzzyMatch[] {
  if (!input || input.trim().length === 0) return [];

  const inputNorm = normalizeValue(input);

  const matches: FuzzyMatch[] = [];
  for (const option of options) {
    const score = calculateSimilarity(inputNorm, option.value);
    if (score >= threshold) {
      matches.push({ option, score });
    }
  }
  matches.sort((a, b) => b.score - a.score);

  return matches;
}

/**
 * Check if input is a near-duplicate of an existing option.
 * Returns the matching option if found, null otherwise.
 */
export function findNearDuplicate(
  input: string,
  options: ComboboxOption[],
  threshold: number = 0.85
): ComboboxOption | null {
  const matches = findFuzzyMatches(input, options, threshold);
  return matches.length > 0 ? matches[0].option : null;
}

// ============================================================================
// COMBOBOX MANAGEMENT
// ============================================================================

/**
 * Add a custom option to the list if it doesn't already exist.
 * Returns the updated list and whether the option was newly added.
 */
export function addCustomOption(
  customValue: string,
  existingOptions: ComboboxOption[]
): { options: ComboboxOption[]; wasAdded: boolean; normalizedValue: string } {
  const normalized = normalizeValue(customValue);

  if (!normalized) {
    return { options: existingOptions, wasAdded: false, normalizedValue: '' };
  }

  // Check if option already exists (after normalization)
  const existing = existingOptions.find(opt => valuesMatch(opt.value, normalized));
  if (existing) {
    return { options: existingOptions, wasAdded: false, normalizedValue: existing.value };
  }

  // Add new custom option
  const newOption: ComboboxOption = {
    value: normalized,
    label: normalized,
    isCustom: true,
  };

  // Sort: predefined options first, then custom alphabetically
  const predefined = existingOptions.filter(opt => !opt.isCustom);
  const custom = [...existingOptions.filter(opt => opt.isCustom), newOption]
    .sort((a, b) => a.value.localeCompare(b.value));

  return {
    options: [...predefined, ...custom],
    wasAdded: true,
    normalizedValue: normalized,
  };
}

/**
 * Get display options with sections (predefined vs custom).
 */
export function getGroupedOptions(options: ComboboxOption[]): {
  predefined: ComboboxOption[];
  custom: ComboboxOption[];
} {
  return {
    predefined: options.filter(opt => !opt.isCustom),
    custom: options.filter(opt => opt.isCustom).sort((a, b) => a.value.localeCompare(b.value)),
  };
}

// ============================================================================
// PREDEFINED OPTIONS FOR TRAVEL FIELDS
// ============================================================================

/**
 * Predefined trip types with common categories.
 */
export const TRIP_TYPE_OPTIONS: ComboboxOption[] = [
  { value: 'Honeymoon', label: 'Honeymoon' },
  { value: 'Family Vacation', label: 'Family Vacation' },
  { value: 'Adventure', label: 'Adventure / Activity' },
  { value: 'Beach', label: 'Beach / Relaxation' },
  { value: 'Pilgrimage', label: 'Pilgrimage' },
  { value: 'Business', label: 'Business / Corporate' },
  { value: 'Weekend Getaway', label: 'Weekend Getaway' },
  { value: 'Group Tour', label: 'Group Tour' },
  { value: 'Luxury', label: 'Luxury Travel' },
  { value: 'Backpacking', label: 'Backpacking / Budget' },
  { value: 'Cultural', label: 'Cultural / Historical' },
  { value: 'Wildlife', label: 'Wildlife / Safari' },
  { value: 'Cruise', label: 'Cruise' },
  { value: 'Wellness', label: 'Wellness / Retreat' },
  { value: 'Solo Trip', label: 'Solo Trip' },
];

/**
 * Common destinations (can be extended).
 */
export const DESTINATION_OPTIONS: ComboboxOption[] = [
  // International
  { value: 'Thailand', label: '🇹🇭 Thailand' },
  { value: 'Dubai', label: '🇦🇪 Dubai' },
  { value: 'Singapore', label: '🇸🇬 Singapore' },
  { value: 'Bali', label: '🇮🇩 Bali' },
  { value: 'Maldives', label: '🇲🇻 Maldives' },
  { value: 'Europe', label: '🇪🇺 Europe' },
  { value: 'Switzerland', label: '🇨🇭 Switzerland' },
  { value: 'Paris', label: '🇫🇷 Paris' },
  { value: 'Japan', label: '🇯🇵 Japan' },
  { value: 'Vietnam', label: '🇻🇳 Vietnam' },
  { value: 'Sri Lanka', label: '🇱🇰 Sri Lanka' },
  { value: 'Nepal', label: '🇳🇵 Nepal' },
  { value: 'Malaysia', label: '🇲🇾 Malaysia' },
  // Domestic (India)
  { value: 'Andaman', label: '🏝️ Andaman' },
  { value: 'Kerala', label: '🌴 Kerala' },
  { value: 'Goa', label: '🏖️ Goa' },
  { value: 'Himachal', label: '🏔️ Himachal Pradesh' },
  { value: 'Kashmir', label: '❄️ Kashmir' },
  { value: 'Rajasthan', label: '🏰 Rajasthan' },
  { value: 'Ladakh', label: '🏔️ Ladakh' },
  { value: 'North East', label: '🌲 North East India' },
  { value: 'Delhi', label: '🏛️ Delhi' },
  { value: 'Mumbai', label: '🌆 Mumbai' },
];

/**
 * Date window / season options.
 */
export const SEASON_OPTIONS: ComboboxOption[] = [
  { value: 'Summer 2026', label: 'Summer 2026 (Apr - Jun)' },
  { value: 'Monsoon 2026', label: 'Monsoon 2026 (Jul - Sep)' },
  { value: 'Winter 2026', label: 'Winter 2026-27 (Oct - Mar)' },
  { value: 'Flexible Dates', label: 'Flexible Dates' },
];

/**
 * Accommodation types.
 */
export const ACCOMMODATION_OPTIONS: ComboboxOption[] = [
  { value: 'Hotel', label: 'Hotel' },
  { value: 'Resort', label: 'Resort' },
  { value: 'Villa', label: 'Villa' },
  { value: 'Hostel', label: 'Hostel' },
  { value: 'Homestay', label: 'Homestay' },
  { value: 'Houseboat', label: 'Houseboat' },
  { value: 'Glamping', label: 'Glamping' },
  { value: 'Camp', label: 'Camp' },
];

/**
 * Meal plan options.
 */
export const MEAL_PLAN_OPTIONS: ComboboxOption[] = [
  { value: 'Room Only', label: 'Room Only (EP)' },
  { value: 'Breakfast', label: 'Breakfast (CP)' },
  { value: 'Half Board', label: 'Half Board (Breakfast + Dinner)' },
  { value: 'Full Board', label: 'Full Board (All Meals)' },
  { value: 'All Inclusive', label: 'All Inclusive' },
];
