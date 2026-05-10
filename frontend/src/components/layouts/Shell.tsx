'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useTrip } from '@/hooks/useTrips';
import { useRuntimeVersion } from '@/hooks/useRuntimeVersion';
import {
  Inbox,
  LayoutDashboard,
  BarChart2,
  ClipboardCheck,
  MapPin,
  Activity,
  Zap,
  Layers,
  Settings,
  AlertTriangle,
  Users,
  FileText,
  CalendarCheck,
  DollarSign,
  Briefcase,
  Search,
  BookOpen,
  Send,
  type LucideProps,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { LiveRegion } from '@/lib/accessibility';
import { toast } from '@/lib/toast-store';
import { useUnifiedState } from '@/hooks/useUnifiedState';
import { useAgencySettings } from '@/hooks/useAgencySettings';
import { NAV_SECTIONS } from '@/lib/nav-modules';
import { UserMenu } from './UserMenu';

const ICON_MAP: Record<string, React.ComponentType<LucideProps>> = {
  LayoutDashboard,
  Inbox,
  ClipboardCheck,
  Users,
  Layers,
  FileText,
  CalendarCheck,
  DollarSign,
  Briefcase,
  Search,
  BarChart2,
  BookOpen,
  Send,
  Settings,
};


function parseTripIdFromPathname(pathname: string): string | null {
  const match = pathname.match(/^\/trips\/([^/]+)/);
  return match?.[1] ?? null;
}

function getPageLabel(pathname: string, isLeadReviewRoute: boolean): string {
  // Prevent breadcrumb from exposing internal route names
  if (pathname === '/workbench') return 'New Inquiry';
  if (isLeadReviewRoute) return 'Lead Inbox';
  for (const section of NAV_SECTIONS) {
    for (const item of section.items) {
      if (pathname === item.href || pathname.startsWith(item.href + '/')) {
        return item.label;
      }
    }
  }
  return pathname.split('/').filter(Boolean).pop()?.replace(/-/g, ' ') ?? 'Overview';
}

export function Shell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const shellTripId = parseTripIdFromPathname(pathname);
  const { data: shellTrip, isLoading: isShellTripLoading } = useTrip(shellTripId);
  const { detailsLabel } = useRuntimeVersion();
  const { isConsistent } = useUnifiedState();
  const { data: agencySettings } = useAgencySettings();
  const productName = 'Waypoint OS';
  const agencyName = agencySettings?.profile?.agency_name || 'Agency Workspace';
  const brandDescriptor = [agencySettings?.profile?.sub_brand, agencySettings?.profile?.plan_label]
    .filter((v): v is string => Boolean(v && v.trim()))
    .join(' · ');
  const isTripIntakeRoute = /^\/trips\/[^/]+\/intake$/.test(pathname);
  const isLeadReviewRoute =
    (pathname.startsWith('/trips/') &&
      (shellTrip?.status === 'new' || shellTrip?.status === 'incomplete')) ||
    (isTripIntakeRoute && isShellTripLoading);

  return (
    <div className='flex h-screen overflow-hidden' style={{ background: 'var(--bg-canvas)', color: 'var(--text-primary)' }}>
      <LiveRegion />
      <a href='#main-content' className='sr-only-focusable'>Skip to main content</a>

      {/* Sidebar - distinct surface, visible edge */}
      <aside
        className='flex flex-col w-[72px] md:w-[220px] shrink-0'
        style={{
          borderRight: '1px solid var(--border-default)',
          background: 'var(--bg-surface)',
        }}
        aria-label='Main navigation'
      >
        {/* Brand */}
        <div
          className='flex items-center gap-2.5 px-3 md:px-4 h-14 shrink-0 justify-center md:justify-start'
          style={{ borderBottom: '1px solid var(--border-default)' }}
        >
          <div
            className='flex size-7 items-center justify-center rounded-sm shrink-0'
            style={{ background: 'var(--accent-blue)' }}
          >
            <MapPin className='size-3.5' style={{ color: 'var(--text-on-accent)' }} aria-hidden='true' />
          </div>
          <div className='hidden md:block overflow-hidden'>
            <div className='text-sm font-semibold leading-tight tracking-tight truncate'>
              {productName}
            </div>
            <div className='text-xs font-mono truncate' style={{ color: 'var(--text-muted)' }}>
              {agencyName}
            </div>
            {brandDescriptor ? (
              <div className='text-[10px] font-mono truncate' style={{ color: 'var(--text-placeholder)' }}>
                {brandDescriptor}
              </div>
            ) : null}
          </div>
        </div>

        {/* New Inquiry CTA - action, not a place. Icon-only on collapsed sidebar. */}
        <div className='px-2 md:px-4 pt-3 pb-1'>
          <Link
            href='/workbench?draft=new&tab=intake'
            aria-label='New Inquiry'
            className='flex items-center justify-center gap-2 px-3 py-1.5 rounded-lg text-[12px] font-medium transition-colors border'
            style={{
              background: 'var(--bg-elevated)',
              color: 'var(--text-primary)',
              borderColor: 'var(--border-default)',
            }}
            onMouseEnter={(e) => {
              const el = e.currentTarget as HTMLAnchorElement;
              el.style.borderColor = 'var(--accent-blue)'; el.style.color = 'var(--accent-blue)';
            }}
            onMouseLeave={(e) => {
              const el = e.currentTarget as HTMLAnchorElement;
              el.style.borderColor = 'var(--border-default)'; el.style.color = 'var(--text-primary)';
            }}
          >
            <Send className='size-3.5 shrink-0' aria-hidden='true' />
            <span className='hidden md:inline'>New Inquiry</span>
          </Link>
        </div>

        {/* Navigation */}
        <nav className='flex-1 overflow-y-auto py-3 px-2 space-y-4' aria-label='Primary navigation'>
          {NAV_SECTIONS.map((section) => (
            <div key={section.label}>
              <div className='hidden md:block px-2 pb-1.5 text-xs font-semibold uppercase tracking-wider' style={{ color: 'var(--text-muted)' }}>
                {section.label}
              </div>
              <ul className='space-y-0.5' role='list'>
                {section.items.map((item) => {
                  const Icon = ICON_MAP[item.icon] ?? Activity;
                  // Active check: ignore query params for href matching
                  const hrefPath = item.href.split('?')[0];
                  const defaultIsActive = pathname === hrefPath || pathname.startsWith(hrefPath + '/');
                  const isActive = item.enabled && (
                    isLeadReviewRoute
                      ? hrefPath === '/inbox'
                      : defaultIsActive
                  );
                  if (!item.enabled) {
                    return (
                      <li key={item.href}>
                        <button
                          type="button"
                          onClick={() => toast(`${item.label} is coming soon. We'll notify you when it's ready.`, 'info')}
                          className='w-full flex items-center justify-center md:justify-start gap-2.5 px-2.5 py-2 rounded-md opacity-40 cursor-pointer select-none hover:opacity-60 transition-opacity'
                          title={`${item.description} - Coming soon`}
                          aria-disabled='true'
                          aria-label={`${item.label}, coming soon`}
                        >
                          <Icon className='size-3.5 shrink-0' aria-hidden='true' />
                          <span className='hidden md:inline text-[13px]' style={{ color: 'var(--text-muted)' }}>
                            {item.label}
                          </span>
                          <span className='hidden md:inline text-[10px] ml-auto' style={{ color: 'var(--text-placeholder)' }}>
                            Planned
                          </span>
                        </button>
                      </li>
                    );
                  }
                  return (
                    <li key={item.href}>
                      <Link
                        href={item.href}
                        className={cn(
                          'relative flex items-center justify-center md:justify-start gap-2.5 px-2.5 py-2 rounded-md text-[13px] font-medium transition-colors',
                          isActive
                            ? 'text-text-primary'
                            : 'hover:text-text-primary'
                        )}
                        style={isActive
                          ? { background: 'var(--bg-elevated)', color: 'var(--text-primary)' }
                          : { color: 'var(--text-muted)' }
                        }
                        aria-current={isActive ? 'page' : undefined}
                        aria-label={item.label}
                      >
                        {/* Active indicator: functional, not decorative */}
                        {isActive && (
                          <span
                            className='absolute left-0 top-1.5 bottom-1.5 w-[2px] rounded-full'
                            style={{ background: 'var(--accent-blue)' }}
                            aria-hidden='true'
                          />
                        )}
                        <Icon
                          className='size-3.5 shrink-0'
                          style={isActive ? { color: 'var(--accent-blue)' } : { color: 'var(--text-muted)' }}
                          aria-hidden='true'
                        />
                        <span className='hidden md:inline'>{item.label}</span>
                      </Link>
                    </li>
                  );
                })}
              </ul>
            </div>
          ))}
        </nav>

        {/* Status footer */}
        <div
          className='hidden md:block px-4 py-3 shrink-0'
          style={{ borderTop: '1px solid var(--border-default)' }}
        >
          <div className='flex items-center gap-2'>
            <span className='inline-block size-1.5 rounded-full animate-pulse-dot' style={{ background: 'var(--accent-green)' }} aria-hidden='true' />
            <span className='text-xs font-mono' style={{ color: 'var(--text-muted)' }} aria-live='polite'>
              Operations live
            </span>
          </div>
          {detailsLabel ? (
            <div className='mt-1 flex items-center gap-1.5 text-xs font-mono' style={{ color: 'var(--text-placeholder)' }}>
              <Activity className='size-3' aria-hidden='true' />
              <span aria-live='polite'>{detailsLabel}</span>
            </div>
          ) : null}
        </div>
      </aside>

      {/* Main column */}
      <div className='flex flex-col flex-1 min-w-0 overflow-hidden'>
        {/* Integrity Warning */}
        {!isConsistent && (
          <div
            className='flex items-center justify-center gap-2 py-1.5 px-4 text-center text-xs font-bold tracking-wider uppercase z-50'
            style={{ background: 'var(--accent-red)', color: '#ffffff' }}
          >
            <AlertTriangle className='size-3' aria-hidden='true' />
            CRITICAL: Data inconsistency detected. Please refresh.
          </div>
        )}

        {/* Command bar */}
        <header
          className='flex items-center justify-between h-11 px-5 shrink-0'
          style={{
            borderBottom: '1px solid var(--border-default)',
            background: 'var(--bg-canvas)',
          }}
        >
          <nav className='flex items-center gap-2 text-sm' aria-label='Breadcrumb navigation'>
            <Link href='/overview' className='transition-colors' style={{ color: 'var(--text-placeholder)' }}>
              Waypoint OS
            </Link>
            {pathname !== '/overview' && (
              <>
                <span style={{ color: 'var(--border-default)' }} aria-hidden='true'>/</span>
                <span className='capitalize font-medium' style={{ color: 'var(--text-primary)' }} aria-current='page'>
                  {getPageLabel(pathname, isLeadReviewRoute)}
                </span>
              </>
            )}
          </nav>
          <div className='flex items-center gap-3'>
            <div className='flex items-center gap-1.5 text-xs font-mono' style={{ color: 'var(--text-muted)' }} role='status' aria-live='polite'>
              <Zap className='size-3' style={{ color: 'var(--accent-amber)' }} aria-hidden='true' />
              <span>System ready</span>
            </div>
            <UserMenu />
          </div>
        </header>

        {/* Page content */}
        <main id='main-content' className='flex-1 overflow-y-auto pb-0' tabIndex={-1}>
          {children}
        </main>
      </div>
    </div>
  );
}
