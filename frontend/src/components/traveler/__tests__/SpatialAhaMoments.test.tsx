import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import React from 'react';
import { WedgeVisualShowcase } from '../WedgeVisualShowcase';
import { LayoverStressGauge } from '../LayoverStressGauge';
import { RouteArcRibbon } from '../RouteArcRibbon';
import { PacingExhaustionCurve } from '../PacingExhaustionCurve';
import { BeforeAfterComparison } from '../BeforeAfterComparison';
import { HiddenPerksRadar } from '../HiddenPerksRadar';
import { IsometricAirportCutaway } from '../IsometricAirportCutaway';
import { Interactive3DGlobeFlightArc } from '../Interactive3DGlobeFlightArc';
import { IsometricHotelSanctuary } from '../IsometricHotelSanctuary';

describe('Spatial & Visual Aha Moments Suite', () => {
  it('renders IsometricAirportCutaway with 2.5D axonometric projection and particle tracking', () => {
    render(<IsometricAirportCutaway />);
    expect(screen.getByText(/Axonometric Hub Cutaway & Particle Flow Simulation/i)).toBeInTheDocument();
    expect(screen.getByText(/T5A Inbound/i)).toBeInTheDocument();
    expect(screen.getByText(/T3 Connecting Gate/i)).toBeInTheDocument();
    expect(screen.getByText(/Airside APM & Security/i)).toBeInTheDocument();

    const slider = screen.getByLabelText(/Simulate runway delay on inbound flight/i);
    expect(slider).toBeInTheDocument();
    fireEvent.change(slider, { target: { value: '30' } });
    expect(screen.getByText(/\+30 minutes delay/i)).toBeInTheDocument();
    expect(screen.getByText(/GATE CLOSED/i)).toBeInTheDocument();
  });

  it('renders Interactive3DGlobeFlightArc with Great-Circle canvas and waypoints', () => {
    render(<Interactive3DGlobeFlightArc />);
    expect(screen.getByText(/Interactive Orthographic 3D Journey Telemetry/i)).toBeInTheDocument();
    expect(screen.getByText(/GEO: Transatlantic Great-Circle WGS84/i)).toBeInTheDocument();
    expect(screen.getAllByText(/JFK/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/LHR/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/CDG/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/FCO/i).length).toBeGreaterThan(0);
  });

  it('renders IsometricHotelSanctuary with suite arbitrage and wing comparison', () => {
    const onClaimMock = vi.fn();
    render(<IsometricHotelSanctuary onClaim={onClaimMock} />);
    expect(screen.getByText(/Isometric Suite Cutaway: Unlocked VIP Amenities/i)).toBeInTheDocument();
    expect(screen.getByText(/Standard Room \(35m²\)/i)).toBeInTheDocument();
    expect(screen.getByText(/Deluxe Suite \(68m²\)/i)).toBeInTheDocument();

    // Toggle view
    const suiteBtn = screen.getByText(/Waypoint Suite Only/i);
    fireEvent.click(suiteBtn);

    // Click claim suite upgrades
    const claimBtn = screen.getByText(/Claim Suite Upgrades →/i);
    fireEvent.click(claimBtn);
    expect(onClaimMock).toHaveBeenCalledTimes(1);
  });

  it('renders WedgeVisualShowcase with seamless tab navigation across 2.5D, 3D, and planar views', () => {
    render(<WedgeVisualShowcase />);

    // Default: Connection Stress
    expect(screen.getByText(/Connection Stress & Minimum Buffer Gauge/i)).toBeInTheDocument();

    // 2.5D Airport Cutaway tab
    const airportTab = screen.getByRole('button', { name: /2.5D Airport Cutaway/i });
    fireEvent.click(airportTab);
    expect(screen.getByText(/Axonometric Hub Cutaway & Particle Flow Simulation/i)).toBeInTheDocument();

    // 3D Globe Flight Arc tab
    const globeTab = screen.getByRole('button', { name: /3D Globe Flight Arc/i });
    fireEvent.click(globeTab);
    expect(screen.getByText(/Interactive Orthographic 3D Journey Telemetry/i)).toBeInTheDocument();

    // 2.5D Suite Cutaway tab
    const hotelTab = screen.getByRole('button', { name: /2.5D Suite Cutaway/i });
    fireEvent.click(hotelTab);
    expect(screen.getByText(/Isometric Suite Cutaway: Unlocked VIP Amenities/i)).toBeInTheDocument();
  });
});
