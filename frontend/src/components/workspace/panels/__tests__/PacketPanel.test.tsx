import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { PacketPanel } from "../PacketPanel";
import type { Trip } from "@/lib/api-client";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ refresh: vi.fn() }),
}));

vi.mock("@/stores/workbench", () => ({
  useWorkbenchStore: () => ({
    result_packet: null,
    result_validation: null,
    debug_raw_json: false,
    setDebugRawJson: vi.fn(),
  }),
}));

describe("PacketPanel trip details fallback", () => {
  it("surfaces operator-critical priorities and date flexibility", () => {
    const trip: Trip = {
      id: "trip-priorities-visible",
      destination: "Singapore",
      type: "Family leisure",
      state: "green",
      age: "1h",
      createdAt: "2026-05-27T00:00:00Z",
      updatedAt: "2026-05-27T00:00:00Z",
      party: 4,
      dateWindow: "Dec 2026",
      budget: "₹4L",
      origin: "Bengaluru",
      tripPriorities: "Kid-friendly hotel, direct flights, beach access",
      dateFlexibility: "moderate",
    };

    render(<PacketPanel tripId={trip.id} trip={trip} />);

    expect(screen.getByText("Date flexibility")).toBeInTheDocument();
    expect(screen.getByText("moderate")).toBeInTheDocument();
    expect(screen.getByText("Priorities")).toBeInTheDocument();
    expect(screen.getByText("Kid-friendly hotel, direct flights, beach access")).toBeInTheDocument();
  });

  it("shows trip purpose in the summary cards when packet data includes it", () => {
    const trip: Trip = {
      id: "trip-purpose-visible",
      destination: "Goa",
      type: "Family leisure",
      state: "green",
      age: "1h",
      createdAt: "2026-05-27T00:00:00Z",
      updatedAt: "2026-05-27T00:00:00Z",
      party: 2,
      dateWindow: "Aug 2026",
      budget: "₹2.5L",
      origin: "Mumbai",
      packet: {
        facts: {
          trip_purpose: {
            value: "honeymoon",
            confidence: 0.8,
            authority_level: "customer",
            extraction_mode: "direct",
            derived_from: [],
          },
        },
        derived_signals: {},
        unknowns: [],
        ambiguities: [],
        contradictions: [],
      } as never,
    };

    render(<PacketPanel tripId={trip.id} trip={trip} />);

    expect(screen.getByText("Purpose")).toBeInTheDocument();
    expect(screen.getAllByText("honeymoon").length).toBeGreaterThan(0);
  });

  it("falls back to the trip-level purpose when packet facts do not include it", () => {
    const trip: Trip = {
      id: "trip-purpose-fallback",
      destination: "Zanzibar",
      type: "Family leisure",
      tripPurpose: "family holiday",
      state: "green",
      age: "1h",
      createdAt: "2026-05-27T00:00:00Z",
      updatedAt: "2026-05-27T00:00:00Z",
      party: 3,
      dateWindow: "Jan 2026",
      budget: "$4,500 - $5,500",
      origin: "Nairobi",
      packet: {
        facts: {},
        derived_signals: {},
        unknowns: [],
        ambiguities: [],
        contradictions: [],
      } as never,
    };

    render(<PacketPanel tripId={trip.id} trip={trip} />);

    expect(screen.getByText("Purpose")).toBeInTheDocument();
    expect(screen.getByText("family holiday")).toBeInTheDocument();
  });

  it("shows group logistics when rooming and procurement signals are captured", () => {
    const trip: Trip = {
      id: "trip-group-logistics",
      destination: "Singapore",
      type: "Corporate group",
      state: "green",
      age: "1h",
      createdAt: "2026-05-27T00:00:00Z",
      updatedAt: "2026-05-27T00:00:00Z",
      party: 18,
      dateWindow: "Oct 2026",
      budget: "USD 42,000",
      origin: "Nairobi",
      packet: {
        facts: {
          rooming_list_count: {
            value: 2,
            confidence: 0.9,
            authority_level: "customer",
            extraction_mode: "direct",
            derived_from: [],
          },
          procurement_share_needed: {
            value: true,
            confidence: 0.85,
            authority_level: "customer",
            extraction_mode: "direct",
            derived_from: [],
          },
        },
        derived_signals: {},
        unknowns: [],
        ambiguities: [],
        contradictions: [],
      } as never,
    };

    render(<PacketPanel tripId={trip.id} trip={trip} />);

    expect(screen.getByText("Group Logistics")).toBeInTheDocument();
    expect(screen.getByText(/2 rooming lists/)).toBeInTheDocument();
    expect(screen.getByText(/Shareable with procurement/)).toBeInTheDocument();
  });

  it("treats any concrete origin value as manual instead of special-casing a city name", () => {
    const trip: Trip = {
      id: "trip-origin-label",
      destination: "TBD",
      type: "Family leisure",
      state: "green",
      age: "1h",
      createdAt: "2026-05-27T00:00:00Z",
      updatedAt: "2026-05-27T00:00:00Z",
      origin: "Patna",
    };

    render(<PacketPanel tripId={trip.id} trip={trip} />);

    expect(screen.getByText("Origin")).toBeInTheDocument();
    expect(screen.getByText("Patna")).toBeInTheDocument();
    expect(screen.getByText("Manual")).toBeInTheDocument();
  });
});
