import type { Metadata } from 'next';
import PageClient from './PageClient';

export const metadata: Metadata = {
  title: "Waypoint OS — Itinerary Checker",
  description: "Check itinerary quality, risk, cost, and readiness before travel decisions are finalized.",
};

export default function Page() {
  return <PageClient />;
}
