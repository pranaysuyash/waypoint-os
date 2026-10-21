import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ClaimDispositionCard } from "../ClaimDispositionCard";
import type { Trip } from "@/lib/api-client";

function tripWithDisposition(overrides: Record<string, unknown> = {}): Trip {
  return {
    id: "T1",
    destination: "Munich",
    type: "Family",
    state: "amber",
    age: "2h",
    passenger_claim: {
      claim_id: "claim_abc",
      booking_reference: "BK-1",
      passenger_names: ["Ada Test"],
      disposition: {
        state: "SUBMITTED",
        history: [{ state: "SUBMITTED", at: "2026-09-30T10:00:00+00:00" }],
        overdue: false,
        ...overrides,
      },
    },
  } as unknown as Trip;
}

describe("ClaimDispositionCard", () => {
  it("renders nothing without a claim", () => {
    const { container } = render(<ClaimDispositionCard trip={{ id: "T1" } as unknown as Trip} />);
    expect(container.querySelector('[data-testid="claim-disposition-card"]')).toBeNull();
  });

  it("renders the current state on the parcel-tracking model", () => {
    render(<ClaimDispositionCard trip={tripWithDisposition()} />);
    expect(screen.getByTestId("claim-disposition-card")).toBeInTheDocument();
    expect(screen.getByText("Sent to airline")).toBeInTheDocument();
    expect(screen.getByText(/never moves money/i)).toBeInTheDocument();
  });

  it("shows the airline-paid outcome when recorded", () => {
    render(
      <ClaimDispositionCard
        trip={tripWithDisposition({
          state: "TRAVELER_PAID",
          outcome: { amount_eur: 400, channel: "bank_transfer", date: "2026-09-30" },
        })}
      />
    );
    expect(screen.getByText("Traveler paid")).toBeInTheDocument();
    expect(screen.getByText(/€400/)).toBeInTheDocument();
    expect(screen.getByText(/bank_transfer/)).toBeInTheDocument();
  });

  it("surfaces the follow-up nudge when the airline is overdue", () => {
    render(<ClaimDispositionCard trip={tripWithDisposition({ overdue: true })} />);
    expect(screen.getByText(/follow up/i)).toBeInTheDocument();
  });
});
