import { describe, it, expect, vi, beforeEach } from "vitest";
import React from "react";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import { ReviewControls } from "../ReviewControls";
import type { Trip } from "@/lib/api-client";

// Mock the workbench store
const mockStoreState = {
  acknowledged_suitability_flags: new Set<string>(),
};

vi.mock("@/stores/workbench", () => ({
  useWorkbenchStore: () => mockStoreState,
}));

// Mock the API client
vi.mock("@/lib/api-client", () => ({
  submitTripReviewAction: vi.fn(),
}));

function buildTrip(overrides: Partial<Trip> = {}): Trip {
  return {
    id: "trip-123",
    destination: "Tokyo",
    type: "leisure",
    state: "amber",
    age: "new",
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    review_status: "pending",
    ...overrides,
  };
}

describe("ReviewControls - suitability gate", () => {
  beforeEach(() => {
    mockStoreState.acknowledged_suitability_flags = new Set<string>();
  });

  it("enables Approve button when no suitability flags exist", () => {
    const trip = buildTrip({ decision: { decision_state: "PROCEED_TRAVELER_SAFE" } as any });
    render(<ReviewControls trip={trip} />);
    expect(screen.getByTestId("approve-button")).not.toBeDisabled();
  });

  it("enables Approve button when decision_state is not suitability_review_required", () => {
    const trip = buildTrip({
      decision: {
        decision_state: "PROCEED_TRAVELER_SAFE",
        suitability_flags: [{ flag_type: "toddler_water_unsafe", severity: "critical", confidence: 0.9, reason: "Unsafe" }],
      } as any,
    });
    render(<ReviewControls trip={trip} />);
    expect(screen.getByTestId("approve-button")).not.toBeDisabled();
  });

  it("blocks Approve when suitability_review_required and critical flags unacknowledged", () => {
    const trip = buildTrip({
      decision: {
        decision_state: "suitability_review_required",
        suitability_flags: [
          { flag_type: "toddler_water_unsafe", severity: "critical", confidence: 0.95, reason: "Unsafe" },
        ],
      } as any,
    });
    render(<ReviewControls trip={trip} />);
    const approveBtn = screen.getByTestId("approve-button");
    expect(approveBtn).toBeDisabled();
    expect(screen.getByText(/Approval blocked/)).toBeInTheDocument();
  });

  it("unblocks Approve when all critical flags are acknowledged", () => {
    mockStoreState.acknowledged_suitability_flags = new Set(["toddler_water_unsafe"]);
    const trip = buildTrip({
      decision: {
        decision_state: "suitability_review_required",
        suitability_flags: [
          { flag_type: "toddler_water_unsafe", severity: "critical", confidence: 0.95, reason: "Unsafe" },
        ],
      } as any,
    });
    render(<ReviewControls trip={trip} />);
    expect(screen.getByTestId("approve-button")).not.toBeDisabled();
    expect(screen.queryByText(/Approval blocked/)).not.toBeInTheDocument();
  });

  it("blocks when some critical flags remain unacknowledged", () => {
    mockStoreState.acknowledged_suitability_flags = new Set(["toddler_water_unsafe"]);
    const trip = buildTrip({
      decision: {
        decision_state: "suitability_review_required",
        suitability_flags: [
          { flag_type: "toddler_water_unsafe", severity: "critical", confidence: 0.95, reason: "Unsafe" },
          { flag_type: "elderly_intense", severity: "critical", confidence: 0.9, reason: "Intense" },
        ],
      } as any,
    });
    render(<ReviewControls trip={trip} />);
    expect(screen.getByTestId("approve-button")).toBeDisabled();
  });

  it("does not block on non-critical (high) flags", () => {
    const trip = buildTrip({
      decision: {
        decision_state: "suitability_review_required",
        suitability_flags: [
          { flag_type: "elderly_intense", severity: "high", confidence: 0.85, reason: "Intense" },
        ],
      } as any,
    });
    render(<ReviewControls trip={trip} />);
    expect(screen.getByTestId("approve-button")).not.toBeDisabled();
  });
});
