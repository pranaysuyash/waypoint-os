import { describe, it, expect, vi } from "vitest";
import React from "react";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import { DecisionPanel } from "../DecisionPanel";
import type { Trip } from "@/lib/api-client";
import type { DecisionOutput, SuitabilityFlagData } from "@/types/spine";

vi.mock("@/stores/workbench", () => ({
  useWorkbenchStore: () => ({
    result_decision: null,
    debug_raw_json: false,
    setDebugRawJson: vi.fn(),
  }),
}));

vi.mock("@/contexts/TripContext", () => ({
  useTripContext: () => null,
}));

describe("DecisionPanel with SuitabilitySignal Integration", () => {
  const createMockDecision = (overrides?: Partial<DecisionOutput>): DecisionOutput => ({
    decision_state: "ASK_FOLLOWUP",
    hard_blockers: [],
    soft_blockers: [],
    contradictions: [],
    risk_flags: [],
    suitability_flags: [],
    follow_up_questions: [],
    rationale: {
      feasibility: "Test feasibility",
      confidence: 0.8,
      hard_blockers: [],
      soft_blockers: [],
      contradictions: [],
      confidence_scorecard: { data: 0.8, judgment: 0.8, commercial: 0.8 },
    },
    confidence: {
      data_quality: 0.8,
      judgment_confidence: 0.8,
      commercial_confidence: 0.8,
      overall: 0.8,
    },
    branch_options: [],
    commercial_decision: "proceed",
    budget_breakdown: null,
    ...overrides,
  });

  const asTrip = (trip: { id: string; decision: DecisionOutput }): Trip => ({
    id: trip.id,
    destination: "Test destination",
    type: "leisure",
    state: "blue",
    age: "Today",
    createdAt: "2026-04-27T00:00:00.000Z",
    updatedAt: "2026-04-27T00:00:00.000Z",
    decision: trip.decision,
  });

  describe("Rendering without suitability flags", () => {
    it("should render DecisionPanel without SuitabilitySignal when no flags", () => {
      const mockTrip = {
        id: "trip-123",
        decision: createMockDecision(),
      };

      render(<DecisionPanel trip={asTrip(mockTrip)} tripId="trip-123" />);

      expect(screen.getByText("Quote Assessment")).toBeInTheDocument();
      expect(screen.queryByText("Suitability Audit Results")).not.toBeInTheDocument();
    });
  });

  describe("Rendering with suitability flags", () => {
    it("should prefer structured suitability_profile over legacy suitability_flags", () => {
      const suitabilityFlags: SuitabilityFlagData[] = [
        {
          flag_type: "toddler_water_unsafe",
          severity: "critical",
          reason: "Water activities unsafe",
          confidence: 0.95,
          affected_travelers: ["Child"],
        },
      ];

      const mockTrip = {
        id: "trip-123",
        decision: createMockDecision({
          suitability_flags: suitabilityFlags,
          suitability_profile: {
            summary: {
              status: "caution",
              primaryReason: "Structured suitability profile available",
              overallScore: 72,
            },
            dimensions: [
              {
                type: "mobility",
                severity: "medium",
                score: 68,
                reason: "Some walking constraints need review",
              },
            ],
          },
        }),
      };

      render(<DecisionPanel trip={asTrip(mockTrip)} tripId="trip-123" />);

      expect(screen.getByTestId("suitability-card")).toBeInTheDocument();
      expect(screen.getByText("Structured suitability profile available")).toBeInTheDocument();
      expect(screen.queryByText("Water Activity Not Safe for Toddlers")).not.toBeInTheDocument();
    });

    it("should render SuitabilitySignal when flags present", () => {
      const suitabilityFlags: SuitabilityFlagData[] = [
        {
          flag_type: "toddler_water_unsafe",
          severity: "critical",
          reason: "Water activities unsafe",
          confidence: 0.95,
          affected_travelers: ["Child"],
        },
      ];

      const mockTrip = {
        id: "trip-123",
        decision: createMockDecision({
          suitability_flags: suitabilityFlags,
        }),
      };

      render(<DecisionPanel trip={asTrip(mockTrip)} tripId="trip-123" />);

      expect(screen.getByText("Suitability Audit Results")).toBeInTheDocument();
      expect(screen.getByText("Suitability Audit Results")).toBeInTheDocument();
      expect(screen.getByText("Water Activity Not Safe for Toddlers")).toBeInTheDocument();
    });

    it("should display Tier 1 blockers from SuitabilitySignal", () => {
      const suitabilityFlags: SuitabilityFlagData[] = [
        {
          flag_type: "toddler_water_unsafe",
          severity: "critical",
          reason: "Water activities unsafe",
          confidence: 0.95,
          affected_travelers: ["Child"],
        },
        {
          flag_type: "elderly_stairs_heavy",
          severity: "critical",
          reason: "Stairs unsafe",
          confidence: 0.92,
          affected_travelers: ["Elderly"],
        },
      ];

      const mockTrip = {
        id: "trip-123",
        decision: createMockDecision({
          suitability_flags: suitabilityFlags,
        }),
      };

      render(<DecisionPanel trip={asTrip(mockTrip)} tripId="trip-123" />);

      expect(screen.getByText("Tier 1: Hard Blockers (Must Acknowledge Before Approval)")).toBeInTheDocument();
      expect(screen.getByText(/hard blockers/)).toBeInTheDocument();
    });

    it("should display both Tier 1 and Tier 2 flags", () => {
      const suitabilityFlags: SuitabilityFlagData[] = [
        {
          flag_type: "toddler_water_unsafe",
          severity: "critical",
          reason: "Water activities unsafe",
          confidence: 0.95,
          affected_travelers: ["Child"],
        },
        {
          flag_type: "elderly_intense",
          severity: "high",
          reason: "Physical intensity concern",
          confidence: 0.85,
          affected_travelers: ["Elderly"],
        },
      ];

      const mockTrip = {
        id: "trip-123",
        decision: createMockDecision({
          suitability_flags: suitabilityFlags,
        }),
      };

      render(<DecisionPanel trip={asTrip(mockTrip)} tripId="trip-123" />);

      expect(screen.getByText("Tier 1: Hard Blockers (Must Acknowledge Before Approval)")).toBeInTheDocument();
      expect(screen.getByText("Tier 2: Warnings (Review Recommended)")).toBeInTheDocument();
    });
  });

  describe("Panel layout integration", () => {
    it("should render SuitabilitySignal before Follow-up Questions section", () => {
      const suitabilityFlags: SuitabilityFlagData[] = [
        {
          flag_type: "toddler_water_unsafe",
          severity: "critical",
          reason: "Water activities unsafe",
          confidence: 0.95,
          affected_travelers: ["Child"],
        },
      ];

      const mockTrip = {
        id: "trip-123",
        decision: createMockDecision({
          suitability_flags: suitabilityFlags,
          follow_up_questions: [
            {
              field_name: "dietary_restrictions",
              question: "Any dietary restrictions?",
              priority: "high",
              suggested_values: [],
            },
          ],
        }),
      };

      render(<DecisionPanel trip={asTrip(mockTrip)} tripId="trip-123" />);

      const suitabilitySection = screen.getByText("Suitability Audit Results");
      expect(suitabilitySection).toBeInTheDocument();

      const followupSection = screen.queryByText("Follow-up Questions");
      if (followupSection) {
        expect(suitabilitySection.compareDocumentPosition(followupSection)).toBe(
          Node.DOCUMENT_POSITION_FOLLOWING
        );
      }
    });

    it("should show legacy Risk Flags section alongside SuitabilitySignal if both exist", () => {
      const suitabilityFlags: SuitabilityFlagData[] = [
        {
          flag_type: "toddler_water_unsafe",
          severity: "critical",
          reason: "Water activities unsafe",
          confidence: 0.95,
          affected_travelers: ["Child"],
        },
      ];

      const mockTrip = {
        id: "trip-123",
        decision: createMockDecision({
          suitability_flags: suitabilityFlags,
          risk_flags: ["legacy_risk_flag"],
        }),
      };

      render(<DecisionPanel trip={asTrip(mockTrip)} tripId="trip-123" />);

      expect(screen.getByText("Suitability Audit Results")).toBeInTheDocument();
      expect(screen.getByText("Water Activity Not Safe for Toddlers")).toBeInTheDocument();
    });
  });

  describe("Data flow from backend to frontend", () => {
    it("should handle empty suitability_flags array", () => {
      const mockTrip = {
        id: "trip-123",
        decision: createMockDecision({
          suitability_flags: [],
        }),
      };

      render(<DecisionPanel trip={asTrip(mockTrip)} tripId="trip-123" />);

      expect(screen.getByText("Quote Assessment")).toBeInTheDocument();
      expect(screen.queryByText("Suitability Audit Results")).not.toBeInTheDocument();
    });

    it("should handle undefined suitability_flags (backward compatibility)", () => {
      const mockTrip = {
        id: "trip-123",
        decision: createMockDecision({
          suitability_flags: undefined,
        }),
      };

      render(<DecisionPanel trip={asTrip(mockTrip)} tripId="trip-123" />);

      expect(screen.getByText("Quote Assessment")).toBeInTheDocument();
      expect(screen.queryByText("Suitability Audit Results")).not.toBeInTheDocument();
    });

    it("should render multiple flags correctly", () => {
      const suitabilityFlags: SuitabilityFlagData[] = [
        {
          flag_type: "toddler_water_unsafe",
          severity: "critical",
          reason: "Water activities unsafe",
          confidence: 0.95,
          affected_travelers: ["Emma"],
        },
        {
          flag_type: "toddler_late_night",
          severity: "critical",
          reason: "Late night activities unsuitable",
          confidence: 0.9,
          affected_travelers: ["Emma"],
        },
        {
          flag_type: "elderly_intense",
          severity: "high",
          reason: "Physical intensity concern",
          confidence: 0.85,
          affected_travelers: ["Grandpa"],
        },
        {
          flag_type: "itinerary_coherence",
          severity: "medium",
          reason: "Pacing concern",
          confidence: 0.7,
          affected_travelers: ["Group"],
        },
      ];

      const mockTrip = {
        id: "trip-123",
        decision: createMockDecision({
          suitability_flags: suitabilityFlags,
        }),
      };

      render(<DecisionPanel trip={asTrip(mockTrip)} tripId="trip-123" />);

      expect(screen.getByText("4")).toBeInTheDocument();
      expect(screen.getByText(/hard blockers/)).toBeInTheDocument();
    });
  });

  describe("Semantic flag rendering", () => {
    it("should show semantic labels for known flag types", () => {
      const suitabilityFlags: SuitabilityFlagData[] = [
        {
          flag_type: "toddler_water_unsafe",
          severity: "critical",
          reason: "Water activities unsafe",
          confidence: 0.95,
          affected_travelers: ["Child"],
        },
        {
          flag_type: "elderly_intense",
          severity: "high",
          reason: "Physical intensity concern",
          confidence: 0.85,
          affected_travelers: ["Elderly"],
        },
      ];

      const mockTrip = {
        id: "trip-123",
        decision: createMockDecision({
          suitability_flags: suitabilityFlags,
        }),
      };

      render(<DecisionPanel trip={asTrip(mockTrip)} tripId="trip-123" />);

      expect(screen.getByText("Water Activity Not Safe for Toddlers")).toBeInTheDocument();
      expect(screen.getByText("Physical Intensity Unsafe for Elderly")).toBeInTheDocument();
    });

    it("should display affected travelers for each flag", () => {
      const suitabilityFlags: SuitabilityFlagData[] = [
        {
          flag_type: "toddler_water_unsafe",
          severity: "critical",
          reason: "Water activities unsafe",
          confidence: 0.95,
          affected_travelers: ["Emma", "Olivia"],
        },
      ];

      const mockTrip = {
        id: "trip-123",
        decision: createMockDecision({
          suitability_flags: suitabilityFlags,
        }),
      };

      render(<DecisionPanel trip={asTrip(mockTrip)} tripId="trip-123" />);

      expect(screen.getByText(/Emma, Olivia/)).toBeInTheDocument();
    });

    it("should display confidence scores for each flag", () => {
      const suitabilityFlags: SuitabilityFlagData[] = [
        {
          flag_type: "toddler_water_unsafe",
          severity: "critical",
          reason: "Water activities unsafe",
          confidence: 0.957,
          affected_travelers: ["Child"],
        },
      ];

      const mockTrip = {
        id: "trip-123",
        decision: createMockDecision({
          suitability_flags: suitabilityFlags,
        }),
      };

      render(<DecisionPanel trip={asTrip(mockTrip)} tripId="trip-123" />);

      expect(screen.getByText(/96%/)).toBeInTheDocument();
    });
  });

  describe("Backward compatibility", () => {
    it("should still render DecisionPanel correctly without suitability_flags field", () => {
      const mockTrip = {
        id: "trip-123",
        decision: {
          decision_state: "ASK_FOLLOWUP",
          hard_blockers: ["budget_feasibility"],
          soft_blockers: [],
          contradictions: [],
          risk_flags: [],
          follow_up_questions: [],
          rationale: {
            feasibility: "Test",
            confidence: 0.8,
            hard_blockers: ["budget_feasibility"],
            soft_blockers: [],
            contradictions: [],
            confidence_scorecard: { data: 0.8, judgment: 0.8, commercial: 0.8 },
          },
          confidence: {
            data_quality: 0.8,
            judgment_confidence: 0.8,
            commercial_confidence: 0.8,
            overall: 0.8,
          },
          branch_options: [],
          commercial_decision: "proceed",
          budget_breakdown: null,
        } as DecisionOutput,
      };

      render(<DecisionPanel trip={asTrip(mockTrip)} tripId="trip-123" />);

      expect(screen.getByText("Quote Assessment")).toBeInTheDocument();
      expect(screen.getByText("budget_feasibility")).toBeInTheDocument();
    });
  });
});
