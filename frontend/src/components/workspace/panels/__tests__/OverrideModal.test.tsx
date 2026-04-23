import { describe, it, expect, vi } from "vitest";
import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import { OverrideModal } from "../../modals/OverrideModal";
import { SuitabilityPanel } from "../SuitabilityPanel";

describe("OverrideModal (panel-linked coverage)", () => {
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

  it("renders modal content with flag metadata", () => {
    render(<OverrideModal {...defaultProps} />);

    expect(screen.getByText("Override Risk Flag")).toBeInTheDocument();
    expect(screen.getByText(/toddler water unsafe/i)).toBeInTheDocument();
    expect(screen.getByText("CRITICAL")).toBeInTheDocument();
  });

  it("enforces minimum reason length before submit", () => {
    render(<OverrideModal {...defaultProps} />);

    const textarea = screen.getByPlaceholderText(/minimum 10 characters/i);
    const submitButton = screen.getByRole("button", { name: /Submit Override/i });

    fireEvent.change(textarea, { target: { value: "short" } });
    expect(submitButton).toBeDisabled();

    fireEvent.change(textarea, { target: { value: "Owner approved after manual review" } });
    expect(submitButton).not.toBeDisabled();
  });

  it("submits a valid override request payload", async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    const onClose = vi.fn();

    render(<OverrideModal {...defaultProps} onSubmit={onSubmit} onClose={onClose} />);

    fireEvent.change(screen.getByPlaceholderText(/minimum 10 characters/i), {
      target: { value: "Owner approved after discussing with customer" },
    });

    fireEvent.click(screen.getByRole("button", { name: /Submit Override/i }));

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith(
        expect.objectContaining({
          flag: "toddler_water_unsafe",
          action: "suppress",
          overridden_by: "agent-1",
          scope: "this_trip",
          original_severity: "critical",
        })
      );
    });

    await waitFor(() => {
      expect(onClose).toHaveBeenCalledTimes(1);
    });
  });
});

describe("SuitabilityPanel override controls", () => {
  const criticalFlags = [
    {
      flag: "toddler_water_unsafe",
      flag_type: "toddler_water_unsafe",
      severity: "critical" as const,
      reason: "Water activities unsafe for toddlers",
      confidence: 0.95,
    },
  ];

  it("shows override action for critical flags when tripId is present", () => {
    render(<SuitabilityPanel flags={criticalFlags} tripId="trip-123" />);

    expect(screen.getByText("Override")).toBeInTheDocument();
  });

  it("hides override action when tripId is not provided", () => {
    render(<SuitabilityPanel flags={criticalFlags} />);

    expect(screen.queryByText("Override")).not.toBeInTheDocument();
  });
});
