import { afterEach, describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { RevenueChart } from '../RevenueChart';

const SAMPLE_DATA = [
  { month: 'Jan', inquiries: 12, booked: 8, revenue: 42000 },
  { month: 'Feb', inquiries: 15, booked: 10, revenue: 58000 },
  { month: 'Mar', inquiries: 18, booked: 12, revenue: 72000 },
];

describe('RevenueChart', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders chart title and legend labels', () => {
    vi.spyOn(HTMLElement.prototype, 'getBoundingClientRect').mockReturnValue({
      width: 960,
      height: 260,
      top: 0,
      left: 0,
      right: 960,
      bottom: 260,
      x: 0,
      y: 0,
      toJSON: () => ({}),
    });

    render(<RevenueChart data={SAMPLE_DATA} />);

    expect(screen.getByText('Monthly Trend')).toBeInTheDocument();
    expect(screen.getByText('Revenue')).toBeInTheDocument();
    expect(screen.getByText('Booked')).toBeInTheDocument();
  });

  it('renders the chart surface when data is provided', () => {
    vi.spyOn(HTMLElement.prototype, 'getBoundingClientRect').mockReturnValue({
      width: 960,
      height: 260,
      top: 0,
      left: 0,
      right: 960,
      bottom: 260,
      x: 0,
      y: 0,
      toJSON: () => ({}),
    });

    render(<RevenueChart data={SAMPLE_DATA} />);

    expect(screen.getByRole('application')).toBeInTheDocument();
  });

  it('renders an empty state when no data is provided', () => {
    render(<RevenueChart data={[]} />);

    expect(screen.getByText('Monthly Trend')).toBeInTheDocument();
    expect(screen.getByText('No revenue data available.')).toBeInTheDocument();
  });
});
