import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import React from 'react';
import { WedgeVisualShowcase } from '../WedgeVisualShowcase';
import { LayoverStressGauge } from '../LayoverStressGauge';
import { RouteArcRibbon } from '../RouteArcRibbon';
import { PacingExhaustionCurve } from '../PacingExhaustionCurve';
import { BeforeAfterComparison } from '../BeforeAfterComparison';
import { HiddenPerksRadar } from '../HiddenPerksRadar';

describe('Wedge Visual Aha Moments Components', () => {
  it('renders LayoverStressGauge with friction breakdown and simulator', () => {
    render(<LayoverStressGauge />);
    expect(screen.getByText(/Connection Stress & Minimum Buffer Gauge/i)).toBeInTheDocument();
    expect(screen.getByText('London Heathrow (LHR)')).toBeInTheDocument();
    expect(screen.getByText(/Taxi & Deplane/i)).toBeInTheDocument();

    const slider = screen.getByLabelText(/Simulate inbound flight delay/i);
    expect(slider).toBeInTheDocument();
    fireEvent.change(slider, { target: { value: '30' } });
    expect(screen.getByText(/\+30 minutes delay/i)).toBeInTheDocument();
  });

  it('renders RouteArcRibbon with stops and interactive legs', () => {
    render(<RouteArcRibbon />);
    expect(screen.getByText(/Multi-Destination Route Flow & Transfer Arcs/i)).toBeInTheDocument();
    expect(screen.getByText('JFK')).toBeInTheDocument();
    expect(screen.getByText('LHR')).toBeInTheDocument();
    expect(screen.getByText('CDG')).toBeInTheDocument();
    expect(screen.getByText('FCO')).toBeInTheDocument();

    // Click on flight duration badge
    const legButton = screen.getByText('7h 10m');
    fireEvent.click(legButton);
    expect(screen.getByText(/Selected Segment: New York \(JFK\) → London \(LHR\)/i)).toBeInTheDocument();
  });

  it('renders PacingExhaustionCurve with burnout ceiling and day points', () => {
    render(<PacingExhaustionCurve hasElderlyOrKids={true} />);
    expect(screen.getByText(/Day-by-day pacing comparison/i)).toBeInTheDocument();
    expect(screen.getByText(/Multi-gen pace threshold/i)).toBeInTheDocument();
    expect(screen.getByText(/High-load threshold \(70%\)/i)).toBeInTheDocument();

    // Keyboard activation should expose the same day breakdown as a click.
    const day2 = screen.getByRole('button', { name: /Day 2: Paris Highlights/ });
    fireEvent.keyDown(day2, { key: 'Enter' });
    expect(day2).toHaveAttribute('aria-pressed', 'true');
    expect(screen.getByText(/Paris Highlights/i)).toBeInTheDocument();
  });

  it('draws a day at the threshold on the threshold line and handles an empty schedule', () => {
    const { rerender } = render(<PacingExhaustionCurve days={[{
      dayNumber: 1, label: 'City walk', activitiesCount: 3, estimatedSteps: 8000,
      standingHours: 3, exhaustionScore: 70, notes: 'Leave time for lunch.',
    }]} />);
    const day = screen.getByRole('button', { name: 'Day 1: City walk', pressed: true });
    const threshold = screen.getByText('High-load threshold', { selector: 'title' }).parentElement;
    expect(day.querySelector('circle')).toHaveAttribute('cy', threshold?.getAttribute('y1'));

    rerender(<PacingExhaustionCurve days={[]} />);
    expect(screen.getByText('No daily activities are available for this comparison.')).toBeInTheDocument();
  });

  it('renders BeforeAfterComparison with toggle between views', () => {
    render(<BeforeAfterComparison />);
    expect(screen.getByText(/Before vs. After: What Professional Advisory Changes/i)).toBeInTheDocument();
    expect(screen.getAllByText(/Your Raw Plan/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/Protected Connection/i)).toBeInTheDocument();

    // Toggle to 'Raw DIY Only'
    const rawBtn = screen.getByText('Raw DIY Only');
    fireEvent.click(rawBtn);
    expect(screen.queryByText(/Protected Connection/i)).not.toBeInTheDocument();
  });

  it('renders HiddenPerksRadar with amenity tally and property switching', () => {
    const onClaimMock = vi.fn();
    render(<HiddenPerksRadar onClaimPerks={onClaimMock} />);
    expect(screen.getByText(/Unclaimed Luxury Perks & Amenities Value/i)).toBeInTheDocument();
    expect(screen.getAllByText(/The Ritz Paris/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/Daily American Breakfast for Two/i)).toBeInTheDocument();

    // Switch to Hotel de Russie
    const russieTab = screen.getByText(/Hotel de Russie/i);
    fireEvent.click(russieTab);
    expect(screen.getByText(/Le Jardin de Russie/i)).toBeInTheDocument();

    // Click claim perks
    const claimBtn = screen.getByText(/Claim My Amenities →/i);
    fireEvent.click(claimBtn);
    expect(onClaimMock).toHaveBeenCalledTimes(1);
  });

  it('renders WedgeVisualShowcase with seamless tab switching between all 5 visual moments', () => {
    render(<WedgeVisualShowcase />);

    // Default tab is Connection Stress
    expect(screen.getByText(/Connection Stress & Minimum Buffer Gauge/i)).toBeInTheDocument();

    const currentTab = screen.getByRole('tab', { selected: true });
    expect(currentTab).toHaveAccessibleName(/Connection Stress/);
    fireEvent.keyDown(currentTab, { key: 'End' });
    const lastTab = screen.getByRole('tab', { selected: true });
    expect(lastTab).toHaveAccessibleName(/Hotel Perks Check/);
    expect(lastTab).toHaveFocus();
    expect(screen.getByRole('tabpanel', { name: /Hotel Perks Check/ })).toHaveAttribute('id', lastTab.getAttribute('aria-controls'));
    fireEvent.keyDown(lastTab, { key: 'ArrowRight' });
    expect(currentTab).toHaveFocus();
    expect(currentTab).toHaveAttribute('aria-selected', 'true');

    const routeTab = screen.getByRole('tab', { name: /Stop Sequence/i });
    fireEvent.click(routeTab);
    expect(screen.getByText(/Multi-Destination Route Flow & Transfer Arcs/i)).toBeInTheDocument();

    // Switch to Pacing Curve
    const pacingTab = screen.getByRole('tab', { name: /Daily Pacing/i });
    fireEvent.click(pacingTab);
    expect(screen.getByText(/Day-by-day pacing comparison/i)).toBeInTheDocument();

    // Switch to Before vs After
    const comparisonTab = screen.getByRole('tab', { name: /Before vs. After/i });
    fireEvent.click(comparisonTab);
    expect(screen.getByText(/Before vs. After: What Professional Advisory Changes/i)).toBeInTheDocument();

    // Switch to Perks Radar
    const perksTab = screen.getByRole('tab', { name: /Hotel Perks Check/i });
    fireEvent.click(perksTab);
    expect(screen.getByText(/Unclaimed Luxury Perks & Amenities Value/i)).toBeInTheDocument();
  });
});
