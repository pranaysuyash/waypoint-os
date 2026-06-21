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
