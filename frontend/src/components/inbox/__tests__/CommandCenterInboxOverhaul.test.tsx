import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";

const pushMock = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushMock }),
}));

vi.mock("next/link", () => ({
  default: ({ children, href, ...props }: { children: React.ReactNode; href: string }) => (
    <a href={href} {...props}>
      {children}
    </a>
  ),
}));

import ChannelMessagesPanel from "../ChannelMessagesPanel";
import { TripCard } from "../TripCard";
import { formatFlagLabel } from "@/lib/inbox-helpers";
import type { InboxTrip } from "@/types/governance";

describe("Command Center /inbox UX overhaul", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("humanizes snake_case trip flags via formatFlagLabel", () => {
    expect(formatFlagLabel("details_unclear")).toBe("Details unclear");
    expect(formatFlagLabel("incomplete")).toBe("Incomplete details");
    expect(formatFlagLabel("custom_vendor_flag")).toBe("Custom vendor flag");
  });

  it("renders TripCard flags with calm human labels and non-uppercase SLA/stage pills", () => {
    const trip: InboxTrip = {
      id: "trip-1",
      reference: "TRIP-ABC123",
      customerName: "Riya Sen",
      destination: "Kyoto",
      tripType: "leisure",
      dateWindow: "Dec 1 – Dec 7, 2026",
      partySize: 2,
      value: 4500,
      stage: "intake",
      stageNumber: 1,
      daysInCurrentStage: 6,
      slaStatus: "breached",
      flags: ["details_unclear"],
      priority: "high",
      priorityScore: 80,
      urgency: 85,
      importance: 75,
      submittedAt: "2026-11-01T10:00:00Z",
      lastUpdated: "2026-11-05T10:00:00Z",
    };

    render(<TripCard trip={trip} isSelected={false} onSelect={vi.fn()} />);

    expect(screen.getByText("Details unclear")).toBeInTheDocument();
    expect(screen.queryByText("details_unclear")).not.toBeInTheDocument();

    const slaPill = screen.getByTestId("trip-card-sla");
    expect(slaPill.className).not.toContain("uppercase");

    const stagePill = screen.getByTestId("trip-card-stage");
    expect(stagePill).toHaveTextContent("Intake");
    expect(stagePill.className).not.toContain("uppercase");
  });

  it("collapses ChannelMessagesPanel into a single-row preview bar when defaultCollapsed is true and expands on click", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            messages: [
              {
                message_id: "m1",
                trip_id: null,
                channel: "whatsapp",
                direction: "inbound",
                from_party: "Marco Polo",
                to_party: "Agency",
                body: "Looking for 5 nights in Kyoto in December",
                received_at: "2026-11-11T09:00:00Z",
              },
              {
                message_id: "m2",
                trip_id: null,
                channel: "sms",
                direction: "inbound",
                from_party: "Older Guest",
                to_party: "Agency",
                body: "Older message hidden when collapsed",
                received_at: "2026-11-10T09:00:00Z",
              },
            ],
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        ),
      ),
    );

    render(<ChannelMessagesPanel defaultCollapsed />);

    await waitFor(() => {
      expect(screen.getByTestId("channel-messages-collapsed-summary")).toBeInTheDocument();
    });

    expect(screen.getByText(/Looking for 5 nights in Kyoto/)).toBeInTheDocument();
    expect(screen.queryByTestId("channel-message-row")).not.toBeInTheDocument();

    fireEvent.click(screen.getByTestId("channel-messages-toggle"));

    expect(screen.getAllByTestId("channel-message-row")).toHaveLength(2);
    expect(screen.getByText("Older message hidden when collapsed")).toBeInTheDocument();
  });
});
