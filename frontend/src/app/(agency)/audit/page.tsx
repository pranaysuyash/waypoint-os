import type { Metadata } from 'next';
import PageClient from './PageClient';

export const metadata: Metadata = {
  title: "Waypoint OS — Audit Log",
  description: "Review operational audit events and system activity for the agency workspace.",
};

export default function Page() {
  return <PageClient />;
}
