/**
 * P1 Integration Assertion: Mode selector sends correct operating_mode payload to /api/spine/run
 *
 * This test locks the coupling between the IntakePanel mode selector and the
 * spine-client request, ensuring operating_mode is always correctly propagated.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import { IntakePanel } from "@/components/workspace/panels/IntakePanel";
import type { Trip } from "@/lib/api-client";
import type { OperatingMode } from "@/types/spine";

const mockStore: Record<string, any> = {
  input_raw_note: "Test trip for Singapore, 2 adults, budget 1L",
  input_owner_note: "",
  input_structured_json: "",
  input_itinerary_text: "",
  stage: "discovery",
  operating_mode: "normal_intake",
  strict_leakage: false,
  scenario_id: "",
  debug_raw_json: false,
  result_decision: null,
};

const storeSetters: Record<string, ReturnType<typeof vi.fn>> = {
  setInputRawNote: vi.fn(),
  setInputOwnerNote: vi.fn(),
  setStage: vi.fn(),
  setOperatingMode: vi.fn(),
  setScenarioId: vi.fn(),
  setStrictLeakage: vi.fn(),
  setDebugRawJson: vi.fn(),
  setResultPacket: vi.fn(),
  setResultValidation: vi.fn(),
  setResultDecision: vi.fn(),
  setResultStrategy: vi.fn(),
  setResultInternalBundle: vi.fn(),
  setResultTravelerBundle: vi.fn(),
  setResultSafety: vi.fn(),
  setResultFees: vi.fn(),
  setResultRunTs: vi.fn(),
};

vi.mock("@/stores/workbench", () => ({
  useWorkbenchStore: () => ({
    ...mockStore,
    ...storeSetters,
  }),
}));

const executeMock = vi.fn().mockResolvedValue({
  ok: true,
  run_id: "run-test-001",
  packet: {},
  validation: null,
  decision: { decision_state: "PROCEED_TRAVELER_SAFE" },
  strategy: null,
  internal_bundle: null,
  traveler_bundle: null,
  safety: { leakage_passed: true },
  fees: null,
});

vi.mock("@/hooks/useSpineRun", () => ({
  useSpineRun: () => ({
    execute: executeMock,
    isLoading: false,
    error: null,
    reset: vi.fn(),
    data: null,
  }),
}));

vi.mock("@/hooks/useTrips", () => ({
  useTrips: () => ({
    data: [],
    total: 0,
    isLoading: false,
    error: null,
    refetch: vi.fn(),
  }),
  useUpdateTrip: () => ({
    mutate: vi.fn().mockResolvedValue({}),
    isSaving: false,
    error: null,
  }),
}));

vi.mock("@/hooks/useFieldAuditLog", () => ({
  useFieldAuditLog: () => ({
    logChange: vi.fn(),
    getLatestChangeForField: vi.fn(),
  }),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn(), prefetch: vi.fn(), back: vi.fn() }),
  useSearchParams: () => ({ get: vi.fn(), getAll: vi.fn(), toString: vi.fn() }),
  usePathname: () => "/",
}));

vi.mock("@/lib/currency", () => ({
  CURRENCY_CONFIG: { INR: { symbol: "₹", code: "INR", name: "Indian Rupee" } },
  formatMoney: (a: number) => `₹${a}`,
  formatMoneyCompact: (a: number) => `₹${a}`,
  parseBudgetString: () => ({ amount: 100000, currency: "INR" }),
  getCurrencyOptions: () => [{ value: "INR", label: "INR", flag: "🇮🇳" }],
}));

vi.mock("@/lib/combobox", () => ({
  TRIP_TYPE_OPTIONS: [{ value: "Leisure", label: "Leisure" }],
  DESTINATION_OPTIONS: [{ value: "Singapore", label: "Singapore" }],
}));

vi.mock("@/lib/routes", () => ({
  getTripRoute: (id: string, tab: string) => `/workspace/${id}/${tab}`,
}));

describe("Mode Selector → /api/spine/run Payload Integration", () => {
  const mockTrip: Trip = {
    id: "TRIP-MODE-001",
    destination: "Singapore",
    type: "Leisure",
    state: "green",
    age: "0d",
    dateWindow: "June 2026",
    party: 2,
    budget: "₹100000",
    createdAt: "2026-04-23T08:00:00.000Z",
    updatedAt: "2026-04-23T08:15:00.000Z",
  };

  beforeEach(() => {
    vi.clearAllMocks();
    mockStore.operating_mode = "normal_intake";
    mockStore.stage = "discovery";
    executeMock.mockResolvedValue({
      ok: true,
      run_id: "run-test-001",
      packet: {},
      decision: { decision_state: "PROCEED_TRAVELER_SAFE" },
      safety: { leakage_passed: true },
    });
  });

  const modes: { value: OperatingMode; label: string }[] = [
    { value: "normal_intake", label: "New Request" },
    { value: "audit", label: "Audit" },
    { value: "emergency", label: "Emergency" },
    { value: "follow_up", label: "Follow Up" },
    { value: "cancellation", label: "Cancellation" },
    { value: "post_trip", label: "Post Trip" },
  ];

  it("sends normal_intake operating_mode in spine payload by default", async () => {
    render(<IntakePanel tripId="TRIP-MODE-001" trip={mockTrip} />);

    const processButton = screen.getByRole("button", { name: /Process Trip/i });
    fireEvent.click(processButton);

    await waitFor(() => {
      expect(executeMock).toHaveBeenCalledTimes(1);
    });

    const payload = executeMock.mock.calls[0][0];
    expect(payload.operating_mode).toBe("normal_intake");
    expect(payload.stage).toBe("discovery");
    expect(payload.raw_note).toBe("Test trip for Singapore, 2 adults, budget 1L");
  });

  it.each(modes.map((m) => [m.value, m.label]))(
    "sends correct operating_mode=%s when '%s' is selected",
    async (mode, label) => {
      mockStore.operating_mode = mode;

      render(<IntakePanel tripId="TRIP-MODE-001" trip={mockTrip} />);

      const processButton = screen.getByRole("button", { name: /Process Trip/i });
      fireEvent.click(processButton);

      await waitFor(() => {
        expect(executeMock).toHaveBeenCalledTimes(1);
      });

      const payload = executeMock.mock.calls[0][0];
      expect(payload.operating_mode).toBe(mode);
    }
  );

  it("calls setOperatingMode when mode selector changes", () => {
    render(<IntakePanel tripId="TRIP-MODE-001" trip={mockTrip} />);

    const modeSelect = screen.getByDisplayValue("New Request");
    fireEvent.change(modeSelect, { target: { value: "emergency" } });

    expect(storeSetters.setOperatingMode).toHaveBeenCalledWith("emergency");
  });

  it("includes strict_leakage flag in the spine payload", async () => {
    mockStore.strict_leakage = true;

    render(<IntakePanel tripId="TRIP-MODE-001" trip={mockTrip} />);

    const processButton = screen.getByRole("button", { name: /Process Trip/i });
    fireEvent.click(processButton);

    await waitFor(() => {
      expect(executeMock).toHaveBeenCalledTimes(1);
    });

    const payload = executeMock.mock.calls[0][0];
    expect(payload.strict_leakage).toBe(true);
  });

  it("sends stage from store config in the payload", async () => {
    mockStore.stage = "proposal";

    render(<IntakePanel tripId="TRIP-MODE-001" trip={mockTrip} />);

    const processButton = screen.getByRole("button", { name: /Process Trip/i });
    fireEvent.click(processButton);

    await waitFor(() => {
      expect(executeMock).toHaveBeenCalledTimes(1);
    });

    const payload = executeMock.mock.calls[0][0];
    expect(payload.stage).toBe("proposal");
  });
});
