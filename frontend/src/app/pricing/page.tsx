import type { Metadata } from 'next';
import PricingPage, { metadata as pricingMetadata } from '@/components/marketing/pricing-page';

export const metadata: Metadata = pricingMetadata;

export default function Page() {
  return <PricingPage />;
}
