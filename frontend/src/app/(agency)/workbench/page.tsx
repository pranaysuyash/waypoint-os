import { redirect } from 'next/navigation';

// T2 route unification (FND-0304): /inquiries/new is the canonical intake URL
// (the Shell nav pushes it); /workbench renders the same PageClient. This
// route now forwards to the canonical path, preserving the full query string
// (?tab=, ?trip=, ?draft=, ?repair=…) so programmatic deep links
// (auth-redirect restore, getWorkbenchTripHref) keep working at one URL.
export default async function WorkbenchRedirectPage({
  searchParams,
}: {
  searchParams: Record<string, string | string[] | undefined>;
}) {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(searchParams)) {
    if (Array.isArray(value)) {
      for (const v of value) params.append(key, v);
    } else if (value !== undefined) {
      params.append(key, value);
    }
  }
  const query = params.toString();
  redirect(query ? `/inquiries/new?${query}` : '/inquiries/new');
}
