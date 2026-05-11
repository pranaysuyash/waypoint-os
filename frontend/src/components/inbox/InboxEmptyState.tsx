'use client';

import { memo } from 'react';
import { Search, Filter, Inbox } from 'lucide-react';
import { EmptyState } from '@/components/ui/empty-state';

export interface InboxEmptyStateProps {
  hasSearch: boolean;
  activeFilter?: string;
  hasFilters?: boolean;
  onClearSearch?: () => void;
  onClearFilter?: () => void;
  onClearAllFilters?: () => void;
  className?: string;
}

export const InboxEmptyState = memo(function InboxEmptyState({
  hasSearch,
  activeFilter,
  hasFilters,
  onClearSearch,
  onClearFilter,
  onClearAllFilters,
  className,
}: InboxEmptyStateProps) {
  const isFiltered = hasFilters !== undefined ? hasFilters : (activeFilter ?? 'all') !== 'all';
  const isTrulyEmpty = !isFiltered && !hasSearch;

  const title = isTrulyEmpty
    ? 'No new leads'
    : hasSearch && isFiltered
    ? 'No leads match this filter and search.'
    : hasSearch
    ? 'No leads match your search.'
    : isFiltered
    ? 'No leads match this filter.'
    : 'Your inbox is empty.';

  const description = isTrulyEmpty
    ? 'New customer inquiries will appear here before planning starts. Leads you start planning move to Trips in Planning.'
    : hasSearch && isFiltered
    ? 'Try broadening your search or clearing the filter.'
    : hasSearch
    ? 'Try a different search term.'
    : isFiltered
    ? 'Try a different filter or check back later.'
    : 'New inquiries will appear here as they come in.';

  return (
    <EmptyState
      icon={isTrulyEmpty ? Inbox : hasSearch ? Search : Filter}
      title={title}
      description={description}
      className={className}
      action={
        isTrulyEmpty
          ? { label: 'New Inquiry', href: '/workbench' }
          : hasSearch && onClearSearch
          ? { label: 'Clear search', onClick: onClearSearch }
          : undefined
      }
      secondaryAction={
        isFiltered && (onClearFilter || onClearAllFilters)
          ? { label: 'Show all trips', onClick: onClearAllFilters || onClearFilter }
          : undefined
      }
    />
  );
});

