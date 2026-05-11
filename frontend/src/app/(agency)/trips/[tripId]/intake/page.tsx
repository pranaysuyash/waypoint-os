import type { Metadata } from 'next';
import PageClient from './PageClient';

export const metadata: Metadata = {
  title: "Waypoint OS — Trip Intake",
  description: "Review and edit intake details for the selected customer trip.",
};

export default function Page() {
  return <PageClient />;
}
