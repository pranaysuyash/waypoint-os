// @vitest-environment jsdom

import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

/**
 * D-08 contract (2026-09-04): the sibling memory/crisis surfaces are
 * client-local previews. A badge is necessary but not sufficient; actions,
 * statuses, and hidden subviews must not imply a live write, verification,
 * dispatch, slot, or compliance result.
 */
describe('D-08 sibling sample-panel boundaries', () => {
  it('contains MemoryArchitectPanel writes, search, freshness, and erasure claims', async () => {
    const { MemoryArchitectPanel } = await import('../MemoryArchitectPanel');

    render(<MemoryArchitectPanel />);

    expect(screen.getByTestId('simulated-badge')).toHaveTextContent('Sample data');
    expect(screen.getByText(/Preference Intake Preview/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Preview Ingest \(No Save\)/i })).toBeInTheDocument();
    expect(screen.queryByText(/Verified Preference Intake|Auto-Curation Active|Save to Traveler Profile/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/One-Click Compliance|Automatically included in new trip proposals|Permanently purges/i)).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /Preview Erasure \(No Deletion\)/i }));
    expect(screen.getByText(/no records were purged/i)).toBeInTheDocument();
    expect(screen.getByText(/Nothing was erased in this demo/i)).toBeInTheDocument();
  });

  it('contains MemorySettingsTab persistence and compliance claims', async () => {
    const { MemorySettingsTab } = await import('@/app/(agency)/settings/components/MemorySettingsTab');

    render(<MemorySettingsTab />);

    expect(screen.getByTestId('simulated-badge')).toHaveTextContent('Sample data');
    expect(screen.getByText(/not persisted to the backend yet/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Preview Retention Rules/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Preview Erasure \(No Deletion\)/i })).toBeInTheDocument();
    expect(screen.queryByText(/Compliance Enforced|Purge Customer Records|permanently wiped/i)).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /Preview Retention Rules/i }));
    expect(screen.getByRole('button', { name: /Preview saved locally \(no backend\)/i })).toBeInTheDocument();
  });

  it('contains CrisisEvacuationPanel dispatch, slot, beacon, and embassy claims in every view', async () => {
    const { CrisisEvacuationPanel } = await import('../CrisisEvacuationPanel');

    render(<CrisisEvacuationPanel />);

    expect(screen.getByTestId('simulated-badge')).toHaveTextContent('Sample data');
    expect(screen.getByText(/Sample Incident \(Not a Live Feed\)/i)).toBeInTheDocument();
    expect(screen.queryByText(/Live Ground Driver Dispatch|Verified Safe Zone|Slot Guaranteed|TRANSMITTED TO EMBASSY DESK|GPS Verified/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/^(DISPATCHED|TICKETED|CONFIRMED)$/i)).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /Multi-Modal Escape Routing \(Sample\)/i }));
    expect(screen.getByText(/Sample Evacuation Itinerary Preview/i)).toBeInTheDocument();
    expect(screen.getByText(/Sample status: CANDIDATE PLAN \(SIMULATED\)/i)).toBeInTheDocument();
    expect(screen.getByText(/Sample status: PROVIDER STATUS UNKNOWN \(SIMULATED\)/i)).toBeInTheDocument();
    expect(screen.queryByText(/^(DISPATCHED|TICKETED|CONFIRMED)$/i)).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /Ground Dispatch Draft \(Sample\)/i }));
    expect(screen.getByText(/Sample driver \(no provider assignment\)/i)).toBeInTheDocument();
    expect(screen.getByText(/nothing was sent/i)).toBeInTheDocument();
    expect(screen.queryByText(/Marcus Vance|\+81-90-555-0192|品川 300 84-92|EN ROUTE TO SHELTER/i)).not.toBeInTheDocument();
  });
});
