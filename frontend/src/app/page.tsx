import Link from 'next/link';
import {
  ArrowRight,
  Check,
  CheckCircle2,
  CircleAlert,
  Clock3,
  MessageSquareText,
  Sparkles,
} from 'lucide-react';
import {
  CtaBand,
  Kicker,
  ProofChip,
  PublicFooter,
  PublicHeader,
  PublicPage,
  SectionIntro,
} from '@/components/marketing/marketing';
import { AgencyHeroCockpit } from '@/components/marketing/MarketingVisuals';
import { GsapInitializer } from '@/components/marketing/GsapInitializer';
import styles from '@/components/marketing/marketing.module.css';

const painPoints = [
  {
    icon: MessageSquareText,
    title: 'FIT requests never arrive clean',
    body: 'WhatsApp notes, voice memos, screenshots, old preferences, and half-formed family constraints all land in different places.',
  },
  {
    icon: CircleAlert,
    title: 'Margin leaks hide until quoting',
    body: 'Visa gaps, pacing problems, DMC friction, and budget mismatches usually surface after advisors have already spent hours researching.',
  },
  {
    icon: Clock3,
    title: 'Quality control breaks at scale',
    body: 'A growing agency needs structured review points, not more status meetings. The system should flag itinerary risks before the client sees them.',
  },
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

const personaCards = [
  {
    title: 'Solo advisors',
    body: 'Move faster without turning every request into a blank-page research project.',
    accentColor: '#58a6ff',
  },
  {
    title: 'Agency owners',
    body: 'See which trips need review, which clients are waiting, and where quality is slipping.',
    accentColor: '#39d0d8',
  },
  {
    title: 'Junior agents',
    body: 'Get better questions, safer drafts, and clear next steps while learning agency judgment.',
    accentColor: '#d29922',
  },
];

const proofCards = [
  {
    title: 'Preferred suppliers first',
    body: 'Keep commercial logic visible before agents jump to open-market options.',
  },
  {
    title: 'Private notes stay private',
    body: 'Client-facing output is separated from internal risk, confidence, and review notes.',
  },
  {
    title: 'Review where it matters',
    body: 'Escalate the trips with real risk instead of forcing owners to inspect every message.',
  },
];

export default function HomePage() {
  return (
    <PublicPage>
      <GsapInitializer />
      <PublicHeader
        ctaHref='/signup'
        ctaLabel='Book a demo'
        navItems={[
          { href: '#product', label: 'Product' },
          { href: '#workflow', label: 'Solutions' },
          { href: '#personas', label: 'For Agencies' },
          { href: '#resources', label: 'Resources' },
          { href: '#pricing', label: 'Pricing' },
        ]}
      />

      <section className={`${styles.hero} ${styles.visualHero} ${styles.agencyHero} animate-fade-up`}>
        <div className={`${styles.heroCopy} animate-stagger-container`}>
          <div className={styles.eyebrow}>Built for boutique agencies</div>
          <h1 className={`${styles.heroTitle} font-display`}>Waypoint OS</h1>
          <h2 className={styles.heroSubtitle}>The operating system for boutique travel agencies.</h2>
          <p className={styles.heroBody}>
            From messy WhatsApp notes to client-safe proposals — Waypoint structures the intake, surfaces the risks, and protects your margins.
          </p>

          <div className={styles.heroActions}>
            <Link href='/signup' className={styles.primaryButton}>
              Book a demo
              <ArrowRight className='h-4 w-4' />
            </Link>
            <Link href='#product' className={styles.secondaryButton}>
              Explore the product
            </Link>
          </div>

          {/* Trust chips */}
          <div className='flex flex-wrap gap-x-5 gap-y-2 mt-6'>
            {[
              'Built for travel, not generic SaaS',
              'End-to-end agency workspace',
              'AI that learns your judgment',
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

      <section className={`${styles.section} ${styles.problemSection} animate-fade-up`} id='product'>
        <div className={`${styles.problemLead} animate-fade-up`}>
          <Kicker>Why agencies switch</Kicker>
          <h2 className="font-display">Your best clients do not start as clean forms.</h2>
          <p>
            They arrive as messy conversations. Waypoint turns that mess into the brief,
            questions, owner checks, and client-ready response your team needs to win the trip.
          </p>
        </div>

        <div className={`${styles.problemRail} animate-stagger-container`}>
          {painPoints.map(({ icon: Icon, title, body }) => (
            <article key={title} className={styles.problemItem}>
              <Icon className='h-5 w-5' />
              <div>
                <h3>{title}</h3>
                <p>{body}</p>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className={`${styles.section} ${styles.productStory} animate-fade-up`} id='workflow'>
        <div className="animate-fade-up">
          <SectionIntro
            eyebrow='How it works'
            title='One workspace from first message to safe reply.'
            body='Waypoint does not replace your agency judgment. It gives that judgment a place to live, repeat, and scale.'
          />
        </div>

        <div className={`${styles.productNarrative} animate-stagger-container`}>
          <article className={styles.narrativeFeature}>
            <div>
              <Kicker>Live agency work</Kicker>
              <h2 className="text-2xl font-semibold font-display">Waypoint reads the request like an experienced luxury advisor.</h2>
              <p>
                It pulls out travelers, dates, constraints, budget tension, missing documents,
                pacing risks, and the exact questions to ask before you begin building the itinerary.
              </p>
            </div>
            <div className={styles.operatorSnapshot}>
              <div>
                <span>Missing before quote</span>
                <strong>Passport validity, room split, transfer tolerance</strong>
              </div>
              <div>
                <span>Suggested next move</span>
                <strong>Ask 4 questions, then build two option bands</strong>
              </div>
              <div>
                <span>Owner check</span>
                <strong>High-value repeat client, review before send</strong>
              </div>
            </div>
          </article>

          <div className={styles.momentStack}>
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
        </div>
      </section>

      <section className={`${styles.section} ${styles.personaBand} animate-fade-up`} id='personas'>
        <div className={`${styles.personaBandHeader} animate-fade-up`}>
          <Kicker>Built for the agency floor</Kicker>
          <h2 className="font-display">The same system, different leverage for each role.</h2>
        </div>

        <div className={`${styles.personaStrip} animate-stagger-container`}>
          {personaCards.map((card) => (
            <article key={card.title} style={{ borderTop: `2px solid ${card.accentColor}` }}>
              <h3>{card.title}</h3>
              <p>{card.body}</p>
            </article>
          ))}
        </div>
      </section>

      <section className={`${styles.section} ${styles.trustSection} animate-fade-up`} id='resources'>
        <div className={`${styles.trustPanel} animate-fade-up`}>
          <div>
            <Kicker>Trust controls</Kicker>
            <h2 className="font-display">Built to protect margin, quality, and client trust.</h2>
            <p>
              The platform keeps commercial logic, DMC markups, and internal review states in the
              agency workspace, ensuring the client only sees the final, confident proposal.
            </p>
          </div>
          <div className={`${styles.trustList} animate-stagger-container`}>
            {proofCards.map((card) => (
              <article key={card.title}>
                <CheckCircle2 className='h-5 w-5' />
                <div>
                  <h3>{card.title}</h3>
                  <p>{card.body}</p>
                </div>
              </article>
            ))}
          </div>
        </div>

        <div className={styles.metricsRibbon}>
          <div>
            <strong>Fewer dead-end quotes</strong>
            <span>Questions before research.</span>
          </div>
          <div>
            <strong>Cleaner owner review</strong>
            <span>Escalation where judgment matters.</span>
          </div>
          <div>
            <strong>Safer client replies</strong>
            <span>Internal notes never leak.</span>
          </div>
        </div>
      </section>

      <section className={`${styles.section} ${styles.wedgeSection} animate-fade-up`}>
        <div className="animate-fade-up">
          <Kicker>Free public tool</Kicker>
          <h2 className="font-display">Test your plan before you book. Free, no account needed.</h2>
          <p>
            The itinerary checker gives travelers a structured first pass across their plan — timing
            risks, document gaps, pacing problems — then hands agencies cleaner context than any
            generic contact form.
          </p>
          <div className={styles.wedgeActions}>
            <Link href='/itinerary-checker' className={styles.primaryButton}>
              Try the free itinerary checker
              <ArrowRight className='h-4 w-4' />
            </Link>
            <ProofChip>
              <Sparkles className='h-4 w-4' />
              Upload-first, notebook-style interaction
            </ProofChip>
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
          title='Run the next high-value inquiry through Waypoint.'
          body='Book a demo and see how the operating system handles a real messy request from inbox to client-safe output.'
          primaryHref='/signup'
          primaryLabel='Book a demo'
          secondaryHref='/itinerary-checker'
          secondaryLabel='Try the itinerary checker'
        />
      </div>

      <PublicFooter />
    </PublicPage>
  );
}
