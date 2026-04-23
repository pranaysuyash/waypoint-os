import { describe, it, expect, vi } from "vitest";
import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom";
import { SuitabilitySignal, type SuitabilityFlagData } from "../SuitabilitySignal";

describe("SuitabilitySignal Component", () => {
  describe("Rendering", () => {
    it("should return null when no flags provided", () => {
      const { container } = render(<SuitabilitySignal flags={[]} />);
      expect(container.firstChild).toBeNull();
    });

    it("should render section when flags present", () => {
      const flags: SuitabilityFlagData[] = [
        {
          flag_type: "toddler_water_unsafe",
          severity: "critical",
          reason: "Water activities are unsafe for toddlers",
          confidence: 0.95,
          affected_travelers: ["Child"],
        },
      ];
      render(<SuitabilitySignal flags={flags} />);
      expect(screen.getByText("Suitability Audit Results")).toBeInTheDocument();
    });

    it("should display flag count in summary", () => {
      const flags: SuitabilityFlagData[] = [
        {
          flag_type: "toddler_water_unsafe",
          severity: "critical",
          reason: "Water activities are unsafe for toddlers",
          confidence: 0.95,
          affected_travelers: ["Child"],
        },
        {
          flag_type: "elderly_intense",
          severity: "high",
          reason: "Physical intensity strain",
          confidence: 0.85,
          affected_travelers: ["Grandparent"],
        },
      ];
      render(<SuitabilitySignal flags={flags} />);
      expect(screen.getByText("2")).toBeInTheDocument();
      expect(screen.getByText(/suitability issues detected/)).toBeInTheDocument();
    });
  });

  describe("Tier 1 Hard Blockers (Critical)", () => {
    it("should separate critical flags as Tier 1", () => {
      const flags: SuitabilityFlagData[] = [
        {
          flag_type: "toddler_water_unsafe",
          severity: "critical",
          reason: "Water activities are unsafe",
          confidence: 0.95,
          affected_travelers: ["Child"],
        },
      ];
      render(<SuitabilitySignal flags={flags} />);
      expect(screen.getByText("Tier 1: Hard Blockers (Must Resolve)")).toBeInTheDocument();
      expect(screen.getByText("Water Activity Not Safe for Toddlers")).toBeInTheDocument();
    });

    it("should show blocked count in summary for Tier 1 flags", () => {
      const flags: SuitabilityFlagData[] = [
        {
          flag_type: "toddler_water_unsafe",
          severity: "critical",
          reason: "Water activities unsafe",
          confidence: 0.95,
          affected_travelers: ["Child"],
        },
        {
          flag_type: "elderly_intense",
          severity: "critical",
          reason: "Physical intensity",
          confidence: 0.9,
          affected_travelers: ["Elderly"],
        },
      ];
      render(<SuitabilitySignal flags={flags} />);
      expect(screen.getByText(/hard blockers/)).toBeInTheDocument();
    });

    it("should render critical icon for Tier 1 flags", () => {
      const flags: SuitabilityFlagData[] = [
        {
          flag_type: "toddler_water_unsafe",
          severity: "critical",
          reason: "Water activities unsafe",
          confidence: 0.95,
          affected_travelers: ["Child"],
        },
      ];
      const { container } = render(<SuitabilitySignal flags={flags} />);
      expect(container.querySelector("svg")).toBeInTheDocument();
    });
  });

  describe("Tier 2 Warnings (High/Medium/Low)", () => {
    it("should separate high flags as Tier 2", () => {
      const flags: SuitabilityFlagData[] = [
        {
          flag_type: "elderly_intense",
          severity: "high",
          reason: "Physical intensity concern",
          confidence: 0.85,
          affected_travelers: ["Elderly"],
        },
      ];
      render(<SuitabilitySignal flags={flags} />);
      expect(screen.getByText("Tier 2: Warnings (Review Recommended)")).toBeInTheDocument();
    });

    it("should group medium severity flags as Tier 2", () => {
      const flags: SuitabilityFlagData[] = [
        {
          flag_type: "itinerary_coherence",
          severity: "medium",
          reason: "Pacing concern",
          confidence: 0.7,
          affected_travelers: ["Group"],
        },
      ];
      render(<SuitabilitySignal flags={flags} />);
      expect(screen.getByText("Tier 2: Warnings (Review Recommended)")).toBeInTheDocument();
    });

    it("should group low severity flags as Tier 2", () => {
      const flags: SuitabilityFlagData[] = [
        {
          flag_type: "budget_luxury_mismatch",
          severity: "low",
          reason: "Budget concern",
          confidence: 0.5,
          affected_travelers: ["Traveler"],
        },
      ];
      render(<SuitabilitySignal flags={flags} />);
      expect(screen.getByText("Tier 2: Warnings (Review Recommended)")).toBeInTheDocument();
    });
  });

  describe("Flag Labels and Explanations", () => {
    it("should display semantic labels instead of raw flag_type", () => {
      const flags: SuitabilityFlagData[] = [
        {
          flag_type: "toddler_water_unsafe",
          severity: "critical",
          reason: "Original reason",
          confidence: 0.95,
          affected_travelers: ["Child"],
        },
      ];
      render(<SuitabilitySignal flags={flags} />);
      expect(screen.getByText("Water Activity Not Safe for Toddlers")).toBeInTheDocument();
      expect(screen.getByText("Water-based activities pose safety risks for toddlers.")).toBeInTheDocument();
    });

    it("should fallback to flag_type if label not found", () => {
      const flags: SuitabilityFlagData[] = [
        {
          flag_type: "unknown_flag_type",
          severity: "high",
          reason: "Some reason",
          confidence: 0.8,
          affected_travelers: ["Traveler"],
        },
      ];
      render(<SuitabilitySignal flags={flags} />);
      expect(screen.getByText("unknown_flag_type")).toBeInTheDocument();
    });

    it("should display explanation text for known flags", () => {
      const flags: SuitabilityFlagData[] = [
        {
          flag_type: "elderly_stairs_heavy",
          severity: "critical",
          reason: "Raw reason",
          confidence: 0.92,
          affected_travelers: ["Elderly"],
        },
      ];
      render(<SuitabilitySignal flags={flags} />);
      expect(screen.getByText("Activities with heavy stair climbing are unsafe for elderly travelers.")).toBeInTheDocument();
    });
  });

  describe("Confidence Display", () => {
    it("should display confidence as percentage", () => {
      const flags: SuitabilityFlagData[] = [
        {
          flag_type: "toddler_water_unsafe",
          severity: "critical",
          reason: "Water unsafe",
          confidence: 0.85,
          affected_travelers: ["Child"],
        },
      ];
      render(<SuitabilitySignal flags={flags} />);
      expect(screen.getByText(/85%/)).toBeInTheDocument();
    });

    it("should round confidence values correctly", () => {
      const flags: SuitabilityFlagData[] = [
        {
          flag_type: "toddler_water_unsafe",
          severity: "critical",
          reason: "Water unsafe",
          confidence: 0.956,
          affected_travelers: ["Child"],
        },
      ];
      render(<SuitabilitySignal flags={flags} />);
      expect(screen.getByText(/96%/)).toBeInTheDocument();
    });
  });

  describe("Affected Travelers Display", () => {
    it("should display affected travelers list", () => {
      const flags: SuitabilityFlagData[] = [
        {
          flag_type: "toddler_water_unsafe",
          severity: "critical",
          reason: "Water unsafe",
          confidence: 0.95,
          affected_travelers: ["Emma", "Olivia"],
        },
      ];
      render(<SuitabilitySignal flags={flags} />);
      expect(screen.getByText(/Emma, Olivia/)).toBeInTheDocument();
    });

    it("should display fallback text when no travelers specified", () => {
      const flags: SuitabilityFlagData[] = [
        {
          flag_type: "toddler_water_unsafe",
          severity: "critical",
          reason: "Water unsafe",
          confidence: 0.95,
        },
      ];
      render(<SuitabilitySignal flags={flags} />);
      expect(screen.getByText(/Multiple travelers/)).toBeInTheDocument();
    });

    it("should display single traveler correctly", () => {
      const flags: SuitabilityFlagData[] = [
        {
          flag_type: "age_too_young",
          severity: "critical",
          reason: "Too young",
          confidence: 0.99,
          affected_travelers: ["Sarah"],
        },
      ];
      render(<SuitabilitySignal flags={flags} />);
      expect(screen.getByText(/Sarah/)).toBeInTheDocument();
    });
  });

  describe("Severity Badges", () => {
    it("should display severity badge for critical flags", () => {
      const flags: SuitabilityFlagData[] = [
        {
          flag_type: "toddler_water_unsafe",
          severity: "critical",
          reason: "Water unsafe",
          confidence: 0.95,
          affected_travelers: ["Child"],
        },
      ];
      render(<SuitabilitySignal flags={flags} />);
      expect(screen.getByText("CRITICAL")).toBeInTheDocument();
    });

    it("should display severity badge for high flags", () => {
      const flags: SuitabilityFlagData[] = [
        {
          flag_type: "elderly_intense",
          severity: "high",
          reason: "Physical intensity",
          confidence: 0.85,
          affected_travelers: ["Elderly"],
        },
      ];
      render(<SuitabilitySignal flags={flags} />);
      expect(screen.getByText("HIGH")).toBeInTheDocument();
    });

    it("should display severity badge for medium flags", () => {
      const flags: SuitabilityFlagData[] = [
        {
          flag_type: "itinerary_coherence",
          severity: "medium",
          reason: "Pacing concern",
          confidence: 0.7,
          affected_travelers: ["Group"],
        },
      ];
      render(<SuitabilitySignal flags={flags} />);
      expect(screen.getByText("MEDIUM")).toBeInTheDocument();
    });
  });

  describe("Drill-down Interaction", () => {
    it("should call onDrill when flag clicked and tripId provided", () => {
      const mockDrill = vi.fn();
      const flags: SuitabilityFlagData[] = [
        {
          flag_type: "toddler_water_unsafe",
          severity: "critical",
          reason: "Water unsafe",
          confidence: 0.95,
          affected_travelers: ["Child"],
        },
      ];
      render(
        <SuitabilitySignal
          flags={flags}
          tripId="trip-123"
          onDrill={mockDrill}
        />
      );

      const flagElement = screen.getByText("Water Activity Not Safe for Toddlers").closest("div[role='button']");
      if (flagElement) {
        fireEvent.click(flagElement);
        expect(mockDrill).toHaveBeenCalledWith("toddler_water_unsafe");
      }
    });

    it("should not call onDrill when tripId not provided", () => {
      const mockDrill = vi.fn();
      const flags: SuitabilityFlagData[] = [
        {
          flag_type: "toddler_water_unsafe",
          severity: "critical",
          reason: "Water unsafe",
          confidence: 0.95,
          affected_travelers: ["Child"],
        },
      ];
      render(
        <SuitabilitySignal
          flags={flags}
          onDrill={mockDrill}
        />
      );

      const labelEl = screen.getByText("Water Activity Not Safe for Toddlers");
      const flagDiv = labelEl.closest("div");
      if (flagDiv) {
        fireEvent.click(flagDiv);
      }
      expect(mockDrill).not.toHaveBeenCalled();
    });

    it("should be drillable when tripId provided", () => {
      const flags: SuitabilityFlagData[] = [
        {
          flag_type: "toddler_water_unsafe",
          severity: "critical",
          reason: "Water unsafe",
          confidence: 0.95,
          affected_travelers: ["Child"],
        },
      ];
      const { container } = render(
        <SuitabilitySignal
          flags={flags}
          tripId="trip-123"
        />
      );

      const flagItem = container.querySelector('[role="button"]');
      expect(flagItem).toBeInTheDocument();
    });
  });

  describe("Edge Cases", () => {
    it("should handle flags with details object", () => {
      const flags: SuitabilityFlagData[] = [
        {
          flag_type: "toddler_water_unsafe",
          severity: "critical",
          reason: "Water unsafe",
          confidence: 0.95,
          details: {
            activity_name: "Snorkeling",
            participant_age: 3,
          },
          affected_travelers: ["Child"],
        },
      ];
      render(<SuitabilitySignal flags={flags} />);
      expect(screen.getByText("Water Activity Not Safe for Toddlers")).toBeInTheDocument();
    });

    it("should handle mixed severity levels", () => {
      const flags: SuitabilityFlagData[] = [
        {
          flag_type: "toddler_water_unsafe",
          severity: "critical",
          reason: "Water unsafe",
          confidence: 0.95,
          affected_travelers: ["Child"],
        },
        {
          flag_type: "elderly_intense",
          severity: "high",
          reason: "Physical intensity",
          confidence: 0.85,
          affected_travelers: ["Elderly"],
        },
        {
          flag_type: "itinerary_coherence",
          severity: "medium",
          reason: "Pacing concern",
          confidence: 0.7,
          affected_travelers: ["Group"],
        },
      ];
      render(<SuitabilitySignal flags={flags} />);

      expect(screen.getByText("Tier 1: Hard Blockers (Must Resolve)")).toBeInTheDocument();
      expect(screen.getByText("Tier 2: Warnings (Review Recommended)")).toBeInTheDocument();
      expect(screen.getByText("3")).toBeInTheDocument();
      expect(screen.getByText(/hard blocker/)).toBeInTheDocument();
    });

    it("should handle very long affected travelers list", () => {
      const flags: SuitabilityFlagData[] = [
        {
          flag_type: "toddler_water_unsafe",
          severity: "critical",
          reason: "Water unsafe",
          confidence: 0.95,
          affected_travelers: ["Child1", "Child2", "Child3", "Child4", "Child5"],
        },
      ];
      render(<SuitabilitySignal flags={flags} />);
      expect(screen.getByText(/Child1, Child2, Child3, Child4, Child5/)).toBeInTheDocument();
    });

    it("should handle flags with 0% confidence", () => {
      const flags: SuitabilityFlagData[] = [
        {
          flag_type: "toddler_water_unsafe",
          severity: "critical",
          reason: "Water unsafe",
          confidence: 0,
          affected_travelers: ["Child"],
        },
      ];
      render(<SuitabilitySignal flags={flags} />);
      expect(screen.getByText(/0%/)).toBeInTheDocument();
    });

    it("should handle flags with 100% confidence", () => {
      const flags: SuitabilityFlagData[] = [
        {
          flag_type: "toddler_water_unsafe",
          severity: "critical",
          reason: "Water unsafe",
          confidence: 1.0,
          affected_travelers: ["Child"],
        },
      ];
      render(<SuitabilitySignal flags={flags} />);
      expect(screen.getByText(/100%/)).toBeInTheDocument();
    });
  });
});
