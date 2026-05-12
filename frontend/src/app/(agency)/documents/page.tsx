import type { Metadata } from 'next';
import PageClient from './PageClient';

export const metadata: Metadata = {
  title: "Waypoint OS — Documents",
  description: "Canonical document upload, review, and extraction workspace.",
};

export default function Page() {
  return <PageClient />;
}

