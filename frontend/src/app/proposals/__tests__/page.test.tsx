// @vitest-environment jsdom

import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import InteractiveProposalPage from '../[proposalId]/page';

vi.mock('next/navigation', () => ({
  useParams: () => ({ proposalId: 'prop_test_123' }),
}));

describe('InteractiveProposalPage', () => {
  it('renders the interactive proposal with tiers and add-ons', async () => {
    render(<InteractiveProposalPage />);

    expect(await screen.findByText(/Curated Luxury Itinerary Proposal/i)).toBeInTheDocument();
    expect(screen.getByTestId('simulated-badge')).toHaveTextContent('Sample proposal');
    expect(screen.getByText(/not a supplier-backed booking/i)).toBeInTheDocument();
    expect(screen.getByText(/South Africa: Cape Town, Winelands/i)).toBeInTheDocument();
    expect(screen.getByText(/Select Your Preferred Proposal Tier/i)).toBeInTheDocument();
    expect(screen.getByText('Signature Curator')).toBeInTheDocument();
    expect(screen.getByText('Essential Saver')).toBeInTheDocument();
    expect(screen.getByText('Ultra Prestige Suite')).toBeInTheDocument();
    expect(screen.getByText(/Detailed Day-by-Day Journey/i)).toBeInTheDocument();
    expect(screen.getByText(/Enhance Your Journey/i)).toBeInTheDocument();

    const acceptBtn = screen.getByText(/Simulate Proposal Acceptance/i);
    expect(acceptBtn).toBeInTheDocument();
    expect(screen.getByText(/Illustrative pricing · not refreshed/i)).toBeInTheDocument();
    expect(screen.getByText(/Sample details — confirm availability/i)).toBeInTheDocument();
    expect(screen.queryByText(/Loading verified proposal/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/48h Price Lock Active/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Direct DMC Verified/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Live Pricing Updated/i)).not.toBeInTheDocument();
  });

  it('describes acceptance as simulated instead of claiming a DMC hold exists', async () => {
    const user = userEvent.setup();
    render(<InteractiveProposalPage />);

    const acceptBtn = await screen.findByText(/Simulate Proposal Acceptance/i);
    await user.click(acceptBtn.closest('button')!);

    // Demo confirmation must state that only a local preview occurred.
    expect(await screen.findByText(/Acceptance Preview Complete \(Demo\)/i)).toBeInTheDocument();
    expect(screen.getByText(/rendered an acceptance result locally/i)).toBeInTheDocument();
    expect(screen.getByText(/nothing was submitted/i)).toBeInTheDocument();
    expect(screen.getByText(/no inventory hold has actually been placed/i)).toBeInTheDocument();
  });
});
