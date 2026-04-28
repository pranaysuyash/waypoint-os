'use client';

import Link from 'next/link';
import { useState, useRef, DragEvent } from 'react';
import { ArrowRight, Check, Mail, MapPin, Upload } from 'lucide-react';

// ── Design tokens (matches globals.css vars) ─────────────────────────────────
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
  b0: '#21262d',
  b1: '#30363d',
  fDisplay: "'Outfit', system-ui, sans-serif",
  fBody:    "'Inter', system-ui, sans-serif",
  fMono:    "'JetBrains Mono', monospace",
};

// ── Minimal header ───────────────────────────────────────────────────────────
function WedgeHeader() {
  return (
    <header style={{
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      padding: '14px 32px', borderBottom: `1px solid ${T.b0}`,
      background: 'rgba(10,13,17,0.9)', backdropFilter: 'blur(12px)',
      flexShrink: 0, position: 'sticky', top: 0, zIndex: 50,
    }}>
      <Link href='/' style={{ display: 'flex', alignItems: 'center', gap: 9, textDecoration: 'none' }}>
        <div style={{
          width: 28, height: 28, borderRadius: 8,
          background: 'linear-gradient(135deg, #2563eb, #39d0d8)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white',
          flexShrink: 0,
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
          cursor: 'pointer',
        }}>
          For agencies →
        </Link>
      </div>
    </header>
  );
}

// ── Upload state ─────────────────────────────────────────────────────────────
function UploadView({ onResults }: { onResults: () => void }) {
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
    <div style={{
      background: T.canvas, minHeight: '100vh', display: 'flex', flexDirection: 'column',
      fontFamily: T.fBody, color: T.t1,
    }}>
      <WedgeHeader />

      {/* Background radial glow */}
      <div style={{
        position: 'fixed', inset: 0, pointerEvents: 'none',
        background: 'radial-gradient(circle at 50% 30%, rgba(88,166,255,0.09) 0%, transparent 55%)',
        zIndex: 0,
      }} />

      <div style={{
        flex: 1, display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: 'center',
        padding: '48px 24px', position: 'relative', zIndex: 1,
      }}>

        {/* Kicker */}
        <span style={{
          display: 'inline-flex', alignItems: 'center', gap: 7,
          padding: '5px 12px', borderRadius: 999, marginBottom: 20,
          color: '#d8eef0', fontSize: 10.5, letterSpacing: '0.13em',
          textTransform: 'uppercase', fontFamily: T.fBody, fontWeight: 600,
          border: '1px solid rgba(57,208,216,0.22)', background: 'rgba(7,22,26,0.8)',
        }}>
          <span style={{ width: 5, height: 5, borderRadius: '50%', background: '#39d0d8', boxShadow: '0 0 5px #39d0d8', flexShrink: 0 }} />
          Free itinerary stress-test
        </span>

        {/* Headline */}
        <div style={{ textAlign: 'center', marginBottom: 40, maxWidth: 580 }}>
          <h1 style={{
            fontSize: 'clamp(38px, 6vw, 56px)', fontWeight: 900,
            lineHeight: 1.0, letterSpacing: '-0.04em',
            color: '#f5fbff', fontFamily: T.fDisplay, marginBottom: 16,
          }}>
            Find what your travel plan missed.
          </h1>
          <p style={{ fontSize: 16, lineHeight: 1.72, color: T.t2, maxWidth: '42ch', margin: '0 auto' }}>
            Upload your itinerary. Get a structured risk report — timing gaps, visa issues, pacing problems, hidden costs — in under 60 seconds.
          </p>
        </div>

        {/* Upload card */}
        <div style={{ width: '100%', maxWidth: 560 }}>

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
            /* Paste mode */
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
            /* File / Screenshot drop zone */
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

        {/* Social proof */}
        <div style={{ marginTop: 40, display: 'flex', alignItems: 'center', gap: 20, flexWrap: 'wrap', justifyContent: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <div style={{ display: 'flex' }}>
              {['#58a6ff','#39d0d8','#3fb950','#d29922','#a371f7'].map((c, i) => (
                <div key={i} style={{
                  width: 24, height: 24, borderRadius: '50%', background: c,
                  marginLeft: i ? -6 : 0, border: `2px solid ${T.canvas}`,
                }} />
              ))}
            </div>
            <span style={{ fontSize: 12, color: T.t3 }}>20,000+ itineraries analyzed</span>
          </div>
          <div style={{ width: 1, height: 16, background: T.b0 }} />
          <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            {'★★★★★'.split('').map((s, i) => (
              <span key={i} style={{ color: T.amber, fontSize: 13 }}>{s}</span>
            ))}
            <span style={{ fontSize: 12, color: T.t3, marginLeft: 4 }}>4.8 / 5 from travelers</span>
          </div>
        </div>

      </div>
    </div>
  );
}

// ── Results state ────────────────────────────────────────────────────────────
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

const sevColor = (sev: string) => sev === 'Critical' ? 'red' : sev === 'Warning' ? 'amber' : 'blue';
const sevBadgeBg  = { red: 'rgba(248,81,73,0.1)', amber: 'rgba(210,153,34,0.12)', blue: 'rgba(88,166,255,0.1)' } as const;
const sevBadgeBdr = { red: 'rgba(248,81,73,0.22)', amber: 'rgba(210,153,34,0.25)', blue: 'rgba(88,166,255,0.22)' } as const;
const sevBadgeTxt = { red: T.red, amber: T.amber, blue: T.blue } as const;

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

        {/* Back link */}
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
              {/* Score ring */}
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
              const c = sevColor(issue.sev) as keyof typeof sevBadgeTxt;
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
                    color: sevBadgeTxt[c], background: sevBadgeBg[c], border: `1px solid ${sevBadgeBdr[c]}`,
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

// ── Page ─────────────────────────────────────────────────────────────────────
export default function ItineraryCheckerPage() {
  const [view, setView] = useState<'upload' | 'results'>('upload');

  if (view === 'results') {
    return <ResultsView onReset={() => setView('upload')} />;
  }

  return <UploadView onResults={() => setView('results')} />;
}
