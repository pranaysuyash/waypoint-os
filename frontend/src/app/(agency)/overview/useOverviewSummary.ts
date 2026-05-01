'use client';

import { useMemo } from 'react';
import {
  AlertTriangle,
  Briefcase,
  CheckCircle2,
  Inbox,
  type LucideIcon,
} from 'lucide-react';
import { useTrips } from '@/hooks/useTrips';
import { useInboxTrips, useReviews } from '@/hooks/useGovernance';
import { useUnifiedState } from '@/hooks/useUnifiedState';
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

function pluralize(count: number, singular: string, plural: string): string {
  return `${count} ${count === 1 ? singular : plural}`;
}

function opsHealthSummary(
  total: number,
  isLoading: boolean,
  hasError: boolean,
): { value: string | number; sub: string } {
  if (hasError) {
    return { value: '—', sub: 'System check unavailable' };
  }

  if (isLoading) {
    return { value: '—', sub: 'Checking...' };
  }

  return {
    value: total,
    sub: `${pluralize(total, 'item to check', 'items to check')}`,
  };
}

const PLANNING_PIPELINE_STAGES = new Set(['assigned', 'in_progress']);

export function useOverviewSummary() {
  const workspace = useTrips({ view: 'workspace', limit: 5 });
  const inbox = useInboxTrips(undefined, 1, 1);
  const pendingReviews = useReviews({ status: 'pending' });
  const integrityIssues = useIntegrityIssues();
  const { state: unifiedState, loading: unifiedLoading, error: unifiedErrorMessage } = useUnifiedState();

  const unifiedError = unifiedErrorMessage ? new Error(unifiedErrorMessage) : null;
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
        value: workspace.total,
        sub: workspace.isLoading
          ? 'Loading...'
          : `${pluralize(workspace.total, 'trip', 'trips')} being planned`,
        ctaLabel: 'Open trips',
        href: '/trips',
        state: 'blue',
        icon: Briefcase,
        isLoading: workspace.isLoading,
        error: workspace.error,
      },
      {
        title: 'Lead Inbox',
        value: inbox.total,
        sub: inbox.isLoading
          ? 'Loading...'
          : `${pluralize(inbox.total, 'new lead', 'new leads')} to review`,
        ctaLabel: inbox.total > 0 ? 'Review leads' : 'Open inbox',
        href: '/inbox',
        state: 'amber',
        icon: Inbox,
        isLoading: inbox.isLoading,
        error: inbox.error,
      },
      {
        title: 'Quote Review',
        value: pendingApprovalCount,
        sub: pendingReviews.isLoading
          ? 'Loading...'
          : `${pluralize(pendingApprovalCount, 'quote', 'quotes')} to review`,
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
        href: '/workbench?panel=integrity',
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
        href: '/workbench?panel=integrity',
        label: 'System Check',
        sub: opsHealth.sub,
        subColor: 'var(--accent-red)',
        icon: AlertTriangle,
      },
    ],
    [inbox.total, opsHealth.sub, pendingApprovalCount, workspace.total]
  );

  const pipeline = useMemo(() => {
    if (!unifiedState) return null;
    return Object.entries(unifiedState.stages)
      .filter(([label]) => PLANNING_PIPELINE_STAGES.has(label))
      .map(([label, count]) => ({
        label: label.charAt(0).toUpperCase() + label.slice(1).replace('_', ' '),
        count,
      }));
  }, [unifiedState]);

  const headerSubtitle = useMemo(() => {
    if (workspace.isLoading && inbox.isLoading && pendingReviews.isLoading && unifiedLoading) {
      return 'Loading...';
    }

    return `${pluralize(workspace.total, 'trip', 'trips')} in planning · ${pluralize(inbox.total, 'lead', 'leads')} · ${pluralize(pendingApprovalCount, 'quote', 'quotes')} to review`;
  }, [
    inbox.isLoading,
    inbox.total,
    pendingApprovalCount,
    pendingReviews.isLoading,
    unifiedLoading,
    workspace.isLoading,
    workspace.total,
  ]);

  return {
    headerSubtitle,
    metrics,
    navItems,
    pipeline,
    pipelineLoading: unifiedLoading,
    pipelineError: unifiedError,
    recentTrips: workspace.data,
    recentTripsLoading: workspace.isLoading,
    recentTripsError: workspace.error,
    planningTripsTotal: workspace.total,
    leadInboxTotal: inbox.total,
  };
}
