'use client';

import Link from 'next/link';
import { useEffect, useState, useRef, type RefObject, DragEvent } from 'react';
import gsap from 'gsap';
import { useSpineRun } from '@/hooks/useSpineRun';
import type { RunStatusResponse } from '@/types/spine';
import {
  Activity, ArrowRight, Check, Clock, DollarSign,
  FileCheck, Globe, Mail, MapPin, Shield, Star, Upload,
} from 'lucide-react';

// ── Design tokens ─────────────────────────────────────────────────────────────
const T = {
  canvas:   '#07090b',
  surface:  '#0d1117',
  elevated: '#161b22',
  input:    '#111318',
  t1: '#e6edf3',
  t2: '#8b949e',
  t3: '#6e7681',
  t4: '#484f58',
  blue:   '#58a6ff',
  cyan:   '#39d0d8',
  amber:  '#d29922',
  green:  '#3fb950',
  red:    '#f85149',
  purple: '#a371f7',
  b0: '#21262d',
  b1: '#30363d',
  fDisplay: "'Outfit', system-ui, sans-serif",
  fBody:    "'Inter', system-ui, sans-serif",
  fMono:    "'JetBrains Mono', monospace",
};

// ── Header ────────────────────────────────────────────────────────────────────
function WedgeHeader() {
  return (
    <header style={{
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      padding: '14px 32px', borderBottom: `1px solid ${T.b0}`,
      background: 'rgba(10,13,17,0.9)', backdropFilter: 'blur(12px)',
      position: 'sticky', top: 0, zIndex: 50, flexShrink: 0,
    }}>
      <Link href='/' style={{ display: 'flex', alignItems: 'center', gap: 9, textDecoration: 'none' }}>
        <div style={{
          width: 28, height: 28, borderRadius: 8,
          background: 'linear-gradient(135deg, #2563eb, #39d0d8)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          color: 'white', flexShrink: 0,
        }}>
          <MapPin size={14} />
        </div>
        <div className='itinerary-reveal'>
          <div style={{ fontSize: 13, fontWeight: 700, color: T.t1, letterSpacing: '-0.01em', fontFamily: T.fBody }}>Waypoint</div>
          <div style={{ fontSize: 10, color: T.t3, lineHeight: 1, fontFamily: T.fBody }}>Itinerary Checker</div>
        </div>
      </Link>
      <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
        <span style={{ fontSize: 12, color: T.t3, fontFamily: T.fBody }}>Free · No account required · 60 seconds</span>
        <Link href='/signup' style={{
          display: 'inline-flex', alignItems: 'center', gap: 6,
          height: 34, padding: '0 14px', borderRadius: 999,
          fontSize: 12, fontWeight: 600, fontFamily: T.fBody,
          background: 'rgba(15,17,21,0.72)', color: '#c9d1d9',
          border: '1px solid rgba(168,179,193,0.14)', textDecoration: 'none',
        }}>
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
    pdfjs.GlobalWorkerOptions.workerSrc = new URL(
      'pdfjs-dist/build/pdf.worker.min.mjs',
      import.meta.url,
    ).toString();

    const data = await file.arrayBuffer();
    const doc = await pdfjs.getDocument({ data }).promise;
    const pageTexts: string[] = [];

    for (let pageNumber = 1; pageNumber <= doc.numPages; pageNumber += 1) {
      const page = await doc.getPage(pageNumber);
      const content = await page.getTextContent();
      const text = (content.items as Array<{ str?: string }>)
        .map((item) => item.str ?? '')
        .filter(Boolean)
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

// ── Upload card (reused in hero) ──────────────────────────────────────────────
function UploadCard({
  onAnalyze,
  onAnalyzeFile,
  onFallbackResults,
  isBusy,
}: {
  onAnalyze: (plan: string, sourcePayload?: Record<string, unknown>) => void;
  onAnalyzeFile: (file: File, retentionConsent: boolean) => Promise<void>;
  onFallbackResults: () => void;
  isBusy: boolean;
}) {
  const [activeTab, setActiveTab] = useState<'file' | 'paste' | 'screenshot'>('file');
  const [dragging, setDragging] = useState(false);
  const [text, setText] = useState('');
  const [isProcessingFile, setIsProcessingFile] = useState(false);
  const [fileError, setFileError] = useState<string | null>(null);
  const [retentionConsent, setRetentionConsent] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  const tabs: { key: 'file' | 'paste' | 'screenshot'; label: string }[] = [
    { key: 'file',       label: 'Upload file'     },
    { key: 'paste',      label: 'Paste itinerary' },
    { key: 'screenshot', label: 'Screenshot'      },
  ];

  const handleDragOver = (e: DragEvent) => { e.preventDefault(); setDragging(true); };
  const handleDragLeave = () => setDragging(false);
  const handleFile = async (file: File) => {
    setFileError(null);
    setIsProcessingFile(true);
    try {
      await onAnalyzeFile(file, retentionConsent);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Could not read that file.';
      setFileError(message);
    } finally {
      setIsProcessingFile(false);
    }
  };

  const handleDrop = (e: DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (!file) {
      onFallbackResults();
      return;
    }
    void handleFile(file);
  };

  return (
    <div style={{ width: '100%', position: 'relative' }}>
      <div aria-hidden style={{
        position: 'absolute', inset: '-16px -16px 0', pointerEvents: 'none',
        borderRadius: 24, overflow: 'hidden',
      }}>
        <div className='itinerary-glow' style={{
          position: 'absolute', inset: '14% 10% auto', height: 180,
          background: 'radial-gradient(circle, rgba(57,208,216,0.16) 0%, rgba(57,208,216,0.03) 38%, transparent 72%)',
          filter: 'blur(8px)',
        }} />
        <div className='itinerary-ring' style={{
          position: 'absolute', right: -40, top: -36, width: 180, height: 180,
          borderRadius: '50%',
          background: 'conic-gradient(from 0deg, rgba(122,185,255,0.14), rgba(57,208,216,0.04), rgba(163,113,247,0.14), rgba(57,208,216,0.04), rgba(122,185,255,0.14))',
          filter: 'blur(1px)',
          opacity: 0.8,
        }} />
        <div className='itinerary-scanline' style={{
          position: 'absolute', left: 18, right: 18, top: 18, height: 2,
          borderRadius: 999,
          background: 'linear-gradient(90deg, transparent, rgba(57,208,216,0.92), rgba(122,185,255,0.18), transparent)',
          boxShadow: '0 0 18px rgba(57,208,216,0.6)',
        }} />
      </div>
      {/* Mode tabs */}
      <div style={{
        display: 'flex', gap: 4, marginBottom: 12,
        background: T.surface, borderRadius: 10, padding: 4,
        border: `1px solid ${T.b0}`,
      }}>
        {tabs.map(tab => (
          <button key={tab.key} onClick={() => setActiveTab(tab.key)} style={{
            flex: 1, padding: '7px 0', borderRadius: 7, border: 'none', cursor: 'pointer',
            fontSize: 12, fontWeight: activeTab === tab.key ? 600 : 400,
            background: activeTab === tab.key ? T.elevated : 'transparent',
            color: activeTab === tab.key ? T.t1 : T.t2,
            fontFamily: T.fBody, transition: 'all 150ms',
          }}>
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === 'paste' ? (
        <div style={{ borderRadius: 14, border: `1px solid ${T.b1}`, background: T.surface, overflow: 'hidden' }}>
          <textarea
            value={text}
            onChange={e => setText(e.target.value)}
            placeholder={'Paste your day-by-day plan here…\n\nDay 1: Arrive LAX → London Heathrow (AA100, dep 10:30)\nDay 2: London — check-in The Connaught, walking tour\nDay 3: Paris Eurostar (07:55) — Musée d\'Orsay, Seine dinner\n…'}
            style={{
              width: '100%', minHeight: 180, padding: '16px 18px',
              background: 'none', border: 'none', outline: 'none', resize: 'none',
              color: T.t1, fontSize: 13, fontFamily: T.fMono, lineHeight: 1.65,
              boxSizing: 'border-box',
            }}
          />
          <div style={{
            padding: '10px 16px', borderTop: `1px solid ${T.b0}`,
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          }}>
            <span style={{ fontSize: 11, color: T.t4 }}>
              {text.length > 0 ? `${text.length} characters` : 'Messy inputs work fine'}
            </span>
            <button onClick={() => onAnalyze(text, { kind: 'paste', source: 'typed', retention_consent: retentionConsent })} disabled={text.length < 10 || isBusy || isProcessingFile} style={{
              display: 'inline-flex', alignItems: 'center', gap: 7,
              height: 34, padding: '0 14px', borderRadius: 999,
              fontSize: 12, fontWeight: 600, fontFamily: T.fBody,
              background: text.length >= 10 && !isBusy
                ? 'linear-gradient(135deg, #7ab9ff 0%, #57e0ef 50%, #39d0d8 100%)'
                : T.elevated,
              color: text.length >= 10 && !isBusy ? '#071018' : T.t3,
              border: 'none', cursor: text.length >= 10 && !isBusy ? 'pointer' : 'not-allowed',
              boxShadow: text.length >= 10 && !isBusy ? '0 8px 24px rgba(57,208,216,0.3)' : 'none',
              transition: 'all 160ms',
            }}>
              {isBusy ? 'Scoring…' : 'Score My Itinerary'} <ArrowRight size={13} />
            </button>
          </div>
        </div>
      ) : (
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileRef.current?.click()}
          style={{
            borderRadius: 14,
            border: `2px dashed ${dragging ? T.cyan : T.b1}`,
            background: dragging ? 'rgba(57,208,216,0.04)' : T.surface,
            padding: '44px 24px', textAlign: 'center',
            cursor: 'pointer', transition: 'all 200ms',
          }}
        >
          <div style={{
            width: 52, height: 52, borderRadius: 14,
            background: 'rgba(88,166,255,0.1)', border: '1px solid rgba(88,166,255,0.2)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            margin: '0 auto 14px', color: T.blue,
          }}>
            <Upload size={22} strokeWidth={1.5} />
          </div>
          <div style={{ fontSize: 15, fontWeight: 600, color: T.t1, marginBottom: 5 }}>
            {activeTab === 'screenshot' ? 'Drop your screenshot here' : 'Drop your PDF here'}
          </div>
          <div style={{ fontSize: 12, color: T.t3, marginBottom: 20 }}>
            {activeTab === 'screenshot' ? 'JPG, PNG, or WEBP up to 25 MB' : 'PDF, JPG, PNG, or .txt up to 25 MB'}
          </div>
          <div style={{
            padding: '0 16px 14px',
            display: 'flex',
            alignItems: 'flex-start',
            gap: 10,
          }}>
            <input
              type='checkbox'
              checked={retentionConsent}
              onChange={(e) => setRetentionConsent(e.target.checked)}
              style={{ marginTop: 3, accentColor: T.cyan }}
            />
            <div style={{ fontSize: 11.5, color: T.t2, lineHeight: 1.45 }}>
              Store my upload, extracted text, and score for product improvement and future training.
              I can turn this off for a one-time analysis.
            </div>
          </div>
          <button
            onClick={e => { e.stopPropagation(); onFallbackResults(); }}
            disabled={isBusy || isProcessingFile}
            style={{
              display: 'inline-flex', alignItems: 'center', gap: 7,
              height: 42, padding: '0 20px', borderRadius: 999,
              fontSize: 13, fontWeight: 600, fontFamily: T.fBody,
              background: isBusy || isProcessingFile
                ? T.elevated
                : 'linear-gradient(135deg, #7ab9ff 0%, #57e0ef 50%, #39d0d8 100%)',
              color: isBusy || isProcessingFile ? T.t3 : '#071018',
              border: 'none', cursor: isBusy || isProcessingFile ? 'not-allowed' : 'pointer',
              boxShadow: isBusy || isProcessingFile ? 'none' : '0 8px 24px rgba(57,208,216,0.3), inset 0 1px 0 rgba(255,255,255,0.38)',
            }}
          >
            {isProcessingFile ? 'Reading file…' : 'Score my itinerary'}
          </button>
          <input
            ref={fileRef}
            type='file'
            accept='.pdf,.jpg,.jpeg,.png,.txt,.webp'
            style={{ display: 'none' }}
            onChange={async (e) => {
              const file = e.target.files?.[0];
              if (!file) {
                return;
              }
              const input = e.currentTarget;
              await handleFile(file);
              input.value = '';
            }}
          />
        </div>
      )}

      {fileError ? (
        <div style={{
          marginTop: 10, padding: '10px 12px', borderRadius: 10,
          border: '1px solid rgba(248,81,73,0.22)', background: 'rgba(248,81,73,0.08)',
          color: '#ffb4ae', fontSize: 12, lineHeight: 1.45,
        }}>
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
            <span style={{ fontSize: 11, color: T.t4 }}>{label}</span>
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

// ── Sample findings data ──────────────────────────────────────────────────────
const SAMPLE_FINDINGS = [
  {
    sev: 'Critical', color: T.red,
    bg: 'rgba(248,81,73,0.06)', border: 'rgba(248,81,73,0.2)',
    label: 'LAX layover may be too tight',
    body: '47-minute connection with international customs clearance required. Standard minimum is 90 min.',
  },
  {
    sev: 'Warning', color: T.amber,
    bg: 'rgba(210,153,34,0.06)', border: 'rgba(210,153,34,0.2)',
    label: 'Day 4 is heavily over-packed',
    body: '3 distant sites + dinner reservation. Real-world slack is under 30 min if anything runs long.',
  },
  {
    sev: 'Warning', color: T.amber,
    bg: 'rgba(210,153,34,0.06)', border: 'rgba(210,153,34,0.2)',
    label: 'No travel insurance detected',
    body: 'Nothing in the itinerary mentions coverage. Confirm before final payment.',
  },
  {
    sev: 'Info', color: T.blue,
    bg: 'rgba(88,166,255,0.05)', border: 'rgba(88,166,255,0.15)',
    label: 'Schengen visa status not confirmed',
    body: 'Trip includes Paris + Rome. Confirm passport validity — 6 months beyond return date required.',
  },
];

const sevBadgeBg  = { Critical: 'rgba(248,81,73,0.1)', Warning: 'rgba(210,153,34,0.12)', Info: 'rgba(88,166,255,0.1)' } as const;
const sevBadgeBdr = { Critical: 'rgba(248,81,73,0.22)', Warning: 'rgba(210,153,34,0.25)', Info: 'rgba(88,166,255,0.22)' } as const;
const sevBadgeTxt = { Critical: T.red, Warning: T.amber, Info: T.blue } as const;

// ── Testimonials ──────────────────────────────────────────────────────────────
const TESTIMONIALS = [
  {
    quote: 'Found a 52-minute connection I completely missed. That alone was worth the 60 seconds.',
    name: 'Sarah K.',
    role: 'Solo traveler, Japan trip 2025',
    color: T.cyan,
  },
  {
    quote: 'I\'m a 20-year travel veteran and it still caught a visa issue my agent didn\'t flag.',
    name: 'Marcus T.',
    role: 'Frequent business traveler',
    color: T.blue,
  },
  {
    quote: 'Shared the report with my advisor. She said it was the most useful pre-trip brief she\'d seen.',
    name: 'Priya N.',
    role: 'Family trip, Italy 2025',
    color: T.purple,
  },
];

// ── Upload view (landing + tool) ──────────────────────────────────────────────
function UploadView({
  rootRef,
  onAnalyze,
  onAnalyzeFile,
  onFallbackResults,
  isBusy,
}: {
  rootRef: RefObject<HTMLDivElement | null>;
  onAnalyze: (plan: string, sourcePayload?: Record<string, unknown>) => void;
  onAnalyzeFile: (file: File, retentionConsent: boolean) => Promise<void>;
  onFallbackResults: () => void;
  isBusy: boolean;
}) {
  return (
    <div ref={rootRef} style={{
      background: T.canvas, fontFamily: T.fBody, color: T.t1,
    }}>
      <WedgeHeader />

      {/* Background radial glow */}
      <div style={{
        position: 'fixed', inset: 0, pointerEvents: 'none',
        backgroundImage: `
          radial-gradient(circle at 50% 25%, rgba(88,166,255,0.10) 0%, transparent 54%),
          radial-gradient(circle at 20% 15%, rgba(57,208,216,0.05) 0%, transparent 22%),
          linear-gradient(rgba(255,255,255,0.025) 1px, transparent 1px),
          linear-gradient(90deg, rgba(255,255,255,0.025) 1px, transparent 1px)
        `,
        backgroundSize: 'auto, auto, 52px 52px, 52px 52px',
        backgroundPosition: 'center top, center top, center center, center center',
        zIndex: 0,
      }} />

      {/* ── HERO: split 2-col ── */}
      <section style={{
        position: 'relative', zIndex: 1,
        maxWidth: 1140, margin: '0 auto',
        padding: '72px 40px 80px',
        display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 64,
        alignItems: 'center',
      }}>
        {/* Left: headline + context */}
        <div>
          {/* Kicker */}
          <span style={{
            display: 'inline-flex', alignItems: 'center', gap: 7,
            padding: '5px 12px', borderRadius: 999, marginBottom: 24,
            color: '#d8eef0', fontSize: 10.5, letterSpacing: '0.13em',
            textTransform: 'uppercase', fontFamily: T.fBody, fontWeight: 600,
            border: '1px solid rgba(57,208,216,0.22)', background: 'rgba(7,22,26,0.8)',
          }}>
            <span style={{ width: 5, height: 5, borderRadius: '50%', background: '#39d0d8', boxShadow: '0 0 5px #39d0d8', flexShrink: 0 }} />
            Free itinerary ATS
          </span>

          <h1 style={{
            fontSize: 'clamp(36px, 4vw, 54px)', fontWeight: 900,
            lineHeight: 1.04, letterSpacing: '-0.04em',
            color: '#f5fbff', fontFamily: T.fDisplay, marginBottom: 20,
          }}>
            Bring your plan. Get it checked.
          </h1>

          <p style={{ fontSize: 16, lineHeight: 1.72, color: T.t2, maxWidth: '40ch', marginBottom: 32 }}>
            Upload an itinerary or paste a plan. Like an ATS for resumes, we score the one you already have,
            flag weak points, and suggest upgrades you can use yourself or share with your agent.
          </p>

          {/* Stats row */}
          <div className='itinerary-stagger' style={{ display: 'flex', gap: 32, flexWrap: 'wrap', marginBottom: 36 }}>
            {[
              { stat: '20,000+', label: 'itineraries analyzed' },
              { stat: '98%',     label: 'recommend to friends' },
              { stat: '4.8/5',   label: 'traveler rating' },
            ].map(s => (
              <div key={s.stat}>
                <div style={{ fontSize: 24, fontWeight: 800, color: T.t1, fontFamily: T.fDisplay, lineHeight: 1 }}>{s.stat}</div>
                <div style={{ fontSize: 11, color: T.t3, marginTop: 3 }}>{s.label}</div>
              </div>
            ))}
          </div>

          {/* Avatar stack */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{ display: 'flex' }}>
              {[T.blue, T.cyan, T.green, T.amber, T.purple].map((c, i) => (
                <div key={i} style={{
                  width: 26, height: 26, borderRadius: '50%', background: c,
                  marginLeft: i ? -8 : 0, border: `2px solid ${T.canvas}`,
                }} />
              ))}
            </div>
            <span style={{ fontSize: 12, color: T.t3 }}>Travelers checking in every day</span>
          </div>
        </div>

        {/* Right: upload card */}
        <div className='itinerary-reveal' style={{ position: 'relative' }}>
          <div aria-hidden className='itinerary-orb' style={{
            position: 'absolute', inset: '-18px -20px auto auto', width: 220, height: 220,
            borderRadius: '50%',
            background: 'radial-gradient(circle, rgba(122,185,255,0.12) 0%, rgba(57,208,216,0.08) 28%, rgba(163,113,247,0.06) 44%, transparent 70%)',
            filter: 'blur(6px)',
            pointerEvents: 'none',
          }} />
          <div aria-hidden className='itinerary-orb' style={{
            position: 'absolute', left: -18, bottom: 120, width: 120, height: 120,
            borderRadius: '50%',
            background: 'radial-gradient(circle, rgba(63,185,80,0.12) 0%, rgba(63,185,80,0.05) 34%, transparent 72%)',
            filter: 'blur(4px)',
            pointerEvents: 'none',
          }} />

          {[
            { text: 'Visa timing', top: '12%', left: '-2%' },
            { text: 'Pacing risk', top: '20%', right: '-4%' },
            { text: 'Fee watch', bottom: '24%', left: '3%' },
            { text: 'Advisor-ready', bottom: '12%', right: '5%' },
          ].map((chip) => (
            <div
              key={chip.text}
              aria-hidden
              className='itinerary-orb itinerary-chip'
              style={{
                position: 'absolute',
                top: chip.top,
                left: chip.left,
                right: chip.right,
                bottom: chip.bottom,
                width: 'fit-content',
                padding: '7px 11px',
                borderRadius: 999,
                border: '1px solid rgba(168,179,193,0.14)',
                background: 'rgba(10,13,17,0.78)',
                color: T.t1,
                fontSize: 11,
                fontWeight: 600,
                letterSpacing: '-0.01em',
                boxShadow: '0 10px 28px rgba(0,0,0,0.25)',
                backdropFilter: 'blur(10px)',
                transform: 'translateZ(0)',
                zIndex: 0,
                opacity: 0.95,
              }}
            >
              {chip.text}
            </div>
          ))}

          <UploadCard
            onAnalyze={onAnalyze}
            onAnalyzeFile={onAnalyzeFile}
            onFallbackResults={onFallbackResults}
            isBusy={isBusy}
          />

          {/* Score preview teaser */}
          <div style={{
            marginTop: 16, padding: '14px 16px', borderRadius: 12,
            background: 'rgba(210,153,34,0.06)', border: '1px solid rgba(210,153,34,0.2)',
            display: 'flex', alignItems: 'center', gap: 14,
          }}>
            <div style={{ position: 'relative', width: 52, height: 52, flexShrink: 0 }}>
              <svg width='52' height='52' viewBox='0 0 52 52' style={{ transform: 'rotate(-90deg)' }}>
                <circle cx='26' cy='26' r='20' fill='none' stroke={T.b0} strokeWidth='5' />
                <circle cx='26' cy='26' r='20' fill='none' stroke={T.amber} strokeWidth='5'
                  strokeDasharray={`${2 * Math.PI * 20 * 0.62} ${2 * Math.PI * 20}`}
                  strokeLinecap='round' />
              </svg>
              <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <span style={{ fontSize: 15, fontWeight: 900, color: T.t1, fontFamily: T.fDisplay }}>62</span>
              </div>
            </div>
            <div>
              <div style={{ fontSize: 12, fontWeight: 600, color: T.amber, marginBottom: 2 }}>Needs Attention</div>
              <div style={{ fontSize: 11, color: T.t2, lineHeight: 1.5 }}>Example report — your score depends on what your plan contains</div>
            </div>
          </div>
        </div>
      </section>

      {/* ── TRUST LOGOS ── */}
      <section style={{
        position: 'relative', zIndex: 1,
        borderTop: `1px solid ${T.b0}`, borderBottom: `1px solid ${T.b0}`,
        padding: '20px 40px',
      }}>
        <div style={{
          maxWidth: 1140, margin: '0 auto',
          display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 52, flexWrap: 'wrap',
        }}>
          <span style={{ fontSize: 10, fontWeight: 700, color: T.t4, letterSpacing: '0.12em', textTransform: 'uppercase', flexShrink: 0 }}>
            Trusted by travelers from
          </span>
          {['Virtuoso', 'ASTA', 'Signature', 'Ensemble', 'Travellers Choice'].map(name => (
            <span key={name} style={{
              fontSize: 13, fontWeight: 700, color: T.t3, letterSpacing: '-0.01em',
              fontFamily: T.fDisplay, opacity: 0.7,
            }}>{name}</span>
          ))}
        </div>
      </section>

      {/* ── WHAT WE CHECK ── */}
      <section style={{ position: 'relative', zIndex: 1, padding: '88px 40px' }}>
        <div style={{ maxWidth: 1140, margin: '0 auto' }}>
          <div style={{ textAlign: 'center', marginBottom: 52 }}>
            <div style={{
              display: 'inline-flex', alignItems: 'center', gap: 6,
              fontSize: 10, fontWeight: 700, letterSpacing: '0.14em', textTransform: 'uppercase',
              color: T.cyan, marginBottom: 14,
            }}>
              <FileCheck size={13} /> Six categories
            </div>
            <h2 style={{
              fontSize: 'clamp(28px, 3.5vw, 40px)', fontWeight: 800,
              letterSpacing: '-0.03em', color: T.t1, fontFamily: T.fDisplay, marginBottom: 14,
            }}>
              What we check
            </h2>
            <p style={{ fontSize: 15, color: T.t2, maxWidth: '46ch', margin: '0 auto', lineHeight: 1.65 }}>
              Every report covers six dimensions that travel agents and experienced travelers know to watch for.
            </p>
          </div>

          <div className='itinerary-stagger' style={{
            display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(230px, 1fr))', gap: 16,
          }}>
            {CHECKS.map(c => {
              const Icon = c.icon;
              return (
                <div key={c.label} style={{
                  padding: '24px 26px', borderRadius: 16,
                  background: T.surface, border: `1px solid ${T.b0}`,
                  transition: 'border-color 200ms',
                }}>
                  <div style={{
                    width: 40, height: 40, borderRadius: 10, marginBottom: 16,
                    background: `${c.color}18`, border: `1px solid ${c.color}30`,
                    display: 'flex', alignItems: 'center', justifyContent: 'center', color: c.color,
                  }}>
                    <Icon size={18} strokeWidth={1.8} />
                  </div>
                  <div style={{ fontSize: 14, fontWeight: 700, color: T.t1, marginBottom: 8 }}>{c.label}</div>
                  <div style={{ fontSize: 12.5, color: T.t2, lineHeight: 1.65 }}>{c.body}</div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* ── EXAMPLE FINDINGS ── */}
      <section style={{
        position: 'relative', zIndex: 1,
        padding: '0 40px 88px',
      }}>
        <div style={{ maxWidth: 1140, margin: '0 auto' }}>
          <div style={{
            display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 64, alignItems: 'start',
          }}>
            {/* Left: copy */}
            <div style={{ paddingTop: 8 }}>
              <div style={{
                fontSize: 10, fontWeight: 700, letterSpacing: '0.14em', textTransform: 'uppercase',
                color: T.amber, marginBottom: 16,
              }}>
                Example upgrade report
              </div>
              <h2 style={{
                fontSize: 'clamp(26px, 3vw, 38px)', fontWeight: 800,
                letterSpacing: '-0.03em', color: T.t1, fontFamily: T.fDisplay,
                marginBottom: 18, lineHeight: 1.1,
              }}>
                Real upgrades, not generic warnings
              </h2>
              <p style={{ fontSize: 15, color: T.t2, lineHeight: 1.7, marginBottom: 28, maxWidth: '38ch' }}>
                Every finding is specific to the plan you already have — the actual route, the exact dates, the specific travelers, and the most useful upgrade points for you or your agent.
              </p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                {[
                  { label: '1 Critical', desc: 'Must-fix before travel', color: T.red },
                  { label: '2 Warnings', desc: 'Should review with advisor', color: T.amber },
                  { label: '1 Info',     desc: 'Worth knowing before you go', color: T.blue },
                ].map(row => (
                  <div key={row.label} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <div style={{
                      width: 8, height: 8, borderRadius: '50%', background: row.color, flexShrink: 0,
                    }} />
                    <span style={{ fontSize: 13, fontWeight: 600, color: T.t1 }}>{row.label}</span>
                    <span style={{ fontSize: 12, color: T.t3 }}>{row.desc}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Right: findings cards */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {SAMPLE_FINDINGS.map(f => {
                const sev = f.sev as keyof typeof sevBadgeTxt;
                return (
                  <div key={f.label} style={{
                    padding: '14px 16px', borderRadius: 12,
                    background: f.bg, border: `1px solid ${f.border}`,
                    display: 'grid', gridTemplateColumns: 'auto 1fr', gap: 12, alignItems: 'flex-start',
                  }}>
                    <span style={{
                      display: 'inline-flex', alignItems: 'center',
                      padding: '2px 7px', borderRadius: 5, marginTop: 1,
                      fontSize: 10, fontWeight: 700, fontFamily: T.fMono,
                      textTransform: 'uppercase', letterSpacing: '0.04em',
                      color: sevBadgeTxt[sev], background: sevBadgeBg[sev], border: `1px solid ${sevBadgeBdr[sev]}`,
                      flexShrink: 0, whiteSpace: 'nowrap',
                    }}>
                      {f.sev}
                    </span>
                    <div>
                      <div style={{ fontSize: 13, fontWeight: 600, color: T.t1, marginBottom: 3 }}>{f.label}</div>
                      <div style={{ fontSize: 11.5, color: T.t2, lineHeight: 1.55 }}>{f.body}</div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </section>

      {/* ── SAMPLE BRIEF PREVIEW ── */}
      <section style={{
        position: 'relative', zIndex: 1,
        borderTop: `1px solid ${T.b0}`,
        padding: '88px 40px',
        background: T.surface,
      }}>
        <div style={{ maxWidth: 1140, margin: '0 auto' }}>
          <div style={{ textAlign: 'center', marginBottom: 48 }}>
            <div style={{
              fontSize: 10, fontWeight: 700, letterSpacing: '0.14em', textTransform: 'uppercase',
              color: T.blue, marginBottom: 14,
            }}>
              What you receive
            </div>
            <h2 style={{
              fontSize: 'clamp(26px, 3vw, 38px)', fontWeight: 800,
              letterSpacing: '-0.03em', color: T.t1, fontFamily: T.fDisplay, marginBottom: 14,
            }}>
              A structured brief your advisor can act on
            </h2>
            <p style={{ fontSize: 15, color: T.t2, maxWidth: '44ch', margin: '0 auto', lineHeight: 1.65 }}>
              Not a vague summary. A scored, categorized, advisor-ready document — shareable with one click.
            </p>
          </div>

          {/* Brief mockup */}
          <div style={{
            maxWidth: 780, margin: '0 auto',
            borderRadius: 20, border: `1px solid ${T.b1}`,
            background: T.canvas, overflow: 'hidden',
          }}>
            {/* Mockup chrome bar */}
            <div style={{
              padding: '12px 18px', borderBottom: `1px solid ${T.b0}`,
              background: T.elevated, display: 'flex', alignItems: 'center', gap: 8,
            }}>
              {['#f85149', '#d29922', '#3fb950'].map(c => (
                <div key={c} style={{ width: 10, height: 10, borderRadius: '50%', background: c }} />
              ))}
              <div style={{
                flex: 1, height: 22, borderRadius: 4, background: T.surface,
                margin: '0 12px', display: 'flex', alignItems: 'center', paddingLeft: 10,
              }}>
                <span style={{ fontSize: 11, color: T.t4, fontFamily: T.fMono }}>waypoint.travel/report/trip-a8k2f</span>
              </div>
            </div>

            {/* Brief content */}
            <div style={{ padding: '24px 28px', display: 'grid', gridTemplateColumns: 'auto 1fr', gap: 24, alignItems: 'start' }}>
              {/* Score block */}
              <div style={{
                padding: '18px 20px', borderRadius: 14, background: T.surface,
                border: `1px solid ${T.b0}`, textAlign: 'center', minWidth: 130,
              }}>
                <div style={{ fontSize: 9, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.1em', color: T.t4, marginBottom: 12 }}>Health Score</div>
                <div style={{ position: 'relative', width: 72, height: 72, margin: '0 auto 12px' }}>
                  <svg width='72' height='72' viewBox='0 0 72 72' style={{ transform: 'rotate(-90deg)' }}>
                    <circle cx='36' cy='36' r='28' fill='none' stroke={T.b0} strokeWidth='6' />
                    <circle cx='36' cy='36' r='28' fill='none' stroke={T.amber} strokeWidth='6'
                      strokeDasharray={`${2 * Math.PI * 28 * 0.62} ${2 * Math.PI * 28}`}
                      strokeLinecap='round' />
                  </svg>
                  <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                    <span style={{ fontSize: 22, fontWeight: 900, color: T.t1, fontFamily: T.fDisplay, lineHeight: 1 }}>62</span>
                    <span style={{ fontSize: 8, color: T.t3 }}>/100</span>
                  </div>
                </div>
                <div style={{ fontSize: 11, fontWeight: 600, color: T.amber }}>Needs Attention</div>
                <div style={{ display: 'flex', gap: 6, marginTop: 12, justifyContent: 'center' }}>
                  {[{ n: 1, c: T.red }, { n: 2, c: T.amber }, { n: 1, c: T.blue }].map((m, i) => (
                    <div key={i} style={{ textAlign: 'center' }}>
                      <div style={{ fontSize: 14, fontWeight: 800, color: m.c, fontFamily: T.fDisplay }}>{m.n}</div>
                      <div style={{ width: 6, height: 6, borderRadius: '50%', background: m.c, margin: '3px auto 0' }} />
                    </div>
                  ))}
                </div>
              </div>

              {/* Summary lines */}
              <div>
                <div style={{ fontSize: 14, fontWeight: 700, color: T.t1, marginBottom: 4 }}>Europe Summer 2025 — 16-Day Report</div>
                <div style={{ fontSize: 11, color: T.t3, marginBottom: 18 }}>Generated 2026-04-28 · LAX → LHR → CDG → FCO → LAX</div>

                {[
                  { label: 'Duration', value: '16 days · 5 segments · 4 hotels' },
                  { label: 'Travelers', value: '2 adults · no minors' },
                  { label: 'Insurance', value: 'Not detected — flag for discussion' },
                  { label: 'Visa', value: 'Schengen — verify 6-month validity' },
                ].map(row => (
                  <div key={row.label} style={{
                    display: 'flex', alignItems: 'baseline', gap: 10,
                    padding: '7px 0', borderBottom: `1px solid ${T.b0}`,
                  }}>
                    <span style={{ fontSize: 10, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.07em', color: T.t4, minWidth: 80 }}>{row.label}</span>
                    <span style={{ fontSize: 12, color: T.t2, fontFamily: T.fMono }}>{row.value}</span>
                  </div>
                ))}

                <div style={{ marginTop: 18, display: 'flex', gap: 8 }}>
                  <button style={{
                    display: 'inline-flex', alignItems: 'center', gap: 6,
                    height: 32, padding: '0 14px', borderRadius: 999,
                    fontSize: 11, fontWeight: 600, fontFamily: T.fBody,
                    background: 'linear-gradient(135deg, #7ab9ff 0%, #39d0d8 100%)',
                    color: '#071018', border: 'none', cursor: 'pointer',
                  }}>
                    Download PDF
                  </button>
                  <button style={{
                    display: 'inline-flex', alignItems: 'center', gap: 6,
                    height: 32, padding: '0 14px', borderRadius: 999,
                    fontSize: 11, fontWeight: 600, fontFamily: T.fBody,
                    background: 'transparent', color: T.t2,
                    border: `1px solid ${T.b1}`, cursor: 'pointer',
                  }}>
                    Share with advisor →
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── TESTIMONIALS ── */}
      <section style={{ position: 'relative', zIndex: 1, padding: '88px 40px' }}>
        <div style={{ maxWidth: 1140, margin: '0 auto' }}>
          <div style={{ textAlign: 'center', marginBottom: 48 }}>
            <h2 style={{
              fontSize: 'clamp(24px, 3vw, 36px)', fontWeight: 800,
              letterSpacing: '-0.03em', color: T.t1, fontFamily: T.fDisplay, marginBottom: 10,
            }}>
              What travelers say
            </h2>
            <p style={{ fontSize: 14, color: T.t3 }}>Real feedback from real itineraries</p>
          </div>

          <div className='itinerary-stagger' style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 20 }}>
            {TESTIMONIALS.map(t => (
              <div key={t.name} style={{
                padding: '24px 24px', borderRadius: 16,
                background: T.surface, border: `1px solid ${T.b0}`,
                borderTop: `2px solid ${t.color}`,
              }}>
                <div style={{ display: 'flex', marginBottom: 14, gap: 2 }}>
                  {'★★★★★'.split('').map((s, i) => (
                    <span key={i} style={{ color: T.amber, fontSize: 13 }}>{s}</span>
                  ))}
                </div>
                <p style={{ fontSize: 13.5, color: T.t1, lineHeight: 1.65, marginBottom: 18 }}>
                  &ldquo;{t.quote}&rdquo;
                </p>
                <div>
                  <div style={{ fontSize: 13, fontWeight: 600, color: T.t1 }}>{t.name}</div>
                  <div style={{ fontSize: 11, color: T.t3, marginTop: 2 }}>{t.role}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── FINAL CTA ── */}
      <section style={{
        position: 'relative', zIndex: 1,
        borderTop: `1px solid ${T.b0}`,
        padding: '88px 40px 96px',
        background: 'radial-gradient(circle at 50% 0%, rgba(57,208,216,0.07) 0%, transparent 60%)',
      }}>
        <div style={{ maxWidth: 640, margin: '0 auto', textAlign: 'center' }}>
          <span style={{
            display: 'inline-flex', alignItems: 'center', gap: 7,
            padding: '5px 12px', borderRadius: 999, marginBottom: 24,
            color: '#d8eef0', fontSize: 10.5, letterSpacing: '0.13em',
            textTransform: 'uppercase', fontFamily: T.fBody, fontWeight: 600,
            border: '1px solid rgba(57,208,216,0.22)', background: 'rgba(7,22,26,0.8)',
          }}>
            <span style={{ width: 5, height: 5, borderRadius: '50%', background: T.cyan, boxShadow: `0 0 5px ${T.cyan}`, flexShrink: 0 }} />
            Free · 60 seconds · No account
          </span>

          <h2 style={{
            fontSize: 'clamp(28px, 4vw, 46px)', fontWeight: 900,
            letterSpacing: '-0.04em', color: T.t1, fontFamily: T.fDisplay,
            marginBottom: 18, lineHeight: 1.05,
          }}>
            Ready to stress-test your itinerary?
          </h2>

          <p style={{ fontSize: 15, color: T.t2, lineHeight: 1.7, marginBottom: 36, maxWidth: '40ch', margin: '0 auto 36px' }}>
            60 seconds is all it takes. Upload now and know exactly what to fix before you book.
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 16 }}>
            <button
              onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
              style={{
                display: 'inline-flex', alignItems: 'center', gap: 8,
                height: 52, padding: '0 28px', borderRadius: 999,
                fontSize: 15, fontWeight: 700, fontFamily: T.fBody,
                background: 'linear-gradient(135deg, #7ab9ff 0%, #57e0ef 50%, #39d0d8 100%)',
                color: '#071018', border: 'none', cursor: 'pointer',
                boxShadow: '0 12px 32px rgba(57,208,216,0.35), inset 0 1px 0 rgba(255,255,255,0.38)',
              }}
            >
              Check my itinerary now <ArrowRight size={16} />
            </button>

            <div style={{ display: 'flex', alignItems: 'center', gap: 18, flexWrap: 'wrap', justifyContent: 'center' }}>
              {['No account needed', 'Results in 60 seconds', 'Private & secure'].map(label => (
                <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
                  <Check size={12} color={T.green} strokeWidth={2.5} />
                  <span style={{ fontSize: 11, color: T.t4 }}>{label}</span>
                </div>
              ))}
            </div>
          </div>

          <div style={{ marginTop: 48, paddingTop: 36, borderTop: `1px solid ${T.b0}`, fontSize: 12, color: T.t4 }}>
            Travel agent?{' '}
            <Link href='/signup' style={{ color: T.blue, textDecoration: 'none' }}>
              See Waypoint OS for agencies →
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}

// ── Results data ──────────────────────────────────────────────────────────────
function scoreFromAnalysis(analysis: RunStatusResponse | null): number {
  if (!analysis) return 62;

  const validation = analysis.validation as Record<string, unknown> | null | undefined;
  const packet = analysis.packet as Record<string, unknown> | null | undefined;
  const decisionState = analysis.decision_state ?? null;
  const hardBlockers = analysis.hard_blockers?.length ?? 0;
  const softBlockers = analysis.soft_blockers?.length ?? 0;

  const candidateScore = [
    validation?.overall_score,
    validation?.quality_score,
    packet?.quality_score,
    packet?.score,
  ].find((value): value is number => typeof value === 'number' && Number.isFinite(value));

  if (typeof candidateScore === 'number') {
    return Math.max(0, Math.min(100, Math.round(candidateScore)));
  }

  if (decisionState === 'PROCEED_TRAVELER_SAFE') return 82;
  if (decisionState === 'PROCEED_INTERNAL_DRAFT') return 74;
  if (decisionState === 'ASK_FOLLOWUP') return 64;
  if (decisionState === 'STOP_NEEDS_REVIEW') return 42;

  return Math.max(35, 80 - (hardBlockers * 12) - (softBlockers * 6));
}

function summaryFromAnalysis(analysis: RunStatusResponse | null): string {
  if (!analysis) return 'Example report — your score depends on what your plan contains';

  const decisionState = analysis.decision_state ?? 'unknown';
  const hardBlockers = analysis.hard_blockers?.length ?? 0;
  const softBlockers = analysis.soft_blockers?.length ?? 0;
  const followUps = analysis.follow_up_questions?.length ?? 0;

  return `Live analysis: ${decisionState} · ${hardBlockers} hard blockers · ${softBlockers} soft blockers · ${followUps} follow-up questions`;
}

const ISSUES = [
  {
    sev: 'Critical', color: T.red,
    bg: 'rgba(248,81,73,0.06)', border: 'rgba(248,81,73,0.2)',
    label: 'LAX layover may be too tight',
    body: '47-minute connection with international customs. Standard minimum is 90 min. High rebooking risk.',
  },
  {
    sev: 'Warning', color: T.amber,
    bg: 'rgba(210,153,34,0.06)', border: 'rgba(210,153,34,0.2)',
    label: 'Day 4 is heavily over-packed',
    body: '3 distant sites + a dinner reservation. Real-world slack is under 30 minutes if anything runs long.',
  },
  {
    sev: 'Heads up', color: T.blue,
    bg: 'rgba(88,166,255,0.05)', border: 'rgba(88,166,255,0.15)',
    label: 'No travel insurance detected',
    body: 'Nothing in the itinerary mentions coverage. Worth confirming before the final payment.',
  },
  {
    sev: 'Heads up', color: T.blue,
    bg: 'rgba(88,166,255,0.05)', border: 'rgba(88,166,255,0.15)',
    label: 'Schengen visa status not confirmed',
    body: 'Trip includes Paris + Rome. Confirm passport validity (6 months beyond return date required).',
  },
];

const rSevColor = (sev: string) => sev === 'Critical' ? 'Critical' : sev === 'Warning' ? 'Warning' : 'Info';
const rSevBadgeBg  = { Critical: 'rgba(248,81,73,0.1)', Warning: 'rgba(210,153,34,0.12)', Info: 'rgba(88,166,255,0.1)' } as const;
const rSevBadgeBdr = { Critical: 'rgba(248,81,73,0.22)', Warning: 'rgba(210,153,34,0.25)', Info: 'rgba(88,166,255,0.22)' } as const;
const rSevBadgeTxt = { Critical: T.red, Warning: T.amber, Info: T.blue } as const;

// ── Results view ──────────────────────────────────────────────────────────────
function ResultsView({
  rootRef,
  onReset,
  analysis,
}: {
  rootRef: RefObject<HTMLDivElement | null>;
  onReset: () => void;
  analysis?: RunStatusResponse | null;
}) {
  const [email, setEmail] = useState('');
  const [sent,  setSent]  = useState(false);
  const [manageMessage, setManageMessage] = useState<string | null>(null);
  const [manageBusy, setManageBusy] = useState<'export' | 'delete' | null>(null);

  const SCORE = scoreFromAnalysis(analysis ?? null);
  const summaryCopy = summaryFromAnalysis(analysis ?? null);
  const circumference = 2 * Math.PI * 36;
  const tripId = analysis?.trip_id ?? null;
  const liveChecks = ((analysis?.packet as Record<string, any> | null | undefined)?.public_checker_live_checks as Record<string, any> | undefined) ?? undefined;

  const handleExport = async () => {
    if (!tripId) return;
    setManageBusy('export');
    setManageMessage(null);
    try {
      const response = await fetch(`/api/public-checker/${tripId}/export`);
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
    if (!tripId) return;
    const confirmed = window.confirm('Delete this saved itinerary report and its stored upload data?');
    if (!confirmed) return;
    setManageBusy('delete');
    setManageMessage(null);
    try {
      const response = await fetch(`/api/public-checker/${tripId}`, { method: 'DELETE' });
      if (!response.ok) throw new Error('Delete failed');
      setManageMessage('Deleted.');
      onReset();
    } catch {
      setManageMessage('Could not delete this report.');
    } finally {
      setManageBusy(null);
    }
  };

  return (
    <div ref={rootRef} style={{
      background: 'radial-gradient(circle at 15% 10%, rgba(122,185,255,0.07) 0%, transparent 28%), radial-gradient(circle at 85% 0%, rgba(163,113,247,0.06) 0%, transparent 24%), radial-gradient(circle at 50% 100%, rgba(57,208,216,0.05) 0%, transparent 26%), #07090b',
      minHeight: '100vh', display: 'flex', flexDirection: 'column',
      fontFamily: T.fBody, color: T.t1,
    }}>
      <WedgeHeader />
      <div style={{ flex: 1, overflowY: 'auto', padding: '28px 32px', maxWidth: 860, margin: '0 auto', width: '100%', boxSizing: 'border-box' }}>

        <button onClick={onReset} style={{
          background: 'none', border: 'none', cursor: 'pointer',
          fontSize: 12, color: T.t3, fontFamily: T.fBody, marginBottom: 20,
          display: 'flex', alignItems: 'center', gap: 5, padding: 0,
        }}>
          ← Analyze another itinerary
        </button>

        {/* Results header grid */}
        <div className='itinerary-reveal' style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 20, marginBottom: 24 }}>
          {/* Score card */}
          <div style={{ padding: '24px 26px', borderRadius: 20, background: T.surface, border: `1px solid ${T.b0}` }}>
            <div style={{ fontSize: 10, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.1em', color: T.t3, marginBottom: 14 }}>
              Itinerary Health Score
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
              <div style={{ position: 'relative', width: 88, height: 88, flexShrink: 0 }}>
                <svg width='88' height='88' viewBox='0 0 88 88' style={{ transform: 'rotate(-90deg)' }}>
                  <circle cx='44' cy='44' r='36' fill='none' stroke={T.b0} strokeWidth='8' />
                  <circle cx='44' cy='44' r='36' fill='none' stroke={T.amber} strokeWidth='8'
                    strokeDasharray={`${circumference * (SCORE / 100)} ${circumference}`}
                    strokeLinecap='round' />
                </svg>
                <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                  <div style={{ fontSize: 26, fontWeight: 900, color: T.t1, fontFamily: T.fDisplay, lineHeight: 1 }}>{SCORE}</div>
                  <div style={{ fontSize: 9, color: T.t3, marginTop: 1 }}>/100</div>
                </div>
              </div>
              <div>
                <div style={{ fontSize: 15, fontWeight: 600, color: T.t1, marginBottom: 5 }}>
                  {analysis ? 'Live review' : 'Needs attention'}
                </div>
                <div style={{ fontSize: 12, color: T.t2, lineHeight: 1.55 }}>{summaryCopy}</div>
              </div>
            </div>
            <div style={{ display: 'flex', gap: 10, marginTop: 16 }}>
              {[{ l: 'Critical', v: 1, c: T.red }, { l: 'Warnings', v: 2, c: T.amber }, { l: 'Heads up', v: 2, c: T.blue }].map(m => (
                <div key={m.l} style={{ flex: 1, padding: '8px 10px', background: T.elevated, borderRadius: 8, textAlign: 'center' }}>
                  <div style={{ fontSize: 20, fontWeight: 800, color: m.c, fontFamily: T.fDisplay }}>{m.v}</div>
                  <div style={{ fontSize: 10, color: T.t3, marginTop: 1 }}>{m.l}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Trip summary + email gate */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <div style={{ padding: '18px 20px', borderRadius: 16, background: T.surface, border: `1px solid ${T.b0}`, flex: 1 }}>
              <div style={{ fontSize: 10, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.1em', color: T.t3, marginBottom: 12 }}>
                Trip Summary (Extracted)
              </div>
              <div className='itinerary-stagger' style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: 10 }}>
                {[
                  { l: 'Dates',         v: 'May 19 – Jun 3, 2025' },
                  { l: 'Duration',      v: '16 days'              },
                  { l: 'Destinations',  v: 'LAX → LHR → PAR → FCO' },
                  { l: 'Travelers',     v: '2 adults'             },
                  { l: 'Hotels',        v: '4 properties'         },
                  { l: 'Flights',       v: '5 segments'           },
                ].map(f => (
                  <div key={f.l}>
                    <div style={{ fontSize: 9.5, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.07em', color: T.t4 }}>{f.l}</div>
                    <div style={{ fontSize: 12.5, color: T.t1, marginTop: 2, fontFamily: T.fMono }}>{f.v}</div>
                  </div>
                ))}
              </div>
            </div>

            {liveChecks ? (
              <div style={{ padding: '16px 18px', borderRadius: 14, background: 'rgba(57,208,216,0.04)', border: '1px solid rgba(57,208,216,0.16)' }}>
                <div style={{ fontSize: 13, fontWeight: 600, color: T.t1, marginBottom: 3 }}>Live destination check</div>
                <div style={{ fontSize: 11, color: T.t2, marginBottom: 10 }}>
                  {String(liveChecks.destination ?? 'Destination')} · {String(liveChecks.climate?.precipitation_mm_avg ?? 'n/a')} mm avg rain · {String(liveChecks.climate?.wind_kmh_avg ?? 'n/a')} km/h wind
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {(Array.isArray(liveChecks.soft_blockers) ? liveChecks.soft_blockers : []).slice(0, 2).map((item: string) => (
                    <div key={item} style={{ fontSize: 11.5, color: T.t1, lineHeight: 1.5 }}>
                      • {item}
                    </div>
                  ))}
                  {(Array.isArray(liveChecks.hard_blockers) ? liveChecks.hard_blockers : []).slice(0, 1).map((item: string) => (
                    <div key={item} style={{ fontSize: 11.5, color: T.red, lineHeight: 1.5 }}>
                      • {item}
                    </div>
                  ))}
                </div>
              </div>
            ) : null}

            {/* Email gate */}
            <div style={{ padding: '16px 18px', borderRadius: 14, background: 'rgba(57,208,216,0.05)', border: '1px solid rgba(57,208,216,0.18)' }}>
              {sent ? (
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <span style={{ color: T.green, fontSize: 20 }}>✓</span>
                  <div>
                    <div style={{ fontSize: 13, fontWeight: 600, color: T.t1 }}>Report sent!</div>
                    <div style={{ fontSize: 11, color: T.t2 }}>Check your inbox for the full PDF.</div>
                  </div>
                </div>
              ) : (
                <>
                  <div style={{ fontSize: 13, fontWeight: 600, color: T.t1, marginBottom: 3 }}>Get your full report</div>
                  <div style={{ fontSize: 11, color: T.t2, marginBottom: 10 }}>Detailed findings + advisor-ready brief sent to your inbox.</div>
                  <div style={{ display: 'flex', gap: 8 }}>
                    <div style={{
                      flex: 1, display: 'flex', alignItems: 'center', gap: 8,
                      padding: '8px 11px', borderRadius: 8,
                      background: T.input, border: `1px solid ${T.b1}`,
                    }}>
                      <Mail size={14} color={T.t4} />
                      <input
                        value={email}
                        onChange={e => setEmail(e.target.value)}
                        placeholder='your@email.com'
                        style={{
                          flex: 1, background: 'none', border: 'none', outline: 'none',
                          color: T.t1, fontSize: 12, fontFamily: T.fBody,
                        }}
                      />
                    </div>
                    <button
                      onClick={() => email.includes('@') && setSent(true)}
                      style={{
                        display: 'inline-flex', alignItems: 'center', gap: 6,
                        height: 34, padding: '0 14px', borderRadius: 999,
                        fontSize: 12, fontWeight: 600, fontFamily: T.fBody,
                        background: 'linear-gradient(135deg, #7ab9ff 0%, #57e0ef 50%, #39d0d8 100%)',
                        color: '#071018', border: 'none', cursor: 'pointer',
                        boxShadow: '0 4px 14px rgba(57,208,216,0.25)',
                      }}
                    >
                      Send →
                    </button>
                  </div>
                  <div style={{ fontSize: 10, color: T.t4, marginTop: 7 }}>Stored only with consent. Not shared. Delete anytime.</div>
                  {manageMessage ? (
                    <div style={{ fontSize: 10, color: T.t3, marginTop: 7 }}>{manageMessage}</div>
                  ) : null}
                </>
              )}
            </div>

            <div style={{ padding: '16px 18px', borderRadius: 14, background: 'rgba(57,208,216,0.04)', border: '1px solid rgba(57,208,216,0.16)' }}>
              <div style={{ fontSize: 13, fontWeight: 600, color: T.t1, marginBottom: 3 }}>Manage your saved data</div>
              <div style={{ fontSize: 11, color: T.t2, marginBottom: 10 }}>
                Your report is stored only if you opted in. Export or delete the saved record with this report ID.
              </div>
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                <button
                  onClick={handleExport}
                  disabled={!tripId || manageBusy !== null}
                  style={{
                    display: 'inline-flex', alignItems: 'center', gap: 6,
                    height: 34, padding: '0 14px', borderRadius: 999,
                    fontSize: 12, fontWeight: 600, fontFamily: T.fBody,
                    background: tripId && manageBusy === null ? 'linear-gradient(135deg, #7ab9ff 0%, #57e0ef 50%, #39d0d8 100%)' : T.elevated,
                    color: tripId && manageBusy === null ? '#071018' : T.t3,
                    border: 'none', cursor: tripId && manageBusy === null ? 'pointer' : 'not-allowed',
                  }}
                >
                  {manageBusy === 'export' ? 'Exporting…' : 'Export JSON'}
                </button>
                <button
                  onClick={handleDelete}
                  disabled={!tripId || manageBusy !== null}
                  style={{
                    display: 'inline-flex', alignItems: 'center', gap: 6,
                    height: 34, padding: '0 14px', borderRadius: 999,
                    fontSize: 12, fontWeight: 600, fontFamily: T.fBody,
                    background: 'transparent', color: T.red,
                    border: `1px solid rgba(248,81,73,0.24)`, cursor: tripId && manageBusy === null ? 'pointer' : 'not-allowed',
                  }}
                >
                  {manageBusy === 'delete' ? 'Deleting…' : 'Delete saved data'}
                </button>
              </div>
              <div style={{ fontSize: 10, color: T.t4, marginTop: 8 }}>
                Report ID: {tripId ?? 'pending'}
              </div>
            </div>
          </div>
        </div>

        {/* Findings */}
        <div className='itinerary-stagger' style={{ marginBottom: 24 }}>
          <div style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.1em', color: T.t2, marginBottom: 12 }}>Findings</div>
          <div className='itinerary-stagger' style={{ display: 'grid', gap: 10 }}>
            {ISSUES.map(issue => {
              const c = rSevColor(issue.sev) as keyof typeof rSevBadgeTxt;
              return (
                <div key={issue.label} style={{
                  padding: '14px 16px', borderRadius: 12,
                  background: issue.bg, border: `1px solid ${issue.border}`,
                  display: 'grid', gridTemplateColumns: 'auto 1fr auto', gap: 14, alignItems: 'flex-start',
                }}>
                  <span style={{
                    display: 'inline-flex', alignItems: 'center', gap: 4,
                    padding: '2px 7px', borderRadius: 5, marginTop: 1,
                    fontSize: 10, fontWeight: 700, fontFamily: T.fMono,
                    textTransform: 'uppercase', letterSpacing: '0.04em',
                    color: rSevBadgeTxt[c], background: rSevBadgeBg[c], border: `1px solid ${rSevBadgeBdr[c]}`,
                    flexShrink: 0,
                  }}>
                    {issue.sev}
                  </span>
                  <div>
                    <div style={{ fontSize: 13.5, fontWeight: 600, color: T.t1, marginBottom: 3 }}>{issue.label}</div>
                    <div style={{ fontSize: 12, color: T.t2, lineHeight: 1.55 }}>{issue.body}</div>
                  </div>
                  <button style={{
                    fontSize: 11, color: issue.color, fontWeight: 600,
                    background: 'none', border: 'none', cursor: 'pointer',
                    fontFamily: T.fBody, flexShrink: 0, paddingTop: 2,
                  }}>
                    Fix it →
                  </button>
                </div>
              );
            })}
          </div>
        </div>

        {/* Soft agency conversion */}
        <div className='itinerary-reveal' style={{
          padding: '20px 24px', borderRadius: 16,
          background: 'rgba(13,17,23,0.9)', border: `1px solid ${T.b0}`,
          display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 24,
          flexWrap: 'wrap',
        }}>
          <div>
            <div style={{ fontSize: 14, fontWeight: 600, color: T.t1, marginBottom: 4 }}>Working with a travel advisor?</div>
            <div style={{ fontSize: 12, color: T.t2, lineHeight: 1.55, maxWidth: '50ch' }}>
              Share this report with them directly — or find an advisor who uses Waypoint OS to fix these issues professionally.
            </div>
          </div>
          <div style={{ display: 'flex', gap: 8, flexShrink: 0 }}>
            <button style={{
              display: 'inline-flex', alignItems: 'center', gap: 7,
              height: 34, padding: '0 14px', borderRadius: 999,
              fontSize: 12, fontWeight: 600, fontFamily: T.fBody,
              background: 'linear-gradient(180deg, rgba(13,23,33,0.8), rgba(10,18,26,0.8))',
              color: T.t1, border: '1px solid rgba(88,166,255,0.22)', cursor: 'pointer',
            }}>
              Share report
            </button>
            <Link href='/signup' style={{
              display: 'inline-flex', alignItems: 'center', gap: 7,
              height: 34, padding: '0 14px', borderRadius: 999,
              fontSize: 12, fontWeight: 600, fontFamily: T.fBody,
              background: 'linear-gradient(135deg, #7ab9ff 0%, #57e0ef 50%, #39d0d8 100%)',
              color: '#071018', border: 'none', cursor: 'pointer', textDecoration: 'none',
              boxShadow: '0 4px 14px rgba(57,208,216,0.25)',
            }}>
              Find an advisor →
            </Link>
          </div>
        </div>

        <div style={{ paddingBottom: 48 }} />
      </div>
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────
export default function ItineraryCheckerPage() {
  const [view, setView] = useState<'upload' | 'results'>('upload');
  const [analysis, setAnalysis] = useState<RunStatusResponse | null>(null);
  const { execute: executeSpineRun, isLoading: isAnalyzing } = useSpineRun();
  const motionRootRef = useRef<HTMLDivElement>(null);

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

  const handleAnalyze = async (plan: string, sourcePayload?: Record<string, unknown>) => {
    const trimmed = plan.trim();
    if (trimmed.length < 10) {
      return;
    }

    const retentionConsent = Boolean(sourcePayload?.retention_consent);
    const storedPayload = retentionConsent ? sourcePayload : undefined;

    try {
      const result = await executeSpineRun({
        raw_note: trimmed,
        owner_note: '',
        itinerary_text: trimmed,
        structured_json: storedPayload ? { source_payload: storedPayload } : null,
        retention_consent: retentionConsent,
        stage: 'discovery',
        operating_mode: 'normal_intake',
        strict_leakage: true,
        scenario_id: null,
      });
      setAnalysis(result);
      setView('results');
    } catch {
      setAnalysis(null);
      setView('results');
    }
  };

  const handleAnalyzeFile = async (file: File, retentionConsent: boolean) => {
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

    await handleAnalyze(trimmed, {
      kind: 'file_upload',
      uploaded_file: uploadedFile,
      retention_consent: retentionConsent,
    });
  };

  const handleFallbackResults = () => {
    setAnalysis(null);
    setView('results');
  };

  if (view === 'results') {
    return <ResultsView rootRef={motionRootRef} onReset={() => { setAnalysis(null); setView('upload'); }} analysis={analysis} />;
  }

  return (
    <UploadView
      rootRef={motionRootRef}
      onAnalyze={handleAnalyze}
      onAnalyzeFile={handleAnalyzeFile}
      onFallbackResults={handleFallbackResults}
      isBusy={isAnalyzing}
    />
  );
}
