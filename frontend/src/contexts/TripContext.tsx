"use client";

import { createContext, use, type ReactNode } from "react";
import type { Trip } from "@/lib/api-client";

export interface TripContextValue {
  tripId: string | null;
  trip: Trip | null;
  isLoading: boolean;
  error: Error | null;
  refetchTrip: () => void;
  replaceTrip: (trip: Trip) => void;
}

const TripContext = createContext<TripContextValue | undefined>(undefined);

interface TripContextProviderProps {
  value: TripContextValue;
  children: ReactNode;
}

export function TripContextProvider({ value, children }: TripContextProviderProps) {
  return <TripContext.Provider value={value}>{children}</TripContext.Provider>;
}

export function useTripContext(): TripContextValue;
export function useTripContext(opts: { optional: true }): TripContextValue | null;
export function useTripContext(opts?: { optional?: boolean }): TripContextValue | null {
  const context = use(TripContext);
  if (!context) {
    if (opts?.optional) return null;
    throw new Error("useTripContext must be used within TripContextProvider");
  }
  return context;
}
