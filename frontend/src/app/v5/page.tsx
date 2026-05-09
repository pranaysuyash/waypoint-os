import type { Metadata } from 'next';
import { V5LandingPage } from '@/components/marketing/landing-v5';

export const metadata: Metadata = {
  title: 'Waypoint OS — Quote-Ready Travel Requests',
  description:
    'A brighter landing page direction for turning scattered travel requests into quote-ready agency work.',
};

export default function V5Page() {
  return <V5LandingPage />;
}
