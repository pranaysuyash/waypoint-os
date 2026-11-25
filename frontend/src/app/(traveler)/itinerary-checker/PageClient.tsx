'use client';

import { getItineraryFeasibilityEvidence, getItineraryFeasibilityFindings } from '@/lib/itinerary-feasibility';
import Link from 'next/link';
import { useEffect, useState, useRef, useReducer, type CSSProperties, type RefObject, DragEvent } from 'react';
import gsap from 'gsap';
import { api } from '@/lib/api-client';
import { safeWriteClipboardText } from '@/lib/clipboard';
import { formatPacketValue, isLegacyBookingDefault } from '@/lib/label-maps';
import type { RunStatusResponse } from '@/types/spine';
import {
  WedgeVisualShowcase,
  WEDGE_SCENARIO_LIST,
  WEDGE_SCENARIO_CATALOG,
  type WedgeScenarioBundle,
  type WedgeScenarioKey,
} from '@/components/traveler/WedgeVisualShowcase';
import {
  Activity, ArrowRight, Check, Clock, DollarSign,
  Camera, Compass, FileCheck, Globe, MapPin, Pause, Play, PlaneTakeoff, Route,
  Shield, Sparkles, Star, SunMedium, Ticket, Upload,
} from 'lucide-react';

// ── Design tokens ─────────────────────────────────────────────────────────────
const T = {
  canvas:   '#07090b',
  surface:  '#0d1117',
  elevated: '#161b22',
  input:    '#111318',
  t1: '#e6edf3',
  t2: '#8b949e',
  t3: 'var(--text-muted)',
  t4: '#484f58',
  blue:   '#58a6ff',
  cyan:   '#39d0d8',
  amber:  '#d29922',
  green:  '#3fb950',
  red:    '#f85149',
  purple: '#a371f7',
  b0: '#21262d',
  b1: '#30363d',
  fDisplay: "var(--font-sora), 'Outfit', system-ui, sans-serif",
  fBody:    "var(--font-rubik), system-ui, sans-serif",
  fMono:    "'JetBrains Mono', monospace",
};

const S = {
  header: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '14px 32px',
    borderBottom: `1px solid ${T.b0}`,
    background: 'rgba(10,13,17,0.9)',
    backdropFilter: 'blur(8px)',
    position: 'sticky',
    top: 0,
    zIndex: 50,
    flexShrink: 0,
  },
  logoMark: {
    width: 28,
    height: 28,
    borderRadius: 8,
    background: 'linear-gradient(135deg, #2563eb, #39d0d8)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    color: 'white',
    flexShrink: 0,
  },
  agencyPillLink: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: 6,
    height: 34,
    padding: '0 14px',
    borderRadius: 999,
    fontSize: 12,
    fontWeight: 600,
    fontFamily: T.fBody,
    background: 'rgba(15,17,21,0.72)',
    color: '#c9d1d9',
    border: '1px solid rgba(168,179,193,0.14)',
    textDecoration: 'none',
  },
  uploadGlowFrame: {
    position: 'absolute',
    inset: '-16px -16px 0',
    pointerEvents: 'none',
    borderRadius: 24,
    overflow: 'hidden',
  },
  uploadRing: {
    position: 'absolute',
    right: -40,
    top: -36,
    width: 180,
    height: 180,
    borderRadius: '50%',
    background: 'conic-gradient(from 0deg, rgba(122,185,255,0.14), rgba(57,208,216,0.04), rgba(163,113,247,0.14), rgba(57,208,216,0.04), rgba(122,185,255,0.14))',
    filter: 'blur(1px)',
    opacity: 0.8,
  },
  uploadScanline: {
    position: 'absolute',
    left: 18,
    right: 18,
    top: 18,
    height: 2,
    borderRadius: 999,
    background: 'linear-gradient(90deg, transparent, rgba(57,208,216,0.92), rgba(122,185,255,0.18), transparent)',
    boxShadow: '0 0 18px rgba(57,208,216,0.6)',
  },
  pasteTextarea: {
    width: '100%',
    minHeight: 180,
    padding: '16px 18px',
    background: 'none',
    border: 'none',
    resize: 'none',
    color: T.t1,
    fontSize: 13,
    fontFamily: T.fMono,
    lineHeight: 1.65,
    boxSizing: 'border-box',
  },
  uploadIconFrame: {
    width: 52,
    height: 52,
    borderRadius: 14,
    background: 'rgba(88,166,255,0.1)',
    border: '1px solid rgba(88,166,255,0.2)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    margin: '0 auto 14px',
    color: T.blue,
  },
  inlineError: {
    marginTop: 10,
    padding: '10px 12px',
    borderRadius: 10,
    border: '1px solid rgba(248,81,73,0.22)',
    background: 'rgba(248,81,73,0.08)',
    color: '#ffb4ae',
    fontSize: 12,
    lineHeight: 1.45,
  },
  previewCard: {
    position: 'relative',
    borderRadius: 28,
    padding: 18,
    background: 'linear-gradient(180deg, rgba(10,18,26,0.98), rgba(7,9,11,0.98))',
    border: '1px solid rgba(88,166,255,0.22)',
    boxShadow: '0 28px 80px rgba(0,0,0,0.42)',
    overflow: 'hidden',
  },
  previewBackground: {
    position: 'absolute',
    inset: 0,
    background:
      'radial-gradient(circle at 18% 18%, rgba(255,193,122,0.22) 0%, transparent 26%), radial-gradient(circle at 86% 8%, rgba(57,208,216,0.18) 0%, transparent 24%), linear-gradient(135deg, rgba(122,185,255,0.04) 0%, transparent 40%)',
    pointerEvents: 'none',
  },
  previewPlane: {
    position: 'absolute',
    right: 20,
    top: 18,
    color: '#d8eef0',
    transform: 'rotate(12deg)',
    filter: 'drop-shadow(0 8px 20px rgba(57,208,216,0.35))',
  },
  previewStamp: {
    padding: '5px 9px',
    borderRadius: 999,
    background: 'rgba(255,193,122,0.12)',
    border: '1px solid rgba(255,193,122,0.24)',
    color: '#ffd6a6',
    fontSize: 12,
    fontWeight: 700,
    textTransform: 'uppercase',
    letterSpacing: '0.08em',
  },
  pageBackdrop: {
    display: 'none',
  },
  heroSection: {
    position: 'relative',
    zIndex: 1,
    maxWidth: 1180,
    margin: '0 auto',
    padding: '44px clamp(16px, 4vw, 40px) 56px',
    alignItems: 'start',
  },
  amberKicker: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: 7,
    padding: '4px 10px',
    borderRadius: 6,
    marginBottom: 18,
    color: T.t2,
    fontSize: 11.5,
    letterSpacing: '0.1em',
    textTransform: 'uppercase',
    fontFamily: T.fMono,
    fontWeight: 600,
    border: `1px solid ${T.b1}`,
    background: T.surface,
  },
  heroOrbBlue: {
    position: 'absolute',
    inset: '-18px -20px auto auto',
    width: 220,
    height: 220,
    borderRadius: '50%',
    background: 'radial-gradient(circle, rgba(122,185,255,0.12) 0%, rgba(57,208,216,0.08) 28%, rgba(163,113,247,0.06) 44%, transparent 70%)',
    filter: 'blur(6px)',
    pointerEvents: 'none',
  },
  heroOrbGreen: {
    position: 'absolute',
    left: -18,
    bottom: 120,
    width: 120,
    height: 120,
    borderRadius: '50%',
    background: 'radial-gradient(circle, rgba(63,185,80,0.12) 0%, rgba(63,185,80,0.05) 34%, transparent 72%)',
    filter: 'blur(4px)',
    pointerEvents: 'none',
  },
  travelMomentsSection: {
    position: 'relative',
    zIndex: 1,
    borderTop: `1px solid ${T.b0}`,
    borderBottom: `1px solid ${T.b0}`,
    padding: '28px 40px',
    background: 'linear-gradient(180deg, rgba(8,12,16,0.92), rgba(9,13,19,0.98))',
  },
  travelMomentIcon: {
    width: 38,
    height: 38,
    borderRadius: 12,
    background: 'linear-gradient(135deg, rgba(122,185,255,0.18), rgba(57,208,216,0.12))',
    border: '1px solid rgba(57,208,216,0.18)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    color: T.cyan,
    flexShrink: 0,
  },
  sectionKicker: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: 6,
    fontSize: 12,
    fontWeight: 700,
    letterSpacing: '0.14em',
    textTransform: 'uppercase',
    color: T.cyan,
    marginBottom: 14,
  },
  resultsRoot: {
    background: T.canvas,
    minHeight: '100vh',
    display: 'flex',
    flexDirection: 'column',
    fontFamily: T.fBody,
    color: T.t1,
  },
  backButton: {
    background: 'none',
    border: 'none',
    cursor: 'pointer',
    fontSize: 12,
    color: T.t3,
    fontFamily: T.fBody,
    marginBottom: 20,
    display: 'flex',
    alignItems: 'center',
    gap: 5,
    padding: 0,
  },
  emailInputFrame: {
    flex: 1,
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    padding: '8px 11px',
    borderRadius: 8,
    background: T.input,
    border: `1px solid ${T.b1}`,
  },
  conversionCard: {
    padding: '20px 24px',
    borderRadius: 16,
    background: 'rgba(13,17,23,0.9)',
    border: `1px solid ${T.b0}`,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 24,
    flexWrap: 'wrap',
  },
  shareReportButton: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: 7,
    height: 34,
    padding: '0 14px',
    borderRadius: 999,
    fontSize: 12,
    fontWeight: 600,
    fontFamily: T.fBody,
    background: 'linear-gradient(180deg, rgba(13,23,33,0.8), rgba(10,18,26,0.8))',
    color: T.t1,
    border: '1px solid rgba(88,166,255,0.22)',
    cursor: 'pointer',
  },
  advisorLinkButton: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: 7,
    height: 34,
    padding: '0 14px',
    borderRadius: 999,
    fontSize: 12,
    fontWeight: 600,
    fontFamily: T.fBody,
    background: T.cyan,
    color: '#07090b',
    border: 'none',
    cursor: 'pointer',
    textDecoration: 'none',
  },
} satisfies Record<string, CSSProperties>;

const tabButtonStyle = (isActive: boolean): CSSProperties => ({
  flex: 1,
  padding: '7px 0',
  borderRadius: 7,
  border: 'none',
  cursor: 'pointer',
  fontSize: 12,
  fontWeight: isActive ? 600 : 400,
  background: isActive ? T.elevated : 'transparent',
  color: isActive ? T.t1 : T.t2,
  fontFamily: T.fBody,
  transition: 'color 150ms, background 150ms',
});

const primaryButtonStyle = (enabled: boolean, height = 34, padding = '0 14px'): CSSProperties => ({
  display: 'inline-flex',
  alignItems: 'center',
  gap: 7,
  height,
  padding,
  borderRadius: 999,
  fontSize: height > 40 ? 13 : 12,
  fontWeight: 600,
  fontFamily: T.fBody,
  background: enabled ? T.cyan : T.elevated,
  color: enabled ? '#07090b' : T.t3,
  border: 'none',
  cursor: enabled ? 'pointer' : 'not-allowed',
  transition: 'background 160ms, color 160ms',
});

const uploadDropZoneStyle = (dragging: boolean): CSSProperties => ({
  borderRadius: 14,
  border: `2px dashed ${dragging ? T.cyan : T.b1}`,
  background: dragging ? 'rgba(57,208,216,0.04)' : T.surface,
  padding: '36px 24px',
  minHeight: 477,
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  justifyContent: 'center',
  boxSizing: 'border-box',
  textAlign: 'center',
  cursor: 'pointer',
  transition: 'border-color 200ms, background 200ms',
});

const colorIconStyle = (color: string, size = 24, radius = 8): CSSProperties => ({
  width: size,
  height: size,
  borderRadius: radius,
  background: `${color}18`,
  border: `1px solid ${color}2e`,
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  color,
});

const sectionButtonStyle = (variant: 'primary' | 'secondary' = 'primary'): CSSProperties => ({
  display: 'inline-flex',
  alignItems: 'center',
  gap: 6,
  height: 32,
  padding: '0 14px',
  borderRadius: 999,
  fontSize: 12,
  fontWeight: 600,
  fontFamily: T.fBody,
  background: variant === 'primary' ? T.cyan : 'transparent',
  color: variant === 'primary' ? '#07090b' : T.t2,
  border: variant === 'primary' ? 'none' : `1px solid ${T.b1}`,
  cursor: 'pointer',
});

const severityCardStyle = (background: string, border: string): CSSProperties => ({
  padding: '14px 16px',
  borderRadius: 12,
  background,
  border: `1px solid ${border}`,
  display: 'grid',
  gridTemplateColumns: 'auto 1fr',
  gap: 12,
  alignItems: 'flex-start',
});

const severityBadgeStyle = (
  severity: keyof typeof sevBadgeTxt,
  compact = false,
): CSSProperties => ({
  display: 'inline-flex',
  alignItems: 'center',
  gap: compact ? 4 : undefined,
  padding: '2px 7px',
  borderRadius: 5,
  marginTop: 1,
  fontSize: 12,
  fontWeight: 700,
  fontFamily: T.fMono,
  textTransform: 'uppercase',
  letterSpacing: '0.04em',
  color: sevBadgeTxt[severity],
  background: sevBadgeBg[severity],
  border: `1px solid ${sevBadgeBdr[severity]}`,
  flexShrink: 0,
  whiteSpace: compact ? undefined : 'nowrap',
});

const revisionButtonStyle = (
  color: string,
  background: string,
  border: string,
): CSSProperties => ({
  height: 30,
  padding: '0 12px',
  borderRadius: 999,
  fontSize: 12,
  fontWeight: 600,
  fontFamily: T.fBody,
  background,
  color,
  border,
  cursor: 'pointer',
});

const TRAVEL_MOMENTS = [
  {
    icon: PlaneTakeoff,
    title: 'Map the route',
    body: 'Turn a messy draft into a readable trip path with the important stops highlighted.',
  },
  {
    icon: Compass,
    title: 'Catch friction',
    body: 'Spot timing slips, overpacked days, and travel friction before it becomes a bad day.',
  },
  {
    icon: Ticket,
    title: 'Share the brief',
    body: 'Bring the cleaner brief to your agent or use the upgrade notes yourself.',
  },
];

export interface AgencyBrandingContext {
  agency_id: string;
  slug?: string;
  display_name: string;
  blurb?: string;
  response_sla_hours?: number;
  places_covered?: string[];
  customer_types?: string[];
  services?: string[];
  languages?: string[];
}

// ── Header ────────────────────────────────────────────────────────────────────
function WedgeHeader({ agencyContext }: { agencyContext?: AgencyBrandingContext | null }) {
  if (agencyContext) {
    return (
      <header style={S.header} className="px-4 py-3 sm:px-8">
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={S.logoMark}>
            <MapPin size={14} />
          </div>
          <div>
            <div style={{ fontSize: 13, fontWeight: 700, color: T.t1, letterSpacing: '-0.01em', fontFamily: T.fBody }}>
              {agencyContext.display_name}
            </div>
            <div style={{ fontSize: 11, color: T.t3, lineHeight: 1.2, fontFamily: T.fBody }}>
              Client Travel Plan Diagnostic · Powered by Waypoint
            </div>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <span className="hidden md:inline" style={{ fontSize: 12, color: T.t3, fontFamily: T.fBody }}>
            Complimentary Client Audit
          </span>
          {agencyContext.response_sla_hours ? (
            <span style={{ fontSize: 11, color: T.cyan, background: 'rgba(57,208,216,0.1)', padding: '2px 8px', borderRadius: 4, border: '1px solid rgba(57,208,216,0.3)', fontFamily: T.fBody }}>
              Listed response time: {agencyContext.response_sla_hours}h
            </span>
          ) : null}
        </div>
      </header>
    );
  }

  return (
    <header style={S.header} className="px-4 py-3 sm:px-8">
      <Link href='/' style={{ display: 'flex', alignItems: 'center', gap: 9, textDecoration: 'none' }}>
        <div style={S.logoMark}>
          <MapPin size={14} />
        </div>
        <div className='itinerary-reveal'>
          <div style={{ fontSize: 13, fontWeight: 700, color: T.t1, letterSpacing: '-0.01em', fontFamily: T.fBody }}>Waypoint</div>
          <div style={{ fontSize: 12, color: T.t3, lineHeight: 1, fontFamily: T.fBody }}>Travel plan checker</div>
        </div>
      </Link>
      <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
        <span className="hidden md:inline" style={{ fontSize: 12, color: T.t3, fontFamily: T.fBody }}>Free · No account required</span>
        <Link href='/signup' style={S.agencyPillLink}>
          For agencies →
        </Link>
      </div>
    </header>
  );
}

async function extractTextFromFile(file: File): Promise<string> {
  const lowerName = file.name.toLowerCase();
  const type = file.type.toLowerCase();

  if (type.startsWith('text/') || lowerName.endsWith('.txt') || lowerName.endsWith('.md')) {
    return await file.text();
  }

  if (type === 'application/pdf' || lowerName.endsWith('.pdf')) {
    const pdfjs = await import('pdfjs-dist/build/pdf.mjs');

    const data = await file.arrayBuffer();
    // Keep the public checker self-contained. pdfjs-dist v5 ships an ESM
    // worker that Next/Terser cannot safely bundle as a classic script;
    // bounded checker uploads are intentionally parsed on the main thread
    // until a first-class, version-pinned worker asset is hosted.
    const doc = await pdfjs.getDocument({ data, disableWorker: true }).promise;

    const pages = await Promise.all(
      Array.from({ length: doc.numPages }, (_, i) => doc.getPage(i + 1))
    );
    const contents = await Promise.all(pages.map((p) => p.getTextContent()));
    const pageTexts: string[] = [];
    for (const content of contents) {
      const text = (content.items as Array<{ str?: string }>)
        .flatMap((item) => item.str ? [item.str] : [])
        .join(' ');
      if (text.trim()) {
        pageTexts.push(text.trim());
      }
    }

    return pageTexts.join('\n\n').trim();
  }

  if (type.startsWith('image/') || /\.(png|jpe?g|webp|avif|gif)$/i.test(file.name)) {
    const { recognize } = await import('tesseract.js');
    const dataUrl = await new Promise<string>((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(String(reader.result));
      reader.onerror = () => reject(reader.error ?? new Error('Could not load image.'));
      reader.readAsDataURL(file);
    });

    const result = await recognize(dataUrl, 'eng');
    return result.data.text.trim();
  }

  throw new Error('Supported file types are .txt, .md, .pdf, and common image formats.');
}

async function fileToBase64(file: File): Promise<string> {
  const buffer = await file.arrayBuffer();
  const bytes = new Uint8Array(buffer);
  let binary = '';
  const chunkSize = 0x8000;

  for (let i = 0; i < bytes.length; i += chunkSize) {
    binary += String.fromCharCode(...bytes.slice(i, i + chunkSize));
  }

  return btoa(binary);
}

const KNOWN_DESTINATION_PATTERNS: ReadonlyArray<readonly [RegExp, string]> = [
  [/\btokyo\b/i, 'Tokyo'],
  [/\bkyoto\b/i, 'Kyoto'],
  [/\bosaka\b/i, 'Osaka'],
  [/\bnara\b/i, 'Nara'],
  [/\bdubai\b/i, 'Dubai'],
  [/\babu dhabi\b/i, 'Abu Dhabi'],
  [/\bal maha\b/i, 'Al Maha'],
  [/\bsingapore\b/i, 'Singapore'],
  [/\bsentosa\b/i, 'Sentosa'],
  [/universal studios/i, 'Universal Studios Singapore'],
  [/gardens by the bay/i, 'Gardens by the Bay'],
  [/marina bay/i, 'Marina Bay'],
  [/\brome\b/i, 'Rome'],
  [/amalfi/i, 'Amalfi Coast'],
  [/positano/i, 'Positano'],
  [/ravello/i, 'Ravello'],
  [/\bparis\b/i, 'Paris'],
  [/\blondon\b/i, 'London'],
  [/zermatt/i, 'Zermatt'],
  [/st\.?\s*moritz/i, 'St. Moritz'],
  [/zurich/i, 'Zurich'],
  [/\bbali\b/i, 'Bali'],
  [/\bubud\b/i, 'Ubud'],
  [/maldives/i, 'Maldives'],
  [/hong kong/i, 'Hong Kong'],
  [/bangkok/i, 'Bangkok'],
  [/barcelona/i, 'Barcelona'],
  [/lisbon/i, 'Lisbon'],
  [/athens/i, 'Athens'],
  [/santorini/i, 'Santorini'],
  [/istanbul/i, 'Istanbul'],
];

function inferTravelContext(text: string): Record<string, unknown> {
  const matches = {
    origin:
      text.match(/origin(?:\s+city)?\s*[:\-]\s*([^\n\r|]+)/i)?.[1]?.trim() ??
      text.match(/\bfrom\s+([A-Z][a-zA-Z\s]+?)\s+to\b/)?.[1]?.trim(),
    purpose: text.match(/trip purpose\s*[:\-]\s*([^\n\r|]+)/i)?.[1]?.trim(),
    budget: text.match(/budget\s*[:\-]\s*([^\n\r|]+)/i)?.[1]?.trim(),
    dateWindow:
      text.match(/trip window\s*[:\-]\s*([^\n\r|]+)/i)?.[1]?.trim() ??
      text.match(/late may\s+\d{4}/i)?.[0]?.trim(),
  };

  const destinationCandidates = new Set<string>();
  for (const [pattern, label] of KNOWN_DESTINATION_PATTERNS) {
    if (pattern.test(text)) {
      destinationCandidates.add(label);
    }
  }

  return {
    ...(matches.origin ? { origin_city: matches.origin } : {}),
    ...(matches.purpose ? { trip_purpose: matches.purpose } : {}),
    ...(matches.budget ? { budget_raw_text: matches.budget } : {}),
    ...(matches.dateWindow ? { date_window: matches.dateWindow } : {}),
    ...(destinationCandidates.size > 0 ? { destination_candidates: [...destinationCandidates] } : {}),
  };
}

const makeTrackingId = (prefix: 'sess' | 'inq') =>
  `${prefix}_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 10)}`;

type ProductBEventPayload = {
  event_name: string;
  session_id: string;
  inquiry_id: string;
  trip_id?: string | null;
  actor_type: 'traveler' | 'system' | 'operator';
  actor_id?: string | null;
  workspace_id?: string | null;
  channel: 'web' | 'mobile_web' | 'api';
  locale?: string | null;
  currency?: string | null;
  properties: Record<string, unknown>;
};

type UploadTab = 'file' | 'paste' | 'screenshot';

type UploadCardState = {
  activeTab: UploadTab;
  dragging: boolean;
  text: string;
  isProcessingFile: boolean;
  fileError: string | null;
  retentionConsent: boolean;
  declaredPlanSource: 'self' | 'ai' | 'vendor';
  alreadyBooked: boolean;
};

type UploadCardAction =
  | { type: 'selectTab'; tab: UploadTab }
  | { type: 'setDragging'; dragging: boolean }
  | { type: 'setText'; text: string }
  | { type: 'startFileProcessing' }
  | { type: 'fileProcessingSucceeded' }
  | { type: 'fileProcessingFailed'; message: string }
  | { type: 'setFileError'; message: string | null }
  | { type: 'setRetentionConsent'; retentionConsent: boolean }
  | { type: 'setDeclaredPlanSource'; source: 'self' | 'ai' | 'vendor' }
  | { type: 'setAlreadyBooked'; alreadyBooked: boolean };

const initialUploadCardState: UploadCardState = {
  activeTab: 'paste',
  dragging: false,
  text: '',
  isProcessingFile: false,
  fileError: null,
  retentionConsent: false,
  declaredPlanSource: 'ai',
  alreadyBooked: false,
};

function uploadCardReducer(state: UploadCardState, action: UploadCardAction): UploadCardState {
  switch (action.type) {
    case 'selectTab':
      return { ...state, activeTab: action.tab };
    case 'setDragging':
      return { ...state, dragging: action.dragging };
    case 'setText':
      return { ...state, text: action.text };
    case 'startFileProcessing':
      return { ...state, fileError: null, isProcessingFile: true };
    case 'fileProcessingSucceeded':
      return { ...state, isProcessingFile: false };
    case 'fileProcessingFailed':
      return { ...state, isProcessingFile: false, fileError: action.message };
    case 'setFileError':
      return { ...state, fileError: action.message };
    case 'setRetentionConsent':
      return { ...state, retentionConsent: action.retentionConsent };
    case 'setDeclaredPlanSource':
      return { ...state, declaredPlanSource: action.source };
    case 'setAlreadyBooked':
      return { ...state, alreadyBooked: action.alreadyBooked };
    default:
      return state;
  }
}

// ── Upload card (reused in hero) ──────────────────────────────────────────────
function UploadCard({
  onAnalyze,
  onAnalyzeFile,
  isBusy,
  externalDraftText,
  onSelectScenario,
  activeScenarioKey,
}: {
  onAnalyze: (plan: string, sourcePayload?: Record<string, unknown>, declaredPlanSource?: 'self' | 'ai' | 'vendor') => void;
  onAnalyzeFile: (file: File, retentionConsent: boolean, declaredPlanSource?: 'self' | 'ai' | 'vendor', alreadyBooked?: boolean) => Promise<void>;
  isBusy: boolean;
  externalDraftText?: { text: string; nonce: number } | null;
  onSelectScenario?: (index: number) => void;
  activeScenarioKey?: WedgeScenarioKey;
}) {
  const [state, dispatch] = useReducer(uploadCardReducer, initialUploadCardState);
  const { activeTab, dragging, text, isProcessingFile, fileError, retentionConsent, declaredPlanSource, alreadyBooked } = state;
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!externalDraftText) return;
    dispatch({ type: 'selectTab', tab: 'paste' });
    dispatch({ type: 'setText', text: externalDraftText.text });
  }, [externalDraftText]);

  const tabs: { key: UploadTab; label: string }[] = [
    { key: 'paste',      label: 'Paste plan / ChatGPT' },
    { key: 'file',       label: 'Upload PDF / file'     },
    { key: 'screenshot', label: 'Screenshot'           },
  ];

  const handleDragOver = (e: DragEvent) => { e.preventDefault(); dispatch({ type: 'setDragging', dragging: true }); };
  const handleDragLeave = () => dispatch({ type: 'setDragging', dragging: false });
  const handleFile = async (file: File) => {
    dispatch({ type: 'startFileProcessing' });
    try {
      await onAnalyzeFile(file, retentionConsent, declaredPlanSource, alreadyBooked);
      dispatch({ type: 'fileProcessingSucceeded' });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Could not read that file.';
      dispatch({ type: 'fileProcessingFailed', message });
    }
  };

  const handleDrop = (e: DragEvent) => {
    e.preventDefault();
    dispatch({ type: 'setDragging', dragging: false });
    const file = e.dataTransfer.files?.[0];
    if (!file) {
      dispatch({ type: 'setFileError', message: 'Drop a PDF, image, or text file here, or click to choose one.' });
      return;
    }
    void handleFile(file);
  };

  return (
    <div style={{ width: '100%', position: 'relative' }}>
      {/* Mode tabs */}
      <div style={{
        display: 'flex', gap: 4, marginBottom: 12,
        background: T.surface, borderRadius: 10, padding: 4,
        border: `1px solid ${T.b0}`,
      }}>
        {tabs.map(tab => (
          <button key={tab.key} type='button' onClick={() => dispatch({ type: 'selectTab', tab: tab.key })} aria-pressed={activeTab === tab.key} style={tabButtonStyle(activeTab === tab.key)}>
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === 'paste' ? (
        <div style={{ borderRadius: 14, border: `1px solid ${T.b1}`, background: T.surface, overflow: 'hidden' }}>
          {/* Quick-fill sample scenarios */}
          <div style={{
            padding: '10px 14px',
            borderBottom: `1px solid ${T.b0}`,
            background: 'rgba(22,27,34,0.75)',
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            flexWrap: 'wrap',
          }}>
            <span style={{ fontSize: 11, fontWeight: 600, color: T.t3, marginRight: 2 }}>
              Try a sample plan:
            </span>
            {WEDGE_SCENARIO_LIST.map((scenario, idx) => {
              const isSelected = activeScenarioKey === scenario.key && text === scenario.samplePasteText;
              return (
                <button
                  key={scenario.key}
                  type='button'
                  onClick={() => {
                    dispatch({ type: 'setText', text: scenario.samplePasteText });
                    onSelectScenario?.(idx);
                  }}
                  style={{
                    fontSize: 11,
                    fontWeight: 600,
                    padding: '4px 9px',
                    borderRadius: 999,
                    cursor: 'pointer',
                    background: isSelected ? 'rgba(57,208,216,0.16)' : T.elevated,
                    color: isSelected ? T.cyan : T.t2,
                    border: `1px solid ${isSelected ? 'rgba(57,208,216,0.45)' : T.b0}`,
                    whiteSpace: 'nowrap',
                  }}
                >
                  {scenario.badge}
                </button>
              );
            })}
          </div>
          <label htmlFor='checker-itinerary' style={{ display: 'block', padding: '12px 16px 0', color: T.t2 }}>Your itinerary</label>
          <textarea
            id='checker-itinerary'
            name='itinerary'
            value={text}
            onChange={e => dispatch({ type: 'setText', text: e.target.value })}
            placeholder={'Paste your day-by-day plan here…\n\nDay 1: Arrive LAX → London Heathrow (AA100, dep 10:30)\nDay 2: London - check-in The Connaught, walking tour\nDay 3: Paris Eurostar (07:55) - Musée d\'Orsay, Seine dinner\n…'}
            style={S.pasteTextarea}
          />
          <div style={{
            padding: '10px 16px', borderTop: `1px solid ${T.b0}`,
            display: 'flex',
            flexDirection: 'column',
            rowGap: 10,
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: 12, color: T.t3 }}>
                {text.length > 0 ? `${text.length} characters` : 'Messy inputs work fine'}
              </span>
              <button
                type='button'
                onClick={() => onAnalyze(text, { kind: 'paste', source: 'typed', retention_consent: retentionConsent, already_booked: alreadyBooked }, declaredPlanSource)}
                disabled={text.trim().length < 10 || isBusy || isProcessingFile}
                style={primaryButtonStyle(text.trim().length >= 10 && !isBusy && !isProcessingFile)}
              >
                {isBusy ? 'Checking…' : 'Check my itinerary'} <ArrowRight size={13} />
              </button>
            </div>
            <PlanSourcePicker
              value={declaredPlanSource}
              onChange={(source) => dispatch({ type: 'setDeclaredPlanSource', source })}
            />
            <AlreadyBookedPicker
              value={alreadyBooked}
              onChange={(booked) => dispatch({ type: 'setAlreadyBooked', alreadyBooked: booked })}
            />
            <ConsentToggle
              checked={retentionConsent}
              onChange={(next) => dispatch({ type: 'setRetentionConsent', retentionConsent: next })}
            />
          </div>
        </div>
      ) : (
        <>
        <div
          role='region'
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={(e) => {
            const target = e.target as HTMLElement;
            if (target.closest('button') || target.closest('input')) return;
            fileRef.current?.click();
          }}
          aria-label={activeTab === 'screenshot' ? 'Upload itinerary screenshot' : 'Upload itinerary document'}
          style={{ ...uploadDropZoneStyle(dragging), cursor: 'pointer' }}
        >
          <div style={S.uploadIconFrame}>
            <Upload size={22} strokeWidth={1.5} />
          </div>
          <div style={{ fontSize: 15, fontWeight: 600, color: T.t1, marginBottom: 5 }}>
            {activeTab === 'screenshot' ? 'Drop your screenshot here' : 'Drop your PDF here'}
          </div>
          <div style={{ fontSize: 12, color: T.t3, marginBottom: 20 }}>
            {activeTab === 'screenshot' ? 'JPG, PNG, or WEBP up to 25 MB' : 'PDF, JPG, PNG, or .txt up to 25 MB'}
          </div>
          <PlanSourcePicker
            value={declaredPlanSource}
            onChange={(source) => dispatch({ type: 'setDeclaredPlanSource', source })}
          />
          <AlreadyBookedPicker
            value={alreadyBooked}
            onChange={(booked) => dispatch({ type: 'setAlreadyBooked', alreadyBooked: booked })}
          />
          <ConsentToggle
            checked={retentionConsent}
            onChange={(next) => dispatch({ type: 'setRetentionConsent', retentionConsent: next })}
          />
          <div style={{ position: 'relative', display: 'inline-flex' }}>
            <button
              type='button'
              onClick={() => fileRef.current?.click()}
              style={primaryButtonStyle(!(isBusy || isProcessingFile), 42, '0 20px')}
            >
              {isProcessingFile ? 'Reading file…' : 'Choose file to score'}
            </button>
          </div>
        </div>
        <input
          ref={fileRef}
          type='file'
          accept='.pdf,.jpg,.jpeg,.png,.txt,.webp'
          aria-label='Upload itinerary file'
          onChange={async (e) => {
            const file = e.target.files?.[0];
            if (!file) {
              return;
            }
            const input = e.currentTarget;
            await handleFile(file);
            input.value = '';
          }}
          style={{
            display: 'none',
          }}
        />
        </>
      )}

      {fileError ? (
        <div style={S.inlineError}>
          {fileError}
        </div>
      ) : null}

      {/* Trust chips */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        gap: 18, marginTop: 14, flexWrap: 'wrap',
      }}>
        {['Free to use', 'No sign-up required', 'Consent-based storage'].map(label => (
          <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
            <Check size={12} color={T.green} strokeWidth={2.5} />
            <span style={{ fontSize: 12, color: T.t3 }}>{label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── What we check data ────────────────────────────────────────────────────────
const CHECKS = [
  {
    icon: Clock, color: T.cyan, label: 'Timing & Connections',
    body: 'Layover durations, minimum connection times, and airport transit requirements by route.',
  },
  {
    icon: Globe, color: T.blue, label: 'Visa & Entry Requirements',
    body: 'Passport validity, visa eligibility, e-visa availability, and border crossing restrictions.',
  },
  {
    icon: Activity, color: T.amber, label: 'Pacing & Fatigue',
    body: 'Daily activity density, travel time between sites, and over-scheduled day detection.',
  },
  {
    icon: DollarSign, color: T.green, label: 'Cost & Hidden Fees',
    body: 'City taxes, resort fees, luggage charges, and payment requirements not shown at booking.',
  },
  {
    icon: Shield, color: T.purple, label: 'Insurance & Emergency',
    body: 'Coverage gaps, no-insurance flags, and missing emergency contact or evacuation plans.',
  },
  {
    icon: Star, color: T.red, label: 'Supplier Reliability',
    body: 'Hotel rating changes, airline code-share risks, and supplier stability signals.',
  },
];

const sevBadgeBg  = { Critical: 'rgba(248,81,73,0.1)', Warning: 'rgba(210,153,34,0.12)', Info: 'rgba(88,166,255,0.1)' } as const;
const sevBadgeBdr = { Critical: 'rgba(248,81,73,0.22)', Warning: 'rgba(210,153,34,0.25)', Info: 'rgba(88,166,255,0.22)' } as const;
const sevBadgeTxt = { Critical: T.red, Warning: T.amber, Info: T.blue } as const;
const sevCardBg   = { Critical: 'rgba(248,81,73,0.06)', Warning: 'rgba(210,153,34,0.06)', Info: 'rgba(88,166,255,0.05)' } as const;
const sevCardBdr  = { Critical: 'rgba(248,81,73,0.2)', Warning: 'rgba(210,153,34,0.2)', Info: 'rgba(88,166,255,0.15)' } as const;

// EX-05 legal disclaimer — OWNER-APPROVED AS-IS (Pranay, 2026-09-09).
// Mounted on the result view and the upload footer; asserted by honesty-sweep.
const CHECKER_DISCLAIMER =
  'Automated guidance based on what you provided and public data sources — not legal, visa, or booking advice. Verify with official sources and your travel advisor before you pay or travel.';

// ── Upload view sections ─────────────────────────────────────────────────────
function UploadHeroSection({
  onAnalyze,
  onAnalyzeFile,
  isBusy,
  analysisError,
  activeScenario,
  onSelectScenario,
  externalDraftText,
}: {
  onAnalyze: (plan: string, sourcePayload?: Record<string, unknown>, declaredPlanSource?: 'self' | 'ai' | 'vendor') => void;
  onAnalyzeFile: (file: File, retentionConsent: boolean, declaredPlanSource?: 'self' | 'ai' | 'vendor', alreadyBooked?: boolean) => Promise<void>;
  isBusy: boolean;
  analysisError: string | null;
  activeScenario: WedgeScenarioBundle;
  onSelectScenario: (index: number) => void;
  externalDraftText: { text: string; nonce: number } | null;
}) {
  const topFinding = activeScenario.findings[0];
  const errorRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (analysisError) errorRef.current?.focus();
  }, [analysisError]);

  return (
    <>
      {/* ── HERO: balanced 2-col ── */}
      <section className='grid gap-6 md:grid-cols-2 md:gap-x-12' style={S.heroSection}>
        {/* Left: clear problem/output framing + compact real-output snapshot */}
        <div>
          <span style={S.amberKicker}>
            Free travel plan check
          </span>

          <h1 style={{
            fontSize: 'clamp(34px, 3.8vw, 48px)', fontWeight: 600,
            lineHeight: 1.06, letterSpacing: '-0.035em',
            color: '#f5fbff', fontFamily: T.fDisplay, marginBottom: 16,
          }}>
            Check your itinerary before you book.
          </h1>

          <p style={{ fontSize: 15, lineHeight: 1.65, color: T.t2, maxWidth: '46ch', marginBottom: 0 }}>
            Upload a PDF, paste your draft, or drop a screenshot. Waypoint extracts your route and dates
            and shows which details to confirm before paying.
          </p>
        </div>

        {/* Right: interactive upload/paste tool */}
        <div className='itinerary-reveal min-w-0 md:col-start-2 md:row-span-2 md:row-start-1' style={{ position: 'relative' }}>
          {analysisError ? (
            <div role='alert' ref={errorRef} tabIndex={-1} style={{ scrollMarginTop: 88, ...severityCardStyle('rgba(248,81,73,0.08)', 'rgba(248,81,73,0.25)'), display: 'block', marginBottom: 12, color: T.t1 }}>
              <strong>Itinerary check unavailable</strong>
              <div style={{ marginTop: 4, lineHeight: 1.5 }}>{analysisError}</div>
            </div>
          ) : null}
          {isBusy ? <p role='status' style={{ color: T.t2 }}>Checking your itinerary…</p> : null}
          <UploadCard
            onAnalyze={onAnalyze}
            onAnalyzeFile={onAnalyzeFile}
            isBusy={isBusy}
            externalDraftText={externalDraftText}
            onSelectScenario={onSelectScenario}
            activeScenarioKey={activeScenario.key}
          />
        </div>
        <div className='min-w-0 md:col-start-1 md:row-start-2'>
          {/* Illustrative finding from the selected sample itinerary */}
          <div style={{
            borderRadius: 12,
            background: T.surface,
            border: `1px solid ${T.b0}`,
            padding: '16px 18px',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
          }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: 12,
              paddingBottom: 12,
              borderBottom: `1px solid ${T.b0}`,
              marginBottom: 12,
            }}>
              <div style={{ minWidth: 0 }}>
                <div style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: T.t2, fontFamily: T.fMono }}>
                  Sample finding · {activeScenario.badge}
                </div>
                <div style={{ fontSize: 14, fontWeight: 600, color: T.t1, marginTop: 2, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  {activeScenario.title}
                </div>
              </div>
            </div>

            {topFinding ? (
              <div style={{
                padding: '10px 12px',
                borderRadius: 8,
                background: 'rgba(248,81,73,0.06)',
                border: '1px solid rgba(248,81,73,0.2)',
                display: 'flex',
                alignItems: 'flex-start',
                gap: 10,
                minHeight: 42,
              }}>
                <span style={{
                  fontSize: 10,
                  fontWeight: 700,
                  textTransform: 'uppercase',
                  fontFamily: T.fMono,
                  color: T.red,
                  marginTop: 2,
                  flexShrink: 0,
                }}>
                  Flagged
                </span>
                <div style={{ fontSize: 12, color: T.t1, lineHeight: 1.45 }}>
                  {topFinding.label}
                </div>
              </div>
            ) : null}
          </div>
        </div>
      </section>
    </>
  );
}

function PublicVisualDiagnosticSection({
  scenario,
  activeScenarioIdx,
  onSelectScenario,
  onLoadScenario,
  onInteractPause,
}: {
  scenario: WedgeScenarioBundle;
  activeScenarioIdx: number;
  onSelectScenario: (index: number) => void;
  onLoadScenario: (scenario: WedgeScenarioBundle) => void;
  onInteractPause: () => void;
}) {
  return (
    <section style={{
      position: 'relative',
      zIndex: 1,
      borderTop: `1px solid ${T.b0}`,
      padding: '56px clamp(16px, 4vw, 40px)',
    }}>
      <div style={{ maxWidth: 1180, margin: '0 auto' }}>
        <div style={{
          display: 'flex',
          flexWrap: 'wrap',
          justifyContent: 'space-between',
          alignItems: 'flex-end',
          gap: 20,
          marginBottom: 20,
        }}>
          <div>
            <div style={S.sectionKicker}>
              Diagnostic Engine
            </div>
            <h2 style={{
              fontSize: 'clamp(24px, 3vw, 34px)',
              fontWeight: 600,
              letterSpacing: '-0.03em',
              color: T.t1,
              fontFamily: T.fDisplay,
              margin: '0 0 8px 0',
            }}>
              Inspect how each check works
            </h2>
            <p style={{ fontSize: 14, color: T.t2, maxWidth: '58ch', margin: 0, lineHeight: 1.6 }}>
              Switch scenarios to inspect hub layover buffers, multi-stop routes, daily pacing load, and eligible
              hotel rate-parity perks before uploading your own plan.
            </p>
          </div>

          <button
            type='button'
            onClick={() => onLoadScenario(scenario)}
            style={sectionButtonStyle('primary')}
          >
            Load this trip into checker ↑
          </button>
        </div>

        {/* Scenario Switcher Strip */}
        <div style={{
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          gap: 8,
          marginBottom: 14,
        }}>
          <span style={{ fontSize: 12, fontWeight: 600, color: T.t3, marginRight: 4 }}>
            Scenario:
          </span>
          {WEDGE_SCENARIO_LIST.map((item, idx) => {
            const active = idx === activeScenarioIdx;
            return (
              <button
                key={item.key}
                type='button'
                onClick={() => onSelectScenario(idx)}
                style={{
                  padding: '6px 12px',
                  borderRadius: 999,
                  fontSize: 12,
                  fontWeight: active ? 700 : 500,
                  cursor: 'pointer',
                  background: active ? 'rgba(57,208,216,0.14)' : T.surface,
                  color: active ? T.cyan : T.t2,
                  border: `1px solid ${active ? 'rgba(57,208,216,0.45)' : T.b0}`,
                }}
              >
                {item.badge}
              </button>
            );
          })}
        </div>

        <div onPointerDown={onInteractPause}>
          <WedgeVisualShowcase
            scenarioKey={scenario.key}
            onAdvisorHelp={() => onLoadScenario(scenario)}
          />
        </div>
      </div>
    </section>
  );
}

function ExampleFindingsSection({
  scenario,
  onLoadScenario,
}: {
  scenario: WedgeScenarioBundle;
  onLoadScenario: (scenario: WedgeScenarioBundle) => void;
}) {
  return (
    <>
      {/* ── EXAMPLE FINDINGS (SCENARIO-SYNCED) ── */}
      <section style={{
        position: 'relative', zIndex: 1,
        borderTop: `1px solid ${T.b0}`,
        padding: '64px clamp(16px, 4vw, 40px)',
        background: T.surface,
      }}>
        <div style={{ maxWidth: 1180, margin: '0 auto' }}>
          <div style={{
            display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 320px), 1fr))', gap: 56, alignItems: 'start',
          }}>
            {/* Left: copy */}
            <div style={{ paddingTop: 4 }}>
              <div style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 8,
                padding: '4px 10px',
                borderRadius: 6,
                background: 'rgba(210,153,34,0.08)',
                border: '1px solid rgba(210,153,34,0.22)',
                fontSize: 11,
                fontWeight: 700,
                letterSpacing: '0.06em',
                textTransform: 'uppercase',
                color: T.amber,
                marginBottom: 14,
              }}>
                {scenario.title} · {scenario.routeSummary}
              </div>
              <h2 style={{
                fontSize: 'clamp(24px, 2.8vw, 34px)', fontWeight: 600,
                letterSpacing: '-0.03em', color: T.t1, fontFamily: T.fDisplay,
                marginBottom: 16, lineHeight: 1.12,
              }}>
                Specific signals, not vague travel advice
              </h2>
              <p style={{ fontSize: 14.5, color: T.t2, lineHeight: 1.65, marginBottom: 22, maxWidth: '42ch' }}>
                Every check surfaces what the engine extracted, what feels brittle or missing, and what to confirm
                before you book or hand the brief to an advisor.
              </p>
              <button
                type='button'
                onClick={() => onLoadScenario(scenario)}
                style={sectionButtonStyle('secondary')}
              >
                Load {scenario.badge} into checker ↑
              </button>
            </div>

            {/* Right: synced findings cards */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10, minHeight: 396 }}>
              {scenario.findings.map(f => {
                const sev = f.sev;
                return (
                  <div key={f.label} style={severityCardStyle(sevCardBg[sev], sevCardBdr[sev])}>
                    <span style={severityBadgeStyle(sev)}>
                      {f.sev}
                    </span>
                    <div>
                      <div style={{ fontSize: 13, fontWeight: 600, color: T.t1, marginBottom: 3 }}>{f.label}</div>
                      <div style={{ fontSize: 12, color: T.t2, lineHeight: 1.55 }}>{f.body}</div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </section>
    </>
  );
}

function FinalCtaSection() {
  return (
    <footer style={{
      position: 'relative',
      zIndex: 1,
      borderTop: `1px solid ${T.b0}`,
      padding: '36px 40px 44px',
      background: T.canvas,
    }}>
      <div style={{
        maxWidth: 1180,
        margin: '0 auto',
        display: 'flex',
        flexWrap: 'wrap',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: 20,
      }}>
        <div style={{ maxWidth: 680, fontSize: 11.5, color: T.t3, lineHeight: 1.55 }}>
          {CHECKER_DISCLAIMER} Submitted itineraries, extracted facts, and scores are saved by default to improve
          the checker unless you uncheck storage above.
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 14, flexWrap: 'wrap' }}>
          <button
            type='button'
            onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
            style={sectionButtonStyle('primary')}
          >
            Check my itinerary ↑
          </button>
          <Link href='/signup' style={{ fontSize: 12, color: T.blue, textDecoration: 'none', whiteSpace: 'nowrap' }}>
            For agencies: Waypoint OS →
          </Link>
        </div>
      </div>
    </footer>
  );
}

// ── Upload view (landing + tool) ──────────────────────────────────────────────
function UploadView({
  rootRef,
  onAnalyze,
  onAnalyzeFile,
  isBusy,
  analysisError,
  initialDraft,
  agencyContext,
}: {
  rootRef: RefObject<HTMLDivElement | null>;
  onAnalyze: (plan: string, sourcePayload?: Record<string, unknown>, declaredPlanSource?: 'self' | 'ai' | 'vendor') => void;
  onAnalyzeFile: (file: File, retentionConsent: boolean, declaredPlanSource?: 'self' | 'ai' | 'vendor', alreadyBooked?: boolean) => Promise<void>;
  isBusy: boolean;
  analysisError: string | null;
  initialDraft: string | null;
  agencyContext?: AgencyBrandingContext | null;
}) {
  const [activeScenarioIdx, setActiveScenarioIdx] = useState(0);
  const [isAutoPlaying, setIsAutoPlaying] = useState(false);
  const [draftToLoad, setDraftToLoad] = useState<{ text: string; nonce: number } | null>(initialDraft ? { text: initialDraft, nonce: 0 } : null);

  useEffect(() => {
    if (!isAutoPlaying) return;
    if (typeof window !== 'undefined' && window.matchMedia?.('(prefers-reduced-motion: reduce)').matches) {
      return;
    }
    const timer = window.setInterval(() => {
      setActiveScenarioIdx((prev) => (prev + 1) % WEDGE_SCENARIO_LIST.length);
    }, 5500);
    return () => window.clearInterval(timer);
  }, [isAutoPlaying]);

  const activeScenario = WEDGE_SCENARIO_LIST[activeScenarioIdx] ?? WEDGE_SCENARIO_CATALOG.tokyo_kyoto;

  const handleSelectScenario = (index: number) => {
    setActiveScenarioIdx(index);
    setIsAutoPlaying(false);
  };

  const handleLoadScenario = (scenario: WedgeScenarioBundle) => {
    const idx = WEDGE_SCENARIO_LIST.findIndex((s) => s.key === scenario.key);
    if (idx >= 0) {
      setActiveScenarioIdx(idx);
    }
    setIsAutoPlaying(false);
    setDraftToLoad((prev) => ({
      text: scenario.samplePasteText,
      nonce: (prev?.nonce ?? 0) + 1,
    }));
    if (typeof window !== 'undefined') {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  return (
    <div ref={rootRef} style={{
      background: T.canvas, fontFamily: T.fBody, color: T.t1,
    }}>
      <WedgeHeader agencyContext={agencyContext} />
      <UploadHeroSection
        onAnalyze={onAnalyze}
        onAnalyzeFile={onAnalyzeFile}
        isBusy={isBusy}
        analysisError={analysisError}
        activeScenario={activeScenario}
        onSelectScenario={handleSelectScenario}
        externalDraftText={draftToLoad}
      />
      <PublicVisualDiagnosticSection
        scenario={activeScenario}
        activeScenarioIdx={activeScenarioIdx}
        onSelectScenario={handleSelectScenario}
        onLoadScenario={handleLoadScenario}
        onInteractPause={() => setIsAutoPlaying(false)}
      />
      <ExampleFindingsSection
        scenario={activeScenario}
        onLoadScenario={handleLoadScenario}
      />
      <FinalCtaSection />
    </div>
  );
}

// ── Results data ──────────────────────────────────────────────────────────────
// RDA_EX07 rec-3 (FND-0399): booking-critical visa/passport checks fire at
// stage="booking", which doubles as the declared-already-booked stage for the
// public checker. Everyone else runs the discovery checks.
export function stageForSubmittedPlan(alreadyBooked: boolean): 'booking' | 'discovery' {
  return alreadyBooked ? 'booking' : 'discovery';
}

export function formatTravelerBlockerItem(item: string, sourceFindings: readonly string[] = []): string {
  if (item === 'extraction_quality') {
    return 'We could not confidently read the key trip details from this plan yet. Please add clearer dates, route details, and traveler info.';
  }

  if (item === 'incomplete_intake') {
    return 'A few core intake details are still missing. Review the missing details below and add what you know.';
  }

  if (sourceFindings.includes(item) && /\s/.test(item.trim())) return item;

  // Part-K AT-21: backend slugs must not reach travelers as findings — an
  // unknown blocker falls back to an honest generic line, never raw copy.
  return 'We flagged something in this plan that needs a human eye. Your travel advisor can confirm the details.';
}

function getPacketFactValue(packet: Record<string, unknown> | null | undefined, key: string): unknown {
  const facts = packet?.facts;
  if (!facts || typeof facts !== 'object') return undefined;
  const factEntry = (facts as Record<string, unknown>)[key];
  if (!factEntry || typeof factEntry !== 'object') return undefined;
  if (key === 'traveler_plan' && isLegacyBookingDefault(factEntry)) return undefined;
  return (factEntry as Record<string, unknown>).value;
}

function getBooleanFromUnknown(value: unknown): boolean | null {
  if (typeof value === 'boolean') {
    return value;
  }
  return null;
}

type PublicCheckerReportStorageSummary = {
  loading: boolean;
  retentionConsented: boolean | null;
  hasStoredUpload: boolean;
  uploadFileName: string | null;
};

function pickPublicCheckerReportStorage(payload: unknown): PublicCheckerReportStorageSummary {
  const safe: PublicCheckerReportStorageSummary = {
    loading: false,
    retentionConsented: null,
    hasStoredUpload: false,
    uploadFileName: null,
  };

  if (!payload || typeof payload !== 'object') {
    return safe;
  }

  const artifactManifest = (payload as Record<string, unknown>).artifact_manifest;
  if (artifactManifest && typeof artifactManifest === 'object') {
    const uploadedFile = (artifactManifest as Record<string, unknown>).uploaded_file;
    if (uploadedFile && typeof uploadedFile === 'object') {
      const fileNameValue = (uploadedFile as Record<string, unknown>).file_name;
      if (typeof fileNameValue === 'string' && fileNameValue.trim().length > 0) {
        safe.uploadFileName = fileNameValue.trim();
      }
    }
    safe.hasStoredUpload = true;
  }

  const trip = (payload as Record<string, unknown>).trip;
  if (!trip || typeof trip !== 'object') {
    return safe;
  }

  const rawInput = (trip as Record<string, unknown>).raw_input;
  if (!rawInput || typeof rawInput !== 'object') {
    return safe;
  }

  const rawInputRecord = rawInput as Record<string, unknown>;
  const submission = rawInputRecord.submission;
  if (submission && typeof submission === 'object') {
    const consentFromSubmission = getBooleanFromUnknown((submission as Record<string, unknown>).retention_consent);
    if (typeof consentFromSubmission === 'boolean') {
      safe.retentionConsented = consentFromSubmission;
      return safe;
    }

    const submissionSourcePayload = (submission as Record<string, unknown>).source_payload;
    if (submissionSourcePayload && typeof submissionSourcePayload === 'object') {
      const sourcePayloadConsent = getBooleanFromUnknown((submissionSourcePayload as Record<string, unknown>).retention_consent);
      if (typeof sourcePayloadConsent === 'boolean') {
        safe.retentionConsented = sourcePayloadConsent;
        return safe;
      }
    }
  }

  const sourcePayload = rawInputRecord.source_payload;
  if (sourcePayload && typeof sourcePayload === 'object') {
    const sourcePayloadConsent = getBooleanFromUnknown((sourcePayload as Record<string, unknown>).retention_consent);
    if (typeof sourcePayloadConsent === 'boolean') {
      safe.retentionConsented = sourcePayloadConsent;
      return safe;
    }
  }

  const directFlag = getBooleanFromUnknown(rawInputRecord.retention_consent);
  if (typeof directFlag === 'boolean') {
    safe.retentionConsented = directFlag;
  }

  return safe;
}

function ConsentToggle({
  checked,
  onChange,
}: {
  checked: boolean;
  onChange: (next: boolean) => void;
}) {
  return (
    <label
      onClick={(e) => e.stopPropagation()}
      style={{
        padding: '0 16px 10px',
        display: 'flex',
        alignItems: 'flex-start',
        gap: 10,
        cursor: 'pointer',
        textAlign: 'left',
      }}
    >
      <input
        type='checkbox'
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
        style={{ marginTop: 3, accentColor: T.cyan }}
      />
      <span style={{ fontSize: 12, color: T.t2, lineHeight: 1.45 }}>
        Allow Waypoint to save my original text or upload to help improve the checker.
        Leave unchecked to run the check without saving your original input. A derived report can still be saved.
      </span>
    </label>
  );
}

// Plan-source picker (WOBS P3): owner declares the plan's origin for the
// source-keyed corpus. Declare-radio only — no silent classification.
function PlanSourcePicker({
  value,
  onChange,
}: {
  value: 'self' | 'ai' | 'vendor';
  onChange: (source: 'self' | 'ai' | 'vendor') => void;
}) {
  const options: Array<{ key: 'self' | 'ai' | 'vendor'; label: string }> = [
    { key: 'self', label: 'I planned it' },
    { key: 'ai', label: 'AI planned it' },
    { key: 'vendor', label: 'A company did' },
  ];
  return (
    <div style={{ padding: '0 16px 10px', display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
      <span style={{ fontSize: 12, color: T.t3 }}>Who made this plan?</span>
      {options.map((option) => (
        <button
          key={option.key}
          type='button'
          onClick={() => onChange(option.key)}
          style={{
            fontSize: 11.5,
            padding: '4px 10px',
            borderRadius: 999,
            cursor: 'pointer',
            color: value === option.key ? T.canvas : T.t2,
            background: value === option.key ? T.cyan : T.elevated,
            border: `1px solid ${value === option.key ? T.cyan : T.b0}`,
          }}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}

// Booking-stage declaration (RDA_EX07 rec-3, FND-0399): travelers who have
// already booked submit under stage="booking" so the booking-critical
// visa/passport checks fire for them too. Declare-radio only — the engine
// never infers booked-ness from freeform text.
function AlreadyBookedPicker({
  value,
  onChange,
}: {
  value: boolean;
  onChange: (alreadyBooked: boolean) => void;
}) {
  const options: Array<{ key: boolean; label: string }> = [
    { key: false, label: 'Not booked yet' },
    { key: true, label: 'Already booked' },
  ];
  return (
    <div style={{ padding: '0 16px 10px', display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
      <span style={{ fontSize: 12, color: T.t3 }}>Have you booked this trip?</span>
      {options.map((option) => (
        <button
          key={String(option.key)}
          type='button'
          onClick={() => onChange(option.key)}
          style={{
            fontSize: 11.5,
            padding: '4px 10px',
            borderRadius: 999,
            cursor: 'pointer',
            color: value === option.key ? T.canvas : T.t2,
            background: value === option.key ? T.cyan : T.elevated,
            border: `1px solid ${value === option.key ? T.cyan : T.b0}`,
          }}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}

function normalizeFactValue(value: unknown): unknown | null {
  if (value == null) return null;

  if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') {
    return value;
  }

  if (Array.isArray(value)) {
    const normalized = value
      .map(normalizeFactValue)
      .filter((item): item is string | number | boolean => item !== null);
    if (normalized.length === 0) return null;
    return normalized.slice(0, 4);
  }

  if (typeof value === 'object') {
    const valueField = (value as Record<string, unknown>).value;
    if (valueField !== undefined) {
      return normalizeFactValue(valueField);
    }

    const amountField = (value as Record<string, unknown>).amount;
    if (amountField !== undefined) {
      return normalizeFactValue(amountField);
    }

    const startDate = (value as Record<string, unknown>).start_date;
    const endDate = (value as Record<string, unknown>).end_date;
    if (startDate != null && endDate != null) {
      const start = normalizeFactValue(startDate);
      const end = normalizeFactValue(endDate);
      if (start != null && end != null) {
        const startText = formatTravelerValue(start);
        const endText = formatTravelerValue(end);
        if (startText && endText) {
          return `${startText} → ${endText}`;
        }
      }
    }

    const rawWindow = (value as Record<string, unknown>).raw_window;
    if (rawWindow != null) return normalizeFactValue(rawWindow);
  }

  return null;
}

function formatTravelerValue(value: unknown): string | null {
  if (typeof value === 'string') {
    const trimmed = value.trim();
    return trimmed.length > 0 ? trimmed.replaceAll('_', ' ') : null;
  }

  if (typeof value === 'number' || typeof value === 'boolean') {
    return String(value);
  }

  if (Array.isArray(value)) {
    const items = value
      .map((item) => formatTravelerValue(item))
      .filter((item): item is string => Boolean(item));
    return items.length > 0 ? items.join(', ') : null;
  }

  if (value && typeof value === 'object') {
    const objectItems = Object.entries(value as Record<string, unknown>)
      .map(([key, entryValue]) => {
        const formatted = formatTravelerValue(entryValue);
        if (!formatted) return null;
        return `${key.replaceAll('_', ' ')} ${formatted}`;
      })
      .filter((item): item is string => Boolean(item));
    return objectItems.length > 0 ? objectItems.join(', ') : null;
  }

  return null;
}

function formatTravelerFactValue(value: unknown): string | null {
  const normalized = normalizeFactValue(value);
  if (Array.isArray(normalized)) {
    const items = normalized
      .map((item) => formatTravelerValue(item))
      .filter((item): item is string => Boolean(item));
    if (items.length === 0) return null;
    const dedup = [...new Set(items)];
    const filtered = dedup.filter((item) => item.toLowerCase() !== 'day');
    const finalItems = filtered.length > 0 ? filtered : dedup;
    return finalItems.slice(0, 4).join(', ');
  }

  return formatTravelerValue(normalized);
}

function buildSummaryFactItem(packet: Record<string, unknown> | null | undefined, key: string, label: string): ResultSummaryItem | null {
  const raw = getPacketFactValue(packet, key);
  const value = key === 'traveler_plan' && typeof raw === 'string' ? formatPacketValue(raw) : formatTravelerFactValue(raw);
  if (!value) return null;
  return {
    l: label,
    v: value,
  };
}

function formatUnknownFieldLabel(raw: string): string {
  const normalized = formatClarificationLabel(raw).toLowerCase();
  if (normalized === 'date window') return 'travel dates';
  if (normalized === 'origin city') return 'departure city';
  if (normalized === 'destination candidates') return 'destination';
  return normalized;
}

function buildUnknownFieldHints(
  validation: Record<string, unknown> | null | undefined,
  packet: Record<string, unknown> | null | undefined,
): string[] {
  const unknownFields = new Set<string>();

  const validationErrors = Array.isArray(validation?.errors) ? validation.errors : [];
  for (const item of validationErrors) {
    if (!item || typeof item !== 'object') continue;
    const field = String((item as Record<string, unknown>).field ?? '').trim();
    if (field) unknownFields.add(field);
  }

  const packetUnknowns = Array.isArray((packet as Record<string, unknown> | null | undefined)?.unknowns)
    ? ((packet as Record<string, unknown>).unknowns as unknown[])
    : [];
  for (const item of packetUnknowns) {
    if (!item || typeof item !== 'object') continue;
    const field = String((item as Record<string, unknown>).field_name ?? '').trim();
    if (field) unknownFields.add(field);
  }

  const observedUnknowns = Array.from(unknownFields)
    .map(formatUnknownFieldLabel)
    .filter((field) => field.length > 0);

  return observedUnknowns.slice(0, 3);
}

function buildTravelerSummaryPreamble(
  validation: Record<string, unknown> | null | undefined,
  packet: Record<string, unknown> | null | undefined,
): string[] {
  const lines: string[] = [];
  const origin = formatTravelerFactValue(getPacketFactValue(packet, 'origin_city'));
  if (origin) lines.push(`Departure identified as ${origin}`);

  const budget = formatTravelerFactValue(getPacketFactValue(packet, 'budget_raw_text'));
  if (budget) lines.push(`Budget context found (${budget})`);

  const unknowns = buildUnknownFieldHints(validation, packet);
  if (unknowns.length > 0) {
    lines.push(`Next inputs needed: ${unknowns.join(', ')}`);
  }

  return lines.slice(0, 2);
}

function buildTravelerTripSummary(
  analysis: RunStatusResponse | null | undefined,
  liveChecks: Record<string, any> | undefined,
): ResultSummaryItem[] {
  const packet = (analysis?.packet as Record<string, unknown> | null | undefined) ?? null;
  const destinationFromFacts =
    buildSummaryFactItem(packet, 'destination', 'Destination')
    || buildSummaryFactItem(packet, 'destination_candidates', 'Destination candidates');
  const dateWindowFromFacts = buildSummaryFactItem(packet, 'date_window', 'Travel window');
  const travelWindowFromLiveChecks = liveChecks?.travel_window?.start_date && liveChecks?.travel_window?.end_date
    ? { l: 'Travel window', v: `${String(liveChecks.travel_window.start_date)} -> ${String(liveChecks.travel_window.end_date)}` }
    : null;
  const partySizeFromFacts = buildSummaryFactItem(packet, 'party_size', 'Travelers');
  const partyMixFromFacts = buildSummaryFactItem(packet, 'party_composition', 'Group');
  const purposeFromFacts = buildSummaryFactItem(packet, 'trip_purpose', 'Trip type');
  const preferencesFromFacts = buildSummaryFactItem(packet, 'soft_preferences', 'Trip notes');
  const travelerPlanFromFacts = buildSummaryFactItem(packet, 'traveler_plan', 'Booking stage');
  const destinationStatusFromFacts = buildSummaryFactItem(packet, 'destination_status', 'Destination status');
  const budgetFromFacts =
    buildSummaryFactItem(packet, 'budget_raw_text', 'Budget')
    || buildSummaryFactItem(packet, 'budget_scope', 'Budget');
  const sourceFromLiveChecks = liveChecks?.source ? { l: 'Data checked', v: 'Live sources' } : null;

  const summaryLines = [
    ...buildTravelerSummaryPreamble(
      (analysis?.validation as Record<string, unknown> | null | undefined) ?? null,
      packet,
    ).map((line) => ({
      l: 'Signal',
      v: line,
    })),
    destinationFromFacts,
    travelWindowFromLiveChecks,
    dateWindowFromFacts,
    partySizeFromFacts,
    partyMixFromFacts,
    purposeFromFacts,
    budgetFromFacts,
    travelerPlanFromFacts,
    preferencesFromFacts,
    destinationStatusFromFacts,
    sourceFromLiveChecks,
  ].filter((item): item is ResultSummaryItem => Boolean(item));

  return summaryLines.slice(0, 8);
}

function formatClarificationLabel(raw: string): string {
  const normalized = raw.replaceAll('_', ' ').trim();
  if (normalized === 'date window') return 'Travel dates';
  if (normalized === 'origin city') return 'Departure city';
  if (normalized === 'budget raw text') return 'Budget';
  if (normalized === 'destination candidates') return 'Destination';
  return normalized.charAt(0).toUpperCase() + normalized.slice(1);
}

function buildTravelerClarifications(analysis: RunStatusResponse | null | undefined): string[] {
  const packet = (analysis?.packet as Record<string, unknown> | null | undefined) ?? null;
  if (getItineraryFeasibilityEvidence(packet).returnDatePending) {
    return ['Add your return date when you know it.'];
  }
  const validation = (analysis?.validation as Record<string, unknown> | null | undefined) ?? null;

  const unknowns = Array.isArray(packet?.unknowns) ? packet.unknowns : [];
  const ambiguityReport = Array.isArray(validation?.ambiguity_report) ? validation.ambiguity_report : [];
  const validationErrors = Array.isArray(validation?.errors) ? validation.errors : [];
  const followUps = Array.isArray(analysis?.follow_up_questions) ? analysis.follow_up_questions : [];

  const items = [
    ...unknowns.map((item) => {
      const fieldName = typeof item === 'object' && item && 'field_name' in item ? String((item as Record<string, unknown>).field_name ?? '') : '';
      if (!fieldName) return null;
      const reason = typeof item === 'object' && item && 'reason' in item ? String((item as Record<string, unknown>).reason ?? '') : '';
      if (reason && reason !== 'None' && reason.toLowerCase() !== 'null') {
        // Part-K AT-21: raw backend reason slugs stay out of traveler copy.
        return `Add ${formatClarificationLabel(fieldName).toLowerCase()} — this detail is still missing.`;
      }
      return `Add ${formatClarificationLabel(fieldName).toLowerCase()}.`;
    }),
    ...ambiguityReport.map((item) => {
      const rawField = typeof item === 'object' && item && 'field' in item ? String((item as Record<string, unknown>).field ?? '') : '';
      const rawValue = typeof item === 'object' && item && 'raw_value' in item ? String((item as Record<string, unknown>).raw_value ?? '') : '';
      if (!rawField) return null;
      return rawValue
        ? `Clarify ${formatClarificationLabel(rawField).toLowerCase()} (${rawValue}).`
        : `Clarify ${formatClarificationLabel(rawField).toLowerCase()}.`;
    }),
    ...validationErrors.map((item) => {
      if (!item || typeof item !== 'object') return null;
      const message = (item as Record<string, unknown>).message;
      const cleaned = typeof message === 'string' ? message.trim() : '';
      if (!cleaned) return null;
      // Part-K AT-21: slug-shaped backend messages never render raw.
      return cleaned.includes('_')
        ? 'Please double-check your travel dates and traveler details.'
        : cleaned;
    }),
    ...followUps.map((item) => {
      if (!item || typeof item !== 'object') return null;
      const prompt =
        (item as Record<string, unknown>).question ??
        (item as Record<string, unknown>).prompt ??
        (item as Record<string, unknown>).message;
      return typeof prompt === 'string' && prompt.trim().length > 0 ? prompt.trim() : null;
    }),
  ]
    .filter((item): item is string => Boolean(item))
    .filter((item, index, array) => array.indexOf(item) === index);

  return items.slice(0, 4);
}

const rSevColor = (sev: string) => sev === 'Critical' ? 'Critical' : sev === 'Warning' ? 'Warning' : 'Info';
const rSevBadgeBg  = { Critical: 'rgba(248,81,73,0.1)', Warning: 'rgba(210,153,34,0.12)', Info: 'rgba(88,166,255,0.1)' } as const;
const rSevBadgeBdr = { Critical: 'rgba(248,81,73,0.22)', Warning: 'rgba(210,153,34,0.25)', Info: 'rgba(88,166,255,0.22)' } as const;
const rSevBadgeTxt = { Critical: T.red, Warning: T.amber, Info: T.blue } as const;

type CheckerView = 'upload' | 'results';

type CheckerTracking = {
  sessionId: string;
  inquiryId: string;
};

type ItineraryCheckerState = {
  view: CheckerView;
  analysis: RunStatusResponse | null;
  analysisError: string | null;
  isAnalyzing: boolean;
  tracking: CheckerTracking | null;
  lastRetentionConsent: boolean;
  submittedText: string | null;
  editDraft: string | null;
};

type ItineraryCheckerAction =
  | { type: 'analysisStarted' }
  | { type: 'analysisSucceeded'; analysis: RunStatusResponse; tracking: CheckerTracking; retentionConsent: boolean; submittedText: string }
  | { type: 'analysisFailed'; message: string }
  | { type: 'resetToUpload'; edit?: boolean };

const initialItineraryCheckerState: ItineraryCheckerState = {
  view: 'upload',
  analysis: null,
  analysisError: null,
  isAnalyzing: false,
  tracking: null,
  lastRetentionConsent: false,
  submittedText: null,
  editDraft: null,
};

function itineraryCheckerReducer(
  state: ItineraryCheckerState,
  action: ItineraryCheckerAction,
): ItineraryCheckerState {
  switch (action.type) {
    case 'analysisStarted':
      return {
        ...state,
        analysisError: null,
        isAnalyzing: true,
      };
    case 'analysisSucceeded':
      return {
        ...state,
        analysis: action.analysis,
        tracking: action.tracking,
        submittedText: action.submittedText,
        lastRetentionConsent: action.retentionConsent,
        analysisError: null,
        isAnalyzing: false,
        view: 'results',
      };
    case 'analysisFailed':
      return {
        ...state,
        analysisError: action.message,
        isAnalyzing: false,
      };
    case 'resetToUpload':
      return {
        ...state,
        editDraft: action.edit ? state.submittedText : null,
        submittedText: null,
        analysis: null,
        analysisError: null,
        view: 'upload',
      };
    default:
      return state;
  }
}

type ResultSummaryItem = { l: string; v: string };
type ManageBusyState = 'export' | 'delete' | null;
type RevisionOutcome = 'revised' | 'no_change' | 'rejected';

function ResultsHeaderGrid({
  tripSummary,
  liveChecks,
          clarificationItems,
          manageMessage,
  manageBusy,
  tripId,
  onExport,
  onDelete,
  onReportRevision,
  storageCopy,
  hasScopedQuestion,
}: {
  tripSummary: ResultSummaryItem[];
  liveChecks?: Record<string, any>;
  clarificationItems: string[];
  manageMessage: string | null;
  manageBusy: ManageBusyState;
  tripId: string | null;
  onExport: () => Promise<void>;
  onDelete: () => Promise<void>;
  onReportRevision: (revisionOutcome: RevisionOutcome) => Promise<void>;
  storageCopy: string;
  hasScopedQuestion?: boolean;
}) {
  const handleExport = onExport;
  const handleDelete = onDelete;
  const handleReportRevision = onReportRevision;
  const summary = hasScopedQuestion ? tripSummary.filter(({ l, v }) =>
    !(l === 'Signal' && v.startsWith('Next inputs needed:'))
    && !(l === 'Booking stage' && v.toLowerCase() === 'nothing booked'),
  ) : tripSummary;
  return (
    <>
      <div style={{ marginBottom: 24 }}>
          {/* Trip summary + saved-data management */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {(!hasScopedQuestion || summary.length > 0) && (
            <div style={{ padding: '18px 20px', borderRadius: 16, background: T.surface, border: `1px solid ${T.b0}`, flex: 1 }}>
              <div style={{ fontSize: 12, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.1em', color: T.t3, marginBottom: 12 }}>
                Trip Summary (Extracted)
              </div>
              <div className='itinerary-stagger' style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: 10 }}>
                {(summary.length > 0 ? summary : [{ l: 'Status', v: 'We couldn’t confidently identify the key trip details.' }]).map(f => (
                  <div key={f.l}>
                    <div style={{ fontSize: 12, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.07em', color: T.t3 }}>{f.l}</div>
                    <div style={{ fontSize: 12.5, color: T.t1, marginTop: 2, fontFamily: T.fMono }}>{f.v}</div>
                  </div>
                ))}
              </div>
            </div>
            )}

            {liveChecks ? (
              <div style={{ padding: '16px 18px', borderRadius: 14, background: 'rgba(57,208,216,0.04)', border: '1px solid rgba(57,208,216,0.16)' }}>
                <div style={{ fontSize: 13, fontWeight: 600, color: T.t1, marginBottom: 3 }}>Destination evidence</div>
                <div style={{ fontSize: 12, color: T.t2, marginBottom: 10 }}>
                  {String(liveChecks.destination ?? 'Destination')}
                  {typeof liveChecks.climate?.precipitation_mm_avg === 'number' ? ` · ${liveChecks.climate.precipitation_mm_avg} mm average rain` : ''}
                  {typeof liveChecks.climate?.wind_kmh_avg === 'number' ? ` · ${liveChecks.climate.wind_kmh_avg} km/h average wind` : ''}
                </div>
                <div style={{ fontSize: 12, color: T.t3, marginBottom: 10 }}>
                  {typeof liveChecks.current_conditions?.current?.temperature_c === 'number' ? (
                    <>
                      Current weather: {String(liveChecks.current_conditions.current.temperature_c)}°C now
                      {liveChecks.current_conditions.current?.apparent_temperature_c != null
                        ? `, feels like ${String(liveChecks.current_conditions.current.apparent_temperature_c)}°C`
                        : ''}
                      {liveChecks.current_conditions.current?.wind_kmh != null
                        ? `, wind ${String(liveChecks.current_conditions.current.wind_kmh)} km/h`
                        : ''}
                    </>
                  ) : (
                    'Current weather signal unavailable'
                  )}
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {Array.isArray(liveChecks.signals) && liveChecks.signals.length > 0 ? (
                    <div style={{ fontSize: 12, color: T.cyan, lineHeight: 1.5 }}>
                      Source signals are available for this destination.
                    </div>
                  ) : null}
                  {(Array.isArray(liveChecks.soft_blockers) ? liveChecks.soft_blockers : []).slice(0, 2).map((item: string) => (
                    <div key={item} style={{ fontSize: 12, color: T.t1, lineHeight: 1.5 }}>
                      • {item}
                    </div>
                  ))}
                  {(Array.isArray(liveChecks.hard_blockers) ? liveChecks.hard_blockers : []).slice(0, 1).map((item: string) => (
                    <div key={item} style={{ fontSize: 12, color: T.red, lineHeight: 1.5 }}>
                      • {item}
                    </div>
                  ))}
                </div>
              </div>
            ) : null}

            {clarificationItems.length > 0 ? (
              <div style={{ padding: '16px 18px', borderRadius: 14, background: 'rgba(255,193,122,0.05)', border: '1px solid rgba(255,193,122,0.18)' }}>
                <div style={{ fontSize: 13, fontWeight: 600, color: T.t1, marginBottom: 6 }}>What to clarify next</div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {clarificationItems.map((item) => (
                    <div key={item} style={{ fontSize: 12, color: T.t2, lineHeight: 1.5 }}>
                      • {item}
                    </div>
                  ))}
                </div>
              </div>
            ) : null}

            <div style={{ padding: '16px 18px', borderRadius: 14, background: 'rgba(57,208,216,0.04)', border: '1px solid rgba(57,208,216,0.16)' }}>
              <div style={{ fontSize: 13, fontWeight: 600, color: T.t1, marginBottom: 3 }}>Manage your saved data</div>
              <div style={{ fontSize: 12, color: T.t2, marginBottom: 10 }}>
                {storageCopy}
              </div>
              {manageMessage ? (
                <div role='status' style={{ fontSize: 12, color: T.t2, marginBottom: 10 }}>{manageMessage}</div>
              ) : null}
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                <button
                  onClick={handleExport}
                  disabled={!tripId || manageBusy !== null}
                  style={primaryButtonStyle(Boolean(tripId && manageBusy === null))}
                >
                  {manageBusy === 'export' ? 'Exporting…' : 'Download my saved report'}
                </button>
                <button
                  onClick={handleDelete}
                  disabled={!tripId || manageBusy !== null}
                  style={{
                    ...sectionButtonStyle('secondary'),
                    height: 34,
                    color: T.red,
                    border: '1px solid rgba(248,81,73,0.24)',
                    cursor: tripId && manageBusy === null ? 'pointer' : 'not-allowed',
                  }}
                >
                  {manageBusy === 'delete' ? 'Deleting…' : 'Delete saved data'}
                </button>
              </div>
              <div style={{ marginTop: 10, fontSize: 12, color: T.t3 }}>
                Did your advisor revise after seeing this report?
              </div>
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 8 }}>
                <button
                  onClick={() => void handleReportRevision('revised')}
                  style={revisionButtonStyle(T.green, 'rgba(63,185,80,0.12)', '1px solid rgba(63,185,80,0.24)')}
                >
                  Yes, revised
                </button>
                <button
                  onClick={() => void handleReportRevision('no_change')}
                  style={revisionButtonStyle(T.amber, 'rgba(210,153,34,0.12)', '1px solid rgba(210,153,34,0.24)')}
                >
                  No change
                </button>
                <button
                  onClick={() => void handleReportRevision('rejected')}
                  style={revisionButtonStyle(T.red, 'rgba(248,81,73,0.12)', '1px solid rgba(248,81,73,0.24)')}
                >
                  Rejected
                </button>
              </div>
              <div style={{ fontSize: 12, color: T.t3, marginTop: 8 }}>
                Reference: {tripId ?? 'being generated'}
              </div>
            </div>
          </div>
        </div>
    </>
  );
}

function ResultsFindingsSection({
  blockerItems,
  analysis,
  needsDetails,
  sourceFindings,
  hasScopedResult,
}: {
  sourceFindings: string[];
  blockerItems: string[];
  needsDetails: boolean;
  hasScopedResult?: boolean;
  analysis?: RunStatusResponse | null;
}) {
  // Disagree is per-report UI feedback only (honest label below) — it is not
  // emitted as telemetry and does not feed the corpus until a server-side
  // escrow exists (WOBS P3).
  const [disputed, setDisputed] = useState<Record<string, boolean>>({});
  const packet = (analysis?.packet ?? null) as Record<string, any> | null;
  const entityChecks = Array.isArray(packet?.public_checker_entity_checks)
    ? (packet!.public_checker_entity_checks as Array<Record<string, any>>)
    : [];
  if ((hasScopedResult || sourceFindings.length > 0) && !blockerItems.length && !entityChecks.length) return null;

  return (
    <>
      {/* Findings — first object on the page (Manifest: pins before numbers) */}
        <div className='itinerary-stagger' style={{ marginBottom: 24 }}>
          <h2 style={{ fontSize: 16, fontWeight: 650, color: T.t1, marginBottom: 12 }}>Findings to review</h2>
          {blockerItems.length > 0 ? (
            <div className='itinerary-stagger' style={{ display: 'grid', gap: 10 }}>
              {blockerItems.map((item) => {
                const severity = analysis?.hard_blockers?.includes(item) ? 'Critical' : 'Warning';
                const c = rSevColor(severity) as keyof typeof rSevBadgeTxt;
                const key = `${severity}-${item.slice(0, 30)}`;
                const isDisputed = Boolean(disputed[key]);
                return (
                  <div key={key} style={{
                    ...severityCardStyle(
                      severity === 'Critical' ? 'rgba(248,81,73,0.06)' : 'rgba(210,153,34,0.06)',
                      severity === 'Critical' ? 'rgba(248,81,73,0.2)' : 'rgba(210,153,34,0.2)',
                    ),
                    gap: 14,
                  }}>
                    <span style={{
                      ...severityBadgeStyle(c, true),
                      color: rSevBadgeTxt[c],
                      background: rSevBadgeBg[c],
                      border: `1px solid ${rSevBadgeBdr[c]}`,
                    }}>
                      {severity}
                    </span>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: 12.5, fontWeight: 600, color: T.t1, lineHeight: 1.55 }}>
                        {formatTravelerBlockerItem(item, sourceFindings)}
                      </div>
                      {isDisputed ? (
                        <div style={{ fontSize: 11.5, color: T.t3, marginTop: 4 }}>
                          Noted for this report — you flagged this finding for review.
                        </div>
                      ) : null}
                    </div>
                    <button
                      type='button'
                      onClick={() => {
                        setDisputed((state) => ({ ...state, [key]: !state[key] }));
                        if (!isDisputed && analysis?.trip_id) {
                          // Second-Opinion Escrow v0: best-effort, quarantined server-side.
                          void api.post('/api/public-checker/disputes', {
                            trip_id: analysis.trip_id,
                            finding_text: item.slice(0, 500),
                            verdict: 'disagree',
                          }).catch(() => undefined);
                        }
                      }}
                      style={{
                        alignSelf: 'center',
                        fontSize: 11,
                        color: isDisputed ? T.t3 : T.t2,
                        background: 'none',
                        border: `1px solid ${T.b0}`,
                        borderRadius: 999,
                        padding: '4px 10px',
                        cursor: 'pointer',
                        whiteSpace: 'nowrap',
                      }}
                    >
                      {isDisputed ? 'Undo feedback' : 'Question this finding'}
                    </button>
                  </div>
                );
              })}
            </div>
          ) : hasScopedResult || sourceFindings.length > 0 || entityChecks.length > 0 ? null : (
            <div style={{
              padding: '14px 16px', borderRadius: 12,
              background: 'rgba(88,166,255,0.05)', border: '1px solid rgba(88,166,255,0.15)',
              fontSize: 12, color: T.t2, lineHeight: 1.55,
            }}>
              {needsDetails ? 'There is too little information to draw a conclusion for all checks.' : 'This report has no specific findings. Confirm booking details with the relevant provider.'}
            </div>
          )}

          {entityChecks.length > 0 ? (
            <div style={{ marginTop: 14 }}>
              <div style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.1em', color: T.t3, marginBottom: 8 }}>Place checks — advisory</div>
              <div style={{ display: 'grid', gap: 8 }}>
                {entityChecks.map((check, index) => {
                  const verified = check.status === 'verified';
                  const notFound = check.status === 'not_found';
                  const outcome = verified ? 'Public record found'
                    : notFound ? 'No public record'
                    : check.reason === 'source_unavailable' ? 'Source unavailable'
                    : check.reason === 'lodging_match_uncertain' ? 'Lodging match uncertain' : 'Unable to verify';
                  return (
                    <div key={`${check.name}-${index}`} style={{
                      padding: '10px 14px', borderRadius: 10,
                      background: verified ? 'rgba(88,166,255,0.05)' : 'rgba(210,153,34,0.05)',
                      border: `1px solid ${verified ? 'rgba(88,166,255,0.15)' : 'rgba(210,153,34,0.18)'}`,
                      fontSize: 12, color: notFound ? T.t1 : T.t2, lineHeight: 1.5,
                    }}>
                      <span style={{
                        fontSize: 10, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em',
                        color: verified ? T.blue : T.amber, marginRight: 8,
                      }}>
                        {outcome}
                      </span>
                      {String(check.message ?? '')}
                    </div>
                  );
                })}
              </div>
            </div>
          ) : null}

          <div style={{ marginTop: 16, fontSize: 11.5, color: T.t3, lineHeight: 1.55 }}>
            {CHECKER_DISCLAIMER}
          </div>
        </div>
    </>
  );
}

type MarketplaceMatch = {
  agency_id: string;
  display_name: string;
  response_sla_hours?: number;
  blurb: string;
  match_reasons: string[];
};

// Matched-choice close (WOBS P2): user picks from the matched set, or joins
// the demand-capture waitlist when no agency matches yet. The consent moment
// (explicit checkbox + send) is the qualification — nothing is sent without it.
function RouteRequestPanel({
  tripId,
  agencyContext,
}: {
  tripId: string | null;
  agencyContext?: AgencyBrandingContext | null;
}) {
  const [phase, setPhase] = useState<'idle' | 'loading' | 'matched' | 'waitlist' | 'sent' | 'error'>(
    agencyContext ? 'matched' : 'idle'
  );
  const [matches, setMatches] = useState<MarketplaceMatch[]>(
    agencyContext
      ? [
          {
            agency_id: agencyContext.agency_id,
            display_name: agencyContext.display_name,
            response_sla_hours: agencyContext.response_sla_hours,
            blurb: agencyContext.blurb ?? 'Your dedicated travel agency advisor.',
            match_reasons: agencyContext.places_covered?.length
              ? [`Listed coverage: ${agencyContext.places_covered.join(', ')}`]
              : ['Dedicated Advisor'],
          },
        ]
      : []
  );
  const [pickedAgency, setPickedAgency] = useState<string | null>(agencyContext?.agency_id ?? null);
  const [contact, setContact] = useState('');
  const [consented, setConsented] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sending, setSending] = useState(false);
  const [leadStatus, setLeadStatus] = useState<string | null>(null);

  const findMatches = async () => {
    if (!tripId) return;
    setPhase('loading');
    setError(null);
    try {
      const res = await api.post<{ trip_id: string; matches: MarketplaceMatch[] }>(
        '/api/public-checker/matches',
        { trip_id: tripId },
      );
      setMatches(res.matches ?? []);
      setPhase((res.matches ?? []).length > 0 ? 'matched' : 'waitlist');
    } catch {
      setError('Could not load matches right now.');
      setPhase('error');
    }
  };

  const sendBrief = async () => {
    if (!tripId || !consented || !pickedAgency || !contact.trim() || sending) return;
    setError(null);
    setSending(true);
    try {
      const receipt = await api.post<{ ok: boolean; lead_id: string; status: string }>('/api/public-checker/route-request', {
        trip_id: tripId,
        contact,
        agency_id: pickedAgency,
        consent: true,
      }, { retry: 0 });
      if (!receipt.ok || !receipt.lead_id) throw new Error('Missing request receipt');
      setLeadStatus(receipt.status);
      setPhase('sent');
    } catch {
      setError('Could not confirm your request. Please try again.');
    } finally {
      setSending(false);
    }
  };

  if (phase === 'sent') {
    return (
      <div role='status' style={{ fontSize: 12.5, color: T.t1, lineHeight: 1.55 }}>
        {leadStatus === 'routed' ? 'Request recorded for the selected agency. Delivery has not been confirmed.' : 'Request recorded. No agency delivery has been confirmed.'}
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      {phase === 'idle' || phase === 'error' ? (
        <button
          onClick={() => void findMatches()}
          disabled={!tripId}
          style={{
            ...primaryButtonStyle(Boolean(tripId)),
            boxShadow: '0 4px 14px rgba(57,208,216,0.25)',
          }}
        >
          Check advisor availability
        </button>
      ) : null}

      {phase === 'loading' ? <div style={{ fontSize: 12, color: T.t3 }}>Matching your plan…</div> : null}

      {phase === 'matched' ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          <div style={{ fontSize: 12, color: T.t2 }}>{agencyContext ? 'Agency linked to this checker' : 'Agencies matched to your plan — pick who receives it:'}</div>
          {matches.map((match) => (
            <button
              key={match.agency_id}
              aria-pressed={pickedAgency === match.agency_id}
              onClick={() => { setPickedAgency(match.agency_id); setConsented(false); }}
              style={{
                textAlign: 'left', padding: '10px 14px', borderRadius: 10,
                background: pickedAgency === match.agency_id ? 'rgba(57,208,216,0.1)' : T.elevated,
                border: `1px solid ${pickedAgency === match.agency_id ? 'rgba(57,208,216,0.4)' : T.b0}`,
                cursor: 'pointer',
              }}
            >
              <div style={{ fontSize: 12.5, fontWeight: 600, color: T.t1 }}>
                {match.display_name}
                {match.response_sla_hours != null ? <span style={{ fontSize: 12, color: T.t2, marginLeft: 8 }}>Listed response time: {match.response_sla_hours}h</span> : null}
              </div>
              {match.match_reasons.length > 0 ? (
                <div style={{ fontSize: 11.5, color: T.t3, marginTop: 2 }}>
                  {match.match_reasons.join(' · ')}
                </div>
              ) : null}
            </button>
          ))}
        </div>
      ) : null}

      {phase === 'waitlist' ? (
        <div style={{ fontSize: 12, color: T.t2, lineHeight: 1.55 }}>
          No matching advisor is available for this trip. You can still keep the report or take it to an advisor you know.
        </div>
      ) : null}

      {phase === 'matched' && pickedAgency ? (
        <>
          <label htmlFor='checker-advisor-contact' style={{ color: T.t2 }}>Email or phone</label>
          <input
            id='checker-advisor-contact'
            value={contact}
            onChange={(e) => setContact(e.target.value)}
            placeholder='Email or phone for the agency to reach you'
            style={{
              padding: '9px 12px', borderRadius: 10, background: T.elevated,
              border: `1px solid ${T.b0}`, color: T.t1, fontSize: 12, fontFamily: T.fBody,
            }}
          />
          <label style={{ display: 'flex', alignItems: 'flex-start', gap: 8, fontSize: 11.5, color: T.t2, lineHeight: 1.45 }}>
            <input type='checkbox' checked={consented} onChange={(e) => setConsented(e.target.checked)} style={{ marginTop: 2, accentColor: T.cyan }} />
            <span>
              {pickedAgency
                ? `Send my brief and contact to ${matches.find((m) => m.agency_id === pickedAgency)?.display_name ?? 'the selected agency'}. Findings only — your raw documents stay private.`
                : null}
            </span>
          </label>
          <button
            onClick={() => void sendBrief()}
            disabled={sending || !consented || contact.trim().length === 0}
            style={primaryButtonStyle(Boolean(consented && contact.trim()))}
          >
            {sending ? 'Recording request…' : 'Request advisor follow-up'}
          </button>
        </>
      ) : null}

      {error ? <div role='alert' style={{ fontSize: 12, color: T.red }}>{error}</div> : null}
    </div>
  );
}

function ResultsConversionSection({
  onShareReport,
  shareText,
  shareStatus,
  tripId,
  agencyContext,
}: {
  onShareReport: () => Promise<void>;
  shareText: string;
  shareStatus: string | null;
  tripId: string | null;
  agencyContext?: AgencyBrandingContext | null;
}) {
  const handleShareReport = onShareReport;
  return (
    <>
      {/* Soft agency conversion — matched choice + user-owned brief (WOBS P2) */}
        <div className='itinerary-reveal' style={S.conversionCard}>
          <div style={{ marginBottom: 12 }}>
            <div style={{ fontSize: 14, fontWeight: 600, color: T.t1, marginBottom: 4 }}>
              {agencyContext ? `Have ${agencyContext.display_name} handle your trip` : 'Want a professional to handle this?'}
            </div>
            <div style={{ fontSize: 12, color: T.t2, lineHeight: 1.55, maxWidth: '50ch' }}>
              {agencyContext
                ? 'Request follow-up from the agency using your report and contact details.'
                : 'Check whether an advisor is available, or take your findings to one you already trust.'}
            </div>
          </div>
          <RouteRequestPanel tripId={tripId} agencyContext={agencyContext} />
          <details style={{ marginTop: 16 }}>
            <summary style={{ color: T.t1, cursor: 'pointer', paddingBlock: 8 }}>Share findings summary</summary>
            <p style={{ color: T.t2, whiteSpace: 'pre-wrap', overflowWrap: 'anywhere', fontSize: 13 }}>{shareText}</p>
            <button type='button' onClick={handleShareReport} style={S.shareReportButton}>Share this summary</button>
            {shareStatus ? <p role='status' style={{ color: T.t2, marginBlock: 8 }}>{shareStatus}</p> : null}
          </details>
        </div>
    </>
  );
}

// ── Results view ──────────────────────────────────────────────────────────────
function ResultsView({
  rootRef,
  onReset,
  onEdit,
  onRecheck,
  submittedText,
  rechecking,
  recheckError,
  onEmitEvent,
  tracking,
  analysis,
  agencyContext,
  lastRetentionConsent = false,
}: {
  rootRef: RefObject<HTMLDivElement | null>;
  onReset: () => void;
  onEdit: () => void;
  onRecheck: (text: string) => Promise<void>;
  submittedText: string;
  rechecking: boolean;
  recheckError: string | null;
  onEmitEvent: (eventName: string, properties: Record<string, unknown>, tripId?: string | null) => Promise<void>;
  tracking: { sessionId: string; inquiryId: string } | null;
  analysis?: RunStatusResponse | null;
  lastRetentionConsent?: boolean;
  agencyContext?: AgencyBrandingContext | null;
}) {
  const [manageMessage, setManageMessage] = useState<string | null>(null);
  const [revisedText, setRevisedText] = useState(submittedText);
  const [showRevision, setShowRevision] = useState(false);
  const revisionInput = useRef<HTMLTextAreaElement>(null);
  useEffect(() => { if (showRevision) revisionInput.current?.focus(); }, [showRevision]);
  const [shareStatus, setShareStatus] = useState<string | null>(null);
  const [manageBusy, setManageBusy] = useState<'export' | 'delete' | null>(null);
  const [reportStorage, setReportStorage] = useState<PublicCheckerReportStorageSummary>({
    loading: false,
    retentionConsented: null,
    hasStoredUpload: false,
    uploadFileName: null,
  });

  const tripId = analysis?.trip_id ?? null;
  const accessToken = analysis?.access_token ?? null;
  const liveChecks = ((analysis?.packet as Record<string, any> | null | undefined)?.public_checker_live_checks as Record<string, any> | undefined) ?? undefined;
  const tripSummary = buildTravelerTripSummary(analysis ?? null, liveChecks);
  const clarificationItems = buildTravelerClarifications(analysis ?? null);
  const reportHeading = useRef<HTMLHeadingElement>(null);
  useEffect(() => {
    reportHeading.current?.focus();
  }, []);
  const sourceFindings = [liveChecks?.hard_blockers, liveChecks?.soft_blockers]
    .flatMap((items) => Array.isArray(items) ? items.filter((item): item is string => typeof item === 'string') : []);
  const needsDetails = analysis?.state === 'blocked'
    || analysis?.decision_state === 'ASK_FOLLOWUP'
    || analysis?.decision_state === 'STOP_NEEDS_REVIEW'
    || clarificationItems.length > 0;
  const blockerItems = [
    ...(Array.isArray(analysis?.hard_blockers) ? analysis?.hard_blockers : []),
    ...(Array.isArray(analysis?.soft_blockers) ? analysis?.soft_blockers : []),
  ];

  const genericIntakeBlockers = new Set(['incomplete_intake', 'extraction_quality']);
  const concreteBlocker = blockerItems.find((item) => !genericIntakeBlockers.has(item));
  const firstAction = concreteBlocker ? formatTravelerBlockerItem(concreteBlocker, sourceFindings) : clarificationItems[0];
  const submittedFacts = analysis?.packet as Record<string, unknown> | null | undefined;
  const itineraryFindings = getItineraryFeasibilityFindings(submittedFacts);
  const feasibilityEvidence = getItineraryFeasibilityEvidence(submittedFacts);
  const detailCount = itineraryFindings.length + Number(Boolean(feasibilityEvidence.question));
  const scopedHeading = detailCount === 1 ? '1 itinerary detail to confirm' : `${detailCount} itinerary details to confirm`;
  const returnPromptAtEditor = feasibilityEvidence.returnDatePending && detailCount > 0 && !concreteBlocker;
  const outboundOnly = getPacketFactValue(submittedFacts, 'date_confidence') === 'outbound_only'
    && !getPacketFactValue(submittedFacts, 'date_end');
  const keyTripFacts = [
    buildSummaryFactItem(submittedFacts ?? null, 'origin_city', 'Departure city'),
    buildSummaryFactItem(submittedFacts ?? null, 'destination', 'Destination')
      ?? buildSummaryFactItem(submittedFacts ?? null, 'destination_candidates',
        getPacketFactValue(submittedFacts, 'destination_status') === 'definite' ? 'Destination' : 'Destination candidates'),
    buildSummaryFactItem(submittedFacts ?? null, 'date_window', outboundOnly ? 'Outbound date' : 'Travel window'),
    buildSummaryFactItem(submittedFacts ?? null, 'party_size', 'Travelers'),
  ].filter((item): item is ResultSummaryItem => Boolean(item));


  useEffect(() => {
    if (!tripId || !accessToken) return;

    let isMounted = true;

    const loadReportData = async () => {
      try {
        if (!isMounted) return;
        setReportStorage((state) => ({ ...state, loading: true }));
        const response = await fetch(`/api/public-checker/trip/${encodeURIComponent(tripId)}`, {
          headers: { Authorization: `Bearer ${accessToken}` },
        });
        if (!response.ok) throw new Error('Could not read report metadata');
        const payload = await response.json();
        if (!isMounted) return;
        setReportStorage({
          ...pickPublicCheckerReportStorage(payload),
          loading: false,
        });
      } catch {
        if (!isMounted) return;
        setReportStorage((state) => ({ ...state, loading: false }));
      }
    };

    void loadReportData();

    return () => {
      isMounted = false;
    };
  }, [tripId, accessToken]);

  const storageCopy = reportStorage.loading
    ? 'Checking what we saved…'
    : reportStorage.retentionConsented === true
      ? reportStorage.hasStoredUpload
        ? `Report and upload were saved${reportStorage.uploadFileName ? ` (file: ${reportStorage.uploadFileName})` : ''}.`
        : 'Report was saved with your consent.'
      : reportStorage.retentionConsented === false
        ? 'You did not opt in to saving your original input. The derived report may still be available.'
        : lastRetentionConsent
          ? 'You requested that we save this report. We couldn’t confirm what was saved.'
          : 'You requested a one-time check. We couldn’t confirm the storage status.';

  const handleExport = async () => {
    if (!tripId || !accessToken) return;
    setManageBusy('export');
    setManageMessage(null);
    try {
      const response = await fetch(`/api/public-checker/trip/${encodeURIComponent(tripId)}/export`, {
        headers: { Authorization: `Bearer ${accessToken}` },
      });
      if (!response.ok) throw new Error('Export failed');
      const payload = await response.json();
      const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `waypoint-checker-${tripId}.json`;
      link.click();
      URL.revokeObjectURL(url);
      setManageMessage('Export downloaded.');
    } catch {
      setManageMessage('Could not export this report.');
    } finally {
      setManageBusy(null);
    }
  };

  const handleDelete = async () => {
    if (!tripId || !accessToken) return;
    const confirmed = window.confirm('Delete this saved itinerary report and its stored upload data?');
    if (!confirmed) return;
    setManageBusy('delete');
    setManageMessage(null);
    try {
      const response = await fetch(`/api/public-checker/trip/${encodeURIComponent(tripId)}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${accessToken}` },
      });
      if (!response.ok) throw new Error('Delete failed');
      setManageMessage('Deleted.');
      onReset();
    } catch {
      setManageMessage('Could not delete this report.');
    } finally {
      setManageBusy(null);
    }
  };

  const shareUrl = agencyContext?.slug
    ? `https://waypoint.app/check/${agencyContext.slug}`
    : 'https://waypoint.app/itinerary-checker';
  const reportBlockers = detailCount > 0
    ? blockerItems.filter((item) => !genericIntakeBlockers.has(item))
    : blockerItems;
  const shareFindings = [
    ...reportBlockers.slice(0, 3).map((item) => formatTravelerBlockerItem(item, sourceFindings)),
    ...(feasibilityEvidence.question ? [
      `${feasibilityEvidence.question}${feasibilityEvidence.ask ? `\n  Ask ${feasibilityEvidence.ask}` : ''}`,
    ] : []),
    ...itineraryFindings.map(({ title, message, source, ask }) =>
      `${title}: ${message}${ask ? `\n  Ask ${ask}` : ''}${source ? `\n  ${source.label}: ${source.url}` : ''}`,
    ),
  ];
  const findingsPreview = shareFindings.length > 0
    ? `\nKey findings:\n${[...new Set(shareFindings)].map((finding) => `• ${finding}`).join('\n')}`
      : '';
  const shareText = `Waypoint itinerary findings${findingsPreview}\n\n${shareUrl}`;
  const handleShareReport = async () => {
    const packetId = tripId ?? `packet_${Date.now().toString(36)}`;
    setShareStatus(null);
    const shareChannel = typeof navigator.share === 'function' ? 'other' : 'copy_paste';
    try {
      if (shareChannel === 'other') {
        await navigator.share({ title: 'Waypoint itinerary findings', text: shareText });
      } else {
        if (!await safeWriteClipboardText(shareText)) throw new Error('Clipboard unavailable');
      }
      setShareStatus(shareChannel === 'other' ? 'Findings shared.' : 'Findings copied.');
    } catch (error) {
      if (!(error instanceof DOMException && error.name === 'AbortError')) {
        setShareStatus('Could not share findings. Please try again.');
      }
      return;
    }
    if (!tracking) return;

    await onEmitEvent(
      'action_packet_shared',
      {
        packet_id: packetId,
        share_channel: shareChannel,
        had_manual_edits: false,
      },
      tripId,
    );
  };

  const handleReportRevision = async (revisionOutcome: 'revised' | 'no_change' | 'rejected') => {
    if (!tracking) return;
    await onEmitEvent(
      'agency_revision_reported',
      {
        revision_report_mode: 'self_report',
        revision_outcome: revisionOutcome,
        time_from_share_ms: null,
      },
      tripId,
    );
    setManageMessage(
      revisionOutcome === 'revised'
        ? 'Marked as revised. Thanks for closing the loop.'
        : revisionOutcome === 'no_change'
          ? 'Marked as no change.'
          : 'Marked as rejected.',
    );
  };

  return (
    <div ref={rootRef} style={S.resultsRoot}>
      <WedgeHeader agencyContext={agencyContext} />
      <div style={{ flex: 1, overflowWrap: 'anywhere', padding: '24px clamp(16px, 4vw, 32px)', maxWidth: 1080, margin: '0 auto', width: '100%', boxSizing: 'border-box' }}>
        <nav aria-label='Itinerary actions' style={{ display: 'flex', flexWrap: 'wrap', gap: '0 16px' }}>
          <button onClick={onEdit} disabled={rechecking} style={{ ...S.backButton, color: T.t2 }}>← Edit itinerary</button>
          <button onClick={onReset} disabled={rechecking} style={{ ...S.backButton, color: T.t2 }}>Check another itinerary</button>
        </nav>
        <header style={{ padding: '24px clamp(16px, 4vw, 32px)', background: T.surface, border: `1px solid ${T.b0}`, borderRadius: 16, marginBottom: 24 }}>
          <p style={{ color: T.cyan, fontSize: 13, margin: '0 0 8px' }}>Itinerary report</p>
          <h1 ref={reportHeading} tabIndex={-1} style={{ color: T.t1, fontSize: 'clamp(28px, 5vw, 42px)', lineHeight: 1.12, margin: '0 0 12px' }}>
            {concreteBlocker ? 'Review these findings before booking' : detailCount > 0 ? scopedHeading : needsDetails ? 'Your check needs more details' : 'Your itinerary check'}
          </h1>
          {(!returnPromptAtEditor || feasibilityEvidence.question) && <p style={{ color: T.t2, lineHeight: 1.6, margin: 0 }}>
            {(concreteBlocker ? firstAction : feasibilityEvidence.question ?? firstAction) ?? (needsDetails
              ? 'Check that your itinerary includes the key trip details, then run the check again.'
              : 'Review the checks we could run and confirm booking details with your providers.')}
          </p>}
          {concreteBlocker && feasibilityEvidence.question && (
            <p style={{ color: T.t1, margin: '8px 0 0' }}>{feasibilityEvidence.question}</p>
          )}
          {feasibilityEvidence.context && (
            <p style={{ color: T.t2, margin: '8px 0 0' }}>{feasibilityEvidence.context}</p>
          )}
          {feasibilityEvidence.question && feasibilityEvidence.ask && (
            <p style={{ color: T.t2, margin: '8px 0 0' }}>Ask {feasibilityEvidence.ask}</p>
          )}
          {feasibilityEvidence.question && feasibilityEvidence.source && (
            <a href={feasibilityEvidence.source.url} style={{ color: T.cyan, textDecoration: 'underline' }}>{feasibilityEvidence.source.label}</a>
          )}
          {keyTripFacts.length > 0 ? (
            <dl aria-label='What we read from your itinerary' style={{ display: 'flex', flexWrap: 'wrap', gap: '10px 24px', margin: '16px 0 0' }}>
              {keyTripFacts.map(({ l, v }) => (
                <div key={l}>
                  <dt style={{ color: T.t2, fontSize: 12 }}>{l}</dt>
                  <dd style={{ color: T.t1, margin: '3px 0 0', fontSize: 14 }}>{v}</dd>
                </div>
              ))}
            </dl>
          ) : null}
          {itineraryFindings.map(({ id, title, message, source, ask }) => (
            <aside key={id} aria-labelledby={`checker-${id}`} style={{ marginTop: 16, padding: 16, borderRadius: 12, border: '1px solid rgba(210,153,34,0.45)', background: 'rgba(210,153,34,0.08)' }}>
              <h2 id={`checker-${id}`} style={{ margin: '0 0 6px', color: T.amber, fontSize: 16, fontWeight: 650 }}>{title}</h2>
              <p style={{ margin: 0, color: T.t1, lineHeight: 1.6 }}>{message}</p>
              {ask && <p style={{ color: T.t2, margin: '8px 0 0' }}>Ask {ask}</p>}
              {source ? <a href={source.url} style={{ display: 'inline-block', marginTop: 8, color: T.cyan, textDecoration: 'underline' }}>{source.label}</a> : null}
            </aside>
          ))}
          {returnPromptAtEditor && <p style={{ color: T.t2, margin: '16px 0 0' }}>{clarificationItems[0]}</p>}
          {submittedText ? (
            <div style={{ marginTop: 16 }}>
              <button type='button' aria-expanded={showRevision} aria-controls='checker-revision' disabled={rechecking}
                onClick={() => setShowRevision((open) => !open)} style={sectionButtonStyle('secondary')}>
                {showRevision ? 'Hide itinerary editor' : 'Correct or add trip details'}
              </button>
              {showRevision ? (
                <form id='checker-revision' onSubmit={(event) => { event.preventDefault(); void onRecheck(revisedText); }}
                  style={{ marginTop: 16, display: 'grid', gap: 10, justifyItems: 'start' }}>
                  <label htmlFor='checker-revision-text' style={{ color: T.t1 }}>Your submitted itinerary</label>
                  <textarea id='checker-revision-text' ref={revisionInput} value={revisedText} disabled={rechecking}
                    onChange={(event) => setRevisedText(event.target.value)} rows={5}
                    style={{ width: '100%', minWidth: 0, boxSizing: 'border-box', padding: 12, background: T.input, color: T.t1, border: `1px solid ${T.b1}`, borderRadius: 10 }} />
                  {rechecking ? <p role='status' style={{ color: T.t2, margin: 0 }}>Checking your updated itinerary…</p> : null}
                  {recheckError ? <p role='alert' style={{ color: T.red, margin: 0 }}>{recheckError} The report below is from your previous check.</p> : null}
                  <button type='submit' disabled={rechecking || revisedText.trim().length < 10 || revisedText.trim() === submittedText.trim()}
                    style={sectionButtonStyle('primary')}>
                    {rechecking ? 'Checking again…' : 'Recheck my itinerary'}
                  </button>
                </form>
              ) : null}
            </div>
          ) : null}
        </header>
        <ResultsFindingsSection blockerItems={clarificationItems.length || feasibilityEvidence.question ? blockerItems.filter((item) => !genericIntakeBlockers.has(item)) : blockerItems} analysis={analysis} needsDetails={needsDetails} sourceFindings={sourceFindings} hasScopedResult={Boolean(feasibilityEvidence.question) || itineraryFindings.length > 0} />
        <ResultsHeaderGrid
          tripSummary={tripSummary}
          liveChecks={liveChecks}
          clarificationItems={feasibilityEvidence.question || (feasibilityEvidence.returnDatePending && !concreteBlocker) ? [] : clarificationItems}
          manageMessage={manageMessage}
          manageBusy={manageBusy}
          tripId={accessToken ? tripId : null}
          onExport={handleExport}
          onDelete={handleDelete}
          onReportRevision={handleReportRevision}
          storageCopy={storageCopy}
          hasScopedQuestion={Boolean(feasibilityEvidence.question)}
        />
        <ResultsConversionSection
          onShareReport={handleShareReport}
          shareText={shareText}
          shareStatus={shareStatus}
          tripId={tripId}
          agencyContext={agencyContext}
        />
        <div style={{ paddingBottom: 48 }} />
      </div>
    </div>
  );
}// ── Page ──────────────────────────────────────────────────────────────────────

const CHECKER_DISABLED = process.env.NEXT_PUBLIC_PUBLIC_CHECKER_DISABLED === '1';

function CheckerMaintenanceNotice() {
  return (
    <div style={{
      minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center',
      background: T.canvas, fontFamily: T.fBody, color: T.t1, padding: 24,
    }}>
      <div style={{
        maxWidth: 460, padding: '32px 28px', borderRadius: 16,
        background: T.surface, border: `1px solid ${T.b0}`, textAlign: 'center',
      }}>
        <div style={{ fontSize: 18, fontWeight: 600, marginBottom: 8 }}>Checker is temporarily offline</div>
        <div style={{ fontSize: 13.5, color: T.t2, lineHeight: 1.6 }}>
          The public itinerary check is paused for maintenance. Please try again later.
        </div>
      </div>
    </div>
  );
}

export default function ItineraryCheckerPage({
  agencyContext,
}: {
  agencyContext?: AgencyBrandingContext | null;
} = {}) {
  if (CHECKER_DISABLED) {
    return <CheckerMaintenanceNotice />;
  }
  return <CheckerPage agencyContext={agencyContext} />;
}

function CheckerPage({
  agencyContext,
}: {
  agencyContext?: AgencyBrandingContext | null;
} = {}) {
  const [state, dispatch] = useReducer(itineraryCheckerReducer, initialItineraryCheckerState);
  const { view, analysis, analysisError, isAnalyzing, tracking, lastRetentionConsent, editDraft, submittedText } = state;
  const motionRootRef = useRef<HTMLDivElement>(null);
  const sessionIdRef = useRef<string>(makeTrackingId('sess'));

  const emitProductBEvent = async (
    eventName: string,
    properties: Record<string, unknown>,
    tripId?: string | null,
    context?: { sessionId: string; inquiryId: string } | null,
  ) => {
    const eventContext = context ?? tracking;
    if (!eventContext) return;
    const payload: ProductBEventPayload = {
      event_name: eventName,
      session_id: eventContext.sessionId,
      inquiry_id: eventContext.inquiryId,
      trip_id: tripId ?? analysis?.trip_id ?? null,
      actor_type: 'traveler',
      actor_id: null,
      workspace_id: agencyContext?.agency_id ?? 'waypoint-hq',
      channel: 'web',
      locale: typeof navigator !== 'undefined' ? navigator.language : null,
      currency: null,
      properties,
    };

    try {
      await api.post('/api/public-checker/events', payload);
    } catch {
      // Telemetry should not block traveler flow.
    }
  };

  useEffect(() => {
    const root = motionRootRef.current;
    if (!root || window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      return;
    }

    const ctx = gsap.context(() => {
      if (view === 'upload') {
        gsap.to('.itinerary-glow', {
          scale: 1.08,
          opacity: 0.9,
          duration: 4.8,
          repeat: -1,
          yoyo: true,
          ease: 'sine.inOut',
        });

        gsap.to('.itinerary-orb', {
          y: -14,
          x: 8,
          duration: 5.2,
          repeat: -1,
          yoyo: true,
          ease: 'sine.inOut',
          stagger: 0.12,
        });

        gsap.to('.itinerary-ring', {
          rotate: 360,
          duration: 28,
          repeat: -1,
          ease: 'none',
        });

        gsap.to('.itinerary-scanline', {
          yPercent: 220,
          duration: 3.2,
          repeat: -1,
          ease: 'none',
        });

        gsap.to('.itinerary-plane', {
          x: 18,
          y: -12,
          rotate: 10,
          duration: 4.4,
          repeat: -1,
          yoyo: true,
          ease: 'sine.inOut',
        });

        gsap.to('.itinerary-stamp', {
          rotate: 4,
          scale: 1.02,
          duration: 2.8,
          repeat: -1,
          yoyo: true,
          ease: 'sine.inOut',
        });

        gsap.to('.itinerary-route-pip circle', {
          scale: 1.18,
          transformOrigin: '50% 50%',
          duration: 1.6,
          repeat: -1,
          yoyo: true,
          ease: 'sine.inOut',
          stagger: 0.18,
        });
      }

      gsap.fromTo('.itinerary-reveal', {
        y: 20,
        opacity: 0,
      }, {
        y: 0,
        opacity: 1,
        duration: 0.8,
        ease: 'power3.out',
      });

      gsap.fromTo('.itinerary-stagger > *', {
        y: 14,
        opacity: 0,
      }, {
        y: 0,
        opacity: 1,
        duration: 0.7,
        ease: 'power2.out',
        stagger: 0.12,
      });
    }, root);

    return () => ctx.revert();
  }, [view]);

  const handleAnalyze = async (plan: string, sourcePayload?: Record<string, unknown>, declaredPlanSource?: 'self' | 'ai' | 'vendor') => {
    const trimmed = plan.trim();
    if (trimmed.length < 10) {
      return;
    }

    const retentionConsent = Boolean(sourcePayload?.retention_consent);
    const inferredContext = inferTravelContext(trimmed);
    const nextTracking = {
      sessionId: sessionIdRef.current,
      inquiryId: makeTrackingId('inq'),
    };

    dispatch({ type: 'analysisStarted' });
    if (analysis?.trip_id && tracking?.inquiryId) {
      void emitProductBEvent(
        're_audit_started',
        {
          prior_packet_id: analysis.trip_id,
          revision_input_mode: sourcePayload?.kind === 'file_upload' ? 'upload' : sourcePayload?.kind === 'mixed' ? 'mixed' : 'freeform_text',
        },
        analysis.trip_id,
        tracking,
      );
    }

    const storedPayload = retentionConsent
      ? {
          ...(sourcePayload ?? {}),
          trip_context: inferredContext,
          session_id: nextTracking.sessionId,
          inquiry_id: nextTracking.inquiryId,
        }
      : {
          ...(sourcePayload ?? {}),
          session_id: nextTracking.sessionId,
          inquiry_id: nextTracking.inquiryId,
        };

    try {
      const result = await api.post<RunStatusResponse>('/api/public-checker/run', {
        raw_note: trimmed,
        owner_note: '',
        itinerary_text: trimmed,
        structured_json: { source_payload: storedPayload, ...inferredContext },
        retention_consent: retentionConsent,
        declared_plan_source: declaredPlanSource ?? null,
        // RDA_EX07 rec-3 (FND-0399): a traveler who declared the trip already
        // booked submits under stage="booking" so the booking-critical
        // visa/passport checks fire; everyone else runs the discovery checks.
        stage: stageForSubmittedPlan(Boolean(sourcePayload?.already_booked)),
        operating_mode: 'normal_intake',
        strict_leakage: true,
        scenario_id: null,
      }, { retry: 0 });
      if (!result?.run_id || !['completed', 'blocked'].includes(result.state)
        || result.error_message || !result.packet || typeof result.packet !== 'object'
        || Array.isArray(result.packet) || Object.keys(result.packet).length === 0) {
        throw new Error('The checker returned no usable report.');
      }
      dispatch({ type: 'analysisSucceeded', analysis: result, tracking: nextTracking, submittedText: trimmed, retentionConsent });
    } catch {
      dispatch({
        type: 'analysisFailed',
        message: 'We couldn’t check your itinerary right now. Your input is still here. Try again in a moment.',
      });
    }
  };

  const handleAnalyzeFile = async (file: File, retentionConsent: boolean, declaredPlanSource?: 'self' | 'ai' | 'vendor', alreadyBooked?: boolean) => {
    const extracted = await extractTextFromFile(file);
    const trimmed = extracted.trim();
    if (trimmed.length < 10) {
      throw new Error('Could not extract enough readable text from that file.');
    }
    const extractionMethod = file.type.startsWith('image/')
      ? 'ocr'
      : file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf')
        ? 'pdf_text'
        : 'direct_text';
    const uploadedFile: Record<string, unknown> = {
      file_name: file.name,
      mime_type: file.type || 'application/octet-stream',
      file_size: file.size,
      extraction_method: extractionMethod,
      extracted_text: trimmed,
    };

    if (retentionConsent) {
      uploadedFile.content_base64 = await fileToBase64(file);
    }

    const inferredContext = inferTravelContext(trimmed);
    await handleAnalyze(trimmed, {
      kind: 'file_upload',
      uploaded_file: uploadedFile,
      retention_consent: retentionConsent,
      already_booked: alreadyBooked ?? false,
      trip_context: inferredContext,
    }, declaredPlanSource);
  };

  if (view === 'results') {
    return (
      <ResultsView
        key={analysis?.run_id}
        submittedText={submittedText ?? ''}
        rechecking={isAnalyzing}
        recheckError={analysisError}
        onRecheck={(text) => handleAnalyze(text, { kind: 'paste', source: 'typed', retention_consent: false, already_booked: analysis?.stage === 'booking' })}
        rootRef={motionRootRef}
        onReset={() => dispatch({ type: 'resetToUpload' })}
        onEdit={() => dispatch({ type: 'resetToUpload', edit: true })}
        onEmitEvent={emitProductBEvent}
        tracking={tracking}
        analysis={analysis}
        lastRetentionConsent={lastRetentionConsent}
        agencyContext={agencyContext}
      />
    );
  }

  return (
    <UploadView
      rootRef={motionRootRef}
      onAnalyze={handleAnalyze}
      onAnalyzeFile={handleAnalyzeFile}
      isBusy={isAnalyzing}
      analysisError={analysisError}
      initialDraft={editDraft}
      agencyContext={agencyContext}
    />
  );
}
