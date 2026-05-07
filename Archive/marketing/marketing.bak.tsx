import Link from 'next/link';
import type { ReactNode } from 'react';
import { ArrowRight, ShieldCheck, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';
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
      <Link href='/' className={styles.brand}>
        <img className={styles.brandLogo} src='/brand/waypoint-logo-compass.svg' alt='' />
        <span>
          <strong className='block text-[14px] font-semibold tracking-tight'>Waypoint OS</strong>
          <span className='block text-[12px] text-[#8b949e]'>Travel agency operating system</span>
        </span>
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
          <ArrowRight className='h-4 w-4' />
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

export function CtaBand({
  title,
  body,
  primaryHref,
  primaryLabel,
  secondaryHref,
  secondaryLabel,
}: {
  title: string;
  body: string;
  primaryHref: string;
  primaryLabel: string;
  secondaryHref?: string;
  secondaryLabel?: string;
}) {
  return (
    <div className={styles.ctaBand}>
      <div>
        <h3>{title}</h3>
        <p className='mt-2 max-w-[56ch] text-[15px] leading-7 text-[#9ba3b0]'>{body}</p>
      </div>
      <div className='flex flex-wrap gap-3'>
        <Link href={primaryHref} className={styles.primaryButton}>
          {primaryLabel}
          <ArrowRight className='h-4 w-4' />
        </Link>
        {secondaryHref && secondaryLabel ? (
          <Link href={secondaryHref} className={styles.secondaryButton}>
            {secondaryLabel}
          </Link>
        ) : null}
      </div>
    </div>
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
      <ShieldCheck className='h-4 w-4 text-[#39d0d8]' />
      {children}
    </div>
  );
}

export function DemoButton({ href, label }: { href: string; label: string }) {
  return (
    <Button asChild size='lg' className='rounded-full px-5'>
      <Link href={href}>
        {label}
        <Sparkles className='h-4 w-4' />
      </Link>
    </Button>
  );
}
