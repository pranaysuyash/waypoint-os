import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { RevenueChart } from '../RevenueChart';

const SAMPLE_DATA = [
  { month: 'Jan', inquiries: 12, booked: 8, revenue: 42000 },
  { month: 'Feb', inquiries: 15, booked: 10, revenue: 58000 },
  { month: 'Mar', inquiries: 18, booked: 12, revenue: 72000 },
];

describe('RevenueChart', () => {
  it('renders chart title and legend labels', () => {
    render(<RevenueChart data={SAMPLE_DATA} />);

    expect(screen.getByText('Monthly Trend')).toBeInTheDocument();
    expect(screen.getByText('Revenue')).toBeInTheDocument();
    expect(screen.getByText('Booked')).toBeInTheDocument();
  });

  it('renders month labels from dataset', () => {
    render(<RevenueChart data={SAMPLE_DATA} />);

    expect(screen.getByText('Jan')).toBeInTheDocument();
    expect(screen.getByText('Feb')).toBeInTheDocument();
    expect(screen.getByText('Mar')).toBeInTheDocument();
  });

  it('renders an empty state when no data is provided', () => {
    render(<RevenueChart data={[]} />);

    expect(screen.getByText('Monthly Trend')).toBeInTheDocument();
    expect(screen.getByText('No revenue data available.')).toBeInTheDocument();
  });
});
