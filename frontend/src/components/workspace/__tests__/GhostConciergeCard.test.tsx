import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { GhostConciergeCard } from "../GhostConciergeCard";
import type { Trip } from "@/lib/api-client";

function tripWithGc(gc: Record<string, unknown> | undefined): Trip {
  return { id: "T1", destination: "Munich", type: "Family", state: "red", age: "1h", ghost_concierge: gc } as unknown as Trip;
}

const disrupted = {
  overall_health: "DISRUPTED",
  evaluated_at: "2026-09-30T12:00:00+00:00",
  drafted_interventions: [
    { action_type: "DRAFT_EU261_CLAIM", severity: "INFO", summary: "Cancellation may qualify for statutory compensation.", status: "DRAFT_AWAITING_OPERATOR" },
    { action_type: "SEARCH_FALLBACK_FLIGHTS", severity: "CRITICAL", summary: "Flight XY123 has been CANCELLED.", recommended_action: "Hold alternative seats on next codeshare.", status: "DRAFT_AWAITING_OPERATOR" },
  ],
  healer_note: "healer not chained: trip has no stored journey graph",
};

describe("GhostConciergeCard", () => {
  it("renders nothing for a stable/unevaluated trip", () => {
    const { container } = render(<GhostConciergeCard trip={tripWithGc(undefined)} />);
    expect(container.querySelector('[data-testid="ghost-concierge-card"]')).toBeNull();
    const { container: c2 } = render(<GhostConciergeCard trip={tripWithGc({ overall_health: "STABLE" })} />);
    expect(c2.querySelector('[data-testid="ghost-concierge-card"]')).toBeNull();
  });

  it("renders critical-first interventions and the operator-gate note", () => {
    render(<GhostConciergeCard trip={tripWithGc(disrupted)} />);
    expect(screen.getByTestId("ghost-concierge-card")).toBeInTheDocument();
    expect(screen.getByText(/Disruption detected/)).toBeInTheDocument();
    // CRITICAL sorts before INFO regardless of input order
    const items = screen.getAllByRole("listitem");
    expect(items[0].textContent).toContain("CANCELLED");
    expect(screen.getByText(/nothing is sent automatically/i)).toBeInTheDocument();
    expect(screen.getByText(/no stored journey graph/)).toBeInTheDocument();
  });
});
