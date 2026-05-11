import type { Metadata } from 'next';
import PageClient from './PageClient';

export const metadata: Metadata = {
  title: "Waypoint OS — Trips in Planning",
  description: "Manage active customer trips and continue planning work from the agency workspace.",
};

export default function Page() {
  return <PageClient />;
}
