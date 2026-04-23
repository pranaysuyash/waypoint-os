import Link from 'next/link';
import {
  ArrowRight,
  Briefcase,
  Building2,
  CheckCircle2,
  ClipboardCheck,
  Clock3,
  FolderKanban,
  Layers3,
  MessageSquareText,
  Shield,
  Sparkles,
  Workflow,
} from 'lucide-react';
import {
  BulletList,
  CtaBand,
  HeroStat,
  Kicker,
  ProofChip,
  PublicFooter,
  PublicHeader,
  PublicPage,
  SectionIntro,
} from '@/components/marketing/marketing';
import styles from '@/components/marketing/marketing.module.css';

const surfaces = [
  {
    icon: MessageSquareText,
    title: 'Inbox + intent extraction',
    body: 'Turn WhatsApp chaos, notes, and half-complete asks into a structured brief with blocker-aware follow-up.',
    details: ['What we know', 'Need to clarify', 'Suggested next move'],
  },
  {
    icon: Layers3,
    title: 'Intake workspace',
    body: 'Keep raw context, extracted facts, traveler fit, and operator notes in one working surface.',
    details: ['Raw note and evidence', 'Trip packet maturity', 'Traveler-safe draft'],
  },
  {
    icon: Workflow,
    title: 'Decision + clarification',
    body: 'Expose hard blockers, soft blockers, feasibility tension, and the exact questions that unlock quoting.',
    details: ['Decision state', 'Risk flags', 'Follow-up pack'],
  },
  {
    icon: FolderKanban,
    title: 'Quote and option builder',
    body: 'Sequence the commercial logic behind your proposal before anything reaches the traveler.',
    details: ['Option framing', 'Trade-off logic', 'Internal notes'],
  },
  {
    icon: ClipboardCheck,
    title: 'Booking readiness',
    body: 'Prevent operational mistakes with checklists for docs, payments, confirmations, and execution handoff.',
    details: ['Readiness checks', 'Vendor coordination', 'Trip master record'],
  },
  {
    icon: Building2,
    title: 'Owner console',
    body: 'Give owners SLA visibility, review queues, exception control, and quality oversight across the team.',
    details: ['Reviews queue', 'Workload radar', 'Conversion diagnostics'],
  },
];

const personaCards = [
  {
    title: 'Solo agents',
    body: 'Respond faster, ask sharper follow-ups, and protect quality without hiring a second brain.',
    bullets: ['Inbox-to-options in minutes', 'Traveler memory across repeat trips', 'Less rework on vague inquiries'],
  },
  {
    title: 'Agency owners',
    body: 'Turn institutional knowledge into an operating system instead of depending on whoever is online.',
    bullets: ['Quality visibility across the team', 'Owner review where it matters', 'Fewer silent operational misses'],
  },
  {
    title: 'Junior agents',
    body: 'Teach judgment in the flow of work instead of through scattered corrections after the fact.',
    bullets: ['Prompted questions and next steps', 'Coaching signals before mistakes ship', 'Clear internal vs customer-facing output'],
  },
];

const proofCards = [
  {
    title: 'Commercially grounded sourcing',
    body: 'Waypoint OS mirrors the real agency hierarchy: preferred supply first, open market only when justified.',
  },
  {
    title: 'Traveler-safe output boundaries',
    body: 'Internal confidence, blocker logic, and rationale stay on the operator side. The traveler sees a safe message.',
  },
  {
    title: 'Operational risk reduction',
    body: 'Suitability, pacing, logistics, visa/document checks, and review states live inside the workflow instead of outside it.',
  },
];

export default function HomePage() {
  return (
    <PublicPage>
      <PublicHeader ctaHref='/signup' ctaLabel='Create workspace' />

      <section className={styles.hero}>
        <div className={styles.heroCopy}>
          <div className={styles.eyebrow}>Agency Copilot for real travel operations</div>
          <h1 className={styles.heroTitle}>The operating system for boutique travel agencies</h1>
          <p className={styles.heroBody}>
            Waypoint OS compresses the workflow from messy lead intake to confident, traveler-safe execution.
            It is built for the one-person planner, the growing agency owner, and the junior agent who needs
            guidance before mistakes reach the client.
          </p>

          <div className={styles.heroActions}>
            <Link href='/signup' className={styles.primaryButton}>
              Create workspace
              <ArrowRight className='h-4 w-4' />
            </Link>
            <Link href='/itinerary-checker' className={styles.secondaryButton}>
              Explore the itinerary checker
            </Link>
          </div>

          <div className={styles.heroStats}>
            <HeroStat value='Lead intake -> option framing' label='One continuous workflow, not six disconnected tools.' />
            <HeroStat value='Internal + traveler-safe' label='Separate what the agency needs to know from what the traveler should see.' />
            <HeroStat value='Owner visibility included' label='Reviews, SLAs, and quality drift live inside the same operating surface.' />
          </div>
        </div>

        <div className={styles.previewFrame}>
          <div className={styles.previewGlow} />
          <div className={styles.previewTop}>
            <div>
              <Kicker>Waypoint workspace</Kicker>
              <h2 className='mt-3 text-[28px] font-semibold tracking-[-0.04em] text-[#f5fbff]'>Inbox, decisioning, owner oversight, and traveler-safe output in one system.</h2>
            </div>
            <span className={styles.previewBadge}>System live</span>
          </div>

          <div className={styles.previewGrid}>
            <div className={styles.previewColumn}>
              <div className={styles.moduleList}>
                <div className={styles.moduleItem}>
                  <div>
                    <strong>Inbox triage</strong>
                    <span>Europe family inquiry, June peak season, elderly + kids, budget tension detected.</span>
                  </div>
                  <span className='rounded-full bg-[#58a6ff]/10 px-3 py-1 text-[12px] text-[#9fd0ff]'>ASK_FOLLOWUP</span>
                </div>
                <div className={styles.moduleItem}>
                  <div>
                    <strong>Decision view</strong>
                    <span>Hard blockers surfaced before quote generation. Follow-up questions ready to send.</span>
                  </div>
                  <span className='rounded-full bg-[#d29922]/10 px-3 py-1 text-[12px] text-[#f2d48e]'>2 blockers</span>
                </div>
                <div className={styles.moduleItem}>
                  <div>
                    <strong>Owner review</strong>
                    <span>High-risk trips and exception paths show up with rationale, not just a badge.</span>
                  </div>
                  <span className='rounded-full bg-[#f85149]/10 px-3 py-1 text-[12px] text-[#ffc4c0]'>Needs sign-off</span>
                </div>
              </div>
            </div>

            <div className={styles.previewColumn}>
              <div className={styles.metricList}>
                <div className={styles.metricRow}>
                  <div>
                    <strong>Traveler-safe output</strong>
                    <span>Customer-facing message preview plus agent-only context.</span>
                  </div>
                  <CheckCircle2 className='mt-1 h-5 w-5 text-[#3fb950]' />
                </div>
                <div className={styles.metricRow}>
                  <div>
                    <strong>Booking readiness</strong>
                    <span>Docs, confirmations, transfers, and payment coordination tracked together.</span>
                  </div>
                  <Clock3 className='mt-1 h-5 w-5 text-[#39d0d8]' />
                </div>
                <div className={styles.metricRow}>
                  <div>
                    <strong>Operator memory</strong>
                    <span>Past traveler preferences, supplier trust, and commercial fit stay reusable.</span>
                  </div>
                  <Sparkles className='mt-1 h-5 w-5 text-[#58a6ff]' />
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className={styles.section} id='product'>
        <SectionIntro
          eyebrow='Product surfaces'
          title='Designed as a real agency workspace, not a consumer trip planner.'
          body='The homepage has to communicate the operating surface clearly: where work lands, how judgment is made, how output is controlled, and how owners stay in control as the team scales.'
        />

        <div className={styles.surfaceGrid}>
          {surfaces.map(({ icon: Icon, title, body, details }) => (
            <article key={title} className={styles.surfaceCard}>
              <div className={styles.surfaceCardHeader}>
                <Kicker>{title}</Kicker>
                <Icon className='h-5 w-5 text-[#58a6ff]' />
              </div>
              <h3 className='text-[22px] font-semibold tracking-[-0.04em]'>{title}</h3>
              <p className='mt-3 text-[15px] leading-7'>{body}</p>
              <div className={styles.surfaceMini}>
                {details.map((detail) => (
                  <div key={detail} className={styles.miniPanel}>
                    <strong>{detail}</strong>
                    <span>Visible without leaving the workflow.</span>
                  </div>
                ))}
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className={styles.section} id='workflow'>
        <SectionIntro
          eyebrow='Workflow compression'
          title='From messy inquiry to ready-to-send output without losing the commercial and operational logic.'
          body='This is the real operating story the page needs to sell: intake, blocker analysis, strategic option building, booking readiness, and owner visibility all belong to the same decision system.'
        />

        <div className={styles.storyGrid}>
          <article className={styles.storyCardLarge}>
            <div className={styles.storyHeader}>
              <Kicker>How the work moves</Kicker>
              <span className='rounded-full bg-[#39d0d8]/10 px-3 py-1 text-[12px] text-[#b9f4f6]'>Agency workflow</span>
            </div>

            <div className={styles.storySteps}>
              {[
                ['01', 'Capture the messy brief', 'WhatsApp, notes, PDFs, and half-specified asks get normalized into an operator-readable packet.'],
                ['02', 'Expose what blocks quoting', 'Decision state, hard blockers, and follow-up questions surface before anyone wastes time on impossible research.'],
                ['03', 'Build options with internal logic', 'Commercial fit, traveler fit, and operational ease stay visible as options are shaped.'],
                ['04', 'Ship traveler-safe output', 'The traveler sees a polished response while owners and agents keep the internal rationale and control plane.'],
              ].map(([index, title, body]) => (
                <div key={title} className={styles.storyStep}>
                  <div className={styles.stepIndex}>{index}</div>
                  <div>
                    <strong>{title}</strong>
                    <p>{body}</p>
                  </div>
                </div>
              ))}
            </div>

            <div className={styles.inlineMetrics}>
              <div className={styles.inlineMetric}>
                <strong>What we know / need to clarify / next steps</strong>
                <span>The core interface pattern throughout the product.</span>
              </div>
              <div className={styles.inlineMetric}>
                <strong>Ops and selling stay connected</strong>
                <span>No context loss between intake, quoting, and execution.</span>
              </div>
            </div>
          </article>

          <article className={styles.quoteCard}>
            <div className={styles.exampleHeader}>
              <Kicker>Operator view</Kicker>
              <Shield className='h-5 w-5 text-[#3fb950]' />
            </div>
            <h3 className='text-[24px] font-semibold tracking-[-0.04em]'>A homepage that shows the real product architecture.</h3>
            <p className='mt-3 text-[15px] leading-7'>Not just a floating hero. The public front door should make the internal system legible to owners, planners, and future hires.</p>
            <div className='mt-5 grid gap-3'>
              <ProofChip>Preferred supply before open market</ProofChip>
              <ProofChip>Traveler fit + operational fit + commercial fit</ProofChip>
              <ProofChip>Owner review and quality control in the same surface</ProofChip>
            </div>
            <div className='mt-6 rounded-[22px] border border-[rgba(48,54,61,0.82)] bg-[#161b22] p-4'>
              <p className='text-[12px] uppercase tracking-[0.18em] text-[#8b949e]'>Surface summary</p>
              <div className='mt-3 grid gap-3'>
                <div className='flex items-start justify-between gap-3 rounded-[16px] bg-[#0f1115] px-4 py-3'>
                  <div>
                    <strong className='text-[14px] text-[#eff6fb]'>Inbox {'->'} Workspace</strong>
                    <p className='mt-1 text-[13px] leading-6 text-[#8b949e]'>The handoff from demand capture to execution is explicit.</p>
                  </div>
                  <Briefcase className='mt-1 h-4 w-4 text-[#39d0d8]' />
                </div>
                <div className='flex items-start justify-between gap-3 rounded-[16px] bg-[#0f1115] px-4 py-3'>
                  <div>
                    <strong className='text-[14px] text-[#eff6fb]'>Decision {'->'} Strategy {'->'} Output</strong>
                    <p className='mt-1 text-[13px] leading-6 text-[#8b949e]'>The reasoning path is visible instead of buried behind one button.</p>
                  </div>
                  <Workflow className='mt-1 h-4 w-4 text-[#58a6ff]' />
                </div>
              </div>
            </div>
          </article>
        </div>
      </section>

      <section className={styles.section} id='personas'>
        <SectionIntro
          eyebrow='Persona fit'
          title='Different users. Same system. Different value density.'
          body='The homepage should reassure each buyer that the system understands their actual job-to-be-done, not just generic travel-software category copy.'
        />

        <div className={styles.personaGrid}>
          {personaCards.map((card) => (
            <article key={card.title} className={styles.personaCard}>
              <div className={styles.surfaceCardHeader}>
                <Kicker>{card.title}</Kicker>
                <span className='rounded-full bg-[#58a6ff]/10 px-3 py-1 text-[12px] text-[#9fd0ff]'>Role-specific</span>
              </div>
              <h3 className='text-[24px] font-semibold tracking-[-0.04em]'>{card.title}</h3>
              <p className='mt-3 text-[15px] leading-7'>{card.body}</p>
              <div className='mt-5'>
                <BulletList items={card.bullets} />
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className={styles.section}>
        <SectionIntro
          eyebrow='Operational trust'
          title='Built around how agencies actually work, not how travel software demos itself.'
          body='Commercial sourcing hierarchy, traveler-safe output boundaries, and risk reduction are part of the product story. They are not hidden implementation details.'
        />

        <div className={styles.proofGrid}>
          {proofCards.map((card) => (
            <article key={card.title} className={styles.proofCard}>
              <div className={styles.surfaceCardHeader}>
                <Kicker>{card.title}</Kicker>
                <CheckCircle2 className='h-5 w-5 text-[#3fb950]' />
              </div>
              <h3 className='text-[21px] font-semibold tracking-[-0.04em]'>{card.title}</h3>
              <p className='mt-3 text-[15px] leading-7'>{card.body}</p>
            </article>
          ))}
        </div>
      </section>

      <CtaBand
        title='See the operating system, then try the acquisition wedge.'
        body='Waypoint OS is the internal product. The itinerary checker is the public intelligence surface that creates demand, trust, and better-structured briefs.'
        primaryHref='/signup'
        primaryLabel='Create workspace'
        secondaryHref='/itinerary-checker'
        secondaryLabel='Open itinerary checker'
      />

      <PublicFooter />
    </PublicPage>
  );
}
