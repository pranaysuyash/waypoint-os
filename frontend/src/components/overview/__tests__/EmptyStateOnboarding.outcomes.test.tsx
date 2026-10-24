import { beforeEach, describe, expect, it } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { EmptyStateOnboarding } from '../EmptyStateOnboarding';

const empty = {
  inquiryCount: 0,
  needsDetailsCount: 0,
  readyBriefCount: 0,
  reviewedBriefCount: 0,
  planningStartedCount: 0,
  firstValueAchieved: false,
  nextAction: 'add_inquiry' as const,
  nextTripId: null,
};

describe('first-value onboarding evidence', () => {
  beforeEach(() => localStorage.clear());

  it('starts with an inquiry and keeps the team route optional for a solo owner', () => {
    render(<EmptyStateOnboarding activation={empty} />);
    const steps = screen.getAllByRole('listitem');
    expect(steps[0]).toHaveTextContent('Add your first inquiry');
    expect(screen.getByText(/optional.*invite your team/i).closest('a'))
      .toHaveAttribute('href', '/settings?tab=people');
  });

  it('does not complete a step when an operator clicks a destination', () => {
    render(<EmptyStateOnboarding activation={empty} />);
    fireEvent.click(screen.getByRole('link', { name: /add your first inquiry/i }));
    expect(screen.getByText('0 of 3 outcomes complete')).toBeInTheDocument();
    expect(localStorage.getItem('waypoint:onboarding-checklist:v2')).toBeNull();
  });

  it('keeps a blocked first inquiry visible with a direct recovery action', () => {
    render(<EmptyStateOnboarding activation={{
      ...empty,
      inquiryCount: 1,
      needsDetailsCount: 1,
      nextAction: 'resolve_details',
      nextTripId: 'blocked-inquiry',
    }} />);
    expect(screen.getByText('1 of 3 outcomes complete')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /resolve required details/i }))
      .toHaveAttribute('href', '/inquiries/new?trip=blocked-inquiry');
    expect(screen.getByText(/required details.*customer/i)).toBeInTheDocument();
  });

  it('uses current agency facts after a workspace switch instead of browser history', () => {
    localStorage.setItem('waypoint:onboarding-checklist:v2', JSON.stringify([
      'invite_team', 'first_inquiry', 'review_inbox',
    ]));
    const { rerender } = render(<EmptyStateOnboarding activation={{
      ...empty, inquiryCount: 1, readyBriefCount: 1, nextAction: 'review_brief', nextTripId: 'agency-a-inquiry',
    }} />);
    expect(screen.getByText('2 of 3 outcomes complete')).toBeInTheDocument();
    rerender(<EmptyStateOnboarding activation={empty} />);
    expect(screen.getByText('0 of 3 outcomes complete')).toBeInTheDocument();
    expect(screen.queryByRole('link', { name: /agency-a-inquiry/i })).not.toBeInTheDocument();
  });
});
