/**
 * InboxEmptyState
 *
 * Guidance component shown when no trips match the current filters.
 * Provides contextual help and quick actions to recover.
 */

'use client';

import { memo } from 'react';
import Link from 'next/link';
import { Search, Filter, Inbox, Plus } from 'lucide-react';


export interface InboxEmptyStateProps {
  hasSearch: boolean;
  activeFilter: string;
  onClearSearch?: () => void;
  onClearFilter?: () => void;
  className?: string;
}

export const InboxEmptyState = memo(function InboxEmptyState({
  hasSearch,
  activeFilter,
  onClearSearch,
  onClearFilter,
  className,
}: InboxEmptyStateProps) {
  const isFiltered = activeFilter !== 'all';
  const isTrulyEmpty = !isFiltered && !hasSearch;

  return (
    <div className={`col-span-full py-16 text-center ${className || ''}`}>
      <div
        className="inline-flex items-center justify-center w-12 h-12 rounded-full mb-4"
        style={{ background: 'rgba(139, 148, 158, 0.08)' }}
      >
        <Inbox className="w-6 h-6" style={{ color: 'var(--text-muted)' }} />
      </div>

      <p className="text-[var(--ui-text-sm)] font-medium" style={{ color: 'var(--text-secondary)' }}>
        {isTrulyEmpty
          ? 'No trips in your inbox'
          : hasSearch && isFiltered
          ? 'No trips match this filter and search.'
          : hasSearch
          ? 'No trips match your search.'
          : isFiltered
          ? 'No trips match this filter.'
          : 'Your inbox is empty.'}
      </p>

      <p className="text-[var(--ui-text-xs)] mt-1" style={{ color: 'var(--text-muted)' }}>
        {isTrulyEmpty
          ? 'Create a new inquiry to get started.'
          : hasSearch && isFiltered
          ? 'Try broadening your search or clearing the filter.'
          : hasSearch
          ? 'Try a different search term.'
          : isFiltered
          ? 'Try a different filter or check back later.'
          : 'New trips will appear here as they come in.'}
      </p>

      <div className="flex items-center justify-center gap-3 mt-4">
        {isTrulyEmpty && (
          <Link
            href="/workbench"
            className="inline-flex items-center gap-2 px-5 py-2.5 bg-[var(--accent-blue)] text-[var(--text-on-accent)] rounded-lg text-[var(--ui-text-sm)] font-semibold hover:bg-[var(--accent-blue-hover)] transition-colors"
          >
            <Plus className="w-4 h-4" />
            New Inquiry
          </Link>
        )}
        {hasSearch && onClearSearch && (
          <button
            type="button"
            onClick={onClearSearch}
className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[var(--ui-text-xs)] font-medium transition-colors"
             style={{
               color: 'var(--accent-blue)',
                background: 'rgba(var(--accent-blue-rgb), 0.1)',
             }}
          >
            <Search className="w-3.5 h-3.5" />
            Clear search
          </button>
        )}
        {isFiltered && onClearFilter && (
          <button
            type="button"
            onClick={onClearFilter}
className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[var(--ui-text-xs)] font-medium transition-colors"
             style={{
               color: 'var(--text-secondary)',
                background: 'rgba(var(--text-muted-rgb), 0.08)',
             }}
          >
            <Filter className="w-3.5 h-3.5" />
            Show all trips
          </button>
        )}
      </div>
    </div>
  );
});

export default InboxEmptyState;
