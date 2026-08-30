// @vitest-environment jsdom

import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import InteractiveProposalPage from '../[proposalId]/page';

vi.mock('next/navigation', () => ({
  useParams: () => ({ proposalId: 'prop_test_123' }),
}));

describe('InteractiveProposalPage', () => {
  it('renders the interactive proposal with tiers and add-ons', async () => {
    render(<InteractiveProposalPage />);

    expect(await screen.findByText(/Curated Luxury Itinerary Proposal/i)).toBeInTheDocument();
    expect(screen.getByText(/South Africa: Cape Town, Winelands/i)).toBeInTheDocument();
    expect(screen.getByText(/Select Your Preferred Proposal Tier/i)).toBeInTheDocument();
    expect(screen.getByText('Signature Curator')).toBeInTheDocument();
    expect(screen.getByText('Essential Saver')).toBeInTheDocument();
    expect(screen.getByText('Ultra Prestige Suite')).toBeInTheDocument();
    expect(screen.getByText(/Detailed Day-by-Day Journey/i)).toBeInTheDocument();
    expect(screen.getByText(/Enhance Your Journey/i)).toBeInTheDocument();

    const acceptBtn = screen.getByText(/Accept Proposal & Lock in 48-Hour Price Hold/i);
    expect(acceptBtn).toBeInTheDocument();
  });
});
