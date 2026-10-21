import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Privacy — Waypoint OS',
  description: 'How Waypoint OS handles traveler and agency data.',
};

// T14: privacy page grounded in actual product behavior (encryption at rest,
// RLS tenant isolation, token TTLs, retention). Legal-language review is
// pending owner/DPA — the page says so rather than impersoning counsel.

const PRACTICES: Array<{ title: string; body: string }> = [
  {
    title: 'What we store',
    body: 'Agency account data (workspace, members, roles), the travel inquiries you submit (notes, structured details, attachments), the decisions and proposals generated from them, and messages you exchange through connected channels such as WhatsApp.',
  },
  {
    title: 'How it is protected',
    body: 'Every agency’s data is isolated at the database level (row-level security keyed to your workspace). Sensitive lead content is encrypted at rest. Proposal and question links are cryptographically signed, expire on a timer, and can be revoked by your advisor at any time.',
  },
  {
    title: 'Who sees your data',
    body: 'The agency you are working with, and the platform only to operate the service. We do not sell traveler data. Public surfaces (a proposal page, a question page) expose only what your advisor explicitly sends to you, behind expiring links.',
  },
  {
    title: 'How long we keep it',
    body: 'Trip records are retained while your agency’s relationship is active. Sensitive artifacts such as passport data captured during document checks are held under short retention windows. Deletion requests are honored through your agency’s data contact and are cryptographically certified when completed.',
  },
  {
    title: 'AI processing',
    body: 'Trip planning uses AI models to read your inquiry, ask clarifying questions, and propose itineraries. Personal constraints you state (dietary, mobility, occasions) are attributed inside your trip record and are never published on public pages — public documents show what the plan accounts for, not who stated it.',
  },
];

export default function PrivacyPage() {
  return (
    <main className='min-h-screen bg-[#0d1117] text-white'>
      <div className='mx-auto max-w-3xl px-4 py-14'>
        <h1 className='text-3xl font-bold tracking-tight mb-2'>Privacy at Waypoint OS</h1>
        <p className='text-sm text-[#8b949e] mb-8'>
          This page describes how the platform actually handles data. It is written from the
          product&apos;s behavior, not boilerplate.
        </p>

        <div className='rounded-lg border border-amber-500/30 bg-amber-500/10 p-4 text-xs text-amber-200 mb-8'>
          <p className='font-semibold uppercase tracking-wide'>Review pending</p>
          <p className='mt-1'>
            This summary reflects implemented behavior as of September 2026. Formal legal review and a
            data-processing agreement (DPA) are completed with each agency before production onboarding.
          </p>
        </div>

        <dl className='space-y-6'>
          {PRACTICES.map((p) => (
            <div key={p.title} className='rounded-xl border border-[#30363d] bg-[#161b22] p-5'>
              <dt className='text-base font-semibold text-white mb-1.5'>{p.title}</dt>
              <dd className='text-sm text-[#8b949e] leading-relaxed'>{p.body}</dd>
            </div>
          ))}
        </dl>

        <p className='text-xs text-[#484f58] mt-10'>
          Questions or deletion requests: contact your travel agency, who can act on your data through
          the platform&apos;s data-management tools.
        </p>
      </div>
    </main>
  );
}
