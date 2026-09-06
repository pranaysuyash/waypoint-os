import type { Metadata } from 'next';
import PageClient from './PageClient';

export const metadata: Metadata = {
  title: 'Platform Product-B Analytics',
  description: 'Global, read-only Product-B adoption and performance analytics.',
};

export default function PlatformProductBPage() {
  return <PageClient />;
}
