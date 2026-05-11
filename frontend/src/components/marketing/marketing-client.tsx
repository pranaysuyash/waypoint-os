'use client';

import Link from 'next/link';
import { useState, type ReactNode } from 'react';
import { ArrowRight, Mail, ShieldCheck } from 'lucide-react';
import styles from './marketing.module.css';

export interface CtaBandProps {
  title: string;
  body: string;
  primaryHref: string;
  primaryLabel: string;
  secondaryHref?: string;
  secondaryLabel?: string;
  showWaitlist?: boolean;
}

export function CtaBand({
  title,
  body,
  primaryHref,
  primaryLabel,
  secondaryHref,
  secondaryLabel,
  showWaitlist = true,
}: CtaBandProps) {
  const [email, setEmail] = useState('');
  const [submitted, setSubmitted] = useState(false);

  return (
    <div className={styles.ctaBand}>
      <div className='flex flex-col gap-4 md:flex-row md:items-start md:justify-between md:gap-10 flex-wrap'>
        <div className='flex-1 min-w-[280px]'>
          <h3>{title}</h3>
          <p className='mt-2 max-w-[56ch] text-[15px] leading-7 text-[#9ba3b0]'>{body}</p>
          <div className='flex flex-wrap gap-3 mt-5'>
            <Link href={primaryHref} className={styles.primaryButton}>
              {primaryLabel}
              <ArrowRight className='size-4' />
            </Link>
            {secondaryHref && secondaryLabel ? (
              <Link href={secondaryHref} className={styles.secondaryButton}>
                {secondaryLabel}
              </Link>
            ) : null}
          </div>
        </div>

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
                <div className='text-[14px] font-semibold text-[#e6edf3]'>You&apos;re on the list.</div>
                <div className='text-[12px] text-[#9ba3b0] mt-1'>We&apos;ll be in touch before launch.</div>
              </div>
            ) : (
              <>
                <div className='text-[13px] font-semibold text-[#e6edf3] mb-1'>Not ready for a demo?</div>
                 <div className='text-[12px] text-[#9ba3b0] mb-3'>Join the waitlist - no pressure, no spam.</div>
                <div className='flex gap-2'>
                  <div
                    className='flex-1 flex items-center gap-2 px-3 py-2 rounded-[9px]'
                    style={{ background: '#111318', border: '1px solid #30363d' }}
                  >
                    <Mail className='size-3.5 text-[#484f58] shrink-0' />
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
                  <ShieldCheck className='size-3.5 text-[#484f58]' />
                   <span className='text-[var(--ui-text-xs)] text-[#8b949e]'>No spam. Unsubscribe anytime.</span>
                </div>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

