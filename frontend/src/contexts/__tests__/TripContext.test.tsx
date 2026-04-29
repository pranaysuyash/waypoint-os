import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { TripContextProvider, useTripContext } from "@/contexts/TripContext";
import type { Trip } from "@/lib/api-client";

function ReadTripContext() {
  const { tripId, trip } = useTripContext();
  return (
    <div>
      <span data-testid="trip-id">{tripId}</span>
      <span data-testid="destination">{trip?.destination}</span>
    </div>
  );
}

describe("TripContext", () => {
  it("throws when useTripContext is used outside provider", () => {
    expect(() => render(<ReadTripContext />)).toThrow(
      "useTripContext must be used within TripContextProvider",
    );
  });

  it("provides trip data when wrapped in provider", () => {
    const trip: Trip = {
      id: "TRIP-001",
      destination: "Tokyo",
      type: "Leisure",
      state: "green",
      age: "2h",
      createdAt: "2026-04-18T00:00:00.000Z",
      updatedAt: "2026-04-18T00:00:00.000Z",
    };

    render(
      <TripContextProvider
        value={{ tripId: trip.id, trip, isLoading: false, error: null, refetchTrip: () => {}, replaceTrip: () => {} }}
      >
        <ReadTripContext />
      </TripContextProvider>,
    );

    expect(screen.getByTestId("trip-id")).toHaveTextContent("TRIP-001");
    expect(screen.getByTestId("destination")).toHaveTextContent("Tokyo");
  });
});
