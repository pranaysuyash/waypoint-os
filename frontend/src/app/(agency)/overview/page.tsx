import type { Metadata } from 'next';
import PageClient from './PageClient';

export const metadata: Metadata = {
  title: "Waypoint OS — Agency Overview",
  description: "Review agency health, active planning work, lead inbox, quote review, and system status.",
};

export default function Page() {
  return <PageClient />;
}
