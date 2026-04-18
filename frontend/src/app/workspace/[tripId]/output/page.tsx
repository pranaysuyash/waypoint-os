/**
 * Wave 1L compat redirect — 'output' maps to 'strategy' in workbench
 * (traveller-safe bundle lives there pre-Wave 3).
 * Replace with OutputPanel in Wave 3.
 */
import { redirect } from 'next/navigation';
import { _getWorkbenchCompatRoute } from '@/lib/routes';

interface PageProps {
  params: Promise<{ tripId: string }>;
}

export default async function OutputPage({ params }: PageProps) {
  const { tripId } = await params;
  redirect(_getWorkbenchCompatRoute(tripId, 'output'));
}