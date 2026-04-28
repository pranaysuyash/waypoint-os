import { describe, it, expect, vi, beforeEach } from "vitest";
import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import userEvent from "@testing-library/user-event";
import CaptureCallPanel from "../CaptureCallPanel";
import * as apiClient from "@/lib/api-client";
import type { Trip } from "@/lib/api-client";

// Mock the API client
vi.mock("@/lib/api-client", async () => {
  const actual = await vi.importActual("@/lib/api-client");
  return {
    ...actual,
    createTrip: vi.fn(),
  };
});

describe("CaptureCallPanel", () => {
  const mockTrip: Trip = {
    id: "trip-123",
    destination: "Japan",
    type: "international",
    state: "blue",
    age: "0",
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    status: "open",
    customerMessage: "Family of 4 wants Japan",
    agentNotes: "Budget conscious",
    followUpDueDate: new Date(Date.now() + 48 * 60 * 60 * 1000).toISOString(),
  };

  const defaultProps = {
    onSave: vi.fn(),
    onCancel: vi.fn(),
    defaultFollowUpHours: 48,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  // Test 1: Component renders with empty form
  it("renders with empty form and correct labels", () => {
    render(<CaptureCallPanel {...defaultProps} />);

    expect(screen.getByText("Capture Call")).toBeInTheDocument();
    expect(
      screen.getByText("Record the customer's travel intent and next steps")
    ).toBeInTheDocument();

    expect(screen.getByLabelText("What did the customer tell you?")).toHaveValue("");
    expect(screen.getByLabelText("Any notes for yourself?")).toHaveValue("");
    // Follow-up date has a default value, so just verify it exists and is truthy
    const followUpInput = screen.getByLabelText("Promise to follow up by:") as HTMLInputElement;
    expect(followUpInput.value).toBeTruthy();

    expect(screen.getByRole("button", { name: /Cancel/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Save/i })).toBeInTheDocument();
  });

  // Test 2: Save button is disabled if raw_note is empty
  it("disables save button when raw_note is empty", () => {
    render(<CaptureCallPanel {...defaultProps} />);

    const saveButton = screen.getByRole("button", { name: /Save/i });
    expect(saveButton).toBeDisabled();
  });

  // Test 3: Save button is enabled when raw_note has content
  it("enables save button when raw_note has content", async () => {
    const user = userEvent.setup();
    render(<CaptureCallPanel {...defaultProps} />);

    const rawNoteInput = screen.getByLabelText("What did the customer tell you?");
    await user.type(rawNoteInput, "Family wants to explore Japan");

    const saveButton = screen.getByRole("button", { name: /Save/i });
    expect(saveButton).not.toBeDisabled();
  });

  // Test 3: Form submission validation - raw_note is required
  it("prevents submission when raw_note is empty", async () => {
    const user = userEvent.setup();
    render(<CaptureCallPanel {...defaultProps} />);

    const saveButton = screen.getByRole("button", { name: /Save/i });
    
    // Button should be disabled because raw_note is empty
    expect(saveButton).toBeDisabled();

    // API should not be called
    const mockCreateTrip = vi.mocked(apiClient.createTrip);
    expect(mockCreateTrip).not.toHaveBeenCalled();
  });

  // Test 4: Default follow-up is 48 hours from now (±5 min tolerance)
  it("sets default follow-up to 48 hours from now (±5 min tolerance)", async () => {
    render(<CaptureCallPanel {...defaultProps} />);

    const followUpInput = screen.getByLabelText(
      "Promise to follow up by:"
    ) as HTMLInputElement;
    const defaultValue = followUpInput.value;

    expect(defaultValue).toBeTruthy();

    // Parse the datetime-local value (format: YYYY-MM-DDTHH:mm)
    // The datetime-local input stores local time, not UTC
    const [datePart, timePart] = defaultValue.split("T");
    const [year, month, day] = datePart.split("-").map(Number);
    const [hours, minutes] = timePart.split(":").map(Number);
    
    const defaultDate = new Date(year, month - 1, day, hours, minutes, 0);
    const now = new Date();
    const expected48h = new Date(now.getTime() + 48 * 60 * 60 * 1000);

    // Allow 5 minute tolerance
    const tolerance = 5 * 60 * 1000;
    const diffMs = Math.abs(defaultDate.getTime() - expected48h.getTime());

    expect(diffMs).toBeLessThan(tolerance);
  });

  // Test 5: Custom follow-up hours parameter works
  it("respects custom defaultFollowUpHours parameter", async () => {
    const customHours = 72;
    render(
      <CaptureCallPanel
        onSave={defaultProps.onSave}
        onCancel={defaultProps.onCancel}
        defaultFollowUpHours={customHours}
      />
    );

    const followUpInput = screen.getByLabelText(
      "Promise to follow up by:"
    ) as HTMLInputElement;
    const defaultValue = followUpInput.value;

    // Parse the datetime-local value (format: YYYY-MM-DDTHH:mm)
    const [datePart, timePart] = defaultValue.split("T");
    const [year, month, day] = datePart.split("-").map(Number);
    const [hours, minutes] = timePart.split(":").map(Number);
    
    const defaultDate = new Date(year, month - 1, day, hours, minutes, 0);
    const now = new Date();
    const expectedTime = new Date(now.getTime() + customHours * 60 * 60 * 1000);

    const tolerance = 5 * 60 * 1000;
    const diffMs = Math.abs(defaultDate.getTime() - expectedTime.getTime());

    expect(diffMs).toBeLessThan(tolerance);
  });

  // Test 7: Form submission succeeds with valid data
  it("submits form with valid raw_note and calls onSave callback", async () => {
    const user = userEvent.setup();
    const mockCreateTrip = vi.mocked(apiClient.createTrip);
    mockCreateTrip.mockResolvedValue(mockTrip);

    render(<CaptureCallPanel {...defaultProps} />);

    const rawNoteInput = screen.getByLabelText("What did the customer tell you?");
    const ownerNoteInput = screen.getByLabelText("Any notes for yourself?");

    await user.type(rawNoteInput, "Family of 4 wants to explore Japan");
    await user.type(ownerNoteInput, "Budget concerns mentioned");

    const saveButton = screen.getByRole("button", { name: /Save/i });
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(mockCreateTrip).toHaveBeenCalledWith(
        expect.objectContaining({
          raw_note: "Family of 4 wants to explore Japan",
          owner_note: "Budget concerns mentioned",
        })
      );
    });

    await waitFor(() => {
      expect(defaultProps.onSave).toHaveBeenCalledWith(mockTrip);
    });
  });

  // Test 8: Form clears after successful submission
  it("clears form after successful submission", async () => {
    const user = userEvent.setup();
    const mockCreateTrip = vi.mocked(apiClient.createTrip);
    mockCreateTrip.mockResolvedValue(mockTrip);

    render(<CaptureCallPanel {...defaultProps} />);

    const rawNoteInput = screen.getByLabelText(
      "What did the customer tell you?"
    ) as HTMLInputElement;
    const ownerNoteInput = screen.getByLabelText("Any notes for yourself?") as HTMLInputElement;

    await user.type(rawNoteInput, "Test data");
    await user.type(ownerNoteInput, "Test owner note");

    const saveButton = screen.getByRole("button", { name: /Save/i });
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(rawNoteInput.value).toBe("");
      expect(ownerNoteInput.value).toBe("");
    });
  });

  // Test 9: onCancel callback is called when clicking Cancel
  it("calls onCancel callback when Cancel button is clicked", async () => {
    const user = userEvent.setup();
    render(<CaptureCallPanel {...defaultProps} />);

    const rawNoteInput = screen.getByLabelText("What did the customer tell you?");
    await user.type(rawNoteInput, "Test data");

    const cancelButton = screen.getByRole("button", { name: /Cancel/i });
    await user.click(cancelButton);

    expect(defaultProps.onCancel).toHaveBeenCalledTimes(1);
  });

  // Test 10: Form clears when Cancel is clicked
  it("clears form data when Cancel button is clicked", async () => {
    const user = userEvent.setup();
    render(<CaptureCallPanel {...defaultProps} />);

    const rawNoteInput = screen.getByLabelText(
      "What did the customer tell you?"
    ) as HTMLInputElement;
    const ownerNoteInput = screen.getByLabelText("Any notes for yourself?") as HTMLInputElement;

    await user.type(rawNoteInput, "Test data");
    await user.type(ownerNoteInput, "Test owner note");

    const cancelButton = screen.getByRole("button", { name: /Cancel/i });
    await user.click(cancelButton);

    await waitFor(() => {
      expect(rawNoteInput.value).toBe("");
      expect(ownerNoteInput.value).toBe("");
    });
  });

  // Test 11: Loading state while POST is in flight
  it("shows loading state while POST is in flight", async () => {
    const user = userEvent.setup();
    const mockCreateTrip = vi.mocked(apiClient.createTrip);

    // Create a promise that we can resolve manually to control timing
    let resolveRequest: (value: Trip) => void;
    const requestPromise = new Promise<Trip>((resolve) => {
      resolveRequest = resolve;
    });

    mockCreateTrip.mockReturnValue(requestPromise);

    render(<CaptureCallPanel {...defaultProps} />);

    const rawNoteInput = screen.getByLabelText("What did the customer tell you?");
    await user.type(rawNoteInput, "Family wants Japan");

    const saveButton = screen.getByRole("button", { name: /Save/i });
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /Saving/i })).toBeInTheDocument();
      expect(saveButton).toBeDisabled();
    });

    // Resolve the request
    resolveRequest!(mockTrip);

    // Wait for the loading state to be gone
    await waitFor(() => {
      expect(screen.queryByRole("button", { name: /Saving/i })).not.toBeInTheDocument();
    });
  });

  // Test 12: API error is displayed when request fails
  it("displays API error message when request fails", async () => {
    const user = userEvent.setup();
    const mockCreateTrip = vi.mocked(apiClient.createTrip);
    const errorMessage = "Network error: Failed to reach server";
    mockCreateTrip.mockRejectedValue(new Error(errorMessage));

    render(<CaptureCallPanel {...defaultProps} />);

    const rawNoteInput = screen.getByLabelText("What did the customer tell you?");
    await user.type(rawNoteInput, "Family wants Japan");

    const saveButton = screen.getByRole("button", { name: /Save/i });
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(screen.getByText(/Error saving call/i)).toBeInTheDocument();
      expect(screen.getByText(errorMessage)).toBeInTheDocument();
    });

    // onSave should not be called
    expect(defaultProps.onSave).not.toHaveBeenCalled();
  });

  // Test 13: Empty owner_note is not sent if not provided
  it("does not send owner_note if empty", async () => {
    const user = userEvent.setup();
    const mockCreateTrip = vi.mocked(apiClient.createTrip);
    mockCreateTrip.mockResolvedValue(mockTrip);

    render(<CaptureCallPanel {...defaultProps} />);

    const rawNoteInput = screen.getByLabelText("What did the customer tell you?");
    await user.type(rawNoteInput, "Just the raw note");

    const saveButton = screen.getByRole("button", { name: /Save/i });
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(mockCreateTrip).toHaveBeenCalledWith(
        expect.objectContaining({
          raw_note: "Just the raw note",
          // owner_note should be undefined
        })
      );

      const call = mockCreateTrip.mock.calls[0][0];
      expect(call.owner_note).toBeUndefined();
    });
  });

  // Test 14: Whitespace-only input is treated as empty
  it("treats whitespace-only raw_note as empty on submit", async () => {
    const user = userEvent.setup();
    const mockCreateTrip = vi.mocked(apiClient.createTrip);

    render(<CaptureCallPanel {...defaultProps} />);

    const rawNoteInput = screen.getByLabelText("What did the customer tell you?");
    await user.type(rawNoteInput, "   ");

    const saveButton = screen.getByRole("button", { name: /Save/i });
    expect(saveButton).toBeDisabled();
    expect(mockCreateTrip).not.toHaveBeenCalled();
  });

  // Test 15: Follow-up due date is optional
  it("submits successfully without follow-up due date", async () => {
    const user = userEvent.setup();
    const mockCreateTrip = vi.mocked(apiClient.createTrip);
    mockCreateTrip.mockResolvedValue(mockTrip);

    render(<CaptureCallPanel {...defaultProps} />);

    const rawNoteInput = screen.getByLabelText("What did the customer tell you?");
    const followUpInput = screen.getByLabelText("Promise to follow up by:") as HTMLInputElement;

    await user.type(rawNoteInput, "Family wants Japan");

    // Clear the follow-up date
    fireEvent.change(followUpInput, { target: { value: "" } });

    const saveButton = screen.getByRole("button", { name: /Save/i });
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(mockCreateTrip).toHaveBeenCalledWith(
        expect.objectContaining({
          raw_note: "Family wants Japan",
        })
      );
    });

    await waitFor(() => {
      expect(defaultProps.onSave).toHaveBeenCalledWith(mockTrip);
    });
  });

  // Test 16: Cancel button is disabled while loading
  it("disables Cancel button while loading", async () => {
    const user = userEvent.setup();
    const mockCreateTrip = vi.mocked(apiClient.createTrip);

    let resolveRequest: (value: Trip) => void;
    const requestPromise = new Promise<Trip>((resolve) => {
      resolveRequest = resolve;
    });

    mockCreateTrip.mockReturnValue(requestPromise);

    render(<CaptureCallPanel {...defaultProps} />);

    const rawNoteInput = screen.getByLabelText("What did the customer tell you?");
    await user.type(rawNoteInput, "Test");

    const saveButton = screen.getByRole("button", { name: /Save/i });
    fireEvent.click(saveButton);

    await waitFor(() => {
      const cancelButton = screen.getByRole("button", { name: /Cancel/i });
      expect(cancelButton).toBeDisabled();
    });

    resolveRequest!(mockTrip);
  });
});
