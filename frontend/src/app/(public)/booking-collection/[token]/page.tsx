import type { Metadata } from 'next';
import PageClient from './PageClient';

export const metadata: Metadata = {
  title: "Waypoint OS — Secure Booking Collection",
  description: "Securely provide traveler and booking details requested by your travel advisor.",
};

export default function Page({
  params,
}: {
  params: Promise<{ token: string }>;
}) {
  return <PageClient params={params} />;
}
