import type { Metadata } from 'next';
import PageClient from './PageClient';

export const metadata: Metadata = {
  title: 'Waypoint OS — Suppliers',
  description: 'Canonical supplier intelligence and route-level supplier context.',
};

export default function Page() {
  return <PageClient />;
}
