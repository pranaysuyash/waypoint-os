import type { Metadata } from 'next';
import { V5LandingPage } from '@/components/marketing/landing-v5';

export const metadata: Metadata = {
  title: 'Waypoint OS — Quote-Ready Travel Requests',
  description:
    'Waypoint turns calls, emails, WhatsApp messages, and copied trip notes into quote-ready agency work for boutique travel teams.',
};

export default function HomePage() {
  return <V5LandingPage />;
}
