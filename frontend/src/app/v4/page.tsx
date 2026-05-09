import type { Metadata } from 'next';
import { V4LandingPage } from '@/components/marketing/landing-experiments';

export const metadata: Metadata = {
  title: 'Waypoint OS — Safer Trip Decisions',
  description:
    'A cinematic, animated landing page direction for boutique travel agency operations.',
};

export default function V4Page() {
  return <V4LandingPage />;
}
