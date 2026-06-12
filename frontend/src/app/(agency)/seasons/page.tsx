import type { Metadata } from 'next';
import PageClient from './PageClient';

export const metadata: Metadata = {
  title: 'Waypoint OS — Seasonal Campaigns',
  description: 'Create, simulate, preflight, and dispatch seasonal marketing campaign plans.',
};

export default function Page() {
  return <PageClient />;
}
