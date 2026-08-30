import type { Metadata } from 'next';
import PageClient from '../../workbench/PageClient';

export const metadata: Metadata = {
  title: "Waypoint OS — New Inquiry",
  description: "Create and process a new traveler inquiry, intake notes, and trip requests.",
};

export default function Page() {
  return <PageClient />;
}
