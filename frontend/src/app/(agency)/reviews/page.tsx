import type { Metadata } from 'next';
import PageClient from './PageClient';

export const metadata: Metadata = {
  title: "Waypoint OS — Quote Reviews",
  description: "Review, approve, reject, and resolve travel proposal decisions that need owner oversight.",
};

export default function Page() {
  return <PageClient />;
}
