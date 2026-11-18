import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, act } from "@testing-library/react";

const reviewsMockData: Array<Record<string, unknown>> = [
  {
    id: "REV-101",
    tripId: "TRIP-101",
    tripReference: "TRIP-101",
    destination: "Unknown",
    tripType: "leisure",
    partySize: 2,
    dateWindow: "June 2026",
    value: 5000,
    currency: "USD",
    agentId: "agent-1",
    agentName: "Sarah Connor",
    submittedAt: "2026-11-10T10:00:00Z",
    status: "pending",
    reason: "Policy hold: requires owner review",
    riskFlags: [],
  },
  {
    id: "REV-102",
    tripId: "TRIP-102",
    tripReference: "TRIP-102",
    destination: "Tokyo",
    tripType: "luxury",
    partySize: 4,
    dateWindow: "July 2026",
    value: 12000,
    currency: "USD",
    agentId: "agent-2",
    agentName: "John Doe",
    submittedAt: "2026-11-11T10:00:00Z",
    status: "pending",
    reason: "High value quote check",
    riskFlags: ["high_value"],
  },
];

const mockBulkAction = vi.fn().mockResolvedValue({ success: true, processed: 2, failed: 0 });
const mockSubmitAction = vi.fn().mockResolvedValue({ success: true });
const mockRefetch = vi.fn().mockResolvedValue({});

vi.mock("next/link", () => ({
  default: ({ children, href, ...props }: { children: React.ReactNode; href: string }) => (
    <a href={href} {...props}>
      {children}
    </a>
  ),
}));

vi.mock("@/hooks/useGovernance", () => ({
  useReviews: () => ({
    data: reviewsMockData,
    isLoading: false,
    error: null,
    refetch: mockRefetch,
    submitAction: mockSubmitAction,
    bulkAction: mockBulkAction,
  }),
}));

vi.mock("@/hooks/useUnifiedState", () => ({
  useUnifiedState: () => ({
    state: {
      pending_review_count: 2,
      review_counts: { pending: 2 },
      pending_review_value_by_currency: { USD: 17000 },
      primary_review_currency: "USD",
    },
  }),
}));

import ReviewsPage from "../PageClient";

describe("Bulk Review Actions and Routing", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("surfaces multi-selection checkboxes and triggers bulk approval modal", async () => {
    render(<ReviewsPage />);

    // Checkboxes exist for each quote
    const checkboxes = screen.getAllByRole("checkbox");
    expect(checkboxes.length).toBe(2);

    // Select the first quote
    await act(async () => {
      fireEvent.click(checkboxes[0]);
    });

    // Bulk actions toolbar should appear
    expect(screen.getByText(/quote selected/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Bulk Approve/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Bulk Request Changes/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Bulk Reject/i })).toBeInTheDocument();

    // Click Bulk Approve
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /Bulk Approve/i }));
    });

    // Modal opens
    expect(screen.getByRole("heading", { name: /Bulk approve \(1 quote\)/i })).toBeInTheDocument();

    // Confirm bulk approval
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /Confirm approve/i }));
    });

    expect(mockBulkAction).toHaveBeenCalledWith([
      {
        reviewId: "REV-101",
        action: "approve",
        notes: "Bulk approved by owner via dashboard.",
      },
    ]);
  });

  it("routes View Quote link directly to the output quote stage", () => {
    render(<ReviewsPage />);

    const quoteLinks = screen.getAllByRole("link", { name: /View Quote/i });
    expect(quoteLinks.length).toBe(2);
    expect(quoteLinks[0]).toHaveAttribute("href", "/trips/TRIP-101/output");
    expect(quoteLinks[1]).toHaveAttribute("href", "/trips/TRIP-102/output");
  });
});
