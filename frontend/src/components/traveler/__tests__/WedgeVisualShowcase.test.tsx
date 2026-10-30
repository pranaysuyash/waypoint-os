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
    expect(screen.getByText(/London Heathrow \(LHR\)/i)).toBeInTheDocument();
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
    expect(screen.getByText(/Day-by-Day Pacing & Exhaustion Curve/i)).toBeInTheDocument();
    expect(screen.getByText(/Elderly \/ Multi-Gen Pace Threshold/i)).toBeInTheDocument();
    expect(screen.getByText(/Burnout Ceiling/i)).toBeInTheDocument();

    // Click on Day 2 point
    const day2 = screen.getByText('Day 2');
    fireEvent.click(day2);
    expect(screen.getByText(/Paris Highlights/i)).toBeInTheDocument();
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

    // Switch to Route Arc Ribbon
    const routeTab = screen.getByRole('button', { name: /Route Arc Ribbon/i });
    fireEvent.click(routeTab);
    expect(screen.getByText(/Multi-Destination Route Flow & Transfer Arcs/i)).toBeInTheDocument();

    // Switch to Pacing Curve
    const pacingTab = screen.getByRole('button', { name: /Pacing Curve/i });
    fireEvent.click(pacingTab);
    expect(screen.getByText(/Day-by-Day Pacing & Exhaustion Curve/i)).toBeInTheDocument();

    // Switch to Before vs After
    const comparisonTab = screen.getByRole('button', { name: /Before vs. After/i });
    fireEvent.click(comparisonTab);
    expect(screen.getByText(/Before vs. After: What Professional Advisory Changes/i)).toBeInTheDocument();

    // Switch to Perks Radar
    const perksTab = screen.getByRole('button', { name: /Perks Radar/i });
    fireEvent.click(perksTab);
    expect(screen.getByText(/Unclaimed Luxury Perks & Amenities Value/i)).toBeInTheDocument();
  });
});
