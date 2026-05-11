import type { Metadata } from 'next';
import PageClient from './PageClient';

export const metadata: Metadata = {
  title: "Waypoint OS — Lead Inbox",
  description: "Review, filter, and assign new travel inquiries entering the agency workflow.",
};

export default function Page() {
  return <PageClient />;
}
