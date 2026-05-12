'use client';

import { useMemo } from 'react';
import {
  AlertTriangle,
  Briefcase,
  CheckCircle2,
  Inbox,
  type LucideIcon,
} from 'lucide-react';
import { useTrips, usePipeline } from '@/hooks/useTrips';
import { useInboxTrips, useReviews } from '@/hooks/useGovernance';
import { useIntegrityIssues } from '@/hooks/useIntegrityIssues';

export type OverviewStateKey = 'green' | 'amber' | 'red' | 'blue';

export interface OverviewMetric {
  title: string;
  value: string | number;
  sub: string;
  ctaLabel: string;
  href: string;
  state: OverviewStateKey;
  icon: LucideIcon;
  isLoading?: boolean;
  error?: Error | null;
}

export interface OverviewNavItem {
  href: string;
  label: string;
  sub: string;
  subColor: string;
  icon: LucideIcon;
}

const SYSTEM_CHECK_HREF = '/overview?panel=system-check';

function pluralize(count: number, singular: string, plural: string): string {
  return `${count} ${count === 1 ? singular : plural}`;
}

function displayCount(total: number, isLoading: boolean, error?: Error | null): string | number {
  if (isLoading || error) return '-';
  return total;
}

function displaySub(
  isLoading: boolean,
  error: Error | null | undefined,
  readyLabel: string,
  errorLabel = 'Unavailable',
  loadingLabel = 'Loading…',
): string {
  if (error) return errorLabel;
  if (isLoading) return loadingLabel;
  return readyLabel;
}

function opsHealthSummary(
  total: number,
  isLoading: boolean,
  hasError: boolean,
): { value: string | number; sub: string } {
  if (hasError) {
    return { value: '-', sub: 'System check unavailable' };
  }

  if (isLoading) {
    return { value: '-', sub: 'Checking…' };
  }

  return {
    value: total,
    sub: `${pluralize(total, 'item to check', 'items to check')}`,
  };
}

export function useOverviewSummary() {
  const workspace = useTrips({ view: 'workspace', limit: 5 });
  const inbox = useInboxTrips(undefined, 1, 1);
  const pendingReviews = useReviews({ status: 'pending' });
  const integrityIssues = useIntegrityIssues();
  const pipelineQuery = usePipeline();
  const orphanCount = integrityIssues.total;
  const pendingApprovalCount = pendingReviews.total;
  const opsHealth = opsHealthSummary(
    integrityIssues.total,
    integrityIssues.isLoading,
    Boolean(integrityIssues.error)
  );

  const metrics = useMemo<OverviewMetric[]>(
    () => [
      {
        title: 'Trips in Planning',
        value: displayCount(workspace.total, workspace.isLoading, workspace.error),
        sub: displaySub(
          workspace.isLoading,
          workspace.error,
          `${pluralize(workspace.total, 'trip', 'trips')} being planned`,
          'Trips unavailable',
        ),
        ctaLabel: 'Open trips',
        href: '/trips',
        state: 'blue',
        icon: Briefcase,
        isLoading: workspace.isLoading,
        error: workspace.error,
      },
      {
        title: 'Lead Inbox',
        value: displayCount(inbox.total, inbox.isLoading, inbox.error),
        sub: displaySub(
          inbox.isLoading,
          inbox.error,
          `${pluralize(inbox.total, 'new lead', 'new leads')} to review`,
          'Leads unavailable',
        ),
        ctaLabel: inbox.total > 0 ? 'Review leads' : 'Open inbox',
        href: '/inbox',
        state: 'amber',
        icon: Inbox,
        isLoading: inbox.isLoading,
        error: inbox.error,
      },
      {
        title: 'Quote Review',
        value: displayCount(pendingApprovalCount, pendingReviews.isLoading, pendingReviews.error),
        sub: displaySub(
          pendingReviews.isLoading,
          pendingReviews.error,
          `${pluralize(pendingApprovalCount, 'quote', 'quotes')} to review`,
          'Quotes unavailable',
        ),
        ctaLabel: pendingApprovalCount > 0 ? 'Review quotes' : 'Open quote review',
        href: '/reviews',
        state: 'green',
        icon: CheckCircle2,
        isLoading: pendingReviews.isLoading,
        error: pendingReviews.error,
      },
      {
        title: 'System Check',
        value: opsHealth.value,
        sub: opsHealth.sub,
        ctaLabel: 'Check status',
        href: SYSTEM_CHECK_HREF,
        state: 'red',
        icon: AlertTriangle,
        isLoading: integrityIssues.isLoading,
        error: null,
      },
    ],
    [
      inbox.error,
      inbox.isLoading,
      inbox.total,
      integrityIssues.isLoading,
      pendingApprovalCount,
      pendingReviews.error,
      pendingReviews.isLoading,
      opsHealth.sub,
      opsHealth.value,
      workspace.error,
      workspace.isLoading,
      workspace.total,
    ]
  );

  const navItems = useMemo<OverviewNavItem[]>(
    () => [
      {
        href: '/inbox',
        label: 'Lead Inbox',
        sub: `${pluralize(inbox.total, 'new lead', 'new leads')} to review`,
        subColor: 'var(--accent-amber)',
        icon: Inbox,
      },
      {
        href: '/trips',
        label: 'Trips in Planning',
        sub: `${pluralize(workspace.total, 'trip', 'trips')} being planned`,
        subColor: 'var(--accent-blue)',
        icon: Briefcase,
      },
      {
        href: '/reviews',
        label: 'Quote Review',
        sub: `${pluralize(pendingApprovalCount, 'quote', 'quotes')} to review`,
        subColor: 'var(--accent-green)',
        icon: CheckCircle2,
      },
      {
        href: SYSTEM_CHECK_HREF,
        label: 'System Check',
        sub: opsHealth.sub,
        subColor: 'var(--accent-red)',
        icon: AlertTriangle,
      },
    ],
    [inbox.total, opsHealth.sub, pendingApprovalCount, workspace.total]
  );

  const pipeline = useMemo(() => {
    return pipelineQuery.data;
  }, [pipelineQuery.data]);

  const headerSubtitle = useMemo(() => {
    const anyPrimaryLoading =
      workspace.isLoading || inbox.isLoading || pendingReviews.isLoading;
    const anyPrimaryError =
      workspace.error || inbox.error || pendingReviews.error;

    if (anyPrimaryError) {
      return 'Some overview counts are unavailable';
    }

    if (anyPrimaryLoading) {
      return 'Loading overview counts…';
    }

    return `${pluralize(workspace.total, 'trip', 'trips')} in planning · ${pluralize(inbox.total, 'lead', 'leads')} · ${pluralize(pendingApprovalCount, 'quote', 'quotes')} to review`;
  }, [
    inbox.error,
    inbox.isLoading,
    inbox.total,
    pendingApprovalCount,
    pendingReviews.error,
    pendingReviews.isLoading,
    workspace.error,
    workspace.isLoading,
    workspace.total,
  ]);

  return {
    headerSubtitle,
    metrics,
    navItems,
    pipeline,
    pipelineLoading: pipelineQuery.isLoading,
    pipelineError: pipelineQuery.error,
    recentTrips: workspace.data,
    recentTripsLoading: workspace.isLoading,
    recentTripsError: workspace.error,
    planningTripsTotal: workspace.total,
    leadInboxTotal: inbox.total,
  };
}
