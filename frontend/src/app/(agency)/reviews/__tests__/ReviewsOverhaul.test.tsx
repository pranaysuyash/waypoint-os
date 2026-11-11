import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";

const reviewsState = vi.hoisted(() => ({
  reviews: [] as Array<Record<string, unknown>>,
}));

const unifiedState = vi.hoisted(() => ({
  data: {
    pending_review_count: 2,
    pending_review_value_by_currency: {} as Record<string, number>,
    primary_review_currency: "INR",
  },
}));

vi.mock("next/link", () => ({
  default: ({ children, href, ...props }: { children: React.ReactNode; href: string }) => (
    <a href={href} {...props}>
      {children}
    </a>
  ),
}));

vi.mock("@/hooks/useGovernance", () => ({
  useReviews: () => ({
    data: reviewsState.reviews,
    isLoading: false,
    error: null,
    refetch: vi.fn(),
    submitAction: vi.fn(),
  }),
}));

vi.mock("@/hooks/useUnifiedState", () => ({
  useUnifiedState: () => ({
    data: unifiedState.data,
    isLoading: false,
    error: null,
    refetch: vi.fn(),
  }),
}));

import ReviewsPage from "../PageClient";

describe("Command Center /reviews UX & currency overhaul", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("never renders '$ ₹' or '$0.0k' for zero-value INR quotes and humanizes STOP_NEEDS_REVIEW", () => {
    reviewsState.reviews = [
      {
        id: "REV-1",
        tripId: "TRIP-1",
        tripName: "Kyoto Honeymoon",
        customerName: "Asha Nair",
        destination: "Kyoto",
        tripType: "honeymoon",
        value: 0,
        currency: "INR",
        submittedBy: "System",
        submittedAt: "2026-11-10T10:00:00Z",
        waitingDays: 4,
        reason: "Decision state STOP_NEEDS_REVIEW requires owner review",
        status: "pending",
        riskFlags: [],
      },
    ];
    unifiedState.data = {
      pending_review_count: 1,
      pending_review_value_by_currency: {},
      primary_review_currency: "INR",
    };

    const { container } = render(<ReviewsPage />);

    expect(container.textContent).not.toContain("$ ₹");
    expect(container.textContent).not.toContain("$0.0k");
    expect(container.textContent).not.toContain("STOP_NEEDS_REVIEW");

    expect(screen.getByText("Budget to confirm")).toBeInTheDocument();
    expect(screen.getByText("To confirm")).toBeInTheDocument();
    expect(screen.getByText("Policy hold: requires owner review")).toBeInTheDocument();
  });

  it("paginates long queues at 25 rows and lets operators expand incrementally", () => {
    reviewsState.reviews = Array.from({ length: 60 }, (_, idx) => ({
      id: `REV-${idx + 1}`,
      tripId: `TRIP-${idx + 1}`,
      tripName: `Trip ${idx + 1}`,
      customerName: `Guest ${idx + 1}`,
      destination: "Paris",
      tripType: "leisure",
      value: 150000,
      currency: "INR",
      submittedBy: "Planner",
      submittedAt: "2026-11-10T10:00:00Z",
      waitingDays: 1,
      triggerReason: "High margin check",
      status: "pending",
      riskFlags: [],
    }));
    unifiedState.data = {
      pending_review_count: 60,
      pending_review_value_by_currency: { INR: 9000000 },
      primary_review_currency: "INR",
    };

    render(<ReviewsPage />);

    expect(screen.getByText(/Showing 25 of 60/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /Show 25 more/i }));
    expect(screen.getByText(/Showing 50 of 60/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /Show all \(60\)/i }));
    expect(screen.queryByRole("button", { name: /Show all/i })).not.toBeInTheDocument();
  });
});
