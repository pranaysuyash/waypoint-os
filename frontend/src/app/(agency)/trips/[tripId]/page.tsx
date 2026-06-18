import { redirect } from 'next/navigation';

export default async function TripWorkspaceRedirectPage({
  params,
}: {
  params: Promise<{ tripId: string }>;
}) {
  const { tripId } = await params;
  redirect(`/trips/${encodeURIComponent(tripId)}/intake`);
}
