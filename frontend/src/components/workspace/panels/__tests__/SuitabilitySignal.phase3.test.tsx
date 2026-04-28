import { describe, it, expect, vi } from "vitest";
import React from "react";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import { SuitabilitySignal, type SuitabilityFlagData } from "../SuitabilitySignal";

describe("SuitabilitySignal - Phase 3 Confidence & Tier Display", () => {
  describe("Confidence Percentage Display", () => {
    it("should display confidence as percentage (0-100%)", () => {
      const flags: SuitabilityFlagData[] = [
        {
          flag_type: "test_flag",
          severity: "critical",
          reason: "Test reason",
          confidence: 0.85,
          affected_travelers: ["Traveler"],
        },
      ];
      render(<SuitabilitySignal flags={flags} />);
      expect(screen.getByText("85% confidence")).toBeInTheDocument();
    });

    it("should handle confidence of 0%", () => {
      const flags: SuitabilityFlagData[] = [
        {
          flag_type: "test_flag",
          severity: "low",
          reason: "Test",
          confidence: 0,
          affected_travelers: [],
        },
      ];
      render(<SuitabilitySignal flags={flags} />);
      expect(screen.getByText("0% confidence")).toBeInTheDocument();
    });

    it("should handle confidence of 100%", () => {
      const flags: SuitabilityFlagData[] = [
        {
          flag_type: "test_flag",
          severity: "critical",
          reason: "Test",
          confidence: 1.0,
          affected_travelers: [],
        },
      ];
      render(<SuitabilitySignal flags={flags} />);
      expect(screen.getByText("100% confidence")).toBeInTheDocument();
    });

    it("should round confidence to nearest integer", () => {
      const flags: SuitabilityFlagData[] = [
        {
          flag_type: "test_flag",
          severity: "high",
          reason: "Test",
          confidence: 0.456,
          affected_travelers: [],
        },
      ];
      render(<SuitabilitySignal flags={flags} />);
      // Should round 0.456 to 46%
      expect(screen.getByText("46% confidence")).toBeInTheDocument();
    });

    it("should display confidence for all flags", () => {
      const flags: SuitabilityFlagData[] = [
        {
          flag_type: "flag1",
          severity: "critical",
          reason: "Critical issue",
          confidence: 0.95,
          affected_travelers: ["Traveler1"],
        },
        {
          flag_type: "flag2",
          severity: "high",
          reason: "High issue",
          confidence: 0.72,
          affected_travelers: ["Traveler2"],
        },
        {
          flag_type: "flag3",
          severity: "medium",
          reason: "Medium issue",
          confidence: 0.50,
          affected_travelers: ["Traveler3"],
        },
      ];
      render(<SuitabilitySignal flags={flags} />);
      expect(screen.getByText("95% confidence")).toBeInTheDocument();
      expect(screen.getByText("72% confidence")).toBeInTheDocument();
      expect(screen.getByText("50% confidence")).toBeInTheDocument();
    });
  });

  describe("Tier Classification Colors", () => {
    it("should classify critical as Tier 1 (red)", () => {
      const flags: SuitabilityFlagData[] = [
        {
          flag_type: "critical_flag",
          severity: "critical",
          reason: "Critical issue",
          confidence: 0.9,
          affected_travelers: [],
        },
      ];
      const { container } = render(<SuitabilitySignal flags={flags} />);
      // Check for Tier 1 section (red styling)
      expect(screen.getByText("Tier 1: Hard Blockers (Must Acknowledge Before Approval)")).toBeInTheDocument();
      // The flag container should have red styling
      const flagElement = container.querySelector('[data-testid="suitability-flag-critical_flag"]');
      expect(flagElement?.className).toContain("bg-red-50");
    });

    it("should classify high as Tier 1 (red)", () => {
      const flags: SuitabilityFlagData[] = [
        {
          flag_type: "high_flag",
          severity: "high",
          reason: "High issue",
          confidence: 0.8,
          affected_travelers: [],
        },
      ];
      const { container } = render(<SuitabilitySignal flags={flags} />);
      // High severity should still be in Tier 1 section
      expect(screen.getByText("Tier 1: Hard Blockers (Must Acknowledge Before Approval)")).toBeInTheDocument();
    });

    it("should classify medium as Tier 2 (blue)", () => {
      const flags: SuitabilityFlagData[] = [
        {
          flag_type: "medium_flag",
          severity: "medium",
          reason: "Medium issue",
          confidence: 0.7,
          affected_travelers: [],
        },
      ];
      const { container } = render(<SuitabilitySignal flags={flags} />);
      // Check for Tier 2 section
      expect(screen.getByText("Tier 2: Warnings (Review Recommended)")).toBeInTheDocument();
      const flagElement = container.querySelector('[data-testid="suitability-flag-medium_flag"]');
      expect(flagElement?.className).toContain("bg-blue-50");
    });

    it("should classify low as Tier 2 (gray)", () => {
      const flags: SuitabilityFlagData[] = [
        {
          flag_type: "low_flag",
          severity: "low",
          reason: "Low issue",
          confidence: 0.4,
          affected_travelers: [],
        },
      ];
      const { container } = render(<SuitabilitySignal flags={flags} />);
      expect(screen.getByText("Tier 2: Warnings (Review Recommended)")).toBeInTheDocument();
      const flagElement = container.querySelector('[data-testid="suitability-flag-low_flag"]');
      expect(flagElement?.className).toContain("bg-gray-50");
    });

    it("should apply correct badge colors by severity", () => {
      const flags: SuitabilityFlagData[] = [
        {
          flag_type: "critical_flag",
          severity: "critical",
          reason: "Critical",
          confidence: 0.9,
          affected_travelers: [],
        },
        {
          flag_type: "high_flag",
          severity: "high",
          reason: "High",
          confidence: 0.8,
          affected_travelers: [],
        },
        {
          flag_type: "medium_flag",
          severity: "medium",
          reason: "Medium",
          confidence: 0.7,
          affected_travelers: [],
        },
        {
          flag_type: "low_flag",
          severity: "low",
          reason: "Low",
          confidence: 0.6,
          affected_travelers: [],
        },
      ];
      const { container } = render(<SuitabilitySignal flags={flags} />);
      
      // Check that severity badges are rendered
      expect(screen.getByText("CRITICAL")).toBeInTheDocument();
      expect(screen.getByText("HIGH")).toBeInTheDocument();
      expect(screen.getByText("MEDIUM")).toBeInTheDocument();
      expect(screen.getByText("LOW")).toBeInTheDocument();
    });

    it("should maintain dark mode colors for Tier 1", () => {
      const flags: SuitabilityFlagData[] = [
        {
          flag_type: "critical_flag",
          severity: "critical",
          reason: "Critical",
          confidence: 0.9,
          affected_travelers: [],
        },
      ];
      const { container } = render(<SuitabilitySignal flags={flags} />);
      const flagElement = container.querySelector('[data-testid="suitability-flag-critical_flag"]');
      // Should have dark mode red background
      expect(flagElement?.className).toContain("dark:bg-red-950");
    });

    it("should maintain dark mode colors for Tier 2", () => {
      const flags: SuitabilityFlagData[] = [
        {
          flag_type: "medium_flag",
          severity: "medium",
          reason: "Medium",
          confidence: 0.7,
          affected_travelers: [],
        },
      ];
      const { container } = render(<SuitabilitySignal flags={flags} />);
      const flagElement = container.querySelector('[data-testid="suitability-flag-medium_flag"]');
      // Should have dark mode blue background
      expect(flagElement?.className).toContain("dark:bg-blue-950");
    });
  });

  describe("Phase 3 Display Requirements", () => {
    it("should display confidence % in flag summary", () => {
      const flags: SuitabilityFlagData[] = [
        {
          flag_type: "mobility_risk",
          severity: "critical",
          reason: "Elderly traveler with high-intensity activities",
          confidence: 0.85,
          affected_travelers: ["Senior"],
        },
      ];
      render(<SuitabilitySignal flags={flags} />);
      // Should show: "CRITICAL 85% confidence"
      expect(screen.getByText("CRITICAL")).toBeInTheDocument();
      expect(screen.getByText("85% confidence")).toBeInTheDocument();
    });

    it("should show affected travelers info", () => {
      const flags: SuitabilityFlagData[] = [
        {
          flag_type: "test_flag",
          severity: "critical",
          reason: "Test",
          confidence: 0.9,
          affected_travelers: ["Parent A", "Parent B"],
        },
      ];
      render(<SuitabilitySignal flags={flags} />);
      expect(screen.getByText("Parent A, Parent B")).toBeInTheDocument();
    });

    it("should show 'Multiple travelers' when none specified", () => {
      const flags: SuitabilityFlagData[] = [
        {
          flag_type: "test_flag",
          severity: "critical",
          reason: "Test",
          confidence: 0.9,
        },
      ];
      render(<SuitabilitySignal flags={flags} />);
      expect(screen.getByText("Multiple travelers")).toBeInTheDocument();
    });

    it("should display reason text for context", () => {
      const flags: SuitabilityFlagData[] = [
        {
          flag_type: "visa_risk",
          severity: "high",
          reason: "5 nationalities with limited processing time window",
          confidence: 0.72,
          affected_travelers: [],
        },
      ];
      render(<SuitabilitySignal flags={flags} />);
      expect(screen.getByText("5 nationalities with limited processing time window")).toBeInTheDocument();
    });

    it("should separate Tier 1 and Tier 2 sections clearly", () => {
      const flags: SuitabilityFlagData[] = [
        {
          flag_type: "critical_flag",
          severity: "critical",
          reason: "Critical issue",
          confidence: 0.9,
          affected_travelers: [],
        },
        {
          flag_type: "medium_flag",
          severity: "medium",
          reason: "Medium issue",
          confidence: 0.6,
          affected_travelers: [],
        },
      ];
      render(<SuitabilitySignal flags={flags} />);
      expect(screen.getByText("Tier 1: Hard Blockers (Must Acknowledge Before Approval)")).toBeInTheDocument();
      expect(screen.getByText("Tier 2: Warnings (Review Recommended)")).toBeInTheDocument();
    });

    it("should show operator acknowledgment requirement for Tier 1", () => {
      const flags: SuitabilityFlagData[] = [
        {
          flag_type: "critical_flag",
          severity: "critical",
          reason: "Critical",
          confidence: 0.9,
          affected_travelers: [],
        },
      ];
      render(<SuitabilitySignal flags={flags} />);
      expect(screen.getByText(/hard blocker.*require acknowledgment before approval/i)).toBeInTheDocument();
    });
  });
});
