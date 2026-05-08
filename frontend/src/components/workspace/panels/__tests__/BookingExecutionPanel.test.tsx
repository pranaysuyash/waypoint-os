import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import BookingExecutionPanel from "@/components/workspace/panels/BookingExecutionPanel";
import * as api from "@/lib/api-client";

// ── Mocks ───────────────────────────────────────────────────────────────────

vi.mock("@/lib/api-client", () => ({
  listBookingTasks: vi.fn(),
  generateBookingTasks: vi.fn(),
  completeBookingTask: vi.fn(),
  cancelBookingTask: vi.fn(),
  updateBookingTask: vi.fn(),
}));

const mockTask = (overrides: Partial<api.BookingTask> = {}): api.BookingTask => ({
  id: "task-1",
  trip_id: "trip-1",
  agency_id: "agency-1",
  task_type: "verify_passport",
  title: "Verify passport for Traveler 1",
  description: null,
  status: "not_started",
  priority: "medium",
  owner_id: null,
  due_at: null,
  blocker_code: null,
  blocker_refs: null,
  source: "readiness_generated",
  generation_hash: "abc123",
  created_by: "system",
  completed_by: null,
  completed_at: null,
  cancelled_at: null,
  created_at: "2026-05-09T00:00:00Z",
  updated_at: "2026-05-09T00:00:00Z",
  ...overrides,
});

const emptySummary: api.BookingTaskSummary = {
  total: 0,
  not_started: 0,
  blocked: 0,
  ready: 0,
  in_progress: 0,
  waiting_on_customer: 0,
  completed: 0,
  cancelled: 0,
};

// ── Tests ───────────────────────────────────────────────────────────────────

describe("BookingExecutionPanel", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows loading state", async () => {
    vi.mocked(api.listBookingTasks).mockReturnValue(new Promise(() => {}));
    render(<BookingExecutionPanel tripId="trip-1" />);

    expect(screen.getByText(/loading booking tasks/i)).toBeInTheDocument();
  });

  it("shows empty state when no tasks", async () => {
    vi.mocked(api.listBookingTasks).mockResolvedValue({
      ok: true,
      tasks: [],
      summary: emptySummary,
    });

    render(<BookingExecutionPanel tripId="trip-1" />);

    await waitFor(() => {
      expect(screen.getByText(/no booking tasks yet/i)).toBeInTheDocument();
    });
  });

  it("renders task list with titles", async () => {
    vi.mocked(api.listBookingTasks).mockResolvedValue({
      ok: true,
      tasks: [
        mockTask({ id: "t1", title: "Verify passport for Traveler 1", status: "not_started" }),
        mockTask({ id: "t2", title: "Confirm flights", status: "ready" }),
      ],
      summary: { ...emptySummary, total: 2, not_started: 1, ready: 1 },
    });

    render(<BookingExecutionPanel tripId="trip-1" />);

    await waitFor(() => {
      expect(screen.getByText("Verify passport for Traveler 1")).toBeInTheDocument();
      expect(screen.getByText("Confirm flights")).toBeInTheDocument();
    });
  });

  it("shows generate button and calls generate endpoint", async () => {
    const user = userEvent.setup();
    vi.mocked(api.listBookingTasks).mockResolvedValue({
      ok: true,
      tasks: [],
      summary: emptySummary,
    });
    vi.mocked(api.generateBookingTasks).mockResolvedValue({
      ok: true,
      created: [],
      skipped: [],
      reconciled: [],
    });

    render(<BookingExecutionPanel tripId="trip-1" />);

    const btn = await screen.findByRole("button", { name: /generate \/ reconcile/i });
    expect(btn).toBeInTheDocument();

    await user.click(btn);
    expect(api.generateBookingTasks).toHaveBeenCalledWith("trip-1");
  });

  it("shows blocked badge for blocked tasks", async () => {
    vi.mocked(api.listBookingTasks).mockResolvedValue({
      ok: true,
      tasks: [
        mockTask({ status: "blocked", blocker_code: "missing_document" }),
      ],
      summary: { ...emptySummary, total: 1, blocked: 1 },
    });

    render(<BookingExecutionPanel tripId="trip-1" />);

    await waitFor(() => {
      expect(screen.getByText("1 blocked")).toBeInTheDocument();
      expect(screen.getByText(/missing document/i)).toBeInTheDocument();
    });
  });

  it("shows ready badge", async () => {
    vi.mocked(api.listBookingTasks).mockResolvedValue({
      ok: true,
      tasks: [
        mockTask({ status: "ready" }),
      ],
      summary: { ...emptySummary, total: 1, ready: 1 },
    });

    render(<BookingExecutionPanel tripId="trip-1" />);

    await waitFor(() => {
      expect(screen.getByText("1 ready")).toBeInTheDocument();
    });
  });

  it("shows complete button for in_progress tasks", async () => {
    vi.mocked(api.listBookingTasks).mockResolvedValue({
      ok: true,
      tasks: [mockTask({ id: "t1", status: "in_progress" })],
      summary: { ...emptySummary, total: 1, in_progress: 1 },
    });

    render(<BookingExecutionPanel tripId="trip-1" />);

    await waitFor(() => {
      const completeBtn = screen.getByTitle("Complete");
      expect(completeBtn).toBeInTheDocument();
    });
  });

  it("hides cancel button for completed tasks", async () => {
    vi.mocked(api.listBookingTasks).mockResolvedValue({
      ok: true,
      tasks: [mockTask({ id: "t1", status: "completed" })],
      summary: { ...emptySummary, total: 1, completed: 1 },
    });

    render(<BookingExecutionPanel tripId="trip-1" />);

    await waitFor(() => {
      // Completed tasks are in the collapsible section
      expect(screen.queryByTitle("Cancel")).not.toBeInTheDocument();
    });
  });

  it("collapses completed tasks by default", async () => {
    vi.mocked(api.listBookingTasks).mockResolvedValue({
      ok: true,
      tasks: [
        mockTask({ id: "t1", title: "Active task", status: "ready" }),
        mockTask({ id: "t2", title: "Done task", status: "completed" }),
      ],
      summary: { ...emptySummary, total: 2, ready: 1, completed: 1 },
    });

    render(<BookingExecutionPanel tripId="trip-1" />);

    await waitFor(() => {
      expect(screen.getByText("Active task")).toBeInTheDocument();
      expect(screen.getByText("1 completed")).toBeInTheDocument();
      // Completed task should not be visible (collapsed)
      expect(screen.queryByText("Done task")).not.toBeInTheDocument();
    });
  });

  it("shows 'auto' badge for system-generated tasks", async () => {
    vi.mocked(api.listBookingTasks).mockResolvedValue({
      ok: true,
      tasks: [mockTask({ source: "readiness_generated" })],
      summary: { ...emptySummary, total: 1, not_started: 1 },
    });

    render(<BookingExecutionPanel tripId="trip-1" />);

    await waitFor(() => {
      expect(screen.getByText("auto")).toBeInTheDocument();
    });
  });

  it("does not show 'auto' badge for agent-created tasks", async () => {
    vi.mocked(api.listBookingTasks).mockResolvedValue({
      ok: true,
      tasks: [mockTask({ source: "agent_created" })],
      summary: { ...emptySummary, total: 1, not_started: 1 },
    });

    render(<BookingExecutionPanel tripId="trip-1" />);

    await waitFor(() => {
      expect(screen.queryByText("auto")).not.toBeInTheDocument();
    });
  });
});
