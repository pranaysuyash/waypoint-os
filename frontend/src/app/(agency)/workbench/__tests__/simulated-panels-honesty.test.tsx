// @vitest-environment jsdom

import { describe, expect, it, vi } from 'vitest';
import { render, screen, fireEvent, act } from '@testing-library/react';

const apiGet = vi.fn();
const apiPost = vi.fn();
vi.mock('@/lib/api-client', () => ({
  api: { get: apiGet, post: apiPost },
}));

/**
 * Frontend honesty batch (GM-01 / F-03 / D-08, 2026-09-02): every Gemini-wave
 * simulated panel must carry a visible honesty badge, and the five worst
 * mechanism-implying copy strings must be gone.
 */
describe('simulated panel honesty labels', () => {
  it('GDSSandboxPanel shows a simulated-sandbox badge and never claims Live offers', async () => {
    const { default: GDSSandboxPanel } = await import('../GDSSandboxPanel');

    render(<GDSSandboxPanel />);

    expect(screen.getByTestId('simulated-badge')).toHaveTextContent('Simulated sandbox');
    expect(screen.getByText(/Simulated GDS Sandbox/i)).toBeInTheDocument();
    expect(screen.queryByText(/Live GDS Sandbox/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Live Sandbox Flight Offers/i)).not.toBeInTheDocument();
  });

  it('NegotiationPanel labels supplier acceptance as simulated sample data', async () => {
    const { NegotiationPanel } = await import('../NegotiationPanel');

    render(<NegotiationPanel />);

    expect(screen.getByTestId('simulated-badge')).toHaveTextContent('Sample data');
    expect(screen.queryByText(/Accepted by Supplier ✅/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Live Multi-Round Bargaining Log/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Autonomous Session Completed/i)).not.toBeInTheDocument();
    expect(screen.getByText(/no supplier connectivity/i)).toBeInTheDocument();
  });

  it('CrisisEvacuationPanel never claims an embassy transmission', async () => {
    const { CrisisEvacuationPanel } = await import('../CrisisEvacuationPanel');

    render(<CrisisEvacuationPanel />);

    expect(screen.getByTestId('simulated-badge')).toHaveTextContent('Sample data');
    expect(screen.queryByText(/TRANSMITTED TO EMBASSY DESK/i)).not.toBeInTheDocument();
    expect(screen.getByText(/NOT TRANSMITTED/i)).toBeInTheDocument();
    // D-08: hardcoded traveler names replaced with sample defaults.
    expect(screen.queryByText(/Alex Morgan|Taylor Morgan/)).not.toBeInTheDocument();
    expect(screen.getByText(/Sample Traveler A/)).toBeInTheDocument();
  });

  it('IVRBypassPanel aligns the hold window with the simulator constant', async () => {
    const { default: IVRBypassPanel } = await import('../IVRBypassPanel');

    render(<IVRBypassPanel />);

    expect(screen.getByTestId('simulated-badge')).toHaveTextContent('Simulated');
    expect(screen.queryByText(/Est\. wait 18m/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/LIVE TELEPHONY TRANSCRIPT/i)).not.toBeInTheDocument();
    expect(screen.getByText(/TELEPHONY SIMULATOR \(NO REAL CALLS\)/i)).toBeInTheDocument();
  });

  it('FinancialSettlementPanel keeps FX, VCC, and schedules as local previews', async () => {
    const { default: FinancialSettlementPanel } = await import('../FinancialSettlementPanel');
    const fetchMock = vi.fn();
    vi.stubGlobal('fetch', fetchMock);

    render(<FinancialSettlementPanel />);

    expect(screen.getByTestId('simulated-badge')).toBeInTheDocument();
    expect(screen.getByTestId('financial-settlement-preview-notice')).toHaveTextContent(/no money is captured/i);
    expect(screen.getByText(/ARITHMETIC PREVIEW · NOT A QUOTE/i)).toBeInTheDocument();
    expect(screen.queryByText(/Issue Single-Use Merchant-Bound Virtual Card/i)).not.toBeInTheDocument();

    // Switch to the VCC tab and prove the preview never calls issuance.
    fireEvent.click(screen.getByRole('button', { name: /VCC Design Preview/i }));
    expect(screen.getByText(/does not call an issuance endpoint/i)).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /Preview Amount \(No Card\)/i }));
    expect(screen.getByTestId('vcc-preview-result')).toHaveTextContent(/NO CARD CREATED/i);
    expect(screen.getByTestId('vcc-preview-result')).toHaveTextContent(/authorization: not attempted/i);
    expect(fetchMock).not.toHaveBeenCalled();
    expect(screen.queryByText(/5424-XXXX-XXXX-8821/i)).not.toBeInTheDocument();

    // Invalid input is an explicit validation error, never a fallback success.
    fireEvent.change(screen.getByRole('spinbutton', { name: /Sample VCC amount in EUR/i }), { target: { value: '' } });
    fireEvent.click(screen.getByRole('button', { name: /Preview Amount \(No Card\)/i }));
    expect(screen.getByRole('alert')).toHaveTextContent(/Enter a positive amount/i);

    // Schedules remain timing examples, not invoices or charges.
    fireEvent.click(screen.getByRole('button', { name: /Payment Timing Preview/i }));
    expect(screen.getByText(/No invoice, payment schedule, authorization, or charge is created/i)).toBeInTheDocument();
  });

  it('MemoryArchitectPanel uses the Sample Traveler default and sample badge', async () => {
    const { MemoryArchitectPanel } = await import('../MemoryArchitectPanel');

    render(<MemoryArchitectPanel />);

    expect(screen.getByTestId('simulated-badge')).toHaveTextContent('Sample data');
    expect(screen.getAllByDisplayValue(/Sample Traveler \(cust_sample_demo\)/).length).toBeGreaterThan(0);
    expect(screen.queryByDisplayValue(/Alex Morgan/)).not.toBeInTheDocument();
  });

  it('MemorySettingsTab uses the Sample Traveler default and does not claim backend persistence', async () => {
    const { MemorySettingsTab } = await import('@/app/(agency)/settings/components/MemorySettingsTab');

    render(<MemorySettingsTab />);

    expect(screen.getByTestId('simulated-badge')).toHaveTextContent('Sample data');
    expect(screen.getByDisplayValue(/Sample Traveler \(cust_sample_demo\)/)).toBeInTheDocument();
    expect(screen.queryByDisplayValue(/Alex Morgan/)).not.toBeInTheDocument();
    expect(screen.getByText(/not persisted to the backend yet/i)).toBeInTheDocument();
  });

  it('GroupParetoPanel and DistributionPanel carry sample-data badges', async () => {
    const { default: GroupParetoPanel } = await import('../GroupParetoPanel');
    const { DistributionPanel } = await import('../DistributionPanel');

    const { unmount } = render(<GroupParetoPanel />);
    expect(screen.getByTestId('simulated-badge')).toHaveTextContent('Sample data');
    unmount();

    render(<DistributionPanel />);
    expect(screen.getByTestId('simulated-badge')).toHaveTextContent('Sample data');
    expect(screen.queryByText(/ADM Shield: Active/i)).not.toBeInTheDocument();
  });

  it('PersonaCouncilPanel header no longer claims live nominal engines', async () => {
    const { default: PersonaCouncilPanel } = await import('../PersonaCouncilPanel');

    render(<PersonaCouncilPanel />);

    expect(screen.getAllByTestId('simulated-badge').length).toBeGreaterThan(0);
    expect(screen.queryByText(/11-Persona Council Command Center/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/All 11 Engines Nominal/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Live operational controls/i)).not.toBeInTheDocument();
    expect(screen.getByText(/Demo Engines — Simulated Output/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /All Demo Engines/i })).toBeInTheDocument();
    expect(screen.getByText(/Proposal Compiler \(Simulation\)/i)).toBeInTheDocument();
    expect(screen.getByText(/Generate Sample HMAC Token/i)).toBeInTheDocument();
    expect(screen.getByDisplayValue('trip_demo_001')).toBeInTheDocument();
    expect(screen.queryByText(/All Operational Engines/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Autonomous Proposal Compiler/i)).not.toBeInTheDocument();
    expect(screen.queryByDisplayValue('trip_live_001')).not.toBeInTheDocument();
  });

  it('YieldArbitragePanel requires trip context and uses the canonical yield contract', async () => {
    const { default: YieldArbitragePanel } = await import('../YieldArbitragePanel');

    render(<YieldArbitragePanel />);
    expect(screen.getByText(/Select a trip to inspect agency-scoped yield data/i)).toBeInTheDocument();
    expect(screen.queryByText(/BKG-PARIS-882/i)).not.toBeInTheDocument();
    expect(apiGet).not.toHaveBeenCalled();

    apiGet.mockResolvedValueOnce({
      ok: true,
      trip_id: 'trip-123',
      data_sufficient: false,
      supplier_options: [],
      optimal_supplier: 'None (No Contracts Uploaded)',
      potential_margin_gain: 0,
      generated_at: '2026-09-04T00:00:00Z',
    });

    const { unmount } = render(<YieldArbitragePanel tripId="trip-123" />);
    expect(await screen.findByText(/No uploaded supplier contracts are available/i)).toBeInTheDocument();
    expect(apiGet).toHaveBeenCalledWith('/api/v1/yield/arbitrage/trip-123');
    unmount();
  });

  it('TravelerCompanionPage softens the SOS beacon into an explicitly simulated demo flow', async () => {
    vi.useFakeTimers();
    try {
      const { default: TravelerCompanionPage } = await import(
        '@/app/(traveler)/companion/page'
      );

      render(<TravelerCompanionPage />);

      // Page-level sample banner (C-01 equivalent for the companion surface).
      expect(screen.getByText(/Sample data/i)).toBeInTheDocument();

      // F-03a: the beacon must never claim a real transmission.
      expect(screen.queryByText(/TRANSMITTED ✅/i)).not.toBeInTheDocument();
      expect(screen.queryByText(/has been alerted/i)).not.toBeInTheDocument();

      // Run the demo SOS flow: the panel completes its simulated flow on a
      // 1.5s timer — advance fake timers past it, then assert the honest copy.
      fireEvent.click(screen.getByRole('button', { name: /SIMULATE SOS \(DEMO\)/i }));
      act(() => {
        vi.advanceTimersByTime(1600);
      });

      expect(
        screen.getByText(/flow simulated, nothing transmitted/i)
      ).toBeInTheDocument();
      expect(screen.getByText(/no beacon was sent/i)).toBeInTheDocument();
      expect(screen.queryByText(/TRANSMITTED ✅/i)).not.toBeInTheDocument();
    } finally {
      vi.useRealTimers();
    }
  });
});
