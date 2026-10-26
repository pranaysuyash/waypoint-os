import type { Metadata } from 'next';
import LandingVariant from '@/components/marketing/LandingVariant';

export const metadata: Metadata = {
  title: 'Waypoint OS — Every Inquiry. Under Control.',
  description:
    'Waypoint turns calls, emails, WhatsApp messages, and copied trip notes into structured briefs and quote-ready agency work for boutique travel teams.',
};

// FND-0386: the departure-board landing ships behind NEXT_PUBLIC_LANDING_VARIANT
// (see LandingVariant) — the committed V5 landing stays the default until the
// board is explicitly opted in.
export default function HomePage() {
  return <LandingVariant />;
}
