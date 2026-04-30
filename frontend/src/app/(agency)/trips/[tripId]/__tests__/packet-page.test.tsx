import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import PacketPage from "../packet/page";

vi.mock("@/contexts/TripContext", () => ({
  useTripContext: vi.fn(),
}));

vi.mock("@/stores/workbench", () => ({
  useWorkbenchStore: vi.fn(() => ({
    result_packet: null,
    result_validation: null,
    debug_raw_json: false,
    setDebugRawJson: vi.fn(),
  })),
}));

const { useTripContext } = await import("@/contexts/TripContext");

describe("packet page", () => {
  it("renders useful trip details for blocked planning trips without exposing raw ids or process-trip copy", () => {
    vi.mocked(useTripContext).mockReturnValue({
      tripId: "trip_4b9e0d894872",
      trip: {
        id: "trip_4b9e0d894872",
        destination: "Singapore",
        type: "family leisure",
        status: "assigned",
        state: "amber",
        party: 5,
        dateWindow: "around 9th to 14th feb",
        origin: "TBD",
        budget: "$0",
        rawInput: { fixture_id: "SC-901" },
        decision: {
          decision_state: "ASK_FOLLOWUP",
          hard_blockers: [],
          soft_blockers: ["incomplete_intake"],
        },
        validation: {
          warnings: [
            { field: "origin_city" },
            { field: "budget_raw_text" },
          ],
        },
      } as any,
      isLoading: false,
      error: null,
      refetchTrip: vi.fn(),
      replaceTrip: vi.fn(),
    });

    render(<PacketPage />);

    expect(screen.getByRole("heading", { name: "Trip Details" })).toBeInTheDocument();
    expect(screen.getByText("Known details")).toBeInTheDocument();
    expect(screen.getByText("Singapore")).toBeInTheDocument();
    expect(screen.getByText("family leisure")).toBeInTheDocument();
    expect(screen.getByText("5 pax")).toBeInTheDocument();
    expect(screen.getByText("Around Feb 9–14")).toBeInTheDocument();
    expect(screen.getByText("Budget missing")).toBeInTheDocument();
    expect(screen.getByText("Origin missing")).toBeInTheDocument();
    expect(screen.getByText("4B9E")).toBeInTheDocument();
    expect(screen.getByText("Missing required details")).toBeInTheDocument();
    expect(screen.getByText("Budget range")).toBeInTheDocument();
    expect(screen.getByText("Origin city")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Add budget" })).toHaveAttribute(
      "href",
      "/trips/trip_4b9e0d894872/intake?field=budget",
    );
    expect(screen.getByRole("link", { name: "Add origin" })).toHaveAttribute(
      "href",
      "/trips/trip_4b9e0d894872/intake?field=origin",
    );
    expect(screen.getByRole("link", { name: "Go to missing details" })).toHaveAttribute(
      "href",
      "/trips/trip_4b9e0d894872/intake",
    );
    expect(screen.queryByText(/Process a trip/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/trip_4b9e0d894872/i)).not.toBeInTheDocument();
  });
});
