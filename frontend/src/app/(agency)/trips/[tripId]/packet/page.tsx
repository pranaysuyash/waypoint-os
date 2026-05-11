import type { Metadata } from 'next';
import PageClient from './PageClient';

export const metadata: Metadata = {
  title: "Waypoint OS — Trip Details",
  description: "Review structured trip details, customer requirements, and planning inputs.",
};

export default function Page() {
  return <PageClient />;
}
