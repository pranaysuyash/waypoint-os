import Link from 'next/link';
import {
  ArrowRight,
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
import { DataTransformationHero } from '@/components/marketing/MarketingVisuals';
import styles from '@/components/marketing/marketing-v2.module.css';

const painPoints = [
  {
    icon: MessageSquareText,
    title: 'The inbox never arrives clean',
    body: 'WhatsApp notes, voice memos, screenshots, old preferences, and half-formed family constraints all land in different places.',
  },
  {
    icon: CircleAlert,
    title: 'Risk hides until it is expensive',
    body: 'Visa gaps, pacing problems, supplier friction, and budget mismatch usually surface after someone has already spent hours quoting.',
  },
  {
    icon: Clock3,
    title: 'Owners cannot see quality drift',
    body: 'A growing team needs review points, not more status meetings. The system should show what needs attention before the client does.',
  },
];

const productMoments = [
  {
    label: '01',
    title: 'Capture the messy request',
    body: 'Turn scattered traveler context into one usable brief: who is going, what matters, what is missing, and what cannot be assumed.',
  },
  {
    label: '02',
    title: 'Ask before quoting',
    body: 'Waypoint shows the few questions that actually change the trip, instead of sending agents into research with bad inputs.',
  },
  {
    label: '03',
    title: 'Send safer client output',
    body: 'Internal rationale stays inside the agency. The traveler gets a polished reply, clear choices, and no operational uncertainty.',
  },
];

const personaCards = [
  {
    title: 'Solo Advisors',
    body: 'Respond to leads in minutes instead of hours. Let the system handle the context so you can focus on the sale.',
  },
  {
    title: 'Agency Owners',
    body: 'Get total visibility into your team\'s judgment. Sign off on high-value trips and catch quality drift before it hits the client.',
  },
  {
    title: 'Operations & Juniors',
    body: 'Turn training into execution. Surface the right questions automatically, reducing operational rework on complex itineraries.',
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

      <section className={`${styles.hero} ${styles.visualHero} ${styles.agencyHero}`}>
        <div className={styles.heroCopy}>
          <div className={styles.eyebrow}>Built for boutique agencies</div>
          <h1 className={styles.heroTitle}>Stop guessing what your clients want.</h1>
          <p className={styles.heroBody}>
            Turn messy WhatsApp messages, emails, and PDFs into structured, bookable trips in seconds. The operating system for modern boutique travel agencies.
          </p>

          <div className={styles.heroActions}>
            <Link href='/signup' className={styles.primaryButton}>
              Get Started
              <ArrowRight className='h-4 w-4' />
            </Link>
            <Link href='/itinerary-checker' className={styles.secondaryButton}>
              Try the Itinerary Checker
            </Link>
          </div>
        </div>

        <DataTransformationHero />
      </section>

      <section className={`${styles.section} ${styles.problemSection}`} id='product'>
        <div className={styles.problemLead}>
          <Kicker>Why agencies switch</Kicker>
          <h2>Your best clients do not start as clean forms.</h2>
          <p>
            They arrive as messy conversations. Waypoint turns that mess into the brief,
            questions, owner checks, and client-ready response your team needs to win the trip.
          </p>
        </div>

        <div className={styles.problemRail}>
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

      <section className={`${styles.section} ${styles.productStory}`} id='workflow'>
        <SectionIntro
          eyebrow='Workflow Compression'
          title='From messy inquiry to structured brief in one surface.'
          body='Waypoint gives your team a place to capture intent, surface operational risks, and build options without losing context.'
        />

        <div className={styles.productNarrative}>
          <article className={styles.narrativeFeature}>
            <div>
              <Kicker>Live agency work</Kicker>
              <h3>Waypoint reads the request like an experienced operator.</h3>
              <p>
                It pulls out travelers, dates, constraints, budget tension, missing documents,
                pacing risk, and the exact questions that should be answered before quoting.
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

      <section className={`${styles.section} ${styles.personaBand}`} id='personas'>
        <div className={styles.personaBandHeader}>
          <Kicker>Team Visibility</Kicker>
          <h2>Scale your judgment without increasing meetings.</h2>
          <p className='mt-4 max-w-[56ch] text-[16px] leading-relaxed text-[#9ba3b0]'>
            Waypoint OS gives owners, managers, and agents the same high-resolution view 
            of a trip, allowing for surgical feedback instead of scattered corrections.
          </p>
        </div>

        <div className={styles.personaStrip}>
          {personaCards.map((card) => (
            <article key={card.title}>
              <h3>{card.title}</h3>
              <p>{card.body}</p>
            </article>
          ))}
        </div>
      </section>

      <section className={`${styles.section} ${styles.trustSection}`} id='resources'>
        <div className={styles.trustPanel}>
          <div>
            <Kicker>Trust controls</Kicker>
            <h2>Built for margin, quality, and client safety.</h2>
            <p>
              The product keeps commercial logic, private judgment, and review states in the
              agency workspace, so the client only sees the confident version.
            </p>
          </div>
          <div className={styles.trustList}>
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

      <section className={`${styles.section} ${styles.wedgeSection}`}>
        <div>
          <Kicker>Itinerary checker</Kicker>
          <h2>Turn itinerary anxiety into better-qualified leads.</h2>
          <p>
            The itinerary checker gives travelers a useful public tool, then hands agencies
            cleaner context than a generic contact form ever could.
          </p>
          <div className={styles.wedgeActions}>
            <Link href='/itinerary-checker' className={styles.secondaryButton}>
              Open itinerary checker
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
