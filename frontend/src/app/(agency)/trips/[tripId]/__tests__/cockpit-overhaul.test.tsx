import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { TripContextProvider } from "@/contexts/TripContext";
import { SafetyPanel } from "@/components/workspace/panels/SafetyPanel";
import { PacketPanel } from "@/components/workspace/panels/PacketPanel";
import { formatBlockerLabel, formatPacketAuthority, formatPacketValue } from "@/lib/label-maps";
import type { Trip } from "@/lib/api-client";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  usePathname: () => "/trips/trip_test_001/followups",
  useParams: () => ({ tripId: "trip_test_001" }),
}));

const sampleTrip = {
  id: "trip_test_001",
  destination: "Dubai",
  origin: "Delhi",
  dateWindow: "2026-12-20 to 2026-12-28",
  party: 4,
  budget: "INR 6-7 Lakhs",
  tripPurpose: "family leisure",
  status: "incomplete",
  stage: "discovery",
  safety: {
    strict_leakage: false,
    leakage_passed: true,
    leakage_errors: [],
  },
  traveler_bundle: {
    system_context: "",
    user_message: "We have drafted options for your Dubai family trip.",
    follow_up_sequence: [],
    branch_prompts: [],
    constraints: [],
    audience: "traveler",
  },
  packet: {
    packet_id: "pkt_1",
    facts: {
      destination_status: { value: "semi_open", confidence: 0.8, authority_level: "explicit_user" },
      party_composition: { value: { adults: 2, children: 2 }, confidence: 0.85, authority_level: "derived_signal" },
      traveler_plan: { value: "nothing_booked", confidence: 0.85, authority_level: "explicit_user" },
    },
    derived_signals: {
      domestic_or_international: { value: "international", confidence: 0.9 },
      internal_data_present: { value: true, confidence: 1 },
      sourcing_path: { value: "open_market", confidence: 0.7 },
    },
    assumptions: [],
    ambiguities: [],
    unknowns: [],
    contradictions: [],
  },
} as unknown as Trip;

describe("Trip Workspace Cockpit Overhaul", () => {
  beforeEach(() => {
    vi.unstubAllEnvs();
  });

  it("SafetyPanel falls back to persisted trip.safety from TripContext and hides debug env banner", () => {
    render(
      <TripContextProvider
        value={{
          tripId: "trip_test_001",
          trip: sampleTrip,
          isLoading: false,
          error: null,
          refetchTrip: vi.fn(),
          replaceTrip: vi.fn(),
        }}
      >
        <SafetyPanel tripId="trip_test_001" />
      </TripContextProvider>,
    );

    expect(screen.getByText(/Message review/i)).toBeInTheDocument();
    expect(screen.getByText("We have drafted options for your Dubai family trip.")).toBeInTheDocument();
    expect(screen.queryByText(/NEXT_PUBLIC_ALLOW_DEBUG_JSON/)).not.toBeInTheDocument();
  });

  it("PacketPanel humanizes values, authorities, objects, and suppresses internal_data_present", () => {
    render(<PacketPanel trip={sampleTrip} tripId="trip_test_001" />);

    expect(screen.getByText("Semi-open")).toBeInTheDocument();
    expect(screen.getByText("2 adults, 2 children")).toBeInTheDocument();
    expect(screen.getByText("Nothing booked yet")).toBeInTheDocument();
    expect(screen.getAllByText("Client stated").length).toBeGreaterThan(0);
    expect(screen.getAllByText("System inferred").length).toBeGreaterThan(0);
    expect(screen.getByText("Open market (70%)")).toBeInTheDocument();
    expect(screen.queryByText("Internal Data Present")).not.toBeInTheDocument();
    expect(screen.queryByText(/NEXT_PUBLIC_ALLOW_DEBUG_JSON/)).not.toBeInTheDocument();
  });

  it("humanizes blocker codes and packet helpers cleanly", () => {
    expect(formatBlockerLabel("extraction_quality")).toBe("Required trip details are still incomplete");
    expect(formatPacketAuthority("explicit_user")).toBe("Client stated");
    expect(formatPacketValue({ adults: 2, children: 1 })).toBe("2 adults, 1 children");
  });
});
