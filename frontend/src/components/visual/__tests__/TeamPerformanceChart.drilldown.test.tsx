import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { TeamPerformanceChart } from '../TeamPerformanceChart';
import type { TeamMember } from '../TeamPerformanceChart';
import { describe, it, expect, vi } from 'vitest';

describe('TeamPerformanceChart Drill-Down', () => {
  const mockTeamData: TeamMember[] = [
    {
      userId: 'agent-1',
      name: 'Sarah Chen',
      conversionRate: 72,
      avgResponseTime: 3.2,
      customerSatisfaction: 4.8,
      workloadScore: 75,
    },
    {
      userId: 'agent-2',
      name: 'Mike Johnson',
      conversionRate: 68,
      avgResponseTime: 5.1,
      customerSatisfaction: 4.5,
      workloadScore: 92,
    },
  ];

  it('renders drill-down hint when onDrillDown is provided', () => {
    const mockDrillDown = vi.fn();
    render(<TeamPerformanceChart data={mockTeamData} onDrillDown={mockDrillDown} />);
    
    expect(screen.getByText(/Click on any metric to drill down/i)).toBeInTheDocument();
  });

  it('does not render drill-down hint when onDrillDown is not provided', () => {
    render(<TeamPerformanceChart data={mockTeamData} />);
    
    expect(screen.queryByText(/Click on any metric to drill down/i)).not.toBeInTheDocument();
  });

  it('calls onDrillDown when conversion rate metric is clicked', () => {
    const mockDrillDown = vi.fn();
    render(<TeamPerformanceChart data={mockTeamData} onDrillDown={mockDrillDown} />);
    
    const conversionElement = screen.getByText('72%');
    fireEvent.click(conversionElement);
    
    expect(mockDrillDown).toHaveBeenCalledWith('agent-1', {
      type: 'conversion',
      value: 72,
      label: 'Conversion Rate',
    });
  });

  it('calls onDrillDown when response time metric is clicked', () => {
    const mockDrillDown = vi.fn();
    render(<TeamPerformanceChart data={mockTeamData} onDrillDown={mockDrillDown} />);
    
    const responseTimeElements = screen.getAllByText('3.2h');
    fireEvent.click(responseTimeElements[0]);
    
    expect(mockDrillDown).toHaveBeenCalledWith('agent-1', {
      type: 'response_time',
      value: 3.2,
      label: 'Response Time',
    });
  });

  it('calls onDrillDown when CSAT metric is clicked', () => {
    const mockDrillDown = vi.fn();
    render(<TeamPerformanceChart data={mockTeamData} onDrillDown={mockDrillDown} />);
    
    const csatElements = screen.getAllByText('4.8/5');
    fireEvent.click(csatElements[0]);
    
    expect(mockDrillDown).toHaveBeenCalledWith('agent-1', {
      type: 'csat',
      value: 4.8,
      label: 'Customer Satisfaction',
    });
  });

  it('calls onDrillDown when workload metric is clicked', () => {
    const mockDrillDown = vi.fn();
    render(<TeamPerformanceChart data={mockTeamData} onDrillDown={mockDrillDown} />);
    
    const workloadElements = screen.getAllByText('75%');
    fireEvent.click(workloadElements[0]);
    
    expect(mockDrillDown).toHaveBeenCalledWith('agent-1', {
      type: 'workload',
      value: 75,
      label: 'Workload',
    });
  });

  it('highlights selected agent card when drill-down is triggered', () => {
    const mockDrillDown = vi.fn();
    const { container } = render(<TeamPerformanceChart data={mockTeamData} onDrillDown={mockDrillDown} />);
    
    const conversionElement = screen.getByText('72%');
    fireEvent.click(conversionElement);
    
    const agentCards = container.querySelectorAll('[class*="border-[#58a6ff]"]');
    expect(agentCards.length).toBeGreaterThan(0);
  });

  it('has cursor-pointer class on metrics when drill-down is enabled', () => {
    const mockDrillDown = vi.fn();
    const { container } = render(<TeamPerformanceChart data={mockTeamData} onDrillDown={mockDrillDown} />);
    
    const clickableMetrics = container.querySelectorAll('[class*="cursor-pointer"]');
    expect(clickableMetrics.length).toBeGreaterThan(0);
  });

  it('does not have cursor-pointer when drill-down is disabled', () => {
    const { container } = render(<TeamPerformanceChart data={mockTeamData} />);
    
    const clickableMetrics = container.querySelectorAll('[class*="cursor-pointer"]');
    expect(clickableMetrics.length).toBe(0);
  });

  it('does not call onDrillDown if agent has no userId', () => {
    const mockDrillDown = vi.fn();
    const dataWithoutUserId: TeamMember[] = [
      {
        name: 'Agent Without ID',
        conversionRate: 72,
        avgResponseTime: 3.2,
        customerSatisfaction: 4.8,
        workloadScore: 75,
      },
    ];
    
    render(<TeamPerformanceChart data={dataWithoutUserId} onDrillDown={mockDrillDown} />);
    
    const conversionElement = screen.getByText('72%');
    fireEvent.click(conversionElement);
    
    expect(mockDrillDown).not.toHaveBeenCalled();
  });
});
