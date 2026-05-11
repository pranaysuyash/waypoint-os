import type { Metadata } from 'next';
import PageClient from './PageClient';

export const metadata: Metadata = {
  title: "Waypoint OS — Trip Follow-ups",
  description: "Review due, overdue, and upcoming follow-up actions for the selected trip.",
};

export default function Page() {
  return <PageClient />;
}
