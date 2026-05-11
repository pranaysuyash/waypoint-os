import type { Metadata } from 'next';
import PageClient from './PageClient';

export const metadata: Metadata = {
  title: "Waypoint OS — Suitability Review",
  description: "Review activity suitability concerns and acknowledge critical traveler-fit flags.",
};

export default function Page() {
  return <PageClient />;
}
