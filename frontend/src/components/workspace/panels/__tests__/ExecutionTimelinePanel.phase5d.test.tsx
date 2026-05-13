import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, waitFor, within } from "@testing-library/react";
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

describe("ExecutionTimelinePanel Phase 5D", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // ── Date grouping ───────────────────────────────────────────────────────

  it("groups events by date with date headers", async () => {
    vi.mocked(api.getExecutionTimeline).mockResolvedValue({
      ok: true,
      events: [
        mockEvent({ subject_id: "t1", timestamp: "2026-05-09T10:00:00Z" }),
        mockEvent({ subject_id: "t2", timestamp: "2026-05-09T14:00:00Z" }),
        mockEvent({ subject_id: "t3", timestamp: "2026-05-10T09:00:00Z" }),
      ],
      summary: { total: 3, task: 3, confirmation: 0, document: 0, extraction: 0 },
    });

    render(<ExecutionTimelinePanel tripId="trip-1" />);

    await waitFor(() => {
      // Two date headers for two different dates
      const dateHeaders = screen.getAllByText(/May/);
      expect(dateHeaders).toHaveLength(2);
    });
  });

  it("shows one date header for single-day events", async () => {
    vi.mocked(api.getExecutionTimeline).mockResolvedValue({
      ok: true,
      events: [
        mockEvent({ subject_id: "t1", timestamp: "2026-05-09T10:00:00Z" }),
        mockEvent({ subject_id: "t2", timestamp: "2026-05-09T14:00:00Z" }),
      ],
      summary: { total: 2, task: 2, confirmation: 0, document: 0, extraction: 0 },
    });

    render(<ExecutionTimelinePanel tripId="trip-1" />);

    await waitFor(() => {
      const dateHeaders = screen.getAllByText(/May/);
      expect(dateHeaders).toHaveLength(1);
    });
  });

  // ── Actor filter ────────────────────────────────────────────────────────

  it("renders actor filter chips", async () => {
    vi.mocked(api.getExecutionTimeline).mockResolvedValue({
      ok: true,
      events: [mockEvent()],
      summary: { total: 1, task: 1, confirmation: 0, document: 0, extraction: 0 },
    });

    render(<ExecutionTimelinePanel tripId="trip-1" />);

    await waitFor(() => {
      expect(screen.getByText("All actors")).toBeInTheDocument();
      expect(screen.getByText("Agent actions")).toBeInTheDocument();
      expect(screen.getByText("System events")).toBeInTheDocument();
    });
  });

  it("clicking agent filter calls API with actor_type=agent", async () => {
    const user = userEvent.setup();
    vi.mocked(api.getExecutionTimeline).mockResolvedValue({
      ok: true,
      events: [mockEvent()],
      summary: { total: 1, task: 1, confirmation: 0, document: 0, extraction: 0 },
    });

    render(<ExecutionTimelinePanel tripId="trip-1" />);

    await screen.findByText("Agent actions");

    await user.click(screen.getByText("Agent actions"));

    expect(api.getExecutionTimeline).toHaveBeenCalledWith("trip-1", undefined, "agent");
  });

  // ── Detail drawer ───────────────────────────────────────────────────────

  it("expands metadata on click", async () => {
    const user = userEvent.setup();
    vi.mocked(api.getExecutionTimeline).mockResolvedValue({
      ok: true,
      events: [mockEvent({ event_metadata: { task_type: "verify_passport" } })],
      summary: { total: 1, task: 1, confirmation: 0, document: 0, extraction: 0 },
    });

    render(<ExecutionTimelinePanel tripId="trip-1" />);

    // Wait for events to render, then click to expand
    const row = await screen.findByText(/task created/i);
    await user.click(row);

    expect(screen.getByText("verify_passport")).toBeInTheDocument();
  });

  it("renders metadata keys with human labels", async () => {
    const user = userEvent.setup();
    vi.mocked(api.getExecutionTimeline).mockResolvedValue({
      ok: true,
      events: [mockEvent({ event_metadata: { latency_ms: 1500, overall_confidence: 0.92 } })],
      summary: { total: 1, task: 1, confirmation: 0, document: 0, extraction: 0 },
    });

    render(<ExecutionTimelinePanel tripId="trip-1" />);

    const row = await screen.findByText(/task created/i);
    await user.click(row);

    expect(screen.getByText("Latency")).toBeInTheDocument();
    expect(screen.getByText("1500ms")).toBeInTheDocument();
    expect(screen.getByText("Confidence")).toBeInTheDocument();
    expect(screen.getByText("92%")).toBeInTheDocument();
  });

  it("only renders keys in SAFE_METADATA_KEYS", async () => {
    const user = userEvent.setup();
    vi.mocked(api.getExecutionTimeline).mockResolvedValue({
      ok: true,
      events: [mockEvent({
        event_metadata: { task_type: "confirm_flights", random_unknown_key: "value" },
      })],
      summary: { total: 1, task: 1, confirmation: 0, document: 0, extraction: 0 },
    });

    render(<ExecutionTimelinePanel tripId="trip-1" />);

    const row = await screen.findByText(/task created/i);
    await user.click(row);

    // Known key rendered
    expect(screen.getByText("Task type")).toBeInTheDocument();
    // Unknown key NOT rendered
    expect(screen.queryByText("random_unknown_key")).not.toBeInTheDocument();
  });

  it("does not render PII keys even if present in metadata", async () => {
    const user = userEvent.setup();
    vi.mocked(api.getExecutionTimeline).mockResolvedValue({
      ok: true,
      events: [mockEvent({
        event_metadata: {
          supplier_name: "Emirates",
          passport_number: "X1234567",
          storage_key: "/secret/path",
          task_type: "confirm_flights",
        },
      })],
      summary: { total: 1, task: 1, confirmation: 0, document: 0, extraction: 0 },
    });

    render(<ExecutionTimelinePanel tripId="trip-1" />);

    const row = await screen.findByText(/task created/i);
    await user.click(row);

    // Safe key rendered
    expect(screen.getByText("Task type")).toBeInTheDocument();
    // PII keys NOT rendered (defense-in-depth)
    expect(screen.queryByText("Emirates")).not.toBeInTheDocument();
    expect(screen.queryByText("X1234567")).not.toBeInTheDocument();
    expect(screen.queryByText("/secret/path")).not.toBeInTheDocument();
    expect(screen.queryByText("supplier_name")).not.toBeInTheDocument();
    expect(screen.queryByText("passport_number")).not.toBeInTheDocument();
    expect(screen.queryByText("storage_key")).not.toBeInTheDocument();
  });

  // ── Empty/error states ──────────────────────────────────────────────────

  it("shows empty state message", async () => {
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

  it("shows error state on API failure", async () => {
    vi.mocked(api.getExecutionTimeline).mockRejectedValue(new Error("Network error"));

    render(<ExecutionTimelinePanel tripId="trip-1" />);

    await waitFor(() => {
      expect(screen.getByText(/failed to load timeline/i)).toBeInTheDocument();
    });
  });

  // ── Redaction sentinel ──────────────────────────────────────────────────

  it("rendered timeline contains zero PII patterns", async () => {
    vi.mocked(api.getExecutionTimeline).mockResolvedValue({
      ok: true,
      events: [
        mockEvent({
          event_type: "extraction_run_completed",
          event_category: "extraction",
          subject_type: "document_extraction",
          subject_id: "ext-1",
          status_to: "success",
          event_metadata: { provider: "openai", overall_confidence: 0.95 },
        }),
        mockEvent({
          event_type: "document_uploaded",
          event_category: "document",
          subject_type: "booking_document",
          subject_id: "doc-1",
          status_to: "pending_review",
          event_metadata: { document_type: "passport", size_bytes: 204800 },
        }),
      ],
      summary: { total: 2, task: 0, confirmation: 0, document: 1, extraction: 1 },
    });

    const { container } = render(<ExecutionTimelinePanel tripId="trip-1" />);

    await waitFor(() => {
      expect(screen.getByText(/extraction run completed/i)).toBeInTheDocument();
    });

    const html = container.innerHTML;
    const piiPatterns = [
      "supplier_name", "confirmation_number", "filename",
      "storage_key", "extracted_fields", "passport_number",
      "error_summary",
    ];
    for (const pattern of piiPatterns) {
      expect(html).not.toContain(pattern);
    }
  });
});
