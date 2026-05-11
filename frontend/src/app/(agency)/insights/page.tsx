import type { Metadata } from 'next';
import PageClient from './PageClient';

export const metadata: Metadata = {
  title: "Waypoint OS — Insights",
  description: "Track agency performance, revenue, pipeline velocity, team workload, and operational alerts.",
};

export default function Page() {
  return <PageClient />;
}
