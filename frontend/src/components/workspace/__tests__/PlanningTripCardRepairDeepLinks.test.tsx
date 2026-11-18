import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import type { Trip } from "@/lib/api-client";
import { PlanningTripCard } from "../PlanningTripCard";

vi.mock("next/link", () => ({
  default: ({ children, href, ...props }: { children: React.ReactNode; href: string }) => (
    <a href={href} {...props}>
      {children}
    </a>
  ),
}));

describe("PlanningTripCard Repair Deep Links", () => {
  it("never produces '?repair=undefined' and resolves canonical field targets", () => {
    const mockTrip: Trip = {
      id: "trip-deep-test",
      destination: "Kyoto",
      dateWindow: "2026-10-01 to 2026-10-15",
      type: "leisure",
      state: "blue",
      age: "today",
      createdAt: "2026-11-10T10:00:00Z",
      updatedAt: "2026-11-10T10:00:00Z",
      status: "in_progress",
      stage: "needs_information",
    };

    render(<PlanningTripCard trip={mockTrip} variant="overview" />);

    const links = screen.getAllByRole("link");
    const hrefs = links.map((l) => l.getAttribute("href"));

    // Verify no broken query parameters
    for (const href of hrefs) {
      if (href) {
        expect(href).not.toContain("repair=undefined");
      }
    }

    // Check specific resolved repair targets
    const budgetLink = screen.getByRole("link", { name: /Add budget/i });
    expect(budgetLink.getAttribute("href")).toBe("/trips/trip-deep-test/intake?repair=budget");

    const partyLink = screen.getByRole("link", { name: /Add traveler count/i });
    expect(partyLink.getAttribute("href")).toBe("/trips/trip-deep-test/intake?repair=party");

    const purposeLink = screen.getByRole("link", { name: /Add trip purpose/i });
    expect(purposeLink.getAttribute("href")).toBe("/trips/trip-deep-test/intake?repair=type");
  });
});
