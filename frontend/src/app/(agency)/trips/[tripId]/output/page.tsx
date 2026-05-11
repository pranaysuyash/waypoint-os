import type { Metadata } from 'next';
import PageClient from './PageClient';

export const metadata: Metadata = {
  title: "Waypoint OS — Outgoing Deliverables",
  description: "Review client-facing deliverables and agent notes for the selected trip.",
};

export default function Page() {
  return <PageClient />;
}
