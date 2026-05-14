import type { Metadata } from 'next';
import PageClient from './PageClient';

export const metadata: Metadata = {
  title: "Waypoint OS — Trip Ops",
  description: "Manage booking operations, documents, payments, and readiness for the selected trip.",
};

export default function Page() {
  return <PageClient />;
}
