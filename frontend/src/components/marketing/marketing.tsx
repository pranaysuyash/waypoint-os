'use client';

import Link from 'next/link';
import type { ReactNode } from 'react';
import { useState } from 'react';
import { ArrowRight, Mail, ShieldCheck, Sparkles } from 'lucide-react';
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
  showWaitlist = true,
}: {
  title: string;
  body: string;
  primaryHref: string;
  primaryLabel: string;
  secondaryHref?: string;
  secondaryLabel?: string;
  showWaitlist?: boolean;
}) {
  const [email, setEmail] = useState('');
  const [submitted, setSubmitted] = useState(false);

  return (
    <div className={styles.ctaBand}>
      <div className='flex flex-col gap-4 md:flex-row md:items-start md:justify-between md:gap-10 flex-wrap'>
        {/* Left: copy + CTAs */}
        <div className='flex-1 min-w-[280px]'>
          <h3>{title}</h3>
          <p className='mt-2 max-w-[56ch] text-[15px] leading-7 text-[#9ba3b0]'>{body}</p>
          <div className='flex flex-wrap gap-3 mt-5'>
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

        {/* Right: waitlist */}
        {showWaitlist && (
          <div
            className='flex-none w-full md:w-[300px] rounded-[18px] p-[22px]'
            style={{
              background: 'rgba(255,255,255,0.03)',
              border: '1px solid rgba(255,255,255,0.08)',
            }}
          >
            {submitted ? (
              <div className='text-center py-4'>
                <div className='text-2xl mb-2 text-[#3fb950]'>✓</div>
                <div className='text-[14px] font-semibold text-[#e6edf3]'>You're on the list.</div>
                <div className='text-[12px] text-[#8b949e] mt-1'>We'll be in touch before launch.</div>
              </div>
            ) : (
              <>
                <div className='text-[13px] font-semibold text-[#e6edf3] mb-1'>Not ready for a demo?</div>
                <div className='text-[12px] text-[#8b949e] mb-3'>Join the waitlist — no pressure, no spam.</div>
                <div className='flex gap-2'>
                  <div
                    className='flex-1 flex items-center gap-2 px-3 py-2 rounded-[9px]'
                    style={{ background: '#111318', border: '1px solid #30363d' }}
                  >
                    <Mail className='h-3.5 w-3.5 text-[#484f58] shrink-0' />
                    <input
                      type='email'
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' && email.includes('@')) setSubmitted(true);
                      }}
                      placeholder='your@agency.com'
                      className='flex-1 bg-transparent border-none outline-none text-[#e6edf3] text-[12px] placeholder:text-[#484f58]'
                    />
                  </div>
                  <button
                    onClick={() => email.includes('@') && setSubmitted(true)}
                    className='px-4 py-2 rounded-full text-[12px] font-semibold text-[#071018] cursor-pointer'
                    style={{
                      background: 'linear-gradient(135deg, #7ab9ff 0%, #57e0ef 52%, #39d0d8 100%)',
                      boxShadow: '0 8px 24px rgba(57,208,216,0.3)',
                    }}
                  >
                    Join
                  </button>
                </div>
                <div className='flex items-center gap-1.5 mt-2.5'>
                  <ShieldCheck className='h-3.5 w-3.5 text-[#484f58]' />
                  <span className='text-[11px] text-[#484f58]'>No spam. Unsubscribe anytime.</span>
                </div>
              </>
            )}
          </div>
        )}
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
