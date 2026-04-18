import { render, screen } from '@testing-library/react';
import { PipelineFunnel } from '../PipelineFunnel';
import type { PipelineStage } from '../PipelineFunnel';
import { describe, it, expect } from 'vitest';

describe('PipelineFunnel', () => {
  const mockData: PipelineStage[] = [
    { stageId: 'intake', stageName: 'New Inquiry', tripCount: 50 },
    { stageId: 'packet', stageName: 'Trip Details', tripCount: 40 },
    { stageId: 'decision', stageName: 'Ready to Quote?', tripCount: 30 },
    { stageId: 'strategy', stageName: 'Build Options', tripCount: 20 },
    { stageId: 'safety', stageName: 'Final Review', tripCount: 10 },
  ];

  it('renders funnel title and stage names', () => {
    render(<PipelineFunnel data={mockData} />);
    expect(screen.getByText('Conversion Funnel')).toBeInTheDocument();
    expect(screen.getByText('New Inquiry')).toBeInTheDocument();
    expect(screen.getByText('Trip Details')).toBeInTheDocument();
    expect(screen.getByText('Ready to Quote?')).toBeInTheDocument();
    expect(screen.getByText('Build Options')).toBeInTheDocument();
    expect(screen.getByText('Final Review')).toBeInTheDocument();
  });

  it('renders all stage names in conversion rates section', () => {
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
    render(<PipelineFunnel data={mockData} />);
    // 40/50 = 80%
    expect(screen.getByText('80%')).toBeInTheDocument();
    // 30/40 = 75%
    expect(screen.getByText('75%')).toBeInTheDocument();
  });

  it('renders empty state when no data provided', () => {
    render(<PipelineFunnel data={[]} />);
    expect(screen.getByText('No pipeline data available.')).toBeInTheDocument();
  });
});
