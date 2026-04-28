// wp-wedge.jsx — GTM Wedge: Itinerary Checker (improved)

// ── Minimal header ────────────────────────────────────────────────────────────
function WedgeHeader() {
  const T = WP;
  return (
    <header style={{
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      padding: '14px 32px', borderBottom: `1px solid ${T.b0}`,
      background: 'rgba(10,13,17,0.9)', backdropFilter: 'blur(12px)',
      flexShrink: 0,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 9 }}>
        <div style={{ width: 28, height: 28, borderRadius: 8, background: 'linear-gradient(135deg, #2563eb, #39d0d8)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white' }}>
          <WpIcon.pin />
        </div>
        <div>
          <div style={{ fontSize: 13, fontWeight: 700, color: T.t1, letterSpacing: '-0.01em' }}>Waypoint</div>
          <div style={{ fontSize: 10, color: T.t3, lineHeight: 1 }}>Itinerary Checker</div>
        </div>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
        <span style={{ fontSize: 12, color: T.t3 }}>Free · No account required · Takes 60 seconds</span>
        <WpBtn variant="ghost" size="sm">For agencies →</WpBtn>
      </div>
    </header>
  );
}

// ── Upload state (hero = the tool) ────────────────────────────────────────────
function WedgeUpload() {
  const T = WP;
  const [dragging, setDragging] = React.useState(false);
  const [pasteMode, setPasteMode] = React.useState(false);
  const [text, setText] = React.useState('');

  return (
    <div style={{ background: T.canvas, height: '100%', display: 'flex', flexDirection: 'column', fontFamily: T.fBody, color: T.t1, overflow: 'hidden' }}>
      <WedgeHeader />

      {/* Background */}
      <div style={{ position: 'absolute', inset: 0, pointerEvents: 'none',
        background: 'radial-gradient(circle at 50% 30%, rgba(88,166,255,0.09) 0%, transparent 50%)',
      }} />

      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '0 24px', position: 'relative', zIndex: 1 }}>

        {/* Headline */}
        <div style={{ textAlign: 'center', marginBottom: 36, maxWidth: 580 }}>
          <WpKicker>Free itinerary stress-test</WpKicker>
          <h1 style={{ fontSize: 52, fontWeight: 900, lineHeight: 1.0, letterSpacing: '-0.04em', color: '#f5fbff', fontFamily: WP.fDisplay, marginBottom: 14 }}>
            Find what your<br />travel plan missed.
          </h1>
          <p style={{ fontSize: 16, lineHeight: 1.72, color: T.t2, maxWidth: '42ch', margin: '0 auto' }}>
            Upload your itinerary. Get a structured risk report — timing gaps, visa issues, pacing problems, hidden costs — in under 60 seconds.
          </p>
        </div>

        {/* Upload card */}
        <div style={{ width: '100%', maxWidth: 560 }}>

          {/* Mode tabs */}
          <div style={{ display: 'flex', gap: 4, marginBottom: 12, background: T.surface, borderRadius: 10, padding: 4, border: `1px solid ${T.b0}` }}>
            {['Upload file', 'Paste itinerary', 'Screenshot'].map((tab, i) => (
              <button key={tab} onClick={() => setPasteMode(i === 1)} style={{
                flex: 1, padding: '7px 0', borderRadius: 7, border: 'none', cursor: 'pointer',
                fontSize: 12, fontWeight: pasteMode === (i === 1) ? 600 : 400,
                background: (i === 0 && !pasteMode) || (i === 1 && pasteMode) ? T.elevated : 'transparent',
                color: (i === 0 && !pasteMode) || (i === 1 && pasteMode) ? T.t1 : T.t2,
                fontFamily: T.fBody, transition: 'all 150ms',
              }}>{tab}</button>
            ))}
          </div>

          {pasteMode ? (
            <div style={{ borderRadius: 14, border: `1px solid ${T.b1}`, background: T.surface, overflow: 'hidden' }}>
              <textarea
                value={text}
                onChange={e => setText(e.target.value)}
                placeholder={'Paste your day-by-day plan here…\n\nDay 1: Arrive LAX → London Heathrow (AA100, dep 10:30)\nDay 2: London — check-in The Connaught, walking tour\nDay 3: Paris Eurostar (07:55) — Musée d\'Orsay, Seine dinner\n…'}
                style={{
                  width: '100%', minHeight: 180, padding: '16px 18px', background: 'none',
                  border: 'none', outline: 'none', resize: 'none',
                  color: T.t1, fontSize: 13, fontFamily: T.fMono, lineHeight: 1.65,
                }}
              />
              <div style={{ padding: '10px 16px', borderTop: `1px solid ${T.b0}`, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: 11, color: T.t4 }}>{text.length > 0 ? `${text.length} characters` : 'Messy inputs work fine'}</span>
                <WpBtn variant="primary" size="sm">Analyze My Itinerary <WpIcon.arrow /></WpBtn>
              </div>
            </div>
          ) : (
            <div
              onDragEnter={() => setDragging(true)}
              onDragLeave={() => setDragging(false)}
              style={{
                borderRadius: 14, border: `2px dashed ${dragging ? T.cyan : T.b1}`,
                background: dragging ? 'rgba(57,208,216,0.04)' : T.surface,
                padding: '36px 24px', textAlign: 'center',
                transition: 'all 200ms',
              }}>
              <div style={{ width: 48, height: 48, borderRadius: 14, background: 'rgba(88,166,255,0.1)', border: `1px solid rgba(88,166,255,0.2)`, display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 14px', color: T.blue }}>
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><polyline points="16 16 12 12 8 16"/><line x1="12" y1="12" x2="12" y2="21"/><path d="M20.39 18.39A5 5 0 0018 9h-1.26A8 8 0 103 16.3"/></svg>
              </div>
              <div style={{ fontSize: 15, fontWeight: 600, color: T.t1, marginBottom: 5 }}>Drop your PDF here</div>
              <div style={{ fontSize: 12, color: T.t3, marginBottom: 18 }}>PDF, JPG, PNG, or .txt up to 25MB</div>
              <WpBtn variant="primary" size="md">Choose file to upload</WpBtn>
            </div>
          )}

          {/* Trust line */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 18, marginTop: 14 }}>
            {['Free to use', 'No sign-up required', 'Analyzed then deleted'].map(t => (
              <div key={t} style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
                <span style={{ color: T.green }}><WpIcon.check /></span>
                <span style={{ fontSize: 11, color: T.t4 }}>{t}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Social proof strip */}
        <div style={{ marginTop: 36, display: 'flex', alignItems: 'center', gap: 24 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <div style={{ display: 'flex' }}>
              {['#58a6ff','#39d0d8','#3fb950','#d29922','#a371f7'].map((c, i) => (
                <div key={i} style={{ width: 24, height: 24, borderRadius: '50%', background: c, marginLeft: i ? -6 : 0, border: `2px solid ${T.canvas}` }} />
              ))}
            </div>
            <span style={{ fontSize: 12, color: T.t3 }}>20,000+ itineraries analyzed</span>
          </div>
          <div style={{ width: 1, height: 16, background: T.b0 }} />
          <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
            {'★★★★★'.split('').map((s, i) => <span key={i} style={{ color: T.amber, fontSize: 13 }}>{s}</span>)}
            <span style={{ fontSize: 12, color: T.t3, marginLeft: 3 }}>4.8 / 5 from travelers</span>
          </div>
        </div>

      </div>
    </div>
  );
}

// ── Results state ─────────────────────────────────────────────────────────────
function WedgeResults() {
  const T = WP;
  const [email, setEmail] = React.useState('');
  const [sent, setSent] = React.useState(false);

  const issues = [
    { sev: 'Critical', label: 'LAX layover may be too tight',        body: '47-minute connection with international customs. Standard minimum is 90 min. High rebooking risk.', color: T.red,   bg: 'rgba(248,81,73,0.06)',   border: 'rgba(248,81,73,0.2)'   },
    { sev: 'Warning',  label: 'Day 4 is heavily over-packed',        body: '3 distant sites + a dinner reservation. Real-world slack is under 30 minutes if anything runs long.', color: T.amber, bg: 'rgba(210,153,34,0.06)',  border: 'rgba(210,153,34,0.2)'  },
    { sev: 'Heads up', label: 'No travel insurance detected',        body: 'Nothing in the itinerary mentions coverage. Worth confirming before the final payment.',            color: T.blue,  bg: 'rgba(88,166,255,0.05)',  border: 'rgba(88,166,255,0.15)' },
    { sev: 'Heads up', label: 'Schengen visa status not confirmed',  body: 'Trip includes Paris + Rome. Confirm passport validity (6 months beyond return date required).',    color: T.blue,  bg: 'rgba(88,166,255,0.05)',  border: 'rgba(88,166,255,0.15)' },
  ];

  return (
    <div style={{ background: T.canvas, height: '100%', display: 'flex', flexDirection: 'column', fontFamily: T.fBody, color: T.t1, overflow: 'hidden' }}>
      <WedgeHeader />
      <div style={{ flex: 1, overflowY: 'auto', padding: '28px 32px' }}>

        {/* Results header */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.4fr', gap: 20, marginBottom: 24 }}>

          {/* Score card */}
          <div style={{ padding: '24px 26px', borderRadius: 20, background: T.surface, border: `1px solid ${T.b0}` }}>
            <div style={{ fontSize: 10, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.1em', color: T.t3, marginBottom: 14 }}>Itinerary Health Score</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
              {/* Score ring */}
              <div style={{ position: 'relative', width: 88, height: 88, flexShrink: 0 }}>
                <svg width="88" height="88" viewBox="0 0 88 88" style={{ transform: 'rotate(-90deg)' }}>
                  <circle cx="44" cy="44" r="36" fill="none" stroke={T.b0} strokeWidth="8" />
                  <circle cx="44" cy="44" r="36" fill="none" stroke={T.amber} strokeWidth="8"
                    strokeDasharray={`${2 * Math.PI * 36 * 0.71} ${2 * Math.PI * 36}`}
                    strokeLinecap="round" />
                </svg>
                <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                  <div style={{ fontSize: 26, fontWeight: 900, color: T.t1, fontFamily: T.fDisplay, lineHeight: 1 }}>71</div>
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
              <div style={{ fontSize: 10, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.1em', color: T.t3, marginBottom: 12 }}>Trip Summary (Extracted)</div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                {[
                  { l: 'Dates',       v: 'May 19 – Jun 3, 2025' },
                  { l: 'Duration',    v: '16 days'               },
                  { l: 'Destinations',v: 'LAX → LHR → PAR → FCO' },
                  { l: 'Travelers',   v: '2 adults'              },
                  { l: 'Hotels',      v: '4 properties'          },
                  { l: 'Flights',     v: '5 segments'            },
                ].map(f => (
                  <div key={f.l}>
                    <div style={{ fontSize: 9.5, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.07em', color: T.t4 }}>{f.l}</div>
                    <div style={{ fontSize: 12.5, color: T.t1, marginTop: 1, fontFamily: T.fMono }}>{f.v}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Email gate */}
            <div style={{ padding: '16px 18px', borderRadius: 14, background: 'rgba(57,208,216,0.05)', border: '1px solid rgba(57,208,216,0.18)' }}>
              {sent ? (
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span style={{ color: T.green, fontSize: 18 }}>✓</span>
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
                    <div style={{ flex: 1, display: 'flex', alignItems: 'center', gap: 8, padding: '8px 11px', borderRadius: 8, background: T.input, border: `1px solid ${T.b1}` }}>
                      <span style={{ color: T.t4 }}><WpIcon.mail /></span>
                      <input value={email} onChange={e => setEmail(e.target.value)} placeholder="your@email.com"
                        style={{ flex: 1, background: 'none', border: 'none', outline: 'none', color: T.t1, fontSize: 12, fontFamily: T.fBody }} />
                    </div>
                    <WpBtn variant="primary" size="sm" onClick={() => email.includes('@') && setSent(true)}>Send →</WpBtn>
                  </div>
                  <div style={{ fontSize: 10, color: T.t4, marginTop: 7 }}>Analyzed then deleted. Not shared. No spam.</div>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Issues */}
        <div style={{ marginBottom: 24 }}>
          <div style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.1em', color: T.t2, marginBottom: 12 }}>Findings</div>
          <div style={{ display: 'grid', gap: 10 }}>
            {issues.map(issue => (
              <div key={issue.label} style={{ padding: '14px 16px', borderRadius: 12, background: issue.bg, border: `1px solid ${issue.border}`, display: 'grid', gridTemplateColumns: 'auto 1fr auto', gap: 14, alignItems: 'flex-start' }}>
                <WpBadge color={issue.sev === 'Critical' ? 'red' : issue.sev === 'Warning' ? 'amber' : 'blue'} style={{ marginTop: 1, flexShrink: 0 }}>{issue.sev}</WpBadge>
                <div>
                  <div style={{ fontSize: 13.5, fontWeight: 600, color: T.t1, marginBottom: 3 }}>{issue.label}</div>
                  <div style={{ fontSize: 12, color: T.t2, lineHeight: 1.55 }}>{issue.body}</div>
                </div>
                <button style={{ fontSize: 11, color: issue.color, fontWeight: 600, background: 'none', border: 'none', cursor: 'pointer', fontFamily: T.fBody, flexShrink: 0, paddingTop: 2 }}>Fix it →</button>
              </div>
            ))}
          </div>
        </div>

        {/* Soft agency conversion */}
        <div style={{
          padding: '20px 24px', borderRadius: 16,
          background: 'rgba(13,17,23,0.9)', border: `1px solid ${T.b0}`,
          display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 24,
        }}>
          <div>
            <div style={{ fontSize: 14, fontWeight: 600, color: T.t1, marginBottom: 4 }}>Working with a travel advisor?</div>
            <div style={{ fontSize: 12, color: T.t2, lineHeight: 1.55 }}>Share this report with them directly — or find an advisor who uses Waypoint OS to fix these issues professionally.</div>
          </div>
          <div style={{ display: 'flex', gap: 8, flexShrink: 0 }}>
            <WpBtn variant="secondary" size="sm">Share report</WpBtn>
            <WpBtn variant="primary" size="sm">Find an advisor →</WpBtn>
          </div>
        </div>

      </div>
    </div>
  );
}

Object.assign(window, { WedgeUpload, WedgeResults });
