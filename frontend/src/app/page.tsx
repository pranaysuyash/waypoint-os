import Link from 'next/link';
import {
  Activity,
  ArrowRight,
  BarChart3,
  Check,
  CheckCircle2,
  ClipboardCheck,
  Edit3,
  FileText,
  HelpCircle,
  Inbox,
  Lock,
  RefreshCw,
  Search,
  Shield,
  Sparkles,
  Users,
  Zap,
} from 'lucide-react';
import {
  Kicker,
  PublicFooter,
  PublicHeader,
  PublicPage,
  SectionIntro,
} from '@/components/marketing/marketing';
import { CtaBand } from '@/components/marketing/marketing-client';
import { AgencyHeroCockpit } from '@/components/marketing/MarketingVisuals';
import { GsapInitializer } from '@/components/marketing/GsapInitializer';
import styles from '@/components/marketing/marketing.module.css';

// ── Data ─────────────────────────────────────────────────────────────────────

const pipelineStages = [
  { icon: Inbox,        label: 'Inbox',                  body: 'Capture every inquiry across all channels.' },
  { icon: FileText,     label: 'Intake Workspace',        body: 'Qualify, brief, and align on traveler goals.' },
  { icon: HelpCircle,   label: 'Decision & Clarification',body: 'Surface preferences, ask the right questions.' },
  { icon: BarChart3,    label: 'Quote / Option Builder',  body: 'Build smart options, price with confidence.' },
  { icon: ClipboardCheck,label:'Booking Readiness',       body: 'Verify details, docs, and supplier holds.' },
  { icon: RefreshCw,    label: 'Change Handling',         body: 'Manage changes, rebooking, and refunds.' },
  { icon: BarChart3,    label: 'Owner Console',           body: 'Oversee performance, people, and profit.' },
];

const workspaceTypes = [
  { label: 'Intake Workspace',          color: '#39d0d8', body: 'Capture and qualify new inquiries with AI.' },
  { label: 'Decision & Clarification',  color: '#58a6ff', body: 'Ask the right questions before you build.' },
  { label: 'Quote / Option Builder',    color: '#39d0d8', body: 'Build beautiful, profitable options in minutes.' },
  { label: 'Booking Readiness',         color: '#3fb950', body: 'Confirm, collect, and prep for smooth execution.' },
  { label: 'Change Handling',           color: '#d29922', body: 'Handle changes without chaos or revenue leakage.' },
  { label: 'Owner Console',             color: '#a371f7', body: 'Lead with live data and actionable metrics.' },
];

const aiCapabilities = [
  { icon: Search,    label: 'Research',    body: 'Find the right hotels, experiences, and routes in seconds.' },
  { icon: Edit3,     label: 'Draft',       body: 'Create proposals, itineraries, and emails in your brand voice.' },
  { icon: Shield,    label: 'Verify',      body: 'Cross-check details, policies, and supplier information.' },
  { icon: FileText,  label: 'Summarize',   body: 'Condense threads, notes, and docs into clear next steps.' },
  { icon: Zap,       label: 'Orchestrate', body: 'Route work, set tasks, and keep deals moving forward.' },
];

const personaCards = [
  {
    icon: Users,
    title: 'Solo Agents',
    body: 'Be an agency of one — without the overwhelm.',
    accentColor: '#58a6ff',
    bullets: ['Run your full pipeline in one place', 'Save hours every week', 'Win more, with less stress'],
  },
  {
    icon: BarChart3,
    title: 'Agency Owners',
    body: 'Lead with clarity. Grow with confidence.',
    accentColor: '#39d0d8',
    bullets: ['Real-time performance and profit', 'Coach and align your team', 'Scale without scaling chaos'],
  },
  {
    icon: Sparkles,
    title: 'Junior Agents',
    body: 'Do your best work. Learn and grow.',
    accentColor: '#d29922',
    bullets: ['Guided workflows and prompts', 'Fewer mistakes, faster ramp', 'More confidence, more impact'],
  },
];

const trustItems = [
  { icon: Lock,          title: 'Security first',        body: 'Enterprise-grade security, SSO, and role-based access control.' },
  { icon: Shield,        title: 'Private & compliant',   body: 'Your data is private. We never train on your agency content.' },
  { icon: Users,         title: 'Supplier network',      body: 'Work with your preferred partners. Your relationships, your terms.' },
  { icon: ClipboardCheck,title: 'Audit & accountability',body: 'Full activity logs, approvals, and change history for every trip.' },
  { icon: Activity,      title: 'Uptime you can rely on',body: '99.9% uptime with redundant infrastructure and daily backups.' },
];

const productMoments = [
  {
    label: '01',
    title: 'Intake normalization',
    body: 'Scattered WhatsApp notes, voice memos, and messy emails are parsed into a structured FIT brief: travelers, dates, constraints, budget signals, and what is explicitly missing.',
  },
  {
    label: '02',
    title: 'Risk question generation',
    body: 'Waypoint surfaces the 3–5 questions that actually change the itinerary — visa gaps, pacing conflicts, supplier dependencies — before advisors start building.',
  },
  {
    label: '03',
    title: 'Owner review escalation',
    body: 'High-value or high-risk trips are flagged for owner check before the proposal leaves. Internal rationale stays inside the agency; the client sees only the confident output.',
  },
];

// ── Page ─────────────────────────────────────────────────────────────────────

export default function HomePage() {
  return (
    <PublicPage>
      <GsapInitializer />
      <PublicHeader
        ctaHref='/signup'
        ctaLabel='Book a demo'
        navItems={[
          { href: '#product',   label: 'Product'      },
          { href: '#workflow',  label: 'Solutions'    },
          { href: '#personas',  label: 'For Agencies' },
          { href: '#resources', label: 'Resources'    },
          { href: '#pricing',   label: 'Pricing'      },
        ]}
      />

      {/* ── Hero ── */}
      <section className={`${styles.hero} ${styles.visualHero} ${styles.agencyHero} animate-fade-up`}>
        <div className={`${styles.heroCopy} animate-stagger-container`}>
          <div className={styles.eyebrow}>Built for boutique agencies</div>
          <h1 className={`${styles.heroTitle} font-display`}>Waypoint OS</h1>
          <h2 className={styles.heroSubtitle}>The operating system for boutique travel agencies.</h2>
          <p className={styles.heroBody}>
            From messy WhatsApp notes to client-safe proposals, Waypoint structures the intake,
            surfaces the risks, and protects your margins. The public itinerary checker gives
            travelers a cleaner brief before they ask you to build. Upload a PDF itinerary or
            paste a travel plan to score weak points first.
          </p>
          <div className={styles.heroActions}>
            <Link href='/signup' className={styles.primaryButton}>
              Book a demo
              <ArrowRight className='h-4 w-4' />
            </Link>
            <Link href='/itinerary-checker' className={styles.secondaryButton}>
              See the public checker
            </Link>
          </div>
          <div className='flex flex-wrap gap-x-5 gap-y-2 mt-6'>
            {[
              'Built for travel, not generic SaaS',
              'End-to-end agency workspace',
              'Public checker for traveler-led plan audits',
            ].map((t) => (
              <div key={t} className='flex items-center gap-1.5'>
                <Check className='h-3.5 w-3.5 text-[#3fb950] shrink-0' />
                <span className='text-[12px] text-[#6e7681]'>{t}</span>
              </div>
            ))}
          </div>
        </div>
        <AgencyHeroCockpit />
      </section>

      {/* ── Industry contrast ── */}
      <section className={`${styles.section} ${styles.industryContrast} animate-fade-up`} id='product'>
        <div className={styles.contrastLeft}>
          <p className={styles.contrastKicker}>The industry has changed.</p>
          <h2 className={`${styles.contrastHeadline} font-display`}>
            Your tools<br />
            <span className={styles.contrastAccent}>haven&apos;t.</span>
          </h2>
          <div className={styles.contrastPainList}>
            {[
              'Scattered tools. Lost context.',
              'Manual updates. Missed details.',
              'No visibility. Hard to lead.',
              'Profit leaks you can\'t see.',
            ].map((p) => (
              <div key={p} className={styles.contrastPainItem}>
                <span className={styles.contrastX}>✕</span>
                <span>{p}</span>
              </div>
            ))}
          </div>
        </div>
        <div className={styles.contrastRight}>
          <p className={styles.contrastKicker}>Waypoint OS brings your agency together.</p>
          <p className={styles.contrastBody}>
            One intelligent workspace that connects your people, processes, and partners —
            with AI that works alongside your team, not instead of them.
          </p>
          <div className={styles.contrastGoodList}>
            {[
              'One system. End-to-end.',
              'AI that assists, not replaces.',
              'Real-time visibility and control.',
              'More profit. Less busywork.',
            ].map((p) => (
              <div key={p} className={styles.contrastGoodItem}>
                <Check className='h-4 w-4 text-[#3fb950] shrink-0' />
                <span>{p}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Pipeline diagram ── */}
      <section className={`${styles.section} ${styles.pipelineSection} animate-fade-up`}>
        <div className={styles.pipelineHeader}>
          <h2 className='font-display'>Your complete agency workspace</h2>
          <p>Every workspace. Every handoff. One unified operating system.</p>
        </div>
        <div className={styles.pipeline}>
          {pipelineStages.map((stage, i) => {
            const Icon = stage.icon;
            return (
              <div key={stage.label} className={styles.pipelineStageWrap}>
                <div className={styles.pipelineStage}>
                  <div className={styles.pipelineIcon}>
                    <Icon className='h-5 w-5' />
                  </div>
                  <div className={styles.pipelineLabel}>{stage.label}</div>
                  <div className={styles.pipelineBody}>{stage.body}</div>
                </div>
                {i < pipelineStages.length - 1 && (
                  <div className={styles.pipelineArrow}>→</div>
                )}
              </div>
            );
          })}
        </div>
      </section>

      {/* ── Workspace detail ── */}
      <section className={`${styles.section} ${styles.workspaceSection} animate-fade-up`} id='workflow'>
        <div className={styles.workspaceCopy}>
          <Kicker>Built for how you work</Kicker>
          <h2 className='font-display'>Workspaces that move work forward</h2>
          <p>
            Purpose-built environments for each stage of the traveler journey.
            Context flows. Nothing falls through.
          </p>
          <div className={styles.workspaceTypeList}>
            {workspaceTypes.map((w) => (
              <div key={w.label} className={styles.workspaceTypeItem}>
                <span className={styles.workspaceTypeDot} style={{ background: w.color }} />
                <div>
                  <strong>{w.label}</strong>
                  <span>{w.body}</span>
                </div>
                <ArrowRight className='h-4 w-4 text-[#484f58] shrink-0' />
              </div>
            ))}
          </div>
        </div>
        <div className={styles.workspaceMockup}>
          <div className={styles.mockupBar}>
            <span className={styles.mockupBarTitle}>Intake Workspace</span>
            <span className={styles.mockupBarChip}>Move to Decision →</span>
          </div>
          <div className={styles.mockupTabs}>
            {['Overview','Brief','Travelers','Notes','Files','Activity'].map((t, i) => (
              <span key={t} className={i === 0 ? styles.mockupTabActive : styles.mockupTab}>{t}</span>
            ))}
          </div>
          <div className={styles.mockupBody}>
            <div className={styles.mockupLeft}>
              <div className={styles.mockupTripTitle}>Italy Honeymoon <span className={styles.mockupNew}>New</span></div>
              <div className={styles.mockupTripSub}>Arnab Couri &amp; Puja</div>
              <div className={styles.mockupMetaGrid}>
                  {([
                    ['Channel','Website'],
                    ['Traveler','Jessica & Michael'],
                    ['Travel window','Sep 7 – Sep 18'],
                    ['Budget','$8,500 – $12,000'],
                    ['Travel style','Romantic, Relaxed, Culture'],
                    ['Lead score','High'],
                  ] as const).map(([k,v]) => (
                    <div key={k} className={styles.mockupMetaRow}>
                      <span>{k}</span>
                      <strong>{v}</strong>
                    </div>
                  ))}
              </div>
            </div>
            <div className={styles.mockupRight}>
              <div className={styles.mockupAiHeader}>
                <Sparkles className='h-3.5 w-3.5 text-[#a371f7]' />
                <span>AI Briefing</span>
              </div>
              <p className={styles.mockupAiBody}>
                A romantic 10–12 day Italy honeymoon focused on coastal relaxation, exceptional food &amp; wine, and memorable experiences.
              </p>
              <div className={styles.mockupNextSteps}>
                <div className={styles.mockupNextHeader}>AI Suggested Next Steps</div>
                {[
                  'Confirm preferred arrival city',
                  'Top 3 experiences to consider',
                  'Budget alignment check',
                ].map((s) => (
                  <div key={s} className={styles.mockupStep}>
                    <CheckCircle2 className='h-3.5 w-3.5 text-[#39d0d8] shrink-0' />
                    <span>{s}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── How it works ── */}
      <section className={`${styles.section} ${styles.productStory} animate-fade-up`}>
        <div className='animate-fade-up'>
          <SectionIntro
            eyebrow='How it works'
            title='One workspace from first message to safe reply.'
            body='Waypoint does not replace your agency judgment. It gives that judgment a place to live, repeat, and scale.'
          />
        </div>
        <div className={`${styles.momentStack} animate-stagger-container`}>
          {productMoments.map((moment) => (
            <article key={moment.title} className={styles.momentItem}>
              <span>{moment.label}</span>
              <div>
                <h3>{moment.title}</h3>
                <p>{moment.body}</p>
              </div>
            </article>
          ))}
        </div>
      </section>

      {/* ── AI capabilities ── */}
      <section className={`${styles.section} ${styles.aiSection} animate-fade-up`}>
        <div className={styles.aiSectionHeader}>
          <Kicker>AI that works with you</Kicker>
          <h2 className='font-display'>Your AI copilot.<br />Trained on travel.<br />Aligned to your process.</h2>
        </div>
        <div className={styles.aiGrid}>
          {aiCapabilities.map((cap) => {
            const Icon = cap.icon;
            return (
              <div key={cap.label} className={styles.aiCell}>
                <div className={styles.aiCellIcon}>
                  <Icon className='h-5 w-5' />
                </div>
                <div className={styles.aiCellLabel}>{cap.label}</div>
                <div className={styles.aiCellBody}>{cap.body}</div>
              </div>
            );
          })}
        </div>
        <div className={styles.aiPrivacyNote}>
          <Lock className='h-4 w-4 text-[#3fb950] shrink-0' />
          <span>Private by design. Your data stays yours. Models don&apos;t train on your content.</span>
        </div>
      </section>

      {/* ── Personas ── */}
      <section className={`${styles.section} ${styles.personaBand} animate-fade-up`} id='personas'>
        <div className={`${styles.personaBandHeader} animate-fade-up`}>
          <Kicker>Built for every role in your agency</Kicker>
          <h2 className='font-display'>Built for every role in your agency</h2>
        </div>
        <div className={`${styles.personaStrip} animate-stagger-container`}>
          {personaCards.map((card) => {
            const Icon = card.icon;
            return (
              <article key={card.title} style={{ borderTop: `2px solid ${card.accentColor}` }}>
                <div className={styles.personaIconWrap} style={{ color: card.accentColor }}>
                  <Icon className='h-5 w-5' />
                </div>
                <h3>{card.title}</h3>
                <p>{card.body}</p>
                <ul className={styles.personaBullets}>
                  {card.bullets.map((b) => (
                    <li key={b}>
                      <Check className='h-3.5 w-3.5 shrink-0' style={{ color: card.accentColor }} />
                      <span>{b}</span>
                    </li>
                  ))}
                </ul>
                <Link href='/signup' className={styles.personaCta}>
                  See how it helps <ArrowRight className='h-3.5 w-3.5' />
                </Link>
              </article>
            );
          })}
        </div>
      </section>

      {/* ── Trust / operations ── */}
      <section className={`${styles.section} ${styles.trustSection} animate-fade-up`} id='resources'>
        <div className={styles.trustIntro}>
          <Kicker>Built for trust. Designed for operations.</Kicker>
          <h2 className='font-display'>Built for trust.<br />Designed for operations.</h2>
        </div>
        <div className={`${styles.operationsGrid} animate-stagger-container`}>
          {trustItems.map((item) => {
            const Icon = item.icon;
            return (
              <div key={item.title} className={styles.operationsCell}>
                <div className={styles.operationsCellIcon}>
                  <Icon className='h-5 w-5' />
                </div>
                <h3>{item.title}</h3>
                <p>{item.body}</p>
              </div>
            );
          })}
        </div>
      </section>

      {/* ── Wedge / itinerary checker ── */}
      <section className={`${styles.section} ${styles.wedgeSection} animate-fade-up`}>
        <div className='animate-fade-up'>
          <Kicker>Free public tool</Kicker>
          <h2 className='font-display'>Bring your itinerary or travel plan. Get it scored.<br />Free, no account needed.</h2>
          <p>
            Think of it like an ATS for resumes, but for itineraries and travel plans. The checker scores the itinerary
            you already have, flags weak spots, and gives travelers cleaner context than any generic
            contact form. Upload a PDF itinerary or paste a travel plan to see the gaps before you ask
            for a proposal. It is a public plan-audit layer, not a replacement for agency work.
          </p>
          <div className={styles.wedgeActions}>
            <Link href='/itinerary-checker' className={styles.primaryButton}>
              Try the free itinerary checker
              <ArrowRight className='h-4 w-4' />
            </Link>
          </div>
        </div>
        <div className={styles.wedgeMock}>
          <span>Uploaded plan</span>
          <strong>Portugal, 9 days, family of four</strong>
          <p>Waypoint found 3 timing risks, 2 document questions, and 1 day worth simplifying.</p>
        </div>
      </section>

      <div id='pricing'>
        <CtaBand
          title='Run a smarter agency. Deliver better trips. Grow profitably.'
          body='See Waypoint OS in action. Personalized demo, no pressure.'
          primaryHref='/signup'
          primaryLabel='Book a demo'
          secondaryHref='/itinerary-checker'
          secondaryLabel='See the public checker'
        />
      </div>

      <PublicFooter />
    </PublicPage>
  );
}
