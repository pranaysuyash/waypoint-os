import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { PriorityIndicator } from '@/components/ui/PriorityIndicator';

describe('PriorityIndicator', () => {
  it('renders dual-badge variant with urgency dot and importance diamond', () => {
    render(<PriorityIndicator urgency={70} importance={40} priorityLabel="high" />);
    const indicator = screen.getByRole('status');
    expect(indicator).toBeInTheDocument();
    expect(indicator).toHaveAttribute('aria-label', expect.stringContaining('Urgency'));
    expect(indicator).toHaveAttribute('aria-label', expect.stringContaining('Importance'));
  });

  it('renders compact variant as a priority chip', () => {
    render(<PriorityIndicator urgency={90} importance={80} priorityLabel="critical" variant="compact" />);
    const chip = screen.getByRole('status');
    expect(chip).toHaveTextContent('CRIT');
  });

  it('renders dot-only variant with urgency dot and priority text', () => {
    render(<PriorityIndicator urgency={30} importance={25} priorityLabel="medium" variant="dot-only" />);
    const dot = screen.getByRole('status');
    expect(dot).toHaveTextContent('MEDI');
  });

  it('shows labels when showLabels is true', () => {
    render(<PriorityIndicator urgency={90} importance={15} priorityLabel="high" showLabels />);
    expect(screen.getByText('CRITICAL')).toBeInTheDocument();
    expect(screen.getByText('LOW')).toBeInTheDocument();
  });

  it('handles low priority correctly', () => {
    render(<PriorityIndicator urgency={5} importance={3} priorityLabel="low" variant="compact" />);
    const chip = screen.getByRole('status');
    expect(chip).toHaveTextContent('LOW');
  });

  it('handles medium priority with high urgency', () => {
    render(<PriorityIndicator urgency={65} importance={15} priorityLabel="medium" variant="dot-only" />);
    const dot = screen.getByRole('status');
    expect(dot).toHaveTextContent('MEDI');
  });
});
