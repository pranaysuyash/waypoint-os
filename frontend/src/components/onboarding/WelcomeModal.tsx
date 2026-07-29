'use client';

/**
 * WelcomeModal - shown to the user on their first login.
 *
 * Persists dismissal in localStorage so it only shows once.
 * Displays a brief overview of the app's key workflows with
 * actionable links to the most important pages.
 */

import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { X, Compass, Inbox, MessageSquare, Settings } from 'lucide-react';
import { Modal } from '@/components/ui/modal';

const WELCOME_SEEN_KEY = 'waypoint:welcome-seen:v1';

export interface WelcomeModalProps {
  /** Whether the user is authenticated (modal triggers on auth transition) */
  isAuthenticated: boolean;
}

export function WelcomeModal({ isAuthenticated }: WelcomeModalProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [hasSeenWelcome, setHasSeenWelcome] = useState(true);
  const { push } = useRouter();

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
  if (hasSeenWelcome) return null;

  return (
    <Modal
      isOpen={isOpen}
      onClose={dismiss}
      title="Welcome to Waypoint"
      size="md"
      closeOnOverlay={false}
    >
      <div className="space-y-6">
        <p className="text-[13px] leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
          Your workspace is ready. Here are the key areas to get started.
        </p>

        {/* Quick links */}
        <div className="space-y-2">
          <button
            type="button"
            onClick={() => handleNavigate('/workbench?draft=new&tab=intake')}
            className="w-full flex items-center gap-4 p-3.5 rounded-xl border transition-colors text-left"
            style={{
              background: 'var(--bg-surface)',
              borderColor: 'var(--border-default)',
            }}
            onMouseEnter={(e) => {
              Object.assign(e.currentTarget.style, { borderColor: 'var(--accent-blue)', background: 'var(--bg-elevated)' });
            }}
            onMouseLeave={(e) => {
              Object.assign(e.currentTarget.style, { borderColor: 'var(--border-default)', background: 'var(--bg-surface)' });
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
            className="w-full flex items-center gap-4 p-3.5 rounded-xl border transition-colors text-left"
            style={{
              background: 'var(--bg-surface)',
              borderColor: 'var(--border-default)',
            }}
            onMouseEnter={(e) => {
              Object.assign(e.currentTarget.style, { borderColor: 'var(--accent-blue)', background: 'var(--bg-elevated)' });
            }}
            onMouseLeave={(e) => {
              Object.assign(e.currentTarget.style, { borderColor: 'var(--border-default)', background: 'var(--bg-surface)' });
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
            className="w-full flex items-center gap-4 p-3.5 rounded-xl border transition-colors text-left"
            style={{
              background: 'var(--bg-surface)',
              borderColor: 'var(--border-default)',
            }}
            onMouseEnter={(e) => {
              Object.assign(e.currentTarget.style, { borderColor: 'var(--accent-blue)', background: 'var(--bg-elevated)' });
            }}
            onMouseLeave={(e) => {
              Object.assign(e.currentTarget.style, { borderColor: 'var(--border-default)', background: 'var(--bg-surface)' });
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
        </div>

        {/* Tips */}
        <div className="rounded-xl border p-4" style={{ borderColor: 'rgba(88,166,255,0.20)', background: 'rgba(88,166,255,0.04)' }}>
          <div className="flex items-center gap-2 mb-2">
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

        {/* Footer */}
        <div className="flex justify-end pt-2">
          <button
            type="button"
            onClick={dismiss}
            className="px-5 py-2 rounded-lg text-[13px] font-semibold transition-colors"
            style={{
              background: 'var(--accent-blue)',
              color: '#fff',
            }}
            onMouseEnter={(e) => {
              (e.currentTarget as HTMLButtonElement).style.opacity = '0.9';
            }}
            onMouseLeave={(e) => {
              (e.currentTarget as HTMLButtonElement).style.opacity = '1';
            }}
          >
            Get started
          </button>
        </div>
      </div>
    </Modal>
  );
}
