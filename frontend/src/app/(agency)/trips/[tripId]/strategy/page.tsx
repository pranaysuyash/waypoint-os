import type { Metadata } from 'next';
import PageClient from './PageClient';

export const metadata: Metadata = {
  title: "Waypoint OS — Trip Options",
  description: "Build and review trip options for the selected customer itinerary.",
};

export default function Page() {
  return <PageClient />;
}
