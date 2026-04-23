'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useRuntimeVersion } from '@/hooks/useRuntimeVersion';
import {
  Briefcase,
  Inbox,
  LayoutDashboard,
  BarChart2,
  ClipboardCheck,
  MapPin,
  Activity,
  Zap,
  Layers,
  Wrench,
  Settings,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { LiveRegion } from '@/lib/accessibility';
import { useUnifiedState } from '@/hooks/useUnifiedState';
import { useAgencySettings } from '@/hooks/useAgencySettings';
import { AlertTriangle } from 'lucide-react';
import { UserMenu } from './UserMenu';

const NAV = [
  {
    label: 'OPERATE',
    items: [
      {
        href: '/inbox',
        label: 'Inbox',
        icon: Inbox,
        description: 'Triage and prioritize incoming demand',
      },
      {
        href: '/workspace',
        label: 'Workspaces',
        icon: Layers,
        description: 'Active trips in progress',
      },
      {
        href: '/overview',
        label: 'Overview',
        icon: LayoutDashboard,
        description: 'Dashboard and pipeline summary',
      },
    ],
  },
  {
    label: 'GOVERN',
    items: [
      {
        href: '/owner/reviews',
        label: 'Pending Reviews',
        icon: ClipboardCheck,
        description: 'Approve high-risk and exception decisions',
      },
      {
        href: '/owner/insights',
        label: 'Analytics',
        icon: BarChart2,
        description: 'Monitor quality, throughput, and conversion',
      },
      {
        href: '/settings',
        label: 'Settings',
        icon: Settings,
        description: 'Agency profile, autonomy, and operations',
      },
    ],
  },
  {
    label: 'TOOLS',
    items: [
      {
        href: '/workbench',
        label: 'Workbench',
        icon: Wrench,
        description: 'Audit surface — fixture runs, QA, inspection',
      },
    ],
  },
];

function getPageLabel(pathname: string): string {
  for (const section of NAV) {
    for (const item of section.items) {
      if (pathname === item.href || pathname.startsWith(item.href + '/')) {
        return item.label;
      }
    }
  }
  return (
    pathname.split('/').filter(Boolean).pop()?.replace(/-/g, ' ') ?? 'Overview'
  );
}

export function Shell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { versionLabel, detailsLabel } = useRuntimeVersion();
  const { isConsistent } = useUnifiedState();
  const { data: agencySettings } = useAgencySettings();
  const brandName = agencySettings?.profile?.agency_name || 'Waypoint';

  // Public marketing + auth pages render without the app shell chrome
  if (
    pathname === '/' ||
    pathname.startsWith('/itinerary-checker') ||
    pathname.startsWith('/login') ||
    pathname.startsWith('/signup') ||
    pathname.startsWith('/forgot-password') ||
    pathname.startsWith('/reset-password')
  ) {
    return <>{children}</>;
  }

  return (
    <div className='flex h-screen overflow-hidden bg-[#080a0c] text-[#e6edf3]'>
      {/* Live regions for screen reader announcements */}
      <LiveRegion />

      {/* Skip navigation link */}
      <a href='#main-content' className='skip-link'>
        Skip to main content
      </a>

      {/* ── Sidebar ── */}
      <aside
        className='flex flex-col w-[72px] md:w-[220px] shrink-0 border-r border-[#1c2128] bg-[#0a0d11]'
        aria-label='Main navigation'
      >
        {/* Brand */}
        <div className='flex items-center gap-2.5 px-3 md:px-4 h-14 border-b border-[#1c2128] shrink-0 justify-center md:justify-start'>
          <div className='flex h-7 w-7 items-center justify-center rounded-md bg-gradient-to-br from-[#2563eb] to-[#39d0d8] shrink-0'>
            <MapPin className='h-3.5 w-3.5 text-white' aria-hidden='true' />
          </div>
          <div className='min-w-0 hidden md:block'>
            <div className='text-xs font-semibold leading-tight tracking-tight truncate'>
              {brandName}
            </div>
            <div className='text-xs text-[#8b949e] leading-tight font-mono'>
              {versionLabel}
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav
          className='flex-1 overflow-y-auto py-3 px-2 space-y-4'
          aria-label='Primary navigation'
        >
          {NAV.map((section) => (
            <div key={section.label}>
              <div className='hidden md:block px-2 pb-1.5 text-xs font-semibold tracking-widest text-[#484f58] uppercase'>
                {section.label}
              </div>
              <ul className='space-y-0.5' role='list'>
                {section.items.map((item) => {
                  const Icon = item.icon;
                  const isActive =
                    pathname === item.href || pathname.startsWith(item.href + '/');
                  return (
                    <li key={item.href}>
                      <Link
                        href={item.href}
                        className={cn(
                          'flex items-center justify-center md:justify-start gap-2.5 px-2.5 py-2 rounded-md text-[13px] transition-all duration-150',
                          isActive
                            ? 'bg-[#161b22] text-[#e6edf3] border-l-2 border-[#58a6ff]'
                            : 'text-[#8b949e] hover:text-[#e6edf3] hover:bg-[#0f1115]',
                        )}
                        aria-current={isActive ? 'page' : undefined}
                        aria-label={item.label}
                      >
                        <Icon
                          className={cn(
                            'h-3.5 w-3.5 shrink-0',
                            isActive ? 'text-[#58a6ff]' : '',
                          )}
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
        <div className='hidden md:block px-4 py-3 border-t border-[#1c2128] shrink-0'>
          <div className='flex items-center gap-2'>
            <span
              className='inline-block h-1.5 w-1.5 rounded-full bg-[#3fb950] animate-pulse-dot'
              aria-hidden='true'
            />
            <span
              className='text-xs text-[#8b949e] font-mono'
              aria-live='polite'
            >
              system · live
            </span>
          </div>
          <div className='mt-1 flex items-center gap-1.5 text-xs text-[#484f58]'>
            <Activity className='h-3 w-3' aria-hidden='true' />
            <span className='font-mono' aria-live='polite'>
              {detailsLabel}
            </span>
          </div>
        </div>
      </aside>

      {/* ── Main column ── */}
      <div className='flex flex-col flex-1 min-w-0 overflow-hidden'>
        {/* Integrity Warning Banner */}
        {!isConsistent && (
          <div className='bg-[#f85149] text-white py-1.5 px-4 text-center text-[11px] font-bold tracking-wider uppercase flex items-center justify-center gap-2 z-50'>
            <AlertTriangle className='h-3 w-3' />
            CRITICAL: SYSTEM INTEGRITY ERROR - Dashboard sums do not match canonical total.
          </div>
        )}

        {/* Command bar */}
        <header className='flex items-center justify-between h-11 px-5 border-b border-[#1c2128] bg-[#0a0d11]/80 backdrop-blur-xl shrink-0'>
          <nav
            className='flex items-center gap-2 text-sm'
            aria-label='Breadcrumb navigation'
          >
            <Link
              href='/overview'
              className='text-[#484f58] hover:text-[#8b949e] text-[12px] transition-colors'
            >
              {brandName}
            </Link>
            {pathname !== '/overview' && (
              <>
                <span className='text-[#30363d]' aria-hidden='true'>
                  /
                </span>
                <span
                  className='text-[#e6edf3] text-[12px] capitalize font-medium'
                  aria-current='page'
                >
                  {getPageLabel(pathname)}
                </span>
              </>
            )}
          </nav>
          <div className='flex items-center gap-3'>
            <div
              className='flex items-center gap-1.5 text-xs text-[#8b949e] font-mono'
              role='status'
              aria-live='polite'
            >
              <Zap className='h-3 w-3 text-[#d29922]' aria-hidden='true' />
              <span>ready</span>
            </div>
            <UserMenu />
          </div>
        </header>

        {/* Page content */}
        <main
          id='main-content'
          className='flex-1 overflow-y-auto pb-0'
          tabIndex={-1}
        >
          {children}
        </main>
      </div>
    </div>
  );
}
