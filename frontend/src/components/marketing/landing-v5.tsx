'use client';

import Image from 'next/image';
import Link from 'next/link';
import {
  ArrowRight,
  CheckCircle2,
  CircleDollarSign,
  FileQuestion,
  MessageSquareText,
  ShieldCheck,
  Sparkles,
} from 'lucide-react';
import styles from './landing-v5.module.css';

const intakeRows = [
  { label: 'Incoming note', value: 'Italy honeymoon, Sept, flexible budget', icon: MessageSquareText },
  { label: 'Missing before quote', value: 'arrival city, passport validity, room type', icon: FileQuestion },
  { label: 'What it changes', value: 'quote speed, accuracy, and owner review time', icon: CircleDollarSign },
];

const operatorProof = [
  { value: '2m 14s', label: 'From inquiry to usable brief' },
  { value: '3', label: 'Questions before quote' },
  { value: '18%', label: 'Owner reviews routed' },
];

const workflowNotes = [
  'Extract dates, party size, budget, pace, and trip type from messy messages.',
  'Surface the missing facts that change itinerary quality before anyone quotes.',
  'Protect owner time by showing what needs a human decision and what does not.',
];

export function V5LandingPage() {
  return (
    <main className={styles.page}>
      <a href='#content' className='sr-only-focusable'>Skip to content</a>

      <header className={styles.header}>
        <Link href='/' className={styles.brand} aria-label='Waypoint OS home'>
          Waypoint OS
        </Link>
        <nav className={styles.nav} aria-label='Primary'>
          <a href='#product'>Product</a>
          <a href='#workflow'>Workflow</a>
          <a href='#for-agencies'>For agencies</a>
          <Link href='/pricing'>Pricing</Link>
          <Link href='/login'>Sign in</Link>
          <Link href='/signup' className={styles.navCta}>Create workspace</Link>
        </nav>
      </header>

      <section className={styles.hero} id='content'>
        <Image
          src='/landing/experiments/waypoint-ops-hero-v5.png'
          alt='Waypoint OS workspace preview showing a boutique travel operations desk and planning artifacts.'
          fill
          priority
          sizes='100vw'
        />
        <WorkflowRibbon />
        <div className={styles.heroCopy}>
          <span className={styles.kicker}>Boutique travel operations, without the theater</span>
          <h1>Turn raw trip notes into quote-ready briefs.</h1>
          <p>
            Waypoint helps boutique travel agencies turn the notes they already have, whether from calls,
            emails, WhatsApp messages, or copied itineraries, into one clean brief, spot what is missing,
            and draft safer proposals faster.
          </p>
          <div className={styles.actions}>
            <Link href='/signup' className={styles.primaryButton}>
              <span>Create workspace</span>
              <span className={styles.buttonIcon}>
                <ArrowRight className='size-4' />
              </span>
            </Link>
            <Link href='#workflow' className={styles.secondaryButton}>
              See how it helps
            </Link>
            <Link href='/pricing' className={styles.secondaryButton}>
              See pricing
            </Link>
          </div>
          <div className={styles.heroProof}>
            <span>Less manual copying</span>
            <span>Fewer quote mistakes</span>
            <span>Faster owner review</span>
          </div>
        </div>
      </section>

      <section className={styles.signalSection} id='product'>
        <div className={styles.sectionLead}>
          <span className={styles.kicker}>The operating system for boutique travel agencies</span>
          <h2>Not a prettier CRM. A faster intake and quoting surface.</h2>
          <p>
            It gives agency owners and advisors one place to turn rough trip requests into something they can actually quote:
            cleaner briefs, clearer gaps, and less rework. No channel assumptions required.
          </p>
        </div>

        <div className={styles.workbench}>
          <article className={styles.inboxPanel}>
            <div className={styles.panelHeader}>
              <span>New inquiry</span>
              <strong>Honeymoon in Italy</strong>
            </div>
            {intakeRows.map((row) => {
              const Icon = row.icon;
              return (
                <div key={row.label} className={styles.intakeRow}>
                  <Icon className='size-5' />
                  <div>
                    <span>{row.label}</span>
                    <strong>{row.value}</strong>
                  </div>
                </div>
              );
            })}
          </article>

          <article className={styles.decisionPanel}>
            <span className={styles.panelLabel}>What it helps with</span>
            <h3>Ask the right questions before quote build.</h3>
            <ol className={styles.questionList}>
              <li>Confirm the trip window and arrival city.</li>
              <li>Check passport, visa, and timing risks early.</li>
              <li>Choose between options that fit pace and budget.</li>
            </ol>
            <div className={styles.safeReply}>
              <ShieldCheck className='size-5' />
              <span>Internal risk stays private. Client reply is ready to draft.</span>
            </div>
          </article>
        </div>
      </section>

      <section className={styles.workflowSection} id='workflow'>
        <div className={styles.sectionLead}>
          <span className={styles.kicker}>What changes for the agency</span>
          <h2>Less copy-paste. More quoting.</h2>
        </div>

        <div className={styles.workflowGrid}>
          <div className={styles.proofRail}>
            {operatorProof.map((item) => (
              <article key={item.label} className={styles.metricCard}>
                <strong>{item.value}</strong>
                <span>{item.label}</span>
              </article>
            ))}
          </div>

          <div className={styles.workflowCard}>
            <div className={styles.workflowHeader}>
              <Sparkles className='size-5' />
              <span>Operator flow</span>
            </div>
            <ul className={styles.workflowList}>
              {workflowNotes.map((note) => (
                <li key={note}>
                  <CheckCircle2 className='size-4' />
                  <span>{note}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </section>

      <section className={styles.checkerSection} id='for-agencies'>
        <div className={styles.sectionLead}>
          <span className={styles.kicker}>Why agencies use it</span>
          <h2>It helps teams answer faster, quote cleaner, and keep owners out of every tiny decision.</h2>
          <p>
            The value is not “AI” for its own sake. It is fewer messy handoffs, less duplicate work, and fewer expensive mistakes
            when a quote goes out with missing or wrong details.
          </p>
        </div>
        <div className={styles.summaryCard}>
          <span className={styles.summaryLabel}>Agency outcome</span>
          <h3>Cleaner briefs in. Better proposals out.</h3>
          <p>
            Waypoint is for the exact moment a travel request stops being a conversation and starts becoming work.
            It helps the agency decide what to ask next, what to quote, and what to hold back until the details are right.
          </p>
          <div className={styles.summaryNote}>
            The product is doing the translation from raw request to workable brief.
          </div>
        </div>
      </section>

      <section className={styles.ctaSection}>
        <div className={styles.ctaCard}>
          <div>
            <span className={styles.kicker}>Waypoint OS</span>
            <h2>See how it turns messy requests into clean quotes.</h2>
            <p>
              If you want, I can show the exact flow: intake, missing details, suggested questions, and the draftable brief.
            </p>
          </div>
          <div className={styles.actions}>
            <Link href='/signup' className={styles.primaryButton}>
              <span>Create workspace</span>
              <span className={styles.buttonIcon}>
                <ArrowRight className='size-4' />
              </span>
            </Link>
            <Link href='#product' className={styles.secondaryButton}>
              Explore the flow
            </Link>
          </div>
        </div>
      </section>

      <footer className={styles.footer}>
        <span>Waypoint OS. Quote-ready travel requests for boutique agencies.</span>
        <div className={styles.footerLinks}>
          <Link href='/pricing'>Pricing</Link>
          <Link href='/login'>Sign in</Link>
          <Link href='/signup'>Create workspace</Link>
        </div>
      </footer>
    </main>
  );
}

function WorkflowRibbon() {
  return (
    <div className={styles.workflowRibbon} aria-hidden='true'>
      <div className={styles.workflowRibbonCard}>
        <svg className={styles.workflowRibbonSvg} viewBox='0 0 960 720' role='presentation' focusable='false'>
          <defs>
            <linearGradient id='workflow-route' x1='0%' y1='0%' x2='100%' y2='100%'>
              <stop offset='0%' stopColor='#57e0ef' stopOpacity='0.24' />
              <stop offset='52%' stopColor='#39d0d8' stopOpacity='0.72' />
              <stop offset='100%' stopColor='#7ab9ff' stopOpacity='0.9' />
            </linearGradient>
            <linearGradient id='workflow-panel' x1='0%' y1='0%' x2='100%' y2='100%'>
              <stop offset='0%' stopColor='#0d151d' stopOpacity='0.98' />
              <stop offset='100%' stopColor='#101821' stopOpacity='0.92' />
            </linearGradient>
            <filter id='workflow-shadow' x='-20%' y='-20%' width='140%' height='140%'>
              <feDropShadow dx='0' dy='18' stdDeviation='18' floodColor='#06090d' floodOpacity='0.42' />
            </filter>
          </defs>

          <path
            d='M174 540C220 478 290 448 346 454C414 461 445 526 514 520C600 513 620 398 699 366C767 339 807 367 849 330'
            className={styles.workflowRibbonRouteSoft}
          />
          <path
            d='M174 540C220 478 290 448 346 454C414 461 445 526 514 520C600 513 620 398 699 366C767 339 807 367 849 330'
            className={styles.workflowRibbonRoute}
          />
          <path
            d='M174 540C220 478 290 448 346 454C414 461 445 526 514 520C600 513 620 398 699 366C767 339 807 367 849 330'
            className={styles.workflowRibbonRouteDash}
          />

          <g className={styles.workflowRibbonPanelLeft} filter='url(#workflow-shadow)'>
            <rect x='96' y='132' width='252' height='140' rx='28' fill='url(#workflow-panel)' stroke='rgba(88, 166, 255, 0.14)' />
            <rect x='98' y='134' width='248' height='136' rx='26' fill='none' stroke='rgba(57, 208, 216, 0.1)' strokeDasharray='6 10' />
            <text x='126' y='176' className={styles.workflowRibbonLabel}>Incoming note</text>
            <text x='126' y='212' className={styles.workflowRibbonTitle}>Italy honeymoon</text>
            <text x='126' y='245' className={styles.workflowRibbonCopy}>Arrival city, pacing, and room type still missing</text>
          </g>

          <g className={styles.workflowRibbonPanelRight} filter='url(#workflow-shadow)'>
            <rect x='560' y='170' width='282' height='138' rx='28' fill='url(#workflow-panel)' stroke='rgba(88, 166, 255, 0.14)' />
            <text x='668' y='206' className={styles.workflowRibbonLabel}>What changes</text>
            <text x='668' y='242' className={styles.workflowRibbonTitle}>Quote-ready brief</text>
            <text x='668' y='274' className={styles.workflowRibbonCopy}>Fewer gaps before owner review</text>
          </g>

          <g className={styles.workflowRibbonPanelBottom} filter='url(#workflow-shadow)'>
            <rect x='338' y='488' width='260' height='154' rx='30' fill='url(#workflow-panel)' stroke='rgba(88, 166, 255, 0.14)' />
            <text x='366' y='532' className={styles.workflowRibbonLabel}>Review surface</text>
            <text x='366' y='568' className={styles.workflowRibbonTitle}>Suggested questions</text>
            <text x='366' y='601' className={styles.workflowRibbonCopy}>Trip window, visa risk, and budget guardrails</text>
          </g>

          <g className={styles.workflowRibbonDots}>
            <circle cx='174' cy='540' r='9' />
            <circle cx='346' cy='454' r='9' />
            <circle cx='514' cy='520' r='9' />
            <circle cx='699' cy='366' r='9' />
            <circle cx='849' cy='330' r='9' />
          </g>

          <circle className={styles.workflowRibbonPulse} r='12'>
            <animateMotion dur='6.5s' repeatCount='indefinite' rotate='auto'>
              <mpath href='#workflow-route' />
            </animateMotion>
          </circle>

          <circle className={styles.workflowRibbonPulseAlt} r='7'>
            <animateMotion dur='6.5s' begin='1.1s' repeatCount='indefinite' rotate='auto'>
              <mpath href='#workflow-route' />
            </animateMotion>
          </circle>
        </svg>
      </div>
    </div>
  );
}
