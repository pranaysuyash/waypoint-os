/**
 * Tests for EmptyStateOnboarding component.
 *
 * Verifies:
 * - All three onboarding steps render with correct labels and hrefs
 * - Step 1 links to /settings?tab=people (workspace invite from Task 1)
 * - Step 2 links to the workbench intake flow
 * - Step 3 links to inbox
 * - The "disappears once first trip" note is present
 */

import { render, screen } from '@testing-library/react';
import { EmptyStateOnboarding } from '../EmptyStateOnboarding';

describe('EmptyStateOnboarding', () => {
  it('renders the welcome heading', () => {
    render(<EmptyStateOnboarding />);
    expect(screen.getByText('Welcome to Waypoint')).toBeInTheDocument();
  });

  it('renders all three onboarding steps', () => {
    render(<EmptyStateOnboarding />);
    expect(screen.getByText('Invite your team')).toBeInTheDocument();
    expect(screen.getByText('Add your first inquiry')).toBeInTheDocument();
    expect(screen.getByText('Review in Lead Inbox')).toBeInTheDocument();
  });

  it('step 1 links to settings People tab (workspace invite flow)', () => {
    render(<EmptyStateOnboarding />);
    const inviteLink = screen.getByText('Invite your team').closest('a');
    expect(inviteLink).toHaveAttribute('href', '/settings?tab=people');
  });

  it('step 2 links to workbench intake', () => {
    render(<EmptyStateOnboarding />);
    const intakeLink = screen.getByText('Add your first inquiry').closest('a');
    expect(intakeLink).toHaveAttribute('href', '/workbench?draft=new&tab=intake');
  });

  it('step 3 links to inbox', () => {
    render(<EmptyStateOnboarding />);
    const inboxLink = screen.getByText('Review in Lead Inbox').closest('a');
    expect(inboxLink).toHaveAttribute('href', '/inbox');
  });

  it('shows the disappear note', () => {
    render(<EmptyStateOnboarding />);
    expect(
      screen.getByText(/disappears once your first trip/i)
    ).toBeInTheDocument();
  });

  it('renders steps in numbered order 1-2-3', () => {
    render(<EmptyStateOnboarding />);
    const numbers = screen.getAllByText(/^[123]$/);
    expect(numbers).toHaveLength(3);
    expect(numbers[0]).toHaveTextContent('1');
    expect(numbers[1]).toHaveTextContent('2');
    expect(numbers[2]).toHaveTextContent('3');
  });
});
