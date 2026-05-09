import type { Metadata } from 'next';
import { ExperimentLab } from '@/components/marketing/landing-experiments';

export const metadata: Metadata = {
  title: 'Waypoint OS v3 — Landing Experiments',
  description: 'Experimental landing page component lab for Waypoint OS.',
};

export default function V3Page() {
  return <ExperimentLab />;
}
