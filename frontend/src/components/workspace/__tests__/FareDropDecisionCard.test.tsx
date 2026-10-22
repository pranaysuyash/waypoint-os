import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";

import { FareDropDecisionCard } from "../FareDropDecisionCard";
import type { Trip, FareDropDispositionResponse } from "@/lib/api-client";

// Mock only the two endpoint functions; types flow through untouched.
vi.mock("@/lib/api-client", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api-client")>("@/lib/api-client");
  return {
    ...actual,
    getFareDropDisposition: vi.fn(),
    updateFareDropDisposition: vi.fn(),
  };
});

import { getFareDropDisposition, updateFareDropDisposition } from "@/lib/api-client";

const mockedGet = vi.mocked(getFareDropDisposition);
const mockedUpdate = vi.mocked(updateFareDropDisposition);

// Shapes mirror the REAL backend payloads pinned by tests/test_fare_drop_disposition.py
// (Test Schema Validation rule: never mock an imagined contract).
const MARKER = "fare_drop|ABC123|100000.0|INR";

const signal = {
  checked_at: "2026-10-21T10:00:00+00:00",
  source: "ticket_price_watch_agent",
  detection_marker: MARKER,
  booking_ref: "ABC123",
  booked_price: 100000,
  booked_currency: "INR",
  current_price: 88000,
  current_currency: "INR",
  drop_amount: 12000,
  drop_percent: -12,
  threshold_percent: 5,
  severity: "medium",
  tool_evidence: [],
  authority: "Internal fare-drop watch support only. Do not purchase, reprice, contact suppliers, or send customer messages.",
};

function response(overrides: Partial<FareDropDispositionResponse> = {}): FareDropDispositionResponse {
  return {
    ok: true,
    trip_id: "trip_1",
    signal,
    disposition: { state: "DETECTED", history: [{ state: "DETECTED", at: signal.checked_at, by: "system" }], outcome: null, detection_marker: MARKER },
    options: {
      booked_price: 100000,
      current_price: 88000,
      drop_amount: 12000,
      drop_percent: 12,
      reprice: { client_saving: 12000, commission_delta: -1200 },
      upgrade: { upgrade_budget: 12000, commission_delta: 0, note: "commission preserved on recorded upgrade spend" },
      commission: { pct: 0.1, basis: "trip_recorded", source: "booking_data.commission_pct" },
      basis: "trip_recorded",
    },
    options_unavailable_reason: null,
    observations: [],
    traveler_draft: {
      status: "DRAFT_AWAITING_OPERATOR",
      subject: "Good news about your trip fare",
      body: "Hi Ada,\n\nGreat news — the fare for your trip to Dubai has come down by INR 12,000 since you booked. There are two ways you can take advantage of it…",
      channel: "unsent",
      based_on: { drop_amount: 12000, currency: "INR", detection_marker: MARKER },
    },
    ...overrides,
  };
}

function trip(overrides: Record<string, unknown> = {}): Trip {
  return { id: "trip_1", destination: "Dubai", fare_drop_signal: signal, ...overrides } as unknown as Trip;
}

describe("FareDropDecisionCard", () => {
  beforeEach(() => {
    mockedGet.mockReset();
    mockedUpdate.mockReset();
  });

  it("renders nothing when the trip has no fare-drop signal", () => {
    const { container } = render(<FareDropDecisionCard trip={{ id: "trip_1" } as unknown as Trip} />);
    expect(container.querySelector('[data-testid="fare-drop-decision-card"]')).toBeNull();
    expect(mockedGet).not.toHaveBeenCalled();
  });

  it("shows both options with real numbers and the on-file commission badge", async () => {
    mockedGet.mockResolvedValue(response());
    render(<FareDropDecisionCard trip={trip()} />);

    expect(screen.getByTestId("fare-drop-decision-card")).toBeInTheDocument();
    expect(await screen.findByTestId("fare-drop-options")).toBeInTheDocument();
    expect(screen.getByTestId("fare-drop-client-saving")).toHaveTextContent("12,000");
    expect(screen.getByTestId("fare-drop-reprice-commission")).toHaveTextContent("−");
    expect(screen.getByTestId("fare-drop-reprice-commission")).toHaveTextContent("1,200");
    expect(screen.getByTestId("fare-drop-upgrade-budget")).toHaveTextContent("12,000");
    expect(screen.getByTestId("fare-drop-basis")).toHaveTextContent("commission: on file");
    expect(screen.getByText(/never reprices or moves money/i)).toBeInTheDocument();
  });

  it("badges an estimated commission honestly", async () => {
    const res = response();
    res.options!.basis = "estimate";
    res.options!.commission = { pct: 0.1, basis: "estimate", source: "agency_default_rate" };
    mockedGet.mockResolvedValue(res);
    render(<FareDropDecisionCard trip={trip()} />);

    expect(await screen.findByTestId("fare-drop-basis")).toHaveTextContent("commission: estimate");
  });

  it("hides the numbers when the current fare could not be verified", async () => {
    mockedGet.mockResolvedValue(response({ options: null, options_unavailable_reason: "no fare drop: current_price is not below booked_price" }));
    render(<FareDropDecisionCard trip={trip()} />);

    expect(await screen.findByTestId("fare-drop-options-unavailable")).toHaveTextContent(/not below booked_price/);
    expect(screen.queryByTestId("fare-drop-options")).toBeNull();
  });

  it("offers only the legal next steps and sends a compare-and-set transition", async () => {
    mockedGet.mockResolvedValue(response());
    const presented = response({ disposition: { state: "PRESENTED", history: [], outcome: null, detection_marker: MARKER } });
    mockedUpdate.mockResolvedValue(presented);
    render(<FareDropDecisionCard trip={trip()} />);
    await screen.findByTestId("fare-drop-options");

    expect(screen.getByTestId("fare-drop-action-presented")).toBeInTheDocument();
    expect(screen.getByTestId("fare-drop-action-dismissed")).toBeInTheDocument();
    expect(screen.queryByTestId("fare-drop-action-repriced")).toBeNull();

    fireEvent.click(screen.getByTestId("fare-drop-action-presented"));

    await waitFor(() => expect(mockedUpdate).toHaveBeenCalledTimes(1));
    const [tripId, body] = mockedUpdate.mock.calls[0];
    expect(tripId).toBe("trip_1");
    expect(body.new_state).toBe("PRESENTED");
    expect(body.expected_state).toBe("DETECTED");
    expect(body.idempotency_key).toContain(MARKER);
    expect(body.outcome).toBeUndefined();
    expect(await screen.findByText("Options presented to client")).toBeInTheDocument();
  });

  it("records the refund decision with the client delta and supplier reference", async () => {
    mockedGet.mockResolvedValue(response({ disposition: { state: "PRESENTED", history: [], outcome: null, detection_marker: MARKER } }));
    mockedUpdate.mockResolvedValue(
      response({
        disposition: {
          state: "REPRICED",
          history: [],
          outcome: { option: "reprice", client_delta: -12000, supplier_reference: "RB-9", recorded_at: "2026-10-21T11:00:00+00:00" },
          detection_marker: MARKER,
        },
      }),
    );
    render(<FareDropDecisionCard trip={trip()} />);
    await screen.findByTestId("fare-drop-action-repriced");

    fireEvent.change(screen.getByTestId("fare-drop-supplier-reference"), { target: { value: "RB-9" } });
    fireEvent.click(screen.getByTestId("fare-drop-action-repriced"));

    await waitFor(() => expect(mockedUpdate).toHaveBeenCalledTimes(1));
    const body = mockedUpdate.mock.calls[0][1];
    expect(body.new_state).toBe("REPRICED");
    expect(body.expected_state).toBe("PRESENTED");
    expect(body.outcome).toMatchObject({ option: "reprice", client_delta: -12000, supplier_reference: "RB-9" });
    expect(await screen.findByTestId("fare-drop-outcome")).toHaveTextContent(/refund.*RB-9/);
  });

  it("surfaces a rejected transition as a message, not a crash", async () => {
    mockedGet.mockResolvedValue(response());
    mockedUpdate.mockRejectedValue(new Error("illegal transition: DETECTED → REPRICED"));
    render(<FareDropDecisionCard trip={trip()} />);
    await screen.findByTestId("fare-drop-options");

    fireEvent.click(screen.getByTestId("fare-drop-action-dismissed"));

    expect(await screen.findByRole("alert")).toHaveTextContent(/illegal transition/);
    expect(screen.getByTestId("fare-drop-decision-card")).toBeInTheDocument();
  });

  it("renders no actions once the ledger is closed", async () => {
    mockedGet.mockResolvedValue(response({ disposition: { state: "CLOSED", history: [], outcome: null, detection_marker: MARKER } }));
    render(<FareDropDecisionCard trip={trip()} />);

    expect(await screen.findByText("Closed")).toBeInTheDocument();
    expect(screen.queryByRole("button")).toBeNull();
    expect(screen.queryByTestId("fare-drop-draft")).toBeNull();
  });

  it("shows the draft client message as unsent and copies it on request", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.assign(navigator, { clipboard: { writeText } });
    mockedGet.mockResolvedValue(response());
    render(<FareDropDecisionCard trip={trip()} />);

    const draft = await screen.findByTestId("fare-drop-draft");
    expect(draft).toHaveTextContent(/draft, not sent/i);
    const textarea = screen.getByLabelText("Draft message to client") as HTMLTextAreaElement;
    expect(textarea.value).toContain("Great news");

    fireEvent.click(screen.getByTestId("fare-drop-copy-draft"));
    await waitFor(() => expect(writeText).toHaveBeenCalledWith(expect.stringContaining("INR 12,000")));
    expect(mockedUpdate).not.toHaveBeenCalled();
  });

  it("omits the draft when no verified options exist", async () => {
    mockedGet.mockResolvedValue(response({ options: null, traveler_draft: null, options_unavailable_reason: "no fare drop: current_price is not below booked_price" }));
    render(<FareDropDecisionCard trip={trip()} />);

    await screen.findByTestId("fare-drop-options-unavailable");
    expect(screen.queryByTestId("fare-drop-draft")).toBeNull();
  });
});
