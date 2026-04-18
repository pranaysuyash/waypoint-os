/**
 * Wave 1L migration compatibility redirect.
 *
 * Routes users to the fully-functional workbench 'intake' tab until
 * workspace/[tripId]/intake has real content (Wave 3 — IntakePanel extraction).
 *
 * When to remove:
 *   - After workspace layout (Wave 2) and panel extraction (Wave 3) are complete.
 *   - Delete this file and replace with real IntakePage content.
 */
import { redirect } from 'next/navigation';
import { _getWorkbenchCompatRoute } from '@/lib/routes';

interface PageProps {
  params: Promise<{ tripId: string }>;
}

export default async function IntakePage({ params }: PageProps) {
  const { tripId } = await params;
  redirect(_getWorkbenchCompatRoute(tripId, 'intake'));
}