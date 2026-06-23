import { render, screen } from '@testing-library/react';
import { PipelineFunnel } from '../PipelineFunnel';
import type { PipelineStage } from '../PipelineFunnel';
import { afterEach, describe, it, expect, vi } from 'vitest';

describe('PipelineFunnel', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  const mockData: PipelineStage[] = [
    { stageId: 'intake', stageName: 'New Inquiry', tripCount: 50 },
    { stageId: 'packet', stageName: 'Trip Details', tripCount: 40 },
    { stageId: 'decision', stageName: 'Ready to Quote?', tripCount: 30 },
    { stageId: 'strategy', stageName: 'Build Options', tripCount: 20 },
    { stageId: 'safety', stageName: 'Final Review', tripCount: 10 },
  ];

  it('renders funnel title and stage names', () => {
    vi.spyOn(HTMLElement.prototype, 'getBoundingClientRect').mockReturnValue({
      width: 960,
      height: 300,
      top: 0,
      left: 0,
      right: 960,
      bottom: 300,
      x: 0,
      y: 0,
      toJSON: () => ({}),
    });

    render(<PipelineFunnel data={mockData} />);
    expect(screen.getByText('Conversion Funnel')).toBeInTheDocument();
    expect(screen.getByText('New Inquiry')).toBeInTheDocument();
    expect(screen.getByText('Trip Details')).toBeInTheDocument();
    expect(screen.getByText('Ready to Quote?')).toBeInTheDocument();
    expect(screen.getByText('Build Options')).toBeInTheDocument();
    expect(screen.getByText('Final Review')).toBeInTheDocument();
  });

  it('renders all stage names in conversion rates section', () => {
    vi.spyOn(HTMLElement.prototype, 'getBoundingClientRect').mockReturnValue({
      width: 960,
      height: 300,
      top: 0,
      left: 0,
      right: 960,
      bottom: 300,
      x: 0,
      y: 0,
      toJSON: () => ({}),
    });

    render(<PipelineFunnel data={mockData} />);
    expect(screen.getByText('Stage Conversion Rates')).toBeInTheDocument();
    // Verify all stage names appear in the conversion rates list
    expect(screen.getByText('New Inquiry')).toBeInTheDocument();
    expect(screen.getByText('Trip Details')).toBeInTheDocument();
    expect(screen.getByText('Ready to Quote?')).toBeInTheDocument();
    expect(screen.getByText('Build Options')).toBeInTheDocument();
    expect(screen.getByText('Final Review')).toBeInTheDocument();
  });

  it('renders conversion percentages between stages', () => {
    vi.spyOn(HTMLElement.prototype, 'getBoundingClientRect').mockReturnValue({
      width: 960,
      height: 300,
      top: 0,
      left: 0,
      right: 960,
      bottom: 300,
      x: 0,
      y: 0,
      toJSON: () => ({}),
    });

    render(<PipelineFunnel data={mockData} />);
    // 40/50 = 80%
    expect(screen.getByText('80%')).toBeInTheDocument();
    // 30/40 = 75%
    expect(screen.getByText('75%')).toBeInTheDocument();
  });

  it('shows a neutral fallback when the comparison is invalid or exceeds 100%', () => {
    vi.spyOn(HTMLElement.prototype, 'getBoundingClientRect').mockReturnValue({
      width: 960,
      height: 300,
      top: 0,
      left: 0,
      right: 960,
      bottom: 300,
      x: 0,
      y: 0,
      toJSON: () => ({}),
    });

    render(
      <PipelineFunnel
        data={[
          { stageId: 'intake', stageName: 'New Inquiry', tripCount: 10 },
          { stageId: 'packet', stageName: 'Trip Details', tripCount: 12 },
          { stageId: 'decision', stageName: 'Ready to Quote?', tripCount: 0 },
        ]}
      />
    );

    expect(screen.getByText('—')).toBeInTheDocument();
    expect(screen.queryByText('120%')).not.toBeInTheDocument();
  });

  it('renders empty state when no data provided', () => {
    render(<PipelineFunnel data={[]} />);
    expect(screen.getByText('No pipeline data available.')).toBeInTheDocument();
  });
});
