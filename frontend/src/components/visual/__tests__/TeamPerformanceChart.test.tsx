import { render, screen } from '@testing-library/react';
import { TeamPerformanceChart } from '../TeamPerformanceChart';
import type { TeamMember } from '../TeamPerformanceChart';
import { describe, it, expect } from 'vitest';

describe('TeamPerformanceChart', () => {
  const mockTeamData: TeamMember[] = [
    {
      name: 'Sarah Chen',
      conversionRate: 72,
      avgResponseTime: 3.2,
      customerSatisfaction: 4.8,
      workloadScore: 75,
    },
    {
      name: 'Mike Johnson',
      conversionRate: 68,
      avgResponseTime: 5.1,
      customerSatisfaction: 4.5,
      workloadScore: 92,
    },
    {
      name: 'Alex Kim',
      conversionRate: 74,
      avgResponseTime: 2.8,
      customerSatisfaction: 4.9,
      workloadScore: 55,
    },
  ];

  it('renders chart title and agent names', () => {
    render(<TeamPerformanceChart data={mockTeamData} />);
    expect(screen.getByText('Agent Performance Metrics')).toBeInTheDocument();
    expect(screen.getByText('Sarah Chen')).toBeInTheDocument();
    expect(screen.getByText('Mike Johnson')).toBeInTheDocument();
    expect(screen.getByText('Alex Kim')).toBeInTheDocument();
  });

  it('renders legend with metric labels', () => {
    render(<TeamPerformanceChart data={mockTeamData} />);
    // Check for legend label text that appears only in legend
    expect(screen.getByText('↑ Higher is better')).toBeInTheDocument(); // Conversion Rate legend
    expect(screen.getByText('↓ Lower is better')).toBeInTheDocument(); // Response Time or Workload legend
    expect(screen.getByText('↑ Out of 5.0')).toBeInTheDocument(); // CSAT legend
  });

  it('renders metric values in performance summary', () => {
    render(<TeamPerformanceChart data={mockTeamData} />);
    // Check for conversion rate values
    expect(screen.getByText('72%')).toBeInTheDocument();
    expect(screen.getByText('68%')).toBeInTheDocument();
    expect(screen.getByText('74%')).toBeInTheDocument();
  });

  it('renders empty state when no data provided', () => {
    render(<TeamPerformanceChart data={[]} />);
    expect(screen.getByText('No team data available.')).toBeInTheDocument();
  });
});
