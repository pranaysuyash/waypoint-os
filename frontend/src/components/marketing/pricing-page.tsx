import Link from 'next/link';
import { ArrowRight, CheckCircle2, ShieldCheck, Sparkles } from 'lucide-react';
import { PublicFooter, PublicHeader, PublicPage } from '@/components/marketing/marketing';
import styles from './pricing-page.module.css';

const tiers = [
  {
    name: 'Traveler checker',
    price: 'Free',
    summary: 'A separate public tool for pre-qualifying a trip before it reaches the agency.',
    featured: false,
    bullets: ['No sign-up required', 'Upload, paste, or screenshot a trip plan', 'Produces a cleaner brief for the agency'],
    cta: 'Try the public checker',
    href: '/itinerary-checker',
  },
  {
    name: 'Workspace access',
    price: 'Start self-serve',
    summary: 'The B2B workspace for turning messy trip requests into quote-ready briefs.',
    featured: true,
    bullets: [
      'Manual capture from calls, emails, WhatsApp copies, and pasted itineraries',
      'Agency workbench for intake, review, and quote preparation',
      'Internal notes stay separate from anything a traveler sees',
    ],
    cta: 'Create workspace',
    href: '/signup',
  },
  {
    name: 'Guided rollout',
    price: 'Add support when needed',
    summary: 'For teams that want setup help or a cleaner adoption path for multiple advisors.',
    featured: false,
    bullets: ['Onboarding support for team setup', 'Workflow habits for shared use', 'Only if it reduces real adoption friction'],
    cta: 'Start with workspace access',
    href: '/signup',
  },
];

const included = [
  'Manual capture from calls, emails, WhatsApp copies, and pasted itineraries',
  'Trip brief assembly before quote work begins',
  'Internal notes and review are kept separate from traveler-facing surfaces',
  'Public checker remains a separate path',
];

const notIncluded = [
  'No fake demo gate',
  'No hidden pricing funnel',
  'No assumption that every buyer needs rollout help',
  'No mixing public checker traffic into the B2B workspace',
];

const faq = [
  {
    q: 'Is this a real pricing page if exact numbers are not public yet?',
    a: 'Yes. It still tells buyers what they can start with, what is free, and when support is optional. We are not inventing checkout numbers before they exist.',
  },
  {
    q: 'Do buyers need to book a demo first?',
    a: 'No. Self-serve workspace access is the default path. A conversation is only useful when the rollout itself needs human help.',
  },
  {
    q: 'Why keep the traveler checker separate?',
    a: 'Because it is a different job. It helps a traveler show up with a cleaner brief, while the workspace helps the agency do the quoting work.',
  },
];

export const metadata = {
  title: 'Waypoint OS — Pricing & Access',
  description:
    'See how to start with Waypoint: create a workspace, add guided rollout if needed, or use the free traveler checker separately.',
};

export default function PricingPage() {
  return (
    <PublicPage>
      <PublicHeader
        ctaHref='/signup'
        ctaLabel='Create workspace'
        navItems={[
          { href: '/', label: 'Home' },
          { href: '/#product', label: 'Product' },
          { href: '/#workflow', label: 'Workflow' },
          { href: '/pricing', label: 'Pricing' },
          { href: '/itinerary-checker', label: 'Itinerary Checker' },
        ]}
      />

      <main className={styles.page}>
        <section className={styles.hero}>
          <div className={styles.heroCopy}>
            <span className={styles.kicker}>Pricing & access</span>
            <h1>Pricing that matches how the agency actually starts using Waypoint.</h1>
            <p>
              Waypoint is built around the real workflow: capture the messy trip request, shape it into a usable brief,
              and decide whether the agency needs software access, rollout support, or nothing else.
            </p>
            <div className={styles.heroActions}>
              <Link href='/signup' className={styles.primaryButton}>
                Create workspace
                <ArrowRight className='size-4' />
              </Link>
              <Link href='/itinerary-checker' className={styles.secondaryButton}>
                Try the public checker
              </Link>
            </div>
            <div className={styles.heroProof}>
              <span>Self-serve workspace</span>
              <span>Free checker</span>
              <span>Optional rollout support</span>
            </div>
          </div>

          <aside className={styles.liveCard} aria-label='Access note'>
            <div className={styles.liveCardHeader}>
              <span className={styles.liveBadge}>What’s live right now</span>
              <Sparkles className='size-5' />
            </div>
            <p>
              The app already supports manual capture, internal notes, and trip planning. That means self-serve signup
              is a real workspace path, not a placeholder contact form.
            </p>
            <ul className={styles.liveList}>
              {included.slice(0, 3).map((item) => (
                <li key={item}>
                  <CheckCircle2 className='size-4' />
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </aside>
        </section>

        <section className={styles.section}>
          <div className={styles.sectionLead}>
            <div>
              <span className={styles.kicker}>Three ways to start</span>
              <h2>Choose the tier that fits the job you want done.</h2>
            </div>
            <p>
              This is a pricing page, but it does not pretend every path needs a sales call. The free checker, self-serve
              workspace, and guided rollout path each solve a different problem.
            </p>
          </div>

          <div className={styles.tierGrid}>
            {tiers.map((tier) => (
              <article
                key={tier.name}
                className={`${styles.tierCard} ${tier.featured ? styles.featuredTier : ''}`}
              >
                <div className={styles.tierTop}>
                  <div>
                    <span className={styles.tierLabel}>{tier.name}</span>
                    <h3>{tier.price}</h3>
                  </div>
                  {tier.featured ? <span className={styles.tierBadge}>Recommended</span> : null}
                </div>
                <p>{tier.summary}</p>
                <ul className={styles.tierList}>
                  {tier.bullets.map((bullet) => (
                    <li key={bullet}>
                      <CheckCircle2 className='size-4' />
                      <span>{bullet}</span>
                    </li>
                  ))}
                </ul>
                <div className={styles.tierFooter}>
                  <Link href={tier.href} className={tier.featured ? styles.primaryButton : styles.secondaryButton}>
                    {tier.cta}
                    <ArrowRight className='size-4' />
                  </Link>
                </div>
              </article>
            ))}
          </div>
        </section>

        <section className={styles.section}>
          <div className={styles.sectionLead}>
            <div>
              <span className={styles.kicker}>What’s included</span>
              <h2>Every paid path points back to the same operating surface.</h2>
            </div>
            <p>
              The page should answer the pricing question quickly: what the workspace does, what support adds, and what
              stays separate.
            </p>
          </div>

          <div className={styles.matrix}>
            <article className={styles.matrixCard}>
              <span className={styles.matrixTitle}>Included by default</span>
              <ul>
                {included.map((item) => (
                  <li key={item}>
                    <CheckCircle2 className='size-4' />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </article>
            <article className={styles.matrixCard}>
              <span className={styles.matrixTitle}>Not the point of the page</span>
              <ul>
                {notIncluded.map((item) => (
                  <li key={item}>
                    <ShieldCheck className='size-4' />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </article>
          </div>
        </section>

        <section className={styles.section}>
          <div className={styles.sectionLead}>
            <div>
              <span className={styles.kicker}>FAQ</span>
              <h2>Questions a buyer would actually ask on this page.</h2>
            </div>
            <p>
              These are the things that usually get buried in vague pricing pages. Here they are stated plainly so the
              page does its job.
            </p>
          </div>

          <div className={styles.faqGrid}>
            {faq.map((item) => (
              <article key={item.q} className={styles.faqCard}>
                <h3>{item.q}</h3>
                <p>{item.a}</p>
              </article>
            ))}
          </div>
        </section>

        <section className={styles.ctaSection}>
          <div className={styles.ctaCard}>
            <div>
              <span className={styles.kicker}>Next step</span>
              <h2>Start with the path that fits your team now.</h2>
              <p>
                If you are evaluating fit, the cleanest path is to create a workspace and use the product directly. The
                public checker stays available separately for travelers and pre-qualification.
              </p>
            </div>
            <div className={styles.heroActions}>
              <Link href='/signup' className={styles.primaryButton}>
                Create workspace
                <ArrowRight className='size-4' />
              </Link>
              <Link href='/' className={styles.secondaryButton}>
                Back to homepage
              </Link>
            </div>
          </div>
        </section>
      </main>

      <PublicFooter />
    </PublicPage>
  );
}
