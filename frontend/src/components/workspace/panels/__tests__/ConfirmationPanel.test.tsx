import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import ConfirmationPanel from "@/components/workspace/panels/ConfirmationPanel";
import * as api from "@/lib/api-client";

// ── Mocks ────────────────────────────────────────────────────────────────────

vi.mock("@/lib/api-client", () => ({
  listConfirmations: vi.fn(),
  getConfirmation: vi.fn(),
  createConfirmation: vi.fn(),
  updateConfirmation: vi.fn(),
  recordConfirmation: vi.fn(),
  verifyConfirmation: vi.fn(),
  voidConfirmation: vi.fn(),
  getExecutionTimeline: vi.fn(),
}));

const mockSummary = (overrides: Partial<api.ConfirmationSummary> = {}): api.ConfirmationSummary => ({
  id: "conf-1",
  trip_id: "trip-1",
  task_id: null,
  confirmation_type: "flight",
  confirmation_status: "draft",
  has_supplier: false,
  has_confirmation_number: false,
  external_ref_present: false,
  notes_present: false,
  evidence_ref_count: 0,
  recorded_at: null,
  verified_at: null,
  voided_at: null,
  created_by: "user-1",
  created_at: "2026-05-09T00:00:00Z",
  ...overrides,
});

const mockDetail = (overrides: Partial<api.ConfirmationDetail> = {}): api.ConfirmationDetail => ({
  ...mockSummary(overrides),
  evidence_refs: null,
  supplier_name: null,
  confirmation_number: null,
  notes: null,
  external_ref: null,
  recorded_by: null,
  verified_by: null,
  voided_by: null,
  updated_at: "2026-05-09T00:00:00Z",
  ...overrides,
});

// ── Tests ────────────────────────────────────────────────────────────────────

describe("ConfirmationPanel", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows loading state", async () => {
    vi.mocked(api.listConfirmations).mockReturnValue(new Promise(() => {}));
    render(<ConfirmationPanel tripId="trip-1" />);

    expect(screen.getByText(/loading confirmations/i)).toBeInTheDocument();
  });

  it("shows empty state when no confirmations", async () => {
    vi.mocked(api.listConfirmations).mockResolvedValue({
      ok: true,
      confirmations: [],
    });

    render(<ConfirmationPanel tripId="trip-1" />);

    await waitFor(() => {
      expect(screen.getByText(/no confirmations yet/i)).toBeInTheDocument();
    });
  });

  it("renders confirmation list with type labels", async () => {
    vi.mocked(api.listConfirmations).mockResolvedValue({
      ok: true,
      confirmations: [
        mockSummary({ id: "c1", confirmation_type: "flight", confirmation_status: "draft" }),
        mockSummary({ id: "c2", confirmation_type: "hotel", confirmation_status: "recorded" }),
      ],
    });

    render(<ConfirmationPanel tripId="trip-1" />);

    await waitFor(() => {
      expect(screen.getByText("flight")).toBeInTheDocument();
      expect(screen.getByText("hotel")).toBeInTheDocument();
    });
  });

  it("shows has_supplier badge in summary list", async () => {
    vi.mocked(api.listConfirmations).mockResolvedValue({
      ok: true,
      confirmations: [mockSummary({ has_supplier: true })],
    });

    render(<ConfirmationPanel tripId="trip-1" />);

    await waitFor(() => {
      expect(screen.getByText("supplier")).toBeInTheDocument();
    });
  });

  it("shows has_confirmation_number badge in summary list", async () => {
    vi.mocked(api.listConfirmations).mockResolvedValue({
      ok: true,
      confirmations: [mockSummary({ has_confirmation_number: true })],
    });

    render(<ConfirmationPanel tripId="trip-1" />);

    await waitFor(() => {
      expect(screen.getByText("ref#")).toBeInTheDocument();
    });
  });

  it("shows notes_present badge in summary list", async () => {
    vi.mocked(api.listConfirmations).mockResolvedValue({
      ok: true,
      confirmations: [mockSummary({ notes_present: true })],
    });

    render(<ConfirmationPanel tripId="trip-1" />);

    await waitFor(() => {
      expect(screen.getByText("notes")).toBeInTheDocument();
    });
  });

  it("summary list does not show decrypted values", async () => {
    vi.mocked(api.listConfirmations).mockResolvedValue({
      ok: true,
      confirmations: [mockSummary({ has_supplier: true, has_confirmation_number: true })],
    });

    render(<ConfirmationPanel tripId="trip-1" />);

    await waitFor(() => {
      // Summary shows badges but not the actual values
      expect(screen.queryByText("Emirates")).not.toBeInTheDocument();
      expect(screen.queryByText("ABC123")).not.toBeInTheDocument();
    });
  });

  it("opens create form on button click", async () => {
    const user = userEvent.setup();
    vi.mocked(api.listConfirmations).mockResolvedValue({
      ok: true,
      confirmations: [],
    });

    render(<ConfirmationPanel tripId="trip-1" />);

    const btn = await screen.findByRole("button", { name: /add confirmation/i });
    await user.click(btn);

    expect(screen.getByRole("button", { name: /create/i })).toBeInTheDocument();
    expect(screen.getByRole("combobox")).toBeInTheDocument();
  });

  it("calls createConfirmation on form submit", async () => {
    const user = userEvent.setup();
    vi.mocked(api.listConfirmations).mockResolvedValue({
      ok: true,
      confirmations: [],
    });
    vi.mocked(api.createConfirmation).mockResolvedValue({
      ok: true,
      confirmation: mockDetail(),
    });

    render(<ConfirmationPanel tripId="trip-1" />);

    const btn = await screen.findByRole("button", { name: /add confirmation/i });
    await user.click(btn);

    const createBtn = screen.getByRole("button", { name: /create/i });
    await user.click(createBtn);

    expect(api.createConfirmation).toHaveBeenCalledWith("trip-1", expect.objectContaining({
      confirmation_type: "flight",
    }));
  });

  it("calls recordConfirmation for draft confirmations", async () => {
    const user = userEvent.setup();
    vi.mocked(api.listConfirmations).mockResolvedValue({
      ok: true,
      confirmations: [mockSummary({ id: "c1", confirmation_status: "draft" })],
    });
    vi.mocked(api.getConfirmation).mockResolvedValue({
      ok: true,
      confirmation: mockDetail({ id: "c1", confirmation_status: "draft" }),
    });
    vi.mocked(api.recordConfirmation).mockResolvedValue({
      ok: true,
      confirmation: mockSummary({ id: "c1", confirmation_status: "recorded" }),
    });

    render(<ConfirmationPanel tripId="trip-1" />);

    // Click on confirmation to view detail
    const confBtn = await screen.findByText("flight");
    await user.click(confBtn);

    // Wait for detail to load, then click Record
    await waitFor(() => {
      expect(api.getConfirmation).toHaveBeenCalledWith("trip-1", "c1");
    });

    const recordBtn = await screen.findByRole("button", { name: /record/i });
    await user.click(recordBtn);

    expect(api.recordConfirmation).toHaveBeenCalledWith("trip-1", "c1");
  });

  it("shows void button for non-voided confirmations", async () => {
    const user = userEvent.setup();
    vi.mocked(api.listConfirmations).mockResolvedValue({
      ok: true,
      confirmations: [mockSummary({ id: "c1", confirmation_status: "verified" })],
    });
    vi.mocked(api.getConfirmation).mockResolvedValue({
      ok: true,
      confirmation: mockDetail({ id: "c1", confirmation_status: "verified" }),
    });

    render(<ConfirmationPanel tripId="trip-1" />);

    const confBtn = await screen.findByText("flight");
    await user.click(confBtn);

    const voidBtn = await screen.findByRole("button", { name: /void/i });
    expect(voidBtn).toBeInTheDocument();
  });

  it("does not show void button for voided confirmations", async () => {
    const user = userEvent.setup();
    vi.mocked(api.listConfirmations).mockResolvedValue({
      ok: true,
      confirmations: [mockSummary({ id: "c1", confirmation_status: "voided" })],
    });
    vi.mocked(api.getConfirmation).mockResolvedValue({
      ok: true,
      confirmation: mockDetail({ id: "c1", confirmation_status: "voided" }),
    });

    render(<ConfirmationPanel tripId="trip-1" />);

    const confBtn = await screen.findByText("flight");
    await user.click(confBtn);

    await waitFor(() => {
      expect(screen.queryByRole("button", { name: /void/i })).not.toBeInTheDocument();
    });
  });

  it("enforces notes max length on form", async () => {
    const user = userEvent.setup();
    vi.mocked(api.listConfirmations).mockResolvedValue({
      ok: true,
      confirmations: [],
    });

    render(<ConfirmationPanel tripId="trip-1" />);

    const btn = await screen.findByRole("button", { name: /add confirmation/i });
    await user.click(btn);

    const allTextboxes = screen.getAllByRole("textbox");
    const notesTextarea = allTextboxes.find(el => el.tagName === "TEXTAREA") as HTMLTextAreaElement;
    expect(notesTextarea).toBeTruthy();

    fireEvent.change(notesTextarea, { target: { value: "a".repeat(3000) } });
    expect(notesTextarea.value).toBe("a".repeat(2000));

    fireEvent.change(notesTextarea, { target: { value: "a".repeat(500) } });
    expect(notesTextarea.value).toBe("a".repeat(500));
  });
});
