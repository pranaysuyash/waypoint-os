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
import { useInboxStats, useInboxTrips, useReviews } from '@/hooks/useGovernance';
import { useIntegrityIssues } from '@/hooks/useIntegrityIssues';
import { useUnifiedState } from '@/hooks/useUnifiedState';
import { buildActionRequiredItems } from './buildActionRequiredItems';

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

function displayNavSub(
  total: number,
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
  const inbox = useInboxTrips(undefined, 1, 5);
  const inboxStats = useInboxStats();
  const pendingReviews = useReviews({ status: 'pending' });
  const integrityIssues = useIntegrityIssues();
  const pipelineQuery = usePipeline();
  const { state: unifiedState } = useUnifiedState();

  // SSOT: summary card counts come from unified state when available,
  // falling back to domain hooks during initial load.
  const workspaceCount = unifiedState?.workspace_trip_count ?? workspace.total;
  const inboxCount = unifiedState?.inbox_lead_count ?? inbox.total;
  const pendingReviewCount = unifiedState?.pending_review_count ?? pendingReviews.total;

  const orphanCount = integrityIssues.total;
  const pendingApprovalCount = pendingReviewCount;
  const opsHealth = opsHealthSummary(
    integrityIssues.total,
    integrityIssues.isLoading,
    Boolean(integrityIssues.error)
  );

  const metrics = useMemo<OverviewMetric[]>(
    () => [
      {
        title: 'Trips in Planning',
        value: displayCount(workspaceCount, workspace.isLoading, workspace.error),
        sub: displaySub(
          workspace.isLoading,
          workspace.error,
          `${pluralize(workspaceCount, 'trip', 'trips')} being planned`,
          'Trips unavailable',
        ),
        ctaLabel: 'Open trips',
        href: '/trips',
        state: 'blue',
        icon: Briefcase,
        isLoading: workspace.isLoading && !unifiedState,
        error: workspace.error,
      },
      {
        title: 'New enquiries',
        value: displayCount(inboxCount, inbox.isLoading, inbox.error),
        sub: displaySub(
          inbox.isLoading,
          inbox.error,
          `${pluralize(inboxCount, 'new enquiry', 'new enquiries')} to review`,
          'Enquiries unavailable',
        ),
        ctaLabel: inboxCount > 0 ? 'Review enquiries' : 'Open enquiries',
        href: '/inbox',
        state: 'amber',
        icon: Inbox,
        isLoading: inbox.isLoading && !unifiedState,
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
        isLoading: pendingReviews.isLoading && !unifiedState,
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
      inboxCount,
      integrityIssues.isLoading,
      pendingApprovalCount,
      pendingReviews.error,
      pendingReviews.isLoading,
      opsHealth.sub,
      opsHealth.value,
      unifiedState,
      workspace.error,
      workspace.isLoading,
      workspaceCount,
    ]
  );

  const navItems = useMemo<OverviewNavItem[]>(
    () => [
      {
        href: '/inbox',
        label: 'New enquiries',
        sub: displayNavSub(
          inboxCount,
          inbox.isLoading,
          inbox.error,
          `${pluralize(inboxCount, 'new enquiry', 'new enquiries')} to review`,
        ),
        subColor: 'var(--accent-amber)',
        icon: Inbox,
      },
      {
        href: '/trips',
        label: 'Trips in Planning',
        sub: displayNavSub(
          workspaceCount,
          workspace.isLoading,
          workspace.error,
          `${pluralize(workspaceCount, 'trip', 'trips')} being planned`,
        ),
        subColor: 'var(--accent-blue)',
        icon: Briefcase,
      },
      {
        href: '/reviews',
        label: 'Quote Review',
        sub: displayNavSub(
          pendingApprovalCount,
          pendingReviews.isLoading,
          pendingReviews.error,
          `${pluralize(pendingApprovalCount, 'quote', 'quotes')} to review`,
        ),
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
    [inboxCount, inbox.isLoading, inbox.error, opsHealth.sub, pendingApprovalCount, pendingReviews.isLoading, pendingReviews.error, workspaceCount, workspace.isLoading, workspace.error]
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

    if (anyPrimaryLoading && !unifiedState) {
      return 'Loading overview counts…';
    }

    return `${pluralize(workspaceCount, 'trip', 'trips')} in planning · ${pluralize(inboxCount, 'enquiry', 'enquiries')} · ${pluralize(pendingApprovalCount, 'quote', 'quotes')} to review`;
  }, [
    inbox.error,
    inbox.isLoading,
    inboxCount,
    pendingApprovalCount,
    pendingReviews.error,
    pendingReviews.isLoading,
    unifiedState,
    workspace.error,
    workspace.isLoading,
    workspaceCount,
  ]);

  const actionRequiredItems = useMemo(
    () =>
      buildActionRequiredItems({
        workspaceTrips: workspace.data,
        pendingReviews: pendingReviews.data,
        inboxTrips: inbox.data,
        inboxTotal: inboxCount,
        inboxStats: inboxStats.data ?? undefined,
      }),
    [
      inbox.data,
      inboxStats.data,
      inbox.total,
      pendingReviews.data,
      workspace.data,
    ]
  );

  const actionRequiredLoading = useMemo(
    () =>
      workspace.isLoading ||
      pendingReviews.isLoading ||
      inbox.isLoading ||
      inboxStats.isLoading ||
      integrityIssues.isLoading,
    [
      inbox.isLoading,
      inboxStats.isLoading,
      integrityIssues.isLoading,
      pendingReviews.isLoading,
      workspace.isLoading,
    ]
  );

  const actionRequiredError = useMemo<Error | null>(() => {
    return (
      workspace.error ||
      pendingReviews.error ||
      inbox.error ||
      inboxStats.error ||
      integrityIssues.error ||
      null
    );
  }, [inbox.error, inboxStats.error, integrityIssues.error, pendingReviews.error, workspace.error]);

  return {
    headerSubtitle,
    actionRequiredItems,
    actionRequiredLoading,
    actionRequiredError,
    metrics,
    navItems,
    pipeline,
    pipelineLoading: pipelineQuery.isLoading,
    pipelineError: pipelineQuery.error,
    recentTrips: workspace.data,
    recentTripsLoading: workspace.isLoading,
    recentTripsError: workspace.error,
    planningTripsTotal: workspaceCount,
    planningTripsLoading: workspace.isLoading && !unifiedState,
    planningTripsError: workspace.error,
    leadInboxTotal: inboxCount,
    leadInboxLoading: inbox.isLoading && !unifiedState,
    leadInboxError: inbox.error,
  };
}
