import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { TimelineSummary } from "../TimelineSummary";

describe("TimelineSummary", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("uses stage-not-set copy instead of unknown for unset timeline stage", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        trip_id: "TRIP-123",
        events: [
          {
            trip_id: "TRIP-123",
            timestamp: "2026-04-18T10:00:00Z",
            stage: "unknown",
            status: "completed",
            state_snapshot: {},
          },
        ],
      }),
    }) as any;

    render(<TimelineSummary tripId="TRIP-123" />);

    expect(await screen.findByText("Stage not set")).toBeInTheDocument();
    expect(screen.queryByText("Unknown")).not.toBeInTheDocument();
  });
});
