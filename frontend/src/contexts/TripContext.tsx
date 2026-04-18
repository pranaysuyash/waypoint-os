"use client";

import { createContext, useContext, type ReactNode } from "react";
import type { Trip } from "@/lib/api-client";

export interface TripContextValue {
  tripId: string | null;
  trip: Trip | null;
  isLoading: boolean;
  error: Error | null;
}

const TripContext = createContext<TripContextValue | undefined>(undefined);

interface TripContextProviderProps {
  value: TripContextValue;
  children: ReactNode;
}

export function TripContextProvider({ value, children }: TripContextProviderProps) {
  return <TripContext.Provider value={value}>{children}</TripContext.Provider>;
}

export function useTripContext(): TripContextValue {
  const context = useContext(TripContext);
  if (!context) {
    throw new Error("useTripContext must be used within TripContextProvider");
  }
  return context;
}
