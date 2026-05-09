import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Waypoint OS — Traveler Portal",
  description:
    "View your trip details, itinerary, and updates from your travel advisor.",
};

export default function TravelerLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
