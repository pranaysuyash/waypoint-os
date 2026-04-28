// wp-app.jsx — App shell prototype

const MOCK_TRIPS = [
  { id: 'WP-0093', dest: 'Portugal, 12 days',     type: 'FIT LUXURY',    client: 'Mehta family',     stage: 'review',  priority: 'critical', value: 18400, pax: 4, dates: 'Sep 14–26', sla: 'breached',  agent: null,       flags: ['VISA_GAP', 'PACING_RISK'] },
  { id: 'WP-0091', dest: 'Japan, Group FIT',       type: 'GROUP',         client: 'Chen party',       stage: 'options', priority: 'high',     value: 42000, pax: 8, dates: 'Oct 3–18',  sla: 'at_risk',   agent: 'Sara M.',  flags: [] },
  { id: 'WP-0088', dest: 'Maldives, Overwater',    type: 'FIT LUXURY',    client: 'Williams couple',  stage: 'booking', priority: 'medium',   value: 67200, pax: 2, dates: 'Nov 1–10',  sla: 'on_track',  agent: 'David K.', flags: [] },
  { id: 'WP-0086', dest: 'Patagonia Circuit',      type: 'ADVENTURE FIT', client: 'Rodriguez family', stage: 'intake',  priority: 'medium',   value: 22800, pax: 5, dates: 'Jan 8–22',  sla: 'on_track',  agent: 'Sara M.',  flags: [] },
  { id: 'WP-0084', dest: 'Safari, Tanzania',       type: 'LUXURY SAFARI', client: 'Park & Kim',       stage: 'options', priority: 'high',     value: 54600, pax: 2, dates: 'Feb 14–24', sla: 'on_track',  agent: null,       flags: ['SUPPLIER_HOLD'] },
];

// ── Sidebar ──────────────────────────────────────────────────────────────────
function WpSidebar({ active = '/inbox' }) {
  const T = WP;
  const navSections = [
    { label: 'WORK', items: [
      { href: '/inbox',     label: 'Inbox',           icon: WpIcon.inbox,  badge: 12 },
      { href: '/workspace', label: 'Workspaces',      icon: WpIcon.layers, badge: null },
      { href: '/overview',  label: 'Overview',        icon: WpIcon.grid,   badge: null },
    ]},
    { label: 'MANAGE', items: [
      { href: '/reviews',   label: 'Pending Reviews', icon: WpIcon.check2, badge: 3 },
      { href: '/analytics', label: 'Analytics',       icon: WpIcon.chart,  badge: null },
      { href: '/settings',  label: 'Settings',        icon: WpIcon.settings,badge: null },
    ]},
    { label: 'DEV', items: [
      { href: '/workbench', label: 'Workbench',       icon: WpIcon.wrench, badge: null },
    ]},
  ];

  return (
    <aside style={{
      width: 228, flexShrink: 0, display: 'flex', flexDirection: 'column',
      background: T.sidebar, borderRight: '1px solid rgba(96,111,128,0.13)',
      backgroundImage: `
        radial-gradient(circle at 50% 0%, rgba(88,166,255,0.07), transparent 55%),
        radial-gradient(circle at 80% 100%, rgba(57,208,216,0.05), transparent 46%)
      `,
    }}>
      {/* Brand */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '0 14px', height: 56, borderBottom: `1px solid ${T.b0}`, flexShrink: 0 }}>
        <div style={{
          width: 28, height: 28, borderRadius: 9, flexShrink: 0,
          background: 'linear-gradient(135deg, #2563eb, #39d0d8)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          boxShadow: '0 6px 18px rgba(37,99,235,0.28), 0 0 0 1px rgba(255,255,255,0.1)',
          color: 'white',
        }}>
          <WpIcon.pin />
        </div>
        <div style={{ minWidth: 0 }}>
          <div style={{ fontSize: 13, fontWeight: 700, color: T.t1, letterSpacing: '-0.01em', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>Waypoint</div>
          <div style={{ fontSize: 10, color: T.t4, fontFamily: T.fMono }}>v2.4 · spine-v2</div>
        </div>
      </div>

      {/* Nav */}
      <nav style={{ flex: 1, overflowY: 'auto', padding: '10px 8px' }}>
        {navSections.map(sec => (
          <div key={sec.label} style={{ marginBottom: 20 }}>
            <div style={{ padding: '0 8px 5px', fontSize: 9.5, fontWeight: 800, letterSpacing: '0.1em', textTransform: 'uppercase', color: T.t4 }}>
              {sec.label}
            </div>
            {sec.items.map(item => {
              const isActive = item.href === active;
              const Icon = item.icon;
              return (
                <div key={item.href} style={{
                  display: 'flex', alignItems: 'center', gap: 9,
                  padding: '7px 10px', margin: '1px 0', borderRadius: 7,
                  background: isActive ? 'rgba(88,166,255,0.09)' : 'transparent',
                  borderLeft: isActive ? `2px solid ${T.blue}` : '2px solid transparent',
                  color: isActive ? T.t1 : T.t2, fontSize: 13, cursor: 'pointer',
                }}>
                  <span style={{ color: isActive ? T.blue : T.t3, width: 16, flexShrink: 0 }}>
                    {Icon && <Icon />}
                  </span>
                  <span style={{ flex: 1 }}>{item.label}</span>
                  {item.badge && (
                    <span style={{
                      background: isActive ? 'rgba(88,166,255,0.18)' : 'rgba(139,148,158,0.09)',
                      color: isActive ? T.blue : T.t3,
                      fontSize: 10, fontWeight: 700, padding: '1px 6px', borderRadius: 4,
                    }}>
                      {item.badge}
                    </span>
                  )}
                </div>
              );
            })}
          </div>
        ))}
      </nav>

      {/* Status */}
      <div style={{ padding: '11px 14px', borderTop: `1px solid ${T.b0}`, flexShrink: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 7, marginBottom: 4 }}>
          <span style={{ width: 6, height: 6, borderRadius: '50%', background: T.green, boxShadow: `0 0 6px ${T.green}`, flexShrink: 0 }} />
          <span style={{ fontSize: 11, color: T.t3, fontFamily: T.fMono }}>Operations live</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
          <span style={{ color: T.amber }}><WpIcon.zap /></span>
          <span style={{ fontSize: 10, color: T.t4, fontFamily: T.fMono }}>147ms avg · spine-v2</span>
        </div>
      </div>
    </aside>
  );
}

// ── Command bar ──────────────────────────────────────────────────────────────
function WpCommandBar({ page = 'Inbox' }) {
  const T = WP;
  return (
    <header style={{
      height: 44, display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      padding: '0 18px', background: 'rgba(10,13,17,0.82)', borderBottom: `1px solid ${T.b0}`,
      backdropFilter: 'blur(12px)', flexShrink: 0,
    }}>
      <nav style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12 }}>
        <span style={{ color: T.t4 }}>Waypoint</span>
        <span style={{ color: T.b1 }}>/</span>
        <span style={{ color: T.t1, fontWeight: 500 }}>{page}</span>
      </nav>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
          <span style={{ color: T.amber }}><WpIcon.zap /></span>
          <span style={{ fontSize: 11, color: T.t3, fontFamily: T.fMono }}>ready</span>
        </div>
        <WpBtn variant="primary" size="xs">+ New trip</WpBtn>
        <div style={{ width: 28, height: 28, borderRadius: '50%', background: T.elevated, border: `1px solid ${T.b0}`, display: 'flex', alignItems: 'center', justifyContent: 'center', color: T.t2 }}>
          <WpIcon.user />
        </div>
      </div>
    </header>
  );
}

// ── Trip card ────────────────────────────────────────────────────────────────
function WpTripCard({ trip, selected = false }) {
  const T = WP;
  const prioC = { critical: T.red, high: T.amber, medium: T.blue, low: T.t3 };
  const stageC = { review: 'red', booking: 'green', options: 'blue', intake: 'cyan' };
  const slaC   = { on_track: 'green', at_risk: 'amber', breached: 'red' };

  return (
    <div style={{
      display: 'flex', cursor: 'pointer',
      background: selected ? 'rgba(88,166,255,0.04)' : trip.sla === 'breached' ? 'rgba(248,81,73,0.025)' : 'transparent',
      borderBottom: `1px solid ${T.b0}`,
      borderLeft: `3px solid ${prioC[trip.priority]}`,
      transition: 'background 150ms',
    }}>
      <div style={{ flex: 1, padding: '13px 16px', minWidth: 0 }}>

        {/* Row 1: destination + badge */}
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 8, marginBottom: 5 }}>
          <div style={{ minWidth: 0 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 7, marginBottom: 2 }}>
              <span style={{ fontSize: 14, fontWeight: 600, color: T.t1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {trip.dest}
              </span>
              {trip.flags.map(f => (
                <WpBadge key={f} color="red" style={{ fontSize: 8.5 }}>{f.replace('_', ' ')}</WpBadge>
              ))}
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <span style={{ fontSize: 10, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: T.t4 }}>{trip.type}</span>
              <span style={{ width: 2, height: 2, borderRadius: '50%', background: T.t4, flexShrink: 0 }} />
              <span style={{ fontSize: 11, color: T.t2 }}>{trip.client}</span>
            </div>
          </div>
          <WpBadge color={stageC[trip.stage]}>{trip.stage}</WpBadge>
        </div>

        {/* Row 2: metrics */}
        <div style={{
          display: 'flex', alignItems: 'center', gap: 16, padding: '6px 0',
          borderTop: `1px dashed rgba(33,38,45,0.6)`, borderBottom: `1px dashed rgba(33,38,45,0.6)`,
          margin: '4px 0',
        }}>
          {[
            { label: 'PAX',   value: trip.pax,                                             mono: false },
            { label: 'DATES', value: trip.dates,                                            mono: false },
            { label: 'VALUE', value: `$${(trip.value/1000).toFixed(1)}k`, color: T.blue,  mono: true  },
          ].map((m, i) => (
            <div key={m.label} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              {i > 0 && <div style={{ width: 1, height: 14, background: T.b0 }} />}
              <div>
                <div style={{ fontSize: 9, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: T.t4 }}>{m.label}</div>
                <div style={{ fontSize: 12, fontWeight: 500, color: m.color || T.t1, fontFamily: m.mono ? T.fMono : T.fBody }}>{m.value}</div>
              </div>
            </div>
          ))}
        </div>

        {/* Row 3: status + agent */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: 5 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <WpPill color={slaC[trip.sla]} dot>
              {{ on_track: 'On Track', at_risk: 'At Risk', breached: 'Overdue' }[trip.sla]}
            </WpPill>
            <span style={{ fontSize: 11, fontWeight: 600, color: prioC[trip.priority] }}>
              {trip.priority.charAt(0).toUpperCase() + trip.priority.slice(1)} priority
            </span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            {trip.agent ? (
              <div style={{ display: 'flex', alignItems: 'center', gap: 5, padding: '2px 8px', borderRadius: 5, background: T.elevated, border: `1px solid ${T.b0}` }}>
                <span style={{ fontSize: 11, color: T.t2 }}>{trip.agent}</span>
              </div>
            ) : (
              <span style={{ fontSize: 10.5, fontWeight: 700, textTransform: 'uppercase', color: T.amber, fontStyle: 'italic' }}>Unassigned</span>
            )}
            <span style={{ fontSize: 9, fontFamily: T.fMono, color: T.t4 }}>{trip.id}</span>
          </div>
        </div>

      </div>
    </div>
  );
}

// ── Inbox view ───────────────────────────────────────────────────────────────
function AppInbox() {
  const T = WP;
  const [activeStage, setActiveStage] = React.useState('All');
  const stages = ['All', 'Intake', 'Options', 'Review', 'Booking'];

  return (
    <div style={{ display: 'flex', height: '100%', background: T.canvas, fontFamily: T.fBody, color: T.t1, overflow: 'hidden' }}>
      <WpSidebar active="/inbox" />
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0, overflow: 'hidden' }}>
        <WpCommandBar page="Inbox" />

        {/* Filter bar */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '9px 18px', borderBottom: `1px solid ${T.b0}`, background: T.canvas, flexShrink: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '7px 12px', borderRadius: 8, background: T.input, border: `1px solid ${T.b0}`, flex: '0 0 240px' }}>
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#484f58" strokeWidth="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
            <span style={{ fontSize: 12, color: T.t4 }}>Search trips…</span>
          </div>
          <div style={{ display: 'flex', gap: 3 }}>
            {stages.map(s => {
              const on = s === activeStage;
              return (
                <button key={s} onClick={() => setActiveStage(s)} style={{
                  padding: '5px 12px', borderRadius: 999, border: 'none', cursor: 'pointer',
                  fontSize: 12, fontWeight: on ? 600 : 400,
                  background: on ? 'rgba(88,166,255,0.12)' : 'transparent',
                  color: on ? T.blue : T.t2, fontFamily: T.fBody,
                }}>
                  {s}
                </button>
              );
            })}
          </div>
          <div style={{ marginLeft: 'auto' }}>
            <WpPill color="neutral">Priority ↓</WpPill>
          </div>
        </div>

        {/* Trip list */}
        <div style={{ flex: 1, overflowY: 'auto' }}>
          {MOCK_TRIPS.map(trip => (
            <WpTripCard key={trip.id} trip={trip} />
          ))}
        </div>
      </div>
    </div>
  );
}

// ── Workspace detail view ────────────────────────────────────────────────────
function AppWorkspace() {
  const T = WP;
  const trip = MOCK_TRIPS[0];
  const [activeTab, setActiveTab] = React.useState('analysis');

  return (
    <div style={{ display: 'flex', height: '100%', background: T.canvas, fontFamily: T.fBody, color: T.t1, overflow: 'hidden' }}>
      <WpSidebar active="/workspace" />
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0, overflow: 'hidden' }}>
        <WpCommandBar page="Workspaces" />

        <div style={{ flex: 1, display: 'grid', gridTemplateColumns: '230px 1fr 252px', overflow: 'hidden', minHeight: 0 }}>

          {/* Trip list sidebar */}
          <div style={{ borderRight: `1px solid ${T.b0}`, overflowY: 'auto', background: T.sidebar }}>
            <div style={{ padding: '10px 12px 8px', fontSize: 9.5, fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.1em', color: T.t4, borderBottom: `1px solid ${T.b0}` }}>
              Active Trips
            </div>
            {MOCK_TRIPS.map((t, i) => {
              const prioC = { critical: T.red, high: T.amber, medium: T.blue, low: T.t3 };
              return (
                <div key={t.id} style={{
                  display: 'flex', alignItems: 'flex-start', gap: 8, padding: '10px 12px',
                  background: i === 0 ? 'rgba(88,166,255,0.08)' : 'transparent',
                  borderLeft: i === 0 ? `2px solid ${T.blue}` : '2px solid transparent',
                  borderBottom: `1px solid ${T.b0}`, cursor: 'pointer',
                }}>
                  <div style={{ width: 3, height: 32, borderRadius: 2, background: prioC[t.priority], flexShrink: 0, marginTop: 2 }} />
                  <div style={{ minWidth: 0 }}>
                    <div style={{ fontSize: 12, fontWeight: 600, color: i === 0 ? T.t1 : T.t2, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{t.dest}</div>
                    <div style={{ fontSize: 10, color: T.t3, marginTop: 1 }}>{t.client}</div>
                    <div style={{ marginTop: 5 }}>
                      <WpBadge color={t.flags.length ? 'red' : t.stage === 'booking' ? 'green' : 'neutral'} style={{ fontSize: 8 }}>{t.stage}</WpBadge>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Main content */}
          <div style={{ overflowY: 'auto', padding: '20px 24px', minWidth: 0 }}>
            {/* Header */}
            <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12, marginBottom: 14 }}>
              <div>
                <h2 style={{ fontSize: 22, fontWeight: 700, color: T.t1, letterSpacing: '-0.02em', fontFamily: T.fDisplay, marginBottom: 6 }}>{trip.dest}</h2>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <WpBadge color="red">Under review</WpBadge>
                  <WpBadge color="amber">Critical</WpBadge>
                  <span style={{ fontSize: 11, color: T.t4, fontFamily: T.fMono }}>{trip.id}</span>
                </div>
              </div>
              <div style={{ display: 'flex', gap: 8, flexShrink: 0 }}>
                <WpBtn variant="outline" size="sm">Send to client</WpBtn>
                <WpBtn variant="primary" size="sm">Approve</WpBtn>
              </div>
            </div>

            {/* Flags */}
            <div style={{ padding: '10px 14px', borderRadius: 10, background: 'rgba(248,81,73,0.06)', border: '1px solid rgba(248,81,73,0.2)', display: 'flex', gap: 16, marginBottom: 18 }}>
              {trip.flags.map(f => (
                <div key={f} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <span style={{ color: T.red }}><WpIcon.alert /></span>
                  <span style={{ fontSize: 12, color: T.red, fontWeight: 500 }}>{f.replace('_', ' ')}</span>
                </div>
              ))}
            </div>

            {/* Tabs */}
            <div style={{ display: 'flex', gap: 0, borderBottom: `1px solid ${T.b0}`, marginBottom: 18 }}>
              {['analysis', 'details', 'timeline'].map(tab => (
                <button key={tab} onClick={() => setActiveTab(tab)} style={{
                  padding: '8px 16px', border: 'none', cursor: 'pointer', fontFamily: T.fBody,
                  background: 'transparent', fontSize: 13, fontWeight: activeTab === tab ? 600 : 400,
                  color: activeTab === tab ? T.t1 : T.t2,
                  borderBottom: activeTab === tab ? `2px solid ${T.blue}` : '2px solid transparent',
                  marginBottom: -1,
                }}>
                  {tab.charAt(0).toUpperCase() + tab.slice(1)}
                </button>
              ))}
            </div>

            {/* AI Analysis tab */}
            {activeTab === 'analysis' && (
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14 }}>
                  <span style={{ color: T.purple }}><WpIcon.sparkles /></span>
                  <span style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: T.purple }}>AI Analysis</span>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 10, marginBottom: 18 }}>
                  {[
                    { label: 'Missing before quote', value: 'Passport validity, room split, transfer tolerance', color: T.amber },
                    { label: 'Suggested next move',  value: 'Ask 4 questions, then build two option bands',    color: T.cyan  },
                    { label: 'Owner check required', value: 'High-value repeat — review before sending',       color: T.blue  },
                  ].map(item => (
                    <div key={item.label} style={{ padding: '12px 14px', background: T.surface, borderRadius: 10, border: `1px solid ${T.b0}`, borderTop: `2px solid ${item.color}` }}>
                      <div style={{ fontSize: 9.5, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: item.color, marginBottom: 5 }}>{item.label}</div>
                      <div style={{ fontSize: 13, color: T.t1, lineHeight: 1.5 }}>{item.value}</div>
                    </div>
                  ))}
                </div>

                <WpCard style={{ padding: 0 }}>
                  <div style={{ padding: '10px 16px', borderBottom: `1px solid ${T.b0}` }}>
                    <span style={{ fontSize: 10, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: T.t3 }}>Trip Details</span>
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)' }}>
                    {[
                      { label: 'Client',    value: trip.client               },
                      { label: 'Travelers', value: `${trip.pax} pax`         },
                      { label: 'Dates',     value: trip.dates                },
                      { label: 'Budget',    value: `$${(trip.value/1000).toFixed(1)}k`, mono: true },
                    ].map((f, i) => (
                      <div key={f.label} style={{ padding: '12px 16px', borderRight: i < 3 ? `1px solid ${T.b0}` : 'none' }}>
                        <div style={{ fontSize: 9.5, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: T.t4, marginBottom: 4 }}>{f.label}</div>
                        <div style={{ fontSize: 14, color: T.t1, fontFamily: f.mono ? T.fMono : T.fBody }}>{f.value}</div>
                      </div>
                    ))}
                  </div>
                </WpCard>
              </div>
            )}

            {activeTab === 'details' && (
              <div style={{ fontSize: 13, color: T.t2, lineHeight: 1.7 }}>
                <p>Full itinerary builder, supplier assignment, and document generation would appear here in the live app.</p>
              </div>
            )}

            {activeTab === 'timeline' && (
              <div style={{ fontSize: 13, color: T.t2, lineHeight: 1.7 }}>
                <p>Full trip timeline with milestones, tasks, and communications thread appears here.</p>
              </div>
            )}
          </div>

          {/* Activity panel */}
          <div style={{ borderLeft: `1px solid ${T.b0}`, overflowY: 'auto', padding: '16px 14px', background: T.sidebar, minWidth: 0 }}>
            <div style={{ fontSize: 10, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.1em', color: T.t4, marginBottom: 14 }}>Activity</div>
            {[
              { actor: 'AI',      action: 'Flagged visa gap for Portugal entry',        time: '2m ago',  color: T.purple },
              { actor: 'Sara M.', action: 'Moved to Owner Review stage',                time: '14m ago', color: T.blue   },
              { actor: 'AI',      action: 'Extracted 4 follow-up questions from intake',time: '18m ago', color: T.purple },
              { actor: 'System',  action: 'Trip created from WhatsApp intake',          time: '1h ago',  color: T.t3     },
            ].map((ev, i, arr) => (
              <div key={i} style={{ display: 'flex', gap: 10, marginBottom: 14 }}>
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                  <div style={{ width: 7, height: 7, borderRadius: '50%', background: ev.color, flexShrink: 0, marginTop: 2 }} />
                  {i < arr.length - 1 && <div style={{ width: 1, flex: 1, background: T.b0, marginTop: 3 }} />}
                </div>
                <div style={{ flex: 1, minWidth: 0, paddingBottom: 4 }}>
                  <div style={{ fontSize: 12, color: T.t1, lineHeight: 1.45 }}>
                    <span style={{ fontWeight: 600, color: ev.color }}>{ev.actor}</span>{' '}{ev.action}
                  </div>
                  <div style={{ fontSize: 10, color: T.t4, fontFamily: T.fMono, marginTop: 2 }}>{ev.time}</div>
                </div>
              </div>
            ))}

            {/* Comments */}
            <div style={{ marginTop: 20, paddingTop: 16, borderTop: `1px solid ${T.b0}` }}>
              <div style={{ fontSize: 10, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.1em', color: T.t4, marginBottom: 10 }}>Comments</div>
              <div style={{
                display: 'flex', alignItems: 'flex-start', gap: 8, padding: '9px 10px',
                background: T.input, border: `1px solid ${T.b0}`, borderRadius: 9,
              }}>
                <span style={{ color: T.t4, marginTop: 1 }}><WpIcon.msg /></span>
                <span style={{ fontSize: 12, color: T.t4 }}>Add a note…</span>
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}

Object.assign(window, { AppInbox, AppWorkspace, WpSidebar, WpCommandBar, WpTripCard });
