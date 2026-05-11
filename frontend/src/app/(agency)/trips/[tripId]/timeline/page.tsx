import type { Metadata } from 'next';
import PageClient from './PageClient';

export const metadata: Metadata = {
  title: "Waypoint OS — Trip Timeline",
  description: "Review the execution timeline and activity history for the selected trip.",
};

export default function Page() {
  return <PageClient />;
}
