export type EpistemicBasis = 'explicit' | 'inferred' | 'unknown';

export type EndCapIconId = 'plane' | 'travelers' | 'mountain' | 'calendar' | 'palm' | 'torii' | 'dunes';

export interface HighlightToken {
  text: string;
  color?: 'yellow' | 'blue' | 'green' | 'purple';
  targetRow?: 0 | 1 | 2 | 3 | 4;
}

export interface ChatBubble {
  id: string;
  time: string;
  segments: HighlightToken[];
}

export interface BriefRowItem {
  rowIndex: 0 | 1 | 2 | 3 | 4;
  label: string;
  value: string;
  subtitle?: string;
  basis: EpistemicBasis;
  needsConfirmation?: boolean;
  advisorFollowUp?: string;
  sourceQuote: string;
  thumbUrl?: string;
}

export interface DepartureBoardCase {
  id: 'italy' | 'japan' | 'morocco';
  dockTitle: string;
  dockSubtitle: string;
  dockIcon: 'colosseum' | 'torii' | 'palm';
  iataCode: string;
  tagImageUrl: string;
  /** 7 characters exactly for Row 1 (DESTINATION) */
  destinationCells: string;
  destinationPhotoUrl: string;
  destinationPhotoAlt: string;
  /** 11 characters exactly for Row 2 (TRAVELERS) */
  travelersCells: string;
  /** 7 characters exactly for Row 3 (DURATION) */
  durationCells: string;
  durationPhotoUrl: string;
  durationPhotoAlt: string;
  /** 10 characters for Row 4 scanning state (e.g. "APR 18-3? ") before locking to NEED CONFIRMATION */
  datesScanningCells: string;
  /** Whether Row 4 locks into the 7-cell yellow NEED CONFIRMATION + 3 dark blank cells state */
  datesNeedsConfirmation: boolean;
  /** 15 characters exactly for Row 5 (TRIP STYLE) */
  tripStyleCells: string;
  /** Bottom-right 5th end-cap icon */
  styleEndCapIcon: 'palm' | 'torii' | 'dunes';
  /** Frame 2 incoming voice/text request card */
  incomingVoiceCard: {
    timestamp: string;
    durationLabel: string;
    quote: string;
    waveformBars: number[];
  };
  /** Frame 3 multi-message chat thread with provenance highlights */
  chatThread: ChatBubble[];
  /** Frame 3 structured brief items */
  briefItems: BriefRowItem[];
}

export const BOARD_ROW_META: Array<{
  index: 0 | 1 | 2 | 3 | 4;
  label: string;
  endCapIcon: EndCapIconId;
  wireColor: string;
}> = [
  { index: 0, label: 'DESTINATION', endCapIcon: 'plane', wireColor: '#F7D12A' },
  { index: 1, label: 'TRAVELERS', endCapIcon: 'travelers', wireColor: '#48B6FF' },
  { index: 2, label: 'DURATION', endCapIcon: 'mountain', wireColor: '#5EE39A' },
  { index: 3, label: 'DATES', endCapIcon: 'calendar', wireColor: '#F5B82E' },
  { index: 4, label: 'TRIP STYLE', endCapIcon: 'palm', wireColor: '#B57BFF' },
];

/**
 * The 8 two-line yellow cells for Row 4 when `datesNeedsConfirmation === true`:
 * Top line:    N  | E  | E  | D  |    |    |    |
 * Bottom line: CO | NF | IR | MA | TI | ON |    |
 * Aligns 1:1 with the 8 physical flap columns (x=881..1204) above and below it,
 * followed by 3 dark blank flaps (x=1206..1358) matching the photo-flap span.
 */
export const NEED_CONFIRMATION_CELLS: Array<{ top: string; bottom: string }> = [
  { top: 'N', bottom: 'CO' },
  { top: 'E', bottom: 'NF' },
  { top: 'E', bottom: 'IR' },
  { top: 'D', bottom: 'MA' },
  { top: '', bottom: 'TI' },
  { top: '', bottom: 'ON' },
  { top: '', bottom: '' },
  { top: '', bottom: '' },
];

export const DEPARTURE_BOARD_CASES: Record<DepartureBoardCase['id'], DepartureBoardCase> = {
  italy: {
    id: 'italy',
    dockTitle: 'Italy',
    dockSubtitle: 'Culture + Coast',
    dockIcon: 'colosseum',
    iataCode: 'ITA',
    tagImageUrl: '/landing/departure-board/tag-ita.png',
    destinationCells: 'ITALY  ',
    destinationPhotoUrl: '/landing/departure-board/photo-italy-1.png',
    destinationPhotoAlt: 'Roman Colosseum bathed in golden afternoon light',
    travelersCells: '4 TRAVELERS',
    durationCells: '10 DAYS',
    durationPhotoUrl: '/landing/departure-board/photo-italy-2.png',
    durationPhotoAlt: 'Amalfi Coast cliffside villages overlooking the Mediterranean',
    datesScanningCells: 'APR 18-3? ',
    datesNeedsConfirmation: true,
    tripStyleCells: 'CULTURE + COAST',
    styleEndCapIcon: 'palm',
    incomingVoiceCard: {
      timestamp: '10:14 AM',
      durationLabel: '0:24',
      quote:
        '“Hi! Looking to take a group of 4 to Italy for about 10 days next spring. Would love a mix of culture and coastal time. Can you put together some options?”',
      waveformBars: [
        0.25, 0.42, 0.68, 0.92, 0.55, 0.78, 0.35, 0.62, 0.88, 0.96, 0.52, 0.74, 0.44, 0.82, 0.64,
        0.38, 0.72, 0.9, 0.48, 0.32, 0.58, 0.76, 0.4, 0.28,
      ],
    },
    chatThread: [
      {
        id: 'it-1',
        time: '9:14 AM',
        segments: [
          { text: "Hi! We're thinking about " },
          { text: 'Italy', color: 'yellow', targetRow: 0 },
          { text: ' next spring. Probably ' },
          { text: '4 of us', color: 'blue', targetRow: 1 },
          { text: ' (2 couples)...' },
        ],
      },
      {
        id: 'it-2',
        time: '9:16 AM',
        segments: [
          { text: '...around ' },
          { text: '10 days?', color: 'green', targetRow: 2 },
          { text: ' — Not sure exact dates yet.' },
        ],
      },
      {
        id: 'it-3',
        time: '9:18 AM',
        segments: [
          { text: 'We love ' },
          { text: 'food, history', color: 'yellow', targetRow: 4 },
          { text: ' and coastal towns — Rome for sure, maybe the ' },
          { text: 'Amalfi Coast?', color: 'blue', targetRow: 4 },
        ],
      },
      {
        id: 'it-4',
        time: '9:20 AM',
        segments: [
          { text: "We'd prefer a mix of " },
          { text: 'guided', color: 'blue', targetRow: 4 },
          { text: ' ' },
          { text: 'experiences', color: 'yellow', targetRow: 4 },
          { text: ' and some free time. Mid-range to upscale is good.' },
        ],
      },
    ],
    briefItems: [
      {
        rowIndex: 0,
        label: 'Destination',
        value: 'Italy',
        basis: 'explicit',
        sourceQuote: '“Hi! We’re thinking about Italy next spring… Rome for sure, maybe the Amalfi Coast?”',
        thumbUrl: '/landing/departure-board/photo-italy-1.png',
      },
      {
        rowIndex: 1,
        label: 'Travelers',
        value: '4 travelers',
        subtitle: '2 couples (inferred)',
        basis: 'inferred',
        sourceQuote: '“Probably 4 of us (2 couples)…” — requires 2 double-occupancy rooms.',
      },
      {
        rowIndex: 2,
        label: 'Duration',
        value: '10 days',
        basis: 'explicit',
        sourceQuote: '“…around 10 days? — Not sure exact dates yet.”',
      },
      {
        rowIndex: 3,
        label: 'Dates',
        value: 'Needs confirmation',
        basis: 'unknown',
        needsConfirmation: true,
        sourceQuote: '“next spring… Not sure exact dates yet.”',
        advisorFollowUp:
          'Confirm target April/May departure window and whether Easter week is excluded before pricing coastal hotels.',
      },
      {
        rowIndex: 4,
        label: 'Trip style',
        value: 'Culture + Coast',
        subtitle: 'Food, history, coastal towns, guided experiences',
        basis: 'explicit',
        sourceQuote: '“We love food, history and coastal towns… mix of guided experiences and some free time.”',
        thumbUrl: '/landing/departure-board/photo-italy-2.png',
      },
    ],
  },

  japan: {
    id: 'japan',
    dockTitle: 'Japan',
    dockSubtitle: 'Culture + Food',
    dockIcon: 'torii',
    iataCode: 'JPN',
    tagImageUrl: '/landing/departure-board/tag-jpn.png',
    destinationCells: 'JAPAN  ',
    destinationPhotoUrl: '/landing/departure-board/photo-japan-1.png',
    destinationPhotoAlt: 'Chureito Pagoda and Mount Fuji framed by cherry blossoms',
    travelersCells: '2 TRAVELERS',
    durationCells: '14 DAYS',
    durationPhotoUrl: '/landing/departure-board/photo-japan-2.png',
    durationPhotoAlt: 'Mount Fuji reflected over lake with spring sakura blossoms',
    datesScanningCells: 'OCT 12-2? ',
    datesNeedsConfirmation: true,
    tripStyleCells: 'CULTURE + FOOD ',
    styleEndCapIcon: 'torii',
    incomingVoiceCard: {
      timestamp: '2:42 PM',
      durationLabel: '0:19',
      quote:
        '“Hey! Two of us want to do Japan for 14 days—Tokyo, Kyoto, and great culinary spots. Thinking autumn foliage, exact dates still open.”',
      waveformBars: [
        0.32, 0.58, 0.84, 0.46, 0.72, 0.94, 0.62, 0.4, 0.78, 0.88, 0.5, 0.66, 0.92, 0.54, 0.36,
        0.7, 0.82, 0.45, 0.3, 0.64, 0.52, 0.38, 0.26, 0.2,
      ],
    },
    chatThread: [
      {
        id: 'jp-1',
        time: '2:40 PM',
        segments: [
          { text: 'Planning our anniversary trip to ' },
          { text: 'Japan', color: 'yellow', targetRow: 0 },
          { text: ' for just the ' },
          { text: '2 of us', color: 'blue', targetRow: 1 },
          { text: '.' },
        ],
      },
      {
        id: 'jp-2',
        time: '2:41 PM',
        segments: [
          { text: 'Thinking ' },
          { text: '14 days', color: 'green', targetRow: 2 },
          { text: ' total, though our exact October window is not locked yet.' },
        ],
      },
      {
        id: 'jp-3',
        time: '2:42 PM',
        segments: [
          { text: 'Big priority on ' },
          { text: 'temples, ryokans', color: 'yellow', targetRow: 4 },
          { text: ' and ' },
          { text: 'omakase + food tours', color: 'blue', targetRow: 4 },
          { text: ' in Tokyo & Kyoto.' },
        ],
      },
    ],
    briefItems: [
      {
        rowIndex: 0,
        label: 'Destination',
        value: 'Japan',
        subtitle: 'Tokyo · Hakone · Kyoto Golden Route',
        basis: 'explicit',
        sourceQuote: '“Planning our anniversary trip to Japan… in Tokyo & Kyoto.”',
        thumbUrl: '/landing/departure-board/photo-japan-1.png',
      },
      {
        rowIndex: 1,
        label: 'Travelers',
        value: '2 travelers',
        subtitle: '1 couple, anniversary (inferred)',
        basis: 'inferred',
        sourceQuote: '“Planning our anniversary trip… for just the 2 of us.”',
      },
      {
        rowIndex: 2,
        label: 'Duration',
        value: '14 days',
        subtitle: '3-city rail + ryokan pacing',
        basis: 'explicit',
        sourceQuote: '“Thinking 14 days total…”',
      },
      {
        rowIndex: 3,
        label: 'Dates',
        value: 'Needs confirmation',
        basis: 'unknown',
        needsConfirmation: true,
        sourceQuote: '“…though our exact October window is not locked yet.”',
        advisorFollowUp:
          'Confirm exact October/November departure dates and private-onsen ryokan night count before holding Kyoto inventory.',
      },
      {
        rowIndex: 4,
        label: 'Trip style',
        value: 'Culture + Food',
        subtitle: 'Temples, ryokans, omakase, culinary neighborhoods',
        basis: 'explicit',
        sourceQuote: '“Big priority on temples, ryokans and omakase + food tours…”',
        thumbUrl: '/landing/departure-board/photo-japan-2.png',
      },
    ],
  },

  morocco: {
    id: 'morocco',
    dockTitle: 'Morocco',
    dockSubtitle: 'Adventure',
    dockIcon: 'palm',
    iataCode: 'MAR',
    tagImageUrl: '/landing/departure-board/tag-mar.png',
    destinationCells: 'MOROCCO',
    destinationPhotoUrl: '/landing/departure-board/photo-morocco-1.png',
    destinationPhotoAlt: 'Koutoubia Mosque minaret and Marrakech medina at sunset',
    travelersCells: '6 TRAVELERS',
    durationCells: '8  DAYS',
    durationPhotoUrl: '/landing/departure-board/photo-morocco-2.png',
    durationPhotoAlt: 'Sweeping golden dunes of the Erg Chebbi Sahara desert',
    datesScanningCells: 'NOV 04-1? ',
    datesNeedsConfirmation: true,
    tripStyleCells: 'DESERT + KASBAH',
    styleEndCapIcon: 'dunes',
    incomingVoiceCard: {
      timestamp: '4:08 PM',
      durationLabel: '0:28',
      quote:
        '“We want to take our family of 6 to Morocco for 8 days—Marrakech, an Atlas Mountain kasbah, and a luxury Sahara camp. Still checking November school break dates.”',
      waveformBars: [
        0.38, 0.64, 0.76, 0.9, 0.52, 0.44, 0.82, 0.95, 0.7, 0.48, 0.62, 0.86, 0.56, 0.42, 0.78,
        0.68, 0.5, 0.84, 0.6, 0.36, 0.48, 0.66, 0.34, 0.24,
      ],
    },
    chatThread: [
      {
        id: 'ma-1',
        time: '4:05 PM',
        segments: [
          { text: "We'd love to take the family to " },
          { text: 'Morocco', color: 'yellow', targetRow: 0 },
          { text: ' — ' },
          { text: '6 travelers', color: 'blue', targetRow: 1 },
          { text: ' across two generations.' },
        ],
      },
      {
        id: 'ma-2',
        time: '4:06 PM',
        segments: [
          { text: 'Can do ' },
          { text: '8 days', color: 'green', targetRow: 2 },
          { text: ' around November, still coordinating school break dates.' },
        ],
      },
      {
        id: 'ma-3',
        time: '4:08 PM',
        segments: [
          { text: 'Want a private ' },
          { text: 'Sahara desert camp', color: 'yellow', targetRow: 4 },
          { text: ' plus ' },
          { text: 'Atlas kasbah + medina', color: 'blue', targetRow: 4 },
          { text: ' with private 4x4 transfers.' },
        ],
      },
    ],
    briefItems: [
      {
        rowIndex: 0,
        label: 'Destination',
        value: 'Morocco',
        subtitle: 'Marrakech · High Atlas · Erg Chebbi',
        basis: 'explicit',
        sourceQuote: '“We’d love to take the family to Morocco…”',
        thumbUrl: '/landing/departure-board/photo-morocco-1.png',
      },
      {
        rowIndex: 1,
        label: 'Travelers',
        value: '6 travelers',
        subtitle: 'Multi-generational family (inferred)',
        basis: 'inferred',
        sourceQuote: '“6 travelers across two generations.”',
      },
      {
        rowIndex: 2,
        label: 'Duration',
        value: '8 days',
        subtitle: 'Requires charter/flight or tight drive check',
        basis: 'explicit',
        sourceQuote: '“Can do 8 days around November…”',
      },
      {
        rowIndex: 3,
        label: 'Dates',
        value: 'Needs confirmation',
        basis: 'unknown',
        needsConfirmation: true,
        sourceQuote: '“…still coordinating school break dates.”',
        advisorFollowUp:
          'Confirm exact November school holiday dates and whether the group prefers a short domestic hop to Errachidia over the 9-hour desert drive.',
      },
      {
        rowIndex: 4,
        label: 'Trip style',
        value: 'Desert + Kasbah',
        subtitle: 'Private Sahara camp, Atlas kasbah, medina riad',
        basis: 'explicit',
        sourceQuote: '“Want a private Sahara desert camp plus Atlas kasbah + medina…”',
        thumbUrl: '/landing/departure-board/photo-morocco-2.png',
      },
    ],
  },
};

export const CASE_ORDER: Array<DepartureBoardCase['id']> = ['japan', 'morocco', 'italy'];

export type InquiryId = DepartureBoardCase['id'];
export type BoardRowId = 'destination' | 'travelers' | 'duration' | 'dates' | 'tripStyle';

export interface FlapCellSpec {
  topText: string;
  bottomText?: string;
  variant:
    | 'cream'
    | 'yellow_two_line'
    | 'scanning_amber'
    | 'blurred_flip'
    | 'dark_question'
    | 'dark_blank';
  subLabel?: string;
}

export interface BoardRowSpec {
  id: BoardRowId;
  label: string;
  cells: FlapCellSpec[];
  scanningCells?: FlapCellSpec[];
  confirmedCells?: FlapCellSpec[];
  confirmedValueLabel?: string;
  photoFlap?: {
    src: string;
    alt: string;
    caption?: string;
  };
  fact: {
    value: string;
    basis: EpistemicBasis;
    evidenceQuote?: string;
    advisorFollowUp?: string;
  };
}

export interface DepartureInquiryFixture {
  id: InquiryId;
  pillTitle: string;
  pillSubtitle: string;
  eyebrow: string;
  subcopy: string;
  tagCode: string;
  hangingTagImage: string;
  tripStyleIcon: 'palm' | 'torii' | 'dunes';
  rows: BoardRowSpec[];
  voiceNote: {
    timestamp: string;
    durationLabel: string;
    quote: string;
    waveformHeights: number[];
  };
  chatThread: Array<{
    id: string;
    timestamp: string;
    segments: Array<{
      text: string;
      highlight?: {
        color: 'yellow' | 'cyan' | 'green' | 'purple';
        targetRow: BoardRowId;
      };
    }>;
  }>;
  briefSummary: Array<{
    rowId: BoardRowId;
    label: string;
    value: string;
    subtitle?: string;
    thumbUrl?: string;
    status: 'confirmed' | 'needs_confirmation';
  }>;
}

const ROW_INDEX_TO_ID: Record<0 | 1 | 2 | 3 | 4, BoardRowId> = {
  0: 'destination',
  1: 'travelers',
  2: 'duration',
  3: 'dates',
  4: 'tripStyle',
};

function stringToCreamCells(str: string, len: number): FlapCellSpec[] {
  const padded = str.padEnd(len, ' ').slice(0, len);
  return Array.from(padded).map((ch) => ({
    topText: ch,
    variant: 'cream' as const,
  }));
}

function stringToScanningCells(str: string, _len: number): FlapCellSpec[] {
  // Reference Frame 2 Row 4 has 10 cells:
  // Cols 0-1: dark/gold blurred flipping flaps ('N', '-')
  // Cols 2-4: cream 'A', 'P', 'R'
  // Cols 5-7: cream '1', '8', '-'
  // Col 8: motion-blurred cream '3' (or day digit)
  // Col 9: dark charcoal cell with bright white '?'
  const trimmed = str.trim(); // e.g. "APR 18-3?"
  const chars = Array.from(trimmed.replace(/\s+/g, '')).slice(0, 8); // ['A','P','R','1','8','-','3','?']
  return [
    { topText: 'N', variant: 'blurred_flip' },
    { topText: '-', variant: 'blurred_flip' },
    { topText: chars[0] ?? 'A', variant: 'cream' },
    { topText: chars[1] ?? 'P', variant: 'cream' },
    { topText: chars[2] ?? 'R', variant: 'cream' },
    { topText: chars[3] ?? '1', variant: 'cream' },
    { topText: chars[4] ?? '8', variant: 'cream' },
    { topText: chars[5] ?? '-', variant: 'cream' },
    { topText: chars[6] ?? '3', variant: 'blurred_flip' },
    { topText: chars[7] ?? '?', variant: 'dark_question' },
  ];
}

function buildDestinationScanningCells(destStr: string): FlapCellSpec[] {
  const clean = destStr.trim();
  if (clean === 'ITALY') {
    return [
      { topText: 'V', bottomText: 'G', variant: 'blurred_flip' },
      { topText: 'A', bottomText: 'R', variant: 'blurred_flip' },
      { topText: ' ', bottomText: ' ', variant: 'blurred_flip' },
      { topText: 'I', variant: 'cream' },
      { topText: 'T', variant: 'cream' },
      { topText: 'A', variant: 'cream' },
      { topText: 'L', variant: 'cream' },
      { topText: 'Y', variant: 'cream' },
    ];
  }
  const base = stringToCreamCells(clean.padStart(8, ' '), 8);
  base[0] = { topText: 'V', bottomText: 'G', variant: 'blurred_flip' };
  base[1] = { topText: 'A', bottomText: 'R', variant: 'blurred_flip' };
  return base;
}

function buildTravelersScanningCells(travStr: string): FlapCellSpec[] {
  const base = stringToCreamCells(travStr, 12);
  if (base.length > 1) {
    base[1] = { topText: 'A', bottomText: '6', variant: 'blurred_flip' };
  }
  return base;
}

function buildDatesRowCells(): FlapCellSpec[] {
  const yellowCells: FlapCellSpec[] = NEED_CONFIRMATION_CELLS.map((c) => ({
    topText: c.top,
    bottomText: c.bottom,
    variant: 'yellow_two_line' as const,
  }));
  const darkBlanks: FlapCellSpec[] = [
    { topText: ' ', variant: 'dark_blank' },
    { topText: ' ', variant: 'dark_blank' },
    { topText: ' ', variant: 'dark_blank' },
  ];
  return [...yellowCells, ...darkBlanks];
}

function buildConfirmedDatesRowCells(
  scanStr: string,
  durationStr?: string
): {
  cells: FlapCellSpec[];
  label: string;
} {
  const upper = scanStr.toUpperCase();
  const monthMeta: Record<string, { startDay: number; title: string }> = {
    JAN: { startDay: 14, title: 'Jan' },
    FEB: { startDay: 8, title: 'Feb' },
    MAR: { startDay: 12, title: 'Mar' },
    APR: { startDay: 18, title: 'Apr' },
    MAY: { startDay: 11, title: 'May' },
    JUN: { startDay: 10, title: 'Jun' },
    JUL: { startDay: 12, title: 'Jul' },
    AUG: { startDay: 6, title: 'Aug' },
    SEP: { startDay: 9, title: 'Sep' },
    OCT: { startDay: 12, title: 'Oct' },
    NOV: { startDay: 4, title: 'Nov' },
    DEC: { startDay: 5, title: 'Dec' },
  };
  const matchedKey = Object.keys(monthMeta).find((k) => upper.includes(k)) ?? 'APR';
  const meta = monthMeta[matchedKey];
  const parsedDays = durationStr ? Number.parseInt(durationStr.trim(), 10) : Number.NaN;
  const durationDays = Number.isFinite(parsedDays) && parsedDays >= 2 ? parsedDays : 10;
  const startDay = meta.startDay;
  const endDay = Math.min(28, startDay + durationDays - 1);
  const startPad = String(startDay).padStart(2, '0');
  const endPad = String(endDay).padStart(2, '0');
  const resolvedBoard = `${matchedKey}${startPad}-${endPad}`;
  const resolvedLabel = `${meta.title} ${startDay} – ${meta.title} ${endDay} (Confirmed)`;
  const chars = Array.from(resolvedBoard.padEnd(8, ' ').slice(0, 8));
  const creamCells: FlapCellSpec[] = chars.map((ch) => ({
    topText: ch,
    variant: 'cream' as const,
  }));
  const darkBlanks: FlapCellSpec[] = [
    { topText: ' ', variant: 'dark_blank' },
    { topText: ' ', variant: 'dark_blank' },
    { topText: ' ', variant: 'dark_blank' },
  ];
  return {
    cells: [...creamCells, ...darkBlanks],
    label: resolvedLabel,
  };
}

function adaptCaseToFixture(c: DepartureBoardCase): DepartureInquiryFixture {
  const b0 = c.briefItems[0];
  const b1 = c.briefItems[1];
  const b2 = c.briefItems[2];
  const b3 = c.briefItems[3];
  const b4 = c.briefItems[4];

  return {
    id: c.id,
    pillTitle: c.dockTitle,
    pillSubtitle: c.dockSubtitle,
    eyebrow: 'FOR TRAVEL ADVISORS',
    subcopy: 'Turn scattered travel requests into quote-ready briefs your team can actually use.',
    tagCode: c.iataCode,
    hangingTagImage: c.tagImageUrl,
    tripStyleIcon: c.styleEndCapIcon,
    rows: [
      {
        id: 'destination',
        label: 'DESTINATION',
        cells: stringToCreamCells(c.destinationCells, 8),
        scanningCells: buildDestinationScanningCells(c.destinationCells),
        photoFlap: {
          src: c.destinationPhotoUrl,
          alt: c.destinationPhotoAlt,
          caption: c.destinationPhotoAlt,
        },
        fact: {
          value: b0.value,
          basis: b0.basis,
          evidenceQuote: b0.sourceQuote.replace(/[“”]/g, ''),
        },
      },
      {
        id: 'travelers',
        label: 'TRAVELERS',
        cells: stringToCreamCells(c.travelersCells, 12),
        scanningCells: buildTravelersScanningCells(c.travelersCells),
        fact: {
          value: b1.value,
          basis: b1.basis,
          evidenceQuote: b1.sourceQuote.replace(/[“”]/g, ''),
        },
      },
      {
        id: 'duration',
        label: 'DURATION',
        cells: stringToCreamCells(c.durationCells, 8),
        photoFlap: {
          src: c.durationPhotoUrl,
          alt: c.durationPhotoAlt,
          caption: c.durationPhotoAlt,
        },
        fact: {
          value: b2.value,
          basis: b2.basis,
          evidenceQuote: b2.sourceQuote.replace(/[“”]/g, ''),
        },
      },
      {
        id: 'dates',
        label: 'DATES',
        cells: buildDatesRowCells(),
        scanningCells: stringToScanningCells(c.datesScanningCells, 10),
        confirmedCells: buildConfirmedDatesRowCells(c.datesScanningCells, c.durationCells).cells,
        confirmedValueLabel: buildConfirmedDatesRowCells(c.datesScanningCells, c.durationCells).label,
        fact: {
          value: b3.value,
          basis: b3.basis,
          evidenceQuote: b3.sourceQuote.replace(/[“”]/g, ''),
          advisorFollowUp: b3.advisorFollowUp,
        },
      },
      {
        id: 'tripStyle',
        label: 'TRIP STYLE',
        cells: stringToCreamCells(c.tripStyleCells, 15),
        fact: {
          value: b4.value,
          basis: b4.basis,
          evidenceQuote: b4.sourceQuote.replace(/[“”]/g, ''),
        },
      },
    ],
    voiceNote: {
      timestamp: c.incomingVoiceCard.timestamp,
      durationLabel: c.incomingVoiceCard.durationLabel,
      quote: c.incomingVoiceCard.quote.replace(/[“”]/g, ''),
      waveformHeights: c.incomingVoiceCard.waveformBars,
    },
    chatThread: c.chatThread.map((msg) => ({
      id: msg.id,
      timestamp: msg.time,
      segments: msg.segments.map((seg) => ({
        text: seg.text,
        highlight:
          seg.color && seg.targetRow !== undefined
            ? {
                color: seg.color === 'blue' ? 'cyan' : seg.color,
                targetRow: ROW_INDEX_TO_ID[seg.targetRow],
              }
            : undefined,
      })),
    })),
    briefSummary: c.briefItems.map((item) => ({
      rowId: ROW_INDEX_TO_ID[item.rowIndex],
      label: item.label,
      value: item.value,
      subtitle: item.subtitle,
      thumbUrl: item.thumbUrl,
      status: item.needsConfirmation ? 'needs_confirmation' : 'confirmed',
    })),
  };
}

export const INQUIRY_ORDER: readonly InquiryId[] = CASE_ORDER;

export const DEPARTURE_INQUIRIES: Record<InquiryId, DepartureInquiryFixture> = {
  italy: adaptCaseToFixture(DEPARTURE_BOARD_CASES.italy),
  japan: adaptCaseToFixture(DEPARTURE_BOARD_CASES.japan),
  morocco: adaptCaseToFixture(DEPARTURE_BOARD_CASES.morocco),
};

// ============================================================================
// DYNAMIC DESTINATION CATALOG & FREE-TEXT INQUIRY RESOLVER
// ============================================================================

export interface DynamicDestinationCatalogEntry {
  slug: string;
  displayName: string;
  /** Lowercase city/region/country aliases that resolve to this destination */
  aliases?: readonly string[];
  /** 7-character uppercase Solari drum token for Row 1 */
  boardToken7: string;
  /** 3-letter ISO-3 / IATA tag code */
  iataCode: string;
  /** Default traveler count when selected as a deterministic preset */
  defaultTravelersCount: number;
  /** Default trip duration in days when selected as a deterministic preset */
  defaultDurationDays: number;
  /** Default target month abbreviation for scanning & hold state */
  defaultMonthAbbrev: string;
  /** Candidate traveler counts for dynamic randomized rotations */
  travelersOptions?: readonly number[];
  /** Candidate trip durations (days) for dynamic randomized rotations */
  durationOptions?: readonly number[];
  /** Candidate target month abbreviations for dynamic randomized rotations */
  monthOptions?: readonly string[];
  /** Default trip style 15-character Solari drum token for Row 5 */
  defaultStyleToken15: string;
  defaultStyleLabel: string;
  defaultSubcopy: string;
  styleEndCapIcon: 'palm' | 'torii' | 'dunes';
  /** Fallback visual archetype mapped to local high-craft photography */
  visualArchetype: 'italy' | 'japan' | 'morocco';
  /** Dedicated Row 1 & Brief Row 1 destination photography plate */
  destinationPhotoUrl: string;
  destinationPhotoAlt: string;
  /** Dedicated Row 3 & Brief Row 5 duration/experience photography plate */
  durationPhotoUrl: string;
  durationPhotoAlt: string;
  /** Hanging luggage tag base image (reference tag for ITA/JPN/MAR or clean blank cardstock base) */
  tagImageUrl: string;
  sampleRouteSubtitle: string;
  seasonalFollowUp: string;
  sampleVoiceQuote: string;
}

export const DESTINATION_CATALOG_REGISTRY: readonly DynamicDestinationCatalogEntry[] = [
  {
    slug: 'italy',
    displayName: 'Italy',
    aliases: ['rome', 'florence', 'amalfi', 'venice', 'tuscany', 'sicily', 'como', 'milan', 'positano', 'capri', 'puglia', 'dolomites'],
    boardToken7: 'ITALY  ',
    iataCode: 'ITA',
    defaultTravelersCount: 4,
    defaultDurationDays: 10,
    defaultMonthAbbrev: 'APR',
    travelersOptions: [2, 4, 5, 6],
    durationOptions: [8, 10, 12, 14],
    monthOptions: ['APR', 'MAY', 'JUN', 'SEP', 'OCT'],
    defaultStyleToken15: 'CULTURE + COAST',
    defaultStyleLabel: 'Culture + Coast',
    defaultSubcopy: 'Food, history, coastal towns, guided experiences',
    styleEndCapIcon: 'palm',
    visualArchetype: 'italy',
    destinationPhotoUrl: '/landing/departure-board/photo-italy-1.png',
    destinationPhotoAlt: 'Roman Colosseum at golden hour',
    durationPhotoUrl: '/landing/departure-board/photo-italy-2.png',
    durationPhotoAlt: 'Amalfi Coast cliffside village over Mediterranean Sea',
    tagImageUrl: '/landing/departure-board/tag-ita.png',
    sampleRouteSubtitle: 'Rome · Florence · Amalfi Coast',
    seasonalFollowUp: 'Confirm April/May shoulder window before holding cliffside Amalfi inventory.',
    sampleVoiceQuote:
      'Hi! Looking to take a group of 4 to Italy for about 10 days next spring. Would love a mix of culture and coastal time. Can you put together some options?',
  },
  {
    slug: 'japan',
    displayName: 'Japan',
    aliases: ['tokyo', 'kyoto', 'osaka', 'hakone', 'hokkaido', 'naoshima', 'nara', 'okinawa', 'kanazawa'],
    boardToken7: 'JAPAN  ',
    iataCode: 'JPN',
    defaultTravelersCount: 2,
    defaultDurationDays: 14,
    defaultMonthAbbrev: 'OCT',
    travelersOptions: [2, 3, 4, 6],
    durationOptions: [10, 12, 14, 16],
    monthOptions: ['MAR', 'APR', 'OCT', 'NOV'],
    defaultStyleToken15: 'CULTURE + FOOD ',
    defaultStyleLabel: 'Culture + Food',
    defaultSubcopy: 'Temples, ryokans, omakase, culinary neighborhoods',
    styleEndCapIcon: 'torii',
    visualArchetype: 'japan',
    destinationPhotoUrl: '/landing/departure-board/photo-japan-1.png',
    destinationPhotoAlt: 'Chureito Pagoda and Mount Fuji framed by cherry blossoms',
    durationPhotoUrl: '/landing/departure-board/photo-japan-2.png',
    durationPhotoAlt: 'Kyoto wooden pagoda at sunset with Mount Fuji silhouette',
    tagImageUrl: '/landing/departure-board/tag-jpn.png',
    sampleRouteSubtitle: 'Tokyo · Hakone · Kyoto Golden Route',
    seasonalFollowUp: 'Confirm exact autumn foliage or sakura dates before locking private-onsen ryokans.',
    sampleVoiceQuote:
      'Hey! Two of us want to do Japan for 14 days—Tokyo, Kyoto, and great culinary spots. Thinking autumn foliage, exact dates still open.',
  },
  {
    slug: 'morocco',
    displayName: 'Morocco',
    aliases: ['marrakech', 'marrakesh', 'fes', 'fez', 'sahara', 'atlas mountains', 'casablanca', 'tangier', 'essaouira'],
    boardToken7: 'MOROCCO',
    iataCode: 'MAR',
    defaultTravelersCount: 6,
    defaultDurationDays: 8,
    defaultMonthAbbrev: 'NOV',
    travelersOptions: [2, 4, 5, 6],
    durationOptions: [7, 8, 10, 12],
    monthOptions: ['MAR', 'APR', 'OCT', 'NOV'],
    defaultStyleToken15: 'DESERT + KASBAH',
    defaultStyleLabel: 'Desert + Kasbah',
    defaultSubcopy: 'Private Sahara camp, Atlas kasbah, medina riad',
    styleEndCapIcon: 'dunes',
    visualArchetype: 'morocco',
    destinationPhotoUrl: '/landing/departure-board/photo-morocco-1.png',
    destinationPhotoAlt: 'Koutoubia Mosque and Marrakech medina with snow-capped Atlas Mountains',
    durationPhotoUrl: '/landing/departure-board/photo-morocco-2.png',
    durationPhotoAlt: 'Erg Chebbi Sahara desert dunes at golden sunset',
    tagImageUrl: '/landing/departure-board/tag-mar.png',
    sampleRouteSubtitle: 'Marrakech · High Atlas · Erg Chebbi',
    seasonalFollowUp: 'Confirm November dates and whether domestic flight hop is preferred over 4x4 drive.',
    sampleVoiceQuote:
      'We want to take our family of 6 to Morocco for 8 days—Marrakech, an Atlas Mountain kasbah, and a luxury Sahara camp. Still checking November school break dates.',
  },
  {
    slug: 'dubai',
    displayName: 'Dubai',
    aliases: ['uae', 'abu dhabi', 'united arab emirates', 'burj khalifa', 'palm jumeirah', 'arabian desert'],
    boardToken7: 'DUBAI  ',
    iataCode: 'DXB',
    defaultTravelersCount: 2,
    defaultDurationDays: 7,
    defaultMonthAbbrev: 'JUN',
    travelersOptions: [2, 4, 5, 6],
    durationOptions: [6, 7, 8, 10],
    monthOptions: ['FEB', 'MAR', 'JUN', 'OCT', 'NOV', 'DEC'],
    defaultStyleToken15: 'LUXURY + DESERT',
    defaultStyleLabel: 'Luxury + Desert',
    defaultSubcopy: 'Downtown Burj views, private desert oasis, Palm yacht charter',
    styleEndCapIcon: 'dunes',
    visualArchetype: 'morocco',
    destinationPhotoUrl: '/landing/departure-board/catalog/photo-dubai-1.png',
    destinationPhotoAlt: 'Dubai Burj Khalifa and downtown skyline at golden sunset',
    durationPhotoUrl: '/landing/departure-board/catalog/photo-dubai-2.png',
    durationPhotoAlt: 'Arabian desert luxury resort pool surrounded by golden dunes',
    tagImageUrl: '/landing/departure-board/tag-blank-gold.png',
    sampleRouteSubtitle: 'Downtown Dubai · Palm Jumeirah · Al Maha Desert Reserve',
    seasonalFollowUp: 'Confirm target departure week and split between Palm Jumeirah suite and private desert conservation reserve.',
    sampleVoiceQuote:
      'Hi! Looking to take 2 travelers to Dubai for 7 days in June — Downtown skyline suites, private desert oasis, and yacht charter, flexible on dates.',
  },
  {
    slug: 'greece',
    displayName: 'Greece',
    aliases: ['santorini', 'mykonos', 'athens', 'cyclades', 'crete', 'paros', 'naxos', 'milos', 'corfu'],
    boardToken7: 'GREECE ',
    iataCode: 'GRC',
    defaultTravelersCount: 5,
    defaultDurationDays: 12,
    defaultMonthAbbrev: 'JUN',
    travelersOptions: [2, 4, 5, 6],
    durationOptions: [8, 10, 12, 14],
    monthOptions: ['MAY', 'JUN', 'JUL', 'SEP'],
    defaultStyleToken15: 'ISLAND + YACHT ',
    defaultStyleLabel: 'Island + Yacht',
    defaultSubcopy: 'Cyclades island hopping, caldera suites, private catamaran',
    styleEndCapIcon: 'palm',
    visualArchetype: 'italy',
    destinationPhotoUrl: '/landing/departure-board/catalog/photo-greece-1.png',
    destinationPhotoAlt: 'Santorini Oia blue-domed churches overlooking the Aegean caldera',
    durationPhotoUrl: '/landing/departure-board/catalog/photo-greece-2.png',
    durationPhotoAlt: 'Milos Sarakiniko turquoise Aegean cove and white volcanic cliffs',
    tagImageUrl: '/landing/departure-board/tag-blank-gold.png',
    sampleRouteSubtitle: 'Athens · Naxos · Milos · Santorini',
    seasonalFollowUp: 'Confirm June/September window and ferry vs. helicopter inter-island preference.',
    sampleVoiceQuote:
      'Hi! Family of 5 looking at Greece for 12 days in June — private catamaran in the Cyclades and caldera suites, flexible on dates.',
  },
  {
    slug: 'switzerland',
    displayName: 'Switzerland',
    aliases: ['swiss', 'zermatt', 'zurich', 'lucerne', 'interlaken', 'st moritz', 'geneva', 'gstaad', 'matterhorn', 'swiss alps'],
    boardToken7: 'SWISS  ',
    iataCode: 'CHE',
    defaultTravelersCount: 4,
    defaultDurationDays: 9,
    defaultMonthAbbrev: 'SEP',
    travelersOptions: [2, 4, 6],
    durationOptions: [7, 9, 10, 12],
    monthOptions: ['JAN', 'FEB', 'JUL', 'AUG', 'SEP'],
    defaultStyleToken15: 'ALPINE + RAIL  ',
    defaultStyleLabel: 'Alpine + Rail',
    defaultSubcopy: 'First-class panoramic rail, Zermatt chalets, Lake Lucerne',
    styleEndCapIcon: 'torii',
    visualArchetype: 'japan',
    destinationPhotoUrl: '/landing/departure-board/catalog/photo-switzerland-1.png',
    destinationPhotoAlt: 'Matterhorn peak in Zermatt glowing at sunrise',
    durationPhotoUrl: '/landing/departure-board/catalog/photo-switzerland-2.png',
    durationPhotoAlt: 'Glacier Express red panoramic train crossing the Landwasser Viaduct',
    tagImageUrl: '/landing/departure-board/tag-blank-cream.png',
    sampleRouteSubtitle: 'Zurich · Lucerne · Interlaken · Zermatt',
    seasonalFollowUp: 'Confirm Glacier Express Excellence Class seat availability for target departure week.',
    sampleVoiceQuote:
      'Looking to take a group of 4 to Switzerland for 9 days in September — first-class panoramic rail and Zermatt chalets, still coordinating exact dates.',
  },
  {
    slug: 'peru',
    displayName: 'Peru',
    aliases: ['machu picchu', 'cusco', 'lima', 'sacred valley', 'andes', 'titicaca', 'arequipa'],
    boardToken7: 'PERU   ',
    iataCode: 'PER',
    defaultTravelersCount: 2,
    defaultDurationDays: 11,
    defaultMonthAbbrev: 'MAY',
    travelersOptions: [2, 4, 5, 6],
    durationOptions: [8, 10, 11, 13],
    monthOptions: ['APR', 'MAY', 'JUN', 'SEP', 'OCT'],
    defaultStyleToken15: 'ANDES + CULTURE',
    defaultStyleLabel: 'Andes + Culture',
    defaultSubcopy: 'Sacred Valley lodges, Hiram Bingham rail, Lima gastronomy',
    styleEndCapIcon: 'dunes',
    visualArchetype: 'morocco',
    destinationPhotoUrl: '/landing/departure-board/catalog/photo-peru-1.png',
    destinationPhotoAlt: 'Machu Picchu Inca citadel in misty morning Andes peaks',
    durationPhotoUrl: '/landing/departure-board/catalog/photo-peru-2.png',
    durationPhotoAlt: 'Sacred Valley green agricultural terraces at golden hour',
    tagImageUrl: '/landing/departure-board/tag-blank-terracotta.png',
    sampleRouteSubtitle: 'Lima · Sacred Valley · Machu Picchu · Cusco',
    seasonalFollowUp: 'Confirm exact entry dates immediately to secure Machu Picchu circuit permits.',
    sampleVoiceQuote:
      'Two of us want to explore Peru for 11 days in May — Sacred Valley lodges, Hiram Bingham train, and Lima dining, flexible on dates.',
  },
  {
    slug: 'iceland',
    displayName: 'Iceland',
    aliases: ['reykjavik', 'vik', 'blue lagoon', 'golden circle', 'vatnajokull'],
    boardToken7: 'ICELAND',
    iataCode: 'ISL',
    defaultTravelersCount: 4,
    defaultDurationDays: 7,
    defaultMonthAbbrev: 'FEB',
    travelersOptions: [2, 3, 4, 6],
    durationOptions: [6, 7, 8, 10],
    monthOptions: ['FEB', 'MAR', 'JUL', 'AUG', 'OCT'],
    defaultStyleToken15: 'GLACIER + FJORD',
    defaultStyleLabel: 'Glacier + Fjord',
    defaultSubcopy: 'South Coast super-jeep, geothermal retreats, ice caves',
    styleEndCapIcon: 'torii',
    visualArchetype: 'japan',
    destinationPhotoUrl: '/landing/departure-board/catalog/photo-iceland-1.png',
    destinationPhotoAlt: 'Kirkjufell mountain and waterfalls under green aurora borealis',
    durationPhotoUrl: '/landing/departure-board/catalog/photo-iceland-2.png',
    durationPhotoAlt: 'Jokulsarlon glacier lagoon with luminous blue icebergs at sunset',
    tagImageUrl: '/landing/departure-board/tag-blank-cream.png',
    sampleRouteSubtitle: 'Reykjavik · Highlands · Vik · Vatnajökull',
    seasonalFollowUp: 'Confirm winter aurora vs. midnight-sun window and 4x4 super-jeep guide allocation.',
    sampleVoiceQuote:
      'Thinking of taking 4 of us to Iceland for 7 days in February — South Coast super-jeep, ice caves, and geothermal retreats, exact dates still open.',
  },
  {
    slug: 'kenya',
    displayName: 'Kenya',
    aliases: ['nairobi', 'masai mara', 'maasai mara', 'amboseli', 'laikipia', 'lewa', 'samburu'],
    boardToken7: 'KENYA  ',
    iataCode: 'KEN',
    defaultTravelersCount: 6,
    defaultDurationDays: 10,
    defaultMonthAbbrev: 'AUG',
    travelersOptions: [2, 4, 5, 6],
    durationOptions: [8, 10, 12, 14],
    monthOptions: ['JUL', 'AUG', 'SEP', 'OCT'],
    defaultStyleToken15: 'SAFARI + LODGE ',
    defaultStyleLabel: 'Safari + Lodge',
    defaultSubcopy: 'Private conservancy tented camps, bush flights, Masai Mara',
    styleEndCapIcon: 'dunes',
    visualArchetype: 'morocco',
    destinationPhotoUrl: '/landing/departure-board/catalog/photo-kenya-1.png',
    destinationPhotoAlt: 'Maasai Mara savannah at golden sunset with acacia and elephants',
    durationPhotoUrl: '/landing/departure-board/catalog/photo-kenya-2.png',
    durationPhotoAlt: 'Amboseli luxury safari tent with snow-crowned Mount Kilimanjaro',
    tagImageUrl: '/landing/departure-board/tag-blank-terracotta.png',
    sampleRouteSubtitle: 'Nairobi · Lewa Conservancy · Masai Mara',
    seasonalFollowUp: 'Confirm exact bush-plane luggage allowance and Great Migration river-crossing window.',
    sampleVoiceQuote:
      'Family of 6 planning Kenya for 10 days in August — private conservancy safari camps and Masai Mara bush flights, still coordinating dates.',
  },
  {
    slug: 'portugal',
    displayName: 'Portugal',
    aliases: ['lisbon', 'porto', 'douro', 'algarve', 'comporta', 'sintra', 'alentejo', 'madeira', 'azores'],
    boardToken7: 'PORTUGL',
    iataCode: 'PRT',
    defaultTravelersCount: 2,
    defaultDurationDays: 9,
    defaultMonthAbbrev: 'OCT',
    travelersOptions: [2, 4, 6],
    durationOptions: [7, 9, 10, 12],
    monthOptions: ['APR', 'MAY', 'JUN', 'SEP', 'OCT'],
    defaultStyleToken15: 'WINE + COAST   ',
    defaultStyleLabel: 'Wine + Coast',
    defaultSubcopy: 'Douro Valley quintas, Lisbon design hotels, Comporta coast',
    styleEndCapIcon: 'palm',
    visualArchetype: 'italy',
    destinationPhotoUrl: '/landing/departure-board/catalog/photo-portugal-1.png',
    destinationPhotoAlt: 'Historic yellow tram in Lisbon Alfama district with terracotta rooftops',
    durationPhotoUrl: '/landing/departure-board/catalog/photo-portugal-2.png',
    durationPhotoAlt: 'Douro Valley terraced vineyards winding above the river at sunset',
    tagImageUrl: '/landing/departure-board/tag-blank-gold.png',
    sampleRouteSubtitle: 'Porto · Douro Valley · Lisbon · Comporta',
    seasonalFollowUp: 'Confirm harvest-season river cruise and private driver days across Douro and Alentejo.',
    sampleVoiceQuote:
      'Two of us looking at Portugal for 9 days sometime in October — Douro Valley wine quintas, Lisbon, and Comporta coast, flexible on dates.',
  },
  {
    slug: 'bali',
    displayName: 'Bali',
    aliases: ['ubud', 'uluwatu', 'seminyak', 'canggu', 'nusa dua', 'indonesia', 'komodo', 'lombok'],
    boardToken7: 'BALI   ',
    iataCode: 'IDN',
    defaultTravelersCount: 2,
    defaultDurationDays: 12,
    defaultMonthAbbrev: 'JUL',
    travelersOptions: [2, 4, 5],
    durationOptions: [8, 10, 12, 14],
    monthOptions: ['MAY', 'JUN', 'JUL', 'AUG', 'SEP'],
    defaultStyleToken15: 'VILLA + WELLNES',
    defaultStyleLabel: 'Villa + Wellness',
    defaultSubcopy: 'Ubud jungle sanctuaries, private cliff villas, holistic spa',
    styleEndCapIcon: 'palm',
    visualArchetype: 'italy',
    destinationPhotoUrl: '/landing/departure-board/catalog/photo-bali-1.png',
    destinationPhotoAlt: 'Ubud Tegallalang emerald rice terraces in morning mist',
    durationPhotoUrl: '/landing/departure-board/catalog/photo-bali-2.png',
    durationPhotoAlt: 'Uluwatu dramatic ocean cliffside temple at golden sunset',
    tagImageUrl: '/landing/departure-board/tag-blank-gold.png',
    sampleRouteSubtitle: 'Ubud · Sidemen Valley · Uluwatu Coast',
    seasonalFollowUp: 'Confirm July dry-season window and private pool villa split between Ubud and Uluwatu.',
    sampleVoiceQuote:
      'Two of us planning Bali for 12 days in July — Ubud jungle wellness sanctuary and private coastal villa, flexible on dates.',
  },
  {
    slug: 'patagonia',
    displayName: 'Patagonia',
    aliases: ['torres del paine', 'chile', 'el chalten', 'calafate', 'perito moreno', 'atacama', 'santiago'],
    boardToken7: 'PATAGON',
    iataCode: 'CHL',
    defaultTravelersCount: 4,
    defaultDurationDays: 14,
    defaultMonthAbbrev: 'DEC',
    travelersOptions: [2, 4, 6],
    durationOptions: [10, 12, 14, 16],
    monthOptions: ['JAN', 'FEB', 'NOV', 'DEC'],
    defaultStyleToken15: 'TREK + ESTANCIA',
    defaultStyleLabel: 'Trek + Estancia',
    defaultSubcopy: 'Torres del Paine luxury lodges, private pumas & glaciers',
    styleEndCapIcon: 'torii',
    visualArchetype: 'japan',
    destinationPhotoUrl: '/landing/departure-board/catalog/photo-patagonia-1.png',
    destinationPhotoAlt: 'Torres del Paine granite peaks glowing pink at sunrise over turquoise lake',
    durationPhotoUrl: '/landing/departure-board/catalog/photo-patagonia-2.png',
    durationPhotoAlt: 'Perito Moreno glacier wall calving into turquoise Patagonian waters',
    tagImageUrl: '/landing/departure-board/tag-blank-cream.png',
    sampleRouteSubtitle: 'Santiago · Torres del Paine · El Chaltén',
    seasonalFollowUp: 'Confirm austral summer December window and cross-border private transfer permits.',
    sampleVoiceQuote:
      'Group of 4 heading to Patagonia for 14 days in December — Torres del Paine luxury estancia and glacier trekking, exact dates still open.',
  },
  {
    slug: 'norway',
    displayName: 'Norway',
    aliases: ['lofoten', 'oslo', 'bergen', 'tromso', 'geiranger', 'flam', 'svalbard'],
    boardToken7: 'NORWAY ',
    iataCode: 'NOR',
    defaultTravelersCount: 3,
    defaultDurationDays: 8,
    defaultMonthAbbrev: 'JAN',
    travelersOptions: [2, 3, 4, 5],
    durationOptions: [7, 8, 10, 12],
    monthOptions: ['JAN', 'FEB', 'JUN', 'JUL', 'AUG'],
    defaultStyleToken15: 'FJORD + AURORA ',
    defaultStyleLabel: 'Fjord + Aurora',
    defaultSubcopy: 'Lofoten glass cabins, private fjord rib-boat, Arctic rail',
    styleEndCapIcon: 'torii',
    visualArchetype: 'japan',
    destinationPhotoUrl: '/landing/departure-board/catalog/photo-norway-1.png',
    destinationPhotoAlt: 'Lofoten Reine fjord peaks and red rorbu cabins reflected in calm water',
    durationPhotoUrl: '/landing/departure-board/catalog/photo-norway-2.png',
    durationPhotoAlt: 'Geirangerfjord Seven Sisters waterfall cascading into deep blue fjord',
    tagImageUrl: '/landing/departure-board/tag-blank-cream.png',
    sampleRouteSubtitle: 'Oslo · Bergen · Flåm · Lofoten Islands',
    seasonalFollowUp: 'Confirm Arctic aurora window and private heated fjord charter schedule.',
    sampleVoiceQuote:
      'Group of 3 looking at Norway for 8 days in January — private fjord cruise, Lofoten cabins, and northern lights, still coordinating dates.',
  },
  {
    slug: 'maldives',
    displayName: 'Maldives',
    aliases: ['male', 'baa atoll', 'noonu atoll', 'ari atoll'],
    boardToken7: 'MALDIVS',
    iataCode: 'MDV',
    defaultTravelersCount: 2,
    defaultDurationDays: 8,
    defaultMonthAbbrev: 'FEB',
    travelersOptions: [2, 4],
    durationOptions: [6, 7, 8, 10],
    monthOptions: ['JAN', 'FEB', 'MAR', 'APR', 'NOV', 'DEC'],
    defaultStyleToken15: 'ATOLL + LAGOON ',
    defaultStyleLabel: 'Atoll + Lagoon',
    defaultSubcopy: 'Overwater pool villas, seaplane transfer, private reef',
    styleEndCapIcon: 'palm',
    visualArchetype: 'italy',
    destinationPhotoUrl: '/landing/departure-board/catalog/photo-maldives-1.png',
    destinationPhotoAlt: 'Maldives luxury overwater bungalows over turquoise coral lagoon',
    durationPhotoUrl: '/landing/departure-board/catalog/photo-maldives-2.png',
    durationPhotoAlt: 'Private white sandbank island in the Indian Ocean at sunset',
    tagImageUrl: '/landing/departure-board/tag-blank-gold.png',
    sampleRouteSubtitle: 'Malé · Baa Atoll Biosphere · Private Sandbank',
    seasonalFollowUp: 'Confirm international arrival time in Malé to guarantee same-day daylight seaplane transfer.',
    sampleVoiceQuote:
      'Two of us planning Maldives for 8 days in February — overwater pool villa and private sandbank dining, flexible on dates.',
  },
  {
    slug: 'france',
    displayName: 'France',
    aliases: ['paris', 'provence', 'nice', 'cannes', 'antibes', 'st tropez', 'bordeaux', 'champagne', 'normandy', 'loire', 'french riviera', 'cote d azur'],
    boardToken7: 'FRANCE ',
    iataCode: 'FRA',
    defaultTravelersCount: 4,
    defaultDurationDays: 10,
    defaultMonthAbbrev: 'MAY',
    travelersOptions: [2, 4, 6],
    durationOptions: [7, 9, 10, 12],
    monthOptions: ['APR', 'MAY', 'JUN', 'SEP', 'OCT'],
    defaultStyleToken15: 'CULTURE + WINE ',
    defaultStyleLabel: 'Culture + Wine',
    defaultSubcopy: 'Parisian Left Bank suites, Provence vineyards, Riviera coast',
    styleEndCapIcon: 'palm',
    visualArchetype: 'italy',
    destinationPhotoUrl: '/landing/departure-board/catalog/photo-france-1.png',
    destinationPhotoAlt: 'Paris Eiffel Tower and Haussmann rooftops at golden hour sunset',
    durationPhotoUrl: '/landing/departure-board/catalog/photo-france-2.png',
    durationPhotoAlt: 'French Riviera Côte d’Azur cliffside harbor and yachts at sunset',
    tagImageUrl: '/landing/departure-board/tag-blank-gold.png',
    sampleRouteSubtitle: 'Paris · Provence · Côte d’Azur',
    seasonalFollowUp: 'Confirm TGV First Class rail vs. private aviation hop between Paris and Nice.',
    sampleVoiceQuote:
      'Group of 4 looking at France for 10 days in May — Paris Left Bank, Provence wine estates, and Riviera coast, flexible on dates.',
  },
];

interface GlobalGazetteerSpec {
  displayName: string;
  boardToken7: string;
  iataCode: string;
  aliases: readonly string[];
  routeSubtitle: string;
  styleToken15: string;
  styleLabel: string;
  styleSubcopy: string;
  photoSlug: string;
  tagVariant: 'gold' | 'cream' | 'terracotta';
  endCapIcon: 'palm' | 'torii' | 'dunes';
}

const GLOBAL_DESTINATION_FALLBACKS: readonly GlobalGazetteerSpec[] = [
  {
    displayName: 'Spain',
    boardToken7: 'SPAIN  ',
    iataCode: 'ESP',
    aliases: ['spain', 'barcelona', 'madrid', 'seville', 'mallorca', 'ibiza', 'san sebastian', 'granada', 'marbella'],
    routeSubtitle: 'Madrid · Seville · Barcelona · Mallorca',
    styleToken15: 'CULTURE + TAPAS',
    styleLabel: 'Culture + Tapas',
    styleSubcopy: 'Architectural landmarks, private flamenco, Balearic coast',
    photoSlug: 'portugal',
    tagVariant: 'gold',
    endCapIcon: 'palm',
  },
  {
    displayName: 'Thailand',
    boardToken7: 'THAILND',
    iataCode: 'THA',
    aliases: ['thailand', 'bangkok', 'phuket', 'chiang mai', 'koh samui', 'krabi'],
    routeSubtitle: 'Bangkok · Chiang Mai · Koh Samui',
    styleToken15: 'TEMPLE + ISLAND',
    styleLabel: 'Temple + Island',
    styleSubcopy: 'Chao Phraya river suites, northern sanctuaries, Andaman villas',
    photoSlug: 'bali',
    tagVariant: 'gold',
    endCapIcon: 'palm',
  },
  {
    displayName: 'Singapore',
    boardToken7: 'SINGAPR',
    iataCode: 'SGP',
    aliases: ['singapore', 'marina bay', 'sentosa'],
    routeSubtitle: 'Marina Bay · Dempsey Hill · Sentosa Cove',
    styleToken15: 'URBAN + CULINRY',
    styleLabel: 'Urban + Culinary',
    styleSubcopy: 'Botanical gardens, Michelin dining, heritage conservation hotels',
    photoSlug: 'dubai',
    tagVariant: 'gold',
    endCapIcon: 'palm',
  },
  {
    displayName: 'Egypt',
    boardToken7: 'EGYPT  ',
    iataCode: 'EGY',
    aliases: ['egypt', 'cairo', 'luxor', 'aswan', 'nile', 'giza'],
    routeSubtitle: 'Cairo · Luxor · Private Nile Dahabiya · Aswan',
    styleToken15: 'NILE + ANTIQUTY',
    styleLabel: 'Nile + Antiquity',
    styleSubcopy: 'Private Egyptologist access, Nile dahabiya charter, historic palaces',
    photoSlug: 'dubai',
    tagVariant: 'terracotta',
    endCapIcon: 'dunes',
  },
  {
    displayName: 'South Africa',
    boardToken7: 'S AFRCA',
    iataCode: 'ZAF',
    aliases: ['south africa', 'cape town', 'kruger', 'sabi sands', 'franschhoek', 'stellenbosch'],
    routeSubtitle: 'Cape Town · Franschhoek Winelands · Sabi Sands',
    styleToken15: 'SAFARI + WINE  ',
    styleLabel: 'Safari + Wine',
    styleSubcopy: 'Cape peninsula estates, winelands manor, Big Five private reserve',
    photoSlug: 'kenya',
    tagVariant: 'terracotta',
    endCapIcon: 'dunes',
  },
  {
    displayName: 'Costa Rica',
    boardToken7: 'COSTA R',
    iataCode: 'CRI',
    aliases: ['costa rica', 'papagayo', 'arenal', 'monteverde', 'osa peninsula', 'nosara'],
    routeSubtitle: 'Arenal Volcano · Cloud Forest · Peninsula Papagayo',
    styleToken15: 'RAINFRST + COAS',
    styleLabel: 'Rainforest + Coast',
    styleSubcopy: 'Thermal springs, canopy wildlife guides, Pacific cliff villas',
    photoSlug: 'bali',
    tagVariant: 'gold',
    endCapIcon: 'palm',
  },
  {
    displayName: 'New Zealand',
    boardToken7: 'NEW ZLD',
    iataCode: 'NZL',
    aliases: ['new zealand', 'queenstown', 'auckland', 'milford sound', 'fiordland', 'waiheke', 'wanaka'],
    routeSubtitle: 'Waiheke Island · Rotorua · Queenstown · Milford Sound',
    styleToken15: 'ALPINE + FJORD ',
    styleLabel: 'Alpine + Fjord',
    styleSubcopy: 'Helicopter glacier landings, luxury lodges, Waiheke vineyards',
    photoSlug: 'patagonia',
    tagVariant: 'cream',
    endCapIcon: 'torii',
  },
  {
    displayName: 'Mexico',
    boardToken7: 'MEXICO ',
    iataCode: 'MEX',
    aliases: ['mexico', 'oaxaca', 'mexico city', 'cdmx', 'tulum', 'los cabos', 'cabo', 'san miguel', 'riviera maya'],
    routeSubtitle: 'Mexico City · Oaxaca · Los Cabos',
    styleToken15: 'CULTURE + COAST',
    styleLabel: 'Culture + Coast',
    styleSubcopy: 'Contemporary art, mezcal palenques, Sea of Cortez villas',
    photoSlug: 'peru',
    tagVariant: 'terracotta',
    endCapIcon: 'palm',
  },
  {
    displayName: 'Vietnam',
    boardToken7: 'VIETNAM',
    iataCode: 'VNM',
    aliases: ['vietnam', 'hanoi', 'ha long', 'hoi an', 'saigon', 'ho chi minh', 'con dao'],
    routeSubtitle: 'Hanoi · Ha Long Bay · Hoi An · Con Dao',
    styleToken15: 'HERITGE + COAST',
    styleLabel: 'Heritage + Coast',
    styleSubcopy: 'Private junk charter, lantern towns, coastal sanctuary villas',
    photoSlug: 'bali',
    tagVariant: 'gold',
    endCapIcon: 'palm',
  },
  {
    displayName: 'India',
    boardToken7: 'INDIA  ',
    iataCode: 'IND',
    aliases: ['india', 'rajasthan', 'jaipur', 'udaipur', 'jodhpur', 'delhi', 'agra', 'kerala', 'goa', 'mumbai'],
    routeSubtitle: 'Delhi · Agra · Jaipur · Udaipur',
    styleToken15: 'PALACE + CULTUR',
    styleLabel: 'Palace + Culture',
    styleSubcopy: 'Royal lake palaces, private forts, curated artisan encounters',
    photoSlug: 'dubai',
    tagVariant: 'terracotta',
    endCapIcon: 'dunes',
  },
  {
    displayName: 'Croatia',
    boardToken7: 'CROATIA',
    iataCode: 'HRV',
    aliases: ['croatia', 'dubrovnik', 'split', 'hvar', 'korcula', 'rovinj', 'istria'],
    routeSubtitle: 'Split · Hvar · Korčula · Dubrovnik',
    styleToken15: 'ADRIATC + YACHT',
    styleLabel: 'Adriatic + Yacht',
    styleSubcopy: 'Dalmatian island yacht charter, walled cities, coastal wineries',
    photoSlug: 'greece',
    tagVariant: 'gold',
    endCapIcon: 'palm',
  },
  {
    displayName: 'Turkey',
    boardToken7: 'TURKEY ',
    iataCode: 'TUR',
    aliases: ['turkey', 'turkiye', 'istanbul', 'cappadocia', 'bodrum'],
    routeSubtitle: 'Istanbul · Cappadocia · Bodrum Peninsula',
    styleToken15: 'BOSPHRS + COAST',
    styleLabel: 'Bosphorus + Coast',
    styleSubcopy: 'Bosphorus palaces, cave suites at sunrise, Aegean gulet',
    photoSlug: 'greece',
    tagVariant: 'terracotta',
    endCapIcon: 'dunes',
  },
  {
    displayName: 'Australia',
    boardToken7: 'AUSTRLA',
    iataCode: 'AUS',
    aliases: ['australia', 'sydney', 'melbourne', 'uluru', 'great barrier reef', 'whitsundays', 'tasmania'],
    routeSubtitle: 'Sydney · Uluru · Great Barrier Reef',
    styleToken15: 'REEF + OUTBACK ',
    styleLabel: 'Reef + Outback',
    styleSubcopy: 'Harbor opera house views, desert luxury camp, private reef island',
    photoSlug: 'maldives',
    tagVariant: 'gold',
    endCapIcon: 'palm',
  },
  {
    displayName: 'Tanzania',
    boardToken7: 'TANZANA',
    iataCode: 'TZA',
    aliases: ['tanzania', 'serengeti', 'ngorongoro', 'zanzibar', 'kilimanjaro'],
    routeSubtitle: 'Ngorongoro Crater · Serengeti · Zanzibar',
    styleToken15: 'SAFARI + ISLAND',
    styleLabel: 'Safari + Island',
    styleSubcopy: 'Private crater rim lodge, mobile migration camp, spice island',
    photoSlug: 'kenya',
    tagVariant: 'terracotta',
    endCapIcon: 'dunes',
  },
];

const MONTH_FULL_NAMES: Record<string, string> = {
  JAN: 'January',
  FEB: 'February',
  MAR: 'March',
  APR: 'April',
  MAY: 'May',
  JUN: 'June',
  JUL: 'July',
  AUG: 'August',
  SEP: 'September',
  OCT: 'October',
  NOV: 'November',
  DEC: 'December',
};

const STOPWORDS_FOR_DESTINATION_EXTRACTION = new Set([
  'a', 'an', 'the', 'and', 'or', 'but', 'for', 'to', 'in', 'on', 'at', 'by', 'with', 'from', 'of',
  'into', 'onto', 'upon', 'around', 'about', 'roughly', 'approx', 'approximately', 'near', 'towards',
  'during', 'between', 'through', 'over', 'under', 'after', 'before', 'next', 'this', 'coming',
  'early', 'mid', 'late', 'end', 'start', 'beginning', 'sometime', 'maybe', 'flexible', 'open',
  'year', 'years', 'month', 'months', 'week', 'weeks', 'day', 'days', 'night', 'nights',
  'spring', 'summer', 'autumn', 'fall', 'winter', 'season', 'break', 'holiday', 'holidays',
  'vacation', 'trip', 'tour', 'journey', 'getaway', 'escape', 'honeymoon', 'anniversary', 'birthday',
  'traveler', 'travelers', 'traveller', 'travellers', 'people', 'person', 'guests', 'guest',
  'adults', 'adult', 'kids', 'children', 'family', 'couple', 'friends', 'group', 'party', 'pax',
  'we', 'us', 'our', 'my', 'me', 'i', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight',
  'want', 'wants', 'looking', 'planning', 'thinking', 'hoping', 'interested', 'like', 'love',
  'would', 'could', 'can', 'please', 'help', 'book', 'plan', 'explore', 'visit', 'visiting', 'going',
  'heading', 'taking', 'take', 'do', 'doing', 'hi', 'hey', 'hello', 'options', 'dates', 'date',
  'jan', 'january', 'feb', 'february', 'mar', 'march', 'apr', 'april', 'may', 'jun', 'june',
  'jul', 'july', 'aug', 'august', 'sep', 'sept', 'september', 'oct', 'october', 'nov', 'november',
  'dec', 'december', 'luxury', 'private', 'custom', 'bespoke', 'guided', 'hotel', 'hotels', 'villa',
  'villas', 'resort', 'resorts', 'safari', 'beach', 'coast', 'coastal', 'culture', 'food', 'wine',
]);

/**
 * Picks the next destination from the 15-destination catalog (either sequentially or randomly,
 * avoiding repeating the currently active destination).
 */
export function pickNextCatalogDestination(
  currentDisplayName: string,
  mode: 'sequential' | 'random' = 'random'
): DynamicDestinationCatalogEntry {
  const lower = currentDisplayName.trim().toLowerCase();
  const currentIndex = DESTINATION_CATALOG_REGISTRY.findIndex(
    (entry) => entry.slug === lower || entry.displayName.toLowerCase() === lower
  );
  if (mode === 'sequential') {
    const nextIdx = (currentIndex + 1) % DESTINATION_CATALOG_REGISTRY.length;
    return DESTINATION_CATALOG_REGISTRY[nextIdx];
  }
  const candidates = DESTINATION_CATALOG_REGISTRY.filter(
    (_, idx) => idx !== currentIndex
  );
  const randomIdx = Math.floor(Math.random() * candidates.length);
  return candidates[randomIdx] ?? DESTINATION_CATALOG_REGISTRY[0];
}

export interface ResolveDynamicInquiryOptions {
  /**
   * When true, dynamically varies traveler count, trip duration, and target month
   * from the destination's realistic candidate pools and synchronizes those numbers
   * across all 5 Solari rows, Frame 2 voice transcript, Frame 3 chat thread, and Brief Drawer.
   */
  randomizeNumbers?: boolean;
  /** Optional deterministic seed for reproducible variation selection */
  variationSeed?: number;
}

function pickFromPool<T>(pool: readonly T[], fallback: T, seed?: number): T {
  if (!pool.length) return fallback;
  if (typeof seed === 'number') {
    const idx = Math.abs(Math.floor(seed)) % pool.length;
    return pool[idx] ?? fallback;
  }
  const idx = Math.floor(Math.random() * pool.length);
  return pool[idx] ?? fallback;
}

/**
 * Extracts a clean destination name from an arbitrary natural-language sentence
 * when no catalog or global gazetteer entry matched directly.
 */
function extractUnknownDestinationFromText(raw: string): string {
  // 1. Check phrases immediately following location prepositions ("to X", "in X", "for X", "visit X")
  const prepRegex = /\b(?:to|in|for|visit|visiting|towards|at)\s+([a-zA-Z][a-zA-Z\s-]{1,28})/gi;
  let match: RegExpExecArray | null;
  while ((match = prepRegex.exec(raw)) !== null) {
    const words = match[1]
      .trim()
      .split(/[\s,.;!?]+/)
      .filter(Boolean);
    const kept: string[] = [];
    for (const w of words) {
      const clean = w.replace(/[^a-zA-Z-]/g, '');
      if (!clean || clean.length < 2) break;
      if (STOPWORDS_FOR_DESTINATION_EXTRACTION.has(clean.toLowerCase())) {
        if (kept.length > 0) break;
        continue;
      }
      kept.push(clean.charAt(0).toUpperCase() + clean.slice(1).toLowerCase());
      if (kept.length >= 2) break;
    }
    if (kept.length > 0) {
      return kept.join(' ');
    }
  }

  // 2. Fallback: scan all alphabetic tokens and pick the first non-stopword
  const tokens = raw.split(/[\s,.;!?/]+/).filter(Boolean);
  for (const tok of tokens) {
    const clean = tok.replace(/[^a-zA-Z-]/g, '');
    if (clean.length < 3) continue;
    if (!STOPWORDS_FOR_DESTINATION_EXTRACTION.has(clean.toLowerCase())) {
      return clean.charAt(0).toUpperCase() + clean.slice(1).toLowerCase();
    }
  }
  return 'Custom';
}

/**
 * Dynamically compiles any free-text client inquiry or destination name into a
 * structured `DepartureInquiryFixture` for the 5-row mechanical split-flap board.
 * Supports both deterministic preset resolution and dynamic randomized number variations.
 */
export function resolveDynamicInquiryFixture(
  rawInput: string,
  options?: ResolveDynamicInquiryOptions
): DepartureInquiryFixture {
  const trimmed = rawInput.trim();
  const lower = trimmed.toLowerCase();
  const randomize = Boolean(options?.randomizeNumbers);

  // Fast-path exact match for the 3 reference showcase presets when not randomizing numbers
  if (!randomize) {
    if (lower === 'italy') return DEPARTURE_INQUIRIES.italy;
    if (lower === 'japan') return DEPARTURE_INQUIRIES.japan;
    if (lower === 'morocco') return DEPARTURE_INQUIRIES.morocco;
  }

  // 1. Match against the 15-destination primary catalog (slug, displayName, or city/region aliases)
  const matchedEntry =
    DESTINATION_CATALOG_REGISTRY.find((entry) => {
      if (lower === entry.slug || lower === entry.displayName.toLowerCase()) return true;
      const slugRegex = new RegExp(`\\b${entry.slug.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\b`, 'i');
      const nameRegex = new RegExp(`\\b${entry.displayName.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\b`, 'i');
      if (slugRegex.test(lower) || nameRegex.test(lower)) return true;
      return entry.aliases?.some((alias) => {
        const aliasRegex = new RegExp(`\\b${alias.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\b`, 'i');
        return aliasRegex.test(lower);
      }) ?? false;
    }) ?? null;

  // 2. Check secondary global gazetteer if not in the 15 primary catalog entries
  const matchedGlobal =
    !matchedEntry
      ? GLOBAL_DESTINATION_FALLBACKS.find((g) =>
          g.aliases.some((alias) => {
            const aliasRegex = new RegExp(`\\b${alias.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\b`, 'i');
            return aliasRegex.test(lower);
          })
        ) ?? null
      : null;

  const isBareDestinationLookup =
    matchedEntry !== null &&
    (lower === matchedEntry.slug || lower === matchedEntry.displayName.toLowerCase());

  // 3. Resolve Destination Display Name, 7-Char Board Token, IATA Code, & Supporting Visual Assets
  let displayName = matchedEntry?.displayName ?? matchedGlobal?.displayName ?? 'Custom';
  let boardToken7 = matchedEntry?.boardToken7 ?? matchedGlobal?.boardToken7 ?? 'CUSTOM ';
  let iataCode = matchedEntry?.iataCode ?? matchedGlobal?.iataCode ?? 'TRP';
  let destinationPhotoUrl =
    matchedEntry?.destinationPhotoUrl ??
    (matchedGlobal ? `/landing/departure-board/catalog/photo-${matchedGlobal.photoSlug}-1.png` : '/landing/departure-board/catalog/photo-dubai-1.png');
  let destinationPhotoAlt =
    matchedEntry?.destinationPhotoAlt ?? `${displayName} landmark destination view`;
  let durationPhotoUrl =
    matchedEntry?.durationPhotoUrl ??
    (matchedGlobal ? `/landing/departure-board/catalog/photo-${matchedGlobal.photoSlug}-2.png` : '/landing/departure-board/catalog/photo-dubai-2.png');
  let durationPhotoAlt =
    matchedEntry?.durationPhotoAlt ?? `${displayName} curated itinerary experience`;
  let tagImageUrl =
    matchedEntry?.tagImageUrl ??
    (matchedGlobal?.tagVariant === 'cream'
      ? '/landing/departure-board/tag-blank-cream.png'
      : matchedGlobal?.tagVariant === 'terracotta'
        ? '/landing/departure-board/tag-blank-terracotta.png'
        : '/landing/departure-board/tag-blank-gold.png');

  if (!matchedEntry && !matchedGlobal) {
    displayName = extractUnknownDestinationFromText(trimmed);
    boardToken7 = displayName.toUpperCase().replace(/[^A-Z]/g, '').slice(0, 7).padEnd(7, ' ');
    const consonants = displayName.toUpperCase().replace(/[^A-Z]/g, '');
    iataCode = (consonants.slice(0, 3) || 'TRP').padEnd(3, 'X');
    destinationPhotoAlt = `${displayName} destination view`;
    durationPhotoAlt = `${displayName} bespoke itinerary`;
  }

  // 4. Extract or Randomize Traveler Count & Epistemic Basis
  const explicitCountMatch = lower.match(
    /\b(\d{1,2})\s*(?:travelers?|travellers?|people|guests?|adults?|of us|pax|friends|persons?)\b/
  );
  const familyMatch = lower.match(/\bfamily of\s*(\d{1,2})\b/);
  const groupMatch = lower.match(/\b(?:group|party) of\s*(\d{1,2})\b/);
  const wordCountMap: Record<string, number> = {
    two: 2,
    three: 3,
    four: 4,
    five: 5,
    six: 6,
    seven: 7,
    eight: 8,
  };
  const wordTravelerMatch = lower.match(
    /\b(two|three|four|five|six|seven|eight)\s+(?:of us|travelers?|travellers?|people|guests?|adults?|friends)\b/
  );
  const isCouple = /\b(?:couple|honeymoon|anniversary|two of us|2 of us|wife and i|husband and i|partner and i|my partner)\b/.test(lower);
  const isSolo = /\b(?:solo|just me|1 traveler|one traveler)\b/.test(lower);

  let travelersCount = matchedEntry?.defaultTravelersCount ?? 2;
  let travelersBasis: EpistemicBasis = 'inferred';
  let travelersSubtitle = 'Party size inferred from message context';

  if (explicitCountMatch) {
    travelersCount = Math.max(1, Math.min(24, Number.parseInt(explicitCountMatch[1], 10)));
    travelersBasis = 'explicit';
    travelersSubtitle = `${travelersCount} ${travelersCount === 1 ? 'traveler' : 'travelers'} explicitly stated`;
  } else if (familyMatch) {
    travelersCount = Math.max(2, Math.min(24, Number.parseInt(familyMatch[1], 10)));
    travelersBasis = 'explicit';
    travelersSubtitle = `Family group (${travelersCount} travelers)`;
  } else if (groupMatch) {
    travelersCount = Math.max(2, Math.min(24, Number.parseInt(groupMatch[1], 10)));
    travelersBasis = 'explicit';
    travelersSubtitle = `Group party (${travelersCount} travelers)`;
  } else if (wordTravelerMatch) {
    travelersCount = wordCountMap[wordTravelerMatch[1]] ?? 2;
    travelersBasis = 'explicit';
    travelersSubtitle = `${travelersCount} travelers explicitly stated`;
  } else if (isSolo) {
    travelersCount = 1;
    travelersBasis = 'explicit';
    travelersSubtitle = 'Solo traveler';
  } else if (isCouple) {
    travelersCount = 2;
    travelersBasis = 'inferred';
    travelersSubtitle = '1 couple (inferred from inquiry)';
  } else if (matchedEntry) {
    travelersCount = randomize
      ? pickFromPool(matchedEntry.travelersOptions ?? [2, 4, 6], matchedEntry.defaultTravelersCount, options?.variationSeed)
      : matchedEntry.defaultTravelersCount;
    travelersBasis = isBareDestinationLookup ? 'explicit' : 'inferred';
    travelersSubtitle = isBareDestinationLookup
      ? `${travelersCount} travelers (${matchedEntry.displayName} inquiry)`
      : `${travelersCount} travelers (recommended party baseline)`;
  }

  const travelersCells =
    travelersCount === 1 ? '1 TRAVELER ' : `${travelersCount} TRAVELERS`.padEnd(11, ' ').slice(0, 11);

  // 5. Extract or Randomize Duration in Days
  const daysMatch = lower.match(/\b(\d{1,2})\s*(?:days?|nights?)\b/);
  const weeksMatch = lower.match(/\b(\d)\s*weeks?\b/);
  const hasExplicitDuration = Boolean(daysMatch || weeksMatch);

  const durationDays = daysMatch
    ? Math.max(2, Math.min(60, Number.parseInt(daysMatch[1], 10)))
    : weeksMatch
      ? Number.parseInt(weeksMatch[1], 10) * 7
      : matchedEntry
        ? randomize
          ? pickFromPool(
              matchedEntry.durationOptions ?? [7, 10, 12, 14],
              matchedEntry.defaultDurationDays,
              typeof options?.variationSeed === 'number' ? options.variationSeed + 3 : undefined
            )
          : matchedEntry.defaultDurationDays
        : 8;

  const durationBasis: EpistemicBasis =
    hasExplicitDuration || isBareDestinationLookup ? 'explicit' : 'inferred';

  const durationCells =
    durationDays < 10 ? `${durationDays}  DAYS` : `${durationDays} DAYS`.padEnd(7, ' ').slice(0, 7);

  // 6. Extract or Randomize Target Month / Relative Year Window
  const monthRegex =
    /\b(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\b/i;
  const seasonMap: Record<string, string> = {
    spring: 'APR',
    summer: 'JUN',
    autumn: 'OCT',
    fall: 'OCT',
    winter: 'JAN',
  };
  const seasonMatch = lower.match(/\b(spring|summer|autumn|fall|winter)\b/);
  const monthHit = trimmed.match(monthRegex);

  const monthAbbrev = monthHit
    ? monthHit[1].slice(0, 3).toUpperCase()
    : seasonMatch
      ? seasonMap[seasonMatch[1].toLowerCase()] ?? 'JUN'
      : matchedEntry
        ? randomize
          ? pickFromPool(
              matchedEntry.monthOptions ?? ['APR', 'JUN', 'SEP', 'OCT'],
              matchedEntry.defaultMonthAbbrev,
              typeof options?.variationSeed === 'number' ? options.variationSeed + 7 : undefined
            )
          : matchedEntry.defaultMonthAbbrev
        : 'JUN';

  const monthFullName = MONTH_FULL_NAMES[monthAbbrev] ?? monthAbbrev;
  const hasNextYear = /\bnext year\b/i.test(lower);
  const yearMatch = lower.match(/\b(202\d)\b/);
  const yearSuffix = yearMatch ? ` ${yearMatch[1]}` : hasNextYear ? ' next year' : '';
  const scanningStr = `${monthAbbrev} 10-2? `;

  // 7. Extract or Resolve Trip Style
  const archetypeId = matchedEntry?.visualArchetype ?? 'italy';
  const baseCase = DEPARTURE_BOARD_CASES[archetypeId];
  let styleToken15 =
    matchedEntry?.defaultStyleToken15 ?? matchedGlobal?.styleToken15 ?? 'CULTURE + COAST';
  let styleLabel =
    matchedEntry?.defaultStyleLabel ?? matchedGlobal?.styleLabel ?? 'Culture + Luxury';
  let styleSub =
    matchedEntry?.defaultSubcopy ??
    matchedGlobal?.styleSubcopy ??
    'Private guides, boutique stays, curated pacing';

  if (!isBareDestinationLookup) {
    if (/\b(?:honeymoon|romance|romantic|anniversary)\b/.test(lower)) {
      styleToken15 = 'ROMANCE + VILLA';
      styleLabel = 'Romance + Villa';
    } else if (/\b(?:safari|wildlife|game drive)\b/.test(lower)) {
      styleToken15 = 'SAFARI + LODGE ';
      styleLabel = 'Safari + Lodge';
    } else if (/\b(?:yacht|catamaran|sailing|island)\b/.test(lower)) {
      styleToken15 = 'ISLAND + YACHT ';
      styleLabel = 'Island + Yacht';
    } else if (/\b(?:ski|alpine|snow|chalet)\b/.test(lower)) {
      styleToken15 = 'ALPINE + CHALET';
      styleLabel = 'Alpine + Chalet';
    } else if (/\b(?:food|culinary|wine|gastronomy|michelin)\b/.test(lower)) {
      styleToken15 = 'CULTURE + WINE ';
      styleLabel = 'Culture + Wine';
    }
  }

  const routeSubtitle =
    matchedEntry?.sampleRouteSubtitle ??
    matchedGlobal?.routeSubtitle ??
    `${displayName} Private Signature Route`;

  // 8. Build Synchronized Voice Quote (ensuring all 5 workflow tokens highlight in Frame 2 even when numbers randomize or user enters shorthand)
  const synchronizedVoiceQuote =
    isBareDestinationLookup && !randomize && matchedEntry
      ? matchedEntry.sampleVoiceQuote
      : !isBareDestinationLookup && trimmed.length > 0
        ? `Hi! Looking at ${displayName} for ${travelersCount} ${
            travelersCount === 1 ? 'traveler' : 'travelers'
          } for about ${durationDays} days in ${monthFullName}${yearSuffix} — ${styleSub.toLowerCase()}, exact dates still open.`
        : `Hi! Looking to take ${
            travelersCount === 2 ? '2 travelers' : `a group of ${travelersCount}`
          } to ${displayName} for ${durationDays} days in ${monthFullName} — ${styleSub.toLowerCase()}, exact dates still open.`;

  const userEvidenceQuote =
    !isBareDestinationLookup && trimmed.length > 0 ? trimmed : synchronizedVoiceQuote;

  const dynamicCase: DepartureBoardCase = {
    ...baseCase,
    id: archetypeId,
    iataCode,
    tagImageUrl,
    destinationPhotoUrl,
    destinationPhotoAlt,
    durationPhotoUrl,
    durationPhotoAlt,
    dockTitle: displayName,
    dockSubtitle: styleLabel,
    destinationCells: boardToken7,
    travelersCells,
    durationCells,
    datesScanningCells: scanningStr,
    datesNeedsConfirmation: true,
    tripStyleCells: styleToken15,
    styleEndCapIcon:
      matchedEntry?.styleEndCapIcon ?? matchedGlobal?.endCapIcon ?? baseCase.styleEndCapIcon,
    incomingVoiceCard: {
      timestamp: '11:05 AM',
      durationLabel: '0:22',
      quote: `“${synchronizedVoiceQuote}”`,
      waveformBars: baseCase.incomingVoiceCard.waveformBars,
    },
    chatThread: [
      {
        id: 'dyn-1',
        time: '11:02 AM',
        segments: [
          { text: 'Exploring a trip to ' },
          { text: displayName, color: 'yellow', targetRow: 0 },
          { text: ' for ' },
          {
            text: `${travelersCount} ${travelersCount === 1 ? 'traveler' : 'travelers'}`,
            color: 'blue',
            targetRow: 1,
          },
          { text: ` (${routeSubtitle}).` },
        ],
      },
      {
        id: 'dyn-2',
        time: '11:04 AM',
        segments: [
          { text: hasExplicitDuration || isBareDestinationLookup ? 'Planning for ' : 'Paced around ' },
          { text: `${durationDays} days`, color: 'green', targetRow: 2 },
          { text: ` in ${monthFullName}${yearSuffix} — exact departure dates still flexible.` },
        ],
      },
      {
        id: 'dyn-3',
        time: '11:05 AM',
        segments: [
          { text: 'Priority on ' },
          { text: styleLabel.toLowerCase(), color: 'yellow', targetRow: 4 },
          { text: ` (${styleSub.toLowerCase()}).` },
        ],
      },
    ],
    briefItems: [
      {
        rowIndex: 0,
        label: 'Destination',
        value: displayName,
        subtitle: routeSubtitle,
        basis: 'explicit',
        sourceQuote: `“${userEvidenceQuote}”`,
        thumbUrl: destinationPhotoUrl,
      },
      {
        rowIndex: 1,
        label: 'Travelers',
        value: `${travelersCount} ${travelersCount === 1 ? 'traveler' : 'travelers'}`,
        subtitle: travelersSubtitle,
        basis: travelersBasis,
        sourceQuote: `“${travelersCount} ${travelersCount === 1 ? 'traveler' : 'travelers'}”`,
      },
      {
        rowIndex: 2,
        label: 'Duration',
        value: `${durationDays} days`,
        subtitle:
          durationBasis === 'inferred'
            ? `Recommended ${durationDays}-day pace (inferred for ${displayName})`
            : `${durationDays}-day itinerary window`,
        basis: durationBasis,
        sourceQuote:
          durationBasis === 'inferred'
            ? `“Recommended ${durationDays}-day route pacing for ${displayName}”`
            : `“${durationDays} days”`,
      },
      {
        rowIndex: 3,
        label: 'Dates',
        value: 'Needs confirmation',
        basis: 'unknown',
        needsConfirmation: true,
        sourceQuote: `“Target window (${monthFullName}${yearSuffix}) — exact dates not locked yet.”`,
        advisorFollowUp:
          matchedEntry?.seasonalFollowUp ??
          `Confirm exact ${monthFullName}${yearSuffix} departure window and flight gateway before holding ${displayName} inventory.`,
      },
      {
        rowIndex: 4,
        label: 'Trip style',
        value: styleLabel,
        subtitle: styleSub,
        basis: !isBareDestinationLookup && trimmed.length > 0 ? 'inferred' : 'explicit',
        sourceQuote: `“${styleLabel} — ${styleSub}”`,
        thumbUrl: durationPhotoUrl,
      },
    ],
  };

  return adaptCaseToFixture(dynamicCase);
}



