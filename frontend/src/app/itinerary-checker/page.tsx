'use client';

import Link from 'next/link';
import { useState, useRef, DragEvent } from 'react';
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
        <div>
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

// ── Upload card (reused in hero) ──────────────────────────────────────────────
function UploadCard({ onResults }: { onResults: () => void }) {
  const [activeTab, setActiveTab] = useState<'file' | 'paste' | 'screenshot'>('file');
  const [dragging, setDragging] = useState(false);
  const [text, setText] = useState('');
  const fileRef = useRef<HTMLInputElement>(null);

  const tabs: { key: 'file' | 'paste' | 'screenshot'; label: string }[] = [
    { key: 'file',       label: 'Upload file'     },
    { key: 'paste',      label: 'Paste itinerary' },
    { key: 'screenshot', label: 'Screenshot'      },
  ];

  const handleDragOver = (e: DragEvent) => { e.preventDefault(); setDragging(true); };
  const handleDragLeave = () => setDragging(false);
  const handleDrop = (e: DragEvent) => { e.preventDefault(); setDragging(false); onResults(); };

  return (
    <div style={{ width: '100%' }}>
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
            <button onClick={onResults} disabled={text.length < 10} style={{
              display: 'inline-flex', alignItems: 'center', gap: 7,
              height: 34, padding: '0 14px', borderRadius: 999,
              fontSize: 12, fontWeight: 600, fontFamily: T.fBody,
              background: text.length >= 10
                ? 'linear-gradient(135deg, #7ab9ff 0%, #57e0ef 50%, #39d0d8 100%)'
                : T.elevated,
              color: text.length >= 10 ? '#071018' : T.t3,
              border: 'none', cursor: text.length >= 10 ? 'pointer' : 'not-allowed',
              boxShadow: text.length >= 10 ? '0 8px 24px rgba(57,208,216,0.3)' : 'none',
              transition: 'all 160ms',
            }}>
              Analyze My Itinerary <ArrowRight size={13} />
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
          <button
            onClick={e => { e.stopPropagation(); onResults(); }}
            style={{
              display: 'inline-flex', alignItems: 'center', gap: 7,
              height: 42, padding: '0 20px', borderRadius: 999,
              fontSize: 13, fontWeight: 600, fontFamily: T.fBody,
              background: 'linear-gradient(135deg, #7ab9ff 0%, #57e0ef 50%, #39d0d8 100%)',
              color: '#071018', border: 'none', cursor: 'pointer',
              boxShadow: '0 8px 24px rgba(57,208,216,0.3), inset 0 1px 0 rgba(255,255,255,0.38)',
            }}
          >
            Choose file to upload
          </button>
          <input
            ref={fileRef}
            type='file'
            accept='.pdf,.jpg,.jpeg,.png,.txt,.webp'
            style={{ display: 'none' }}
            onChange={onResults}
          />
        </div>
      )}

      {/* Trust chips */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        gap: 18, marginTop: 14, flexWrap: 'wrap',
      }}>
        {['Free to use', 'No sign-up required', 'Analyzed then deleted'].map(label => (
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
function UploadView({ onResults }: { onResults: () => void }) {
  return (
    <div style={{
      background: T.canvas, fontFamily: T.fBody, color: T.t1,
    }}>
      <WedgeHeader />

      {/* Background radial glow */}
      <div style={{
        position: 'fixed', inset: 0, pointerEvents: 'none',
        background: 'radial-gradient(circle at 50% 25%, rgba(88,166,255,0.08) 0%, transparent 55%)',
        zIndex: 0,
      }} />

      {/* ── HERO: split 2-col ── */}
      <section style={{
        position: 'relative', zIndex: 1,
        maxWidth: 1140, margin: '0 auto',
        padding: '72px 40px 80px',
        display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 64,
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
            Free itinerary stress-test
          </span>

          <h1 style={{
            fontSize: 'clamp(36px, 4vw, 54px)', fontWeight: 900,
            lineHeight: 1.04, letterSpacing: '-0.04em',
            color: '#f5fbff', fontFamily: T.fDisplay, marginBottom: 20,
          }}>
            Find what your travel plan missed.
          </h1>

          <p style={{ fontSize: 16, lineHeight: 1.72, color: T.t2, maxWidth: '40ch', marginBottom: 32 }}>
            Upload your itinerary and get a structured risk report — timing gaps, visa issues, pacing problems, hidden costs — in under 60 seconds.
          </p>

          {/* Stats row */}
          <div style={{ display: 'flex', gap: 32, flexWrap: 'wrap', marginBottom: 36 }}>
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
        <div>
          <UploadCard onResults={onResults} />

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

          <div style={{
            display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16,
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
            display: 'grid', gridTemplateColumns: '1fr 1.1fr', gap: 64, alignItems: 'start',
          }}>
            {/* Left: copy */}
            <div style={{ paddingTop: 8 }}>
              <div style={{
                fontSize: 10, fontWeight: 700, letterSpacing: '0.14em', textTransform: 'uppercase',
                color: T.amber, marginBottom: 16,
              }}>
                Example report
              </div>
              <h2 style={{
                fontSize: 'clamp(26px, 3vw, 38px)', fontWeight: 800,
                letterSpacing: '-0.03em', color: T.t1, fontFamily: T.fDisplay,
                marginBottom: 18, lineHeight: 1.1,
              }}>
                Real issues, not generic warnings
              </h2>
              <p style={{ fontSize: 15, color: T.t2, lineHeight: 1.7, marginBottom: 28, maxWidth: '38ch' }}>
                Every finding is specific to your itinerary — the actual route, the exact layover duration, the specific hotels booked.
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

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 20 }}>
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
function ResultsView({ onReset }: { onReset: () => void }) {
  const [email, setEmail] = useState('');
  const [sent,  setSent]  = useState(false);

  const SCORE = 71;
  const circumference = 2 * Math.PI * 36;

  return (
    <div style={{
      background: T.canvas, minHeight: '100vh', display: 'flex', flexDirection: 'column',
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
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.4fr', gap: 20, marginBottom: 24 }}>
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
                <div style={{ fontSize: 15, fontWeight: 600, color: T.t1, marginBottom: 5 }}>Needs attention</div>
                <div style={{ fontSize: 12, color: T.t2, lineHeight: 1.55 }}>Good trip concept. A few issues should be discussed before you confirm or pay.</div>
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
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
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
                  <div style={{ fontSize: 10, color: T.t4, marginTop: 7 }}>Analyzed then deleted. Not shared. No spam.</div>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Findings */}
        <div style={{ marginBottom: 24 }}>
          <div style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.1em', color: T.t2, marginBottom: 12 }}>Findings</div>
          <div style={{ display: 'grid', gap: 10 }}>
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
        <div style={{
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

  if (view === 'results') {
    return <ResultsView onReset={() => setView('upload')} />;
  }

  return <UploadView onResults={() => setView('results')} />;
}
