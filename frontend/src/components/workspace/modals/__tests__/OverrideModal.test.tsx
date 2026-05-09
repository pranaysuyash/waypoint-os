import { describe, it, expect, vi } from "vitest";
import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";
import { OverrideModal } from "../OverrideModal";

describe("OverrideModal", () => {
  const defaultProps = {
    isOpen: true,
    flag: {
      flag: "toddler_water_unsafe",
      severity: "critical",
      reason: "Water activities unsafe for toddlers",
    },
    tripId: "trip-123",
    userId: "agent-1",
    onClose: vi.fn(),
    onSubmit: vi.fn().mockResolvedValue(undefined),
  };

  it("renders modal with flag info when open", () => {
    render(<OverrideModal {...defaultProps} />);

    expect(screen.getByText("Override Risk Flag")).toBeInTheDocument();
    expect(screen.getByText(/toddler water unsafe/)).toBeInTheDocument();
    expect(screen.getByText("CRITICAL")).toBeInTheDocument();
  });

  it("does not render when closed", () => {
    render(<OverrideModal {...defaultProps} isOpen={false} />);
    expect(screen.queryByText("Override Risk Flag")).not.toBeInTheDocument();
  });

  it("validates minimum 10 characters for reason", async () => {
    render(<OverrideModal {...defaultProps} />);

    const textarea = screen.getByPlaceholderText(/minimum 10 characters/);
    fireEvent.change(textarea, { target: { value: "short" } });

    const submitButton = screen.getByText("Submit Override");
    expect(submitButton).toBeDisabled();

    fireEvent.change(textarea, { target: { value: "This is a valid reason for override" } });
    expect(submitButton).not.toBeDisabled();
  });

  it("shows severity dropdown for downgrade action", () => {
    render(<OverrideModal {...defaultProps} />);

    const downgradeRadio = screen.getByText("Downgrade");
    fireEvent.click(downgradeRadio);

    expect(screen.getByText(/Downgrade to/)).toBeInTheDocument();
    expect(screen.getByText(`Must be lower than current severity (critical)`)).toBeInTheDocument();
  });

  it("enables appropriate fields based on action selection", () => {
    render(<OverrideModal {...defaultProps} />);

    const suppressRadio = screen.getByLabelText(/Suppress/);
    const acknowledgeRadio = screen.getByLabelText(/Acknowledge/);

    expect(suppressRadio).toBeChecked();

    fireEvent.click(acknowledgeRadio);
    expect(acknowledgeRadio).toBeChecked();
    expect(screen.queryByText(/Downgrade to/)).not.toBeInTheDocument();
  });

  it("calls onClose when cancel is clicked", () => {
    const onClose = vi.fn();
    render(<OverrideModal {...defaultProps} onClose={onClose} />);

    const cancelButton = screen.getByText("Cancel");
    fireEvent.click(cancelButton);

    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("submits valid override and calls onSubmit", async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    const onClose = vi.fn();
    render(<OverrideModal {...defaultProps} onSubmit={onSubmit} onClose={onClose} />);

    const textarea = screen.getByPlaceholderText(/minimum 10 characters/);
    fireEvent.change(textarea, { target: { value: "Owner confirmed safe to proceed" } });

    const submitButton = screen.getByText("Submit Override");
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith(
        expect.objectContaining({
          flag: "toddler_water_unsafe",
          action: "suppress",
          reason: "Owner confirmed safe to proceed",
          overridden_by: "agent-1",
          scope: "this_trip",
          original_severity: "critical",
        })
      );
    });

    await waitFor(() => {
      expect(onClose).toHaveBeenCalled();
    });
  });

  it("validates downgrade requires a lower severity", async () => {
    render(<OverrideModal {...defaultProps} />);

    fireEvent.click(screen.getByText("Downgrade"));

    const textarea = screen.getByPlaceholderText(/minimum 10 characters/);
    fireEvent.change(textarea, { target: { value: "Valid reason text here" } });

    const select = screen.getByDisplayValue("Select severity…");
    fireEvent.change(select, { target: { value: "high" } });

    const submitButton = screen.getByText("Submit Override");
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/Submit Override/i).closest("button")).not.toBeDisabled();
    });
  });
});

describe("SuitabilityPanel Override Controls", () => {
  it("shows override button for critical flags when tripId provided", async () => {
    const { SuitabilityPanel } = await import("../../panels/SuitabilityPanel");
    const flags = [
      {
        flag: "test_critical",
        flag_type: "test_critical",
        severity: "critical" as const,
        reason: "Critical issue",
        confidence: 0.95,
      },
    ];

    render(<SuitabilityPanel flags={flags} tripId="trip-123" />);

    expect(screen.getByText("Override")).toBeInTheDocument();
  });

  it("does not show override button without tripId", async () => {
    const { SuitabilityPanel } = await import("../../panels/SuitabilityPanel");
    const flags = [
      {
        flag: "test_critical",
        flag_type: "test_critical",
        severity: "critical" as const,
        reason: "Critical issue",
        confidence: 0.95,
      },
    ];

    render(<SuitabilityPanel flags={flags} />);

    expect(screen.queryByText("Override")).not.toBeInTheDocument();
  });
});
