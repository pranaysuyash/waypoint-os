import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { PipelineFlow, PIPELINE_STAGES } from '../PipelineFlow';

describe('PipelineFlow Component', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('renders active stage with correct aria-current attribute', () => {
    render(<PipelineFlow currentStage="decision" />);

    const activeStage = screen.getByLabelText(/Ready to Quote\?/i);
    expect(activeStage).toHaveAttribute('aria-current', 'step');
    expect(screen.getByText('Ready to Quote?')).toBeInTheDocument();
  });

  it('shows completed state for stages before current stage', () => {
    render(<PipelineFlow currentStage="decision" />);

    // "intake" and "packet" should be completed (index < currentIndex)
    const intakeStage = screen.getByLabelText(/New Inquiry: completed/i);
    expect(intakeStage).toBeInTheDocument();

    // Completed stages should have CheckCircle2 icon (svg with aria-hidden="true")
    const checkIcons = document.querySelectorAll('svg[aria-hidden="true"]');
    expect(checkIcons.length).toBeGreaterThan(0);
  });

  it('shows pending state for stages after current stage', () => {
    render(<PipelineFlow currentStage="decision" />);

    // "strategy" and "safety" should be pending (index > currentIndex)
    const pendingStage = screen.getByLabelText(/Build Options: pending/i);
    expect(pendingStage).not.toHaveAttribute('aria-current');
  });

  it('has proper navigation aria-label', () => {
    render(<PipelineFlow currentStage="intake" />);
    expect(screen.getByRole('navigation', { name: 'Pipeline progress' })).toBeInTheDocument();
  });

  it('uses ordered list (ol) for stage structure', () => {
    render(<PipelineFlow currentStage="intake" />);
    expect(screen.getByRole('list')).toBeInTheDocument();
  });

  it('uses shortLabel for mobile view', () => {
    render(<PipelineFlow currentStage="decision" />);
    // Check that shortLabel "Quote?" is present for mobile (lg:hidden)
    expect(screen.getByText('Quote?')).toBeInTheDocument();
  });

  it('includes status in aria-label (completed)', () => {
    render(<PipelineFlow currentStage="packet" />);
    // intake should be completed
    const intakeStage = screen.getByLabelText(/New Inquiry: completed/i);
    expect(intakeStage).toBeInTheDocument();
  });

  it('includes status in aria-label (current)', () => {
    render(<PipelineFlow currentStage="packet" />);
    // packet should be current
    const packetStage = screen.getByLabelText(/Trip Details: current/i);
    expect(packetStage).toHaveAttribute('aria-current', 'step');
  });

  it('includes status in aria-label (pending)', () => {
    render(<PipelineFlow currentStage="packet" />);
    // decision should be pending
    const decisionStage = screen.getByLabelText(/Ready to Quote\?: pending/i);
    expect(decisionStage).toBeInTheDocument();
  });

  it('exports PIPELINE_STAGES constant', () => {
    expect(PIPELINE_STAGES).toBeDefined();
    expect(PIPELINE_STAGES.length).toBe(5);
  });

  it('returns null and logs error for invalid stage (defensive guard)', () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    // Bypass TypeScript by casting to any - simulate runtime type bypass
    const { container } = render(<PipelineFlow currentStage={'invalid_stage' as any} />);

    // Component should return null
    expect(container.firstChild).toBeNull();

    // Should log error in non-production
    expect(consoleSpy.mock.calls.length).toBeGreaterThan(0);
    const firstCall = consoleSpy.mock.calls[0];
    expect(String(firstCall?.[0] || '')).toContain('PipelineFlow: Unknown');

    consoleSpy.mockRestore();
  });

  it('connector divs have aria-hidden attribute', () => {
    render(<PipelineFlow currentStage="intake" />);
    const connectors = document.querySelectorAll('[aria-hidden="true"]');
    // Should have at least 4 connectors (between 5 stages) + 1 pulse dot when active
    expect(connectors.length).toBeGreaterThanOrEqual(4);
  });
});
