import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { RepeatTravelerRecallCard } from '../RepeatTravelerRecallCard';

/**
 * IMP-03 (DEMO-04/DEMO-08): the recall card must be unmistakably sample
 * content and must never inject fabricated facts into the real pipeline.
 */
describe('RepeatTravelerRecallCard', () => {
  it('renders a visible Sample data badge', () => {
    render(<RepeatTravelerRecallCard />);

    expect(screen.getByTestId('sample-data-badge')).toHaveTextContent('Sample data');
  });

  it('describes itself as a sample instead of claiming verified agency memory', () => {
    render(<RepeatTravelerRecallCard />);

    expect(
      screen.getByText(/Sample of the repeat-traveler memory panel/i),
    ).toBeInTheDocument();
    expect(
      screen.queryByText(/Verified historical profile recalled from agency memory/i),
    ).not.toBeInTheDocument();
  });

  it('shows obviously fake loyalty numbers instead of real-looking ones', () => {
    render(<RepeatTravelerRecallCard />);

    expect(screen.getByText(/SkyMiles #000000000 · Marriott Bonvoy #00000000/)).toBeInTheDocument();
    expect(screen.queryByText(/#928410294|#48192041/)).not.toBeInTheDocument();
  });

  it('renders sample-marked provenance sources, not tenant-scoped ones', () => {
    render(<RepeatTravelerRecallCard />);

    expect(screen.getAllByText(/^Source: Sample:/)).toHaveLength(3);
    expect(screen.queryByText(/Trip #\d+/)).not.toBeInTheDocument();
  });

  it('does not render any Apply-to-Proposal control that could inject sample facts', () => {
    render(<RepeatTravelerRecallCard />);

    expect(
      screen.queryByRole('button', { name: /apply to proposal/i }),
    ).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /applied to quote/i })).not.toBeInTheDocument();
  });

  it('never persists anything when a sample note is saved', async () => {
    render(<RepeatTravelerRecallCard />);

    await userEvent.click(screen.getByRole('button', { name: /add note/i }));
    await userEvent.type(
      screen.getByPlaceholderText(/high-floor quiet rooms/i),
      'Quiet room',
    );
    await userEvent.click(screen.getByRole('button', { name: /save fact/i }));

    expect(await screen.findByText(/Sample only — nothing was saved/i)).toBeInTheDocument();
    expect(screen.queryByText(/✅ Saved/i)).not.toBeInTheDocument();
  });

  it('accepts no props that could pipe sample data into the workbench store', () => {
    // Type-level guard is the signature itself (zero props); this runtime check
    // documents that the former onApplyPreferences injection path is gone.
    const onApplyPreferences = vi.fn();
    render(
      // @ts-expect-error — onApplyPreferences was removed in IMP-03; passing it must fail to compile.
      <RepeatTravelerRecallCard onApplyPreferences={onApplyPreferences} />,
    );

    expect(screen.getByTestId('sample-data-badge')).toBeInTheDocument();
    expect(onApplyPreferences).not.toHaveBeenCalled();
  });
});
