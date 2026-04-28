// wp-landing.jsx — Landing page prototype

// ── Animated counter hook ────────────────────────────────────────────────────
function useCountUp(target, duration = 1200) {
  const [val, setVal] = React.useState(0);
  React.useEffect(() => {
    let start = null;
    const step = (ts) => {
      if (!start) start = ts;
      const pct = Math.min((ts - start) / duration, 1);
      const ease = 1 - Math.pow(1 - pct, 3);
      setVal(Math.round(ease * target));
      if (pct < 1) requestAnimationFrame(step);
    };
    const id = requestAnimationFrame(step);
    return () => cancelAnimationFrame(id);
  }, [target, duration]);
  return val;
}

// ── Header ───────────────────────────────────────────────────────────────────
function LandingHeader() {
  const T = WP;
  return (
    <header style={{
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      gap: 16, padding: '11px 18px',
      background: 'linear-gradient(180deg, rgba(11,18,26,0.9), rgba(9,13,18,0.82))',
      border: '1px solid rgba(96,111,128,0.15)',
      borderRadius: 22, backdropFilter: 'blur(24px)',
      boxShadow: '0 16px 40px rgba(0,0,0,0.28), inset 0 1px 0 rgba(255,255,255,0.05)',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <div style={{
          width: 34, height: 34, borderRadius: 10, flexShrink: 0,
          background: 'linear-gradient(135deg, #2563eb, #39d0d8)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          boxShadow: '0 6px 18px rgba(37,99,235,0.3), 0 0 0 1px rgba(255,255,255,0.1)',
          color: 'white',
        }}>
          <WpIcon.pin />
        </div>
        <div>
          <div style={{ fontSize: 13, fontWeight: 700, color: T.t1, letterSpacing: '-0.01em', lineHeight: 1.2 }}>Waypoint OS</div>
          <div style={{ fontSize: 10, color: T.t3, lineHeight: 1 }}>Travel agency OS</div>
        </div>
      </div>

      <nav style={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        {['Product', 'Solutions', 'For Agencies', 'Resources', 'Pricing'].map(item => (
          <a key={item} style={{ padding: '9px 13px', borderRadius: 999, color: T.t2, fontSize: 13, cursor: 'pointer' }}>{item}</a>
        ))}
      </nav>

      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <WpBtn variant="ghost" size="sm">Sign in</WpBtn>
        <WpBtn variant="primary" size="sm">Book a demo <WpIcon.arrow /></WpBtn>
      </div>
    </header>
  );
}

// ── Hero cockpit mockup ───────────────────────────────────────────────────────
function HeroCockpit() {
  const T = WP;
  const trips = [
    { dest: 'Portugal, 12 days',  client: 'Mehta family',    stage: 'review',  val: '$18.4k', flag: 'VISA GAP',  pc: 'red' },
    { dest: 'Japan, Group FIT',   client: 'Chen party · 8p', stage: 'options', val: '$42k',   flag: null,        pc: 'amber' },
    { dest: 'Maldives · Overwater',client: 'Williams couple', stage: 'booking', val: '$67.2k', flag: null,        pc: 'green' },
  ];
  const activeCount = useCountUp(24, 1400);
  const revenue = useCountUp(284, 1600);
  const conv = useCountUp(68, 1300);

  return (
    <div style={{
      background: 'linear-gradient(180deg, rgba(11,20,30,0.95), rgba(8,10,12,0.97))',
      border: '1px solid rgba(88,166,255,0.2)',
      borderRadius: 20, padding: 16,
      boxShadow: '0 32px 64px rgba(0,0,0,0.42), inset 0 1px 0 rgba(255,255,255,0.07)',
      backdropFilter: 'blur(20px)',
      transform: 'perspective(1100px) rotateY(-4deg) rotateX(2deg)',
    }}>
      {/* Top bar */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
        <div>
          <div style={{ fontSize: 9.5, fontWeight: 800, letterSpacing: '0.1em', textTransform: 'uppercase', color: T.t3 }}>Good morning, Alex</div>
          <div style={{ fontSize: 17, fontWeight: 700, color: T.t1, fontFamily: T.fDisplay, marginTop: 1 }}>Agency Dashboard</div>
        </div>
        <WpPill color="red" dot>3 need review</WpPill>
      </div>

      {/* Metrics row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 8, marginBottom: 14 }}>
        {[
          { label: 'Active Trips',  value: activeCount, suffix: '', color: T.blue  },
          { label: 'Revenue MTD',   value: `$${revenue}k`, suffix: '', color: T.green },
          { label: 'Conversion',    value: `${conv}%`,  suffix: '', color: T.cyan  },
        ].map(m => (
          <div key={m.label} style={{ padding: '9px 11px', background: 'rgba(22,27,34,0.86)', borderRadius: 9, border: `1px solid ${T.b0}` }}>
            <div style={{ fontSize: 9, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: T.t3 }}>{m.label}</div>
            <div style={{ fontSize: 22, fontWeight: 800, color: T.t1, lineHeight: 1.15, marginTop: 2, fontFamily: T.fDisplay }}>{m.value}</div>
          </div>
        ))}
      </div>

      {/* Content grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.1fr 0.9fr', gap: 10 }}>
        {/* Inbox */}
        <div style={{ background: 'rgba(13,17,23,0.92)', borderRadius: 11, border: `1px solid ${T.b0}`, overflow: 'hidden' }}>
          <div style={{ padding: '9px 13px', borderBottom: `1px solid ${T.b0}`, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: T.cyan }}>
              <WpIcon.inbox />
              <span style={{ fontSize: 10, fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.08em' }}>Inbox</span>
            </div>
            <WpBadge color="blue">3 new</WpBadge>
          </div>
          {trips.map((trip, i) => (
            <div key={i} style={{
              display: 'flex', alignItems: 'center', gap: 8, padding: '8px 13px',
              borderBottom: i < trips.length - 1 ? `1px solid rgba(33,38,45,0.45)` : 'none',
              background: i === 0 ? 'rgba(248,81,73,0.04)' : 'transparent',
            }}>
              <div style={{ width: 3, height: 26, borderRadius: 2, background: WP_C[trip.pc].text, flexShrink: 0 }} />
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 5, marginBottom: 1 }}>
                  <span style={{ fontSize: 12, fontWeight: 600, color: T.t1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{trip.dest}</span>
                  {trip.flag && <WpBadge color="red" style={{ fontSize: 8 }}>{trip.flag}</WpBadge>}
                </div>
                <span style={{ fontSize: 10.5, color: T.t2 }}>{trip.client} · <span style={{ fontFamily: T.fMono, color: T.blue }}>{trip.val}</span></span>
              </div>
              <WpBadge color={trip.stage === 'review' ? 'red' : trip.stage === 'booking' ? 'green' : 'blue'}>{trip.stage}</WpBadge>
            </div>
          ))}
        </div>

        {/* AI panel */}
        <div style={{ background: 'rgba(13,17,23,0.92)', borderRadius: 11, border: `1px solid ${T.b0}`, overflow: 'hidden' }}>
          <div style={{ padding: '9px 13px', borderBottom: `1px solid ${T.b0}`, display: 'flex', alignItems: 'center', gap: 6, color: T.purple }}>
            <WpIcon.sparkles />
            <span style={{ fontSize: 10, fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.08em' }}>AI Analysis</span>
          </div>
          <div style={{ padding: 12 }}>
            <div style={{ fontSize: 9.5, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: T.t3, marginBottom: 8 }}>Portugal · Mehta</div>
            {[
              { label: 'Missing',  value: 'Passport validity, room split', color: T.amber },
              { label: 'Next move',value: 'Ask 4 Qs, build 2 option bands', color: T.cyan },
              { label: 'Owner',    value: 'High-value repeat — review first', color: T.blue },
            ].map(item => (
              <div key={item.label} style={{ padding: '7px 9px', background: 'rgba(8,10,12,0.5)', borderRadius: 7, borderLeft: `2px solid ${item.color}`, marginBottom: 6 }}>
                <div style={{ fontSize: 8.5, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: item.color, marginBottom: 1 }}>{item.label}</div>
                <div style={{ fontSize: 11, color: T.t1, lineHeight: 1.4 }}>{item.value}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Pulsing route line accent */}
      <div style={{
        position: 'absolute', bottom: -1, left: '10%', right: '10%', height: 2,
        background: 'linear-gradient(90deg, transparent, rgba(57,208,216,0.6), rgba(88,166,255,0.4), transparent)',
        borderRadius: 1,
        animation: 'routePulse 3s ease-in-out infinite',
      }} />
    </div>
  );
}

// ── Hero section ─────────────────────────────────────────────────────────────
function LandingHero() {
  const T = WP;
  return (
    <div style={{ position: 'relative', background: T.canvas, height: '100%', overflow: 'hidden', fontFamily: T.fBody }}>
      <style>{`
        @keyframes routePulse { 0%,100%{opacity:1} 50%{opacity:0.4} }
        @keyframes fadeUp { from{opacity:0;transform:translateY(14px)} to{opacity:1;transform:none} }
      `}</style>

      {/* Background radials + grid */}
      <div style={{ position: 'absolute', inset: 0, pointerEvents: 'none',
        background: `
          radial-gradient(circle at 12% 8%, rgba(88,166,255,0.18) 0%, transparent 26%),
          radial-gradient(circle at 86% 10%, rgba(57,208,216,0.11) 0%, transparent 22%),
          radial-gradient(circle at 55% 90%, rgba(210,153,34,0.06) 0%, transparent 20%)
        `
      }} />
      <div style={{ position: 'absolute', inset: 0, pointerEvents: 'none',
        backgroundImage: `linear-gradient(rgba(255,255,255,0.022) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.022) 1px, transparent 1px)`,
        backgroundSize: '88px 88px',
        maskImage: 'linear-gradient(to bottom, rgba(0,0,0,0.75) 0%, transparent 88%)',
      }} />

      <div style={{ position: 'relative', zIndex: 1, maxWidth: 1200, margin: '0 auto', padding: '0 28px' }}>
        <div style={{ paddingTop: 18 }}><LandingHeader /></div>

        {/* Hero grid */}
        <div style={{ display: 'grid', gridTemplateColumns: '0.94fr 1.06fr', gap: 40, paddingTop: 52, alignItems: 'center' }}>
          {/* Copy */}
          <div style={{ animation: 'fadeUp 0.5s ease both' }}>
            <WpKicker>Built for boutique agencies</WpKicker>
            <h1 style={{ fontSize: 68, fontWeight: 900, lineHeight: 0.96, letterSpacing: '-0.04em', color: '#f5fbff', fontFamily: T.fDisplay, marginBottom: 14 }}>
              Waypoint OS
            </h1>
            <p style={{ fontSize: 21, fontWeight: 400, lineHeight: 1.28, color: T.t2, marginBottom: 20, maxWidth: '22ch' }}>
              The operating system for boutique travel agencies.
            </p>
            <p style={{ fontSize: 15.5, lineHeight: 1.78, color: T.t2, maxWidth: '44ch', marginBottom: 30 }}>
              From messy WhatsApp notes to client-safe proposals — Waypoint structures the intake, surfaces the risks, and protects your margins.
            </p>

            <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 24 }}>
              <WpBtn variant="primary" size="lg">Book a demo <WpIcon.arrow /></WpBtn>
              <WpBtn variant="secondary" size="lg">Explore the product</WpBtn>
            </div>

            {/* Trust chips */}
            <div style={{ display: 'flex', gap: 18, flexWrap: 'wrap' }}>
              {['Built for travel, not generic SaaS', 'End-to-end agency workspace', 'AI that learns your judgment'].map(t => (
                <div key={t} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <span style={{ color: T.green }}><WpIcon.check /></span>
                  <span style={{ fontSize: 12, color: T.t3 }}>{t}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Cockpit */}
          <div style={{ position: 'relative', animation: 'fadeUp 0.5s 0.15s ease both' }}>
            <HeroCockpit />
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Features + CTA ───────────────────────────────────────────────────────────
function LandingSections() {
  const T = WP;
  const [email, setEmail] = React.useState('');
  const [submitted, setSubmitted] = React.useState(false);

  const painPoints = [
    { sym: '⇄', title: 'FIT requests never arrive clean', body: 'WhatsApp notes, voice memos, screenshots, old preferences — all in different places, never structured.', color: T.cyan },
    { sym: '⚑', title: 'Margin leaks hide until quoting', body: 'Visa gaps, pacing problems, DMC friction surface after advisors have already spent hours researching.', color: T.amber },
    { sym: '↻', title: 'Quality control breaks at scale', body: 'Growing agencies need structured review points, not more status meetings.', color: T.red },
  ];

  const steps = [
    { n: '01', title: 'Intake normalization',    body: 'Scattered notes, voice memos, and messy emails parsed into a structured FIT brief — travelers, constraints, budget signals, what\'s missing.' },
    { n: '02', title: 'Risk question generation', body: 'Waypoint surfaces the 3–5 questions that actually change the itinerary: visa gaps, pacing conflicts, supplier dependencies.' },
    { n: '03', title: 'Owner review escalation', body: 'High-value or high-risk trips flagged before the proposal leaves. Internal rationale stays private; client sees only the confident output.' },
  ];

  const roles = [
    { title: 'Solo advisors',  body: 'Move faster without turning every request into a blank-page research project.' },
    { title: 'Agency owners',  body: 'See which trips need review, where quality is slipping, and which clients are waiting.' },
    { title: 'Junior agents',  body: 'Get better questions, safer drafts, and clear next steps while learning agency judgment.' },
  ];

  return (
    <div style={{ background: T.canvas, height: '100%', overflow: 'auto', fontFamily: T.fBody, color: T.t1, padding: '44px 52px 52px' }}>

      {/* ── Problem bento ── */}
      <div style={{ marginBottom: 52 }}>
        <WpKicker>Why agencies switch</WpKicker>
        <div style={{ display: 'grid', gridTemplateColumns: '1.08fr 0.92fr', gap: 12, marginTop: 6 }}>
          <div style={{
            padding: '36px 34px', borderRadius: 28, minHeight: 240,
            background: 'linear-gradient(135deg, rgba(16,20,25,0.97), rgba(8,13,17,0.99))',
            border: `1px solid ${T.b0}`,
            display: 'flex', flexDirection: 'column', justifyContent: 'flex-end',
          }}>
            <div style={{ fontSize: 36, fontWeight: 800, color: '#f5fbff', letterSpacing: '-0.04em', lineHeight: 1.05, fontFamily: T.fDisplay, marginBottom: 16 }}>
              Your best clients don't start as clean forms.
            </div>
            <p style={{ fontSize: 14.5, lineHeight: 1.72, color: T.t2, maxWidth: '40ch' }}>
              They arrive as messy conversations. Waypoint turns that mess into the brief, questions, and client-ready response your team needs to win the trip.
            </p>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {painPoints.map(p => (
              <div key={p.title} style={{
                display: 'grid', gridTemplateColumns: 'auto 1fr', gap: 14,
                padding: '18px 20px', borderRadius: 20,
                background: 'rgba(13,17,23,0.92)', border: `1px solid ${T.b0}`,
                borderLeft: `3px solid ${p.color}`,
              }}>
                <div style={{ fontSize: 18, color: p.color, lineHeight: 1, marginTop: 1 }}>{p.sym}</div>
                <div>
                  <div style={{ fontSize: 14, fontWeight: 600, color: T.t1, marginBottom: 3 }}>{p.title}</div>
                  <div style={{ fontSize: 12.5, color: T.t2, lineHeight: 1.55 }}>{p.body}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── How it works ── */}
      <div style={{ marginBottom: 52 }}>
        <WpKicker>How it works</WpKicker>
        <div style={{ fontSize: 26, fontWeight: 700, color: '#f5fbff', letterSpacing: '-0.03em', fontFamily: T.fDisplay, marginBottom: 18 }}>
          One workspace. First message to safe reply.
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 12 }}>
          {steps.map(s => (
            <div key={s.n} style={{ padding: '22px 20px', borderRadius: 20, background: 'rgba(13,17,23,0.92)', border: `1px solid ${T.b0}` }}>
              <div style={{
                width: 34, height: 34, borderRadius: 11, background: T.cyan,
                color: '#071014', display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 12, fontWeight: 800, marginBottom: 14,
              }}>{s.n}</div>
              <div style={{ fontSize: 15, fontWeight: 600, color: T.t1, marginBottom: 6 }}>{s.title}</div>
              <div style={{ fontSize: 13, color: T.t2, lineHeight: 1.62 }}>{s.body}</div>
            </div>
          ))}
        </div>
      </div>

      {/* ── Personas ── */}
      <div style={{ marginBottom: 52 }}>
        <WpKicker>Built for every role</WpKicker>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 12 }}>
          {roles.map((r, i) => (
            <div key={r.title} style={{
              padding: '22px 20px', borderRadius: 20,
              background: 'rgba(13,17,23,0.92)', border: `1px solid ${T.b0}`,
              borderTop: `2px solid ${[T.blue, T.cyan, T.amber][i]}`,
            }}>
              <div style={{ fontSize: 15, fontWeight: 700, color: T.t1, marginBottom: 8 }}>{r.title}</div>
              <div style={{ fontSize: 13, color: T.t2, lineHeight: 1.62 }}>{r.body}</div>
            </div>
          ))}
        </div>
      </div>

      {/* ── CTA + Waitlist ── */}
      <div style={{
        padding: '36px 40px', borderRadius: 26,
        background: 'linear-gradient(135deg, rgba(14,22,32,0.99), rgba(8,10,12,0.99))',
        border: '1px solid rgba(57,208,216,0.2)',
        boxShadow: '0 0 80px rgba(57,208,216,0.05)',
      }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 40, flexWrap: 'wrap' }}>
          <div style={{ flex: '1 1 360px' }}>
            <div style={{ fontSize: 24, fontWeight: 700, color: '#f5fbff', letterSpacing: '-0.02em', fontFamily: T.fDisplay, marginBottom: 8 }}>
              Run the next high-value inquiry through Waypoint.
            </div>
            <div style={{ fontSize: 14, color: T.t2, lineHeight: 1.65, marginBottom: 18 }}>
              See how the OS handles a real messy request — from inbox to client-safe output.
            </div>
            <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
              <WpBtn variant="primary" size="md">Book a demo <WpIcon.arrow /></WpBtn>
              <WpBtn variant="secondary" size="md">See a walkthrough</WpBtn>
            </div>
          </div>

          {/* Waitlist */}
          <div style={{ flex: '1 1 280px', padding: '22px 24px', borderRadius: 18, background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)' }}>
            {submitted ? (
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: 28, marginBottom: 8 }}>✓</div>
                <div style={{ fontSize: 14, fontWeight: 600, color: T.t1 }}>You're on the list.</div>
                <div style={{ fontSize: 12, color: T.t2, marginTop: 4 }}>We'll be in touch before launch.</div>
              </div>
            ) : (
              <>
                <div style={{ fontSize: 13, fontWeight: 600, color: T.t1, marginBottom: 4 }}>Not ready for a demo?</div>
                <div style={{ fontSize: 12, color: T.t2, marginBottom: 14 }}>Join the waitlist — no pressure, no spam.</div>
                <div style={{ display: 'flex', gap: 8 }}>
                  <div style={{
                    flex: 1, display: 'flex', alignItems: 'center', gap: 8,
                    padding: '8px 12px', borderRadius: 9,
                    background: T.input, border: `1px solid ${T.b1}`,
                  }}>
                    <span style={{ color: T.t4 }}><WpIcon.mail /></span>
                    <input
                      value={email}
                      onChange={e => setEmail(e.target.value)}
                      placeholder="your@agency.com"
                      style={{ flex: 1, background: 'none', border: 'none', outline: 'none', color: T.t1, fontSize: 13, fontFamily: T.fBody }}
                    />
                  </div>
                  <WpBtn variant="primary" size="sm" onClick={() => email.includes('@') && setSubmitted(true)}>
                    Join
                  </WpBtn>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 5, marginTop: 10 }}>
                  <span style={{ color: T.t4 }}><WpIcon.shield /></span>
                  <span style={{ fontSize: 11, color: T.t4 }}>No spam. Unsubscribe anytime.</span>
                </div>
              </>
            )}
          </div>
        </div>
      </div>

    </div>
  );
}

Object.assign(window, { LandingHero, LandingSections });
