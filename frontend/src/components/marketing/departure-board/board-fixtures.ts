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
  iataCode: 'ITA' | 'JPN' | 'MAR';
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
 * The 7 two-line yellow cells for Row 4 when `datesNeedsConfirmation === true`:
 * Top line:    N  | E  | E  | D  |    |    |
 * Bottom line: CO | NF | IR | MA | TI | ON |
 * Matches Frame 1, Frame 3, and Frame 4 typography & cell breakdown.
 */
export const NEED_CONFIRMATION_CELLS: Array<{ top: string; bottom: string }> = [
  { top: 'N', bottom: 'CO' },
  { top: 'E', bottom: 'NF' },
  { top: 'E', bottom: 'IR' },
  { top: 'D', bottom: 'MA' },
  { top: '', bottom: 'TI' },
  { top: '', bottom: 'ON' },
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
  tagCode: 'ITA' | 'JPN' | 'MAR';
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
      { topText: 'V', variant: 'blurred_flip' },
      { topText: 'A', variant: 'blurred_flip' },
      { topText: 'I', variant: 'cream' },
      { topText: 'T', variant: 'cream' },
      { topText: 'A', variant: 'cream' },
      { topText: 'L', variant: 'cream' },
      { topText: 'Y', variant: 'cream' },
    ];
  }
  return stringToCreamCells(destStr, 7);
}

function buildTravelersScanningCells(travStr: string): FlapCellSpec[] {
  const base = stringToCreamCells(travStr, 11);
  if (base.length > 1 && base[1].topText === ' ') {
    base[1] = { topText: 'A', variant: 'blurred_flip' };
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
        cells: stringToCreamCells(c.destinationCells, 7),
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
        cells: stringToCreamCells(c.travelersCells, 11),
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
        cells: stringToCreamCells(c.durationCells, 7),
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

