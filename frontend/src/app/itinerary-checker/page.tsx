import Link from 'next/link';
import {
  AlertTriangle,
  ArrowRight,
  FileUp,
  Lock,
  ScanSearch,
  ShieldCheck,
  Sparkles,
  UploadCloud,
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
import { HeroScene, NotebookAnalyzer } from '@/components/marketing/MarketingVisuals';
import styles from '@/components/marketing/marketing.module.css';

const checks = [
  {
    title: 'Timing and transfer risk',
    body: 'Catch too-tight connections, fragile hotel transfers, and schedules that look fine until you try to execute them.',
  },
  {
    title: 'Visa and document gaps',
    body: 'Surface what is missing, unclear, or likely to become a late-stage problem before you pay. ',
  },
  {
    title: 'Pacing and experience friction',
    body: 'Find the days that are too packed, too far apart, or mismatched for the people actually taking the trip.',
  },
  {
    title: 'Hidden cost exposure',
    body: 'Flag the parts that are likely to become surprise spend, ambiguity, or rework after booking.',
  },
  {
    title: 'Extraction summary',
    body: 'Dates, destinations, hotels, flights, and inclusions are normalized so you can inspect what the tool thinks your plan says.',
  },
  {
    title: 'Structured brief for next conversation',
    body: 'Walk away with a clearer brief and better questions for your planner before anything gets finalized.',
  },
];

const faqs = [
  {
    title: 'Does this replace my travel agent?',
    body: 'No. The point is to help you ask better questions before you finalize. If your planner is good, this makes the conversation stronger.',
  },
  {
    title: 'What can I upload?',
    body: 'PDF itineraries, screenshots, forwarded text, or a pasted day-by-day plan. The analysis works on messy inputs.',
  },
  {
    title: 'What if the tool is not sure?',
    body: 'The consumer-facing surface is intentionally conservative. It shows the findings worth discussing, not speculative drama.',
  },
];

export default function ItineraryCheckerPage() {
  return (
    <PublicPage>
      <PublicHeader
        ctaHref='/itinerary-checker#upload'
        ctaLabel='Start free analysis'
        navItems={[
          { href: '#upload', label: 'Upload' },
          { href: '#notebook', label: 'Notebook mode' },
          { href: '#checks', label: 'What it checks' },
          { href: '#proof', label: 'Why trust it' },
          { href: '/', label: 'For agencies' },
        ]}
      />

      <section className={`${styles.hero} ${styles.visualHero}`}>
        <HeroScene mode='checker' />
        <div className={styles.heroCopy}>
          <div className={styles.eyebrow}>Itinerary stress test</div>
          <h1 className={styles.heroTitle}>Find what your travel plan missed.</h1>
          <p className={styles.heroBody}>
            Upload. Analyze. Travel confident. This is not a booking site and it is not an adversarial agent-replacement pitch.
            It is a calm, structured check for the things worth discussing before you finalize.
          </p>

          <div className={styles.heroActions}>
            <Link href='#upload' className={styles.primaryButton}>
              Start free analysis
              <ArrowRight className='h-4 w-4' />
            </Link>
            <Link href='/signup' className={styles.secondaryButton}>
              For agencies using Waypoint OS
            </Link>
            <a href='#notebook' className={styles.ghostButton}>
              Try notebook mode
            </a>
          </div>

          <div className='mt-7 flex flex-wrap gap-3'>
            <ProofChip>Things worth discussing before you finalize.</ProofChip>
            <ProofChip>Privacy-safe handling and conservative checks.</ProofChip>
            <ProofChip>Structured brief included.</ProofChip>
          </div>
        </div>

        <div className={`${styles.previewFrame} ${styles.heroDock}`} id='upload'>
          <div className={styles.previewGlow} />
          <div className={styles.previewGrid}>
            <article className={styles.uploadCard}>
              <div className={styles.exampleHeader}>
                <Kicker>Upload itinerary</Kicker>
                <UploadCloud className='h-5 w-5 text-[#58a6ff]' />
              </div>
              <h3 className='text-[26px] font-semibold tracking-[-0.04em]'>Upload. Analyze. Travel confident.</h3>
              <p className='mt-3 text-[15px] leading-7'>Drop in a PDF, a screenshot, or pasted plan text. The tool extracts the structure, checks the trip, and returns a short list of issues that matter.</p>
              <div className={styles.uploadTabs}>
                <div className={styles.uploadTab}>PDF itinerary</div>
                <div className={styles.uploadTab}>Screenshot</div>
                <div className={styles.uploadTab}>Pasted text</div>
              </div>
              <div className={styles.uploadZone}>
                <strong>Drop your itinerary here</strong>
                <span>Example: flights, hotels, daily plan, transfers, inclusions, and notes from your planner.</span>
                <div className='mt-5 flex flex-wrap gap-3'>
                  <Link href='#checks' className={styles.primaryButton}>
                    Analyze sample plan
                    <ScanSearch className='h-4 w-4' />
                  </Link>
                  <Link href='/login' className={styles.ghostButton}>
                    Planner sign in
                  </Link>
                </div>
              </div>
            </article>

            <article className={styles.exampleCard}>
              <div className={styles.exampleHeader}>
                <Kicker>Result snapshot</Kicker>
                <ShieldCheck className='h-5 w-5 text-[#39d0d8]' />
              </div>
              <div className={styles.scoreRow}>
                <div className={styles.scoreRing}>
                  <div className={styles.scoreRingInner}>7.6</div>
                </div>
                <div>
                  <h3 className='text-[22px] font-semibold tracking-[-0.04em]'>Plan health score</h3>
                  <p className='mt-2 text-[14px] leading-6 text-[#9ba3b0]'>Strong trip concept, but a few important issues should be discussed before payment or confirmation.</p>
                </div>
              </div>

              <div className={styles.issueStack}>
                <div className={styles.issueCard}>
                  <span className={`${styles.issueSeverity} ${styles.issueCritical}`}>Critical</span>
                  <h3 className='mt-3 text-[18px] font-semibold tracking-[-0.04em]'>Transfer timing looks fragile</h3>
                  <p className='mt-2 text-[14px] leading-6'>Airport arrival and hotel check-in buffer appears too tight for the actual transfer distance.</p>
                </div>
                <div className={styles.issueCard}>
                  <span className={`${styles.issueSeverity} ${styles.issueWarning}`}>Warning</span>
                  <h3 className='mt-3 text-[18px] font-semibold tracking-[-0.04em]'>Day 3 may be over-packed</h3>
                  <p className='mt-2 text-[14px] leading-6'>Three distant activities plus a late dinner leave very little real-world slack.</p>
                </div>
                <div className={styles.issueCard}>
                  <span className={`${styles.issueSeverity} ${styles.issueSafe}`}>Summary</span>
                  <h3 className='mt-3 text-[18px] font-semibold tracking-[-0.04em]'>Structured brief ready</h3>
                  <p className='mt-2 text-[14px] leading-6'>Dates, hotel zone, transfer chain, and likely discussion points are normalized for your next conversation.</p>
                </div>
              </div>
            </article>
          </div>
        </div>
      </section>

      <section className={styles.section}>
        <SectionIntro
          eyebrow='Interactive wedge'
          title='A quieter path: upload a trip and let the notebook work.'
          body='This parallel version keeps the page minimal until the user gives it a plan. Then the interface becomes the experience: reading, checking, writing, and handing back better questions.'
        />
        <NotebookAnalyzer />
      </section>

      <section className={styles.section} id='checks'>
        <SectionIntro
          eyebrow='What it checks'
          title='A careful first pass across the trip, not a black-box judgment dump.'
          body='The free surface is designed to be useful quickly and safe to trust. It focuses on the issues that deserve a conversation before you lock the plan.'
        />

        <div className={styles.checkGrid}>
          {checks.map((check) => (
            <article key={check.title} className={styles.checkCard}>
              <div className={styles.surfaceCardHeader}>
                <Kicker>{check.title}</Kicker>
                <AlertTriangle className='h-5 w-5 text-[#d29922]' />
              </div>
              <h3 className='text-[22px] font-semibold tracking-[-0.04em]'>{check.title}</h3>
              <p className='mt-3 text-[15px] leading-7'>{check.body}</p>
            </article>
          ))}
        </div>
      </section>

      <section className={styles.section} id='proof'>
        <SectionIntro
          eyebrow='How it helps'
          title='Better questions, clearer trade-offs, stronger conversations with your planner.'
          body='The wedge works when the analysis is easy to understand and the next action is obvious. The strongest CTA is still the free analysis itself.'
        />

        <div className={styles.storyGrid}>
          <article className={styles.storyCardLarge}>
            <div className={styles.storyHeader}>
              <Kicker>Three-step flow</Kicker>
              <Sparkles className='h-5 w-5 text-[#58a6ff]' />
            </div>
            <div className={styles.storySteps}>
              {[
                ['01', 'Upload the plan', 'PDF, screenshots, or raw text. The system extracts the travel structure even when the input is messy.'],
                ['02', 'Review the findings', 'Score, critical issues, warnings, and a structured trip summary appear in one glanceable report.'],
                ['03', 'Take the next conversation better prepared', 'Use the report to challenge unclear assumptions, fix fragile segments, or ask for a stronger plan.'],
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
          </article>

          <article className={styles.proofCard}>
            <div className={styles.surfaceCardHeader}>
              <Kicker>Trust and privacy</Kicker>
              <Lock className='h-5 w-5 text-[#39d0d8]' />
            </div>
            <h3 className='text-[24px] font-semibold tracking-[-0.04em]'>Built to be helpful before it is persuasive.</h3>
            <p className='mt-3 text-[15px] leading-7'>That means conservative public checks, clear explanation style, and a soft handoff to expert help only when the user wants it.</p>
            <div className='mt-5 grid gap-3'>
              <ProofChip>Conservative, consumer-safe findings</ProofChip>
              <ProofChip>Clear explanation over jargon</ProofChip>
              <ProofChip>Secondary CTA for deeper expert help</ProofChip>
            </div>
          </article>
        </div>
      </section>

      <section className={styles.section}>
        <SectionIntro
          eyebrow='FAQ'
          title='Designed to lower friction, not create a new one.'
          body='The GTM wedge only works if the page answers the obvious trust questions before the user has to ask them.'
        />

        <div className={styles.faqGrid}>
          {faqs.map((faq) => (
            <article key={faq.title} className={styles.faqCard}>
              <div className={styles.surfaceCardHeader}>
                <Kicker>{faq.title}</Kicker>
                <ShieldCheck className='h-5 w-5 text-[#3fb950]' />
              </div>
              <h3 className='text-[22px] font-semibold tracking-[-0.04em]'>{faq.title}</h3>
              <p className='mt-3 text-[15px] leading-7'>{faq.body}</p>
            </article>
          ))}
        </div>
      </section>

      <CtaBand
        title='Run the free check first. Ask better questions next.'
        body='Start with the itinerary analysis. If you later want expert help, the page can introduce it softly without undermining the original planner relationship.'
        primaryHref='/itinerary-checker#upload'
        primaryLabel='Start free analysis'
        secondaryHref='/signup'
        secondaryLabel='Agency workspace'
      />

      <PublicFooter />
    </PublicPage>
  );
}
