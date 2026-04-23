import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { InboxEmptyState } from '../InboxEmptyState';

describe('InboxEmptyState', () => {
  it('shows empty inbox message when no filters active', () => {
    render(
      <InboxEmptyState
        hasSearch={false}
        activeFilter="all"
      />
    );

    expect(screen.getByText('Your inbox is empty.')).toBeInTheDocument();
    expect(screen.getByText('New trips will appear here as they come in.')).toBeInTheDocument();
  });

  it('shows search-only message', () => {
    render(
      <InboxEmptyState
        hasSearch={true}
        activeFilter="all"
      />
    );

    expect(screen.getByText('No trips match your search.')).toBeInTheDocument();
  });

  it('shows filter-only message', () => {
    render(
      <InboxEmptyState
        hasSearch={false}
        activeFilter="at_risk"
      />
    );

    expect(screen.getByText('No trips match this filter.')).toBeInTheDocument();
  });

  it('shows combined filter+search message', () => {
    render(
      <InboxEmptyState
        hasSearch={true}
        activeFilter="critical"
      />
    );

    expect(screen.getByText('No trips match this filter and search.')).toBeInTheDocument();
  });

  it('shows clear search button when has search', () => {
    const onClearSearch = vi.fn();
    render(
      <InboxEmptyState
        hasSearch={true}
        activeFilter="all"
        onClearSearch={onClearSearch}
      />
    );

    const button = screen.getByText('Clear search');
    expect(button).toBeInTheDocument();
    fireEvent.click(button);
    expect(onClearSearch).toHaveBeenCalledTimes(1);
  });

  it('does not show clear search button when no search', () => {
    render(
      <InboxEmptyState
        hasSearch={false}
        activeFilter="all"
        onClearSearch={vi.fn()}
      />
    );

    expect(screen.queryByText('Clear search')).not.toBeInTheDocument();
  });

  it('shows show all button when filtered', () => {
    const onClearFilter = vi.fn();
    render(
      <InboxEmptyState
        hasSearch={false}
        activeFilter="unassigned"
        onClearFilter={onClearFilter}
      />
    );

    const button = screen.getByText('Show all trips');
    expect(button).toBeInTheDocument();
    fireEvent.click(button);
    expect(onClearFilter).toHaveBeenCalledTimes(1);
  });

  it('does not show show all button when not filtered', () => {
    render(
      <InboxEmptyState
        hasSearch={false}
        activeFilter="all"
        onClearFilter={vi.fn()}
      />
    );

    expect(screen.queryByText('Show all trips')).not.toBeInTheDocument();
  });

  it('shows both buttons when both search and filter active', () => {
    render(
      <InboxEmptyState
        hasSearch={true}
        activeFilter="at_risk"
        onClearSearch={vi.fn()}
        onClearFilter={vi.fn()}
      />
    );

    expect(screen.getByText('Clear search')).toBeInTheDocument();
    expect(screen.getByText('Show all trips')).toBeInTheDocument();
  });
});
