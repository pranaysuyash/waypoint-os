'use client';

/**
 * WelcomeModal - shown to the user on their first login.
 *
 * Persists dismissal in localStorage so it only shows once.
 * Displays a brief overview of the app's key workflows with
 * actionable links to the most important pages.
 */

import { useState, useEffect, useCallback } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { Compass, Inbox, MessageSquare, Settings, Sparkles, X } from 'lucide-react';

const WELCOME_SEEN_KEY = 'waypoint:welcome-seen:v1';

export interface WelcomeModalProps {
  /** Whether the user is authenticated (modal triggers on auth transition) */
  isAuthenticated: boolean;
}

export function WelcomeModal({ isAuthenticated }: WelcomeModalProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [hasSeenWelcome, setHasSeenWelcome] = useState(true);
  const [isCompactViewport, setIsCompactViewport] = useState(false);
  const { push } = useRouter();
  const pathname = usePathname();

  // Check localStorage on mount and when auth state changes
  useEffect(() => {
    if (!isAuthenticated) {
      setIsOpen(false);
      return;
    }

    try {
      const seen = localStorage.getItem(WELCOME_SEEN_KEY);
      if (seen === '1') {
        setHasSeenWelcome(true);
        return;
      }
    } catch {
      // localStorage unavailable
    }

    setHasSeenWelcome(false);
    setIsOpen(true);
  }, [isAuthenticated]);

  useEffect(() => {
    const updateViewport = () => setIsCompactViewport(window.innerWidth < 640);
    updateViewport();
    window.addEventListener('resize', updateViewport);
    return () => window.removeEventListener('resize', updateViewport);
  }, []);

  const dismiss = useCallback(() => {
    try {
      localStorage.setItem(WELCOME_SEEN_KEY, '1');
    } catch {
      // ignore
    }
    setHasSeenWelcome(true);
    setIsOpen(false);
  }, []);

  const handleNavigate = useCallback((href: string) => {
    dismiss();
    push(href);
  }, [dismiss, push]);

  // Don't render anything if already seen
  if (hasSeenWelcome || pathname.startsWith('/workbench')) return null;

  const preferCompactCard = isCompactViewport;

  return preferCompactCard ? (
    <div
      className="fixed inset-x-2 bottom-2 z-40 overflow-hidden rounded-2xl border shadow-2xl backdrop-blur-sm"
      style={{
        background: 'rgba(13,17,23,0.94)',
        borderColor: 'rgba(48,54,61,0.95)',
      }}
      aria-label="Welcome to Waypoint"
    >
      <div className="flex items-start gap-3 p-3 border-b" style={{ borderColor: 'rgba(48,54,61,0.85)' }}>
        <div className="size-9 rounded-xl flex items-center justify-center shrink-0"
          style={{ background: 'rgba(88,166,255,0.12)', border: '1px solid rgba(88,166,255,0.18)' }}
        >
          <Sparkles className="size-4" style={{ color: 'var(--accent-blue)' }} />
        </div>
        <div className="min-w-0 flex-1">
          <h2 className="text-[14px] font-semibold text-[#e6edf3] truncate">Welcome to Waypoint</h2>
          <p className="mt-0.5 text-[12px] leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
            Your workspace is ready. These shortcuts won&apos;t block the app.
          </p>
        </div>
        <button
          type="button"
          onClick={dismiss}
          className="rounded-lg p-1.5 transition-colors hover:bg-[#161b22]"
          aria-label="Close welcome card"
        >
          <X className="size-4 text-[#8b949e]" />
        </button>
      </div>

      <div className="flex items-center gap-2 p-3">
        <button
          type="button"
          onClick={() => handleNavigate('/workbench?draft=new&tab=intake')}
          className="flex-1 rounded-lg border px-3 py-2 text-left text-[12px] transition-colors"
          style={{
            background: 'var(--bg-surface)',
            borderColor: 'var(--border-default)',
            color: 'var(--text-primary)',
          }}
        >
          Open intake
        </button>
        <button
          type="button"
          onClick={dismiss}
          className="rounded-lg px-3 py-2 text-[12px] font-semibold transition-colors"
          style={{
            background: 'var(--accent-blue)',
            color: '#fff',
          }}
        >
          Get started
        </button>
      </div>
    </div>
  ) : (
    <div
      className="fixed bottom-4 right-4 z-40 w-[min(92vw,28rem)] rounded-2xl border shadow-2xl backdrop-blur-sm"
      style={{
        background: 'rgba(13,17,23,0.94)',
        borderColor: 'rgba(48,54,61,0.95)',
      }}
      aria-label="Welcome to Waypoint"
    >
        <div className="flex items-start gap-3 p-4 border-b" style={{ borderColor: 'rgba(48,54,61,0.85)' }}>
          <div className="size-10 rounded-xl flex items-center justify-center shrink-0"
            style={{ background: 'rgba(88,166,255,0.12)', border: '1px solid rgba(88,166,255,0.18)' }}
          >
            <Sparkles className="size-5" style={{ color: 'var(--accent-blue)' }} />
          </div>
          <div className="min-w-0 flex-1">
            <h2 className="text-[15px] font-semibold text-[#e6edf3] truncate">Welcome to Waypoint</h2>
            <p className="mt-1 text-[13px] leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
              Your workspace is ready. These shortcuts won&apos;t block the rest of the app.
            </p>
          </div>
          <button
            type="button"
            onClick={dismiss}
            className="rounded-lg p-2 transition-colors hover:bg-[#161b22]"
            aria-label="Close welcome card"
          >
            <X className="size-4 text-[#8b949e]" />
          </button>
        </div>

        <div className="p-4 space-y-2">
          <button
            type="button"
            onClick={() => handleNavigate('/workbench?draft=new&tab=intake')}
            className="w-full flex items-center gap-3 p-3 rounded-xl border transition-colors text-left"
            style={{
              background: 'var(--bg-surface)',
              borderColor: 'var(--border-default)',
            }}
          >
            <div className="size-9 rounded-lg flex items-center justify-center shrink-0"
              style={{ background: 'rgba(88,166,255,0.10)', border: '1px solid rgba(88,166,255,0.20)' }}
            >
              <MessageSquare className="size-4" style={{ color: 'var(--accent-blue)' }} />
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-[13px] font-medium" style={{ color: 'var(--text-primary)' }}>
                Process your first inquiry
              </div>
              <div className="text-[12px] mt-0.5" style={{ color: 'var(--text-muted)' }}>
                Paste a customer note and let Waypoint extract the trip details.
              </div>
            </div>
          </button>

          <button
            type="button"
            onClick={() => handleNavigate('/inbox')}
            className="w-full flex items-center gap-3 p-3 rounded-xl border transition-colors text-left"
            style={{
              background: 'var(--bg-surface)',
              borderColor: 'var(--border-default)',
            }}
          >
            <div className="size-9 rounded-lg flex items-center justify-center shrink-0"
              style={{ background: 'rgba(57,208,216,0.10)', border: '1px solid rgba(57,208,216,0.20)' }}
            >
              <Inbox className="size-4" style={{ color: 'var(--accent-cyan)' }} />
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-[13px] font-medium" style={{ color: 'var(--text-primary)' }}>
                Review the Lead Inbox
              </div>
              <div className="text-[12px] mt-0.5" style={{ color: 'var(--text-muted)' }}>
                See all captured inquiries ready for planning and quotes.
              </div>
            </div>
          </button>

          <button
            type="button"
            onClick={() => handleNavigate('/settings')}
            className="w-full flex items-center gap-3 p-3 rounded-xl border transition-colors text-left"
            style={{
              background: 'var(--bg-surface)',
              borderColor: 'var(--border-default)',
            }}
          >
            <div className="size-9 rounded-lg flex items-center justify-center shrink-0"
              style={{ background: 'rgba(210,153,34,0.10)', border: '1px solid rgba(210,153,34,0.20)' }}
            >
              <Settings className="size-4" style={{ color: 'var(--accent-amber)' }} />
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-[13px] font-medium" style={{ color: 'var(--text-primary)' }}>
                Configure your workspace
              </div>
              <div className="text-[12px] mt-0.5" style={{ color: 'var(--text-muted)' }}>
                Invite team members and customize agency settings.
              </div>
            </div>
          </button>

          <div className="rounded-xl border p-3" style={{ borderColor: 'rgba(88,166,255,0.20)', background: 'rgba(88,166,255,0.04)' }}>
            <div className="flex items-center gap-2 mb-1.5">
              <Compass className="size-4" style={{ color: 'var(--accent-blue)' }} />
              <span className="text-[12px] font-semibold uppercase tracking-wider" style={{ color: 'var(--accent-blue)' }}>
                Pro tip
              </span>
            </div>
            <p className="text-[13px] leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
              Press{' '}
              <kbd className="inline-flex items-center px-1.5 py-0.5 rounded text-[11px] font-mono" style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-default)' }}>
                {typeof window !== 'undefined' && window.navigator.platform.includes('Mac') ? 'Cmd' : 'Ctrl'}
              </kbd>
              {' + '}
              <kbd className="inline-flex items-center px-1.5 py-0.5 rounded text-[11px] font-mono" style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-default)' }}>
                N
              </kbd>
              {' '}anywhere to start a new inquiry quickly.
            </p>
          </div>

          <div className="flex justify-end pt-1">
            <button
              type="button"
              onClick={dismiss}
              className="px-4 py-2 rounded-lg text-[13px] font-semibold transition-colors"
              style={{
                background: 'var(--accent-blue)',
                color: '#fff',
              }}
            >
              Get started
            </button>
          </div>
        </div>
    </div>
  );
}
