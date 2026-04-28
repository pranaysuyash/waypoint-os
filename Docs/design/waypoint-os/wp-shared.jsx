// wp-shared.jsx — Design tokens + base components for Waypoint OS

const WP = {
  canvas:   '#07090b',
  surface:  '#0d1117',
  elevated: '#161b22',
  highlight:'#1c2330',
  sidebar:  '#0a0d11',
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
  bGlass: 'rgba(255,255,255,0.08)',
  fDisplay: "'Outfit', system-ui, sans-serif",
  fBody:    "'Inter', system-ui, sans-serif",
  fMono:    "'JetBrains Mono', monospace",
};

const WP_C = {
  blue:    { text: '#58a6ff', bg: 'rgba(88,166,255,0.1)',   border: 'rgba(88,166,255,0.22)'  },
  cyan:    { text: '#39d0d8', bg: 'rgba(57,208,216,0.1)',   border: 'rgba(57,208,216,0.22)'  },
  amber:   { text: '#d29922', bg: 'rgba(210,153,34,0.12)',  border: 'rgba(210,153,34,0.25)'  },
  green:   { text: '#3fb950', bg: 'rgba(63,185,80,0.1)',    border: 'rgba(63,185,80,0.22)'   },
  red:     { text: '#f85149', bg: 'rgba(248,81,73,0.1)',    border: 'rgba(248,81,73,0.22)'   },
  purple:  { text: '#a371f7', bg: 'rgba(163,113,247,0.1)',  border: 'rgba(163,113,247,0.22)' },
  neutral: { text: '#8b949e', bg: 'rgba(139,148,158,0.08)', border: 'rgba(139,148,158,0.15)' },
};

// ── Button ──────────────────────────────────────────────────────────────────
function WpBtn({ children, variant = 'primary', size = 'md', onClick, style: ext = {} }) {
  const wpBtnSz = {
    xs: { height: 28, padding: '0 10px', fontSize: 11, borderRadius: 999 },
    sm: { height: 34, padding: '0 14px', fontSize: 12, borderRadius: 999 },
    md: { height: 42, padding: '0 20px', fontSize: 13, borderRadius: 999 },
    lg: { height: 48, padding: '0 24px', fontSize: 14, borderRadius: 999 },
  };
  const wpBtnV = {
    primary: {
      background: 'linear-gradient(135deg, #7ab9ff 0%, #57e0ef 50%, #39d0d8 100%)',
      color: '#071018',
      boxShadow: '0 8px 24px rgba(57,208,216,0.3), inset 0 1px 0 rgba(255,255,255,0.38)',
      border: 'none',
    },
    secondary: {
      background: 'linear-gradient(180deg, rgba(13,23,33,0.8), rgba(10,18,26,0.8))',
      color: '#e6edf3',
      border: '1px solid rgba(88,166,255,0.22)',
      borderRadius: 14,
      boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.05)',
    },
    ghost: {
      background: 'rgba(15,17,21,0.72)',
      color: '#c9d1d9',
      border: '1px solid rgba(168,179,193,0.14)',
    },
    outline: { background: 'transparent', color: '#e6edf3', border: '1px solid #30363d' },
    danger:  { background: 'rgba(248,81,73,0.1)', color: '#f85149', border: '1px solid rgba(248,81,73,0.25)', borderRadius: 8 },
  };
  return (
    <button onClick={onClick} style={{
      display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
      gap: 7, cursor: 'pointer', fontFamily: WP.fBody, fontWeight: 600,
      transition: 'all 160ms ease', userSelect: 'none',
      ...wpBtnSz[size], ...wpBtnV[variant], ...ext,
    }}>
      {children}
    </button>
  );
}

// ── Badge ───────────────────────────────────────────────────────────────────
function WpBadge({ children, color = 'neutral', style: ext = {} }) {
  const c = WP_C[color] || WP_C.neutral;
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 4,
      padding: '2px 7px', borderRadius: 5,
      fontSize: 10, fontWeight: 700, fontFamily: WP.fMono,
      textTransform: 'uppercase', letterSpacing: '0.04em',
      color: c.text, background: c.bg, border: `1px solid ${c.border}`,
      ...ext,
    }}>
      {children}
    </span>
  );
}

// ── Pill ────────────────────────────────────────────────────────────────────
function WpPill({ children, color = 'neutral', dot = false, style: ext = {} }) {
  const c = WP_C[color] || WP_C.neutral;
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 5,
      padding: '3px 10px', borderRadius: 999, fontSize: 11, fontWeight: 500,
      color: c.text, background: c.bg, ...ext,
    }}>
      {dot && <span style={{ width: 5, height: 5, borderRadius: '50%', background: c.text, flexShrink: 0 }} />}
      {children}
    </span>
  );
}

// ── Card ────────────────────────────────────────────────────────────────────
function WpCard({ children, style: ext = {}, accent }) {
  const glowMap = { blue: '0 0 28px rgba(88,166,255,0.1)', cyan: '0 0 28px rgba(57,208,216,0.1)', amber: '0 0 28px rgba(210,153,34,0.12)', green: '0 0 28px rgba(63,185,80,0.1)' };
  return (
    <div style={{
      background: WP.surface,
      border: `1px solid ${WP.b0}`,
      borderRadius: 12,
      boxShadow: `0 2px 8px rgba(0,0,0,0.2), inset 0 1px 0 rgba(255,255,255,0.04)${accent ? `, ${glowMap[accent] || ''}` : ''}`,
      overflow: 'hidden', ...ext,
    }}>
      {children}
    </div>
  );
}

// ── Kicker ──────────────────────────────────────────────────────────────────
function WpKicker({ children }) {
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 7,
      padding: '5px 12px', borderRadius: 999, marginBottom: 14,
      color: '#d8eef0', fontSize: 10.5, letterSpacing: '0.13em',
      textTransform: 'uppercase', fontFamily: WP.fBody, fontWeight: 600,
      border: '1px solid rgba(57,208,216,0.22)',
      background: 'rgba(7,22,26,0.8)',
    }}>
      <span style={{ width: 5, height: 5, borderRadius: '50%', background: '#39d0d8', boxShadow: '0 0 5px #39d0d8', flexShrink: 0 }} />
      {children}
    </span>
  );
}

// ── Icons ───────────────────────────────────────────────────────────────────
const WpIcon = {
  arrow:    () => <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="5" y1="12" x2="19" y2="12" /><polyline points="12 5 19 12 12 19" /></svg>,
  check:    () => <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="20 6 9 17 4 12" /></svg>,
  pin:      () => <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z"/><circle cx="12" cy="10" r="3"/></svg>,
  inbox:    () => <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="22 12 16 12 14 15 10 15 8 12 2 12"/><path d="M5.45 5.11L2 12v6a2 2 0 002 2h16a2 2 0 002-2v-6l-3.45-6.89A2 2 0 0016.76 4H7.24a2 2 0 00-1.79 1.11z"/></svg>,
  layers:   () => <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg>,
  grid:     () => <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>,
  check2:   () => <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="9 11 12 14 22 4"/><path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/></svg>,
  chart:    () => <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>,
  settings: () => <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z"/></svg>,
  wrench:   () => <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M14.7 6.3a1 1 0 000 1.4l1.6 1.6a1 1 0 001.4 0l3.77-3.77a6 6 0 01-7.94 7.94l-6.91 6.91a2.12 2.12 0 01-3-3l6.91-6.91a6 6 0 017.94-7.94l-3.76 3.76z"/></svg>,
  alert:    () => <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>,
  sparkles: () => <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 3l1.5 4.5L18 9l-4.5 1.5L12 15l-1.5-4.5L6 9l4.5-1.5z"/><path d="M19 3l.75 2.25L22 6l-2.25.75L19 9l-.75-2.25L16 6l2.25-.75z"/></svg>,
  zap:      () => <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>,
  user:     () => <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>,
  mail:     () => <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>,
  shield:   () => <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>,
  msg:      () => <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/></svg>,
  clock:    () => <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>,
};

Object.assign(window, { WP, WP_C, WpBtn, WpBadge, WpPill, WpCard, WpKicker, WpIcon });
