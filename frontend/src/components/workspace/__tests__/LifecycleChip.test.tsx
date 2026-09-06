import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { LifecycleChip } from "@/components/workspace/LifecycleChip";
import type { Trip } from "@/lib/api-client";

function makeTrip(overrides: Partial<Trip> = {}): Trip {
  return {
    id: "trip_test",
    destination: "Tokyo",
    type: "leisure",
    state: "blue",
    age: "2h",
    createdAt: "2026-09-01T00:00:00Z",
    updatedAt: "2026-09-01T01:00:00Z",
    ...overrides,
  };
}

describe("LifecycleChip", () => {
  it("renders the derived lifecycle label", () => {
    render(<LifecycleChip trip={makeTrip({ status: "new" })} />);
    expect(screen.getByText("Intake")).toBeTruthy();
  });

  it("renders blocker count when blockers exist", () => {
    render(
      <LifecycleChip
        trip={makeTrip({ status: "active", review_status: "escalated" })}
      />,
    );
    expect(screen.getByText("Escalated")).toBeTruthy();
    expect(screen.getByText("1")).toBeTruthy(); // blocker count badge
    const chip = screen.getByText("Escalated").closest("[data-lifecycle-state]");
    expect(chip?.getAttribute("data-lifecycle-state")).toBe("escalated");
    expect(chip?.getAttribute("data-blocker-count")).toBe("1");
  });

  it("exposes the next action in the tooltip", () => {
    render(<LifecycleChip trip={makeTrip({ status: "incomplete" })} />);
    const chip = screen.getByText("Needs Information").closest("[data-lifecycle-state]");
    expect(chip?.getAttribute("title")).toContain("Next:");
  });

  it("renders with no blockers badge when clean", () => {
    render(<LifecycleChip trip={makeTrip({ status: "active", stage: "proposal" })} />);
    const chip = screen.getByText("Planning").closest("[data-lifecycle-state]");
    expect(chip?.getAttribute("data-blocker-count")).toBe("0");
  });
});
