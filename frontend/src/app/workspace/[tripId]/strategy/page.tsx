/** Wave 1L compat redirect — replace with StrategyPanel in Wave 3. */
import { redirect } from 'next/navigation';
import { _getWorkbenchCompatRoute } from '@/lib/routes';

interface PageProps {
  params: Promise<{ tripId: string }>;
}

export default async function StrategyPage({ params }: PageProps) {
  const { tripId } = await params;
  redirect(_getWorkbenchCompatRoute(tripId, 'strategy'));
}