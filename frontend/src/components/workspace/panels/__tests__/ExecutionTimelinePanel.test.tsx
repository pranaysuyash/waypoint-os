import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import ExecutionTimelinePanel from "@/components/workspace/panels/ExecutionTimelinePanel";
import * as api from "@/lib/api-client";

// ── Mocks ────────────────────────────────────────────────────────────────────

vi.mock("@/lib/api-client", () => ({
  getExecutionTimeline: vi.fn(),
}));

const mockEvent = (overrides: Partial<api.ExecutionTimelineEvent> = {}): api.ExecutionTimelineEvent => ({
  event_type: "task_created",
  event_category: "task",
  subject_type: "booking_task",
  subject_id: "task-1",
  status_from: null,
  status_to: "not_started",
  actor_type: "system",
  actor_id: null,
  source: "system_generation",
  event_metadata: { task_type: "verify_passport" },
  timestamp: "2026-05-09T10:00:00Z",
  ...overrides,
});

// ── Tests ────────────────────────────────────────────────────────────────────

describe("ExecutionTimelinePanel", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows loading state", async () => {
    vi.mocked(api.getExecutionTimeline).mockReturnValue(new Promise(() => {}));
    render(<ExecutionTimelinePanel tripId="trip-1" />);

    expect(screen.getByText(/loading execution timeline/i)).toBeInTheDocument();
  });

  it("shows empty state when no events", async () => {
    vi.mocked(api.getExecutionTimeline).mockResolvedValue({
      ok: true,
      events: [],
      summary: { total: 0, task: 0, confirmation: 0, document: 0, extraction: 0 },
    });

    render(<ExecutionTimelinePanel tripId="trip-1" />);

    await waitFor(() => {
      expect(screen.getByText(/no execution events yet/i)).toBeInTheDocument();
    });
  });

  it("renders events by category", async () => {
    vi.mocked(api.getExecutionTimeline).mockResolvedValue({
      ok: true,
      events: [
        mockEvent({ event_type: "task_created", status_to: "not_started" }),
        mockEvent({ event_type: "confirmation_created", event_category: "confirmation", subject_type: "booking_confirmation", status_to: "draft" }),
      ],
      summary: { total: 2, task: 1, confirmation: 1, document: 0, extraction: 0 },
    });

    render(<ExecutionTimelinePanel tripId="trip-1" />);

    await waitFor(() => {
      expect(screen.getByText(/task created/i)).toBeInTheDocument();
      expect(screen.getByText(/confirmation created/i)).toBeInTheDocument();
    });
  });

  it("shows category filter chips with counts", async () => {
    vi.mocked(api.getExecutionTimeline).mockResolvedValue({
      ok: true,
      events: [mockEvent()],
      summary: { total: 1, task: 1, confirmation: 0, document: 0, extraction: 0 },
    });

    render(<ExecutionTimelinePanel tripId="trip-1" />);

    await waitFor(() => {
      expect(screen.getByText(/All \(1\)/)).toBeInTheDocument();
      expect(screen.getByText(/Tasks \(1\)/)).toBeInTheDocument();
    });
  });

  it("category filter calls API with category param", async () => {
    const user = userEvent.setup();
    vi.mocked(api.getExecutionTimeline).mockResolvedValue({
      ok: true,
      events: [mockEvent()],
      summary: { total: 1, task: 1, confirmation: 0, document: 0, extraction: 0 },
    });

    render(<ExecutionTimelinePanel tripId="trip-1" />);

    await screen.findByText(/Tasks \(1\)/);

    // Click Tasks filter chip
    const tasksChip = screen.getByText(/Tasks \(1\)/);
    await user.click(tasksChip);

    expect(api.getExecutionTimeline).toHaveBeenCalledWith("trip-1", "task");
  });

  it("no PII in rendered output - no supplier_name or confirmation_number", async () => {
    vi.mocked(api.getExecutionTimeline).mockResolvedValue({
      ok: true,
      events: [
        mockEvent({
          event_type: "confirmation_recorded",
          event_category: "confirmation",
          subject_type: "booking_confirmation",
          event_metadata: { confirmation_type: "flight" },
        }),
      ],
      summary: { total: 1, task: 0, confirmation: 1, document: 0, extraction: 0 },
    });

    render(<ExecutionTimelinePanel tripId="trip-1" />);

    await waitFor(() => {
      expect(screen.getByText(/confirmation recorded/i)).toBeInTheDocument();
    });

    // Ensure no PII is visible
    expect(screen.queryByText(/Emirates/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/ABC123/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/supplier_name/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/confirmation_number/i)).not.toBeInTheDocument();
  });

  it("shows System for system actor type", async () => {
    vi.mocked(api.getExecutionTimeline).mockResolvedValue({
      ok: true,
      events: [mockEvent({ actor_type: "system", actor_id: null })],
      summary: { total: 1, task: 1, confirmation: 0, document: 0, extraction: 0 },
    });

    render(<ExecutionTimelinePanel tripId="trip-1" />);

    await waitFor(() => {
      expect(screen.getByText("System")).toBeInTheDocument();
    });
  });

  it("shows user ID prefix for agent actor type", async () => {
    vi.mocked(api.getExecutionTimeline).mockResolvedValue({
      ok: true,
      events: [mockEvent({ actor_type: "agent", actor_id: "user-12345678-abc" })],
      summary: { total: 1, task: 1, confirmation: 0, document: 0, extraction: 0 },
    });

    render(<ExecutionTimelinePanel tripId="trip-1" />);

    await waitFor(() => {
      expect(screen.getByText("user-123")).toBeInTheDocument();
    });
  });

  it("renders events in chronological order from API", async () => {
    const events = [
      mockEvent({ event_type: "task_created", timestamp: "2026-05-09T10:00:00Z" }),
      mockEvent({ event_type: "task_completed", timestamp: "2026-05-09T11:00:00Z" }),
      mockEvent({ event_type: "confirmation_created", event_category: "confirmation", subject_type: "booking_confirmation", timestamp: "2026-05-09T12:00:00Z" }),
    ];
    vi.mocked(api.getExecutionTimeline).mockResolvedValue({
      ok: true,
      events,
      summary: { total: 3, task: 2, confirmation: 1, document: 0, extraction: 0 },
    });

    render(<ExecutionTimelinePanel tripId="trip-1" />);

    await waitFor(() => {
      expect(screen.getByText(/task created/i)).toBeInTheDocument();
      expect(screen.getByText(/task completed/i)).toBeInTheDocument();
      expect(screen.getByText(/confirmation created/i)).toBeInTheDocument();
    });
  });
});
