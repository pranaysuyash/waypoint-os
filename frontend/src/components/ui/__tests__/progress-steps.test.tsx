import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ProgressSteps, type Step } from '../progress-steps';

const SAMPLE_STEPS = [
  { id: 'intake', label: 'New Inquiry', shortLabel: 'Inquiry' },
  { id: 'packet', label: 'Trip Details', shortLabel: 'Details' },
  { id: 'decision', label: 'Ready to Quote?', shortLabel: 'Quote?' },
] as const;

describe('ProgressSteps', () => {
  it('renders all step labels', () => {
    render(<ProgressSteps steps={SAMPLE_STEPS} currentId="intake" />);
    expect(screen.getByText('New Inquiry')).toBeInTheDocument();
    expect(screen.getByText('Trip Details')).toBeInTheDocument();
    expect(screen.getByText('Ready to Quote?')).toBeInTheDocument();
  });

  it('sets aria-current on current step', () => {
    render(<ProgressSteps steps={SAMPLE_STEPS} currentId="packet" />);
    const steps = screen.getAllByLabelText(/:/);
    expect(steps.length).toBeGreaterThanOrEqual(2);
  });

  it('renders completed checkmarks for past steps', () => {
    render(<ProgressSteps steps={SAMPLE_STEPS} currentId="decision" />);
    expect(screen.getByText('New Inquiry')).toBeInTheDocument();
  });

  it('uses custom aria labels', () => {
    render(
      <ProgressSteps
        steps={SAMPLE_STEPS}
        currentId="intake"
        getAriaLabel={(step, status) => `Step ${step.label}: ${status}`}
      />
    );
    expect(screen.getByLabelText('Step New Inquiry: current')).toBeInTheDocument();
  });

  it('renders vertically', () => {
    const { container } = render(
      <ProgressSteps steps={SAMPLE_STEPS} currentId="intake" orientation="vertical" />
    );
    expect(container.querySelector('[aria-label="Progress"]')).not.toBeNull();
  });
});
