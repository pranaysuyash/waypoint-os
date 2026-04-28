// wp-tokens.jsx — Design system showcase components

function DSColors() {
  const T = WP;
  const backgrounds = [
    { name: 'Canvas',    hex: '#07090b', val: T.canvas },
    { name: 'Surface',   hex: '#0d1117', val: T.surface },
    { name: 'Elevated',  hex: '#161b22', val: T.elevated },
    { name: 'Highlight', hex: '#1c2330', val: T.highlight },
    { name: 'Sidebar',   hex: '#0a0d11', val: T.sidebar },
  ];
  const accents = [
    { name: 'Blue',   hex: '#58a6ff', val: T.blue },
    { name: 'Cyan',   hex: '#39d0d8', val: T.cyan },
    { name: 'Amber',  hex: '#d29922', val: T.amber },
    { name: 'Green',  hex: '#3fb950', val: T.green },
    { name: 'Red',    hex: '#f85149', val: T.red },
    { name: 'Purple', hex: '#a371f7', val: T.purple },
  ];
  const textColors = [
    { name: 'Primary',   hex: '#e6edf3', val: T.t1 },
    { name: 'Secondary', hex: '#8b949e', val: T.t2 },
    { name: 'Tertiary',  hex: '#6e7681', val: T.t3 },
    { name: 'Muted',     hex: '#484f58', val: T.t4 },
  ];

  const dsLabel = { fontSize: 10, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: T.t3, marginBottom: 8 };

  return (
    <div style={{ background: T.canvas, padding: 28, height: '100%', fontFamily: T.fBody, color: T.t1, overflow: 'hidden' }}>
      <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.1em', textTransform: 'uppercase', color: T.t2, marginBottom: 22 }}>Color System</div>

      <div style={{ marginBottom: 22 }}>
        <div style={dsLabel}>Backgrounds</div>
        <div style={{ display: 'flex', gap: 6 }}>
          {backgrounds.map(s => (
            <div key={s.name} style={{ flex: 1 }}>
              <div style={{ height: 44, borderRadius: 8, background: s.val, border: '1px solid rgba(255,255,255,0.07)' }} />
              <div style={{ marginTop: 5, fontSize: 10, color: T.t3, lineHeight: 1.3 }}>{s.name}</div>
              <div style={{ fontSize: 9, fontFamily: T.fMono, color: T.t4 }}>{s.hex}</div>
            </div>
          ))}
        </div>
      </div>

      <div style={{ marginBottom: 22 }}>
        <div style={dsLabel}>Accents</div>
        <div style={{ display: 'flex', gap: 6 }}>
          {accents.map(s => (
            <div key={s.name} style={{ flex: 1 }}>
              <div style={{ height: 44, borderRadius: 8, background: s.val }} />
              <div style={{ marginTop: 5, fontSize: 10, color: T.t3, lineHeight: 1.3 }}>{s.name}</div>
              <div style={{ fontSize: 9, fontFamily: T.fMono, color: T.t4 }}>{s.hex}</div>
            </div>
          ))}
        </div>
      </div>

      <div style={{ marginBottom: 22 }}>
        <div style={dsLabel}>Text</div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 8 }}>
          {textColors.map(s => (
            <div key={s.name} style={{ padding: '10px 12px', background: T.surface, borderRadius: 8, border: `1px solid ${T.b0}` }}>
              <div style={{ fontSize: 20, fontWeight: 700, color: s.val, marginBottom: 4, fontFamily: T.fDisplay }}>Aa</div>
              <div style={{ fontSize: 10, color: T.t3 }}>{s.name}</div>
              <div style={{ fontSize: 9, fontFamily: T.fMono, color: T.t4 }}>{s.hex}</div>
            </div>
          ))}
        </div>
      </div>

      <div>
        <div style={dsLabel}>State Palette</div>
        <div style={{ display: 'flex', gap: 7, flexWrap: 'wrap' }}>
          {['blue','cyan','amber','green','red','purple','neutral'].map(c => (
            <WpBadge key={c} color={c}>{c}</WpBadge>
          ))}
        </div>
        <div style={{ display: 'flex', gap: 7, flexWrap: 'wrap', marginTop: 8 }}>
          {['blue','cyan','amber','green','red'].map(c => (
            <WpPill key={c} color={c} dot>{c}</WpPill>
          ))}
        </div>
      </div>
    </div>
  );
}

function DSTypography() {
  const T = WP;
  const scale = [
    { label: 'Display', size: 44, weight: 800, family: T.fDisplay, sample: 'Waypoint OS', ls: '-0.04em' },
    { label: 'H2 / 2xl', size: 28, weight: 700, family: T.fDisplay, sample: 'Agency Dashboard', ls: '-0.03em' },
    { label: 'H3 / xl',  size: 20, weight: 600, family: T.fDisplay, sample: 'Trip Workspace', ls: '-0.02em' },
    { label: 'Body base',size: 14, weight: 400, family: T.fBody,    sample: 'Run your entire agency on one intelligent platform.' },
    { label: 'Body sm',  size: 12, weight: 400, family: T.fBody,    sample: 'Stage label, metadata, caption text' },
    { label: 'Mono data',size: 12, weight: 500, family: T.fMono,    sample: 'WP-0093 · $18,400 · 0.94 conf' },
    { label: 'Kicker',   size: 10.5, weight: 600, family: T.fBody,  sample: 'BUILT FOR BOUTIQUE AGENCIES', transform: 'uppercase', ls: '0.13em' },
  ];
  return (
    <div style={{ background: T.canvas, padding: 28, height: '100%', fontFamily: T.fBody, color: T.t1, overflow: 'hidden' }}>
      <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.1em', textTransform: 'uppercase', color: T.t2, marginBottom: 22 }}>Typography</div>
      <div>
        {scale.map((item, i) => (
          <div key={i} style={{
            display: 'grid', gridTemplateColumns: '80px 1fr', gap: 14,
            padding: '11px 0', alignItems: 'center',
            borderBottom: i < scale.length - 1 ? `1px solid ${T.b0}` : 'none',
          }}>
            <div>
              <div style={{ fontSize: 9, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', color: T.t4 }}>{item.label}</div>
              <div style={{ fontSize: 9, fontFamily: T.fMono, color: T.t4, marginTop: 1 }}>{item.size}px · {item.weight}</div>
            </div>
            <div style={{
              fontSize: Math.min(item.size, 38),
              fontWeight: item.weight,
              fontFamily: item.family,
              color: T.t1,
              letterSpacing: item.ls || 'normal',
              textTransform: item.transform,
              lineHeight: 1.2,
              overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
            }}>
              {item.sample}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function DSComponents() {
  const T = WP;
  return (
    <div style={{ background: T.canvas, padding: 28, height: '100%', fontFamily: T.fBody, color: T.t1, overflow: 'hidden' }}>
      <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.1em', textTransform: 'uppercase', color: T.t2, marginBottom: 22 }}>Components</div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>

        <div>
          <div style={{ fontSize: 10, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: T.t3, marginBottom: 10 }}>Buttons</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8, alignItems: 'flex-start' }}>
            <WpBtn variant="primary"   size="sm">Book a demo <WpIcon.arrow /></WpBtn>
            <WpBtn variant="secondary" size="sm">Explore product</WpBtn>
            <WpBtn variant="ghost"     size="sm">Sign in</WpBtn>
            <WpBtn variant="danger"    size="sm">Cancel trip</WpBtn>
          </div>
        </div>

        <div>
          <div style={{ fontSize: 10, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: T.t3, marginBottom: 10 }}>Badges + Pills</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            <div style={{ display: 'flex', gap: 5, flexWrap: 'wrap' }}>
              <WpBadge color="green">Booking</WpBadge>
              <WpBadge color="amber">Review</WpBadge>
              <WpBadge color="red">Overdue</WpBadge>
            </div>
            <div style={{ display: 'flex', gap: 5, flexWrap: 'wrap' }}>
              <WpBadge color="blue">Options</WpBadge>
              <WpBadge color="cyan">AI Active</WpBadge>
              <WpBadge color="purple">Owner</WpBadge>
            </div>
            <div style={{ display: 'flex', gap: 5 }}>
              <WpPill color="green" dot>On Track</WpPill>
              <WpPill color="amber" dot>At Risk</WpPill>
              <WpPill color="red"   dot>Overdue</WpPill>
            </div>
          </div>
        </div>

        <div style={{ gridColumn: 'span 2' }}>
          <div style={{ fontSize: 10, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: T.t3, marginBottom: 10 }}>Cards</div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 10 }}>
            <WpCard style={{ padding: 14 }}>
              <div style={{ fontSize: 9.5, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: T.t3, marginBottom: 5 }}>Standard</div>
              <div style={{ fontSize: 13, fontWeight: 600, color: T.t1 }}>Portugal · FIT</div>
              <div style={{ fontSize: 11, color: T.t2, marginTop: 2 }}>Mehta family · $18k</div>
            </WpCard>
            <div style={{ padding: 14, borderRadius: 12, background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)' }}>
              <div style={{ fontSize: 9.5, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: T.t3, marginBottom: 5 }}>Glass</div>
              <div style={{ fontSize: 13, fontWeight: 600, color: T.t1 }}>Japan · Group</div>
              <div style={{ fontSize: 11, color: T.t2, marginTop: 2 }}>Chen party · $42k</div>
            </div>
            <WpCard style={{ padding: 14, borderColor: 'rgba(57,208,216,0.25)' }} accent="cyan">
              <div style={{ fontSize: 9.5, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: T.cyan, marginBottom: 5 }}>Accent</div>
              <div style={{ fontSize: 13, fontWeight: 600, color: T.t1 }}>Maldives · FIT</div>
              <div style={{ fontSize: 11, color: T.t2, marginTop: 2 }}>Williams · $67k</div>
            </WpCard>
          </div>
        </div>

        <div style={{ gridColumn: 'span 2' }}>
          <div style={{ fontSize: 10, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: T.t3, marginBottom: 10 }}>Navigation (improved active state)</div>
          <div style={{ background: T.sidebar, borderRadius: 10, border: `1px solid ${T.b0}`, overflow: 'hidden' }}>
            {[
              { label: 'Inbox',      icon: 'inbox',  active: true,  badge: 12 },
              { label: 'Workspaces', icon: 'layers', active: false, badge: null },
              { label: 'Overview',   icon: 'grid',   active: false, badge: null },
            ].map(item => {
              const Icon = { inbox: WpIcon.inbox, layers: WpIcon.layers, grid: WpIcon.grid }[item.icon];
              return (
                <div key={item.label} style={{
                  display: 'flex', alignItems: 'center', gap: 9, padding: '8px 12px',
                  background: item.active ? 'rgba(88,166,255,0.08)' : 'transparent',
                  borderLeft: item.active ? '2px solid #58a6ff' : '2px solid transparent',
                  color: item.active ? T.t1 : T.t2, fontSize: 13,
                }}>
                  <span style={{ color: item.active ? T.blue : T.t3, width: 16 }}>{Icon && <Icon />}</span>
                  <span style={{ flex: 1 }}>{item.label}</span>
                  {item.badge && (
                    <span style={{ background: item.active ? 'rgba(88,166,255,0.15)' : 'rgba(139,148,158,0.1)', color: item.active ? T.blue : T.t3, fontSize: 10, fontWeight: 700, padding: '1px 6px', borderRadius: 4 }}>{item.badge}</span>
                  )}
                </div>
              );
            })}
          </div>
        </div>

      </div>
    </div>
  );
}

Object.assign(window, { DSColors, DSTypography, DSComponents });
