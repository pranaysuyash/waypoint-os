import Image from 'next/image';
import Link from 'next/link';
import { ArrowRight, ShieldCheck } from 'lucide-react';
import type { ReactNode } from 'react';
import styles from './marketing.module.css';

export function PublicPage({ children }: { children: ReactNode }) {
  return (
    <div className={styles.page}>
      <div className={styles.shell}>{children}</div>
    </div>
  );
}

export function PublicHeader({
  ctaHref,
  ctaLabel,
  navItems = [
    { href: '#product', label: 'Product' },
    { href: '#workflow', label: 'Workflow' },
    { href: '#personas', label: 'Personas' },
    { href: '/itinerary-checker', label: 'Itinerary Checker' },
  ],
}: {
  ctaHref: string;
  ctaLabel: string;
  navItems?: Array<{ href: string; label: string }>;
}) {
  return (
    <header className={styles.header}>
      <Link href='/' className={styles.brand} aria-label='Waypoint OS home'>
        <Image
          className={styles.brandLogo}
          src='/brand/waypoint-logo-primary.svg'
          alt='Waypoint OS'
          width={240}
          height={72}
          priority
        />
      </Link>

      <nav className={styles.nav}>
        {navItems.map((item) =>
          item.href.startsWith('#') ? (
            <a key={item.href} href={item.href}>
              {item.label}
            </a>
          ) : (
            <Link key={item.href} href={item.href}>
              {item.label}
            </Link>
          ),
        )}
      </nav>

      <div className={styles.actions}>
        <Link href='/login' className={styles.ghostButton}>
          Sign in
        </Link>
        <Link href={ctaHref} className={styles.primaryButton}>
          {ctaLabel}
          <ArrowRight className='size-4' />
        </Link>
      </div>
    </header>
  );
}

export function SectionIntro({
  eyebrow,
  title,
  body,
}: {
  eyebrow: string;
  title: string;
  body: string;
}) {
  return (
    <div className={styles.sectionHeader}>
      <div>
        <div className={styles.eyebrow}>{eyebrow}</div>
        <h2 className={styles.sectionTitle}>{title}</h2>
      </div>
      <p className={styles.sectionCopy}>{body}</p>
    </div>
  );
}

export function Kicker({ children }: { children: ReactNode }) {
  return (
    <span className={styles.kicker}>
      <span className={styles.kickerDot} />
      {children}
    </span>
  );
}

export function PublicFooter() {
  return (
    <footer className={styles.footer}>
      <span>Waypoint OS. Workflow compression for boutique travel operations.</span>
      <div className={styles.footerLinks}>
        <Link href='/'>For agencies</Link>
        <Link href='/itinerary-checker'>Itinerary Checker</Link>
        <Link href='/login'>Sign in</Link>
        <Link href='/signup'>Book a demo</Link>
      </div>
    </footer>
  );
}

export function ProofChip({ children }: { children: ReactNode }) {
  return (
    <div className='inline-flex items-center gap-2 rounded-full border border-[rgba(88,166,255,0.18)] bg-[rgba(12,22,31,0.78)] px-4 py-2 text-[13px] text-[#dce9f4]'>
      <ShieldCheck className='size-4 text-[#39d0d8]' />
      {children}
    </div>
  );
}
