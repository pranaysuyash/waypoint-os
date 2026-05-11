import type { Metadata } from 'next';
import PageClient from './PageClient';

export const metadata: Metadata = {
  title: "Waypoint OS — Risk Review",
  description: "Review safety, compliance, and risk signals for the selected trip.",
};

export default function Page() {
  return <PageClient />;
}
